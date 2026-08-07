#!/usr/bin/env python3
"""统计取证（一期能力，只用标准库）。

**不需要原始数据**的确定性一致性检验。这是本项目相对「让通用大模型读论文提意见」
最能拉开差距的一期能力：下列错误人眼极难发现，大模型也查不出来，
但用论文自己报告的数字就能确定性地判定。

五项检查
--------
1. `test_statistic_p_mismatch`  —— 由检验统计量 + 自由度反算 p，与报告值比对
2. `ci_estimate_mismatch`       —— 点估计是否落在自己报告的 95% CI 内
3. `count_percentage_mismatch`  —— 计数与百分比是否自洽
4. `grim_incompatible_mean`     —— 整数量表均值在给定 n 下是否可能
5. `table_total_mismatch`       —— 分类计数之和是否等于声明的分母

设计原则 · 前提不全就不跑
-------------------------
每项检查都有明确的**适用前提**，前提不满足**一律不运行**，
产出 `partial_extraction` 而不是猜。所有比较都用**报告精度对应的舍入区间**，
不用点值相等 —— 论文写 `p = 0.03` 意味着真值在 [0.025, 0.035)，
拿它跟反算出的 0.0312 比「相等」是错的。

**本模块只产出 `extraction_signal`（无 severity），不产出 finding。**
是否构成稿件问题由 M4 判定（`references/04-statistics.md`）。
这与「M1 与工具层不下稿件结论」的契约一致。

用法
----
    from statistical_forensics import check_all
    signals = check_all(claims)

命令行：
    python3 <Skill 目录>/scripts/statistical_forensics.py --input checks.json
    printf '%s' '[{"check":"count_percentage","count":3,"n":10,"reported_percent":30,"reported_percent_text":"30"}]' |
      python3 <Skill 目录>/scripts/statistical_forensics.py --input -
    python3 <Skill 目录>/scripts/statistical_forensics.py --selftest
"""

import argparse
import json
import math
import re
import sys

RULE_VERSION = "2026-08-07"


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"error": {"code": "invalid_input", "detail": message}},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)


# ================================================================ 分布函数
# 标准库无 scipy，以下为纯 Python 实现（连分数展开的正则化不完全 beta / gamma）。

def _log_beta(a, b):
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _betacf(a, b, x, itmax=300, eps=3e-16):
    """连分数展开，Numerical Recipes §6.4。"""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-300:
        d = 1e-300
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    """正则化不完全 beta 函数 I_x(a,b)。"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(a * math.log(x) + b * math.log(1.0 - x) - _log_beta(a, b))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(b * math.log(1.0 - x) + a * math.log(x) - _log_beta(b, a)) \
        * _betacf(b, a, 1.0 - x) / b


def gammainc_lower(s, x, itmax=300, eps=3e-16):
    """正则化下不完全 gamma P(s,x)。"""
    if x <= 0.0:
        return 0.0
    if x < s + 1.0:
        ap, total, delta = s, 1.0 / s, 1.0 / s
        for _ in range(itmax):
            ap += 1.0
            delta *= x / ap
            total += delta
            if abs(delta) < abs(total) * eps:
                break
        return total * math.exp(-x + s * math.log(x) - math.lgamma(s))
    # 连分数（上不完全）
    b = x + 1.0 - s
    c = 1e300
    d = 1.0 / b
    h = d
    for i in range(1, itmax + 1):
        an = -i * (i - s)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    q = math.exp(-x + s * math.log(x) - math.lgamma(s)) * h
    return 1.0 - q


def norm_sf(z):
    """标准正态上尾。"""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def t_sf(t, df):
    """t 分布上尾 P(T > t)。"""
    if df <= 0:
        return float("nan")
    x = df / (df + t * t)
    p = 0.5 * betainc(df / 2.0, 0.5, x)
    return p if t > 0 else 1.0 - p


def chi2_sf(stat, df):
    """卡方上尾。"""
    if df <= 0 or stat < 0:
        return float("nan")
    return 1.0 - gammainc_lower(df / 2.0, stat / 2.0)


def f_sf(stat, df1, df2):
    """F 分布上尾。"""
    if stat <= 0 or df1 <= 0 or df2 <= 0:
        return float("nan")
    x = df2 / (df2 + df1 * stat)
    return betainc(df2 / 2.0, df1 / 2.0, x)


# ================================================================ 舍入区间

def rounding_interval(text):
    """由报告文本推出真值所在的舍入区间。

    '0.03'    -> (0.025, 0.035)
    '0.0312'  -> (0.03115, 0.03125)
    '12.4'    -> (12.35, 12.45)
    带不等号的（'<0.001'）返回 None —— 那不是舍入值，需另行处理。
    """
    s = str(text).strip()
    if s.startswith("<") or s.startswith(">") or s.startswith("≤") or s.startswith("≥"):
        return None
    m = re.match(r"^-?\d+(?:\.(\d+))?$", s)
    if not m:
        return None
    decimals = len(m.group(1)) if m.group(1) else 0
    half = 0.5 * (10 ** -decimals)
    val = float(s)
    return (val - half, val + half)


def _sig(signal_id, stype, target, detail, extra):
    """产出符合 extraction_signal 契约的对象（无 severity）。"""
    base = {
        "id": signal_id,
        "type": stype,
        "target": target,
        "detail": detail,
        "observation_refs": [],
        "evidence_refs": [],
        # 契约（00-contracts.md §表）把计数类问题同时路由给 M4 与 M2：
        # 数值本身归 M4，而「表格与正文数据不一致」属 M2 的完整性范畴。
        # 曾经只发 M4，导致 M2 永远收不到这两类 signal。
        "routed_to": (["M4", "M2"]
                      if stype in ("count_percentage_mismatch", "table_total_mismatch")
                      else ["M4"]),
        "produced_by": "stage_2",
        "forensics": dict(extra, rule_version=RULE_VERSION),
    }
    return base


# ================================================================ 检查 1

def check_test_statistic_p(item, signal_id="SIG-101"):
    """反算 p 值并与报告值比对。

    前提（缺一不跑）：test_family ∈ {t,F,chi2,z}、statistic、df（z 除外）、
    tail ∈ {one,two}、reported_p 为可解析的舍入值。
    """
    fam = item.get("test_family")
    stat = item.get("statistic")
    tail = item.get("tail")
    rep = item.get("reported_p")

    if fam not in {"t", "F", "chi2", "z"} or stat is None or tail not in {"one", "two"}:
        return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                    "统计取证前提不全（缺 test_family / statistic / tail），本项未运行。",
                    {"check": "test_statistic_p_mismatch", "ran": False})

    if fam in {"F", "chi2"} and tail != "one":
        return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                    f"{fam} 统计量使用上尾概率；tail 必须为 one，本项未运行。",
                    {"check": "test_statistic_p_mismatch", "ran": False})

    if fam == "t":
        df = item.get("df")
        if df is None:
            return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                        "t 检验缺自由度，未反算 p。",
                        {"check": "test_statistic_p_mismatch", "ran": False})
        p = t_sf(abs(stat), df)
    elif fam == "z":
        p = norm_sf(abs(stat))
    elif fam == "chi2":
        df = item.get("df")
        if df is None:
            return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                        "卡方检验缺自由度，未反算 p。",
                        {"check": "test_statistic_p_mismatch", "ran": False})
        p = chi2_sf(stat, df)
    else:  # F
        df1, df2 = item.get("df1"), item.get("df2")
        if df1 is None or df2 is None:
            return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                        "F 检验缺分子或分母自由度，未反算 p。",
                        {"check": "test_statistic_p_mismatch", "ran": False})
        p = f_sf(stat, df1, df2)

    # F 与 chi2 天然单尾；t/z 按 tail 加倍
    if fam in {"t", "z"} and tail == "two":
        p *= 2.0

    interval = rounding_interval(rep)
    if interval is None:
        # '<0.001' 形式：只检查方向
        s = str(rep).strip()
        m = re.match(r"^(<|≤)\s*([\d.]+)$", s)
        if m:
            operator = m.group(1)
            bound = float(m.group(2))
            violates = p >= bound if operator == "<" else p > bound
            if violates:
                return _sig(signal_id, "test_statistic_p_mismatch",
                            item.get("target", "statistics"),
                            f"报告 p {rep}，但由 {fam} 统计量 {stat}（df={item.get('df', (item.get('df1'), item.get('df2')))}）"
                            f"反算得 p={p:.4g}，不小于所声称的上界。",
                            {"check": "test_statistic_p_mismatch", "ran": True,
                             "test_family": fam, "statistic": stat,
                             "df": item.get("df"), "df1": item.get("df1"),
                             "df2": item.get("df2"), "tail": tail,
                             "recomputed_p": p, "reported_p": rep,
                             "reported_bound": bound, "reported_operator": operator})
            return None
        return _sig(signal_id, "partial_extraction", item.get("target", "statistics"),
                    f"报告 p 值形式 {rep!r} 无法解析为舍入区间，未比对。",
                    {"check": "test_statistic_p_mismatch", "ran": False})

    lo, hi = interval
    if lo <= p <= hi:
        return None  # 一致，不出信号
    return _sig(signal_id, "test_statistic_p_mismatch", item.get("target", "statistics"),
                f"报告 p = {rep}（舍入区间 [{lo:.6g}, {hi:.6g}]），"
                f"但由 {fam} 统计量 {stat} 反算得 p = {p:.6g}，落在区间之外。",
                {"check": "test_statistic_p_mismatch", "ran": True,
                 "test_family": fam, "statistic": stat,
                 "df": item.get("df"), "df1": item.get("df1"),
                 "df2": item.get("df2"), "tail": tail,
                 "recomputed_p": p, "reported_p": rep,
                 "expected_interval": [lo, hi]})


# ================================================================ 检查 2

def check_ci_estimate(item, signal_id="SIG-102"):
    """点估计是否落在自己报告的 CI 内。

    前提：estimate、ci_low、ci_high 齐备且 ci_low < ci_high。
    对 OR/RR/HR 这类比值型，若给出 scale='log'，在对数尺度上比较。
    """
    est, lo, hi = item.get("estimate"), item.get("ci_low"), item.get("ci_high")
    if est is None or lo is None or hi is None:
        return _sig(signal_id, "partial_extraction", item.get("target", "effect_estimate"),
                    "CI 自洽性前提不全（缺点估计或区间端点），本项未运行。",
                    {"check": "ci_estimate_mismatch", "ran": False})
    if lo >= hi:
        return _sig(signal_id, "ci_estimate_mismatch", item.get("target", "effect_estimate"),
                    f"置信区间下界 {lo} 不小于上界 {hi}，区间本身不合法。",
                    {"check": "ci_estimate_mismatch", "ran": True,
                     "estimate": est, "ci": [lo, hi]})

    # 用报告精度的舍入容差，避免把四舍五入判成错误
    tol = 0.0
    for key in ("estimate_text", "ci_low_text", "ci_high_text"):
        iv = rounding_interval(item.get(key, ""))
        if iv:
            tol = max(tol, (iv[1] - iv[0]) / 2.0)

    if lo - tol <= est <= hi + tol:
        return None
    return _sig(signal_id, "ci_estimate_mismatch", item.get("target", "effect_estimate"),
                f"点估计 {est} 落在其自身报告的 95% CI [{lo}, {hi}] 之外"
                f"（已计入舍入容差 {tol:g}）。",
                {"check": "ci_estimate_mismatch", "ran": True,
                 "estimate": est, "ci": [lo, hi], "tolerance": tol})


# ================================================================ 检查 3

def check_count_percentage(item, signal_id="SIG-103"):
    """计数与百分比自洽。前提：count、n、reported_percent 齐备且 n > 0。"""
    count, n, pct = item.get("count"), item.get("n"), item.get("reported_percent")
    if count is None or n is None or pct is None:
        return _sig(signal_id, "partial_extraction", item.get("target", "proportion"),
                    "计数-百分比自洽性前提不全，本项未运行。",
                    {"check": "count_percentage_mismatch", "ran": False})
    if n <= 0:
        return _sig(signal_id, "count_percentage_mismatch", item.get("target", "proportion"),
                    f"分母 n = {n} 不合法。",
                    {"check": "count_percentage_mismatch", "ran": True})
    if count < 0:
        return _sig(signal_id, "count_percentage_mismatch", item.get("target", "proportion"),
                    f"计数 {count} 不得为负数。",
                    {"check": "count_percentage_mismatch", "ran": True,
                     "count": count, "n": n})
    if count > n:
        return _sig(signal_id, "count_percentage_mismatch", item.get("target", "proportion"),
                    f"计数 {count} 超过分母 {n}。",
                    {"check": "count_percentage_mismatch", "ran": True,
                     "count": count, "n": n})

    actual = 100.0 * count / n
    iv = rounding_interval(item.get("reported_percent_text", str(pct)))
    if iv is None:
        return _sig(signal_id, "partial_extraction", item.get("target", "proportion"),
                    f"百分比 {pct!r} 无法解析为舍入区间，未比对。",
                    {"check": "count_percentage_mismatch", "ran": False})
    lo, hi = iv
    if lo <= actual <= hi:
        return None
    return _sig(signal_id, "count_percentage_mismatch", item.get("target", "proportion"),
                f"报告 {count}/{n} = {pct}%，但实算为 {actual:.4g}%，"
                f"落在报告精度舍入区间 [{lo:g}, {hi:g}] 之外。",
                {"check": "count_percentage_mismatch", "ran": True,
                 "count": count, "n": n, "recomputed_percent": actual,
                 "expected_interval": [lo, hi]})


# ================================================================ 检查 4

def check_grim(item, signal_id="SIG-104"):
    """GRIM：整数量表的等权算术均值在给定 n 下是否可能。

    **严格前提**（任一不满足即不跑）：
      - `scale_is_integer = True`（每个受试者的取值为整数）
      - `items_per_subject`（李克特多题求和时的题数），默认 1
      - `n` 明确且 n <= 200（n 越大 GRIM 分辨力越低，>200 基本失效）
      - 均值以文本形式给出，可解析小数位
      - **不适用**：调整均值、最小二乘均值、加权均值、缺失后 n 不明、连续量表
    """
    if not item.get("scale_is_integer"):
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    "GRIM 前提不满足（未确认为整数量表的原始算术均值），本项未运行。",
                    {"check": "grim_incompatible_mean", "ran": False})
    if item.get("is_adjusted_mean"):
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    "报告的是调整均值 / LS mean，GRIM 不适用，本项未运行。",
                    {"check": "grim_incompatible_mean", "ran": False})

    n = item.get("n")
    mean_text = item.get("mean_text")
    if n is None or mean_text is None:
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    "GRIM 缺 n 或均值文本，本项未运行。",
                    {"check": "grim_incompatible_mean", "ran": False})
    if n <= 0 or n > 200:
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    f"n = {n} 超出 GRIM 有效范围（1–200），本项未运行。",
                    {"check": "grim_incompatible_mean", "ran": False})

    m = re.match(r"^-?\d+(?:\.(\d+))?$", str(mean_text).strip())
    if not m:
        return _sig(signal_id, "partial_extraction", item.get("target", "mean"),
                    f"均值 {mean_text!r} 无法解析小数位，本项未运行。",
                    {"check": "grim_incompatible_mean", "ran": False})
    decimals = len(m.group(1)) if m.group(1) else 0
    mean = float(mean_text)
    k = item.get("items_per_subject", 1)
    total_units = n * k

    half = 0.5 * (10 ** -decimals)
    mean_lo, mean_hi = mean - half, mean + half

    # 可能的总和为整数；对应的均值集合
    lo_sum = math.floor(mean * total_units) - 2
    hi_sum = math.ceil(mean * total_units) + 2
    for s in range(lo_sum, hi_sum + 1):
        cand = s / total_units
        # 舍入端点采用闭区间：原文未声明 half-even/half-up 时，边界候选视为可行，
        # 以避免 Python 二进制浮点与 banker rounding 制造假阳性。
        if mean_lo <= cand <= mean_hi:
            return None  # 存在可行整数总和 → 一致
    return _sig(signal_id, "grim_incompatible_mean", item.get("target", "mean"),
                f"报告均值 {mean_text}（n = {n}"
                + (f"，每人 {k} 题" if k != 1 else "")
                + f"）在整数量表下不可能：不存在整数总和使其四舍五入到 {decimals} 位小数等于该值。",
                {"check": "grim_incompatible_mean", "ran": True,
                 "n": n, "items_per_subject": k, "reported_mean": mean_text})


# ================================================================ 检查 5

def check_table_total(item, signal_id="SIG-105"):
    """分类计数之和是否等于声明的分母。

    前提：`counts`（互斥且穷尽的各类别计数）与 `declared_total` 齐备。
    **只在类别互斥且穷尽时适用** —— 调用方必须确认这一点，
    否则「合计不等于 n」是正常的（例如可多选的合并症）。

    典型错误：表 1 某特征分两类，12 + 18 = 30，而表头声明该组 n = 28。
    """
    counts = item.get("counts")
    total = item.get("declared_total")
    target = item.get("target", "table")

    if not counts or total is None:
        return _sig(signal_id, "partial_extraction", target,
                    "表格合计自洽性前提不全（缺各类别计数或声明分母），本项未运行。",
                    {"check": "table_total_mismatch", "ran": False})

    if not item.get("categories_exhaustive", False):
        return _sig(signal_id, "partial_extraction", target,
                    "未确认各类别互斥且穷尽（如可多选的合并症），"
                    "合计不等于分母属正常，本项未运行。",
                    {"check": "table_total_mismatch", "ran": False})

    try:
        s_counts = sum(int(c) for c in counts)
        total_i = int(total)
    except (TypeError, ValueError):
        return _sig(signal_id, "partial_extraction", target,
                    "计数或分母无法解析为整数，本项未运行。",
                    {"check": "table_total_mismatch", "ran": False})

    missing = item.get("missing_count")
    if missing is not None:
        try:
            s_counts += int(missing)
        except (TypeError, ValueError):
            pass

    if s_counts == total_i:
        return None

    return _sig(signal_id, "table_total_mismatch", target,
                f"各类别计数合计为 {s_counts}（{' + '.join(str(c) for c in counts)}"
                + (f" + 缺失 {missing}" if missing is not None else "")
                + f"），但声明的分母为 {total_i}，相差 {s_counts - total_i}。"
                f"在类别互斥且穷尽的前提下，这是确定性的计数错误。",
                {"check": "table_total_mismatch", "ran": True,
                 "counts": list(counts), "declared_total": total_i,
                 "observed_sum": s_counts, "difference": s_counts - total_i})


# ================================================================ 汇总

CHECKS = {
    "test_statistic_p": check_test_statistic_p,
    "ci_estimate": check_ci_estimate,
    "count_percentage": check_count_percentage,
    "grim": check_grim,
    "table_total": check_table_total,
}


def check_all(items, signal_start=100):
    """items 是 [{check: <名>, ...参数}]，返回 extraction_signal 列表。

    一致的项**不产出信号**（沉默即通过）；只有不一致或前提不全才产出。
    """
    if not isinstance(items, list):
        raise ValueError("统计取证输入必须是 JSON 数组")
    if not isinstance(signal_start, int) or isinstance(signal_start, bool) or signal_start < 0:
        raise ValueError("signal_start 必须是非负整数")

    out = []
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"统计取证第 {i} 项必须是 JSON 对象")
        fn = CHECKS.get(item.get("check"))
        if fn is None:
            raise ValueError(f"统计取证第 {i} 项的 check 不受支持：{item.get('check')!r}")
        try:
            sig = fn(item, signal_id=f"SIG-{signal_start + i:03d}")
        except (TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
            raise ValueError(f"统计取证第 {i} 项参数非法：{exc}") from exc
        if sig is not None:
            # 调用方若已绑定观察与稿件证据，保留这些 ref；工具不自行编造定位。
            # 未提供时维持空数组，由 Stage 2 汇总器在进入 M4 前补齐。
            for ref_key in ("observation_refs", "evidence_refs"):
                refs = item.get(ref_key)
                if refs is not None:
                    if not isinstance(refs, list) or not all(isinstance(x, str) for x in refs):
                        raise ValueError(f"统计取证第 {i} 项的 {ref_key} 必须为字符串数组")
                    sig[ref_key] = list(refs)
            out.append(sig)
    return out


# ================================================================ 自检
def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    # --- 分布函数对照已知值 ---
    expect("norm_sf(1.96)≈0.025", round(norm_sf(1.96), 4), 0.025)
    expect("t_sf(2.228,10)*2≈0.05", round(t_sf(2.228, 10) * 2, 3), 0.05)
    expect("chi2_sf(3.841,1)≈0.05", round(chi2_sf(3.841, 1), 3), 0.05)
    expect("f_sf(4.965,2,10)≈0.032", round(f_sf(4.965, 2, 10), 3), 0.032)

    # --- 检查 1：一致的 t 检验不应报警 ---
    s = check_test_statistic_p({"check": "test_statistic_p", "test_family": "t",
                                "statistic": 2.228, "df": 10, "tail": "two",
                                "reported_p": "0.05"})
    expect("t 一致 → 无信号", s, None)

    # p 值错位（报告 0.001 实际 0.05）
    s = check_test_statistic_p({"test_family": "t", "statistic": 2.228, "df": 10,
                                "tail": "two", "reported_p": "0.001"})
    expect("t 不一致 → 报警", s["type"] if s else None, "test_statistic_p_mismatch")
    expect("p 反算 signal 保留检验族", s["forensics"].get("test_family"), "t")
    expect("p 反算 signal 保留自由度", s["forensics"].get("df"), 10)

    s = check_test_statistic_p({"test_family": "t", "statistic": 4.0, "df": 30,
                                "tail": "two", "reported_p": "<0.001"})
    expect("满足 p 上界 → 无信号", s, None)

    s = check_test_statistic_p({"test_family": "z", "statistic": 0.0,
                                "tail": "one", "reported_p": "≤0.5"})
    expect("等于 p 非严格上界 → 无信号", s, None)

    s = check_test_statistic_p({"test_family": "chi2", "statistic": 3.841, "df": 1,
                                "tail": "two", "reported_p": "0.05"})
    expect("chi2 双尾声明 → 不运行", s["forensics"]["ran"], False)

    # 缺 df → 不跑
    s = check_test_statistic_p({"test_family": "t", "statistic": 2.2, "tail": "two",
                                "reported_p": "0.05"})
    expect("缺 df → partial_extraction", s["type"], "partial_extraction")

    # --- 检查 2 ---
    s = check_ci_estimate({"estimate": 12.4, "ci_low": 9.8, "ci_high": 15.7})
    expect("点估计在 CI 内 → 无信号", s, None)
    s = check_ci_estimate({"estimate": 20.0, "ci_low": 9.8, "ci_high": 15.7})
    expect("点估计在 CI 外 → 报警", s["type"], "ci_estimate_mismatch")

    # --- 检查 3 ---
    s = check_count_percentage({"count": 42, "n": 84, "reported_percent": 50.0,
                                "reported_percent_text": "50.0"})
    expect("42/84=50.0% → 无信号", s, None)
    s = check_count_percentage({"count": 42, "n": 84, "reported_percent": 60.0,
                                "reported_percent_text": "60.0"})
    expect("42/84≠60.0% → 报警", s["type"], "count_percentage_mismatch")
    s = check_count_percentage({"count": -1, "n": 10, "reported_percent": -10.0,
                                "reported_percent_text": "-10.0"})
    expect("负计数 → 报警", s["type"], "count_percentage_mismatch")

    # --- 检查 4 GRIM ---
    # n=10, mean=3.10 可行（总和 31）
    s = check_grim({"scale_is_integer": True, "n": 10, "mean_text": "3.10"})
    expect("GRIM 可行 → 无信号", s, None)
    # n=10, mean=3.14 不可行（总和须为 31.4）
    s = check_grim({"scale_is_integer": True, "n": 10, "mean_text": "3.14"})
    expect("GRIM 不可行 → 报警", s["type"], "grim_incompatible_mean")
    # 调整均值 → 不跑
    s = check_grim({"scale_is_integer": True, "n": 10, "mean_text": "3.14",
                    "is_adjusted_mean": True})
    expect("调整均值 → partial_extraction", s["type"], "partial_extraction")
    # n 过大 → 不跑
    s = check_grim({"scale_is_integer": True, "n": 500, "mean_text": "3.14"})
    expect("n>200 → partial_extraction", s["type"], "partial_extraction")

    # --- 检查 5 表格合计（来自真实 A/B 实测发现的缺口）---
    # rct_clinical Table 1：绝经状态 12 + 18 = 30，表头却声明 n = 28
    s = check_table_total({"counts": [12, 18], "declared_total": 28,
                           "categories_exhaustive": True})
    expect("12+18 != 28 -> 报警", s["type"] if s else None, "table_total_mismatch")
    expect("差值正确", s["forensics"]["difference"] if s else None, 2)
    s = check_table_total({"counts": [13, 15], "declared_total": 28,
                           "categories_exhaustive": True})
    expect("13+15 = 28 -> 无信号", s, None)
    s = check_table_total({"counts": [12, 14], "declared_total": 28,
                           "missing_count": 2, "categories_exhaustive": True})
    expect("计入缺失后相等 -> 无信号", s, None)
    s = check_table_total({"counts": [12, 18], "declared_total": 28})
    expect("未确认互斥穷尽 -> 不运行",
           s["forensics"]["ran"] if s else None, False)

    # --- 信号契约：不得带 severity ---
    sigs = check_all([{"check": "grim", "scale_is_integer": True, "n": 10,
                       "mean_text": "3.14", "evidence_refs": ["EV-001"]}])
    expect("信号 id 符合 schema", bool(re.match(r"^SIG-[0-9]{3,}$", sigs[0]["id"])), True)
    expect("信号无 severity", all("severity" not in x for x in sigs), True)
    expect("信号路由到 M4", sigs[0]["routed_to"], ["M4"])
    expect("输入证据 ref 被保留", sigs[0]["evidence_refs"], ["EV-001"])

    try:
        check_all([None])
        invalid_rejected = False
    except ValueError:
        invalid_rejected = True
    expect("非对象输入给出受控错误", invalid_rejected, True)

    print("\n全部通过" if ok else "\n存在失败项")
    return 0 if ok else 1


def _read_json(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _main(argv=None):
    parser = _JsonArgumentParser(description="无需原始数据的统计一致性取证")
    parser.add_argument("--input", metavar="JSON", help="检查数组 JSON 文件；- 表示 stdin")
    parser.add_argument("--signal-start", type=int, default=100)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.input:
        parser.error("必须提供 --input JSON（或 --selftest）")
    try:
        items = _read_json(args.input)
        signals = check_all(items, signal_start=args.signal_start)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": {"code": "invalid_input", "detail": str(exc)}},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"signals": signals}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(_main())

#!/usr/bin/env python3
"""生物医学单位归一化器（一期能力，只用标准库）。

对应 `references/00-contracts.md §5.4` 第 1 步「单位归一化」——
该步骤此前只写了「无法归一 → ambiguous」，但没有可执行的归一化实现，
导致兼容性判定无法落地。本模块补上这一环。

设计原则 · fail closed
----------------------
**宁可返回「无法归一」，也不做不确定的换算。** 归一化错误会直接制造
假冲突（把 mg/mL 与 g/L 判成矛盾）或掩盖真冲突（把 mg/kg 与 mg/kg/day 合并）。
因此：

- 只做**同量纲**的确定性换算；
- 质量浓度 ↔ 摩尔浓度**必须**同时给出 analyte 与明确分子量，
  否则返回 `conversion_requires_molecular_weight`，**绝不用近似分子量代换**；
- 按体重/体表面积归一的剂量（mg/kg、mg/m²）与总量（mg）**不同量纲**，永不合并；
- 带时间的速率（mg/kg/day）与不带时间的剂量（mg/kg）**不同量纲**，永不合并；
- 未知别名一律 `unknown_unit`，由调用方判 `ambiguous`。

用法
----
    from normalize_biomed_units import normalize, compare_units

    normalize("µM")
    # {'status': 'ok', 'ucum_code': 'uM', 'dimension': 'substance_concentration',
    #  'factor_to_base': 1e-06, 'base_unit': 'mol/L', 'rule_id': 'conc.molar', ...}

    compare_units("mg/mL", "g/L")   # -> ('comparable', 1.0)
    compare_units("mg/kg", "mg/kg/day")  # -> ('incomparable_dimension', None)

命令行：
    python3 <Skill 目录>/scripts/normalize_biomed_units.py --normalize 'µM'
    python3 <Skill 目录>/scripts/normalize_biomed_units.py --compare 'mg/mL' 'g/L'
    python3 <Skill 目录>/scripts/normalize_biomed_units.py --selftest
"""

import argparse
import json
import math
import re
import sys
import unicodedata

RULE_VERSION = "2026-08-07"


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"error": {"code": "invalid_input", "detail": message}},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)

# ---------------------------------------------------------------- 量纲定义
# 每个量纲一个基准单位；同量纲之间才允许换算。

DIMENSIONS = {
    "substance_concentration": "mol/L",
    "mass_concentration": "g/L",
    "mass": "g",
    "mass_per_body_weight": "g/kg",
    "mass_per_body_surface": "g/m2",
    "mass_per_body_weight_per_time": "g/kg/s",
    "time": "s",
    "length": "m",
    "volume": "L",
    "count": "1",
    "count_concentration": "1/L",
    "dimensionless": "1",
    "temperature_celsius": "Cel",
    "catalytic_activity": "U",
    "pressure": "Pa",
}

# ---------------------------------------------------------------- 前缀
SI_PREFIX = {
    "Y": 1e24, "Z": 1e21, "E": 1e18, "P": 1e15, "T": 1e12, "G": 1e9, "M": 1e6,
    "k": 1e3, "h": 1e2, "da": 1e1, "": 1.0,
    "d": 1e-1, "c": 1e-2, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12,
    "f": 1e-15, "a": 1e-18, "z": 1e-21, "y": 1e-24,
}

# ---------------------------------------------------------------- 别名归一
# 键必须是已做过 §1 文本归一（micro sign、上标、空格）之后的形式。
ALIAS = {
    # 摩尔浓度
    "M": ("substance_concentration", 1.0, "conc.molar"),
    "mol/L": ("substance_concentration", 1.0, "conc.molar"),
    "mol/l": ("substance_concentration", 1.0, "conc.molar"),
    "molar": ("substance_concentration", 1.0, "conc.molar"),
    "mol/dm3": ("substance_concentration", 1.0, "conc.molar"),
    # 质量浓度
    "g/L": ("mass_concentration", 1.0, "conc.mass"),
    "g/l": ("mass_concentration", 1.0, "conc.mass"),
    "g/dL": ("mass_concentration", 10.0, "conc.mass"),
    "g/mL": ("mass_concentration", 1000.0, "conc.mass"),
    "%(w/v)": ("mass_concentration", 10.0, "conc.mass.percent_wv"),
    # 质量
    "g": ("mass", 1.0, "mass.base"),
    "Da": ("mass", 1.0, "mass.dalton"),
    # 剂量
    "g/kg": ("mass_per_body_weight", 1.0, "dose.per_bw"),
    "g/m2": ("mass_per_body_surface", 1.0, "dose.per_bsa"),
    # 时间
    "s": ("time", 1.0, "time.base"),
    "sec": ("time", 1.0, "time.base"),
    "min": ("time", 60.0, "time.base"),
    "h": ("time", 3600.0, "time.base"),
    "hr": ("time", 3600.0, "time.base"),
    "d": ("time", 86400.0, "time.base"),
    "day": ("time", 86400.0, "time.base"),
    "wk": ("time", 604800.0, "time.base"),
    "week": ("time", 604800.0, "time.base"),
    # 长度
    "m": ("length", 1.0, "length.base"),
    # 体积
    "L": ("volume", 1.0, "volume.base"),
    "l": ("volume", 1.0, "volume.base"),
    # 计数
    "cells": ("count", 1.0, "count.base"),
    "copies": ("count", 1.0, "count.base"),
    "cells/L": ("count_concentration", 1.0, "count.conc"),
    "cells/mL": ("count_concentration", 1000.0, "count.conc"),
    # 无量纲
    "1": ("dimensionless", 1.0, "dimensionless.base"),
    "%": ("dimensionless", 0.01, "dimensionless.percent"),
    "ratio": ("dimensionless", 1.0, "dimensionless.base"),
    "fold": ("dimensionless", 1.0, "dimensionless.base"),
    "AU": ("dimensionless", 1.0, "dimensionless.arbitrary"),
    # 其他
    "Cel": ("temperature_celsius", 1.0, "temp.celsius"),
    "U": ("catalytic_activity", 1.0, "activity.unit"),
    "Pa": ("pressure", 1.0, "pressure.base"),
    "mmHg": ("pressure", 133.322, "pressure.mmhg"),
}

# 可加 SI 前缀的基础符号（前缀 + 符号 才去查 ALIAS）
PREFIXABLE = {"M", "mol/L", "g/L", "g", "L", "m", "s", "U", "Da", "g/kg", "g/m2",
              "cells/L", "Pa"}


def _normalize_text(raw):
    """§1 文本归一：Unicode 微符号、上标、全角、空格、per、乘方。"""
    if raw is None:
        return ""
    s = unicodedata.normalize("NFKC", str(raw)).strip()
    # 各种「微」符号统一为 ASCII u
    s = s.replace("µ", "u").replace("μ", "u").replace("μ", "u")
    # 上标数字
    for sup, plain in {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
                       "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
                       "⁻": "-"}.items():
        s = s.replace(sup, plain)
    # 各种非 ASCII 负号统一为 ASCII hyphen（U+2212 减号、连接号、短破折号）
    s = s.replace("−", "-").replace("‐", "-").replace("–", "-")
    # 中点乘号
    s = s.replace("·", ".").replace("×", "*").replace("⁄", "/")
    # per -> /
    s = re.sub(r"\s+per\s+", "/", s, flags=re.IGNORECASE)
    # 负指数写法 mg.kg-1 -> mg/kg
    s = re.sub(r"\.?([A-Za-z]+)\s*-1\b", r"/\1", s)
    # 去空格
    s = re.sub(r"\s+", "", s)
    return s


def _split_prefix(token):
    """把 token 拆成 (prefix_factor, base_symbol)，找不到返回 None。"""
    if token in ALIAS:
        return 1.0, token
    for plen in (2, 1):
        if len(token) > plen:
            pre, rest = token[:plen], token[plen:]
            if pre in SI_PREFIX and rest in PREFIXABLE and rest in ALIAS:
                return SI_PREFIX[pre], rest
    return None


def normalize(raw_unit):
    """把稿件原写法归一为 UCUM 风格代码 + 量纲 + 到基准单位的倍率。

    返回 dict，`status` 取：
        ok                                归一成功
        unknown_unit                      无法识别，调用方应判 ambiguous
        conversion_requires_molecular_weight   识别成功但跨量纲需分子量
        dimensionless_input               输入为空 / null
    """
    out = {
        "input": raw_unit,
        "rule_version": RULE_VERSION,
        "status": "unknown_unit",
        "ucum_code": None,
        "dimension": None,
        "base_unit": None,
        "factor_to_base": None,
        "rule_id": None,
        "note": None,
    }

    if raw_unit is None or str(raw_unit).strip() == "":
        out.update(status="dimensionless_input", ucum_code=None,
                   dimension="dimensionless", base_unit="1", factor_to_base=1.0,
                   rule_id="dimensionless.null",
                   note="无量纲指标；调用方不得因缺 unit 判为报告不完整")
        return out

    s = _normalize_text(raw_unit)

    # 速率：X/时间 —— 必须与不带时间的同名单位区分开
    rate = re.match(r"^(.+?)/(s|sec|min|h|hr|d|day|wk|week)$", s)
    if rate:
        head, tspec = rate.group(1), rate.group(2)
        head_res = normalize(head)
        t_res = normalize(tspec)
        if head_res["status"] == "ok" and t_res["status"] == "ok":
            if head_res["dimension"] == "mass_per_body_weight":
                out.update(
                    status="ok",
                    ucum_code=f"{head_res['ucum_code']}/{t_res['ucum_code']}",
                    dimension="mass_per_body_weight_per_time",
                    base_unit=DIMENSIONS["mass_per_body_weight_per_time"],
                    factor_to_base=head_res["factor_to_base"] / t_res["factor_to_base"],
                    rule_id="dose.per_bw_per_time",
                    note="速率量纲，与不带时间的剂量不可比",
                )
                return out
            out.update(status="unknown_unit",
                       note=f"未登记的速率量纲：{head_res['dimension']}/time")
            return out

    hit = _split_prefix(s)
    if hit is None:
        # 常见复合浓度写法 mg/mL、ug/L …
        m = re.match(r"^([A-Za-z]+)/([A-Za-z]+)$", s)
        if m:
            num, den = m.group(1), m.group(2)
            num_hit = _split_prefix(num)
            den_hit = _split_prefix(den)
            if num_hit and den_hit:
                nf, nb = num_hit
                df, db = den_hit
                ndim = ALIAS[nb][0]
                ddim = ALIAS[db][0]
                if ndim == "mass" and ddim == "volume":
                    factor = (nf * ALIAS[nb][1]) / (df * ALIAS[db][1])
                    out.update(status="ok", ucum_code=f"{num}/{den}",
                               dimension="mass_concentration",
                               base_unit=DIMENSIONS["mass_concentration"],
                               factor_to_base=factor, rule_id="conc.mass.compound")
                    return out
                if ndim == "substance_concentration" and ddim == "volume":
                    pass  # 落到下面的 unknown
                if ndim == "mass" and ddim == "mass":
                    factor = (nf * ALIAS[nb][1]) / (df * ALIAS[db][1])
                    out.update(status="ok", ucum_code=f"{num}/{den}",
                               dimension="mass_per_body_weight",
                               base_unit=DIMENSIONS["mass_per_body_weight"],
                               factor_to_base=factor, rule_id="dose.per_bw.compound")
                    return out
                if ndim == "count" and ddim == "volume":
                    factor = (nf * ALIAS[nb][1]) / (df * ALIAS[db][1])
                    out.update(status="ok", ucum_code=f"{num}/{den}",
                               dimension="count_concentration",
                               base_unit=DIMENSIONS["count_concentration"],
                               factor_to_base=factor, rule_id="count.conc.compound")
                    return out
        out["note"] = f"未登记的单位写法：{s}（归一后）"
        return out

    pfactor, base = hit
    dim, bfactor, rule_id = ALIAS[base]
    out.update(status="ok", ucum_code=s, dimension=dim,
               base_unit=DIMENSIONS[dim],
               factor_to_base=pfactor * bfactor, rule_id=rule_id)
    return out


# 质量浓度 ↔ 摩尔浓度：需要分子量，一期不自动查
CONVERTIBLE_WITH_MW = {
    frozenset({"mass_concentration", "substance_concentration"}),
}


def compare_units(unit_a, unit_b, molecular_weight=None, analyte=None):
    """判定两个单位能否比较。

    返回 (verdict, factor_a_to_b)：
        ('comparable', f)                     b_value = a_value * f
        ('incomparable_dimension', None)      量纲不同，是两回事，不构成冲突
        ('conversion_requires_molecular_weight', None)
        ('unknown_unit', None)                至少一方无法识别 → 调用方判 ambiguous
    """
    ra, rb = normalize(unit_a), normalize(unit_b)

    if ra["status"] == "unknown_unit" or rb["status"] == "unknown_unit":
        return "unknown_unit", None

    da, db = ra["dimension"], rb["dimension"]

    if da == db:
        return "comparable", ra["factor_to_base"] / rb["factor_to_base"]

    if frozenset({da, db}) in CONVERTIBLE_WITH_MW:
        try:
            mw = float(molecular_weight)
        except (TypeError, ValueError, OverflowError):
            mw = None
        if (mw is None or not math.isfinite(mw) or mw <= 0
                or analyte is None or not str(analyte).strip()):
            return "conversion_requires_molecular_weight", None
        # g/L -> mol/L 需要除以 MW(g/mol)
        a_base = ra["factor_to_base"]
        b_base = rb["factor_to_base"]
        if da == "mass_concentration":
            return "comparable", (a_base / mw) / b_base
        return "comparable", (a_base * mw) / b_base

    return "incomparable_dimension", None


# ---------------------------------------------------------------- 自检
SELFTEST = [
    # (a, b, 期望 verdict, 期望 factor 或 None)
    ("uM", "umol/L", "comparable", 1.0),
    ("µM", "uM", "comparable", 1.0),
    ("μmol·L−1", "uM", "comparable", 1.0),
    ("mg/mL", "g/L", "comparable", 1.0),
    ("mM", "uM", "comparable", 1000.0),
    ("mg/kg", "mg/kg/day", "incomparable_dimension", None),
    ("mg/kg", "mg/m2", "incomparable_dimension", None),
    ("mg", "mg/kg", "incomparable_dimension", None),
    ("mg/L", "uM", "conversion_requires_molecular_weight", None),
    ("banana", "uM", "unknown_unit", None),
    ("h", "min", "comparable", 60.0),
    ("%", "1", "comparable", 0.01),
]


def _selftest():
    ok = True
    for raw, want_code in (("μM", "uM"), ("μmol·L−1", "umol/L")):
        got = normalize(raw)
        good = got["status"] == "ok" and got["ucum_code"] == want_code
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {raw!r} -> ucum_code={got['ucum_code']!r} "
              f"(期望 {want_code!r})")

    for a, b, want_v, want_f in SELFTEST:
        v, f = compare_units(a, b)
        good = v == want_v and (want_f is None or (f is not None and abs(f - want_f) < 1e-9))
        ok &= good
        mark = "PASS" if good else "FAIL"
        print(f"  {mark}  {a!r} vs {b!r} -> {v} factor={f} (期望 {want_v} {want_f})")

    # 带分子量的跨量纲换算：葡萄糖 180.16 g/mol，1 g/L = 5.551 mmol/L
    v, f = compare_units("g/L", "mmol/L", molecular_weight=180.16, analyte="glucose")
    expect = (1.0 / 180.16) / 1e-3
    good = v == "comparable" and abs(f - expect) < 1e-6
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  g/L vs mmol/L (glucose MW=180.16) -> {v} factor={f}")

    for bad_mw in (0, -1, "unknown", float("inf")):
        v, f = compare_units("g/L", "mmol/L", molecular_weight=bad_mw, analyte="glucose")
        good = v == "conversion_requires_molecular_weight" and f is None
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  非法分子量 {bad_mw!r} 安全拒绝 -> {v}")

    print("\n全部通过" if ok else "\n存在失败项")
    return 0 if ok else 1


def _main(argv=None):
    parser = _JsonArgumentParser(description="生物医学单位归一化与可比性判定")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--normalize", metavar="UNIT", help="归一化一个单位")
    mode.add_argument("--compare", nargs=2, metavar=("UNIT_A", "UNIT_B"),
                      help="判断两个单位是否可比")
    mode.add_argument("--selftest", action="store_true", help="运行内置自检")
    parser.add_argument("--molecular-weight", type=float,
                        help="跨质量/摩尔浓度换算所需的正分子量，单位 g/mol")
    parser.add_argument("--analyte", help="跨质量/摩尔浓度换算所需的分析物名称")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if args.normalize is not None:
        result = normalize(args.normalize)
    else:
        verdict, factor = compare_units(
            args.compare[0], args.compare[1],
            molecular_weight=args.molecular_weight, analyte=args.analyte)
        result = {
            "unit_a": args.compare[0], "unit_b": args.compare[1],
            "verdict": verdict, "factor_a_to_b": factor,
            "rule_version": RULE_VERSION,
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(_main())

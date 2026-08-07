#!/usr/bin/env python3
"""全量基线探针扫描：逐条判断「这个检查真的需要 skill 吗」。

背景
----
评审看 uplift。裸模型本来就能查出来的问题，做进 skill 贡献为零还多花 token。
本轮已实测出两个方向性结论：
  · 裸模型在完整论文上能报出 15 条实质问题，挂 skill 反而只有 9 条（真子集）
  · table_total_mismatch 这类「一眼算术」Qwen 自己就能查出来

所以**每一个已实现的检查都应当被质问一次**：它到底是不是必需的。
本脚本读 tools/probe_cases/manifest.json，对每条检查跑基线探针，
输出保留 / 删减建议。

用法
----
    python3 tools/uplift_sweep.py                      # 全量扫描（可断点续跑）
    python3 tools/uplift_sweep.py --only stat. seq.    # 只扫指定前缀
    python3 tools/uplift_sweep.py --repeats 3 --gap 20
    python3 tools/uplift_sweep.py --report             # 只根据已有缓存出报告

结果缓存在 tools/probe_cases/.sweep_cache.json，中断后重跑不会重复消耗配额。
"""

import argparse
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MANIFEST = os.path.join(HERE, "probe_cases", "manifest.json")
CACHE = os.path.join(HERE, "probe_cases", ".sweep_cache.json")
REPORT = os.path.join(os.path.dirname(HERE), "docs", "uplift-sweep.md")

import baseline_probe as bp  # noqa: E402


def load_cache():
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_cache(c):
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(c, fh, ensure_ascii=False, indent=2)


# 三档处置。关键区分：**「不写详细规则」不等于「删掉」** ——
# 多数检查只需要在 SKILL.md 里占一行清单条目，把注意力引过去就够了；
# 只有裸模型确实查不出的，才值得写完整规则 + 上确定性工具。
ADVICE = {
    "BASELINE_FINDS_IT": ("① 只列清单",
                          "裸模型自己就能查出来 —— 保留一行清单条目引导注意力即可，"
                          "不要在 SKILL.md 里写详细规则，那是纯 token 浪费"),
    "BASELINE_UNRELIABLE": ("② 清单 + 确定性工具",
                            "裸模型时对时错 —— 用工具把它变成稳定命中，规则文字仍应精简"),
    "BASELINE_MISSES_IT": ("③ 完整规则 + 工具（高价值）",
                           "裸模型完全查不出 —— 这是 uplift 主来源，值得写清楚"),
    "INCONCLUSIVE": ("需重跑", "有效样本不足，不得据此下结论"),
}


def write_report(manifest, cache):
    by_id = {c["id"]: c for c in manifest["checks"]}
    rows = []
    for cid, r in cache.items():
        chk = by_id.get(cid, {})
        rows.append((cid, chk.get("implemented_by", "?"), r))

    order = {"BASELINE_MISSES_IT": 0, "BASELINE_UNRELIABLE": 1,
             "INCONCLUSIVE": 2, "BASELINE_FINDS_IT": 3}
    rows.sort(key=lambda x: (order.get(x[2]["verdict"], 9), x[0]))

    lines = [
        "# 已实现检查的基线探针扫描结果",
        "",
        "**问题：这些检查真的需要 skill 吗？**",
        "",
        "评审看的是 uplift —— 挂 skill 比裸模型强多少。裸模型本来就能查出来的问题，",
        "做进 skill 贡献为零，还会多花 token（负分）。本表逐条给出实测结论。",
        "",
        f"探针模型：`{rows[0][2].get('model', 'qwen3.8-max') if rows else 'qwen3.8-max'}`",
        f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| 检查 | 实现位置 | 命中/有效 | 失败 | 结论 | 建议 |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for cid, impl, r in rows:
        act, _ = ADVICE.get(r["verdict"], ("?", ""))
        lines.append(f"| `{cid}` | `{impl}` | {r['hits']}/{r['valid']} | "
                     f"{r['failures']} | {r['verdict']} | **{act}** |")

    keep = [r for _, _, r in rows if r["verdict"] in
            ("BASELINE_MISSES_IT", "BASELINE_UNRELIABLE")]
    drop = [c for c, _, r in rows if r["verdict"] == "BASELINE_FINDS_IT"]
    inc = [c for c, _, r in rows if r["verdict"] == "INCONCLUSIVE"]

    lines += [
        "",
        "## 结论",
        "",
        f"- **③ 完整规则 + 工具**：{len(keep)} 条（裸模型查不出或不稳定）",
        f"- **① 只列清单**：{len(drop)} 条 —— {', '.join('`'+c+'`' for c in drop) or '无'}",
        f"- **需重跑**：{len(inc)} 条 —— {', '.join('`'+c+'`' for c in inc) or '无'}",
        "",
        "## 怎么用这张表",
        "",
        "**核心原则：「不写详细规则」不等于「删掉这个检查」。**",
        "",
        "1. **① 只列清单** —— 裸模型自己查得出来。在 SKILL.md 的通读清单里留**一行**",
        "   把注意力引过去就够了（如「表格分母与计数是否自洽」），",
        "   **不要**写判定细则、阈值、正反例 —— 那是纯 token 浪费，还会挤占发现的注意力。",
        "2. **② 清单 + 确定性工具** —— 裸模型时对时错。清单一行 + 工具跑一遍，规则文字仍精简。",
        "3. **③ 完整规则 + 工具** —— 裸模型确实查不出。这是 uplift 来源，",
        "   值得写进 SKILL.md §6.5「什么时候必须运行」的最前面。",
        "4. **需重跑** —— 调用失败不等于模型查不出来",
        "   （与契约里 `parse_failed != not_reported` 同理），必须重跑。",
        "",
        "## 已知局限",
        "",
        "- **埋入式 vs 孤立片段**：标 `embedded` 的是把错误藏进一篇真实论文里问的，",
        "  与真实审稿难度相当。标 `isolated` 的是孤立片段 —— 片段里几乎只有那一个错误，",
        "  注意力不被稀释，会**系统性高估裸模型**，据此删检查有误删风险。",
        "- 图像类检查（`figure_integrity_audit`）**无法用文本探针测**，未纳入本表。",
        "- 每条只跑少量重复，属方向性证据，不是精确的命中率估计。",
        "- 本表只测「能不能发现」，没测「发现后的表述质量与证据可审计性」——",
        "  后者是 skill 的另一类价值（25% 的证据链维度），不因本表结论而否定。",
    ]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\n报告已写入 {os.path.relpath(REPORT, os.path.dirname(HERE))}")
    return keep, drop, inc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="只扫 id 以这些前缀开头的检查")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--gap", type=int, default=20, help="两条之间的间隔秒数，规避限流")
    ap.add_argument("--model", default=bp.DEFAULT_MODEL)
    ap.add_argument("--base", default=bp.DEFAULT_BASE)
    ap.add_argument("--host", default=None,
                    help="宿主论文文本。**强烈建议给** —— 不给就是孤立片段探针，"
                         "会系统性高估裸模型，从而误删有价值的检查")
    ap.add_argument("--report", action="store_true", help="只出报告，不跑探针")
    ap.add_argument("--refresh", action="store_true", help="忽略缓存重跑")
    args = ap.parse_args()

    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    cache = {} if args.refresh else load_cache()

    if args.report:
        write_report(manifest, cache)
        return 0

    key = bp.load_key()
    if not key:
        print("找不到 DASHSCOPE_API_KEY")
        return 2

    host_text = None
    if args.host:
        host_text = open(args.host, encoding="utf-8").read()
        print(f"埋入式探针：错误将藏进 {len(host_text)} 字符的真实论文中\n")
    else:
        print("警告：未指定 --host，使用孤立片段探针。片段里几乎只有那一个错误，"
              "会**系统性高估裸模型**，据此删检查有风险。\n")

    checks = manifest["checks"]
    if args.only:
        checks = [c for c in checks
                  if any(c["id"].startswith(p) for p in args.only)]

    todo = [c for c in checks if c["id"] not in cache]
    print(f"清单 {len(checks)} 条，已缓存 {len(checks) - len(todo)} 条，本次跑 {len(todo)} 条\n")

    for i, chk in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {chk['id']}  （实现于 {chk['implemented_by']}）")
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(chk["case"])
            case_path = fh.name
        try:
            hits, valid, failures, _ = bp.probe(
                open(case_path, encoding="utf-8").read(), chk["error"],
                key, args.base, args.model, args.repeats, host_text=host_text)
        finally:
            os.unlink(case_path)

        if valid == 0:
            verdict = "INCONCLUSIVE"
        elif hits / valid >= 0.5:
            verdict = "BASELINE_FINDS_IT"
        elif hits == 0:
            verdict = "BASELINE_MISSES_IT"
        else:
            verdict = "BASELINE_UNRELIABLE"

        cache[chk["id"]] = {"hits": hits, "valid": valid, "failures": failures,
                            "repeats": args.repeats, "model": args.model,
                            "mode": "embedded" if host_text else "isolated",
                            "verdict": verdict}
        save_cache(cache)
        act, why = ADVICE[verdict]
        print(f"    → {verdict}：{act}（{why}）\n")
        if i < len(todo):
            time.sleep(args.gap)

    keep, drop, inc = write_report(manifest, cache)
    print(f"保留 {len(keep)} · 删减 {len(drop)} · 待重跑 {len(inc)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

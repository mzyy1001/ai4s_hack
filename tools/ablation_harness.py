#!/usr/bin/env python3
"""五条件消融实验：判断 Skill 的**哪一层**真正带来增益。

为什么要消融而不是只做 A/B
--------------------------
只比「有 Skill / 无 Skill」，赢了不知道赢在哪，输了不知道该砍哪。
实测已经出现过负 uplift，且一次全流程追踪里八个规则库只读了一个 ——
必须能分开回答：增益来自发现方式、来自确定性工具，还是来自五千行规则库。

五个条件
--------
    A  bare_model            不挂 Skill
    B  monolithic_skill      旧架构（单次大提示 + 全部规则）
    C  discovery_only        只做全局发现 + 渲染，不读规则库不跑工具
    D  discovery_plus_tools  全局发现 + 定向工具 + 全局校正，不读规则库
    E  hierarchical_skill    完整分层架构

最关键的一次比较是 **D vs E**：

    D ≈ E   → 五千行规则库贡献有限，应当裁剪而不是继续加规则
    E > D   → 规则库有真实增量价值

用法
----
    python3 tools/ablation_harness.py --conditions A B E --corpus datasets/ground_truth
    python3 tools/ablation_harness.py --conditions D E --only PMC13254492
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys

# 各条件的提示词。差别**只在指令**，论文、模型、参数完全相同 ——
# 否则比较的就不是架构而是别的东西。
BASE_TASK = ("请审阅当前目录下的论文（fulltext.txt），列出你认为存在的所有问题，"
             "按严重程度排序。对每一条说明：问题是什么、依据在论文的哪个位置、为什么重要。")

CONDITIONS = {
    "A": {
        "name": "bare_model",
        "skill": False,
        "prompt": "你是资深同行评审。" + BASE_TASK,
    },
    "B": {
        "name": "monolithic_skill",
        "skill": True,
        # 旧架构行为：一次性把规则读完再审
        "prompt": ("你是资深同行评审。请使用 biomed-paper-review Skill，"
                   "按它的完整流程执行（读取契约与各模块规则库后再审阅）。" + BASE_TASK),
    },
    "C": {
        "name": "discovery_only",
        "skill": True,
        "prompt": ("你是资深同行评审。**只执行 biomed-paper-review Skill 的 Layer 1 全局发现**："
                   "以专家身份通读全文，产出 paper_map、claim_map 与候选问题清单，"
                   "然后直接把候选整理成审稿意见。"
                   "**不要读 M2–M7 规则库，不要运行任何脚本。**" + BASE_TASK),
    },
    "D": {
        "name": "discovery_plus_tools",
        "skill": True,
        "prompt": ("你是资深同行评审。执行 biomed-paper-review Skill 的 "
                   "**Layer 1 全局发现 + Layer 3 确定性核验 + Layer 4 全局校正**："
                   "先通读产出候选问题，再对表格数值、标识符、注册号、参考文献等"
                   "运行 scripts/ 下的确定性工具核验（含主动扫描），最后做跨节校正。"
                   "**不要读 M2–M7 规则库**，判定靠你自己的专业判断加工具结果。"
                   + BASE_TASK),
    },
    "E": {
        "name": "hierarchical_skill",
        "skill": True,
        "prompt": ("你是资深同行评审。请使用 biomed-paper-review Skill，"
                   "严格按其分层架构执行：Layer 1 全局发现 → Layer 2 路由专家"
                   "（每个专家只读它那一本规则库与那一包证据）→ Layer 3 定向工具核验"
                   "→ Layer 4 全局校正 → Layer 5 契约归一。" + BASE_TASK),
    },
}

REF_FILES = ["00-contracts", "00-runtime-contract", "00-routing",
             "01-structured-extraction", "02-macro-logic", "03-experimental-methods",
             "04-statistics", "05-figures-and-charts", "06-ethics-compliance",
             "07-conclusions-discussion"]
SCRIPTS = ["normalize_biomed_units", "statistical_forensics", "ethics_compliance_check",
           "sequence_identifier_audit", "figure_integrity_audit",
           "external_figure_validation"]


def run(cwd, prompt, model, timeout):
    """跑一次 opencode，返回 (事件, 原始输出)。"""
    cmd = ["opencode", "run", "--dir", cwd, "--model", model, "--format", "json", prompt]
    try:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, start_new_session=True)
    except FileNotFoundError:
        return [], "[opencode 不可用]"
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(os.getpgid(p.pid), sig)
            except (ProcessLookupError, PermissionError):
                break
            try:
                p.wait(timeout=10)
                break
            except subprocess.TimeoutExpired:
                continue
        return [], f"[TIMEOUT] 超过 {timeout} 秒"
    events = []
    for line in out.splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events, out + (("\n" + err) if err and err.strip() else "")


def telemetry(events):
    """从事件流还原运行时利用率。

    这是本次实验的核心观测量：不是「赢没赢」，而是**哪些部分真的被用上了**。
    严格区分脚本被 read（读源码，贡献为零）与被 bash 执行。
    """
    tools, texts = [], []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("tool"), str) and isinstance(o.get("state"), dict):
                tools.append(o)
            if o.get("type") == "text" and isinstance(o.get("text"), str):
                texts.append(o["text"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(events)
    read_blob = " ".join(json.dumps(t.get("state", {}).get("input", {}),
                                    ensure_ascii=False)
                         for t in tools if t["tool"] in ("read", "grep", "glob"))
    exec_blob = " ".join(json.dumps(t.get("state", {}).get("input", {}),
                                    ensure_ascii=False)
                         for t in tools if t["tool"] in ("bash", "shell"))
    return {
        "tool_calls": len(tools),
        "references_read": [r for r in REF_FILES if r in read_blob],
        # **只认真正执行的** —— read 到脚本源码不算用了它
        "scripts_executed": [s for s in SCRIPTS if s in exec_blob],
        "review": max(texts, key=len) if texts else "",
    }


def valid(text):
    """审阅是否真的跑起来了。调用失败绝不能记作「没查出来」。"""
    if not text or len(text.strip()) < 400:
        return False, f"输出过短（{len(text or '')} 字符）"
    for m in ("[opencode 不可用]", "[TIMEOUT]", "0 matches", "Error:",
              "ProviderAuthError", "usage limit", "rejected permission"):
        if m in text:
            return False, f"含错误标记 {m!r}"
    return True, ""


def judge(truth, review, model, cwd, timeout=900):
    prompt = f"""你是评审的裁判。

标准答案（权威来源给出的客观事实）：
{truth}

审稿意见：
---
{review[:20000]}
---

这份意见有没有**实质性**指出标准答案里那个问题？
判定从严：只提到相关名词、或给「建议核对」这类通用建议，都**不算**命中。
只回答一个词：HIT 或 MISS。"""
    _, out = run(cwd, prompt, model, timeout)
    u = out.upper()
    if "HIT" in u and "MISS" not in u:
        return "HIT"
    return "MISS" if "MISS" in u else "UNPARSEABLE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", nargs="+", default=["A", "E"],
                    choices=list(CONDITIONS))
    ap.add_argument("--corpus", default="datasets/ground_truth")
    ap.add_argument("--only")
    ap.add_argument("--model", default="dashscope/qwen3.8-max")
    ap.add_argument("--timeout", type=int, default=5400)
    ap.add_argument("--work", default=os.environ.get("CLAUDE_JOB_DIR", "/tmp") + "/ablation")
    ap.add_argument("--out", default="docs/results/ablation.json")
    a = ap.parse_args()

    idx = os.path.join(os.path.abspath(a.corpus), "index.json")
    if not os.path.isfile(idx):
        print(f"找不到 {idx}")
        return 2
    papers = json.load(open(idx, encoding="utf-8"))["papers"]
    if a.only:
        papers = [p for p in papers if p["pmcid"] == a.only]

    skill_src = os.path.abspath("skills/biomed-paper-review")
    rows = []

    for p in papers:
        pmcid, kind = p["pmcid"], p["kind"]
        truth = p["ground_truth"]["expected_finding"]
        print(f"\n=== {pmcid} [{kind}] ===")
        for c in a.conditions:
            cfg = CONDITIONS[c]
            d = os.path.join(a.work, pmcid, cfg["name"])
            if os.path.isdir(d):
                shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)
            shutil.copy(os.path.join(a.corpus, pmcid, "fulltext.txt"),
                        os.path.join(d, "fulltext.txt"))
            if cfg["skill"]:
                dst = os.path.join(d, ".claude", "skills")
                os.makedirs(dst, exist_ok=True)
                shutil.copytree(skill_src, os.path.join(dst, "biomed-paper-review"))

            print(f"  [{c} {cfg['name']}] 审阅中 …")
            ev, raw = run(d, cfg["prompt"], a.model, a.timeout)
            t = telemetry(ev)
            review = t["review"] or raw
            with open(os.path.join(d, "review.md"), "w", encoding="utf-8") as fh:
                fh.write(review)
            ok, why = valid(review)
            if not ok:
                print(f"    **调用失败：{why}** —— 记 INVALID，不得当作没查出来")
                rows.append({"pmcid": pmcid, "kind": kind, "condition": cfg["name"],
                             "verdict": "INVALID", "why": why, **{
                                 k: t[k] for k in
                                 ("tool_calls", "references_read", "scripts_executed")}})
                continue
            v = judge(truth, review, a.model, d)
            rows.append({"pmcid": pmcid, "kind": kind, "condition": cfg["name"],
                         "verdict": v, "review_chars": len(review),
                         "tool_calls": t["tool_calls"],
                         "references_read": t["references_read"],
                         "scripts_executed": t["scripts_executed"]})
            print(f"    {v}  意见 {len(review)} 字符  工具 {t['tool_calls']} 次  "
                  f"读规则 {len(t['references_read'])}  跑脚本 {len(t['scripts_executed'])}")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"rows": rows}, open(a.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"{'条件':24s} {'命中':>8s} {'INVALID':>8s} {'平均跑脚本':>10s}")
    for c in a.conditions:
        n = CONDITIONS[c]["name"]
        sub = [r for r in rows if r["condition"] == n]
        hit = sum(1 for r in sub if r["verdict"] == "HIT")
        inv = sum(1 for r in sub if r["verdict"] == "INVALID")
        sc = sum(len(r.get("scripts_executed") or []) for r in sub) / max(len(sub), 1)
        print(f"  {n:22s} {hit:3d}/{len(sub):<4d} {inv:8d} {sc:10.1f}")
    print(f"\n结果写入 {a.out}")
    print("\n最关键的一行比较是 discovery_plus_tools 与 hierarchical_skill：")
    print("  两者接近 → 规则库贡献有限，应当裁剪；hierarchical 明显更高 → 规则库有真实价值。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

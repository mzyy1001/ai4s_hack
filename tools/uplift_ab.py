#!/usr/bin/env python3
"""Uplift 消融基线测量工具（可复现）。

评审的最高权重维度（30%「可完成性与工程质量」）判的是
**同任务、同模型下，挂本 skill 比裸模型提升了多少**。
这个脚本把那次测量变成可重复执行的流程，而不是一次性手工比对。

做法：造两个**除 skill 外完全相同**的临时目录，跑同一条指令，
把两份输出并排存下来，并给出可比的粗粒度指标。

    python3 tools/uplift_ab.py --paper datasets/papers/<slot>/fulltext.xml
    python3 tools/uplift_ab.py --paper <p> --prompt "自定义指令" --model openai/gpt-5.6-sol

**这个脚本不自动判定质量。** 发现数量只是粗指标 —— 合并同类项会让
条数变少但质量不降。最终必须人工读两份输出。脚本的价值在于
让这件事可复现、可回归，而不是给一个假装客观的分数。

前置：环境里要有 OPENAI_API_KEY（或所选 provider 的凭据）与 opencode。
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_SRC = os.path.join(REPO, "skills", "biomed-paper-review")

DEFAULT_PROMPT = (
    "审阅 paper.xml 这篇论文的统计学方法与伦理合规，指出你发现的问题。"
    "每条问题必须给出论文中的具体出处。控制在 50 行内。"
)


def build_env(root, paper, with_skill):
    """造一个只差 skill 的运行目录。"""
    d = os.path.join(root, "withskill" if with_skill else "baseline")
    os.makedirs(d, exist_ok=True)
    shutil.copy(paper, os.path.join(d, "paper.xml"))
    if with_skill:
        dst = os.path.join(d, ".opencode", "skill")
        os.makedirs(dst, exist_ok=True)
        shutil.copytree(SKILL_SRC, os.path.join(dst, "biomed-paper-review"),
                        dirs_exist_ok=True)
    return d


def run_opencode(cwd, prompt, model, timeout):
    cmd = ["opencode", "run"]
    if model:
        cmd += ["--model", model]
    cmd.append(prompt)
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout)
        return r.stdout + ("\n[STDERR]\n" + r.stderr if r.stderr.strip() else "")
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except FileNotFoundError:
        return "[opencode 不可用]"


# 粗指标：编号条目、出处引用、是否执行了脚本
RE_NUMBERED = re.compile(r"^\s*(?:\d+[.、)]|[-*]\s+\*\*)", re.M)
RE_LOCATOR = re.compile(r"paper\.xml:\d+|`sec\d+`|Table\s*\d|图\s*\d")
RE_RAN_SCRIPT = re.compile(r"python3 -c|--selftest|statistical_forensics|"
                           r"ethics_compliance_check|sequence_identifier_audit|"
                           r"normalize_biomed_units|figure_integrity_audit")


def metrics(text):
    return {
        "编号条目数": len(RE_NUMBERED.findall(text)),
        "出处引用数": len(RE_LOCATOR.findall(text)),
        "执行过确定性脚本": bool(RE_RAN_SCRIPT.search(text)),
        "输出字符数": len(text),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True, help="论文文件（JATS XML 或纯文本）")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--model", default="openai/gpt-5.6-sol",
                    help="官方统一模型为 GLM / Kimi 系列；正式自测应改用该系列")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--outdir", default=None, help="保存两份输出的目录")
    args = ap.parse_args()

    paper = os.path.abspath(args.paper)
    if not os.path.exists(paper):
        print(f"找不到论文：{paper}")
        return 2

    root = args.outdir or tempfile.mkdtemp(prefix="uplift_")
    os.makedirs(root, exist_ok=True)
    print(f"工作目录：{root}\n模型：{args.model}\n论文：{os.path.basename(paper)}\n")

    results = {}
    for with_skill in (False, True):
        label = "挂 skill" if with_skill else "裸模型基线"
        d = build_env(root, paper, with_skill)
        print(f"[{label}] 运行中 …")
        out = run_opencode(d, args.prompt, args.model, args.timeout)
        path = os.path.join(root, ("withskill" if with_skill else "baseline") + ".out.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(out)
        results[label] = (out, path)
        print(f"[{label}] 输出已存至 {path}")

    print("\n" + "=" * 62)
    print("粗指标对照（**不是质量判定**，最终必须人工读两份输出）")
    print("=" * 62)
    keys = list(metrics(results["裸模型基线"][0]).keys())
    b = metrics(results["裸模型基线"][0])
    s = metrics(results["挂 skill"][0])
    print(f"{'指标':<20}{'裸模型':>12}{'挂 skill':>12}{'差值':>10}")
    for k in keys:
        bv, sv = b[k], s[k]
        if isinstance(bv, bool):
            print(f"{k:<20}{str(bv):>12}{str(sv):>12}{'':>10}")
        else:
            print(f"{k:<20}{bv:>12}{sv:>12}{sv - bv:>+10}")

    print("\n判读提示：")
    print("  · 编号条目数下降**不必然**是退步 —— 合并同类项也会让条数变少。")
    print("  · 但若挂 skill 后的发现是裸模型的**真子集**，就是实打实的负 uplift。")
    print("  · 「执行过确定性脚本」为 False 时，本 skill 的主要增量来源没有生效。")
    print(f"\n并排比对：\n  diff -y {results['裸模型基线'][1]} {results['挂 skill'][1]} | less")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""在**真实论文**上跑 A/B：裸模型 vs 挂 Skill，标准答案来自权威数据库。

与旧的植入式基准的区别
----------------------
旧做法是把已知错误写进一篇干净论文再问模型能不能找出来。两轮都饱和 ——
模型是在**挑外来物**，不是在审稿（详见 tools/fetch_ground_truth_papers.py 的说明）。

这里换成真实论文：错误长在论文自己的血肉里，骗过了真实的同行评审，
标准答案由 Cellosaurus 给出而不是我们编的。

判定只问一件事：**审稿意见有没有指出标准答案里那个问题。**

用法
----
    python3 tools/fetch_ground_truth_papers.py --cell-line MDA-MB-435 --limit 5
    python3 tools/real_paper_benchmark.py --corpus datasets/ground_truth

    # 只看某一篇
    python3 tools/real_paper_benchmark.py --corpus datasets/ground_truth --only PMC12572395
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys

REVIEW_PROMPT = (
    "你是资深同行评审。请审阅当前目录下的论文（fulltext.xml），"
    "列出你认为存在的所有问题，按严重程度排序。"
    "对每一条说明：问题是什么、依据在论文的哪个位置、为什么重要。"
)

JUDGE_PROMPT = """你是评审的裁判。下面给你一条**标准答案**和一份**审稿意见**。

标准答案（由权威来源给出的客观事实）：
{truth}

审稿意见：
---
{review}
---

问题：这份审稿意见有没有指出标准答案里说的那个问题？

判定标准（**从严**）：
- 必须实质性地指出**这个具体对象**的事实本身有问题
- 只是提到相关名词（细胞系名、注册号、某篇参考文献）**不算**命中
- 泛泛的通用建议不算命中，例如「建议补充细胞系 STR 鉴定」
  「建议核对注册信息」「建议复核统计方法」—— 这类话几乎每份意见都会写
- 必须触及标准答案指出的那个**具体事实**（身份错了 / 注册晚于开始 /
  该文献已撤稿 / 该统计结论不成立）

只回答一个词：HIT 或 MISS。"""


def run_opencode(cwd, prompt, model=None, timeout=5400):
    """跑一次 opencode。

    两个必须注意的点，都是实际踩出来的：
    1. **opencode 忽略 subprocess 的 cwd**，必须显式传 --dir，
       否则两臂都在仓库根目录跑，裸模型那臂也会加载到 skill，就不是基线了。
    2. `subprocess.run(timeout=)` 只杀直接子进程；opencode 派生的孙进程
       会继续持有管道，父进程永远阻塞。必须独立进程组 + killpg。
    """
    if not shutil.which("opencode"):
        return "[opencode 不可用]"
    cmd = ["opencode", "run", "--dir", cwd]
    if model:
        cmd += ["--model", model]
    cmd.append(prompt)
    try:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True,
                             start_new_session=True)
    except FileNotFoundError:
        return "[opencode 不可用]"
    try:
        out, err = p.communicate(timeout=timeout)
        return out + (("\n" + err) if err and err.strip() else "")
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
        return f"[TIMEOUT] 超过 {timeout} 秒未返回，已杀掉整个进程组。"


def review_is_valid(text):
    """审阅是否真的跑起来了。

    **这是整个基准最重要的一道闸。** 调用失败绝不能记作「没查出来」——
    那是我们没问到，不是模型没查出来。与契约里 parse_failed != not_reported 同理。
    """
    if not text or len(text.strip()) < 400:
        return False, f"输出过短（{len(text or '')} 字符）"
    for marker in ("[opencode 不可用]", "[TIMEOUT]", "0 matches",
                   "error:", "Error:", "ProviderAuthError", "usage limit"):
        if marker in text:
            return False, f"输出含错误标记 {marker!r}"
    return True, ""


def setup_arms(paper_dir, workroot, skill_src):
    """搭两个只差一个变量的工作目录。"""
    arms = {}
    for arm in ("baseline", "withskill"):
        d = os.path.join(workroot, arm)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        shutil.copy(os.path.join(paper_dir, "fulltext.xml"),
                    os.path.join(d, "fulltext.xml"))
        if arm == "withskill":
            dst = os.path.join(d, ".claude", "skills")
            os.makedirs(dst, exist_ok=True)
            shutil.copytree(skill_src, os.path.join(dst, "biomed-paper-review"))
        arms[arm] = d
    return arms


def judge(truth, review, model, cwd):
    out = run_opencode(cwd, JUDGE_PROMPT.format(truth=truth, review=review),
                       model=model, timeout=900)
    if "HIT" in out.upper() and "MISS" not in out.upper():
        return "HIT"
    if "MISS" in out.upper():
        return "MISS"
    return "UNPARSEABLE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="datasets/ground_truth")
    ap.add_argument("--only", help="只跑某一个 PMCID")
    ap.add_argument("--model", default="dashscope/qwen3.8-max")
    ap.add_argument("--judge-model", default="dashscope/qwen3.8-max")
    ap.add_argument("--timeout", type=int, default=5400,
                    help="单臂审阅超时秒数。这是**死锁上限**，不是工作预算 —— "
                         "设太小会杀掉正常的慢速审阅，制造出假的负 uplift")
    ap.add_argument("--work", default=os.environ.get("CLAUDE_JOB_DIR", "/tmp") + "/rpb")
    a = ap.parse_args()

    root = os.path.abspath(a.corpus)
    idx = os.path.join(root, "index.json")
    if not os.path.isfile(idx):
        print(f"找不到语料索引 {idx}\n先跑：python3 tools/fetch_ground_truth_papers.py")
        return 2
    papers = json.load(open(idx, encoding="utf-8"))["papers"]
    if a.only:
        papers = [p for p in papers if p["pmcid"] == a.only]
    if not papers:
        print("语料为空")
        return 2

    skill_src = os.path.abspath("skills/biomed-paper-review")
    os.makedirs(a.work, exist_ok=True)
    results = []

    for p in papers:
        pmcid = p["pmcid"]
        truth = p["ground_truth"]["expected_finding"]
        print(f"\n=== {pmcid} {(p.get('title') or '')[:60]} ===")
        print(f"标准答案：{truth[:120]}")

        arms = setup_arms(os.path.join(root, pmcid),
                          os.path.join(a.work, pmcid), skill_src)
        row = {"pmcid": pmcid, "kind": p.get("kind", "?")}
        for arm, d in arms.items():
            print(f"  [{arm}] 审阅中 …")
            review = run_opencode(d, REVIEW_PROMPT, model=a.model, timeout=a.timeout)
            ok, why = review_is_valid(review)
            with open(os.path.join(d, "review.md"), "w", encoding="utf-8") as fh:
                fh.write(review or "")
            if not ok:
                print(f"  [{arm}] **审阅调用失败：{why}** —— 本次作废")
                print("  不得把这种情况记作「没查出来」：那是我们没问到。")
                return 1
            v = judge(truth, review, a.judge_model, d)
            row[arm] = v
            print(f"  [{arm}] {v}（意见 {len(review)} 字符）")
        results.append(row)

    print("\n" + "=" * 66)
    b = sum(1 for r in results if r.get("baseline") == "HIT")
    w = sum(1 for r in results if r.get("withskill") == "HIT")
    n = len(results)
    print(f"裸模型命中 {b}/{n}    挂 Skill 命中 {w}/{n}    uplift = {w - b:+d}")
    # **按错误类型看，不要只看总分** —— 总分只说明有没有用，
    # 分类型才说明哪里有用，而裸模型本来就会的那几类应该从 Skill 里删掉
    print(f"\n{'kind':30s} {'pmcid':14s} {'baseline':10s} withskill")
    for r in sorted(results, key=lambda x: x["kind"]):
        print(f"  {r['kind']:28s} {r['pmcid']:14s} "
              f"{str(r.get('baseline')):10s} {r.get('withskill')}")

    print("\n按类型汇总：")
    kinds = {}
    for r in results:
        k = kinds.setdefault(r["kind"], {"b": 0, "w": 0, "n": 0})
        k["n"] += 1
        k["b"] += r.get("baseline") == "HIT"
        k["w"] += r.get("withskill") == "HIT"
    for kind, k in sorted(kinds.items()):
        print(f"  {kind:28s} 裸模型 {k['b']}/{k['n']}  挂 Skill {k['w']}/{k['n']}  "
              f"uplift {k['w'] - k['b']:+d}")
    if n < 5:
        print(f"\n注意：只有 {n} 篇，样本太小，差值不足以下结论。至少跑 20 篇。")

    out = os.path.join(a.work, "results.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"results": results, "baseline_hits": b, "withskill_hits": w,
                   "n": n}, fh, ensure_ascii=False, indent=2)
    print(f"\n结果写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

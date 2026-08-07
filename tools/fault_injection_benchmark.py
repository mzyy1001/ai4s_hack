#!/usr/bin/env python3
"""植入式 A/B 基准：往真实论文里埋已知错误，比较裸模型与挂 skill 各能查出几条。

为什么这样测才对
----------------
之前的 `uplift_ab.py` 比的是两份**自由文本**审稿意见，谁多谁少要靠人读，
主观且不可复现。本脚本改成**有标准答案**的测法：

    干净论文 → 植入 N 条已知错误 → 分别跑裸模型与挂 skill
             → 逐条判定「这条错误被发现了吗」
             → uplift = 挂 skill 命中数 − 裸模型命中数

好处：
- **有 ground truth**，不用人读也能出数
- uplift 是**差值**，植入方式带来的系统性偏差对两臂**同等作用**，会被差掉
- 可以看**逐条**差异：到底是哪一类错误只有挂 skill 才查得出来

用法
----
    source ~/.config/qwen/credentials.env
    python3 tools/fault_injection_benchmark.py \\
        --paper datasets/papers/omics_heatmap__journal.pone.0338705/fulltext.xml \\
        --model qwen3.8-max

    # 只植入部分错误、跑多轮取中位数
    python3 tools/fault_injection_benchmark.py --paper <p> --only stat. seq. --repeats 3

前置：opencode 可用；skill 在 skills/biomed-paper-review/。
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL_SRC = os.path.join(REPO, "skills", "biomed-paper-review")
FAULTS = os.path.join(HERE, "probe_cases", "fault_library.json")

sys.path.insert(0, HERE)
import baseline_probe as bp  # noqa: E402

REVIEW_PROMPT = (
    "你是资深生物医药论文审稿人。请审阅 paper.md 这篇论文，"
    "指出你发现的**所有**问题（统计学、方法学、报告规范、伦理、图表、结论等）。"
    "逐条列出，每条给出具体依据与出处。不要客套。"
)

JUDGE = (
    "下面是一份审稿意见，以及一个具体的问题描述。\n"
    "判断：这份意见**是否明确指出了**该问题？实质说到即算 YES，措辞不必相同；\n"
    "只泛泛提到相关章节、或只说「建议核对」而没点出该具体问题，算 NO。\n\n"
    "【问题描述】\n{fault}\n\n【审稿意见】\n{review}\n\n"
    "先输出一行 VERDICT: YES 或 VERDICT: NO，再用一句话说明理由。"
)


def build_paper(host_text, faults):
    """把错误植入宿主论文。

    两种植入方式：
      replace —— 把 `find` 替换成 `faulty`（用于改动已有内容，最自然）
      append  —— 在正文约 position 处插入一段（用于加入新的错误陈述）
    """
    text = host_text
    applied = []
    for f in faults:
        inj = f["inject"]
        if inj["mode"] == "replace":
            if inj["find"] in text:
                text = text.replace(inj["find"], inj["faulty"], 1)
                applied.append(f)
        elif inj["mode"] == "append":
            lines = text.split("\n")
            marks = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
            pos = inj.get("position", 0.6)
            cut = (marks[min(len(marks) - 1, max(1, int(len(marks) * pos)))]
                   if marks else int(len(lines) * pos))
            lines = lines[:cut] + ["", inj["faulty"].strip(), ""] + lines[cut:]
            text = "\n".join(lines)
            applied.append(f)
    return text, applied


def make_env(root, name, paper_text, with_skill):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "paper.md"), "w", encoding="utf-8") as fh:
        fh.write(paper_text)
    if with_skill:
        dst = os.path.join(d, ".opencode", "skill")
        os.makedirs(dst, exist_ok=True)
        shutil.copytree(SKILL_SRC, os.path.join(dst, "biomed-paper-review"),
                        dirs_exist_ok=True)
    return d


# opencode 失败时会把错误 JSON 打到 stdout，长度很短。
# 正常的审稿意见至少有几百字符且含条目结构。
MIN_REVIEW_CHARS = 400
ERROR_MARKERS = ("[TIMEOUT]", "[opencode 不可用]", '"name": "UnknownError"',
                 '"name":"UnknownError"', "Error: {", "usage limit",
                 "rate limit", "Unexpected server error",
                 # 没读到论文 = 跑错目录了，也算无效
                 '"**/paper.md" 0 matches', "0 matches")


def review_is_valid(text):
    """判断这份「审稿意见」是不是真的审稿意见。

    **审阅调用失败绝不能当成「什么都没发现」** —— 那是我们没问到，
    不是模型没查出来。与契约里 parse_failed != not_reported 同理。
    """
    if not text or len(text.strip()) < MIN_REVIEW_CHARS:
        return False, f"输出仅 {len(text.strip())} 字符，短于 {MIN_REVIEW_CHARS}"
    for m in ERROR_MARKERS:
        if m in text:
            return False, f"输出含错误标记 {m!r}"
    return True, ""


def run_opencode(cwd, model, timeout):
    """跑一次审阅。

    **必须用 `--dir` 指定目录，不能只靠 subprocess 的 cwd** ——
    opencode 会自己解析「项目目录」，忽略进程 cwd。踩过一次：
    两臂都跑到了仓库根，baseline 臂甚至因此加载了仓库里的 skill，
    根本不是基线；而 paper.md 不在那儿，等于两臂什么都没审。
    """
    cmd = ["opencode", "run", "--dir", cwd]
    if model:
        cmd += ["--model", model]
    cmd.append(REVIEW_PROMPT)

    # 用独立进程组 + killpg：subprocess.run(timeout=) 只杀直接子进程，
    # opencode 派生的孙进程会继续持有管道，父进程在 communicate() 上永远阻塞。
    # 实测踩过：设了 40 分钟超时，实际跑了 77 分钟也没被杀。
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
        return (f"[TIMEOUT] 超过 {timeout} 秒未返回，已杀掉整个进程组。\n"
                f"常见原因：笔记本睡眠导致经本地代理的连接静默失效 —— "
                f"socket 仍是 ESTABLISHED，但对端早断了。")


def judge_all(review, faults, key, base, model):
    """逐条判定这份意见是否命中。返回 {fault_id: True/False/None}。None = 判定失败。"""
    out = {}
    for f in faults:
        v = bp.chat(key, base, model, JUDGE.format(fault=f["description"],
                                                   review=review),
                    max_tokens=300, temperature=0.0)
        if v.startswith(("[HTTP", "[ERROR]")):
            out[f["id"]] = None          # 判定失败，不计入 —— 不是「没查出来」
        else:
            out[f["id"]] = bool(re.search(r"VERDICT:\s*YES", v, re.I))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True, help="干净的宿主论文（JATS XML 或 .md）")
    ap.add_argument("--model", default="qwen3.8-max")
    ap.add_argument("--judge-model", default=None, help="默认与 --model 相同")
    ap.add_argument("--base", default=bp.DEFAULT_BASE)
    ap.add_argument("--only", nargs="*", default=None, help="只植入 id 以此开头的错误")
    ap.add_argument("--timeout", type=int, default=900,
                    help="单臂审阅超时秒数。正常几分钟即可完成；设太大时卡住会白等很久")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--keep-paper", action="store_true", help="保存植入后的论文供人工核对")
    a = ap.parse_args()

    key = bp.load_key()
    if not key:
        print("找不到 DASHSCOPE_API_KEY"); return 2
    judge_model = a.judge_model or a.model

    # 宿主
    paper = os.path.abspath(a.paper)
    if paper.endswith(".xml"):
        mk = os.path.join(HERE, "make_host_paper.py")
        host = subprocess.run([sys.executable, mk, paper, "--max-chars", "26000"],
                              capture_output=True, text=True).stdout
    else:
        host = open(paper, encoding="utf-8").read()

    with open(FAULTS, encoding="utf-8") as fh:
        lib = json.load(fh)["faults"]
    if a.only:
        lib = [f for f in lib if any(f["id"].startswith(p) for p in a.only)]

    faulty_text, applied = build_paper(host, lib)
    if not applied:
        print("没有任何错误被成功植入（检查 fault_library 的 find 串是否匹配宿主）")
        return 1

    root = a.outdir or tempfile.mkdtemp(prefix="faultbench_")
    os.makedirs(root, exist_ok=True)
    if a.keep_paper:
        with open(os.path.join(root, "paper_with_faults.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(faulty_text)

    print(f"宿主：{os.path.basename(paper)}（{len(host)} 字符）")
    print(f"成功植入 {len(applied)}/{len(lib)} 条错误")
    print(f"审阅模型：{a.model}  裁判模型：{judge_model}")
    print(f"工作目录：{root}\n")

    results = {}
    for arm, with_skill in (("裸模型基线", False), ("挂 skill", True)):
        d = make_env(root, "withskill" if with_skill else "baseline",
                     faulty_text, with_skill)
        print(f"[{arm}] 审阅中 …")
        review = run_opencode(d, a.model, a.timeout)
        out_path = os.path.join(root, ("withskill" if with_skill else "baseline")
                                + ".out.md")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(review)

        ok, why = review_is_valid(review)
        if not ok:
            print(f"\n[{arm}] **审阅调用失败：{why}**")
            print(f"    输出已存至 {out_path}")
            print("\n" + "=" * 74)
            print("本次基准作废 —— 审阅没有真正跑起来。")
            print("**不得**把这种情况记作「两臂都没查出来」：")
            print("那是我们没问到，不是模型没查出来")
            print("（与契约里 parse_failed != not_reported 同理）。")
            print("\n常见原因：opencode 服务端错误、模型配额用尽、超时。")
            print("修好后重跑；不要据此下任何 uplift 结论。")
            return 3

        print(f"[{arm}] 审阅有效（{len(review)} 字符），逐条判定 …")
        results[arm] = judge_all(review, applied, key, a.base, judge_model)

    # ---- 报表 ----
    print("\n" + "=" * 74)
    print(f"{'错误':<38}{'裸模型':>10}{'挂 skill':>12}")
    print("-" * 74)
    b_hit = s_hit = valid = 0
    only_skill, only_base = [], []
    for f in applied:
        b = results["裸模型基线"].get(f["id"])
        s = results["挂 skill"].get(f["id"])
        if b is None or s is None:
            mark_b = mark_s = "判定失败"
        else:
            valid += 1
            b_hit += 1 if b else 0
            s_hit += 1 if s else 0
            mark_b = "✓" if b else "✗"
            mark_s = "✓" if s else "✗"
            if s and not b:
                only_skill.append(f["id"])
            if b and not s:
                only_base.append(f["id"])
        print(f"{f['id']:<38}{mark_b:>10}{mark_s:>12}")

    print("-" * 74)
    print(f"{'命中数（有效 ' + str(valid) + ' 条）':<38}{b_hit:>10}{s_hit:>12}")
    uplift = s_hit - b_hit
    print(f"\n**uplift = {uplift:+d}**  "
          f"（{b_hit}/{valid} → {s_hit}/{valid}）")
    if only_skill:
        print(f"\n只有挂 skill 查出来的（**这是 skill 的真实价值**）：")
        for i in only_skill:
            print(f"  + {i}")
    if only_base:
        print(f"\n只有裸模型查出来的（**skill 反而挡住了发现，要修**）：")
        for i in only_base:
            print(f"  - {i}")
    if not only_skill and not only_base:
        if b_hit == 0 and s_hit == 0:
            print("\n**两臂均 0 命中 —— 高度可疑。**")
            print("植入的错误是刻意加进去的，比天然错误显眼；"
                  "裸模型在真实论文上都能报出十几条问题，")
            print("两臂同时 0 命中通常意味着**审阅或裁判没真正跑起来**，"
                  "而不是「都没查出来」。")
            print("请先人工打开两份 .out.md 确认里面确实是审稿意见。")
        else:
            print("\n两臂完全一致 —— skill 既没加分也没减分。")

    print(f"\n两份完整意见：\n  {root}/baseline.out.md\n  {root}/withskill.out.md")
    print("\n注意：植入方式会让绝对命中率偏高（错误是刻意加进去的，比天然错误显眼），")
    print("但 uplift 是**差值**，这个偏差对两臂同等作用，会被差掉。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

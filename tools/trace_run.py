#!/usr/bin/env python3
"""跑单篇论文的两臂并**完整记录过程**，产出可供人工分析的 Markdown。

与 `real_paper_benchmark.py` 的分工
----------------------------------
- `real_paper_benchmark.py` 只关心结果：命中还是没命中，出一张 uplift 表。
- 本脚本关心**过程**：挂 Skill 那一臂到底读了哪些 reference、跑了哪些脚本、
  拿到了什么 signal、最后怎么下的结论。用来回答「uplift 是从哪儿来的」
  以及更重要的「没 uplift 的时候，它到底卡在哪一步」。

用 `opencode run --format json` 拿原始事件流，把工具调用逐条还原。

用法
----
    python3 tools/trace_run.py --pmcid PMC3742493
    python3 tools/trace_run.py --pmcid PMC13254492 --out docs/traces
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys

REVIEW_PROMPT = (
    "你是资深同行评审。请审阅当前目录下的论文（fulltext.txt），"
    "列出你认为存在的所有问题，按严重程度排序。"
    "对每一条说明：问题是什么、依据在论文的哪个位置、为什么重要。"
)


def run_json(cwd, prompt, model, timeout):
    """跑一次 opencode，返回 (事件列表, 原始输出)。

    `--format json` 输出的是逐行 JSON 事件。解析失败的行原样保留 ——
    **不得**因为解析不了就当作没发生过。
    """
    cmd = ["opencode", "run", "--dir", cwd, "--model", model,
           "--format", "json", prompt]
    try:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True,
                             start_new_session=True)
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

    raw = out + (("\n" + err) if err and err.strip() else "")
    events = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"_unparsed": line[:400]})
    return events, raw


def walk(obj, hit):
    """递归找工具调用与助手文本。

    实测事件形状：外层 {"type":"tool_use", "part":{...}}，
    真正带工具名与参数的是内层 part：{"type":"tool","tool":"read",
    "state":{"input":{...},"output":"..."}}。
    只认内层，否则同一次调用会被外层重复计一次。
    """
    if isinstance(obj, dict):
        if isinstance(obj.get("tool"), str) and isinstance(obj.get("state"), dict):
            hit["tools"].append(obj)
        if obj.get("type") == "text" and isinstance(obj.get("text"), str):
            hit["texts"].append(obj["text"])
        for v in obj.values():
            walk(v, hit)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, hit)


def summarize(events):
    hit = {"tools": [], "texts": []}
    walk(events, hit)
    calls = []
    for t in hit["tools"]:
        st = t.get("state") or {}
        args = st.get("input") or {}
        # 只留人能看懂的关键参数，别把整份文件内容塞进表格
        brief = {k: v for k, v in args.items()
                 if k in ("filePath", "command", "pattern", "path", "query",
                          "description", "prompt")}
        calls.append((t["tool"],
                      json.dumps(brief or args, ensure_ascii=False)[:300],
                      st.get("status")))
    return calls, hit["texts"]


REF_FILES = ["00-contracts", "01-structured-extraction", "02-macro-logic",
             "03-experimental-methods", "04-statistics", "05-figures-and-charts",
             "06-ethics-compliance", "07-conclusions-discussion"]
SCRIPT_FILES = ["normalize_biomed_units", "statistical_forensics",
                "ethics_compliance_check", "sequence_identifier_audit",
                "figure_integrity_audit", "external_figure_validation"]
STAGE_WORDS = ["Stage 0", "Stage 1", "Stage 2", "Stage 3b", "Stage 3c", "Stage 3",
               "Stage 4", "Stage 5", "M1", "M2", "M3", "M4", "M5", "M6", "M7"]


def coverage(calls, review):
    """这一趟到底把 Skill 用起来了多少。

    这是回答「一篇论文是不是把所有阶段和所有 reference 都跑到了」的依据 ——
    光看最终意见看不出来，必须看它实际读了哪些文件、跑了哪些脚本。
    """
    blob = " ".join(a for _, a, _ in calls)
    read_refs = [r for r in REF_FILES if r in blob]
    ran_scripts = [x for x in SCRIPT_FILES if x in blob]
    # 脚本必须是被**执行**（bash）而不只是被读（read）
    exec_blob = " ".join(a for n, a, _ in calls if n in ("bash", "shell", "run"))
    truly_ran = [x for x in SCRIPT_FILES if x in exec_blob]
    mentioned_stages = [w for w in STAGE_WORDS if w in (review or "")]
    return {"read_refs": read_refs, "ran_scripts": ran_scripts,
            "truly_ran": truly_ran, "stages": mentioned_stages}


def render(pmcid, meta, arms, out_path):
    truth = meta["ground_truth"]
    L = []
    A = L.append
    A(f"# 审阅过程记录 · {pmcid}")
    A("")
    A(f"> **论文**：{meta.get('title')}  ")
    A(f"> **期刊 / 年份**：{meta.get('journal')} · {meta.get('year')}  ")
    A(f"> **错误类型**：`{meta['kind']}`  ")
    A(f"> **标准答案出题人**：{truth.get('source', '权威数据库')}")
    A("")
    A("## 标准答案")
    A("")
    A(f"{truth['expected_finding']}")
    A("")
    A("判定只问一件事：审稿意见有没有**实质性**指出这个问题。"
      "只提到名词、或给「建议核对一下」这类通用建议，都不算命中 —— "
      "那种话几乎每份意见都会写，算进去 uplift 就被稀释没了。")
    A("")

    for arm in ("baseline", "withskill"):
        d = arms.get(arm)
        if not d:
            continue
        A("---")
        A("")
        A(f"## {'裸模型（baseline）' if arm == 'baseline' else '挂 Skill（withskill）'}")
        A("")
        calls, texts = d["calls"], d["texts"]
        A(f"**工具调用 {len(calls)} 次**")
        A("")
        if calls:
            A("| # | 工具 | 参数（截断） | 状态 |")
            A("| --- | --- | --- | --- |")
            for i, (n, a, st) in enumerate(calls, 1):
                a = a.replace("|", "\\|").replace("\n", " ")
                A(f"| {i} | `{n}` | {a[:170]} | {st or ''} |")
        else:
            A("_未捕获到工具调用_")
        A("")
        skill_hits = [n for n, a, _ in calls
                      if "scripts/" in a or "biomed-paper-review" in a]
        if arm == "withskill":
            cov = coverage(calls, d["review"])
            A("### Skill 覆盖面")
            A("")
            A(f"- **读了 {len(cov['read_refs'])}/8 个 reference**："
              + (", ".join(f"`{r}`" for r in cov["read_refs"]) or "**一个都没读**"))
            A(f"- **执行了 {len(cov['truly_ran'])}/6 个脚本**："
              + (", ".join(f"`{r}`" for r in cov["truly_ran"]) or "**一个都没执行**"))
            if cov["ran_scripts"] and not cov["truly_ran"]:
                A("  - ⚠️ 脚本只被**读取**未被**执行** —— "
                  "这正是 SKILL.md §6.5「要运行，不要只读」要防的情况，"
                  "读源码对结论毫无贡献")
            A(f"- **意见中提及的阶段/模块**："
              + (", ".join(cov["stages"]) or "无"))
            A("")
            if "external_figure_validation" not in cov["truly_ran"]:
                A("> ⚠️ **X1 外部核验未执行。** 细胞系污染、回顾性注册、"
                  "引用撤稿文献这几类**只有查外部库才可能发现**，"
                  "不跑 X1 就必然漏掉 —— 而这几类正是相对裸模型的主要增益来源。")
                A("")
            A(f"**其中调用 Skill 脚本的次数**：{len(skill_hits)}")
            if not skill_hits:
                A("")
                A("> ⚠️ **一次脚本都没跑。** 这是 uplift 为零的头号原因 —— "
                  "模型把 `scripts/` 当源码读而不执行。SKILL.md §6.5 专门写了"
                  "「要运行，不要只读」，若这里仍为 0，说明那段提示没起作用。")
            A("")
        A("### 最终审稿意见")
        A("")
        A("```markdown")
        A((d["review"] or "").strip()[:12000])
        A("```")
        A("")

    A("---")
    A("")
    A("## 待分析")
    A("")
    A("1. 挂 Skill 那臂**跑脚本了吗**？没跑就说明问题在执行层，不在规则层。")
    A("2. 跑了 X1 吗？`cell_line` / `retrospective_registration` 这两类"
      "**只有查外部库才可能命中**，没跑 X1 就必然 MISS。")
    A("3. 两臂意见的**重合度**有多高？若挂 Skill 只是把裸模型的意见重新组织了一遍，"
      "uplift 结构上就只能是零或负。")
    A("4. 挂 Skill 那臂有没有**漏掉裸模型提到的问题**？"
      "此前实测出现过挂 Skill 9 条、裸模型 15 条且是真子集的情况。")

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pmcid", required=True)
    ap.add_argument("--corpus", default="datasets/ground_truth")
    ap.add_argument("--out", default="docs/traces")
    ap.add_argument("--model", default="dashscope/qwen3.8-max")
    ap.add_argument("--timeout", type=int, default=5400)
    ap.add_argument("--work", default=os.environ.get("CLAUDE_JOB_DIR", "/tmp") + "/trace")
    a = ap.parse_args()

    meta_p = os.path.join(a.corpus, a.pmcid, "meta.json")
    if not os.path.isfile(meta_p):
        print(f"找不到 {meta_p}")
        return 2
    meta = json.load(open(meta_p, encoding="utf-8"))

    skill_src = os.path.abspath("skills/biomed-paper-review")
    os.makedirs(a.out, exist_ok=True)
    arms = {}

    for arm in ("baseline", "withskill"):
        d = os.path.join(a.work, a.pmcid, arm)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)
        shutil.copy(os.path.join(a.corpus, a.pmcid, "fulltext.txt"),
                    os.path.join(d, "fulltext.txt"))
        if arm == "withskill":
            dst = os.path.join(d, ".claude", "skills")
            os.makedirs(dst, exist_ok=True)
            shutil.copytree(skill_src, os.path.join(dst, "biomed-paper-review"))

        print(f"  [{arm}] 审阅中 …")
        events, raw = run_json(d, REVIEW_PROMPT, a.model, a.timeout)
        calls, texts = summarize(events)
        review = max(texts, key=len) if texts else raw
        with open(os.path.join(d, "raw.jsonl"), "w", encoding="utf-8") as fh:
            fh.write(raw)
        arms[arm] = {"calls": calls, "texts": texts, "review": review}
        print(f"  [{arm}] 工具调用 {len(calls)} 次，意见 {len(review)} 字符")

    out_path = os.path.join(a.out, f"{a.pmcid}-{meta['kind']}.md")
    render(a.pmcid, meta, arms, out_path)
    print(f"\n过程记录写入 {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

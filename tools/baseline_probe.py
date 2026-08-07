#!/usr/bin/env python3
"""基线探针：先问裸模型能不能查出来，再决定要不要实现。

**为什么要有这个东西**

评审看的是 uplift —— 挂 skill 比裸模型强多少。
所以「裸模型本来就能查出来的问题」，做进 skill 里贡献为零，
还会多花 token（负分）。反过来，裸模型查不出来的，才是值得投入的地方。

本轮之前的教训是实测出来的：同一篇论文，裸模型报了 15 条实质问题，
挂 skill 反而只有 9 条且是真子集。所以**新组件必须先过这道探针**：

    候选检查 → 用官方同族模型（Qwen）在含该错误的案例上跑开放式审稿
             → 裁判判定它是否指出了该错误
             → 多数命中 = 不值得实现；多数漏掉 = 值得实现

用法
----
    python3 tools/baseline_probe.py --case tools/probe_cases/table_sum.md \\
        --error "表 1 中分类计数之和 30 与声明的 n=28 不符"

    python3 tools/baseline_probe.py --case <f> --error <e> --repeats 3 --model qwen3.8-max

凭据取自 ~/.config/qwen/credentials.env 的 DASHSCOPE_API_KEY，
或环境变量 DASHSCOPE_API_KEY。只用标准库。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

DEFAULT_MODEL = "qwen3.8-max"
DEFAULT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
CRED = os.path.expanduser("~/.config/qwen/credentials.env")

REVIEW_PROMPT = (
    "你是资深生物医药论文审稿人。请审阅下面的论文片段，"
    "指出你发现的所有问题（统计学、方法学、报告规范、伦理、图表、结论等）。"
    "每条给出具体依据。不要客套，直接列问题。\n\n---\n\n{case}"
)

JUDGE_PROMPT = (
    "下面是一份审稿意见，以及一个具体的问题描述。\n"
    "请判断：这份审稿意见**是否明确指出了**该问题？\n"
    "只要意见中有任何一条实质上说到了这个问题就算 YES，措辞不必相同。\n"
    "只是泛泛提到相关章节、或只说「建议核对数据」而没点出该具体问题，算 NO。\n\n"
    "【问题描述】\n{error}\n\n"
    "【审稿意见】\n{review}\n\n"
    "先输出一行 VERDICT: YES 或 VERDICT: NO，再用一句话说明理由。"
)


def load_key():
    k = os.environ.get("DASHSCOPE_API_KEY")
    if k:
        return k
    if os.path.exists(CRED):
        with open(CRED, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("DASHSCOPE_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def chat(key, base, model, prompt, max_tokens=2000, temperature=0.3,
         timeout=600, retries=2):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode("utf-8")
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": "Bearer " + key,
                 "Content-Type": "application/json"})
    last = ""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read().decode("utf-8"))
            return d["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:200]
            last = f"[HTTP {e.code}] {body}"
            if e.code not in (429, 500, 502, 503, 504):
                return last
        except Exception as e:                               # noqa: BLE001
            last = f"[ERROR] {e}"
        if attempt < retries:
            time.sleep(5 * (attempt + 1))
    return last


def probe(case_text, error_desc, key, base, model, repeats):
    """返回 (hits, valid, failures, transcripts)。

    **调用失败绝不能算作「漏掉」** —— 那是我们没问到，不是模型没查出来。
    这与契约里 parse_failed != not_reported 是同一条原则。
    """
    hits, valid, failures, transcripts = 0, 0, 0, []
    for i in range(1, repeats + 1):
        review = chat(key, base, model, REVIEW_PROMPT.format(case=case_text))
        if review.startswith(("[HTTP", "[ERROR]")):
            failures += 1
            print(f"  第 {i} 次：调用失败（不计入判定）—— {review[:110]}")
            transcripts.append((review, "CALL_FAILED"))
            continue
        verdict_raw = chat(key, base, model,
                           JUDGE_PROMPT.format(error=error_desc, review=review),
                           max_tokens=300, temperature=0.0)
        if verdict_raw.startswith(("[HTTP", "[ERROR]")):
            failures += 1
            print(f"  第 {i} 次：裁判调用失败（不计入判定）")
            transcripts.append((review, verdict_raw))
            continue
        yes = bool(re.search(r"VERDICT:\s*YES", verdict_raw, re.I))
        valid += 1
        hits += 1 if yes else 0
        print(f"  第 {i} 次：{'命中' if yes else '漏掉'}  "
              f"（{verdict_raw.splitlines()[0][:60] if verdict_raw else ''}）")
        transcripts.append((review, verdict_raw))
    return hits, valid, failures, transcripts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, help="含该错误的论文片段文件")
    ap.add_argument("--error", required=True, help="该错误的具体描述（裁判据此判定）")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--repeats", type=int, default=3,
                    help="官方评测取 3 次中位数，这里默认同样跑 3 次")
    ap.add_argument("--save", default=None, help="保存完整对话的目录")
    args = ap.parse_args()

    key = load_key()
    if not key:
        print("找不到 DASHSCOPE_API_KEY（环境变量或 ~/.config/qwen/credentials.env）")
        return 2
    if not os.path.exists(args.case):
        print(f"找不到案例文件：{args.case}")
        return 2

    case_text = open(args.case, encoding="utf-8").read()
    print(f"案例：{args.case}")
    print(f"目标错误：{args.error}")
    print(f"模型：{args.model} × {args.repeats} 次\n")

    hits, valid, failures, transcripts = probe(case_text, args.error, key,
                                               args.base, args.model, args.repeats)

    print("\n" + "=" * 60)
    if valid == 0:
        print(f"结果：{args.repeats} 次全部调用失败，有效样本 0 → INCONCLUSIVE")
        print("建议：**不能据此下任何结论**。调用失败是我们没问到，"
              "不是模型查不出来 —— 与契约里 parse_failed != not_reported 同理。"
              "请检查网络/超时/配额后重跑。")
        print(json.dumps({"case": args.case, "error": args.error,
                          "model": args.model, "hits": hits, "valid": valid,
                          "failures": failures, "repeats": args.repeats,
                          "verdict": "INCONCLUSIVE"}, ensure_ascii=False))
        return 3
    if valid < args.repeats:
        print(f"注意：{failures} 次调用失败，仅 {valid} 次有效，判定基于有效样本。")

    ratio = hits / valid
    if ratio >= 0.5:
        verdict = "BASELINE_FINDS_IT"
        advice = ("裸模型多数情况下自己就能查出来 → **不要实现**。"
                  "做进 skill 贡献为零，还多花 token。")
    elif hits == 0:
        verdict = "BASELINE_MISSES_IT"
        advice = ("裸模型完全查不出来 → **值得实现**，这是 uplift 的来源。")
    else:
        verdict = "BASELINE_UNRELIABLE"
        advice = ("裸模型时对时错 → **值得实现**，确定性检查能把它变成稳定命中。")
    print(f"结果：{hits}/{valid} 有效命中（{failures} 次调用失败）→ {verdict}")
    print(f"建议：{advice}")

    if args.save:
        os.makedirs(args.save, exist_ok=True)
        base = os.path.splitext(os.path.basename(args.case))[0]
        for i, (rev, jud) in enumerate(transcripts, 1):
            with open(os.path.join(args.save, f"{base}.{i}.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(f"# 审稿意见\n\n{rev}\n\n# 裁判\n\n{jud}\n")
        print(f"完整对话已存至 {args.save}/")

    print(json.dumps({"case": args.case, "error": args.error,
                      "model": args.model, "hits": hits, "valid": valid,
                      "failures": failures, "repeats": args.repeats,
                      "verdict": verdict}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

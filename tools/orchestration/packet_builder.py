#!/usr/bin/env python3
"""语义证据索引与专家证据包。

**为什么必须是代码而不是模型判断**：上一版靠模型「记住哪些内容与本任务相关」，
实际结果是每个阶段都把全文再读一遍 —— 既浪费注意力，又让「专家只看自己那一包」
成为一句空话。索引和切包是确定性的检索问题，应当由代码做一次并复用。

索引建一次，支持按 section / paragraph_id / experiment_id / claim_id /
figure_id / table_id / reference_id / declaration 检索。
"""

import re

# 各证据包需要的章节。**刻意窄** —— 宁可少给也不要把全文塞进去，
# 缺材料会体现为 unresolved（可见），塞全文则会重演注意力被占满的老问题（不可见）。
PACKET_SECTIONS = {
    "statistics": ["methods", "results"],
    "methods": ["methods"],
    "figures": ["results", "methods"],
    "ethics": ["methods", "declarations"],
    "claims": ["results", "discussion", "conclusion", "abstract"],
    "cross_section": ["abstract", "methods", "results", "discussion", "conclusion"],
    "references": ["references"],
}

SECTION_PATTERNS = [
    ("abstract", r"^\s*(abstract|摘要)\b"),
    ("introduction", r"^\s*(introduction|background|引言|前言)\b"),
    ("methods", r"^\s*(methods?|materials?\s+and\s+methods?|方法|材料与方法)\b"),
    ("results", r"^\s*(results?|结果)\b"),
    ("discussion", r"^\s*(discussion|讨论)\b"),
    ("conclusion", r"^\s*(conclusions?|结论)\b"),
    ("declarations", r"^\s*(declarations?|ethics|funding|conflict|data availability|"
                     r"acknowledg|伦理|资助|利益冲突|数据可得性)\b"),
    ("references", r"^\s*(references?|bibliography|参考文献)\b"),
]

# 统计包要抓的行：带 p 值、置信区间、样本量、检验名
STAT_HINTS = re.compile(
    r"\bp\s*[<=>]|\bP\s*[<=>]|95%\s*CI|confidence interval|\bn\s*=\s*\d|"
    r"t-test|chi-?square|ANOVA|Mann-Whitney|Wilcoxon|regression|Kaplan|log-rank|"
    r"标准差|置信区间|样本量", re.I)
ETHICS_HINTS = re.compile(
    r"ethic|consent|IRB|institutional review|IACUC|Helsinki|approval|"
    r"registered|registration|NCT\d{8}|ChiCTR|伦理|知情同意|批件|注册", re.I)
FIG_HINTS = re.compile(r"\b(figure|fig\.?|table)\s*\d+|图\s*\d+|表\s*\d+", re.I)


class EvidenceIndex:
    """建一次，全程复用。每段落一个 id，按章节归类。"""

    def __init__(self, text):
        self.paragraphs = {}
        self.by_section = {}
        cur = "front"
        n = 0
        for raw in (text or "").split("\n"):
            line = raw.strip()
            if not line:
                continue
            for name, pat in SECTION_PATTERNS:
                if re.match(pat, line, re.I) and len(line) < 120:
                    cur = name
                    break
            n += 1
            pid = f"{cur}-p{n}"
            self.paragraphs[pid] = line
            self.by_section.setdefault(cur, []).append(pid)

    def section(self, name):
        return [(p, self.paragraphs[p]) for p in self.by_section.get(name, [])]

    def search(self, pattern, sections=None):
        out = []
        for sec, pids in self.by_section.items():
            if sections and sec not in sections:
                continue
            for p in pids:
                if pattern.search(self.paragraphs[p]):
                    out.append((p, self.paragraphs[p]))
        return out

    def stats(self):
        return {"paragraphs": len(self.paragraphs),
                "sections": {k: len(v) for k, v in self.by_section.items()}}


def _trim(pairs, limit):
    """按字符预算截断，并**显式记录截断了多少** ——
    静默截断会让下游把「没给它」误当成「稿件里没有」。"""
    out, used, dropped = [], 0, 0
    for pid, txt in pairs:
        if used + len(txt) > limit:
            dropped += 1
            continue
        out.append({"paragraph_id": pid, "text": txt})
        used += len(txt)
    return out, dropped


def build(kind, index, discovery, candidates, signals=None, budget=24000):
    """构建一个证据包。

    每包都带**轻量全局上下文**：没有它，专家会做出局部正确、整体荒谬的判断
    （例如不知道随访只有 48 小时就去评价安全性结论）。
    """
    dm = discovery or {}
    global_ctx = {
        "study_design": dm.get("study_design"),
        "paper_type": (dm.get("paper_map") or {}).get("paper_type"),
        "experiments": [e.get("experiment_id") for e in (dm.get("experiment_map") or [])],
        "n_total": dm.get("n_total"),
        "followup_duration": dm.get("followup_duration"),
        "registration_ids": (dm.get("paper_map") or {}).get("registration_ids", []),
    }

    secs = PACKET_SECTIONS.get(kind, ["methods", "results"])
    if kind == "statistics":
        pairs = index.search(STAT_HINTS, secs)
    elif kind == "ethics":
        pairs = index.search(ETHICS_HINTS, secs) + index.section("declarations")
    elif kind == "figures":
        pairs = index.search(FIG_HINTS, secs)
    elif kind == "references":
        pairs = index.section("references")
    elif kind == "claims":
        pairs = (index.section("conclusion") + index.section("abstract")
                 + index.section("discussion"))
    else:
        pairs = [x for s in secs for x in index.section(s)]

    # 去重保序
    seen, uniq = set(), []
    for p in pairs:
        if p[0] not in seen:
            seen.add(p[0])
            uniq.append(p)

    evidence, dropped = _trim(uniq, budget)
    return {
        "packet_id": f"PACKET-{kind.upper()}",
        "kind": kind,
        "global_context": global_ctx,
        "evidence": evidence,
        "evidence_truncated": dropped,
        "candidate_issues": candidates or [],
        "tool_signals": signals or [],
        "_note": ("这是本专家可见的**全部**稿件内容。若判断所需材料不在其中，"
                  "产出 unresolved 并说明缺什么，**不要**臆测，也不要当作稿件未写。"),
    }


def _selftest():
    ok = True

    def expect(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label}: got={got} want={want}")

    text = """Abstract
We studied 89 patients.

Methods
Patients with ASA I-III were included. Randomisation used sealed envelopes.
Statistical analysis used a two-tailed t-test with p < 0.05 considered significant.
The study was approved by the institutional review board; written informed consent
was obtained. Registered at ClinicalTrials.gov NCT01304069.

Results
Tumour volume differed between groups (t(10) = 2.228, P = 0.001, n = 12).
Table 1 shows baseline characteristics.

Discussion
No serious complications were observed.

Conclusion
This technique is safe.

References
1. Mehra MR et al. Lancet 2020.
"""
    idx = EvidenceIndex(text)
    expect("章节切分识别出 methods", "methods" in idx.by_section, True)
    expect("识别出 references", "references" in idx.by_section, True)

    disc = {"study_design": "randomised controlled trial", "followup_duration": "48 hours"}
    stat = build("statistics", idx, disc, [{"candidate_id": "CAND-001"}])
    joined = " ".join(e["text"] for e in stat["evidence"])
    expect("统计包抓到 p 值段落", "P = 0.001" in joined, True)
    expect("统计包不含结论段", "This technique is safe" in joined, False)
    expect("统计包带全局上下文",
           stat["global_context"]["followup_duration"], "48 hours")

    eth = build("ethics", idx, disc, [])
    ej = " ".join(e["text"] for e in eth["evidence"])
    expect("伦理包抓到注册号", "NCT01304069" in ej, True)

    clm = build("claims", idx, disc, [])
    cj = " ".join(e["text"] for e in clm["evidence"])
    expect("主张包含结论", "This technique is safe" in cj, True)
    expect("主张包不含统计方法细节", "two-tailed t-test" in cj, False)

    ref = build("references", idx, disc, [])
    expect("参考文献包非空", len(ref["evidence"]) > 0, True)

    print("\n全部通过" if ok else "\n存在失败项")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())

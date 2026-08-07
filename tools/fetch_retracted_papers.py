#!/usr/bin/env python3
"""抓取「后来被撤稿的论文 + 撤稿理由」，作为 A/B 基准的真实标准答案。

为什么这个比人工植入错误好
--------------------------
人工植入的错误躲不开两个破绽（我们都踩过）：

1. **语言/格式破绽** —— 中文段落插进英文论文，模型直接挑出「外来段落」
2. **主题破绽** —— 往纯生信论文里插动物实验、临床试验、毒理，
   模型第一句话就是「大量与研究主题无关的段落被插入」

结果是模型在**挑外来物**，不是在**审稿**，基准饱和（两臂都满分）。

真实撤稿论文没有这个问题：

- 错误**长在论文自己的血肉里**，没有任何外来痕迹
- 这些错误**骗过了真实的同行评审**，难度是真实的
- **撤稿声明就是标准答案**，由期刊和编辑给出，不是我们编的

用法
----
    python3 tools/fetch_retracted_papers.py --limit 20
    python3 tools/fetch_retracted_papers.py --limit 40 --out datasets/retracted

只用标准库。数据来自 Europe PMC 的公开 REST 接口（开放获取部分）。

**重要局限**：很多撤稿理由是图像重复、原始数据造假、作者署名争议 ——
这些**光看正文查不出来**。脚本会按理由分类，只把「文本可查」的挑出来做基准，
其余存下来但标注为不适用。这一步不做筛选，基准就会变成「不可能任务」。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"

# 撤稿理由分类。只有 text_detectable 的才适合做本项目的 A/B 基准。
REASON_PATTERNS = [
    ("text_detectable", [
        r"statistical", r"statistics", r"data inconsistenc", r"inconsisten",
        r"calculation", r"miscalculat", r"numerical error", r"incorrect analys",
        r"error in the analys", r"unreliable (data|results)", r"cannot be relied",
        r"errors in the (data|results|reporting)", r"reporting error",
        r"methodological (error|flaw|concern)", r"sample size",
        r"incorrect (data|values|numbers)", r"duplicate (data|values)",
    ]),
    ("image_forensics", [
        r"image (duplication|manipulation|overlap)", r"western blot",
        r"figure (duplication|manipulation)", r"spliced", r"panels? (appear|were)",
        r"identical (images|panels|bands)",
    ]),
    ("integrity_external", [
        r"plagiaris", r"authorship", r"ethical approval", r"ethics approval",
        r"informed consent", r"paper mill", r"peer review (manipulation|process)",
        r"compromised", r"fabricat", r"third[- ]party",
    ]),
]


def get(url, timeout=60, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ai4s-hack/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as exc:                                # noqa: BLE001
            if i == retries - 1:
                print(f"    取回失败：{exc}")
                return None
            time.sleep(3 * (i + 1))
    return None


def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()


def classify(reason_text):
    low = (reason_text or "").lower()
    hits = {}
    for kind, pats in REASON_PATTERNS:
        n = sum(1 for p in pats if re.search(p, low))
        if n:
            hits[kind] = n
    if not hits:
        return "unknown", hits
    return max(hits, key=hits.get), hits


def search_notices(limit):
    """**从撤稿声明反查原文**。

    比从「被撤稿论文」正查更可靠：理由写在声明正文里，
    而不少被撤稿论文的 commentCorrection 里拿不到声明的 pmcid。
    这里直接用理由关键词去搜声明，命中的天然就是「有明确理由」的那些。
    """
    terms = ('"statistical error" OR "data inconsistencies" OR "errors in the analysis" '
             'OR "miscalculation" OR "incorrect statistical" OR "errors in the data" '
             'OR "unreliable data" OR "inconsistencies in the data" '
             'OR "errors in Table" OR "errors in Figure" OR "sample size"')
    q = (f'PUB_TYPE:"Retraction of Publication" AND OPEN_ACCESS:y AND HAS_FT:y '
         f'AND ({terms})')
    url = (f"{EPMC}/search?query={urllib.parse.quote(q)}&format=json"
           f"&pageSize=100&resultType=core")
    raw = get(url)
    if not raw:
        return []
    return json.loads(raw).get("resultList", {}).get("result", [])[:limit * 4]


def notice_to_original(notice):
    """从声明找回被撤稿的原文（EXT_ID）。"""
    ccl = (notice.get("commentCorrectionList") or {}).get("commentCorrection", [])
    for cc in ccl:
        if "retraction" in (cc.get("type") or "").lower() and cc.get("id"):
            return cc["id"]
    return None


def notice_reason(notice):
    npmc = notice.get("pmcid")
    if not npmc:
        return None
    xml = get(f"{EPMC}/{npmc}/fullTextXML", timeout=60)
    if not xml:
        return None
    m = re.search(r"<body[^>]*>(.*?)</body>", xml, re.S)
    t = strip_tags(m.group(1) if m else xml)
    return t[:4000] if len(t) > 80 else None


def resolve_article(ext_id):
    raw = get(f"{EPMC}/search?query={urllib.parse.quote('EXT_ID:'+ext_id)}"
              f"&format=json&resultType=core")
    if not raw:
        return None
    r = json.loads(raw).get("resultList", {}).get("result", [])
    return r[0] if r else None


def search_retracted(limit):
    """找有全文的开放获取撤稿论文。"""
    q = ('PUB_TYPE:"Retracted Publication" AND OPEN_ACCESS:y AND HAS_FT:y '
         'AND (SRC:"MED" OR SRC:"PMC")')
    out, cursor = [], "*"
    while len(out) < limit:
        url = (f"{EPMC}/search?query={urllib.parse.quote(q)}&format=json"
               f"&pageSize=100&cursorMark={urllib.parse.quote(cursor)}&resultType=core")
        raw = get(url)
        if not raw:
            break
        d = json.loads(raw)
        res = d.get("resultList", {}).get("result", [])
        if not res:
            break
        out.extend(res)
        nxt = d.get("nextCursorMark")
        if not nxt or nxt == cursor:
            break
        cursor = nxt
    return out[:limit * 3]          # 多取一些，后面要筛掉不适用的


def retraction_reason(article):
    """从 commentCorrectionList 找到撤稿声明，取其正文作为标准答案。"""
    ccl = (article.get("commentCorrectionList") or {}).get("commentCorrection", [])
    for cc in ccl:
        if "retraction" not in (cc.get("type") or "").lower():
            continue
        rid = cc.get("id")
        if not rid:
            continue
        raw = get(f"{EPMC}/search?query={urllib.parse.quote('EXT_ID:'+rid)}"
                  f"&format=json&resultType=core")
        if not raw:
            continue
        r = json.loads(raw).get("resultList", {}).get("result", [])
        if not r:
            continue
        n = r[0]
        # 撤稿声明的**理由通常写在正文里，不在摘要**。摘要多是
        # 「[This retracts the article DOI: ...]」这类样板，取不到理由。
        text = ""
        npmc = n.get("pmcid")
        if npmc:
            xml = get(f"{EPMC}/{npmc}/fullTextXML", timeout=60)
            if xml:
                m = re.search(r"<body[^>]*>(.*?)</body>", xml, re.S)
                text = strip_tags(m.group(1) if m else xml)
        if len(text) < 60:
            text = strip_tags(n.get("abstractText") or "")
        if len(text) < 60:
            text = strip_tags(n.get("title") or "")
        if text:
            return {"notice_id": rid, "notice_pmcid": npmc,
                    "notice_title": n.get("title"),
                    "reason_text": text[:4000]}
    return None


def fetch_fulltext(pmcid):
    raw = get(f"{EPMC}/{pmcid}/fullTextXML", timeout=90)
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20, help="最多保留几篇可用的")
    ap.add_argument("--out", default="datasets/retracted")
    ap.add_argument("--kinds", nargs="*", default=["text_detectable"],
                    help="要保留的撤稿理由类别；给 all 则全留")
    a = ap.parse_args()

    root = os.path.abspath(a.out)
    os.makedirs(root, exist_ok=True)

    print("检索带明确理由的撤稿声明 …")
    notices = search_notices(a.limit)
    print(f"候选声明 {len(notices)} 条，逐条反查原文\n")

    kept, stats = [], {}
    for nt in notices:
        if len(kept) >= a.limit:
            break
        reason = notice_reason(nt)
        if not reason:
            continue
        ext = notice_to_original(nt)
        if not ext:
            continue
        art = resolve_article(ext)
        if not art:
            continue
        pmcid = art.get("pmcid")
        if not pmcid:
            continue
        rr = {"notice_id": ext, "notice_pmcid": nt.get("pmcid"),
              "notice_title": nt.get("title"), "reason_text": reason}
        kind, hits = classify(reason)
        stats[kind] = stats.get(kind, 0) + 1
        if "all" not in a.kinds and kind not in a.kinds:
            continue

        xml = fetch_fulltext(pmcid)
        if not xml or len(xml) < 5000:
            continue

        d = os.path.join(root, pmcid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "fulltext.xml"), "w", encoding="utf-8") as fh:
            fh.write(xml)
        meta = {
            "pmcid": pmcid,
            "pmid": art.get("pmid"),
            "doi": art.get("doi"),
            "title": art.get("title"),
            "journal": art.get("journalTitle"),
            "year": art.get("pubYear"),
            "retraction": rr,
            "reason_kind": kind,
            "reason_keyword_hits": hits,
            "_note": ("reason_text 是期刊给出的撤稿理由，作为 A/B 基准的标准答案。"
                      "reason_kind=text_detectable 表示该理由**可能**仅凭正文查出；"
                      "image_forensics 需要原图，integrity_external 需要外部信息，"
                      "都不适合做纯文本基准。"),
        }
        with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=2)
        kept.append(meta)
        print(f"  [{len(kept)}] {pmcid}  {kind}")
        print(f"      {(art.get('title') or '')[:78]}")
        print(f"      理由：{rr['reason_text'][:130]}")

    print(f"\n保留 {len(kept)} 篇到 {a.out}/")
    print(f"候选理由分布：{stats}")
    if kept:
        idx = os.path.join(root, "index.json")
        with open(idx, "w", encoding="utf-8") as fh:
            json.dump({"papers": kept, "reason_stats": stats}, fh,
                      ensure_ascii=False, indent=2)
        print(f"索引写入 {os.path.relpath(idx)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

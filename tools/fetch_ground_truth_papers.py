#!/usr/bin/env python3
"""构建**真实论文 + 客观标准答案**的 A/B 基准语料，覆盖多种错误类型。

为什么不用人工植入的错误
------------------------
植入式基准做过两轮，两轮都饱和（两臂满分，测不出差异），
原因不是错误写得不好，而是**植入这个动作本身留下痕迹**：

1. 语言破绽 —— 中文段落插进英文论文，裸模型直接起了个小标题叫
   「插入的中文实验段落（逐条）」。它在挑外来物，不是在审稿。
2. 主题破绽 —— 往纯生信论文里插动物实验段落，模型第一句就是
   「大量与研究主题无关的段落被插入方法部分」。

改成同语言、同文风、不新起标题之后**仍然**饱和。结论：
只要错误是外来的就总有痕迹，难度就不真实。

为什么要**多种**错误类型，每种只要一两篇
----------------------------------------
拿二十篇同一个细胞系错误去测，测的是「这一条检查通不通」，不是 Skill 的能力面。
每种错误一两篇、类型铺开，才能看出哪几类真有 uplift、哪几类是裸模型本来就会。
覆盖窄而深不如宽而浅 —— 我们要的是**哪里有增益**，不是**某一处增益多大**。

四类标准答案，各自的出题人都是权威来源，不是我们编的：

| kind | 错误 | 出题人 | 裸模型能不能自己查 |
| --- | --- | --- | --- |
| `cell_line` | 细胞系被错误鉴定 | Cellosaurus | 著名的几条知道，长尾不知道 |
| `cited_retracted` | 引用了已撤稿文献（且发表于撤稿之后） | Europe PMC | 不能，撤稿常在训练截止后 |
| `retrospective_registration` | 试验注册晚于开始（违反 ICMJE） | ClinicalTrials.gov | **绝无可能**，正文不写注册日期 |
| `retracted_statistical` | 因统计/数据错误被撤稿 | 期刊撤稿声明 | 部分能 |

用法
----
    python3 tools/fetch_ground_truth_papers.py --list-lines 20
    python3 tools/fetch_ground_truth_papers.py --per-kind 2
    python3 tools/fetch_ground_truth_papers.py --kinds cell_line cited_retracted

只用标准库。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CELLO = "https://api.cellosaurus.org"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
CTGOV = "https://clinicaltrials.gov/api/v2/studies"
UA = {"User-Agent": "ai4s-hack-benchmark/1.0"}


def get(url, timeout=60, retries=2):
    """失败返回 None。调用方必须把 None 当作「没查到」而**不是**「不存在」。"""
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:                                        # noqa: BLE001
            pass
        if i < retries:
            time.sleep(2 * (i + 1))
    return None


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def fulltext(pmcid):
    return get(f"{EPMC}/{pmcid}/fullTextXML", timeout=90)


def body_text(xml):
    m = re.search(r"<body[^>]*>(.*?)</body>", xml or "", re.S)
    return strip_tags(m.group(1) if m else xml)


def to_plain_text(xml):
    """把 JATS XML 转成**保留段落结构**的可读正文。

    两个必须做对的地方，都是踩出来的：

    1. **必须转**：原始 XML 有大量标记噪声，397 KB 的 XML 让审阅调用挂死
       （零 CPU、零连接、十一分钟无产出）；转文本后同篇只有 74 KB。
       审稿人本来就读论文不读 JATS 标记。
    2. **必须保留换行**：第一版把标签一律换成空格，结果整篇变成一行
       七万多字符 —— Read 工具会截断长行，模型自己都发现了
       「文件是单行长文本，Read 工具会截断」，等于根本没读到论文。
       所以段落、标题、列表项边界必须显式插入换行。
    """
    m = re.search(r"<body[^>]*>(.*?)</body>", xml or "", re.S)
    body = m.group(1) if m else (xml or "")
    # 表格与图先压成单行，避免撑开大量空白
    body = re.sub(r"<(table-wrap|fig)\b.*?</\1>",
                  lambda x: "\n" + " ".join(
                      re.sub(r"<[^>]+>", " ", x.group(0)).split()) + "\n",
                  body, flags=re.S)
    # 段落/标题/列表项结束处补换行，标题前后各空一行
    body = re.sub(r"</(p|title|label|list-item|caption|abstract)>", "\n", body)
    body = re.sub(r"<(sec|title)\b[^>]*>", "\n\n", body)
    t = re.sub(r"<[^>]+>", " ", body)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def search(query, page_size=25):
    url = (f"{EPMC}/search?query={urllib.parse.quote(query)}&format=json"
           f"&pageSize={page_size}&resultType=core")
    raw = get(url)
    if not raw:
        return [], 0
    try:
        d = json.loads(raw)
    except Exception:                                            # noqa: BLE001
        return [], 0
    return d.get("resultList", {}).get("result", []), d.get("hitCount", 0)


# ------------------------------------------------ kind 1：错误鉴定的细胞系
def problematic_lines(limit=40):
    url = (f"{CELLO}/search/cell-line?"
           f"q={urllib.parse.quote('cc:\"Problematic cell line\"')}"
           f"&format=json&rows={limit}")
    raw = get(url)
    if not raw:
        return []
    try:
        lst = json.loads(raw)["Cellosaurus"]["cell-line-list"]
    except Exception:                                            # noqa: BLE001
        return []
    out = []
    for cl in lst:
        names = [n.get("value") for n in cl.get("name-list", []) if n.get("value")]
        probs = [c["value"] for c in cl.get("comment-list", [])
                 if "Problematic" in (c.get("category") or "")]
        if not names or not probs:
            continue
        # 只要「污染 / 错误鉴定」这一类 —— 它直接推翻论文的研究对象前提。
        # 培养困难之类的问题不构成结论性错误，不适合做标准答案。
        if not re.search(r"contaminat|misidentif|derivative of|shown to be",
                         probs[0], re.I):
            continue
        out.append({
            "name": names[0],
            "accession": next((a.get("value")
                               for a in cl.get("accession-list", [])), None),
            "problem": probs[0][:400],
        })
    return out


def claimed_origin(problem):
    """推断论文常声称的来源：组织，或物种。

    物种错认其实是更干净的标准答案 —— 拿小鼠细胞当人类细胞得出的结论，
    物种前提直接不成立。
    """
    m = re.search(r"[Oo]riginally thought to (?:originate from|be)[^.]*?"
                  r"(breast|lung|liver|hepat\w*|gastric|colon|colorectal|prostate|"
                  r"ovarian|cervical|melanoma|leukemi\w*|lymphom\w*|gliom\w*|"
                  r"esophage\w*|pancrea\w*|bladder|thyroid|endometri\w*|"
                  r"chordoma|carcinoid|neuroblastom\w*)", problem, re.I)
    if m:
        return {"kind": "tissue", "value": m.group(1).lower()}
    m = re.search(r"[Oo]riginally thought to be of (\w+) origin", problem, re.I)
    if m:
        return {"kind": "species", "value": m.group(1).lower()}
    return None


# 细胞培养语境词。细胞系名必须出现在这些词附近，才算真的当作模型在用。
_CULTURE_CUES = re.compile(
    r"cell line|cells were|were cultur|was cultur|cultured in|maintained in|"
    r"ATCC|DMEM|RPMI|FBS|fetal bovine|passage|seeded|transfect|"
    r"grown in|incubat|trypsin|CO2|细胞系|培养", re.I)


def _in_culture_context(text, name, window=400):
    """该细胞系名是否出现在细胞培养语境附近。

    只要有**任意一次**出现落在语境窗口内即可 —— 论文可能先在别处顺带提到。
    查不到语境时宁可丢掉这篇，也不要出一道假题：
    假题会让整个基准的数字失去意义。
    """
    for m in re.finditer(re.escape(name), text):
        seg = text[max(0, m.start() - window): m.end() + window]
        if _CULTURE_CUES.search(seg):
            return True
    return False



def cases_cell_line(n, seen_lines):
    """每条细胞系只取一篇，保证类型内也有多样性。"""
    out = []
    for ln in problematic_lines():
        if len(out) >= n:
            break
        if ln["name"] in seen_lines:
            continue
        origin = claimed_origin(ln["problem"])
        if not origin:
            continue
        papers, hits = search(f'"{ln["name"]}" AND "{origin["value"]}" '
                              f'AND OPEN_ACCESS:y AND HAS_FT:y', 10)
        if not papers:
            continue
        for p in papers:
            pmcid = p.get("pmcid")
            if not pmcid:
                continue
            xml = fulltext(pmcid)
            if not xml or len(xml) < 5000:
                continue
            # 必须**确实把它当作那个来源的模型在用**。三重把关，缺一不可：
            #  1. 正文出现该细胞系名
            #  2. 正文出现声称的组织/物种来源
            #  3. **该名字出现在细胞培养语境里** —— 这一条是踩坑补的：
            #     CCL4 既是细胞系名也是趋化因子基因名，一篇 chordoma 论文
            #     在 CAF marker 列表里写了 "IL1B, HLA-DRA, MMP9, CCL4"，
            #     前两条全中，却和细胞系毫无关系。短名细胞系与基因符号重名
            #     很常见，只查「名字出现过」必然出假题。
            t = body_text(xml)
            tl = t.lower()
            if ln["name"].lower() not in tl or origin["value"] not in tl:
                continue
            if not _in_culture_context(t, ln["name"]):
                continue
            seen_lines.add(ln["name"])
            out.append({
                "pmcid": pmcid, "xml": xml, "paper": p, "kind": "cell_line",
                "truth": {
                    "cell_line": ln["name"],
                    "cellosaurus_accession": ln["accession"],
                    "problem": ln["problem"],
                    "claimed_origin": f'{origin["kind"]}={origin["value"]}',
                    "source": "Cellosaurus",
                    "corpus_size_hint": hits,
                    "expected_finding": (
                        f'论文使用 {ln["name"]} 作为 {origin["value"]} 的模型，'
                        f'但 Cellosaurus（{ln["accession"]}）标注该细胞系：'
                        f'{ln["problem"][:170]} '
                        f'研究对象前提不成立，基于它的结论均需重新评估。'),
                },
            })
            break
    return out


# ------------------------------------------------ kind 2：引用已撤稿文献
# 几篇著名的已撤稿论文。只用作**种子**：撤稿事实与年份都在下面实时核验，
# 不依赖这里写死的信息。
RETRACTED_SEEDS = [
    {"pmid": "32450107", "retracted_year": 2020,
     "what": "Lancet 上的 Surgisphere 羟氯喹研究，因数据来源无法核实于 2020 年撤稿"},
    {"pmid": "32356626", "retracted_year": 2020,
     "what": "NEJM 上的 Surgisphere 心血管疾病与 COVID-19 研究，2020 年撤稿"},
]


def cases_cited_retracted(n):
    """找**在撤稿之后**仍然引用该文献的论文。

    撤稿前引用情有可原，撤稿后仍当作依据才是问题 —— 所以按年份过滤。
    """
    out = []
    for seed in RETRACTED_SEEDS:
        if len(out) >= n:
            break
        # 实时核验这篇确实被标为撤稿，不信任写死的信息
        res, _ = search(f'EXT_ID:{seed["pmid"]} AND SRC:MED', 1)
        if not res:
            continue
        types = (res[0].get("pubTypeList") or {}).get("pubType") or []
        if "Retracted Publication" not in types:
            continue
        doi, title = res[0].get("doi"), res[0].get("title")

        raw = get(f'{EPMC}/MED/{seed["pmid"]}/citations?format=json&pageSize=60')
        if not raw:
            continue
        try:
            cits = json.loads(raw).get("citationList", {}).get("citation", [])
        except Exception:                                        # noqa: BLE001
            continue
        for c in cits:
            if len(out) >= n:
                break
            try:
                year = int(c.get("pubYear") or 0)
            except (TypeError, ValueError):
                continue
            if year <= seed["retracted_year"]:
                continue
            res2, _ = search(f'EXT_ID:{c.get("id")} AND SRC:MED '
                             f'AND OPEN_ACCESS:y AND HAS_FT:y', 1)
            if not res2 or not res2[0].get("pmcid"):
                continue
            pmcid = res2[0]["pmcid"]
            xml = fulltext(pmcid)
            if not xml or len(xml) < 5000:
                continue
            # **引用已撤稿文献本身不一定是错误。** 一篇讨论科研不端的文章
            # 引用那篇被撤稿的论文完全正当；明确写出「该文已撤稿」的也不是问题。
            # 实测踩到：PMC12232383《Misconduct in science and medicine》整篇
            # 就是在讲这次撤稿，却被当成了错误案例 —— 那是在惩罚做对了的论文。
            # 因此：正文只要提到 retract 一律排除，宁可少收也不能出错题。
            if re.search(r"retract", body_text(xml), re.I):
                continue
            out.append({
                "pmcid": pmcid, "xml": xml, "paper": res2[0],
                "kind": "cited_retracted",
                "truth": {
                    "retracted_doi": doi,
                    "retracted_title": title,
                    "retracted_year": seed["retracted_year"],
                    "citing_year": year,
                    "source": "Europe PMC pubType",
                    "expected_finding": (
                        f'本文（{year} 年）引用了 {doi}（{(title or "")[:60]}），'
                        f'该文献已于 {seed["retracted_year"]} 年撤稿'
                        f'（{seed["what"]}），引用发生在撤稿**之后**。'
                        f'若该文献构成本文立论依据，相关推理需重新评估。'),
                },
            })
    return out


# ------------------------------------------------ kind 3：回顾性注册
NCT_RE = re.compile(r"\bNCT\d{8}\b")


def registered_late(reg, start):
    """注册是否**确定**晚于研究开始。

    ClinicalTrials.gov 的 startDate 常常只有 YYYY-MM 精度，而注册日期是
    YYYY-MM-DD。直接字符串比较会把「同月注册」误判为回顾性注册 ——
    start=2011-02、reg=2011-02-24 时，研究完全可能是 24 号之后才开始的，
    我们无从判断。**取两者中较粗的精度比较，并要求严格大于**，
    宁可漏报也不能凭猜测给稿件扣帽子。
    """
    if not (reg and start):
        return False
    n = min(len(reg), len(start))
    return reg[:n] > start[:n]


def cases_retrospective_registration(n):
    """找注册日期晚于研究开始日期的临床试验论文。

    ICMJE 要求首例入组前完成注册。注册日期与开始日期**都只在注册库里**，
    论文正文几乎从不写 —— 这是纯读正文绝无可能发现的一类问题，
    因此也是最能体现外部核验价值的一类题。
    """
    out = []
    papers, _ = search('PUB_TYPE:"Randomized Controlled Trial" '
                       'AND OPEN_ACCESS:y AND HAS_FT:y', 60)
    for p in papers:
        if len(out) >= n:
            break
        pmcid = p.get("pmcid")
        if not pmcid:
            continue
        xml = fulltext(pmcid)
        if not xml or len(xml) < 5000:
            continue
        m = NCT_RE.search(body_text(xml))
        if not m:
            continue
        nct = m.group(0)
        raw = get(f"{CTGOV}/{nct}?fields=protocolSection.statusModule", timeout=45)
        if not raw:
            continue
        try:
            sm = json.loads(raw)["protocolSection"]["statusModule"]
        except Exception:                                        # noqa: BLE001
            continue
        reg = sm.get("studyFirstSubmitDate")
        start = (sm.get("startDateStruct") or {}).get("date")
        if not registered_late(reg, start):
            continue
        out.append({
            "pmcid": pmcid, "xml": xml, "paper": p,
            "kind": "retrospective_registration",
            "truth": {
                "nct": nct, "registered": reg, "started": start,
                "source": "ClinicalTrials.gov",
                "expected_finding": (
                    f"本文声称的注册号 {nct} 的注册日期为 {reg}，"
                    f"晚于研究开始日期 {start} —— 属回顾性注册，"
                    f"不符合 ICMJE 的前瞻性注册要求。"
                    f"注册日期只存在于注册库，正文通常不写。"),
            },
        })
    return out


# ------------------------------------------------ kind 4：因统计错误撤稿
def cases_retracted_statistical(n):
    """从撤稿声明反查原文，只取理由属统计/数据错误的。"""
    terms = ('"statistical error" OR "data inconsistencies" OR "miscalculation" '
             'OR "errors in the analysis" OR "incorrect statistical" '
             'OR "errors in the data"')
    notices, _ = search(f'PUB_TYPE:"Retraction of Publication" AND OPEN_ACCESS:y '
                        f'AND HAS_FT:y AND ({terms})', 30)
    out = []
    for nt in notices:
        if len(out) >= n:
            break
        npmc = nt.get("pmcid")
        if not npmc:
            continue
        nx = get(f"{EPMC}/{npmc}/fullTextXML", timeout=60)
        reason = body_text(nx)[:1500] if nx else ""
        if len(reason) < 80:
            continue
        ext = None
        for cc in (nt.get("commentCorrectionList") or {}).get("commentCorrection", []):
            if "retraction" in (cc.get("type") or "").lower() and cc.get("id"):
                ext = cc["id"]
                break
        if not ext:
            continue
        res, _ = search(f"EXT_ID:{ext}", 1)
        if not res or not res[0].get("pmcid"):
            continue
        pmcid = res[0]["pmcid"]
        xml = fulltext(pmcid)
        if not xml or len(xml) < 5000:
            continue
        out.append({
            "pmcid": pmcid, "xml": xml, "paper": res[0],
            "kind": "retracted_statistical",
            "truth": {
                "notice_pmcid": npmc, "source": "期刊撤稿声明",
                "reason_text": reason,
                "expected_finding": (
                    f"本文后被撤稿，期刊给出的理由为：{reason[:300]}"),
            },
        })
    return out


BUILDERS = {
    "cell_line": lambda n, st: cases_cell_line(n, st),
    "cited_retracted": lambda n, st: cases_cited_retracted(n),
    "retrospective_registration": lambda n, st: cases_retrospective_registration(n),
    "retracted_statistical": lambda n, st: cases_retracted_statistical(n),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-kind", type=int, default=2,
                    help="每类错误取几篇。一两篇足够 —— 我们要的是类型铺开，"
                         "不是某一类堆量")
    ap.add_argument("--kinds", nargs="*", default=list(BUILDERS),
                    choices=list(BUILDERS))
    ap.add_argument("--out", default="datasets/ground_truth")
    ap.add_argument("--list-lines", type=int, metavar="N",
                    help="只列出 N 条已知问题细胞系，不下载论文")
    a = ap.parse_args()

    if a.list_lines:
        for i, ln in enumerate(problematic_lines()[:a.list_lines], 1):
            o = claimed_origin(ln["problem"])
            print(f"\n[{i}] {ln['name']}  ({ln['accession']})")
            print(f"    {ln['problem'][:180]}")
            print(f"    声称来源：{o['kind']}={o['value']}" if o
                  else "    声称来源：未能推断（该条不进语料）")
        return 0

    root = os.path.abspath(a.out)
    os.makedirs(root, exist_ok=True)
    seen_lines, kept = set(), []

    for kind in a.kinds:
        print(f"\n=== {kind}（目标 {a.per_kind} 篇）===")
        try:
            cases = BUILDERS[kind](a.per_kind, seen_lines)
        except Exception as exc:                                 # noqa: BLE001
            print(f"  取回失败：{exc} —— 这是我们没查到，不是「没有这类论文」")
            continue
        if not cases:
            print("  未取到 —— 可能是接口不通或筛选过严，不要据此认为这类错误不存在")
            continue
        for c in cases:
            d = os.path.join(root, c["pmcid"])
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "fulltext.xml"), "w", encoding="utf-8") as fh:
                fh.write(c["xml"])
            # 同时落一份纯文本 —— 基准喂的是它，不是 XML（见 to_plain_text 说明）
            with open(os.path.join(d, "fulltext.txt"), "w", encoding="utf-8") as fh:
                fh.write(to_plain_text(c["xml"]))
            meta = {
                "pmcid": c["pmcid"],
                "doi": c["paper"].get("doi"),
                "title": c["paper"].get("title"),
                "journal": c["paper"].get("journalTitle"),
                "year": c["paper"].get("pubYear"),
                "kind": c["kind"],
                "ground_truth": c["truth"],
                "_note": ("标准答案由权威来源给出，不是我们编的，也不是植入的。"
                          "错误长在论文自己的血肉里，且骗过了真实的同行评审。"
                          "判定时只问一件事：审稿意见有没有指出这个问题。"),
            }
            with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as fh:
                json.dump(meta, fh, ensure_ascii=False, indent=2)
            kept.append(meta)
            print(f"  [{len(kept)}] {c['pmcid']} {(c['paper'].get('title') or '')[:56]}")
            print(f"      {c['truth']['expected_finding'][:110]}")

    if not kept:
        print("\n**一篇都没取到** —— 这是取回失败，不是「没有这类论文」。"
              "检查网络后重试，不要据此下任何结论。")
        return 1

    by_kind = {}
    for m in kept:
        by_kind[m["kind"]] = by_kind.get(m["kind"], 0) + 1
    with open(os.path.join(root, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"papers": kept, "by_kind": by_kind,
                   "_method": "真实论文 + 权威来源客观标准答案，无任何人工植入"},
                  fh, ensure_ascii=False, indent=2)
    print(f"\n共 {len(kept)} 篇，类型分布 {by_kind}")
    print(f"索引写入 {os.path.relpath(os.path.join(root, 'index.json'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Build the test corpus for the biomedical paper-review Skill.

Source is PLOS (fully open access, CC-BY): it serves the JATS manuscript, the
published PDF and every figure as a separate high-res image, all over plain
HTTP with no bot-blocking — which is what makes it usable as a repeatable
fixture. Each paper lands as:

    datasets/papers/<slot>__<doi-slug>/
        meta.json        bibliographic record + which review dimension it stresses
                         + a figure index (label, caption, image file) as ground truth
        fulltext.xml     JATS full text: sections + captions, machine readable
        paper.pdf        published PDF, for page-level 原图定位
        figures/g001.png per-figure images, the actual input to 图谱解析

Usage:  python3 tools/fetch_papers.py
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "datasets", "papers")
SEARCH = "https://api.plos.org/search"
UA = {"User-Agent": "ai4s-hack-corpus/0.2 (research; hongruichen2003@gmail.com)"}

JOURNAL_SLUG = {
    "PLOS ONE": "plosone", "PLoS ONE": "plosone",
    "PLOS Biology": "plosbiology", "PLoS Biology": "plosbiology",
    "PLOS Medicine": "plosmedicine", "PLoS Medicine": "plosmedicine",
    "PLOS Pathogens": "plospathogens", "PLoS Pathogens": "plospathogens",
    "PLOS Genetics": "plosgenetics", "PLoS Genetics": "plosgenetics",
    "PLOS Computational Biology": "ploscompbiol",
    "PLOS Neglected Tropical Diseases": "plosntds",
    "PLOS Global Public Health": "globalpublichealth",
}

# Each slot targets a dimension from the team's 7-module review plan, so the
# corpus exercises every module instead of being 10 lookalike papers.
SLOTS = [
    ("dose_response", "剂量响应曲线 / IC50 拟合：图谱解析主战场",
     'abstract:"dose-response" AND abstract:"curve"'),
    ("animal_invivo", "实验动物必要性 + 伦理审查 (Peter 模块)",
     'abstract:"mouse model" AND abstract:"in vivo" AND abstract:"treatment"'),
    ("rct_clinical", "CONSORT 流程图 + 统计学方法/样本量 (JY 模块)",
     'abstract:"randomized controlled trial" AND abstract:"primary outcome"'),
    ("microscopy_ihc", "显微图 / 免疫组化定量：图像类结果图 (MY 模块)",
     'abstract:"immunohistochemistry" AND abstract:"staining"'),
    ("flow_cytometry", "流式散点/门控图：典型非曲线统计图",
     'abstract:"flow cytometry" AND abstract:"apoptosis"'),
    ("small_sample_pilot", "小样本量负面样例：统计模块应当报警",
     'title:"pilot study" AND abstract:"participants"'),
    ("meta_analysis", "PRISMA 流程图 + 森林图：方法学规范极强",
     'title:"meta-analysis" AND abstract:"heterogeneity"'),
    ("omics_heatmap", "火山图/热图/富集分析：多重比较校正是常见雷区",
     'abstract:"RNA-seq" AND abstract:"differentially expressed"'),
    ("toxicology", "毒理剂量爬坡 + 安全性评价：剂量设计合规性",
     'abstract:"toxicity" AND abstract:"dose" AND abstract:"rats"'),
    ("survival_km", "Kaplan-Meier 生存曲线 + Cox 回归：临床结局图",
     'abstract:"Kaplan-Meier" AND abstract:"overall survival"'),
]


def get(url, binary=False, tries=3, timeout=120):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            return data if binary else data.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            if attempt == tries - 1:
                print(f"    ! fetch failed ({e}) {url[:80]}")
                return None
            time.sleep(2 * (attempt + 1))
    return None


def search(query, rows=8):
    q = (f'({query}) AND doc_type:full AND article_type:"Research Article" '
         f'AND publication_date:[2015-01-01T00:00:00Z TO 2025-12-31T23:59:59Z]')
    url = (f"{SEARCH}?q={urllib.parse.quote(q)}"
           f"&fl=id,title_display,journal,publication_date,subject"
           f"&rows={rows}&wt=json&sort=publication_date%20desc")
    raw = get(url)
    if not raw:
        return []
    try:
        return json.loads(raw)["response"]["docs"]
    except Exception:  # noqa: BLE001
        return []


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def figure_index(xml):
    """Figure ids/labels/captions straight from JATS — ground truth for eval."""
    figs = []
    for block in re.findall(r"<fig\b.*?</fig>", xml, re.S):
        label = re.search(r"<label>(.*?)</label>", block, re.S)
        cap = re.search(r"<caption>(.*?)</caption>", block, re.S)
        graphic = re.search(r'xlink:href="([^"]+)"', block)
        figs.append({
            "label": strip_tags(label.group(1)) if label else None,
            "caption": strip_tags(cap.group(1)) if cap else None,
            "graphic": graphic.group(1) if graphic else None,
        })
    return figs


def fetch_one(slot_id, why, query, seen):
    for doc in search(query):
        doi = doc["id"]
        if doi in seen or not doi.startswith("10.1371/"):
            continue
        slug = JOURNAL_SLUG.get(doc.get("journal", ""), "plosone")
        base = f"https://journals.plos.org/{slug}/article/file?id={urllib.parse.quote(doi)}"

        xml = get(f"{base}&type=manuscript")
        if not xml or "<article" not in xml:
            continue
        figs = figure_index(xml)
        if len(figs) < 3:      # want figure-rich papers for a 图谱解析 skill
            continue

        name = f"{slot_id}__{doi.split('/')[-1]}"
        dest = os.path.join(OUT, name)
        os.makedirs(os.path.join(dest, "figures"), exist_ok=True)
        print(f"  -> {doi}  {strip_tags(doc.get('title_display',''))[:60]}")

        with open(os.path.join(dest, "fulltext.xml"), "w") as f:
            f.write(xml)

        pdf = get(f"{base}&type=printable", binary=True)
        if pdf and pdf[:4] == b"%PDF":
            with open(os.path.join(dest, "paper.pdf"), "wb") as f:
                f.write(pdf)

        n_img = 0
        for i, fig in enumerate(figs, 1):
            gid = fig.get("graphic") or f"{doi.split('/')[-1]}.g{i:03d}"
            tag = gid.split(".")[-1] if "." in gid else f"g{i:03d}"
            url = (f"https://journals.plos.org/{slug}/article/figure/image"
                   f"?size=large&id={urllib.parse.quote(doi)}.{tag}")
            blob = get(url, binary=True, tries=2)
            if blob and blob[:8].startswith((b"\x89PNG", b"\xff\xd8", b"II*", b"MM\x00")):
                fname = f"{tag}.png"
                with open(os.path.join(dest, "figures", fname), "wb") as f:
                    f.write(blob)
                fig["image_file"] = f"figures/{fname}"
                n_img += 1
            time.sleep(0.3)

        meta = {
            "slot": slot_id,
            "why_selected": why,
            "doi": doi,
            "title": strip_tags(doc.get("title_display", "")),
            "journal": doc.get("journal"),
            "published": doc.get("publication_date", "")[:10],
            "subjects": doc.get("subject", [])[:8],
            "license": "CC-BY 4.0 (PLOS)",
            "url": f"https://doi.org/{doi}",
            "n_figures": len(figs),
            "n_tables": len(re.findall(r"<table-wrap\b", xml)),
            "n_images_downloaded": n_img,
            "has_pdf": os.path.exists(os.path.join(dest, "paper.pdf")),
            "figures": figs,
        }
        with open(os.path.join(dest, "meta.json"), "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"     figs={len(figs)} tables={meta['n_tables']} "
              f"images={n_img} pdf={meta['has_pdf']}")
        return meta
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest, seen = [], set()
    for slot_id, why, query in SLOTS:
        print(f"[{slot_id}] {why}")
        meta = fetch_one(slot_id, why, query, seen)
        if meta:
            seen.add(meta["doi"])
            manifest.append(meta)
        else:
            print("  !! no paper matched this slot")
        time.sleep(1)

    keys = ("slot", "why_selected", "doi", "title", "journal", "published",
            "license", "n_figures", "n_tables", "n_images_downloaded",
            "has_pdf", "url")
    summary = {
        "corpus": "生物医药论文 AI 审稿 / 图谱解析 Skill 测试语料",
        "source": "PLOS Open Access (CC-BY 4.0)",
        "count": len(manifest),
        "papers": [{k: m[k] for k in keys} for m in manifest],
    }
    with open(os.path.join(ROOT, "datasets", "manifest.json"), "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nDone: {len(manifest)} papers -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())

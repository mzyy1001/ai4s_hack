#!/usr/bin/env python3
"""把语料里的 JATS XML 转成纯文本宿主论文，供「埋入式」基线探针使用。

为什么需要它
------------
用最小片段做探针会**高估裸模型**：片段里几乎只有那一个错误，
注意力不被稀释，错误因为「是唯一内容」而显眼。
真实审稿是在一整篇论文里找问题 —— 几十个观察互相竞争，难度完全不同。

所以探针必须把错误**埋进一篇真实论文**里再问。本脚本产出宿主文本。

    python3 tools/make_host_paper.py datasets/papers/<slot>/fulltext.xml > host.txt
    python3 tools/make_host_paper.py <xml> --max-chars 30000
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET

DROP_TAGS = {"ref-list", "back", "journal-meta", "article-meta",
             "fn-group", "ack", "author-notes"}
KEEP_SECTIONS = ("abstract", "intro", "method", "material", "result",
                 "discussion", "conclusion", "statistic", "ethic")


def text_of(el):
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        tag = child.tag.split("}")[-1]
        if tag in DROP_TAGS:
            if child.tail:
                parts.append(child.tail)
            continue
        parts.append(text_of(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def extract(path, max_chars):
    tree = ET.parse(path)
    root = tree.getroot()

    chunks = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "article-title" and not chunks:
            chunks.append("# " + " ".join(text_of(el).split()))
        elif tag == "abstract":
            chunks.append("\n## Abstract\n" + " ".join(text_of(el).split()))
        elif tag == "sec":
            title_el = el.find("./title")
            title = " ".join(text_of(title_el).split()) if title_el is not None else ""
            body = " ".join(text_of(el).split())
            if title:
                body = body[len(title):].strip() if body.startswith(title) else body
            if not body:
                continue
            chunks.append(f"\n## {title or 'Section'}\n{body}")
        elif tag == "table-wrap":
            cap = el.find(".//caption")
            lab = el.find(".//label")
            head = " ".join(filter(None, [
                " ".join(text_of(lab).split()) if lab is not None else "",
                " ".join(text_of(cap).split()) if cap is not None else ""]))
            rows = []
            for tr in el.iter():
                if tr.tag.split("}")[-1] == "tr":
                    cells = [" ".join(text_of(td).split())
                             for td in tr
                             if td.tag.split("}")[-1] in ("td", "th")]
                    if cells:
                        rows.append(" | ".join(cells))
            if rows:
                chunks.append(f"\n## {head or 'Table'}\n" + "\n".join(rows))

    out = "\n".join(chunks)
    out = re.sub(r"\n{3,}", "\n\n", out)
    if max_chars and len(out) > max_chars:
        out = out[:max_chars] + "\n\n[（宿主论文因长度截断）]"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xml")
    ap.add_argument("--max-chars", type=int, default=30000)
    a = ap.parse_args()
    sys.stdout.write(extract(a.xml, a.max_chars))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Parse cached arXiv /abs/ pages into .raw/refs_meta.json.

Companion to fetch_arxiv_meta.py: that script downloads, this one parses.
Splitting them means a parse fix does not require re-downloading.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.path.dirname(HERE), ".raw")
ABS = os.path.join(RAW, "abs")
OUT = os.path.join(RAW, "refs_meta.json")


def strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def field(page, pattern):
    m = re.search(pattern, page, re.S)
    return strip(m.group(1)) if m else None


def parse(page):
    d = {}
    t = field(page, r'<h1 class="title[^"]*">(.*?)</h1>')
    d["title"] = re.sub(r"^Title:\s*", "", t) if t else None
    a = field(page, r'<div class="authors">(.*?)</div>')
    d["authors"] = re.sub(r"^Authors:\s*", "", a).split(", ") if a else []
    ab = field(page, r'<blockquote class="abstract[^"]*">(.*?)</blockquote>')
    d["abstract"] = re.sub(r"^Abstract:\s*", "", ab) if ab else None
    dl = field(page, r'<div class="dateline">(.*?)</div>')
    d["dateline"] = dl
    m = re.search(r"Submitted on (\d{1,2} \w+ \d{4})", dl or "") or re.search(
        r"\[v1\]\s*(\d{1,2} \w+ \d{4})", dl or ""
    )
    d["submitted"] = m.group(1) if m else None
    d["comments"] = field(page, r'<td class="tablecell comments[^"]*">(.*?)</td>')
    d["subjects"] = field(page, r'<td class="tablecell subjects">(.*?)</td>')
    d["journal_ref"] = field(page, r'<td class="tablecell jref">(.*?)</td>')
    d["doi"] = field(page, r'<td class="tablecell doi">(.*?)</td>')
    return d


def main():
    meta = json.load(open(OUT)) if os.path.exists(OUT) and "--fresh" not in sys.argv else {}
    files = sorted(f for f in os.listdir(ABS) if f.endswith(".html"))
    n_new = 0
    for f in files:
        aid = f[:-5]
        page = open(os.path.join(ABS, f), encoding="utf-8", errors="replace").read()
        if '<h1 class="title' not in page:
            print(f"  skip {aid} (not a paper page)", file=sys.stderr)
            continue
        meta[aid] = parse(page)
        n_new += 1
    json.dump(meta, open(OUT, "w"), indent=1, ensure_ascii=False)
    ids = [x.strip() for x in open(os.path.join(RAW, "ids.txt")) if x.strip()]
    missing = [i for i in ids if i not in meta]
    print(f"parsed {n_new} pages -> {len(meta)} entries in refs_meta.json")
    if missing:
        print(f"missing ({len(missing)}): {missing}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fetch arXiv metadata by scraping /abs/ pages.

The arXiv API (export.arxiv.org) rate-limits this host hard; the /abs/ pages
do not, so we scrape those instead. Paced + resumable: re-running skips IDs
already parsed into refs_meta.json.

Usage:  python3 scripts/fetch_arxiv_meta.py <ids.txt> [--delay 2.5]
"""
import concurrent.futures as cf
import html
import json
import os
import re
import sys
import threading
import time
import urllib.request

RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".raw")
CACHE = os.path.join(RAW, "abs")
META = os.path.join(RAW, "refs_meta.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) awesome-harness-evolution/0.1"


def strip(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def field(page, pattern):
    m = re.search(pattern, page, re.S)
    return strip(m.group(1)) if m else None


def parse(page):
    d = {}
    d["title"] = field(page, r'<h1 class="title[^"]*">(.*?)</h1>')
    if d["title"]:
        d["title"] = re.sub(r"^Title:\s*", "", d["title"])
    a = field(page, r'<div class="authors">(.*?)</div>')
    d["authors"] = re.sub(r"^Authors:\s*", "", a).split(", ") if a else []
    ab = field(page, r'<blockquote class="abstract[^"]*">(.*?)</blockquote>')
    d["abstract"] = re.sub(r"^Abstract:\s*", "", ab) if ab else None
    dl = field(page, r'<div class="dateline">(.*?)</div>')
    d["dateline"] = dl
    m = re.search(r"Submitted on (\d{1,2} \w+ \d{4})", dl or "")
    d["submitted"] = m.group(1) if m else None
    m = re.search(r'\[Submitted on ([^\]]+)\]', dl or "")
    d["versions"] = m.group(1) if m else None
    d["comments"] = field(page, r'<td class="tablecell comments[^"]*">(.*?)</td>')
    d["subjects"] = field(page, r'<td class="tablecell subjects">(.*?)</td>')
    return d


def main():
    ids_file = sys.argv[1]
    delay = 2.5
    if "--delay" in sys.argv:
        delay = float(sys.argv[sys.argv.index("--delay") + 1])
    ids = [x.strip() for x in open(ids_file) if x.strip() and not x.startswith("#")]
    workers = 4
    if "--workers" in sys.argv:
        workers = int(sys.argv[sys.argv.index("--workers") + 1])
    os.makedirs(CACHE, exist_ok=True)
    meta = json.load(open(META)) if os.path.exists(META) else {}
    lock = threading.Lock()

    todo = [i for i in ids if i not in meta]
    print(f"{len(ids)} ids, {len(meta)} cached, {len(todo)} to fetch, {workers} workers", flush=True)
    done = [0]

    def save():
        with lock:
            json.dump(meta, open(META, "w"), indent=1, ensure_ascii=False)

    def work(aid):
        page = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    f"https://arxiv.org/abs/{aid}", headers={"User-Agent": UA}
                )
                raw = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
                if "Article not found" in raw or '<h1 class="title' not in raw:
                    print(f"{aid} NOT FOUND", flush=True)
                    break
                page = raw
                open(os.path.join(CACHE, aid + ".html"), "w", encoding="utf-8").write(raw)
                break
            except Exception as e:
                print(f"{aid} attempt {attempt}: {e}", flush=True)
                time.sleep(6 * (attempt + 1))
        if page:
            with lock:
                meta[aid] = parse(page)
                done[0] += 1
                print(f"[{done[0]}/{len(todo)}] {aid} ok  {meta[aid]['title'][:68]}", flush=True)
                save()
        time.sleep(delay)

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(work, todo))

    missing = [i for i in ids if i not in meta]
    print(f"=== done: {len(meta)} parsed, missing={missing}", flush=True)


if __name__ == "__main__":
    main()

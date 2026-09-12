#!/usr/bin/env python3
"""Fetch metadata for non-arXiv sources (blogs, position papers, essays).

Reads every non-arXiv link out of README.md, fetches each page once, and caches
title/author/date to .raw/web_meta.json. verify_urls.py then checks the README
against that cache, so a blog entry is held to the same standard as a paper.

Usage:  python3 scripts/fetch_web_meta.py [--refresh] [--url URL ...]
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
README = os.path.join(ROOT, "README.md")
RAW = os.path.join(ROOT, ".raw")
CACHE = os.path.join(RAW, "web_meta.json")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) awesome-harness-evolution/0.1"


def meta(page, *names):
    for n in names:
        for pat in (
            rf'<meta[^>]+(?:name|property)=["\']{re.escape(n)}["\'][^>]+content=["\']([^"\']+)',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']{re.escape(n)}["\']',
        ):
            m = re.search(pat, page, re.I)
            if m:
                return html.unescape(m.group(1)).strip()
    return None


def parse(page):
    d = {}
    d["title"] = (
        meta(page, "citation_title", "og:title", "twitter:title")
        or (html.unescape(re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I).group(1)).strip()
            if re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I) else None)
    )
    if d["title"]:
        d["title"] = re.sub(r"\s+", " ", d["title"]).strip()
    d["author"] = meta(page, "citation_author", "author", "article:author", "og:site_name")
    d["date"] = meta(
        page, "citation_publication_date", "article:published_time",
        "datePublished", "date", "og:updated_time",
    )
    m = re.search(r"(\d{4})-(\d{2})", d["date"] or "")
    d["month"] = f"{m.group(1)}-{m.group(2)}" if m else None
    d["description"] = meta(page, "og:description", "description", "twitter:description")
    d["site"] = meta(page, "og:site_name")
    return d


def readme_urls():
    """Dated entries only: '- [Title](url) — Author, YYYY-MM. ...'

    The date requirement keeps bare link lists (Related Awesome Lists) out of
    the cache, since those are pointers rather than attributed sources.
    """
    t = open(README, encoding="utf-8").read()
    urls = re.findall(r"^- \[.+?\]\((https?://[^)]+)\) — .+?, \d{4}-\d{2}\. ", t, re.M)
    return [u for u in urls if "arxiv.org/abs/" not in u]


def fetch(url, timeout=40):
    """Fetch a URL, falling back to the Wayback Machine on 403.

    Some vendors (OpenAI, Preprints.org) return 403 to non-browser clients.
    The archived copy carries the same citation metadata, so verification can
    still be grounded in the page that actually exists.
    """
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace"), url
    except urllib.error.HTTPError as e:
        if e.code not in (403, 401, 406):
            raise
        api = ("https://archive.org/wayback/available?url="
               + urllib.parse.quote(url, safe=""))
        snap = json.loads(urllib.request.urlopen(api, timeout=timeout).read())
        closest = (snap.get("archived_snapshots") or {}).get("closest") or {}
        if not closest.get("available"):
            raise
        alt = closest["url"].replace("http://", "https://", 1)
        req2 = urllib.request.Request(alt, headers={"User-Agent": UA})
        return urllib.request.urlopen(req2, timeout=timeout).read().decode("utf-8", "replace"), alt


def main():
    refresh = "--refresh" in sys.argv
    if "--url" in sys.argv:
        i = sys.argv.index("--url")
        urls = [u for u in sys.argv[i + 1:] if u.startswith("http")]
    else:
        urls = readme_urls()
    os.makedirs(RAW, exist_ok=True)
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}

    todo = [u for u in urls if refresh or u not in cache]
    print(f"{len(urls)} non-arXiv links, {len(cache)} cached, {len(todo)} to fetch", flush=True)
    for n, url in enumerate(todo, 1):
        try:
            page, used = fetch(url)
            cache[url] = parse(page)
            if used != url:
                cache[url]["via"] = used
            tag = " (via wayback)" if used != url else ""
            print(f"[{n}/{len(todo)}] {cache[url].get('title','?')[:60]}  ({cache[url].get('month')}){tag}", flush=True)
        except Exception as e:
            print(f"[{n}/{len(todo)}] FAIL {url} — {e}", flush=True)
            cache.setdefault(url, {"error": str(e)})
        json.dump(cache, open(CACHE, "w"), indent=1, ensure_ascii=False)
        time.sleep(1.0)
    print("=== done", flush=True)


if __name__ == "__main__":
    main()

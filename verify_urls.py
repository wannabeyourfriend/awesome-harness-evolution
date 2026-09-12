#!/usr/bin/env python3
"""Verify README integrity.

Checks, offline, against the arXiv metadata cached in .raw/refs_meta.json:

  1. every arXiv link in the README resolves to a paper we actually fetched
  2. the link text matches the real title on arXiv
  3. the stated date matches the arXiv ID month
  4. no paper is listed twice
  5. every README heading has a working table-of-contents link, and vice versa
  6. non-arXiv links are reported for manual checking

Run:  python3 verify_urls.py [--online]
      --online additionally HEAD-checks every non-arXiv URL.

Populate .raw/ first with:
      python3 scripts/fetch_arxiv_meta.py .raw/ids.txt && python3 scripts/parse_abs.py
"""
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
README = os.path.join(HERE, "README.md")
META = os.path.join(HERE, ".raw", "refs_meta.json")
WEB = os.path.join(HERE, ".raw", "web_meta.json")

MONTH = {
    "01": "2026", "02": "2026", "03": "2026", "04": "2026", "05": "2026",
    "06": "2026", "07": "2026", "08": "2026", "09": "2026", "10": "2026",
    "11": "2026", "12": "2026",
}


def slug(title):
    """Approximate GitHub's heading -> anchor slug.

    GitHub drops every non-[word, space, hyphen] character and turns each
    remaining space into a hyphen, without collapsing runs. So `&` vanishes
    leaving two spaces and therefore two hyphens, and an emoji prefix leaves
    a leading hyphen (`#-foundations`). Both sides of the comparison are
    stripped of leading/trailing hyphens at use time.
    """
    s = unicodedata.normalize("NFKC", title).lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    return s.replace(" ", "-")


# Sources that block automated clients outright, so their metadata cannot be
# fetched by any route available here. Kept in the list, but reported as a
# warning rather than passing silently.
KNOWN_UNVERIFIABLE = {
    "https://www.preprints.org/manuscript/202603.1756/v1":
        "publisher returns 403 to all automated clients and has no Wayback snapshot",
}


def norm_title(t):
    """Fold the differences between a source's title and ours.

    Handles arXiv's ASCII titles, typographic apostrophes/quotes, dash forms,
    and site names that publishers append to og:title ("X | Site").
    """
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = (t.replace("\u2019", "'").replace("\u2018", "'")
          .replace("\u201c", '"').replace("\u201d", '"'))
    t = re.sub(r"\s*[|\u2013\u2014-]\s*[^|]*$", "", t) if "|" in t else t
    t = re.sub(r"[\u2013\u2014-]+", "-", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def main():
    online = "--online" in sys.argv
    text = open(README, encoding="utf-8").read()
    meta = json.load(open(META)) if os.path.exists(META) else {}
    web = json.load(open(WEB)) if os.path.exists(WEB) else {}

    errors, warnings, non_arxiv = [], [], []

    # ---- headings and ToC anchors
    headings = [h.strip() for h in re.findall(r"^#{2,3} +(.+)$", text, re.M)]
    heading_slugs = {slug(h).strip("-") for h in headings}
    toc = [a.strip("-") for a in re.findall(r"^\s*- \[.+?\]\(#(.+?)\)$", text, re.M)]
    for a in toc:
        if a not in heading_slugs:
            errors.append(f"ToC anchor has no heading: #{a}")
    for h in headings:
        if slug(h).strip("-") not in toc and h not in ("Contents",):
            warnings.append(f"heading not in ToC: {h}")

    # ---- compact entries: 1. Title. [[Paper]](url) `arXiv YYYY-MM`
    seen = {}
    entries = re.findall(
        r"^1\. (.+?) \[\[(?:Paper|Blog)\]\]\((https?://[^)]+)\) "
        r"`(?:arXiv|Preprint|Blog) (\d{4}-\d{2})`$", text, re.M
    )
    if not entries:
        errors.append("no bibliography entries parsed; check the README entry format")
    for title, url, date in entries:
        title = title.removesuffix(".")
        if "arxiv.org/abs/" in url:
            aid = url.rsplit("/", 1)[-1]
            if aid in seen:
                errors.append(f"listed twice: {aid} ({title[:50]})")
            seen[aid] = title
            m = meta.get(aid)
            if not m:
                errors.append(f"unverified (not in .raw): {aid} — {title[:60]}")
                continue
            real = re.sub(r"\s+", " ", m.get("title") or "").strip()
            if real and title.strip() != real:
                if norm_title(title) == norm_title(real):
                    warnings.append(f"title differs only in punctuation/diacritics {aid}: {title[:60]}")
                else:
                    errors.append(f"title mismatch {aid}\n    readme: {title[:80]}\n    arxiv : {real[:80]}")
            ym = f"20{aid[:2]}-{aid[2:4]}"
            if date.strip() != ym:
                errors.append(f"date mismatch {aid}: readme {date.strip()}, expected {ym}")
        else:
            w = web.get(url)
            if not w:
                errors.append(f"unverified non-arXiv link (run scripts/fetch_web_meta.py): {url}")
            elif w.get("error"):
                if url in KNOWN_UNVERIFIABLE:
                    warnings.append(f"unverifiable by design — {url} ({KNOWN_UNVERIFIABLE[url]})")
                else:
                    errors.append(f"fetch failed for {url}: {w['error']}")
            else:
                real = w.get("title")
                if real and norm_title(title) != norm_title(real):
                    errors.append(f"title mismatch {url}\n    readme: {title[:80]}\n    page  : {real[:80]}")
                if w.get("month") and date.strip() != w["month"]:
                    errors.append(f"date mismatch {url}: readme {date.strip()}, page says {w['month']}")
            non_arxiv.append((title, url))

    # ---- coverage: fetched papers missing from the README
    listed = set(seen)
    fetched = set(meta)
    missing = sorted(fetched - listed)

    print(f"README entries (arXiv): {len(seen)}")
    print(f"non-arXiv links:        {len(non_arxiv)}")
    print(f"papers fetched:         {len(fetched)}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print("  ✗ " + e)
    else:
        print("\n✓ all arXiv links verified: titles, dates, and no duplicates")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print("  ! " + w)

    if missing:
        print(f"\nFetched but not listed ({len(missing)}): {', '.join(missing[:20])}"
              + (" ..." if len(missing) > 20 else ""))

    if online:
        import urllib.request
        print("\nOnline checks:")
        for title, url in non_arxiv:
            try:
                req = urllib.request.Request(url, method="HEAD",
                                             headers={"User-Agent": "Mozilla/5.0"})
                code = urllib.request.urlopen(req, timeout=20).status
                if code >= 400:
                    print(f"  ✗ {code} {url}")
            except Exception as e:
                print(f"  ? {url} — {e}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

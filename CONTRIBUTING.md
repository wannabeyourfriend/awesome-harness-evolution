# Contributing

Thanks for helping keep this list current. This area moves fast, and most of the value
comes from people adding papers the maintainers have not seen yet.

## What belongs here

The list covers work on the **agent harness**: the runtime scaffold around a language
model — system prompt and its assembly, tool/function interfaces, context management,
the control loop, sub-agent orchestration, memory, and output parsing.

A paper belongs if it does at least one of the following:

- **Evolves the harness.** Search, optimization, repair, or online adaptation of the
  harness itself, rather than of the model weights.
- **Trains a model to do harness engineering.** The model learns to author, edit, or
  repair harnesses (RL, SFT, evolutionary, or otherwise).
- **Defines or measures the harness as a variable.** A benchmark or evaluation that
  isolates the harness, or a taxonomy/survey of harness engineering.
- **Contributes a harness component** in a way that the harness-evolution literature
  builds on (memory, context management, skills, orchestration, tool interfaces).

Precursor work on automated agent design belongs in the dedicated section, not the core.

## What does not belong here

- **Prompt engineering for a single fixed prompt.** Optimizing one prompt string is not
  harness evolution unless the method generalizes to the rest of the scaffold.
- **Model-only post-training** with no harness component: a better model is not a better
  harness, and the distinction is the point of this list.
- **Marketing posts and vendor announcements** with no method or evaluation.
- **Papers whose only harness claim is a table row.** If a paper happens to report a
  scaffold ablation but the contribution is elsewhere, it is not a harness paper.

## Entry format

Use a compact numbered list for each section, followed by one shared reading-notes fold:

```markdown
1. Title. [[Paper]](https://arxiv.org/abs/XXXX.XXXXX) `arXiv YYYY-MM`

<details>
<summary>Reading notes — authors, mechanisms, and evidence</summary>

- **Title** — First Author et al., YYYY-MM. One or two sentences on what it does
  and why it belongs. Say what is *learned* or *evolved* and what the evidence is.

</details>
```

Rules:

- **Link to the paper**, preferring the arXiv abstract page, then the publisher DOI, then
  the project page.
- **One or two sentences, no more.** Say what the method does and what it shows. Avoid
  "novel" and "state-of-the-art"; give the mechanism or the number instead.
- **Keep the date** (`YYYY-MM`, first submission). It is the only thing that makes the
  chronology of this area readable.
- **Use source labels, not inferred venues.** Use `arXiv YYYY-MM` for arXiv papers,
  `Preprint YYYY-MM` for other preprints, and `[[Blog]](url)` with `Blog YYYY-MM`
  for technical articles. Add each annotation to the section's existing reading-notes fold.
- **Do not delete entries.** If something is superseded, add a note; a curated list is a
  record, not a leaderboard.
- **No invented numbers.** Every figure in an annotation must be traceable to the paper.

## How to add a paper

Open a pull request that appends the entry to the right section and updates the table of
contents if you added a section. If you would rather not write the annotation, open an
issue with the link and a sentence on why it belongs; that is a perfectly good
contribution.

## Verification

Every entry is checked against its source — arXiv for papers, the page itself for everything else.
Refresh both metadata caches, then run the checker:

```bash
python3 scripts/fetch_arxiv_meta.py .raw/ids.txt
python3 scripts/parse_abs.py
python3 scripts/fetch_web_meta.py
python3 verify_urls.py
```

The caches land in `.raw/` (gitignored). The arXiv API rate-limits hard from some networks, so
`fetch_arxiv_meta.py` scrapes `/abs/` pages instead, which does not.

`verify_urls.py` fails on a link that was never fetched, a title or date that does not match the
source record, an entry listed twice, or a broken table-of-contents anchor. It prints warnings for
heading and punctuation differences that are deliberate.

Please run it before opening a pull request. If it reports an entry as `unverified`, re-run the
fetch steps above so the entry gets cached, then re-run the checker.

## Visual assets

The cover is generated artwork; its prompt is saved in `assets/cover-prompt.txt`.
The research timeline is an editable SVG built from selected README entries. Update the
selection in `scripts/build_timeline.py`, then regenerate the SVG and README PNG:

```bash
uv run --with cairosvg python scripts/build_timeline.py --png
```

On Homebrew macOS, prefix that command with `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`
if Cairo cannot be located. The SVG-only command needs no external dependencies:
`python3 scripts/build_timeline.py`.

For each new card, record its institution and primary affiliation source in
`assets/timeline-affiliations.json`. Logo files and their source URLs are stored under
`assets/logos/` and `assets/institutions.json`. Prefer the first author's first listed
institution; for team papers, use the first listed institution. Never infer an
affiliation from the model being used. Keep explicit team/independent/not-stated labels
when the paper does not identify an institution. Third-party logos retain their owners' rights.
Keep it selective, use first-submission dates, and do not imply that chronology proves
capability gains or progress to AGI.

## Adding a non-arXiv source

Blogs, position papers, and essays are welcome when they make a substantive claim. The bar is
higher than for papers, because there is no peer review behind them:

- **First-party or named-author sources only.** A lab engineering post, a researcher's blog, or a
  published position paper. Not marketing pages, not SEO listicles.
- **It must argue something or report a result.** A tutorial or a documentation page is not an
  entry, however good it is.
- **Cite it the same way as a paper** — title, author, `YYYY-MM` — so the entry format stays uniform
  and the checker can validate it.

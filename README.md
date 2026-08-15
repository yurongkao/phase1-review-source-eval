# Phase 1 — Review Data Source Evaluation

Evidence-based evaluation of candidate review-data sources for Phase 1 ingestion.
Prepared for John · updated 2026-08.

## The framing (what John asked for)

We are **not** ranking sources against a single "best" bar. We evaluate each source
for fitness against **two distinct jobs**, and recommend a best source for each:

- **Use-case A — Recurring / repeatable collection.** Can we re-pull the same kind of
  sample consistently on a schedule, without login friction or silent shape changes?
- **Use-case B — Downstream analysis & modeling.** Is the corpus rich, large, and clean
  enough to train / analyze on (fields, rating distribution, quality flags, size)?

A source can win both — but each recommendation is argued separately from its own evidence.

## Repo layout

```
README.md            – this file: shortlist, methodology, how to reproduce
scorecard.md         – side-by-side scorecard on John's dimensions + A/B fit
test_notes.md        – per-source raw findings from the sample pulls
scripts/             – reproducible pull scripts (Steam, Apple RSS, ...)
samples/             – raw sample data saved from each pull (committed for evidence)
```

## Shortlist (sources under evaluation)

| Source | Access | Key needed | Notes |
|---|---|---|---|
| Steam | Public JSON API | No | Game reviews; quick key-free win |
| Apple App Store | Public RSS feed | No | App reviews; quick key-free win |
| Amazon Reviews 2023 | Static dataset | No (download) | Large historical corpus for modeling |
| Google Play | Scrape / library | No key (unofficial) | Compare shape vs Apple |
| Best Buy | Official API | Free key | Optional; compare shape vs Amazon |

## Methodology

1. Build the scorecard structure on John's dimensions (documentation-based columns first).
2. Pull a small representative sample from each source (`scripts/` → `samples/`).
3. Record actual fields, sample size, pagination, repeatability, IDs in `test_notes.md`.
4. **Test — not assume — the cross-source claims** (Apple≈Google shape, Best Buy≈Amazon shape).
5. Fill the evidence-dependent scorecard cells from the samples, not the docs.
6. Score **licensing / permitted use as its own column**.
7. Write the two recommendations (A and B), each justified by sample evidence.

## Volume-units convention (fixes the mixed-units problem)

Two separate, clearly-defined columns — never app-counts as a volume proxy:

- **Reviews per representative item** — number of reviews pullable for ONE typical
  product / app / game in a small controlled pull.
- **Total corpus size** — the full addressable size of the source (dataset total, or
  order-of-magnitude estimate), stated with its unit.

## Status

- [x] Repo skeleton + scorecard scaffold (Thu 8/13)
- [ ] Steam + Apple RSS samples (Fri 8/14)
- [ ] Amazon slice + Google Play / Best Buy samples; test the two claims (Sat 8/15)
- [ ] Fill scorecard from evidence + two recommendations + polish (Sun 8/16)
- [ ] Final review + send update (Mon 8/17)

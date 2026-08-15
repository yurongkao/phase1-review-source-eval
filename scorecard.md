# Source Scorecard

**How to read this:** documentation-based columns are filled now. Every cell that depends
on a real sample pull is marked **TBD — pending sample** and gets filled Fri–Sun from
`test_notes.md`. Licensing is scored as its own column, not a footnote.

## Volume units (fixed convention)

- **Reviews / representative item** = reviews for ONE typical product/app/game in a small controlled pull.
- **Total corpus size** = full addressable size (dataset total or order-of-magnitude).
- ⚠️ App-counts are NOT used as a volume proxy.

## Scorecard — John's dimensions

| Dimension | Steam | Apple App Store | Amazon Reviews 2023 | Google Play | Best Buy |
|---|---|---|---|---|---|
| Source type (live / API / public feed / static) | Public JSON API | Public RSS feed | Static dataset | Unofficial scrape/lib | Official API |
| Auth needed (login / key / manual) | None | None | Download, none | None (unofficial) | Free API key |
| Review fields available (per docs) | review text, rating (up/down), author, playtime, votes, timestamp | title, review, rating (1–5), author, version, updated | text, rating (1–5), title, verified, helpful votes, product meta | text, rating (1–5), author, thumbs-up, version, date | text, rating (1–5), title, verified, submission time |
| Reviews / representative item | TBD — pending sample | TBD — pending sample | TBD — pending sample | TBD — pending sample | TBD — pending sample |
| Total corpus size | TBD (est. order-of-mag) | TBD | ~large (multi-M, category-dependent) | TBD | TBD |
| Repeatability (re-pull consistent?) | TBD — pending sample | TBD — pending sample | Static → fully repeatable | TBD — pending sample | TBD — pending sample |
| Pagination behavior | TBD — pending sample | TBD — pending sample | N/A (bulk file) | TBD — pending sample | TBD — pending sample |
| ID scheme | TBD — pending sample | TBD — pending sample | TBD — pending sample | TBD — pending sample | TBD — pending sample |
| Main data-quality limits | TBD — pending sample | TBD — pending sample | TBD — pending sample | TBD — pending sample | TBD — pending sample |
| Domain represented | PC games | Mobile apps | E-commerce products | Mobile apps | Consumer electronics retail |
| Maintenance / access risk | Low–moderate — **documented** partner endpoint (`partner.steamgames.com/doc/store/getreviews`) | Moderate–high — legacy RSS feed, undocumented, no published support guarantee | Low — static, versioned snapshot | **High** — unofficial access to an internal endpoint; can change without notice | Low–moderate — documented API; key/quota + ToS |
| **Licensing / permitted use** | TBD — confirm ToS (commercial?) | TBD — confirm ToS | TBD — check dataset license + redistribution | TBD — ToS risk | TBD — API ToS |
| **Fit — A: recurring collection** | TBD | TBD | Low (static, no new data) | TBD | TBD |
| **Fit — B: downstream analysis** | TBD | TBD | High (size + fields) | TBD | TBD |

## Claims to TEST (not assume) — see test_notes.md

1. **Apple RSS ≈ Google Play field shape** → verify actual fields / pagination / IDs before asserting reuse.
2. **Best Buy ≈ Amazon field shape** → verify actual fields / pagination / IDs before asserting reuse.

## Recommendations (to be written Sun 8/16 from evidence)

- **A — Recurring collection:** _pending samples._
- **B — Downstream analysis / modeling:** _pending samples._

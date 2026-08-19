# Source Scorecard

**How to read this.** Every cell is labelled by where it came from:

- **[sampled]** — measured from a real pull saved in `samples/`. Evidence.
- **[doc]** — taken from the source's own documentation. Not verified by a pull.
- **not sampled — pending** — no evidence exists. Deliberately empty, never padded.

If a cell is not marked `[sampled]`, it is not evidence, and it is not scored as though it were.
Licensing is scored as its own row, not a footnote. Fit is scored separately for the two jobs.

## Volume units (fixed convention)

- **Reviews / representative item (unit A)** = reviews available for ONE typical product/app/game.
- **Total corpus size (unit B)** = the full addressable size of the source, across all items.
- ⚠️ App-counts / product-counts are NOT used as a volume proxy.
- ⚠️ **The two units are not interchangeable and must not be compared across rows as if they were.**
  Steam reports 2.76M reviews *for one title*; Amazon's 571.54M is *the entire dataset*. Read down
  a row, not across the two rows.

## Fit rating scale (fixed vocabulary)

The two **Fit** rows use these five values and no others. Each cell is a value **plus one
clause naming the fact that decides it** — never a summary of the column above it.

| Value | Means | Test for using it |
|---|---|---|
| **High** | Fit for this job on sampled evidence, no blocking condition | Could you start building on it Monday? |
| **Moderate** | Fit, but with a named cost or limit you have measured | Can you state the limit in one clause? |
| **Low** | Usable only in a narrow case, or a serious defect you measured | Is the defect measured, not assumed? |
| **Disqualified** | A property of the source rules it out for this job entirely | Is it structural, not just bad? |
| **Not assessable** | No sample exists — the question cannot be answered | Are you about to infer from an absence? |

⚠️ **"Not assessable" is not a bad score.** It is the absence of a score. Writing `Low` where
no sample exists would infer a property from missing evidence — the exact failure this
deliverable exists to correct.

⚠️ **A source scoring the same in both Fit rows is a warning sign** — it usually means the
source was rated rather than the fit, which is the single-bar ranking this evaluation rejects.

## Scorecard — John's dimensions

| Dimension | Steam | Apple App Store | Amazon Reviews 2023 | Google Play | Best Buy |
|---|---|---|---|---|---|
| **Source type** | Public JSON API `[doc]` | Legacy RSS feed, undocumented `[sampled]` | Static bulk dataset `[doc]` | Unofficial lib → internal `batchexecute` endpoint `[sampled]` | Official REST API `[doc]` |
| **Auth needed** | None `[sampled]` | None `[sampled]` | None — public file download `[sampled]` | None `[sampled]` | Free API key `[doc]` — ⚠️ see eligibility row |
| **Review fields actually returned** | 18 top-level + nested `author` (11 sub-fields): review, `voted_up`, votes_up/funny, `weighted_vote_score`, language, timestamps, `steam_purchase`, `received_for_free`, `refunded`, playtime `[sampled]` | 9 per row: author, content, id, rating, title, updated, version, vote_count, vote_sum `[sampled]` | 10: rating, title, text, images, asin, parent_asin, user_id, timestamp, verified_purchase, helpful_vote `[sampled]` | 11: reviewId, userName, userImage, content, score, thumbsUpCount, reviewCreatedVersion, at, replyContent, repliedAt, appVersion `[sampled]` | not sampled — pending |
| **Reviews / representative item (unit A)** | 40 pulled over 2 pages at 20/call, no cap hit. Source *reports* 2,757,984 exist for this title — **reachable depth untested** `[sampled + doc]` | **50 — a measured ceiling.** Feed exhausted at page 2 for one of the store's most-reviewed apps `[sampled]` | **6.2 mean** (701.5K reviews ÷ 112.6K items, All_Beauty) — a mean over a long tail; median item has far fewer `[doc]` | 200 pulled, continuation token still present → more available; **ceiling untested** `[sampled]` | not sampled — pending |
| **Total corpus size (unit B)** | **Not measured.** Would require enumerating all appids. The 2.76M figure above is unit A, not B `[—]` | ⚠️ **NOT EXPOSED.** The feed publishes no review-count total; corpus size is unknowable from this source `[sampled]` | All_Beauty **701.5K reviews / 112.6K items**; whole dataset **571.54M reviews · 48.19M items · 33 categories · 1996–2023 · 750 GB** `[doc]` | **Not exposed** in the response `[sampled]` | not sampled — pending. *Docs describe a server-reported `total`; untested `[doc]`* |
| **Repeatability** | Re-pull after ~2s: 20/20 same IDs, same order. ⚠️ **Tests a 2-second window only** — day-to-day ordering untested `[sampled]` | Re-pull after ~2s: 50/50 same IDs, same order. Same 2-second caveat `[sampled]` | **Perfect by construction** — static versioned file, same bytes every read `[sampled]` | Re-pull after ~2s: 50/50 same IDs, same order. Same caveat; `sort=NEWEST` means the window moves between real pulls `[sampled]` | not sampled — pending |
| **Pagination behavior** | Opaque `cursor`; `*` for page 1, next token in body; **cursor recycles when exhausted** `[sampled]` | `page=<n>` path segment; end of feed = an empty page. ⚠️ The ~10-page cap was never reached (this app ran out at page 2) so **the cap is untested** `[sampled]` | N/A — static line-delimited file; "paging" is reading further into it, fully deterministic `[sampled]` | Opaque continuation token, page size capped per call `[sampled]` | not sampled — pending. *Docs describe `page`/`pageSize` + `totalPages` `[doc]`* |
| **ID scheme** | review `recommendationid` · item `appid` (envelope) · author `author.steamid` `[sampled]` | review `id.label` · item = app id (**envelope only**) · **no stable public user id** `[sampled]` | ⚠️ **No standalone review id** — identity is (`user_id`, `parent_asin`, `timestamp`). Item: join on **`parent_asin`**, not `asin` (variants share a parent) `[sampled + doc]` | review `reviewId` · item = package name (**envelope only**) · **no stable user id** — display names only, not unique `[sampled]` | item = `sku` `[doc]`. ⚠️ `sku` is not derivable from Amazon's `asin`; a cross-source join needs a UPC/GTIN bridge |
| **Rating shape** | ⚠️ **Boolean `voted_up`** (thumbs up/down) — **not a 1–5 scale at all** `[sampled]` | 1–5, JSON type **`str`** `[sampled]` | 1–5, JSON type **`float`** (2000/2000 rows) `[sampled]` | 1–5, JSON type **`int`** `[sampled]` | not sampled — pending |
| **Quality flags** | `steam_purchase`, `received_for_free`, `refunded`, `written_during_early_access`, `votes_up`, `weighted_vote_score`, playtime `[sampled]` | `im:voteCount` / `im:voteSum`. **No verified-purchase flag** `[sampled]` | **`verified_purchase` — 48.0% true (960/2000)**; `helpful_vote` (73.7% zero, max 430); 262 rows carry images `[sampled]` | `thumbsUpCount`. **No verified-purchase flag**; developer replies on **0/200** rows `[sampled]` | not sampled — pending |
| **Main data-quality limits** | ⚠️ **Language skew, measured: 31/40 rows Russian, 3 English** in a recency window with `language=all`. Plus the 192× scoping trap (below), and refunded / free / early-access rows included by default `[sampled]` | Storefront-scoped (one country per pull); recency-biased ordering; no verified flag; no corpus total; **shallow depth (50)**; undocumented endpoint `[sampled]` | 1 empty-text row in 2,000; no review id; `helpful_vote` zero-skewed; **historical snapshot, not live** `[sampled]` | Locale-scoped; no user id; display names not unique; `sort=NEWEST` window moves between pulls `[sampled]` | not sampled — pending |
| **⚠️ Scoping traps (measured)** | **192× swing.** Default `purchase_type=steam` returns 14,380 for Dota 2; `purchase_type=all` returns 2,757,984. A pipeline that doesn't pin `language` **and** `purchase_type` reports silently wrong volumes `[sampled]` | `sortby=mostrecent` makes the observed rating distribution a **recency window**, not the app's lifetime distribution `[sampled]` | Slice is the **head of the file**, not a random sample. Head-vs-mid rating gap **7.9 pp** → *borderline*: usable directionally, label as a slice, not the category `[sampled]` | Same recency-window caveat as Apple `[sampled]` | not sampled — pending |
| **Domain represented** | PC games | Mobile apps | E-commerce products (33 categories) | Mobile apps | Consumer electronics retail |
| **Maintenance / access risk** | **Low–moderate** — documented partner endpoint `[doc]` | **High** — legacy, undocumented RSS with no published support guarantee `[sampled behavior, no contract]` | **Low** — static, versioned snapshot `[doc]` | **High** — unofficial access to an internal endpoint; can break without notice `[doc + sampled]` | **Not assessed.** Nothing is inferable from the 403 the placeholder key produced |
| **Access eligibility** | Open `[sampled]` | Open `[sampled]` | Open download `[sampled]` | Open, but unsanctioned `[sampled]` | ⚠️ **A gate, not a delay.** Best Buy [announced in 2016](https://medium.com/best-buy-developers/announcing-a-change-to-best-buy-s-api-access-b09afc4bc27a) it issues no new keys to free email domains (Gmail/Yahoo). *2016 statement; blog stopped publishing 2017; current enforcement unverified* `[doc]` |
| **🔑 Licensing / permitted use** | Not cleared — Steam ToS not reviewed for commercial reuse. **not assessed** | Not cleared — legacy endpoint, no published terms covering it. **not assessed** | 🚨 **NO STATED LICENSE.** No License field on the card, no LICENSE file in the repo. Citation BibTeX is *offered, not required*. Commercial use and redistribution both **unaddressed**. Provenance: third-party scrape of Amazon — even a permissive McAuley license cannot grant rights over Amazon's content. **Needs legal review before any commercial use** `[doc, verified 8/16]` | 🚨 **Not cleared — no sanctioned read path exists.** Score as "likely not permitted," not blank `[doc]` | Official API with published terms at developer.bestbuy.com/legal `[doc]` — the cleanest terms in the shortlist *on paper*, unverified by use |
| **Fit — A: recurring collection** | **Moderate** — key-free, documented endpoint, re-pull stable; but reachable depth before the cursor recycles is untested, and volumes are only correct if `language` and `purchase_type` are pinned explicitly | **Low** — the 50-row ceiling does not bite a scheduled poll, which only needs what is new; it is the accumulation of measured limits that does — no backfill capability, storefront-scoped (one pull per country), no corpus total exposed, on an undocumented endpoint carrying no support guarantee | **Disqualified** — static 2023 snapshot; produces no new data by construction | **Low** — the only one of the three that paginates to real depth, but access is to an undocumented internal endpoint with no sanctioned read path; the binding constraint is permission, not capability | **Not assessable** — no sample obtained; no key held |
| **Fit — B: downstream analysis** | **Moderate** — large, and carries signals no other source has (playtime, purchase provenance, early-access flag); but the rating is boolean, so no star scale exists to align with any other source, and the sampled window is 77.5% Russian — filterable via the `language` field, at a large volume cost | **Low** — 50 reviews per app is a hard ceiling, so a corpus can only be widened by adding apps, never deepened; per-item analysis is capped at 50 rows and there is no verified flag and no stable user id | **High** — 571.54M reviews across 33 categories, the only source carrying both `verified_purchase` (48.0% in-sample) and `helpful_vote`, and perfectly repeatable by construction. *Scored on data fitness only — the licensing risk is scored in its own row and gates the recommendation, not this cell* | **Low** — 200+ per app with working pagination, but display names are not unique and there is no stable user id, so no per-reviewer analysis is possible; no verified-purchase flag | **Not assessable** — no sample obtained; no key held |

### Filling the two Fit rows

One line per cell, and each line should name **the single fact that decides it**, not a summary.
The deciding facts are already measured and sitting in the rows above:

| Source | The fact that decides A (recurring) | The fact that decides B (analysis) |
|---|---|---|
| Steam | cursor recycles; depth reachable is untested | boolean rating — no 1–5 scale to align, and 77.5% non-English in the sampled window |
| Apple | 50-row ceiling on a top-tier app | same ceiling — 50 rows per app is a hard limit on any modelling set |
| Amazon | static snapshot (already scored Low) | 571.54M reviews vs an unresolved licensing question |
| Google Play | 200+ and paging, but no sanctioned read path | no user id, no verified flag, unsanctioned access |
| Best Buy | eligibility gate is upstream of everything else | no sample exists — you cannot score this from documentation |

## Claims tested — see `test_notes.md`

1. **Apple RSS ≈ Google Play field shape** — tested on the same product. **Verdict: true about
   field shape, false about substitutability.** See `test_notes.md`.
2. **Best Buy ≈ Amazon field shape** — **not tested**, no key obtained. Left untested rather than
   filled from documentation.

## Recommendations

Two recommendations, argued separately. Both are **conditional**, and the conditions are named
tests rather than caveats — each one is a piece of work that would settle the question.

### A — Recurring collection: **Steam, conditional on a depth test**

**How the field narrows, on evidence:**

- **Amazon — disqualified.** A static 2023 snapshot cannot produce a review it did not already
  contain. This is structural, not a matter of quality.
- **Best Buy — cannot be assessed.** No sample was obtained. Separately, key issuance appears to
  be gated by email domain, which sits *upstream* of every other access property: a source you
  cannot get credentials for has no access profile to evaluate.
- **Google Play — capable but not permitted.** It paginates to real depth and re-pulls cleanly,
  and on capability alone it is the strongest of the three. But there is no sanctioned read path;
  access is to an undocumented internal endpoint. Recommending it for a *scheduled* pipeline would
  mean recommending recurring unsanctioned access, which is a licensing decision before it is an
  engineering one, and not one this evaluation can make.
- **Apple — the ceiling is not the problem; the contract is.** A 50-row cap limits backfill, but a
  scheduled poll only needs what is new since the last run, so the cap alone would not disqualify
  it. What does is that the feed is an undocumented legacy endpoint carrying no support guarantee,
  is scoped to one storefront per pull, and exposes no corpus total against which completeness
  could ever be checked.

**Which leaves Steam** — the only candidate whose access path is both documented and sanctioned,
and it re-pulled identically with stable ordering. Two conditions before committing:

1. **Test the reachable depth.** The cursor recycles when exhausted, and this sample walked only
   two pages. How many rows are actually retrievable for one title before recycling is unknown,
   and the 2,757,984 the API *reports* is not evidence of what is *pullable*. This is a
   half-hour test and it should be run before any commitment.
2. **Pin `language` and `purchase_type` explicitly.** Left at defaults, reported volume for a
   free-to-play title moves by ~192× (14,380 vs 2,757,984). A pipeline that does not pin them
   reports wrong numbers silently.

> ⚠️ **A question this evaluation cannot answer, and should not pretend to.** Steam covers PC
> games only. If the domain we actually need is e-commerce or mobile, Steam is the right answer to
> the wrong question, and the honest conclusion is that **no source in this shortlist is ready for
> job A** — the next step would be finding a sanctioned API in the target domain rather than
> choosing the least-constrained of these five. **What domain does the ingestion pipeline need to
> serve?** That answer changes this recommendation.

### B — Downstream analysis / modeling: **Amazon Reviews 2023, conditional on legal review**

On data fitness there is no close second. 571.54M reviews across 33 categories and 27 years; the
only source in the shortlist carrying **both** `verified_purchase` (48.0% of the sample) and
`helpful_vote`; a documented schema that the sample confirmed; and perfect repeatability, since a
static versioned file returns the same bytes every read. Nothing else here is within orders of
magnitude.

The objection is not the data. It is that **no license is stated anywhere** — no License field on
the dataset card, no LICENSE file in the repository — and the data is a third-party scrape of
Amazon, so there are two separate permission questions and the card answers neither. Absence is
worse than a restrictive tag: a non-commercial label would at least be an answer.

**Three questions counsel would need to settle**, in order:

1. Is there any grant of rights at all, or is the dataset simply published without terms?
2. If McAuley Lab has a redistribution right, does it extend to our use — and to caching or
   re-serving the reviews inside a product?
3. Does Amazon's own ToS govern the underlying content regardless of what the dataset says?

**If the answer is no**, there is no equivalent substitute. Steam is the only other source with
real depth, but a boolean recommendation is not a star rating and the corpus needs heavy language
filtering — it would be a different kind of dataset, not a replacement. **Apple and Google Play
are not viable for modeling at all**: 50 rows per app is a hard ceiling, and Google Play has no
stable user id, so neither supports per-reviewer or deep per-item analysis.

**Operational note if this proceeds:** stream the raw `.jsonl` directly. The dataset ships a
loading script, so `load_dataset(..., trust_remote_code=True)` executes remote code — the sampling
here deliberately avoided that path.

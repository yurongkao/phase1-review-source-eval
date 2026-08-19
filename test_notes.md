# Test Notes — per-source sample findings
---

## Steam
- **Endpoint used:** https://store.steampowered.com/appreviews/570?json=1&filter=recent&language=all&purchase_type=all&num_per_page=20&cursor=%2A
- **Item sampled:** appid 570
- **Fields actually returned:** app_release_date, author, comment_count, language, primarily_steam_deck, reactions, received_for_free, recommendationid, refunded, review, steam_purchase, timestamp_created, timestamp_updated, voted_up, votes_funny, votes_up, weighted_vote_score, written_during_early_access
  - nested `author`: avatar, last_played, num_games_owned, num_reviews, persona_status, personaname, playtime_at_review, playtime_forever, playtime_last_two_weeks, profile_url, steamid
- **Rows returned in one call:** 20 (requested 20; total pulled across 2 page(s): 40)
- **Pagination behavior:** opaque `cursor` token, `*` for page 1, next token returned in the response body; cursor repeats when exhausted
- **Repeatability:** re-pulled page 1 after ~2s: 20/20 same IDs, identical order = True
- **ID scheme:** review = `recommendationid`; item = Steam `appid`; author = `author.steamid`
- **⚠️ UNIT MISLABEL** This figure was recorded here as "volume unit B." It is **not**. By the convention in `scorecard.md`, unit B is the source's *full addressable corpus across all items*; 2,757,984 is the count for **one title**, which is unit A. Filed under B it would sit next to Amazon's 571.54M-review whole-dataset figure and invite a comparison between one game and thirty-three product categories. **Steam's unit B is not measured** — it would require enumerating every appid. Recording this rather than deleting it: John's feedback named consistent volume units specifically, and this is exactly the error he was pointing at, found in my own notes.
- **Reviews for this title (volume unit A, source-reported):** query_summary.total_reviews = 2757984 (positive 2222310 / negative 535674) — unscoped (language=all, purchase_type=all)
- **Total corpus size (volume unit B):** **NOT MEASURED.** Requires enumerating all appids; out of scope for this deliverable.
- **Reviews / representative item (volume unit A):** 40 rows retrieved over 2 pages at 20/call, no cap encountered. Steam reports 2,757,984 exist for this item, but how many are reachable through cursor paging before the cursor recycles is UNTESTED at this depth — the reported total is not the pullable amount.
- **Rating shape:** boolean `voted_up` (thumbs up/down), NOT a 1-5 star scale -- note this, it matters for cross-source comparability
- **Quality flags:** `steam_purchase`, `received_for_free`, `votes_up`, `votes_funny`, `weighted_vote_score`, `author.playtime_forever`
- **⚠️ Scoping trap (measured):** `query_summary.total_reviews` moves by ~192× depending on two params with non-obvious defaults. Steam's default `purchase_type=steam` excludes non-purchasers, which for a free-to-play title like Dota 2 hides almost the entire corpus: 14,380 scoped vs 2,757,984 unscoped. Any recurring pipeline must pin `language` and `purchase_type` explicitly or its volume numbers are silently wrong.
- **Data-quality limits noticed:** `refunded` / `received_for_free` / `written_during_early_access` rows are all included by default — each is a deliberate inclusion/exclusion decision for a pipeline, not a given.
  - ✅ **Language skew** The note previously said only "multilingual corpus; `language` field varies," which states nothing a reader can act on. Counted from the saved sample: **russian 31 · english 3 · ukrainian 3 · schinese 1 · italian 1** out of 40 rows — **77.5% Russian, 7.5% English.** Decision-relevant: an English-only downstream model would discard ~92% of this window. ⚠️ Scope: 40 rows from a `filter=recent` window on one title, so this is the *recent-review* language mix for Dota 2, **not** the title's lifetime mix and not Steam's.
  - 🐛 **CORRECTION — the `weighted_vote_score` type claim was wrong.** These notes said it "returns as a string, not a float." The saved sample says otherwise: **40/40 rows are JSON `float`**, and the pull script does no type coercion (checked). But the sharper point is that the sample cannot settle the question either way — **all 40 rows carry the identical default value `0.5` with `votes_up = 0`**, so no review with actual votes was observed. Corrected reading: *"observed as JSON float `0.5` in all 40 sampled rows; every sampled review had zero votes, so the type of a populated score is untested."* Same species as the errors logged all fortnight — a claim stated with more confidence than the evidence carries.
- **Raw sample saved to:** `samples/steam_dota2.json`

## Apple App Store
- **Endpoint used:** https://itunes.apple.com/us/rss/customerreviews/page=<n>/id=284882215/sortby=mostrecent/json
- **Item sampled:** app id 284882215 (us storefront)
- **Fields actually returned (raw entry keys):** author, content, id, im:contentType, im:rating, im:version, im:voteCount, im:voteSum, link, title, updated
- **Rows returned per page:** [50, 0] (page-by-page, not an average) — 50 rows total across 1 non-empty page(s)
- **Pagination behavior:** `page=<n>` path segment. Last page with rows = page 1; end of feed signalled by an empty page. ⚠️ Probe was allowed 15 pages but this app's feed ran out at page 2, so the ~10-page cap was never reached and remains UNTESTED. What is measured here is this app's feed depth, not Apple's cap.
- **Total corpus size (volume unit B):** ⚠️ NOT EXPOSED. The RSS feed publishes no review-count total for an app, so the addressable corpus size is unknowable from this source — you can only report what you pulled. This is a real asymmetry vs Steam (which reports `total_reviews`) and it limits any volume comparison.
- **Reviews / representative item (volume unit A):** 50 retrieved; this IS the ceiling for this app (probe walked to exhaustion).
- **Repeatability:** re-pulled page 1 after ~2s: 50/50 same IDs, identical order = True
- **ID scheme:** review = `id.label` (numeric review id); item = Apple `trackId`/app id; author has a `uri` but no stable public user id
- **Rating shape:** 1-5 stars. Observed in sample: {'1': 20, '2': 7, '3': 3, '4': 2, '5': 18} (⚠️ sortby=mostrecent, so this is a RECENCY-BIASED window of 50 reviews, not the app's lifetime rating distribution — do not present it as one)
- **Quality flags:** `im:voteCount` / `im:voteSum` present; NO verified-purchase flag; app metadata entry on page 1 = False
- **Data-quality limits noticed:** storefront-scoped (one country per pull), no verified-purchase flag, no corpus-size total, recency-biased ordering, legacy/undocumented endpoint, shallow feed depth: only 50 reviews retrievable for this app (page cap NOT tested — omitted on purpose)
- **Maintenance/access risk:** HIGH-ish -- this RSS feed is a legacy, undocumented endpoint Apple does not publish support guarantees for. Record it as observed behavior, not a documented contract.
- **Raw sample saved to:** `samples/apple_facebook.json`

## Amazon Reviews 2023
- **Endpoint / file used:** https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/review_categories/All_Beauty.jsonl
- **Item sampled:** category `All_Beauty`, **first 2000 lines (head of file, NOT a random sample)** — 1677 distinct parent_asin, 845 distinct users
- **Fields actually returned:** asin, helpful_vote, images, parent_asin, rating, text, timestamp, title, user_id, verified_purchase
- **Rows returned in one call:** n/a — static file; 2000 taken by choice
- **Pagination behavior:** none -- static line-delimited file; 'pagination' is just reading further into the file, fully deterministic
- **Repeatability:** perfect by construction -- static versioned file, same bytes every read (contrast with the live APIs)
- **ID scheme:** review has no standalone id — identity is (user_id, parent_asin, timestamp); item = `asin` / `parent_asin`
- **Total corpus size (volume unit B):** ~416,686–637,975 reviews ESTIMATED (file 326,611,506 bytes via `content-length`, divided by mean bytes-per-row measured in two windows: 784 at the head, 512 mid-file). Range, not a point value — the two windows disagree on row size by 35%. ⚠️ **Superseded — see the card figure directly below.** (The script's framing that "no review count exists" was true of the *data file*, but the dataset **card** publishes one; the estimate should never have been the headline number.)
  - ✅ **AUTHORITATIVE FIGURE: All_Beauty = 701.5K reviews** (632.0K users, 112.6K items, 31.6M review tokens). **Use this number in the scorecard**, labelled as a documentation figure.
  - ⚠️ **The byte-based estimate MISSED, and that is worth recording.** 417k–638k does **not** contain 701.5K — it undershot by ~10% even at the top of the range. Cause: both sampling windows measured row sizes (784 and 512 bytes) above the file's true average, so the two windows were biased in the *same* direction. **A range built from two samples is not a confidence interval.** Kept here deliberately: the method was reasonable, it was checkable, and it was wrong — which is exactly the standard of evidence this deliverable is arguing for. Where a source publishes a real count (Steam's `query_summary`, this card), that count wins; byte estimation is a last resort for sources that publish nothing (Apple).
  - Whole-dataset context from the card: **571.54M reviews · 54.51M users · 48.19M items · 33 categories · May 1996 – Sep 2023 · 750 GB total.** Largest corpus in the shortlist by orders of magnitude.
  - ⚠️ Label inconsistency in the card: the per-category table heads this column **#Rating** while the version-comparison table calls the equivalent **#Review**. Treating them as the same quantity; noting it rather than silently assuming.
- **Reviews / representative item (volume unit A):** ✅ **6.2 reviews per item on average** (card: 701.5K reviews ÷ 112.6K items, All_Beauty). Documentation figure, and a *mean* over a long-tailed distribution — the median item has far fewer. Contrast worth drawing in the scorecard: **Steam reports 2.76M reviews on a single title; Amazon averages ~6 per product.** Same "volume unit," completely different shape, and it decides what per-item analysis is even possible on each source.
  - ⚠️ **NOT OBTAINABLE from a random slice — do not report the 1.2 rows/parent_asin the script printed.** Because the file is not clustered by item (below) and 2,000 rows is a tiny fraction of the corpus, almost every sampled review lands on a different product *regardless of the true per-item rate*. 1.2 is a sampling artifact, not a property of the category. ✅ Resolved via the card's **#reviews ÷ #items** (above). The only way to *measure* it rather than cite it would be to filter the full category file for one representative `parent_asin` and count — not worth the time for this deliverable, so the cell is labelled a documentation figure.
  - Side note the collisions *do* support: 2,000 draws returned 1,677 distinct items (323 repeats). Under a uniform-item model that implies ~5,500 items in the category; real review counts are long-tailed, so the true item count is higher and the per-item mean lower. Directional only.
- **Rating shape:** ⚠️ **1–5 as a JSON `float`** (verified: 2000/2000 rows are Python `float`, e.g. `5.0`) — **not an integer.** Observed in slice: {1.0: 125, 2.0: 122, 3.0: 214, 4.0: 396, 5.0: 1143} (mean 4.16), slice-scoped, see representativeness below.
  - **Cross-source note — four sources, four rating types:** Amazon `float` · Google Play `score` `int` · Apple `im:rating` **`str`** · Steam boolean `voted_up`. Every one needs its own parse step before a common scale exists. This is concrete evidence for the "what reuse would require" verdicts, not a footnote.
- **Time coverage of slice:** 2004-08-15 → 2023-03-11 — ~19 years in the first 2,000 lines, so **the file is NOT sorted by date.**
- **✅ Head is not clustered (measured):** 1,677 distinct `parent_asin` in 2,000 rows and a 19-year date span → the head is not grouped by item or by time. This is *why* the borderline representativeness verdict below is worth something: the head slice is a broad draw, not a corner of the file.
- **Quality flags:** `verified_purchase` present and explicitly populated (960 `True` / 1040 `False` — **48.0% verified**), `helpful_vote` present (max 430, 73.7% zero), 262 rows carry images.
  - **Decision-relevant:** filtering to verified purchases discards **just over half** this corpus. That is a real cost to weigh, and it is a choice the sources with no verified flag at all (Apple, Google Play) do not even offer.
- **Data-quality limits noticed:** 1 empty-text row in the slice; no review id; helpful_vote heavily zero-skewed; historical snapshot (not live) so it cannot serve a recurring-collection use case on its own
- **📄 Documentation inconsistency (found by comparing the pull against both docs):** the HF card's field table specifies `timestamp` and `helpful_vote`, but the project site's own "Load User Reviews" example prints a **different schema** — `sort_timestamp`, `helpful_votes` (plural), no `timestamp`, and `images` as dicts with `small/medium/large_image_url`. **My pull matches the HF card, not the project-site example** (`timestamp` int, `helpful_vote` int, `images` list). Two official docs for the same dataset disagree; the sample settles it. Concrete argument for sampling over reading documentation — which is the thesis of this whole deliverable.
  - Card schema confirmed against the pull: `rating` float · `title` str · `text` str · `images` list · `asin` str · `parent_asin` str · `user_id` str · `timestamp` int (unix) · `verified_purchase` bool · `helpful_vote` int. **Card explicitly says: use `parent_asin`, not `asin`, to join to product metadata** — variants (colour/size/style) share a parent. Any cross-source item join must use `parent_asin`.
- **Representativeness of the slice (measured, not assumed):**
    - middle probe: read 1952 rows from a 1000 kB window at byte 163,305,753
    - head rating % : {1.0: 6.2, 2.0: 6.1, 3.0: 10.7, 4.0: 19.8, 5.0: 57.1}
    - middle rating %: {1.0: 12.6, 2.0: 6.2, 3.0: 8.2, 4.0: 11.9, 5.0: 61.0}
    - middle slice time coverage: 2006-09-14 → 2023-04-19
    - **borderline -- max gap 7.9 pp between head and middle. Usable directionally, but label it as a slice, not the category.**
    - **Direction of the drift (worth one line in the scorecard):** the mid-file window is *more polarised* — 1★ 6.2%→12.6% (+6.4 pp) and 4★ 19.8%→11.9% (−7.9 pp), so 1★+5★ combined rises 63.3%→73.6%. Mean rating 4.15→4.02. Any rating-distribution statistic taken from one window of this file carries a few points of error; report the shape, not a precise percentage.
- **Licensing / permitted use:** ⚠️ **NO LICENSE IS DECLARED.** Checked 2026-08-16 against the dataset card and the repo file tree.
  - **Declared license tag: ABSENT.** The card's metadata sidebar lists Languages, Size, ArXiv and Tags — there is **no License field at all**. Most HF dataset cards render one; this one does not.
  - **LICENSE file: ABSENT.** Repo root contains `.gitattributes`, `Amazon-Reviews-2023.py`, `README.md`, `all_categories.txt`, `asin2category.json` and the data directories. No LICENSE, no terms-of-use file.
  - **Citation:** a BibTeX entry is provided under a "Citation" heading (Hou et al., *Bridging Language and Items for Retrieval and Recommendation*, arXiv:2403.03952, 2024). ⚠️ It is **offered, not stated as a condition of use** — the card never says "you must cite." Academic convention expects it; that is not the same as a license term. Do not upgrade this to a requirement in the scorecard.
  - **Commercial / non-commercial:** the card is **silent**. There is no restriction to research use — and equally **no grant of commercial permission**. Record as "not addressed," never as "allowed."
  - **Redistribution:** **not addressed.** Relevant because a pipeline that caches or re-serves these reviews is redistributing them, and nothing on the card speaks to that.
  - **Provenance — the part that actually decides this:** the data was **scraped from Amazon by a third party** (McAuley Lab, UCSD) and is mirrored on UCSD servers (`mcauleylab.ucsd.edu`, `datarepo.eng.ucsd.edu`) as well as HF. Even a permissive license from McAuley Lab would only cover *their* redistribution — it cannot grant rights over Amazon's underlying content or override Amazon's terms. **Two separate permission questions, and the card answers neither.**
  - **➡️ Scorecard entry: "NO STATED LICENSE — needs legal review before any commercial use."** This is a *worse* position than a restrictive license, not a better one: a non-commercial tag would at least be a clear answer. Absence means the permission question is open, and only counsel can close it.
  - **📌 Why this belongs in the recommendation, not a footnote:** for use case **B (downstream analysis / modeling)** this is by far the richest corpus available and the licensing risk is the *only* serious objection to it. For use case **A (recurring collection)** it is disqualified anyway — a static 2023 snapshot cannot serve a recurring pipeline. So the licensing gap is decision-relevant for exactly one of the two jobs, which is the kind of split John asked for.
  - **Operational note for a pipeline:** the HF dataset viewer is **disabled** because the repo ships a loading script requiring arbitrary code execution — `load_dataset(..., trust_remote_code=True)` executes remote code. Streaming the raw `.jsonl` directly (what this pull did) avoids that, and is the safer ingestion path to recommend.
  - Sources: card <https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023> · file tree <https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main> · project site <https://amazon-reviews-2023.github.io/>
- **Raw sample saved to:** `samples/amazon_all_beauty.json`

## Google Play
- **Endpoint / file used:** google-play-scraper -> Google internal `batchexecute` (UNDOCUMENTED, no public reviews API exists)
- **Item sampled:** com.facebook.katana (us/en)
- **Fields actually returned:** appVersion, at, content, repliedAt, replyContent, reviewCreatedVersion, reviewId, score, thumbsUpCount, userImage, userName
- **Rows returned in one call:** 200 (requested 200)
- **Pagination behavior:** continuation token returned after 200 rows (token present = True); page size is capped per call, paging is opaque-cursor based
- **Repeatability:** re-pulled first 50 after ~2s: 50/50 same IDs, identical order = True
- **ID scheme:** review = `reviewId` (opaque string); item = package name; user = display name only, NO stable user id
- **Rating shape:** 1-5 integer `score`. Observed: {1: 40, 2: 6, 3: 12, 4: 10, 5: 132}
- **Quality flags:** `thumbsUpCount` present; NO verified-purchase flag; developer replies on 0/200 rows
- **Data-quality limits noticed:** locale-scoped, no user id, display names are not unique, sort=NEWEST means the window moves between pulls
- **Maintenance/access risk:** HIGH -- unofficial access to an internal endpoint; can break without notice
- **Licensing / permitted use:** NOT cleared -- no sanctioned read API. Score this column as 'needs-check / likely not permitted', not blank.
- **Raw sample saved to:** `samples/googleplay_facebook.json`

## Best Buy

**NOT SAMPLED — no API key was ever obtained.** A pull was attempted 2026-08-17 with a
placeholder value in `BESTBUY_API_KEY`, which the API rejected with **HTTP 403**. That
403 means only "this string is not a valid key." It is not evidence of anything about
Best Buy. No rows were retrieved, so every observational cell below stays empty.

- **Pull date:** not sampled — no key held; 
- **Endpoint / file used:** `https://api.bestbuy.com/v1/reviews(sku={sku})` — official,
  documented, key-required. *Recorded from documentation; not confirmed by a successful call.*
- **Item sampled:** none
- **Fields actually returned:** not sampled
- **Rows returned in one call:** not sampled
- **Pagination behavior:** not sampled. *(Documentation describes `page`/`pageSize` params
  with server-reported `total` and `totalPages`. Untested — do not score as verified.)*
- **Repeatability:** not sampled
- **ID scheme:** item = `sku`. *Documentation-level.* Note that `sku` is not derivable from
  Amazon's `asin`; a cross-source join would need a UPC/GTIN bridge.
- **Rating shape:** not sampled
- **Quality flags:** not sampled
- **Data-quality limits noticed:** not sampled
- **Maintenance/access risk:** not assessed. Nothing here is inferable from the 403.
- **Access eligibility:** ⚠️ **a gate, not just a delay.** Best Buy
  [announced in 2016](https://medium.com/best-buy-developers/announcing-a-change-to-best-buy-s-api-access-b09afc4bc27a)
  that it "no longer take[s] new key requests if the email listed is from a free email
  service" (Gmail/Yahoo etc.), moving to company-associated accounts. An educational
  program for `.edu` users was described as planned. **Caveat: this announcement is from
  2016 and the developer blog stopped publishing in 2017; current enforcement is
  unverified.** Recorded as a documented policy statement, not as a tested outcome.
- **Licensing / permitted use:** official API with published terms at
  developer.bestbuy.com/legal. *Documentation-level.* Still the contrast case to Google
  Play's absent read path and Amazon's absent license — provided it is labelled as
  documentation and no observational cell is filled from it.
- **Raw sample saved to:** none

> **Why this row is worth keeping despite having no data.** Best Buy was shortlisted as the
> "clean access" contrast: smaller corpus, documented terms, fully enumerable. That
> argument survives without a sample — but it now needs one qualification. "Free, documented
> API" understates the cost of entry if key issuance is restricted by email domain. For
> **job A (recurring collection)**, eligibility to obtain credentials at all is upstream of
> every other access property, and it is the kind of thing a source list built from
> documentation would miss entirely.
>
> Re-runnable in ~10 minutes via `scripts/bestbuy_reviews.py` if a key is ever obtained.

---

## Cross-source claim tests

> Run `scripts/compare_shapes.py --a <sample> --b <sample> --claim "..."` on the two
> saved samples. It prints a concept-by-concept table plus the rating/ID/pagination
> differences and drafts the bullets below. **It does not write the verdict** — field
> overlap alone does not justify pipeline reuse. Write what reuse *would require*
> ("same extraction logic, separate rating-normalization and pagination adapters")
> rather than "similar."

### Claim 1 — Apple RSS ≈ Google Play field shape

**Tested on the same product** (Facebook: `284882215` / `com.facebook.katana`), pulled
2026-08-15. Samples: `samples/apple_facebook.json` (50 rows),
`samples/googleplay_facebook.json` (200 rows). Raw output:
`samples/claim1_apple_vs_googleplay.txt`.

- **Apple fields:** `author`, `content`, `id`, `rating`, `title`, `updated`, `version`,
  `vote_count`, `vote_sum`
- **Google Play fields:** `appVersion`, `at`, `content`, `repliedAt`, `replyContent`,
  `reviewCreatedVersion`, `reviewId`, `score`, `thumbsUpCount`, `userImage`, `userName`
- **Actual differences (fields / pagination / IDs):**
  - **Shared concepts: 8 of 13** — review_id, user_id, rating, body, timestamp,
    helpful_votes, app_version, **item_id**. *(Note: `compare_shapes.py` prints item_id as
    "neither" because it only inspects per-row fields. Both sources do expose the item id,
    at the envelope. The tool's count of 7 is wrong; 8 is correct.)*
  - **Asymmetric fields:** Apple-only `title`; Google Play-only `developer_reply`
    (`replyContent` + `repliedAt`). A common schema needs both as nullable.
  - **Rating:** same 1–5 scale, different JSON type — Apple `str`, Google Play `int`.
  - **Item identity:** both **envelope-level only**, constant per pull, must be stamped
    onto rows at ingestion. Identical handling on both sides.
  - **Pagination:** Apple = numbered pages. Google Play = opaque continuation token
    (still present after 200 rows). Different control flow, not a different parameter.
  - **Depth returned:** Apple **50 reviews total**, feed exhausted at page 2, for one of
    the most-reviewed apps on the store. Google Play returned 200 with more available.
  - **Repeatability:** both re-pulled 50/50 identical IDs in identical order after ~2s.
    This tests a 2-second window only — day-to-day ordering stability is untested.

- **What porting a working Google Play ingester to Apple would require:**
  1. A field-alias table (`reviewId`→`id`, `score`→`rating`, `at`→`updated`,
     `thumbsUpCount`→`vote_count`, `userName`→`author`, `reviewCreatedVersion`→`version`)
  2. A rating cast, `str` → `int`
  3. Two nullable columns for the asymmetric fields
  4. A second pagination strategy — numbered pages alongside cursor paging
  5. **No change to item-identity handling** — the envelope-stamp step the Google Play
     path already has carries over unmodified. This is the one piece that genuinely reuses.

  Items 1–3 are one-liners. Item 4 is a second control flow in the collector.

- **Verdict:** Every field-level difference between the two sources is mechanical — six
  aliases, a `str`→`int` rating cast, and two nullable columns for Apple's `title` and
  Google Play's developer reply — and item identity, envelope-level on both, needs no change
  at all; **at the level of field shape the claim holds.** What does not carry over is the
  collector: Apple pages by numbered path segment and terminates on an empty page, Google
  Play by opaque continuation token, so an existing Google Play ingester gains a **second
  control flow, not a parameter** — and Apple returned **50 reviews in total** for one of the
  most-reviewed apps on the store, against Google Play's 200 with more available. **The claim
  is therefore true about shape and false about substitutability:** Apple can be added to a
  Google Play pipeline cheaply, but it cannot serve **job A (recurring collection)** at any
  useful volume regardless of how well the fields align, so what the field overlap justifies
  is a **shared schema, not a shared source.**


### Claim 2 — Best Buy ≈ Amazon field shape

**NOT TESTED — no Best Buy API key was obtained. See the `## Best Buy` section above.**

- **Best Buy fields:** not sampled — no key held
- **Amazon fields:** `asin`, `parent_asin`, `rating`, `title`, `text`, `timestamp`,
  `helpful_vote`, `verified_purchase`, `user_id`, `images`
  (from `samples/amazon_all_beauty.json`, 2,000 rows)
- **Actual differences:** not tested. One side of this comparison has no sample, so no
  field-level claim is recorded here. The Amazon column above is evidence; the Best Buy
  column would be documentation, and this deliverable does not mix the two.
- **Verdict:** Not tested. No Best Buy API key was obtained, so this claim has one side
  with no sample. Deliberately left untested rather than filled from Best Buy's API
  documentation. `scripts/bestbuy_reviews.py` is written and verified against a synthetic
  fixture; the claim is ~10 minutes' work if a key is ever obtained.

> **⚠️ The 403 is not evidence.** A placeholder string was sent as the key, so the rejection
> says only that the string was invalid. It says nothing about corpus size, field shape,
> pagination, or licensing, and must not be scored anywhere as "Best Buy: not accessible."
>
> The substantive access finding is separate and comes from Best Buy's own published
> announcement, not from this attempt: **key issuance appears to be gated by email domain**
> (see the `## Best Buy` section). Unverified for 2026, and recorded with that caveat.

> **Known in advance, and still not a substitute for testing:** Best Buy identifies items
> by `sku`, Amazon by `asin`. Neither is derivable from the other, so any cross-source
> item join needs a UPC/GTIN bridge. This is a documentation-level fact and is recorded
> as such — it is *not* a claim-test result.

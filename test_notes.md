# Test Notes — per-source sample findings

Record what the **sample pull actually returned**, not what the docs claim. Fill Fri–Sat.

Template to copy for each source:

---

## <Source name>

- **Pull date:**
- **Endpoint / file used:**
- **Item sampled (id + name):**
- **Fields actually returned:** (list every field key seen in the raw response)
- **Rows returned in one call:**
- **Pagination behavior:** (cursor? page param? hard cap? how to get the next page)
- **Repeatability:** (re-pull same item → same rows? ordering stable? any randomness?)
- **ID scheme:** (what uniquely identifies a review / an item)
- **Rating shape:** (scale, distribution you observed in the sample)
- **Quality flags:** (verified / helpful / vote counts present?)
- **Data-quality limits noticed:** (dupes, truncation, missing fields, language mix)
- **Raw sample saved to:** `samples/<file>`

---

## Steam
- **Pull date:** 2026-08-15
- **Endpoint used:** https://store.steampowered.com/appreviews/570?json=1&filter=recent&language=all&purchase_type=all&num_per_page=20&cursor=%2A
- **Item sampled:** appid 570
- **Fields actually returned:** app_release_date, author, comment_count, language, primarily_steam_deck, reactions, received_for_free, recommendationid, refunded, review, steam_purchase, timestamp_created, timestamp_updated, voted_up, votes_funny, votes_up, weighted_vote_score, written_during_early_access
  - nested `author`: avatar, last_played, num_games_owned, num_reviews, persona_status, personaname, playtime_at_review, playtime_forever, playtime_last_two_weeks, profile_url, steamid
- **Rows returned in one call:** 20 (requested 20; total pulled across 2 page(s): 40)
- **Pagination behavior:** opaque `cursor` token, `*` for page 1, next token returned in the response body; cursor repeats when exhausted
- **Repeatability:** re-pulled page 1 after ~2s: 20/20 same IDs, identical order = True
- **ID scheme:** review = `recommendationid`; item = Steam `appid`; author = `author.steamid`
- **Total corpus size (volume unit B):** query_summary.total_reviews = 2757984 (positive 2222310 / negative 535674) — unscoped (language=all, purchase_type=all) = whole corpus
- **Reviews / representative item (volume unit A):** 40 rows retrieved over 2 pages at 20/call, no cap encountered. Steam reports 2,757,984 exist for this item, but how many are reachable through cursor paging before the cursor recycles is UNTESTED at this depth — the reported total is not the pullable amount.
- **Rating shape:** boolean `voted_up` (thumbs up/down), NOT a 1-5 star scale -- note this, it matters for cross-source comparability
- **Quality flags:** `steam_purchase`, `received_for_free`, `votes_up`, `votes_funny`, `weighted_vote_score`, `author.playtime_forever`
- **⚠️ Scoping trap (measured):** `query_summary.total_reviews` moves by ~192× depending on two params with non-obvious defaults. Steam's default `purchase_type=steam` excludes non-purchasers, which for a free-to-play title like Dota 2 hides almost the entire corpus: 14,380 scoped vs 2,757,984 unscoped. Any recurring pipeline must pin `language` and `purchase_type` explicitly or its volume numbers are silently wrong.
- **Raw sample saved to:** `samples/steam_dota2.json`

## Apple App Store
- **Pull date:** 2026-08-15
- **Endpoint used:** https://itunes.apple.com/us/rss/customerreviews/page=<n>/id=284882215/sortby=mostrecent/json
- **Item sampled:** app id 284882215 (us storefront)
- **Fields actually returned (raw entry keys):** author, content, id, im:contentType, im:rating, im:version, im:voteCount, im:voteSum, link, title, updated
- **Rows returned per page:** [50, 0] (page-by-page, not an average) — 50 rows total across 1 non-empty page(s)
- **Pagination behavior:** `page=<n>` path segment. Last page with rows = page 1; end of feed signalled by an empty page. Probed to 15 pages, so the ~10-page cap claim IS tested here.
- **Total corpus size (volume unit B):** ⚠️ NOT EXPOSED. The RSS feed publishes no review-count total for an app, so the addressable corpus size is unknowable from this source — you can only report what you pulled. This is a real asymmetry vs Steam (which reports `total_reviews`) and it limits any volume comparison.
- **Reviews / representative item (volume unit A):** 50 retrieved; this IS the ceiling for this app (probe walked to exhaustion).
- **Repeatability:** re-pulled page 1 after ~2s: 50/50 same IDs, identical order = True
- **ID scheme:** review = `id.label` (numeric review id); item = Apple `trackId`/app id; author has a `uri` but no stable public user id
- **Rating shape:** 1-5 stars. Observed in sample: {'1': 20, '2': 7, '3': 3, '4': 2, '5': 18} (⚠️ sortby=mostrecent, so this is a RECENCY-BIASED window of 50 reviews, not the app's lifetime rating distribution — do not present it as one)
- **Quality flags:** `im:voteCount` / `im:voteSum` present; NO verified-purchase flag; app metadata entry on page 1 = False
- **Data-quality limits noticed:** storefront-scoped (one country per pull), no verified-purchase flag, no corpus-size total, recency-biased ordering, legacy/undocumented endpoint, page cap confirmed by probe
- **Maintenance/access risk:** HIGH-ish -- this RSS feed is a legacy, undocumented endpoint Apple does not publish support guarantees for. Record it as observed behavior, not a documented contract.
- **Raw sample saved to:** `samples/apple_facebook.json`

## Amazon Reviews 2023
- **Pull date:** TBD (Sat 8/15)

## Google Play
- **Pull date:** TBD (Sat 8/15)

## Best Buy
- **Pull date:** TBD (Sat 8/15, optional)

---

## Cross-source claim tests

> Run `scripts/compare_shapes.py --a <sample> --b <sample> --claim "..."` on the two
> saved samples. It prints a concept-by-concept table plus the rating/ID/pagination
> differences and drafts the bullets below. **It does not write the verdict** — field
> overlap alone does not justify pipeline reuse. Write what reuse *would require*
> ("same extraction logic, separate rating-normalization and pagination adapters")
> rather than "similar."

### Claim 1 — Apple RSS ≈ Google Play field shape
- **Apple fields:** TBD
- **Google Play fields:** TBD
- **Actual differences (fields / pagination / IDs):** TBD
- **Verdict:** TBD (reuse justified? or different enough to need separate handling?)

### Claim 2 — Best Buy ≈ Amazon field shape
- **Best Buy fields:** TBD
- **Amazon fields:** TBD
- **Actual differences:** TBD
- **Verdict:** TBD

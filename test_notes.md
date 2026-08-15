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
- **Reviews / representative item (volume unit A):** 2757984 addressable via cursor paging at up to 100 rows/call (the 20 rows above is the page size chosen, NOT a source limit)
- **Rating shape:** boolean `voted_up` (thumbs up/down), NOT a 1-5 star scale -- note this, it matters for cross-source comparability
- **Quality flags:** `steam_purchase`, `received_for_free`, `votes_up`, `votes_funny`, `weighted_vote_score`, `author.playtime_forever`
- **Raw sample saved to:** `samples/steam_dota2.json`

## Apple App Store
- **Pull date:** TBD (Fri 8/14)
- (fill from `scripts/apple_rss_reviews.py` output)

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

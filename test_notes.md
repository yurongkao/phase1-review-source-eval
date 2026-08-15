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
- **Pull date:** TBD (Fri 8/14)
- (fill from `scripts/steam_reviews.py` output)

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

"""
Cross-source shape comparator -- the tool that TESTS the two assumed claims.

John's objection was that "Apple RSS mirrors Google Play" and "Best Buy is the
same shape as Amazon" were ASSERTED, not tested. This script turns each claim
into an evidence table: which canonical review concepts each source actually
carries, which fields have no counterpart, and where the identifier and
pagination models genuinely differ.

It deliberately does NOT print a yes/no verdict. Field overlap alone does not
justify pipeline reuse -- an identical field list with incompatible ID schemes
or a different rating scale is still two ingestion paths. The script surfaces
the evidence and drafts the wording; you write the verdict.

Usage:
    python compare_shapes.py --a ../samples/apple_facebook.json \
                             --b ../samples/googleplay_facebook.json \
                             --claim "Apple RSS mirrors Google Play field shape"

Works on any two sample files written by the sampler scripts in this folder
(they all share the {source, reviews: [...], ...} envelope).
"""
import argparse
import json
from collections import Counter

# Canonical review concepts an ingestion pipeline actually needs, and the field
# names each source uses for them. Extend as you sample more sources -- this
# table IS the reusability argument, so keep it honest.
ALIASES = {
    "review_id":        ["id", "reviewId", "review_id", "recommendationid", "Id"],
    "item_id":          ["appid", "app_id", "parent_asin", "asin", "sku", "trackId",
                         "product_id"],
    "user_id":          ["author", "userName", "user_id", "reviewerId", "author_id",
                         "steamid"],
    "rating":           ["rating", "score", "stars", "overall", "im:rating"],
    "recommend_bool":   ["voted_up", "recommended"],
    "title":            ["title", "reviewTitle", "headline"],
    "body":             ["content", "text", "review", "comment", "body"],
    "timestamp":        ["updated", "at", "timestamp", "timestamp_created", "date",
                         "submissionTime"],
    "helpful_votes":    ["vote_count", "vote_sum", "thumbsUpCount", "helpful_vote",
                         "votes_up", "helpfulness"],
    "verified_purchase": ["verified_purchase", "verified", "steam_purchase",
                          "verifiedPurchaser"],
    "app_version":      ["version", "reviewCreatedVersion", "appVersion"],
    "language":         ["language", "lang"],
    # NOTE: `comment` is deliberately NOT listed here -- on Best Buy `comment` is the
    # review body, and letting it match here double-maps one field to two concepts
    # and invents a developer-reply capability the source does not have.
    "developer_reply":  ["replyContent", "repliedAt"],
}


def load(path):
    with open(path) as f:
        return json.load(f)


def review_field_keys(payload):
    """Union of keys across sampled reviews + how often each appears."""
    reviews = payload.get("reviews", [])
    counter = Counter()
    for r in reviews:
        if isinstance(r, dict):
            counter.update(r.keys())
    return counter, len(reviews)


def canonical_map(field_counter):
    """concept -> field name found (or None). One field may only serve one concept:
    double-mapping inflates the overlap count and is exactly the kind of soft
    evidence John pushed back on."""
    lowered = {k.lower(): k for k in field_counter}
    out, claimed = {}, set()
    for concept, names in ALIASES.items():
        hit = None
        for n in names:
            cand = lowered.get(n.lower())
            if cand and cand not in claimed:
                hit = cand
                claimed.add(cand)
                break
        out[concept] = hit
    return out


def unmapped(field_counter, cmap):
    claimed = {v for v in cmap.values() if v}
    return sorted(k for k in field_counter if k not in claimed)


ENVELOPE_ITEM_KEYS = ["appid", "app_id", "sku", "asin", "category", "product_id"]


def rating_shape(payload, cmap):
    """Returns (kind, human description). Read the field name from the canonical
    map -- Apple calls it `rating`, Google Play calls it `score`, and hardcoding
    one of them silently reports 'no rating' for the other."""
    rows = [r for r in payload.get("reviews", []) if isinstance(r, dict)]
    field = cmap.get("rating")
    if field:
        vals = [r.get(field) for r in rows if r.get(field) is not None]
        if vals:
            pytypes = sorted({type(v).__name__ for v in vals})
            try:
                nums = sorted({float(v) for v in vals})
                return ("numeric",
                        f"numeric {nums[0]:g}-{nums[-1]:g} via `{field}` "
                        f"(json type: {'/'.join(pytypes)}), "
                        f"distinct values: {[f'{n:g}' for n in nums]}")
            except (TypeError, ValueError):
                return ("categorical",
                        f"non-numeric `{field}`, values: {sorted(set(map(str, vals)))[:8]}")
    bfield = cmap.get("recommend_bool")
    if bfield:
        bools = [r.get(bfield) for r in rows if r.get(bfield) is not None]
        if bools:
            return ("boolean",
                    f"boolean `{bfield}` ({sum(1 for b in bools if b)}/{len(bools)} positive) "
                    f"-- NO star scale exists on this source")
    return ("none", "no rating field found in the sampled rows")


def pagination_summary(payload):
    """Prefer an explicit note. Otherwise summarise the log -- taking log[-1] blindly
    grabs whatever trailing indented remark the sampler happened to print
    ('  -> page 2 empty...'), which reads as gibberish in the deliverable."""
    if payload.get("pagination_note"):
        return payload["pagination_note"]
    log = payload.get("pagination_log") or []
    page_lines = [l for l in log if l.strip().lower().startswith("page ")]
    if not page_lines:
        return "not recorded"
    tail = [l for l in log if l.strip().startswith("->") or "stop" in l.lower()
            or "exhaust" in l.lower()]
    summary = f"{len(page_lines)} page request(s): " + "; ".join(l.strip() for l in page_lines)
    if tail:
        summary += f" — ended: {tail[-1].strip().lstrip('-> ')}"
    return summary


def json_type(rating_desc):
    """Pull the 'json type: X' tag back out of a rating description."""
    marker = "json type: "
    if marker in rating_desc:
        return rating_desc.split(marker, 1)[1].split(")", 1)[0]
    return "unknown"


def item_id_note(payload, cmap):
    """An item id at envelope level (one app/sku per pull) is still an item id --
    just a constant one. Say which it is; the distinction matters for joins."""
    if cmap.get("item_id"):
        return f"per-row field `{cmap['item_id']}`"
    for k in ENVELOPE_ITEM_KEYS:
        if k in payload:
            return f"envelope-level only (`{k}` = {payload[k]}) -- constant per pull, must be stamped onto rows during ingestion"
    return None


def describe(path):
    p = load(path)
    counter, n = review_field_keys(p)
    cmap = canonical_map(counter)
    kind, desc = rating_shape(p, cmap)
    return {
        "path": path,
        "source": p.get("source", "unknown"),
        "n_reviews": n,
        "fields": counter,
        "cmap": cmap,
        "unmapped": unmapped(counter, cmap),
        "rating_kind": kind,
        "rating": desc,
        "item_id": item_id_note(p, cmap),
        "pagination": pagination_summary(p),
        "repeatability": p.get("repeatability", "not recorded"),
    }


def render(a, b, claim):
    lines = []
    w = 20
    lines.append("=" * 78)
    lines.append(f"CLAIM UNDER TEST: {claim}")
    lines.append("=" * 78)
    lines.append(f"A = {a['source']}  ({a['n_reviews']} reviews, {a['path']})")
    lines.append(f"B = {b['source']}  ({b['n_reviews']} reviews, {b['path']})")
    lines.append("")
    lines.append(f"{'concept'.ljust(w)}{'A field'.ljust(26)}{'B field'.ljust(26)}match")
    lines.append("-" * 78)

    both = missing_a = missing_b = 0
    for concept in ALIASES:
        fa, fb = a["cmap"][concept], b["cmap"][concept]
        if fa and fb:
            mark, both = "both", both + 1
        elif fa:
            mark, missing_b = "A only", missing_b + 1
        elif fb:
            mark, missing_a = "B only", missing_a + 1
        else:
            mark = "neither"
        lines.append(f"{concept.ljust(w)}{str(fa or '-').ljust(26)}{str(fb or '-').ljust(26)}{mark}")

    lines.append("-" * 78)
    lines.append(f"shared concepts: {both}   A-only: {missing_b}   B-only: {missing_a}")
    lines.append("")
    lines.append(f"Fields in A with no canonical mapping: {a['unmapped'] or 'none'}")
    lines.append(f"Fields in B with no canonical mapping: {b['unmapped'] or 'none'}")
    lines.append("")
    lines.append("NOT just fields -- these decide whether one pipeline can serve both:")
    lines.append(f"  rating shape   A: {a['rating']}")
    lines.append(f"                 B: {b['rating']}")
    lines.append(f"  item identity  A: {a['item_id'] or 'NONE FOUND'}")
    lines.append(f"                 B: {b['item_id'] or 'NONE FOUND'}")
    lines.append(f"  pagination     A: {a['pagination']}")
    lines.append(f"                 B: {b['pagination']}")
    lines.append(f"  repeatability  A: {a['repeatability']}")
    lines.append(f"                 B: {b['repeatability']}")
    lines.append("")

    blockers = []
    if a["rating_kind"] != b["rating_kind"]:
        blockers.append(f"rating is {a['rating_kind']} on A but {b['rating_kind']} on B -- "
                        "not a shared parser; needs an explicit normalization decision "
                        "(and if one side is boolean, a star scale cannot be recovered)")
    elif a["rating_kind"] == "numeric" and json_type(a["rating"]) != json_type(b["rating"]):
        blockers.append(f"both ratings are numeric but arrive as different JSON types "
                        f"({json_type(a['rating'])} vs {json_type(b['rating'])}) -- same "
                        f"scale, different parse; cheap to fix, but it is a difference, "
                        f"so record it rather than calling the shapes identical")
    if a["item_id"] is None or b["item_id"] is None:
        blockers.append("at least one source exposes no item identifier at all -- "
                        "cross-source joins would fall back to name matching")
    elif ("envelope-level" in (a["item_id"] or "")) != ("envelope-level" in (b["item_id"] or "")):
        blockers.append("item identity lives per-row on one source and per-pull on the "
                        "other -- the ingestion step differs even though both 'have' an id")
    if bool(a["cmap"]["verified_purchase"]) != bool(b["cmap"]["verified_purchase"]):
        blockers.append("only one source carries a verified-purchase signal -- any "
                        "quality filter would behave differently per source")
    if a["cmap"]["review_id"] and b["cmap"]["review_id"] and \
            a["cmap"]["review_id"] != b["cmap"]["review_id"]:
        blockers.append(f"review-id keys differ ({a['cmap']['review_id']} vs "
                        f"{b['cmap']['review_id']}) -- trivial to alias, note it anyway")

    lines.append("Concrete differences a reuse claim has to answer:")
    for blk in (blockers or ["none detected from the sampled rows"]):
        lines.append(f"  - {blk}")
    lines.append("")
    lines.append("=" * 78)
    lines.append("DRAFT FOR test_notes.md (edit the verdict yourself -- do not paste blind)")
    lines.append("=" * 78)
    lines.append(f"- **{a['source']} fields:** {', '.join(sorted(a['fields']))}")
    lines.append(f"- **{b['source']} fields:** {', '.join(sorted(b['fields']))}")
    lines.append(f"- **Shared concepts:** {both} of {len(ALIASES)} "
                 f"({', '.join(c for c in ALIASES if a['cmap'][c] and b['cmap'][c])})")
    lines.append(f"- **Actual differences:** rating shape {a['rating']} vs {b['rating']}; "
                 f"pagination {a['pagination']} vs {b['pagination']}; "
                 f"unmatched fields A={a['unmapped'] or 'none'}, B={b['unmapped'] or 'none'}")
    lines.append("- **Verdict:** <your call. Say what reuse WOULD require -- e.g. "
                 "'same extraction logic, separate rating-normalization and pagination "
                 "adapters' -- rather than 'similar'.>")
    lines.append("=" * 78)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="sample JSON for source A")
    ap.add_argument("--b", required=True, help="sample JSON for source B")
    ap.add_argument("--claim", default="A and B have the same review shape")
    ap.add_argument("--out", help="optional path to also write the report")
    args = ap.parse_args()

    report = render(describe(args.a), describe(args.b), args.claim)
    print(report)
    if args.out:
        with open(args.out, "w") as f:
            f.write(report + "\n")
        print(f"\nAlso written to {args.out}")


if __name__ == "__main__":
    main()

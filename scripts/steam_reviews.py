"""
Steam review sampler (public JSON API, no key).

Endpoint: https://store.steampowered.com/appreviews/<appid>?json=1
Docs: https://partner.steamgames.com/doc/store/getreviews

Pulls a small sample of reviews for one representative game and records the
evidence the scorecard needs: fields returned, row count, pagination behavior,
repeatability, ID scheme, and total corpus size.

Usage:
    python steam_reviews.py --appid 570 --pages 2 --out ../samples/steam_dota2.json
    (570 = Dota 2; swap for any representative game's appid)

Add --repeat to re-pull page 1 a second time and measure whether the same rows
come back (this is the "repeatability" column in the scorecard).
"""
import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://store.steampowered.com/appreviews/{appid}"


def fetch_page(appid: int, cursor: str = "*", num: int = 20,
               filt: str = "recent") -> dict:
    """One page. Raises on network/HTTP failure so we never mistake it for 'end of data'."""
    params = {
        "json": 1,
        "filter": filt,          # 'recent' = newest-first, the fairest repeatability test
        "language": "english",
        "num_per_page": num,     # Steam caps this at 100
        "cursor": cursor,        # '*' for the first page; urlencode handles the escaping
    }
    url = BASE.format(appid=appid) + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "phase1-eval/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect(appid: int, pages: int, num: int = 20) -> tuple[list, dict, list]:
    """Returns (reviews, query_summary_from_page_1, pagination_log)."""
    reviews, cursor, seen_cursors, log = [], "*", set(), []
    summary = {}
    for i in range(pages):
        data = fetch_page(appid, cursor, num)
        if data.get("success") != 1:
            log.append(f"page {i+1}: success != 1 -> {data}")
            break
        if i == 0:
            # query_summary appears on the first page only. total_reviews is the
            # 'total corpus size' number for the volume-units column -- keep it.
            summary = data.get("query_summary", {})
        batch = data.get("reviews", [])
        next_cursor = data.get("cursor", "")
        reviews.extend(batch)
        log.append(f"page {i+1}: {len(batch)} rows · next cursor -> {next_cursor!r}")
        if not batch:
            log.append("  -> empty batch, stopping (end of results)")
            break
        if next_cursor in seen_cursors:
            log.append("  -> cursor repeated, stopping (Steam recycles the cursor at the end)")
            break
        seen_cursors.add(next_cursor)
        cursor = next_cursor
        time.sleep(1)  # be polite
    return reviews, summary, log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--appid", type=int, required=True)
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--num", type=int, default=20, help="rows per page (Steam max 100)")
    ap.add_argument("--repeat", action="store_true",
                    help="re-pull page 1 to test repeatability")
    ap.add_argument("--out", default="../samples/steam_sample.json")
    args = ap.parse_args()

    try:
        reviews, summary, log = collect(args.appid, args.pages, args.num)
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
        # Fail loudly. A network error is NOT evidence about the source.
        raise SystemExit(
            f"NETWORK/HTTP FAILURE, not a data finding: {exc}\n"
            "Do not record this in test_notes.md as a source limitation. "
            "Check your connection and re-run."
        ) from exc

    for line in log:
        print(line)

    # Repeatability test: pull page 1 again and compare IDs.
    repeat_note = "not tested (pass --repeat)"
    if args.repeat and reviews:
        time.sleep(2)
        again, _, _ = collect(args.appid, 1, args.num)
        first_ids = [r.get("recommendationid") for r in reviews[:args.num]]
        again_ids = [r.get("recommendationid") for r in again]
        overlap = len(set(first_ids) & set(again_ids))
        same_order = first_ids == again_ids
        repeat_note = (f"re-pulled page 1 after ~2s: {overlap}/{len(first_ids)} same IDs, "
                       f"identical order = {same_order}")
        print("\nRepeatability:", repeat_note)

    payload = {
        "source": "steam",
        "appid": args.appid,
        "pulled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "query_summary": summary,      # total_reviews / review_score / positive+negative
        "pagination_log": log,
        "repeatability": repeat_note,
        "reviews": reviews,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\nSaved {len(reviews)} reviews -> {args.out}")
    if not reviews:
        return

    fields = sorted(reviews[0].keys())
    nested = {k: sorted(v.keys()) for k, v in reviews[0].items() if isinstance(v, dict)}

    # ---- paste-ready block for test_notes.md -------------------------------
    print("\n" + "=" * 60)
    print("PASTE INTO test_notes.md UNDER '## Steam'")
    print("=" * 60)
    print(f"- **Pull date:** {time.strftime('%Y-%m-%d')}")
    print(f"- **Endpoint used:** {BASE.format(appid=args.appid)}?json=1&filter=recent&num_per_page={args.num}")
    print(f"- **Item sampled:** appid {args.appid}")
    print(f"- **Fields actually returned:** {', '.join(fields)}")
    for k, v in nested.items():
        print(f"  - nested `{k}`: {', '.join(v)}")
    print(f"- **Rows returned in one call:** {min(args.num, len(reviews))} "
          f"(requested {args.num}; total pulled across {args.pages} page(s): {len(reviews)})")
    print("- **Pagination behavior:** opaque `cursor` token, `*` for page 1, "
          "next token returned in the response body; cursor repeats when exhausted")
    print(f"- **Repeatability:** {repeat_note}")
    print("- **ID scheme:** review = `recommendationid`; item = Steam `appid`; "
          "author = `author.steamid`")
    print(f"- **Total corpus size (volume unit B):** query_summary.total_reviews = "
          f"{summary.get('total_reviews', 'n/a')} "
          f"(positive {summary.get('total_positive', 'n/a')} / "
          f"negative {summary.get('total_negative', 'n/a')})")
    print("- **Rating shape:** boolean `voted_up` (thumbs up/down), NOT a 1-5 star scale "
          "-- note this, it matters for cross-source comparability")
    print("- **Quality flags:** `steam_purchase`, `received_for_free`, "
          "`votes_up`, `votes_funny`, `weighted_vote_score`, `author.playtime_forever`")
    print(f"- **Raw sample saved to:** `samples/{args.out.split('/')[-1]}`")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""
Google Play review sampler -- via the `google-play-scraper` package.

READ THIS BEFORE YOU RUN IT, it is scorecard content:
Google publishes NO public API for reading Play Store reviews. The Play Developer
API only exposes reviews for apps you own. `google-play-scraper` works by calling
Google's internal `batchexecute` endpoint -- undocumented, unversioned, and not
covered by any terms that permit collection. So for the scorecard:

  - auth needed:        none (but that is because it is unsanctioned, not because
                        it is open)
  - maintenance risk:   HIGH -- an internal endpoint can change without notice
  - licensing:          NOT cleared. This is the source whose licensing column
                        should read "needs-check / likely not permitted for
                        commercial redistribution", and it is the honest reason
                        it may lose the recurring-ingestion recommendation even
                        if its data is good.

That is a genuine finding and worth stating plainly -- it is exactly the kind of
thing John meant by making licensing a real criterion.

Setup:  pip install google-play-scraper
Usage:
    python google_play_reviews.py --appid com.facebook.katana --count 200 \
        --out ../samples/googleplay_facebook.json
"""
import argparse
import json
import time

try:
    from google_play_scraper import Sort, reviews as gp_reviews
except ImportError:  # pragma: no cover - environment dependent
    gp_reviews = None


def to_jsonable(rows):
    """`at` / `repliedAt` come back as datetime objects."""
    out = []
    for r in rows:
        item = {}
        for k, v in r.items():
            item[k] = v.isoformat() if hasattr(v, "isoformat") else v
        out.append(item)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--appid", default="com.facebook.katana")
    ap.add_argument("--count", type=int, default=200)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--country", default="us")
    ap.add_argument("--repeat", action="store_true",
                    help="re-pull the first batch and measure ID overlap + order stability")
    ap.add_argument("--out", default="../samples/googleplay_sample.json")
    args = ap.parse_args()

    if gp_reviews is None:
        raise SystemExit(
            "google-play-scraper is not installed.\n"
            "  pip install google-play-scraper\n"
            "If you would rather not install an unsanctioned scraper, that is a "
            "defensible call -- record it in the scorecard as 'no permitted access "
            "path found' rather than leaving the row blank."
        )

    batch1, token = gp_reviews(args.appid, lang=args.lang, country=args.country,
                               sort=Sort.NEWEST, count=args.count)
    rows = to_jsonable(batch1)
    pagination_note = (
        f"continuation token returned after {len(rows)} rows "
        f"(token present = {token is not None}); page size is capped per call, "
        f"paging is opaque-cursor based"
    )

    repeat_note = "not tested (pass --repeat)"
    if args.repeat:
        time.sleep(2)
        again, _ = gp_reviews(args.appid, lang=args.lang, country=args.country,
                              sort=Sort.NEWEST, count=min(args.count, 50))
        again = to_jsonable(again)
        first_ids = [r.get("reviewId") for r in rows[:len(again)]]
        again_ids = [r.get("reviewId") for r in again]
        overlap = len(set(first_ids) & set(again_ids))
        repeat_note = (f"re-pulled first {len(again)} after ~2s: {overlap}/{len(first_ids) or 1} "
                       f"same IDs, identical order = {first_ids == again_ids}")
        print("Repeatability:", repeat_note)

    payload = {
        "source": "google_play",
        "appid": args.appid,
        "lang": args.lang,
        "country": args.country,
        "pulled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pagination_note": pagination_note,
        "repeatability": repeat_note,
        "reviews": rows,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    keys = sorted({k for r in rows for k in r})
    scores = sorted({r.get("score") for r in rows if r.get("score") is not None})
    dist = {s: sum(1 for r in rows if r.get("score") == s) for s in scores}
    replies = sum(1 for r in rows if r.get("replyContent"))

    print(f"\nSaved {len(rows)} reviews -> {args.out}\n")
    print("=" * 66)
    print("PASTE INTO test_notes.md UNDER '## Google Play'")
    print("=" * 66)
    print(f"- **Pull date:** {time.strftime('%Y-%m-%d')}")
    print("- **Endpoint / file used:** google-play-scraper -> Google internal "
          "`batchexecute` (UNDOCUMENTED, no public reviews API exists)")
    print(f"- **Item sampled:** {args.appid} ({args.country}/{args.lang})")
    print(f"- **Fields actually returned:** {', '.join(keys)}")
    print(f"- **Rows returned in one call:** {len(rows)} (requested {args.count})")
    print(f"- **Pagination behavior:** {pagination_note}")
    print(f"- **Repeatability:** {repeat_note}")
    print("- **ID scheme:** review = `reviewId` (opaque string); item = package name; "
          "user = display name only, NO stable user id")
    print(f"- **Rating shape:** 1-5 integer `score`. Observed: {dist}")
    print(f"- **Quality flags:** `thumbsUpCount` present; NO verified-purchase flag; "
          f"developer replies on {replies}/{len(rows)} rows")
    print("- **Data-quality limits noticed:** locale-scoped, no user id, display names "
          "are not unique, sort=NEWEST means the window moves between pulls")
    print("- **Maintenance/access risk:** HIGH -- unofficial access to an internal "
          "endpoint; can break without notice")
    print("- **Licensing / permitted use:** NOT cleared -- no sanctioned read API. "
          "Score this column as 'needs-check / likely not permitted', not blank.")
    print(f"- **Raw sample saved to:** `samples/{args.out.split('/')[-1]}`")
    print("=" * 66)


if __name__ == "__main__":
    main()

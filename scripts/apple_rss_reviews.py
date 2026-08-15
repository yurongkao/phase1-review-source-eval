"""
Apple App Store review sampler (public RSS/JSON feed, no key).

Feed: https://itunes.apple.com/<country>/rss/customerreviews/page=<n>/id=<appid>/sortby=mostrecent/json

Two things worth recording as evidence, not assumption:
  1. The feed is a LEGACY, undocumented endpoint -> that is your maintenance/access-risk
     column. Say so and back it up.
  2. Apple caps it at ~10 pages x ~50 reviews -> ~500 reviews per app, US storefront.
     That cap IS the realistic small-sample size. Verify it, don't quote it.

Usage:
    python apple_rss_reviews.py --appid 284882215 --pages 3 --out ../samples/apple_facebook.json
    (284882215 = Facebook; swap for any representative app id)

Add --repeat to re-pull page 1 and measure repeatability.
Add --probe-cap to walk pages until the feed actually stops, to test the ~10-page claim.
"""
import argparse
import json
import time
import urllib.error
import urllib.request

TMPL = ("https://itunes.apple.com/{country}/rss/customerreviews/"
        "page={page}/id={appid}/sortby=mostrecent/json")


class FeedExhausted(Exception):
    """The feed returned no more reviews -- a real finding about the source."""


class NetworkProblem(Exception):
    """Connection/proxy/DNS failure -- NOT a finding about the source."""


def fetch_page(appid: int, page: int, country: str = "us") -> dict:
    url = TMPL.format(country=country, appid=appid, page=page)
    req = urllib.request.Request(url, headers={"User-Agent": "phase1-eval/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as exc:
        # 4xx/5xx from Apple. 403/404 past the cap is a real finding; anything
        # else is worth naming explicitly rather than lumping in with "cap".
        raise FeedExhausted(f"HTTP {exc.code} on page {page}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise NetworkProblem(str(exc)) from exc


def parse_entries(feed: dict) -> tuple[list, list, bool]:
    """Returns (reviews, raw_field_keys_seen, had_app_metadata_entry)."""
    entries = feed.get("feed", {}).get("entry", [])
    if isinstance(entries, dict):        # single-entry pages come back unwrapped
        entries = [entries]
    reviews, raw_keys, had_meta = [], set(), False
    for e in entries:
        raw_keys.update(e.keys())
        if "im:rating" not in e:
            had_meta = True              # page 1 leads with an app-metadata entry
            continue
        reviews.append({
            "id": e.get("id", {}).get("label"),
            "title": e.get("title", {}).get("label"),
            "content": e.get("content", {}).get("label"),
            "rating": e.get("im:rating", {}).get("label"),
            "vote_count": e.get("im:voteCount", {}).get("label"),
            "vote_sum": e.get("im:voteSum", {}).get("label"),
            "author": e.get("author", {}).get("name", {}).get("label"),
            "version": e.get("im:version", {}).get("label"),
            "updated": e.get("updated", {}).get("label"),
        })
    return reviews, sorted(raw_keys), had_meta


def collect(appid: int, pages: int, country: str) -> tuple[list, list, list, bool]:
    reviews, log, raw_keys, had_meta = [], [], [], False
    for page in range(1, pages + 1):
        try:
            feed = fetch_page(appid, page, country)
        except FeedExhausted as exc:
            log.append(f"page {page}: stopped -- {exc} (feed cap reached)")
            break
        batch, keys, meta = parse_entries(feed)
        if page == 1:
            raw_keys, had_meta = keys, meta
        reviews.extend(batch)
        log.append(f"page {page}: {len(batch)} reviews")
        if not batch:
            log.append(f"  -> page {page} empty, feed exhausted here")
            break
        time.sleep(1)
    return reviews, log, raw_keys, had_meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--appid", type=int, required=True)
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--country", default="us")
    ap.add_argument("--repeat", action="store_true")
    ap.add_argument("--probe-cap", action="store_true",
                    help="walk up to 15 pages to test the ~10-page cap claim")
    ap.add_argument("--out", default="../samples/apple_sample.json")
    args = ap.parse_args()

    pages = 15 if args.probe_cap else args.pages
    try:
        reviews, log, raw_keys, had_meta = collect(args.appid, pages, args.country)
    except NetworkProblem as exc:
        raise SystemExit(
            f"NETWORK FAILURE, not a data finding: {exc}\n"
            "Do NOT record this in test_notes.md as 'hit the page cap'. "
            "Check your connection and re-run."
        ) from exc

    for line in log:
        print(line)
    pages_that_worked = sum(1 for line in log if "reviews" in line and "stopped" not in line)

    repeat_note = "not tested (pass --repeat)"
    if args.repeat and reviews:
        time.sleep(2)
        again, _, _, _ = collect(args.appid, 1, args.country)
        first_ids = [r["id"] for r in reviews[:len(again)]]
        again_ids = [r["id"] for r in again]
        overlap = len(set(first_ids) & set(again_ids))
        repeat_note = (f"re-pulled page 1 after ~2s: {overlap}/{len(first_ids) or 1} same IDs, "
                       f"identical order = {first_ids == again_ids}")
        print("\nRepeatability:", repeat_note)

    payload = {
        "source": "apple_app_store_rss",
        "appid": args.appid,
        "country": args.country,
        "pulled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pagination_log": log,
        "pages_returning_reviews": pages_that_worked,
        "raw_entry_keys_page1": raw_keys,
        "repeatability": repeat_note,
        "reviews": reviews,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\nSaved {len(reviews)} reviews -> {args.out}")
    if not reviews:
        return

    ratings = [r["rating"] for r in reviews if r.get("rating")]
    dist = {v: ratings.count(v) for v in sorted(set(ratings))}

    print("\n" + "=" * 60)
    print("PASTE INTO test_notes.md UNDER '## Apple App Store'")
    print("=" * 60)
    print(f"- **Pull date:** {time.strftime('%Y-%m-%d')}")
    print(f"- **Endpoint used:** {TMPL.format(country=args.country, page='<n>', appid=args.appid)}")
    print(f"- **Item sampled:** app id {args.appid} ({args.country} storefront)")
    print(f"- **Fields actually returned (raw entry keys):** {', '.join(raw_keys)}")
    print(f"- **Rows returned per page:** ~{len(reviews) // max(pages_that_worked, 1)} "
          f"(total {len(reviews)} across {pages_that_worked} page(s))")
    print(f"- **Pagination behavior:** `page=<n>` path segment; feed stopped returning "
          f"reviews after page {pages_that_worked}"
          + (" (probed up to 15 -- this TESTS the ~10-page cap claim)" if args.probe_cap
             else f" (only requested {args.pages}; re-run with --probe-cap to test the cap)"))
    print(f"- **Repeatability:** {repeat_note}")
    print("- **ID scheme:** review = `id.label` (numeric review id); item = Apple `trackId`/app id; "
          "author has a `uri` but no stable public user id")
    print(f"- **Rating shape:** 1-5 stars. Observed in sample: {dist}")
    print(f"- **Quality flags:** `im:voteCount` / `im:voteSum` present; "
          f"NO verified-purchase flag; app metadata entry on page 1 = {had_meta}")
    print("- **Data-quality limits noticed:** storefront-scoped (one country per pull), "
          "hard page cap, no verified flag, legacy/undocumented endpoint")
    print("- **Maintenance/access risk:** HIGH-ish -- this RSS feed is a legacy, "
          "undocumented endpoint Apple does not publish support guarantees for. "
          "Record it as observed behavior, not a documented contract.")
    print(f"- **Raw sample saved to:** `samples/{args.out.split('/')[-1]}`")
    print("=" * 60)


if __name__ == "__main__":
    main()

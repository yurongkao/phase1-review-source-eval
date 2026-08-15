"""
Best Buy review sampler (official API, free key required) -- OPTIONAL.

This is the source that tests Claim 2 ("Best Buy is the same shape as Amazon").
Unlike Google Play, Best Buy has a real, documented, terms-covered API -- which is
itself the finding: a smaller corpus with clean access beats a bigger corpus you
are not permitted to collect, for the *recurring ingestion* use case.

Key: free, from https://developer.bestbuy.com (approval is usually quick, but if it
has not arrived by Sunday, skip this and say so -- an untested source recorded as
"not sampled, key pending" is honest; an asserted one is what John objected to).

Usage:
    export BESTBUY_API_KEY=...
    python bestbuy_reviews.py --sku 6486268 --pages 2 \
        --out ../samples/bestbuy_sample.json
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.bestbuy.com/v1/reviews(sku={sku})"


class NetworkProblem(Exception):
    """Connection failure -- NOT a finding about the source."""


def fetch(sku, page, key, page_size):
    qs = urllib.parse.urlencode({
        "apiKey": key, "format": "json", "pageSize": page_size, "page": page,
        "sort": "submissionTime.desc",
    })
    url = f"{BASE.format(sku=sku)}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "phase1-eval/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise SystemExit(f"HTTP {exc.code} -- API key rejected or not yet active.") from exc
        raise SystemExit(f"HTTP {exc.code} from Best Buy on page {page}.") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise NetworkProblem(str(exc)) from exc


def flatten(r):
    out = dict(r)
    reviewer = out.pop("reviewer", None)
    if isinstance(reviewer, dict):
        out["reviewer_name"] = reviewer.get("name")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sku", required=True)
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--out", default="../samples/bestbuy_sample.json")
    args = ap.parse_args()

    key = os.environ.get("BESTBUY_API_KEY")
    if not key:
        raise SystemExit("Set BESTBUY_API_KEY first (free key from developer.bestbuy.com). "
                         "If the key has not arrived, skip this source and record it as "
                         "'not sampled -- key pending', not as assumed.")

    rows, log, meta = [], [], {}
    for page in range(1, args.pages + 1):
        try:
            data = fetch(args.sku, page, key, args.page_size)
        except NetworkProblem as exc:
            raise SystemExit(f"NETWORK FAILURE, not a data finding: {exc}") from exc
        if page == 1:
            meta = {k: v for k, v in data.items() if k != "reviews"}
        batch = [flatten(r) for r in data.get("reviews", [])]
        rows.extend(batch)
        log.append(f"page {page}: {len(batch)} reviews "
                   f"(total reported {data.get('total')}, totalPages {data.get('totalPages')})")
        if not batch or page >= (data.get("totalPages") or 1):
            break
        time.sleep(1)

    payload = {
        "source": "bestbuy_api",
        "sku": args.sku,
        "pulled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pagination_note": (f"explicit page/pageSize params, server reports total + "
                            f"totalPages ({meta.get('totalPages')}) -- fully enumerable"),
        "repeatability": ("deterministic given an explicit sort; server-reported total "
                          "makes drift detectable between pulls"),
        "response_meta_page1": meta,
        "pagination_log": log,
        "reviews": rows,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    for line in log:
        print(line)
    keys = sorted({k for r in rows for k in r})
    ratings = sorted({r.get("rating") for r in rows if r.get("rating") is not None})
    dist = {s: sum(1 for r in rows if r.get("rating") == s) for s in ratings}

    print(f"\nSaved {len(rows)} reviews -> {args.out}\n")
    print("=" * 66)
    print("PASTE INTO test_notes.md UNDER '## Best Buy'")
    print("=" * 66)
    print(f"- **Pull date:** {time.strftime('%Y-%m-%d')}")
    print(f"- **Endpoint used:** {BASE.format(sku=args.sku)} (documented API, key required)")
    print(f"- **Item sampled:** sku {args.sku}")
    print(f"- **Fields actually returned:** {', '.join(keys)}")
    print(f"- **Rows returned in one call:** up to {args.page_size}; got {len(rows)} over "
          f"{len(log)} page(s); server reports total = {meta.get('total')}")
    print(f"- **Pagination behavior:** {payload['pagination_note']}")
    print(f"- **Repeatability:** {payload['repeatability']}")
    print("- **ID scheme:** review = `id`; item = `sku` (Best Buy's own, NOT an ASIN -- "
          "cross-source item joins need a UPC/GTIN bridge)")
    print(f"- **Rating shape:** 1-5. Observed: {dist}")
    print("- **Quality flags:** check for helpfulness/verified fields in the key list above "
          "and record what is actually there")
    print("- **Licensing / permitted use:** documented API terms exist -- this is the "
          "cleanest access story of the retail sources. Score it as such.")
    print(f"- **Raw sample saved to:** `samples/{args.out.split('/')[-1]}`")
    print("=" * 66)


if __name__ == "__main__":
    main()

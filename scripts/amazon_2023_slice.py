"""
Amazon Reviews 2023 (McAuley Lab) -- load ONE category slice, no key, no full download.

The full dataset is enormous; you do not need it and downloading it would waste the
weekend. The category files are line-delimited JSON, so this streams the file over
HTTP and stops after N lines. A 2,000-line slice is plenty to characterise fields,
rating shape and quality flags.

Source: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
Licensing note for the scorecard: this is a RESEARCH dataset with a stated citation
requirement, and the terms are not the same as "public API you may collect from."
That distinction is exactly why John wanted licensing as its own column -- it is the
single biggest difference between this source and the live APIs.

Usage:
    python amazon_2023_slice.py --category All_Beauty --limit 2000 \
        --out ../samples/amazon_all_beauty.json

    # already downloaded a .jsonl / .jsonl.gz yourself:
    python amazon_2023_slice.py --local ~/Downloads/All_Beauty.jsonl --limit 2000 \
        --out ../samples/amazon_all_beauty.json

Small categories that download fast: All_Beauty, Gift_Cards, Magazine_Subscriptions,
Handmade_Products, Digital_Music.
"""
import argparse
import gzip
import io
import json
import time
import urllib.error
import urllib.request
from collections import Counter

BASE = ("https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/"
        "resolve/main/raw/review_categories/{category}.jsonl")


class NetworkProblem(Exception):
    """Connection/proxy failure -- NOT a finding about the source."""


def stream_remote(category, limit):
    url = BASE.format(category=category)
    req = urllib.request.Request(url, headers={"User-Agent": "phase1-eval/0.1"})
    rows = []
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            for raw in io.TextIOWrapper(r, encoding="utf-8"):
                raw = raw.strip()
                if not raw:
                    continue
                rows.append(json.loads(raw))
                if len(rows) >= limit:
                    break            # closing early is the whole point
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"HTTP {exc.code} for {url}\n"
            f"Check the category name spelling against the dataset card. "
            f"This is a real finding only if the category exists."
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise NetworkProblem(str(exc)) from exc
    return rows, url


def stream_local(path, limit):
    opener = gzip.open if str(path).endswith(".gz") else open
    rows = []
    with opener(path, "rt", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            rows.append(json.loads(raw))
            if len(rows) >= limit:
                break
    return rows, str(path)


def summarize(rows):
    fields = Counter()
    for r in rows:
        fields.update(r.keys())
    ratings = [r.get("rating") for r in rows if r.get("rating") is not None]
    dist = dict(sorted(Counter(ratings).items()))
    verified = sum(1 for r in rows if r.get("verified_purchase"))
    helpful = [r.get("helpful_vote", 0) or 0 for r in rows]
    empty_text = sum(1 for r in rows if not (r.get("text") or "").strip())
    with_images = sum(1 for r in rows if r.get("images"))
    asins = {r.get("parent_asin") for r in rows if r.get("parent_asin")}
    users = {r.get("user_id") for r in rows if r.get("user_id")}
    return {
        "fields": fields,
        "rating_dist": dist,
        "verified_pct": round(100 * verified / len(rows), 1) if rows else 0,
        "helpful_max": max(helpful) if helpful else 0,
        "helpful_zero_pct": round(100 * sum(1 for h in helpful if not h) / len(rows), 1) if rows else 0,
        "empty_text": empty_text,
        "with_images": with_images,
        "n_parent_asin": len(asins),
        "n_users": len(users),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="All_Beauty")
    ap.add_argument("--local", help="path to an already-downloaded .jsonl(.gz)")
    ap.add_argument("--limit", type=int, default=2000)
    ap.add_argument("--out", default="../samples/amazon_slice.json")
    args = ap.parse_args()

    try:
        if args.local:
            rows, origin = stream_local(args.local, args.limit)
        else:
            rows, origin = stream_remote(args.category, args.limit)
    except NetworkProblem as exc:
        raise SystemExit(
            f"NETWORK FAILURE, not a data finding: {exc}\n"
            "Do NOT record this in test_notes.md as a property of the dataset. "
            "Re-run, or download the category file and pass --local."
        ) from exc

    s = summarize(rows)

    # Normalized envelope so compare_shapes.py can read this file.
    payload = {
        "source": "amazon_reviews_2023",
        "category": args.category,
        "origin": origin,
        "pulled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pagination_note": ("none -- static line-delimited file; 'pagination' is just "
                            "reading further into the file, fully deterministic"),
        "repeatability": ("perfect by construction -- static versioned file, same bytes "
                          "every read (contrast with the live APIs)"),
        "slice_size": len(rows),
        "reviews": rows,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Read {len(rows)} reviews from {origin}")
    print(f"Saved -> {args.out}\n")

    print("=" * 66)
    print("PASTE INTO test_notes.md UNDER '## Amazon Reviews 2023'")
    print("=" * 66)
    print(f"- **Pull date:** {time.strftime('%Y-%m-%d')}")
    print(f"- **Endpoint / file used:** {origin}")
    print(f"- **Item sampled:** category `{args.category}`, first {len(rows)} lines "
          f"({s['n_parent_asin']} distinct parent_asin, {s['n_users']} distinct users)")
    print(f"- **Fields actually returned:** {', '.join(sorted(s['fields']))}")
    print(f"- **Rows returned in one call:** n/a -- static file, took {len(rows)} by choice")
    print(f"- **Pagination behavior:** {payload['pagination_note']}")
    print(f"- **Repeatability:** {payload['repeatability']}")
    print("- **ID scheme:** review has no standalone id -- identity is "
          "(user_id, parent_asin, timestamp); item = `asin` / `parent_asin`")
    print(f"- **Rating shape:** 1-5 integer. Observed: {s['rating_dist']}")
    print(f"- **Quality flags:** `verified_purchase` present ({s['verified_pct']}% true), "
          f"`helpful_vote` present (max {s['helpful_max']}, {s['helpful_zero_pct']}% zero), "
          f"{s['with_images']} rows carry images")
    print(f"- **Data-quality limits noticed:** {s['empty_text']} empty-text rows in the slice; "
          "no review id; helpful_vote heavily zero-skewed; historical snapshot (not live)")
    print("- **Licensing / permitted use:** research dataset with citation requirement -- "
          "NOT equivalent to an API you may collect from commercially. Confirm terms on the "
          "dataset card before recommending it for a product use case.")
    print(f"- **Raw sample saved to:** `samples/{args.out.split('/')[-1]}`")
    print("=" * 66)


if __name__ == "__main__":
    main()

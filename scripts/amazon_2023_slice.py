"""
Amazon Reviews 2023 (McAuley Lab) -- load ONE category slice, no key, no full download.

The full dataset is enormous; you do not need it and downloading it would waste the
week. The category files are line-delimited JSON, so this streams the file over HTTP
and stops after N lines. A 2,000-line slice is plenty to characterise fields, rating
shape and quality flags.

Source: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
Licensing note for the scorecard: this is a RESEARCH dataset with a stated citation
requirement, and the terms are not the same as "public API you may collect from."
That distinction is exactly why John wanted licensing as its own column -- it is the
single biggest difference between this source and the live APIs.

⚠️ THE TRAP THIS SCRIPT IS BUILT TO AVOID
The first N lines of a static file are a *chosen* window, not a random sample. If the
file is ordered by item or by user (these category files largely are), the head is
clustered and its rating distribution is NOT the category's distribution. Reporting it
as though it were is the same error as Steam's scoped `total_reviews` -- a subset
wearing the label of a total. So this script:
  - measures clustering (rows per distinct item, timestamp span) instead of assuming,
  - fetches a second window from the MIDDLE of the file via an HTTP Range request and
    compares it against the head, so "is the head representative?" is answered with
    evidence,
  - reports total corpus size as an explicit ESTIMATE with the method shown, never as
    a measured count.

Usage:
    python amazon_2023_slice.py --category All_Beauty --limit 2000 \
        --probe-middle --out ../samples/amazon_all_beauty.json

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
CARD = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023"
UA = {"User-Agent": "phase1-eval/0.1"}


class NetworkProblem(Exception):
    """Connection/proxy failure -- NOT a finding about the source."""


# ----------------------------------------------------------------------------
# fetching
# ----------------------------------------------------------------------------
def _open(req, timeout=60):
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError:
        raise
    except (urllib.error.URLError, OSError) as exc:
        raise NetworkProblem(str(exc)) from exc


def file_size(url):
    """Total bytes of the category file, or None if the server won't say.

    HF serves these through an LFS/CDN redirect; the size shows up as either
    content-length on a HEAD or as the x-linked-size header. Returns None rather
    than guessing -- a missing size must read as 'not exposed', not as zero.
    """
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    try:
        with _open(req, timeout=30) as r:
            for key in ("x-linked-size", "content-length"):
                val = r.headers.get(key)
                if val and val.isdigit() and int(val) > 0:
                    return int(val), key
    except urllib.error.HTTPError:
        return None
    return None


def stream_remote(category, limit):
    url = BASE.format(category=category)
    req = urllib.request.Request(url, headers=UA)
    rows, nbytes = [], 0
    try:
        with _open(req) as r:
            for raw in io.TextIOWrapper(r, encoding="utf-8"):
                nbytes += len(raw.encode("utf-8"))
                raw = raw.strip()
                if not raw:
                    continue
                rows.append(json.loads(raw))
                if len(rows) >= limit:
                    break            # closing early is the whole point
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"HTTP {exc.code} for {url}\n"
            f"Check the category name spelling against the dataset card:\n  {CARD}\n"
            f"(File list is under 'Files and versions' -> raw/review_categories/.)\n"
            f"This is a real finding only if the category genuinely exists."
        ) from exc
    return rows, url, nbytes


def stream_local(path, limit):
    opener = gzip.open if str(path).endswith(".gz") else open
    rows, nbytes = [], 0
    with opener(path, "rt", encoding="utf-8") as f:
        for raw in f:
            nbytes += len(raw.encode("utf-8"))
            raw = raw.strip()
            if not raw:
                continue
            rows.append(json.loads(raw))
            if len(rows) >= limit:
                break
    return rows, str(path), nbytes


def probe_middle(url, total_bytes, window=1_000_000):
    """Pull a window from ~the middle of the file with an HTTP Range request.

    The first line landed on is almost certainly partial, so it is discarded; same
    for the last. What comes back is a second, independent sample of the file that
    costs ~1 MB instead of a full download.

    Returns (rows, note). rows == [] with an explanatory note if the server does not
    honour Range -- which is itself worth recording, not silently ignoring.
    """
    if not total_bytes or total_bytes < window * 3:
        return [], "file too small for a meaningful middle probe -- skipped", None
    start = total_bytes // 2
    end = start + window - 1
    req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={start}-{end}"})
    try:
        with _open(req, timeout=60) as r:
            if r.status != 206:
                return [], (f"server ignored the Range request (HTTP {r.status}) -- "
                            "middle probe not possible, representativeness UNTESTED"), None
            blob = r.read(window).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return [], (f"Range request rejected (HTTP {exc.code}) -- "
                    "middle probe not possible, representativeness UNTESTED"), None

    lines = blob.split("\n")[1:-1]          # drop both partial edge lines
    rows, nbytes = [], 0
    for raw in lines:
        nbytes += len(raw.encode("utf-8")) + 1
        raw = raw.strip()
        if not raw:
            continue
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError:
            continue                        # tolerate any residual edge damage
    if not rows:
        return [], "middle probe returned no parseable rows -- representativeness UNTESTED", None
    note = f"read {len(rows)} rows from a {window // 1000} kB window at byte {start:,}"
    return rows, note, nbytes / len(rows)


# ----------------------------------------------------------------------------
# summarising
# ----------------------------------------------------------------------------
def _as_date(ts):
    """Amazon 2023 timestamps are epoch ms; tolerate seconds just in case."""
    try:
        ts = float(ts)
    except (TypeError, ValueError):
        return None
    if ts > 1e11:
        ts /= 1000.0
    try:
        return time.strftime("%Y-%m-%d", time.gmtime(ts))
    except (OverflowError, OSError, ValueError):
        return None


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
    dates = sorted(d for d in (_as_date(r.get("timestamp")) for r in rows) if d)
    n = len(rows) or 1
    return {
        "n": len(rows),
        "fields": fields,
        "rating_dist": dist,
        "mean_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
        "verified_pct": round(100 * verified / n, 1),
        "helpful_max": max(helpful) if helpful else 0,
        "helpful_zero_pct": round(100 * sum(1 for h in helpful if not h) / n, 1),
        "empty_text": empty_text,
        "with_images": with_images,
        "n_parent_asin": len(asins),
        "n_users": len(users),
        "rows_per_item": round(len(rows) / len(asins), 1) if asins else None,
        "date_min": dates[0] if dates else None,
        "date_max": dates[-1] if dates else None,
    }


def pct_dist(dist):
    tot = sum(dist.values()) or 1
    return {k: round(100 * v / tot, 1) for k, v in sorted(dist.items())}


def compare_windows(head, mid):
    """Is the head of the file representative? Answer with numbers, not a guess."""
    h, m = pct_dist(head["rating_dist"]), pct_dist(mid["rating_dist"])
    keys = sorted(set(h) | set(m), key=lambda k: str(k))
    max_gap = max((abs(h.get(k, 0) - m.get(k, 0)) for k in keys), default=0)
    same_items = "unknown"
    if head["n_parent_asin"] and mid["n_parent_asin"]:
        same_items = "no overlap check performed (items differ by construction)"
    if max_gap >= 10:
        verdict = ("NOT representative -- the head and middle windows disagree by "
                   f"{max_gap:.1f} percentage points on at least one rating value. "
                   "Report slice statistics as slice-scoped only; do NOT present them "
                   "as the category's distribution.")
    elif max_gap >= 5:
        verdict = (f"borderline -- max gap {max_gap:.1f} pp between head and middle. "
                   "Usable directionally, but label it as a slice, not the category.")
    else:
        verdict = (f"consistent -- max gap {max_gap:.1f} pp between head and middle. "
                   "The head slice looks representative on rating shape (two windows "
                   "only; this is evidence, not proof).")
    return {"head_pct": h, "mid_pct": m, "max_gap_pp": round(max_gap, 1),
            "verdict": verdict, "items_note": same_items}


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", default="All_Beauty")
    ap.add_argument("--local", help="path to an already-downloaded .jsonl(.gz)")
    ap.add_argument("--limit", type=int, default=2000)
    ap.add_argument("--probe-middle", action="store_true",
                    help="fetch a second window from the middle of the file (Range "
                         "request, ~1 MB) and test whether the head is representative")
    ap.add_argument("--window", type=int, default=1_000_000,
                    help="bytes to read for the middle probe (default 1 MB)")
    ap.add_argument("--out", default="../samples/amazon_slice.json")
    args = ap.parse_args()

    try:
        if args.local:
            rows, origin, nbytes = stream_local(args.local, args.limit)
            size_info = None
        else:
            rows, origin, nbytes = stream_remote(args.category, args.limit)
            size_info = file_size(origin)
    except NetworkProblem as exc:
        raise SystemExit(
            f"NETWORK FAILURE, not a data finding: {exc}\n"
            "Do NOT record this in test_notes.md as a property of the dataset. "
            "Re-run, or download the category file and pass --local."
        ) from exc

    if not rows:
        raise SystemExit("No rows read -- check the category name and try again.")

    s = summarize(rows)
    mean_line = nbytes / len(rows)

    total_bytes = size_info[0] if size_info else None

    # ---- representativeness probe ------------------------------------------
    cmp_result, probe_note, mid, mid_mean_line = None, "not run (pass --probe-middle)", None, None
    if args.probe_middle and args.local:
        probe_note = "skipped -- --probe-middle applies to the remote file only"
    elif args.probe_middle:
        mid_rows, probe_note, mid_mean_line = probe_middle(origin, total_bytes, args.window)
        if mid_rows:
            mid = summarize(mid_rows)
            cmp_result = compare_windows(s, mid)

    # ---- volume unit B: an ESTIMATE, and labelled as one -------------------
    # Row size is the whole basis of this estimate, so when the middle probe gives a
    # second measurement of it, report the SPREAD rather than picking one. The head
    # of a clustered file has systematically different row lengths from the body --
    # quoting a single number off the head would be one more chosen figure wearing
    # the label of a total.
    if size_info:
        _, size_hdr = size_info
        if mid_mean_line:
            lo = int(total_bytes / max(mean_line, mid_mean_line))
            hi = int(total_bytes / min(mean_line, mid_mean_line))
            spread = (hi - lo) / hi if hi else 0
            volume_b = (
                f"~{lo:,}–{hi:,} reviews ESTIMATED (file {total_bytes:,} bytes via "
                f"`{size_hdr}`, divided by mean bytes-per-row measured in two windows: "
                f"{mean_line:.0f} at the head, {mid_mean_line:.0f} mid-file). "
                f"Range, not a point value — the two windows disagree on row size by "
                f"{spread:.0%}. No server-reported review count exists for this dataset, "
                f"so a byte-based estimate is the honest ceiling of what can be measured; "
                f"an exact count requires reading the whole file.")
        else:
            est_rows = int(total_bytes / mean_line)
            volume_b = (
                f"~{est_rows:,} reviews ESTIMATED (file {total_bytes:,} bytes via "
                f"`{size_hdr}` / {mean_line:.0f} mean bytes-per-row in the head slice). "
                f"⚠️ Single-window estimate — row size was measured only at the head of "
                f"the file, so this is as biased as the head slice is. Re-run with "
                f"--probe-middle for a range. Not a server-reported count.")
    else:
        volume_b = ("NOT EXPOSED -- server reported no content length, and the dataset "
                    "publishes no review-count field in the data itself. Any total must "
                    "come from the dataset card (a documentation claim, not a measurement).")

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
        "slice_is_head_of_file": True,
        "total_bytes": total_bytes,
        "estimated_total_rows_note": volume_b,
        "mean_bytes_per_row_head": round(mean_line, 1),
        "mean_bytes_per_row_middle": round(mid_mean_line, 1) if mid_mean_line else None,
        "middle_probe": {"note": probe_note,
                         "n": mid["n"] if mid else 0,
                         "comparison": cmp_result},
        "reviews": rows,
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Read {len(rows)} reviews from {origin}")
    print(f"Saved -> {args.out}\n")

    print("=" * 70)
    print("PASTE INTO test_notes.md UNDER '## Amazon Reviews 2023'")
    print("=" * 70)
    print(f"- **Pull date:** {time.strftime('%Y-%m-%d')}")
    print(f"- **Endpoint / file used:** {origin}")
    print(f"- **Item sampled:** category `{args.category}`, **first {len(rows)} lines "
          f"(head of file, NOT a random sample)** — {s['n_parent_asin']} distinct "
          f"parent_asin, {s['n_users']} distinct users")
    print(f"- **Fields actually returned:** {', '.join(sorted(s['fields']))}")
    print(f"- **Rows returned in one call:** n/a — static file; {len(rows)} taken by choice")
    print(f"- **Pagination behavior:** {payload['pagination_note']}")
    print(f"- **Repeatability:** {payload['repeatability']}")
    print("- **ID scheme:** review has no standalone id — identity is "
          "(user_id, parent_asin, timestamp); item = `asin` / `parent_asin`")
    print(f"- **Total corpus size (volume unit B):** {volume_b}")
    print(f"- **Reviews / representative item (volume unit A):** {s['rows_per_item']} "
          f"rows per distinct parent_asin *within this slice* — a property of the slice's "
          f"clustering, not of the category. The file is not indexed by item, so the true "
          f"per-item count requires filtering the whole category file.")
    print(f"- **Rating shape:** 1–5 integer. Observed in slice: {s['rating_dist']} "
          f"(mean {s['mean_rating']}) — ⚠️ slice-scoped, see representativeness below")
    print(f"- **Time coverage of slice:** {s['date_min']} → {s['date_max']} "
          f"(if this span is narrow, the head is time-clustered and the slice is not "
          f"a cross-section of the category)")
    print(f"- **Quality flags:** `verified_purchase` present ({s['verified_pct']}% true), "
          f"`helpful_vote` present (max {s['helpful_max']}, {s['helpful_zero_pct']}% zero), "
          f"{s['with_images']} rows carry images")
    print(f"- **Data-quality limits noticed:** {s['empty_text']} empty-text rows in the "
          "slice; no review id; helpful_vote heavily zero-skewed; historical snapshot "
          "(not live) so it cannot serve a recurring-collection use case on its own")

    print("- **Representativeness of the slice (measured, not assumed):**")
    if cmp_result:
        print(f"    - middle probe: {probe_note}")
        print(f"    - head rating % : {cmp_result['head_pct']}")
        print(f"    - middle rating %: {cmp_result['mid_pct']}")
        print(f"    - middle slice time coverage: {mid['date_min']} → {mid['date_max']}")
        print(f"    - **{cmp_result['verdict']}**")
    else:
        print(f"    - {probe_note}")
        print("    - **Head-vs-body representativeness UNTESTED.** Record it that way "
              "in the scorecard rather than presenting slice stats as category stats.")

    print("- **Licensing / permitted use:** research dataset with a citation "
          "requirement — NOT equivalent to an API you may collect from commercially. "
          f"Read the terms on the dataset card and record them verbatim: {CARD}")
    print(f"- **Raw sample saved to:** `samples/{args.out.split('/')[-1]}`")
    print("=" * 70)


if __name__ == "__main__":
    main()

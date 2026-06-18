"""
Scrapes r/OnePieceSpoilers using Reddit's public JSON API — no API key needed.
Targets ~600-800 raw items for annotation down to 100 per label.

Usage:
    pip install requests pandas
    python scrape.py
"""

import time
import requests
import pandas as pd
import os
from datetime import datetime, timedelta, timezone

SUBREDDIT  = "OnePieceSpoilers"
BASE_URL   = f"https://www.reddit.com/r/{SUBREDDIT}"
HEADERS    = {"User-Agent": "takemeter-scraper/1.0"}
CUTOFF_TS  = (datetime.now(timezone.utc) - timedelta(days=180)).timestamp()
MIN_WORDS  = 20

rows: dict[str, dict] = {}   # keyed by id to deduplicate


def get(url: str, params: dict = {}) -> dict | None:
    """GET with rate-limit backoff."""
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 60))
                print(f"  rate limited — waiting {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            time.sleep(1.1)   # Reddit public API: ~1 req/sec is safe
            return r.json()
        except Exception as e:
            print(f"  request error ({e}), retrying...")
            time.sleep(5 * (attempt + 1))
    return None


def add_post(data: dict):
    ts = data.get("created_utc", 0)
    if ts < CUTOFF_TS:
        return

    selftext = (data.get("selftext") or "").strip()
    if selftext in ("[deleted]", "[removed]"):
        selftext = ""

    text = data.get("title", "").strip()
    if selftext:
        text = text + "\n\n" + selftext

    if len(text.split()) < MIN_WORDS:
        return

    uid = f"post_{data['id']}"
    if uid not in rows:
        rows[uid] = {
            "id":          uid,
            "source_type": "post",
            "text":        text,
            "url":         "https://reddit.com" + data.get("permalink", ""),
            "created_utc": int(ts),
            "flair":       data.get("link_flair_text") or "",
            "score":       data.get("score", 0),
            "label":       "",
        }


def add_comment(data: dict):
    ts = data.get("created_utc", 0)
    if ts < CUTOFF_TS:
        return

    body = (data.get("body") or "").strip()
    if body in ("[deleted]", "[removed]", ""):
        return
    if len(body.split()) < MIN_WORDS:
        return

    uid = f"comment_{data['id']}"
    if uid not in rows:
        rows[uid] = {
            "id":          uid,
            "source_type": "comment",
            "text":        body,
            "url":         "https://reddit.com" + data.get("permalink", ""),
            "created_utc": int(ts),
            "flair":       "",
            "score":       data.get("score", 0),
            "label":       "",
        }


def scrape_listing(url: str, params: dict, max_pages: int = 5, label: str = ""):
    """Paginate through a Reddit listing endpoint."""
    after = None
    for page in range(max_pages):
        p = {**params, "limit": 100}
        if after:
            p["after"] = after
        data = get(url, p)
        if not data:
            break
        children = data.get("data", {}).get("children", [])
        if not children:
            break
        for child in children:
            add_post(child["data"])
        after = data.get("data", {}).get("after")
        if not after:
            break
    print(f"  [{label}] {len(rows)} unique items total")


def scrape_post_comments(post_id: str, max_comments: int = 40):
    """Pull top-level comments from a single post."""
    url  = f"{BASE_URL}/comments/{post_id}.json"
    data = get(url, {"limit": max_comments, "depth": 1, "sort": "top"})
    if not data or len(data) < 2:
        return
    for child in data[1].get("data", {}).get("children", []):
        if child.get("kind") == "t1":
            add_comment(child["data"])


# ── 1. Top posts past year ────────────────────────────────────────────────────
print("1. Top posts (past year, filtering to 6 months)...")
scrape_listing(f"{BASE_URL}/top.json", {"t": "year"}, max_pages=5, label="top")

# ── 2. Hot posts ──────────────────────────────────────────────────────────────
print("2. Hot posts...")
scrape_listing(f"{BASE_URL}/hot.json", {}, max_pages=2, label="hot")

# ── 3. Theory-flaired posts ───────────────────────────────────────────────────
print("3. Theory-flaired posts...")
scrape_listing(
    f"{BASE_URL}/search.json",
    {"q": 'flair:"Theory"', "sort": "top", "t": "year", "restrict_sr": 1},
    max_pages=3,
    label="flair:Theory",
)

# ── 4. Discussion-flaired posts ───────────────────────────────────────────────
print("4. Discussion-flaired posts...")
scrape_listing(
    f"{BASE_URL}/search.json",
    {"q": 'flair:"Discussion"', "sort": "top", "t": "year", "restrict_sr": 1},
    max_pages=3,
    label="flair:Discussion",
)

# ── 5. Comments from spoiler megathreads ──────────────────────────────────────
print("5. Comments from spoiler megathreads...")
mega_result = get(
    f"{BASE_URL}/search.json",
    {"q": "Chapter Spoilers", "sort": "new", "t": "year", "restrict_sr": 1, "limit": 50},
)
megathread_ids = []
if mega_result:
    for child in mega_result.get("data", {}).get("children", []):
        post = child["data"]
        if post.get("created_utc", 0) >= CUTOFF_TS:
            megathread_ids.append(post["id"])

for pid in megathread_ids[:25]:
    scrape_post_comments(pid, max_comments=40)

print(f"  [megathreads] {len(rows)} unique items total after {len(megathread_ids[:25])} threads")

# ── 6. Comments from top theory posts ─────────────────────────────────────────
print("6. Comments from top theory posts...")
theory_result = get(
    f"{BASE_URL}/search.json",
    {"q": 'flair:"Theory"', "sort": "top", "t": "year", "restrict_sr": 1, "limit": 25},
)
theory_ids = []
if theory_result:
    for child in theory_result.get("data", {}).get("children", []):
        post = child["data"]
        if post.get("created_utc", 0) >= CUTOFF_TS:
            theory_ids.append(post["id"])

for pid in theory_ids[:15]:
    scrape_post_comments(pid, max_comments=20)

print(f"  [theory comments] {len(rows)} unique items total after {len(theory_ids[:15])} posts")

# ── Save ──────────────────────────────────────────────────────────────────────
df = pd.DataFrame(list(rows.values()))
df = df.sort_values("score", ascending=False).reset_index(drop=True)

os.makedirs("data", exist_ok=True)
out = "data/raw_scraped.csv"
df.to_csv(out, index=False)

print(f"\nDone. {len(df)} unique examples → {out}")
print(f"\nBy source type:\n{df['source_type'].value_counts().to_string()}")
print(f"\nBy flair (posts only):\n{df[df['source_type']=='post']['flair'].value_counts().head(10).to_string()}")
cutoff_str = datetime.fromtimestamp(CUTOFF_TS).strftime("%Y-%m-%d")
print(f"\nDate range (cutoff was {cutoff_str}):")
print(f"  oldest: {datetime.fromtimestamp(df['created_utc'].min()).strftime('%Y-%m-%d')}")
print(f"  newest: {datetime.fromtimestamp(df['created_utc'].max()).strftime('%Y-%m-%d')}")
print(f"\nNext step: open {out} and fill in the 'label' column.")
print("Labels: grounded_theory | speculation | reaction | observation")

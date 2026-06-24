"""
Scrapes r/OnePieceSpoilers via Arctic Shift (a Reddit archive API).
No API key or Reddit account needed.

Strategy: Arctic Shift only sorts by date, so we paginate through the whole
1-year window (newest-first) collecting everything, then sort by score locally.

Usage:
    pip install requests pandas
    python scrape.py
"""

import time
import requests
import pandas as pd
import os
from datetime import datetime, timedelta, timezone

SUBREDDIT  = "OnePiecePowerScaling"
BASE       = "https://arctic-shift.photon-reddit.com/api"
HEADERS    = {"User-Agent": "takemeter-scraper/1.0"}
CUTOFF_TS  = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())  # 1 year
NOW_TS     = int(datetime.now(timezone.utc).timestamp())
MIN_WORDS  = 15

rows: dict[str, dict] = {}


def get(endpoint: str, params: dict) -> list | None:
    url = f"{BASE}/{endpoint}"
    for attempt in range(4):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=30)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 30))
                print(f"  rate limited — waiting {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            time.sleep(0.8)
            return r.json().get("data", [])
        except requests.HTTPError as e:
            # 400 = bad params; don't bother retrying those
            if r.status_code == 400:
                print(f"  bad request (400): {r.text[:200]}")
                return None
            print(f"  error: {e}, retrying ({attempt+1}/4)...")
            time.sleep(5 * (attempt + 1))
        except Exception as e:
            print(f"  error: {e}, retrying ({attempt+1}/4)...")
            time.sleep(5 * (attempt + 1))
    return None


def add_post(d: dict):
    selftext = (d.get("selftext") or "").strip()
    if selftext in ("[deleted]", "[removed]"):
        selftext = ""
    text = (d.get("title") or "").strip()
    if selftext:
        text = text + "\n\n" + selftext
    if len(text.split()) < MIN_WORDS:
        return
    uid = f"post_{d['id']}"
    if uid not in rows:
        rows[uid] = {
            "id":          uid,
            "source_type": "post",
            "text":        text,
            "url":         "https://reddit.com" + (d.get("permalink") or ""),
            "created_utc": int(d.get("created_utc", 0)),
            "flair":       d.get("link_flair_text") or "",
            "score":       d.get("score", 0),
            "label":       "",
        }


def add_comment(d: dict):
    body = (d.get("body") or "").strip()
    if body in ("[deleted]", "[removed]", ""):
        return
    if len(body.split()) < MIN_WORDS:
        return
    uid = f"comment_{d['id']}"
    if uid not in rows:
        rows[uid] = {
            "id":          uid,
            "source_type": "comment",
            "text":        body,
            "url":         "https://reddit.com" + (d.get("permalink") or ""),
            "created_utc": int(d.get("created_utc", 0)),
            "flair":       "",
            "score":       d.get("score", 0),
            "label":       "",
        }


def paginate(endpoint: str, adder, label: str, extra: dict = {}, max_pages: int = 40):
    """
    Walk the 1-year window newest-first. Arctic Shift sorts by created_utc,
    so we move the `before` cursor back each page until we hit the cutoff.
    """
    before = NOW_TS
    start_count = len(rows)
    for page in range(max_pages):
        params = {
            "subreddit": SUBREDDIT,
            "after":     CUTOFF_TS,
            "before":    before,
            "limit":     100,
            "sort":      "desc",
            **extra,
        }
        items = get(endpoint, params)
        if items is None:        # hard error
            break
        if not items:            # no more data
            break
        for item in items:
            adder(item)
        oldest = min(int(i.get("created_utc", NOW_TS)) for i in items)
        if oldest <= CUTOFF_TS or oldest >= before:
            break
        before = oldest          # next page ends where this one started
    print(f"  [{label}] +{len(rows) - start_count} new  ({len(rows)} total)")


# ── 1. ALL posts in the 1-year window ─────────────────────────────────────────
print("1. All posts (past year)...")
paginate("posts/search", add_post, "all posts", max_pages=80)

# ── 2. ALL comments in the window — main source of 'takes' ────────────────────
# This is the big one: comments are where grounded_theory/speculation/reaction live.
print("2. Comments (past year)... this is the largest step")
paginate("comments/search", add_comment, "all comments", max_pages=240)

# ── Save ──────────────────────────────────────────────────────────────────────
df = pd.DataFrame(list(rows.values()))
df = df.sort_values("score", ascending=False).reset_index(drop=True)

os.makedirs("data", exist_ok=True)
out = "data/raw_scraped.csv"
df.to_csv(out, index=False)

print(f"\nDone. {len(df)} unique examples -> {out}")
print(f"\nBy source type:\n{df['source_type'].value_counts().to_string()}")
posts = df[df['source_type'] == 'post']
if len(posts):
    print(f"\nTop flairs (posts only):\n{posts['flair'].value_counts().head(10).to_string()}")
print(f"\nDate range:")
print(f"  oldest: {datetime.fromtimestamp(df['created_utc'].min()).strftime('%Y-%m-%d')}")
print(f"  newest: {datetime.fromtimestamp(df['created_utc'].max()).strftime('%Y-%m-%d')}")
print(f"\nNext step: open {out} and fill in the 'label' column.")
print("Labels: grounded_theory | speculation | reaction | observation")

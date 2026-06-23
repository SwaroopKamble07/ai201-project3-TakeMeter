"""
Scrapes r/OnePiecePowerScaling for the Shanks vs. Mihawk debate dataset.
Uses Arctic Shift API — no credentials needed.

Targets:
  shanks_stronger / mihawk_stronger / equal — from posts/comments about Shanks vs Mihawk
  unrelated                                 — from posts about other characters

Output: data/raw_powerscaling.csv (unlabeled, for prelabel.py to label)

Usage:
    python scrape_powerscaling.py
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
    for attempt in range(5):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=40)
            if r.status_code == 400:
                print(f"  bad request: {r.text[:150]}")
                return None
            if r.status_code == 422:
                wait = 15 * (attempt + 1)
                print(f"  server busy (422), waiting {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            time.sleep(1.0)
            return r.json().get("data", [])
        except Exception as e:
            print(f"  error: {e}, retrying ({attempt+1}/5)...")
            time.sleep(5 * (attempt + 1))
    return None


def add_post(d: dict, hint: str = ""):
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
            "id":               uid,
            "source_type":      "post",
            "text":             text,
            "url":              "https://reddit.com" + (d.get("permalink") or ""),
            "created_utc":      int(d.get("created_utc", 0)),
            "flair":            d.get("link_flair_text") or "",
            "score":            d.get("score", 0),
            "suggested_label":  hint,
            "label":            "",
            "annotation_source": "",
            "reviewed":         0,
            "notes":            "",
        }


def add_comment(d: dict, hint: str = ""):
    body = (d.get("body") or "").strip()
    if body in ("[deleted]", "[removed]", ""):
        return
    if len(body.split()) < MIN_WORDS:
        return
    uid = f"comment_{d['id']}"
    if uid not in rows:
        rows[uid] = {
            "id":               uid,
            "source_type":      "comment",
            "text":             body,
            "url":              "https://reddit.com" + (d.get("permalink") or ""),
            "created_utc":      int(d.get("created_utc", 0)),
            "flair":            "",
            "score":            d.get("score", 0),
            "suggested_label":  hint,
            "label":            "",
            "annotation_source": "",
            "reviewed":         0,
            "notes":            "",
        }


def paginate_posts(label: str, hint: str, extra: dict = {}, max_pages: int = 10):
    before = NOW_TS
    start  = len(rows)
    for _ in range(max_pages):
        items = get("posts/search", {
            "subreddit": SUBREDDIT,
            "after":     CUTOFF_TS,
            "before":    before,
            "limit":     100,
            "sort":      "desc",
            **extra,
        })
        if not items:
            break
        for item in items:
            add_post(item, hint)
        oldest = min(int(i.get("created_utc", NOW_TS)) for i in items)
        if oldest <= CUTOFF_TS or oldest >= before:
            break
        before = oldest
    print(f"  [{label}] +{len(rows) - start} new  ({len(rows)} total)")


def paginate_comments(label: str, hint: str, extra: dict = {}, max_pages: int = 5):
    before = NOW_TS
    start  = len(rows)
    for _ in range(max_pages):
        items = get("comments/search", {
            "subreddit": SUBREDDIT,
            "after":     CUTOFF_TS,
            "before":    before,
            "limit":     100,
            "sort":      "desc",
            **extra,
        })
        if not items:
            break
        for item in items:
            add_comment(item, hint)
        oldest = min(int(i.get("created_utc", NOW_TS)) for i in items)
        if oldest <= CUTOFF_TS or oldest >= before:
            break
        before = oldest
    print(f"  [{label}] +{len(rows) - start} new  ({len(rows)} total)")


# ── 1. Posts with Shanks AND Mihawk in title ─────────────────────────────────
print("1. Posts with 'Shanks' in title (debate posts)...")
paginate_posts("shanks title", "debate", {"title": "Shanks"}, max_pages=10)

print("2. Posts with 'Mihawk' in title (debate posts)...")
paginate_posts("mihawk title", "debate", {"title": "Mihawk"}, max_pages=10)

# ── 2. All posts — broad sweep for more context ───────────────────────────────
print("3. Top posts general sweep...")
paginate_posts("all posts", "", {}, max_pages=15)

# ── 3. Comments from Shanks/Mihawk debate posts ───────────────────────────────
print("4. Getting post IDs for comment scraping...")
debate_posts = [
    v for v in rows.values()
    if v["source_type"] == "post"
    and ("shanks" in v["text"].lower() or "mihawk" in v["text"].lower())
]
debate_posts.sort(key=lambda x: x["score"], reverse=True)
print(f"  Found {len(debate_posts)} debate posts — pulling comments from top 30")

for post in debate_posts[:30]:
    post_id = post["id"].replace("post_", "")
    items   = get("comments/search", {
        "subreddit": SUBREDDIT,
        "link_id":   post_id,
        "limit":     50,
        "sort":      "desc",
    })
    if items:
        for item in items:
            add_comment(item, "debate")
    time.sleep(0.5)

print(f"  After comment scrape: {len(rows)} total")

# ── 4. Unrelated posts — no mention of Shanks or Mihawk ──────────────────────
print("5. Filtering unrelated posts...")
for uid, row in list(rows.items()):
    text_lower = row["text"].lower()
    if "shanks" not in text_lower and "mihawk" not in text_lower:
        rows[uid]["suggested_label"] = "unrelated"
    elif row["suggested_label"] == "":
        rows[uid]["suggested_label"] = "debate"

# ── Save ──────────────────────────────────────────────────────────────────────
df = pd.DataFrame(list(rows.values()))
df = df.sort_values("score", ascending=False).reset_index(drop=True)

os.makedirs("data", exist_ok=True)
out = "data/raw_powerscaling.csv"
df.to_csv(out, index=False)

debate = df[df["suggested_label"] == "debate"]
unrel  = df[df["suggested_label"] == "unrelated"]

print(f"\nDone. {len(df)} total rows -> {out}")
print(f"  Debate candidates (Shanks/Mihawk): {len(debate)}")
print(f"  Unrelated candidates:              {len(unrel)}")
print(f"\nNext step: python prelabel_powerscaling.py")

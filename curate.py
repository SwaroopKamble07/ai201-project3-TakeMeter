"""
Turns data/raw_scraped.csv into a balanced, annotation-ready candidate file.

Strategy:
  - Posts: use the subreddit's own flair as a SUGGESTED label (you verify).
  - observation & reaction: thin/absent in flairs, so supplement from comments
    using keyword heuristics.
  - Sort each bucket by score (best community examples first).
  - Aim for ~150 candidates per label so you can keep the best 100 after reading.

Output: data/to_annotate.csv with columns:
    id, source_type, suggested_label, label, score, flair, text, url
The 'suggested_label' is a STARTING GUESS from flair/keywords — the whole point
of the project is to verify it by reading. Fill in the real 'label' yourself.

Usage:
    python curate.py
"""

import re
import pandas as pd

CANDIDATES_PER_LABEL = 150

df = pd.read_csv("data/raw_scraped.csv")
df["text"] = df["text"].fillna("").astype(str)
df["flair"] = df["flair"].fillna("").astype(str)

posts    = df[df["source_type"] == "post"].copy()
comments = df[df["source_type"] == "comment"].copy()


def flair_has(series, *keywords):
    pat = "|".join(keywords)
    return series.str.contains(pat, case=False, regex=True)


# ── grounded_theory candidates: Theory / Analysis flaired posts ──────────────
gt = posts[flair_has(posts["flair"], "theory", "analysis")].copy()
gt["suggested_label"] = "grounded_theory"

# ── speculation candidates: Speculation / Prediction flaired posts ───────────
spec = posts[flair_has(posts["flair"], "spec", "prediction")].copy()
spec["suggested_label"] = "speculation"

# ── observation candidates: Observation-flaired posts + comments by keyword ──
obs_posts = posts[flair_has(posts["flair"], "observation", "nooticing")].copy()
obs_posts["suggested_label"] = "observation"

OBS_KEYWORDS = re.compile(
    r"\b(?:did (?:anyone|you) (?:notice|catch)|i (?:just )?(?:noticed|realized)|"
    r"anyone else notice|notice (?:that|how)|look at the|in the panel|"
    r"if you look|same (?:panel|pose|position|frame)|callback to|"
    r"parallel(?:s)? (?:to|with|between)|foreshadow|easter egg|"
    r"small detail|tiny detail|interesting (?:that|detail)|the way oda|"
    r"you can see|in the background|symbolism|mirror(?:s|ing)?)\b",
    re.IGNORECASE,
)
obs_comments = comments[comments["text"].str.contains(OBS_KEYWORDS)].copy()
obs_comments["suggested_label"] = "observation"
obs = pd.concat([obs_posts, obs_comments])

# ── reaction candidates: comments with emotional markers, no hard evidence ───
REACTION_KEYWORDS = re.compile(
    r"(?:i(?:'m| am)? (?:not ok|crying|sobbing|shaking|deceased|dead)|"
    r"broke me|goosebumps|chills|peak fiction|peak manga|peak oda|"
    r"this chapter (?:was )?(?:insane|crazy|amazing|wild|nuts|fire)|"
    r"oda (?:really )?(?:just|did|cooked)|i can'?t|so (?:good|hyped|excited|happy|sad)|"
    r"goat(?:ed)?|cinema|masterpiece|holy (?:shit|crap)|"
    r"!!!|best chapter|hyped|emotional|made me (?:cry|tear)|love (?:this|that|it|him|her))",
    re.IGNORECASE,
)
# Only exclude on a HARD evidence citation (specific chapter number or panel ref),
# not bare words like "because" that appear constantly in genuine reactions.
EVIDENCE_MARKER = re.compile(r"\b(?:chapter \d+|ch\.? ?\d+|in the panel|the panel where)\b", re.IGNORECASE)
react = comments[
    comments["text"].str.contains(REACTION_KEYWORDS)
    & ~comments["text"].str.contains(EVIDENCE_MARKER)
].copy()
react["suggested_label"] = "reaction"


def top_n(frame, n=CANDIDATES_PER_LABEL):
    return frame.sort_values("score", ascending=False).head(n)


buckets = {
    "grounded_theory": top_n(gt),
    "speculation":     top_n(spec),
    "observation":     top_n(obs),
    "reaction":        top_n(react),
}

print("Candidate pool sizes (before capping at %d):" % CANDIDATES_PER_LABEL)
for name, full in [("grounded_theory", gt), ("speculation", spec),
                   ("observation", obs), ("reaction", react)]:
    print(f"  {name:16s}: {len(full):4d} available -> taking {len(buckets[name])}")

out = pd.concat(buckets.values()).drop_duplicates(subset="id")
out["label"] = ""   # YOU fill this in
out = out[["id", "source_type", "suggested_label", "label",
           "score", "flair", "text", "url"]]

# shuffle so you don't annotate one label at a time (reduces bias),
# deterministic order via sort by id
out = out.sort_values("id").reset_index(drop=True)

out.to_csv("data/to_annotate.csv", index=False)
print(f"\nWrote {len(out)} candidates to data/to_annotate.csv")
print("\nSuggested-label distribution:")
print(out["suggested_label"].value_counts().to_string())
print("\n>> Open data/to_annotate.csv, read each row, and fill the 'label' column.")
print(">> 'suggested_label' is only a hint from flair/keywords — verify by reading.")
print(">> Keep the best ~100 per label; delete or leave blank the rest.")

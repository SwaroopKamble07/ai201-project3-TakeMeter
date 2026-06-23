"""
Builds a balanced candidate pool from data/raw_powerscaling.csv for annotation.

Strategy:
  - "Debate" candidates: posts/comments mentioning BOTH Shanks and Mihawk
    (these become shanks_stronger / mihawk_stronger / equal after labeling).
  - "Unrelated" candidates: posts mentioning NEITHER character.
  - Sort each pool by score (best community content first).

Output: data/to_annotate_powerscaling.csv

Usage:
    python curate_powerscaling.py
"""

import pandas as pd

DEBATE_N    = 350   # candidates that mention both characters
UNRELATED_N = 150   # candidates that mention neither

df = pd.read_csv("data/raw_powerscaling.csv")
df["text"] = df["text"].fillna("").astype(str)
t = df["text"].str.lower()

has_shanks = t.str.contains("shanks", na=False)
has_mihawk = t.str.contains("mihawk", na=False)

# Debate pool: mentions both → likely a Shanks vs Mihawk take
debate = df[has_shanks & has_mihawk].copy()
debate["suggested_label"] = "debate"
debate = debate.sort_values("score", ascending=False).head(DEBATE_N)

# Unrelated pool: mentions neither
unrelated = df[~has_shanks & ~has_mihawk].copy()
unrelated["suggested_label"] = "unrelated"
unrelated = unrelated.sort_values("score", ascending=False).head(UNRELATED_N)

out = pd.concat([debate, unrelated]).drop_duplicates(subset="id")
out = out.sort_values("id").reset_index(drop=True)

# Ensure annotation columns exist
for col, default in [("label", ""), ("annotation_source", ""), ("reviewed", 0), ("notes", "")]:
    if col not in out.columns:
        out[col] = default

out.to_csv("data/to_annotate_powerscaling.csv", index=False)

print(f"Debate candidates (mention both):   {len(debate)}")
print(f"Unrelated candidates (mention neither): {len(unrelated)}")
print(f"Total candidates: {len(out)} -> data/to_annotate_powerscaling.csv")
print(f"\nNext step: python prelabel_powerscaling.py")

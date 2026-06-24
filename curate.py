"""
Turns data/raw_scraped.csv into a balanced, annotation-ready candidate file
for the Shanks vs. Mihawk power-scaling debate.

Strategy:
  - "Debate" candidates: posts/comments mentioning BOTH Shanks and Mihawk
    (these become shanks_stronger / mihawk_stronger / equal after labeling).
  - "Unrelated" candidates: posts mentioning NEITHER character.
  - Sort each pool by score (best community content first).
  - 1400 debate + 600 unrelated = 2000 candidates gives plenty of headroom,
    especially for minority classes like 'equal'.

Output: data/to_annotate.csv

Usage:
    python curate.py
"""

import pandas as pd

DEBATE_N    = 1400
UNRELATED_N = 600

df = pd.read_csv("data/raw_scraped.csv")
df["text"] = df["text"].fillna("").astype(str)
t = df["text"].str.lower()

has_shanks = t.str.contains("shanks", na=False)
has_mihawk = t.str.contains("mihawk", na=False)

# Debate pool: mentions both characters
debate = df[has_shanks & has_mihawk].copy()
debate["suggested_label"] = "debate"
debate = debate.sort_values("score", ascending=False).head(DEBATE_N)

# Unrelated pool: mentions neither
unrelated = df[~has_shanks & ~has_mihawk].copy()
unrelated["suggested_label"] = "unrelated"
unrelated = unrelated.sort_values("score", ascending=False).head(UNRELATED_N)

out = pd.concat([debate, unrelated]).drop_duplicates(subset="id")
out["label"]            = ""
out["annotation_source"] = ""
out["reviewed"]         = 0
out["notes"]            = ""
out = out.sort_values("id").reset_index(drop=True)

out.to_csv("data/to_annotate.csv", index=False)

print(f"Debate candidates (mention both Shanks & Mihawk): {len(debate)}")
print(f"Unrelated candidates (mention neither):           {len(unrelated)}")
print(f"Total written to data/to_annotate.csv:           {len(out)}")
print()
print("Mentions in raw data:")
print(f"  Mention Shanks:  {has_shanks.sum()}")
print(f"  Mention Mihawk:  {has_mihawk.sum()}")
print(f"  Mention BOTH:    {(has_shanks & has_mihawk).sum()}")
print(f"  Mention NEITHER: {(~has_shanks & ~has_mihawk).sum()}")
print()
print("Next step: python prelabel.py")

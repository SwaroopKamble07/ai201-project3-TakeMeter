"""
Turns data/raw_scraped.csv into an annotation-ready candidate file.

Label taxonomy (argument-type classification on r/OnePiecePowerScaling):
  - feat_based       : argument supported by specific in-story feats
  - narrative_based  : argument from narrative role / symbolism / hierarchy
  - assertion        : bold strength claim with no supporting reasoning

Strategy:
  - Curate candidate posts from r/OnePiecePowerScaling — we want posts that
    actually make a strength argument that can plausibly be classified as one
    of the three labels above. Filter to non-trivial posts that engage with
    a named power-scaling dispute (e.g., a comparison or ranking claim).
  - Sort by score (best community content first).
  - 1500 candidates gives plenty of headroom, especially for the assertion class.

Output: data/to_annotate.csv

Usage:
    python curate.py
"""

import pandas as pd

CANDIDATES_N = 1500

df = pd.read_csv("data/raw_scraped.csv")
df["text"] = df["text"].fillna("").astype(str)

t = df["text"].str.lower()

# Loose filter: posts that engage with a strength argument. We look for posts
# that mention at least one named One Piece character often used in
# power-scaling debates AND are long enough to actually contain an argument.
# This drops short memes, image-only posts, and unrelated one-liners before
# prelabeling runs.
scaling_characters = [
    "shanks", "mihawk", "luffy", "zoro", "kaido", "big mom", "whitebeard",
    "roger", "garp", "dragon", "buggy", "crocodile", "doflamingo",
    "sanji", "benn", "shiki", "akainu", "aokiji", "kizaru", "ryokugyu",
    "fujitora", "blackbeard", "loki", "rocks",
]
has_character = t.str.contains("|".join(scaling_characters), na=False)
is_substantive = df["text"].str.len() >= 80

candidates = df[has_character & is_substantive].copy()
candidates["suggested_label"] = ""
candidates = candidates.sort_values("score", ascending=False).head(CANDIDATES_N)

out = candidates.drop_duplicates(subset="id").copy()
out["label"]             = ""
out["annotation_source"] = ""
out["reviewed"]          = 0
out["notes"]             = ""
out = out.sort_values("id").reset_index(drop=True)

out.to_csv("data/to_annotate.csv", index=False)

print(f"Candidate posts (mentions scaling character + substantive): {len(out)}")
print(f"Total written to data/to_annotate.csv: {len(out)}")
print()
print("Next step: python prelabel.py")

"""
Produces data/labeled_powerscaling.csv from data/prelabeled_powerscaling.csv.
Caps each label to keep distribution balanced (rarest label >= 20% of total).

Usage:
    python finalize_powerscaling.py
"""

import sys
import pandas as pd

LABELS   = {"shanks_stronger", "mihawk_stronger", "equal", "unrelated"}
TARGET   = 100
MIN      = 40
MIN_PCT  = 0.20
IN_PATH  = "data/prelabeled_powerscaling.csv"
OUT_PATH = "data/labeled_powerscaling.csv"

df    = pd.read_csv(IN_PATH)
valid = df[df["label"].isin(LABELS)].copy()

print(f"Valid labeled rows: {len(valid)}")
print(valid["label"].value_counts().to_string())

for lbl in LABELS:
    count = (valid["label"] == lbl).sum()
    if count < MIN:
        print(f"\nERROR: '{lbl}' only has {count} examples (need at least {MIN}).")
        sys.exit(1)

counts     = {lbl: (valid["label"] == lbl).sum() for lbl in LABELS}
rarest     = min(counts.values())
n          = len(LABELS)
total_cap  = max(int(rarest / MIN_PCT), 200)
others_cap = min((total_cap - rarest) // (n - 1), TARGET)

print(f"\nRarest label: {rarest} -> capping others at {others_cap} (total ~{rarest + others_cap*(n-1)})")

chunks = []
for lbl in LABELS:
    cap    = rarest if counts[lbl] == rarest else others_cap
    subset = valid[valid["label"] == lbl].sort_values("score", ascending=False).head(cap)
    chunks.append(subset)

out = pd.concat(chunks).sample(frac=1, random_state=42).reset_index(drop=True)
cols = ["text", "label", "annotation_source", "notes", "url"]
cols = [c for c in cols if c in out.columns]
out  = out[cols]

pct = out["label"].value_counts(normalize=True) * 100
print(f"\nFinal dataset: {len(out)} rows")
print(pct.round(1).to_string())

out.to_csv(OUT_PATH, index=False)
print(f"\nSaved to {OUT_PATH} — upload this file to Colab.")

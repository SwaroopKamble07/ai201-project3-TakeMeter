"""
Takes data/prelabeled.csv (after you've reviewed and verified labels) and
produces data/labeled.csv — the clean file to upload to Colab.

Requirements:
- You must have reviewed at least 400 rows (100 per label)
- 'label' column must contain only valid labels
- No single label can exceed 70% of the dataset

Usage:
    python finalize.py
"""

import sys
import pandas as pd

LABELS   = {"grounded_theory", "speculation", "reaction", "observation"}
MIN      = 40    # absolute floor — below this the model can't learn the class
MIN_PCT  = 0.20  # every label must be at least 20% of the final dataset
IN_PATH  = "data/prelabeled.csv"
OUT_PATH = "data/labeled.csv"

df = pd.read_csv(IN_PATH)

valid = df[df["label"].isin(LABELS)].copy()
invalid = df[~df["label"].isin(LABELS)]

if len(invalid):
    print(f"WARNING: {len(invalid)} rows have invalid/blank labels — dropping them.")
    print(invalid[["id","label"]].head(10).to_string())

print(f"\nAll valid labeled rows: {len(valid)}")
print(valid["label"].value_counts().to_string())

# Check floor
for lbl in LABELS:
    count = (valid["label"] == lbl).sum()
    if count < MIN:
        print(f"\nERROR: '{lbl}' only has {count} examples (need at least {MIN}).")
        sys.exit(1)

# Dynamically compute per-label cap so the rarest label is >= MIN_PCT of total.
# Formula: if rarest = R, total = R / MIN_PCT, cap others = (total - R) / (n-1)
counts     = {lbl: (valid["label"] == lbl).sum() for lbl in LABELS}
rarest     = min(counts.values())
n          = len(LABELS)
total_cap  = int(rarest / MIN_PCT)          # e.g. 48/0.20 = 240
others_cap = (total_cap - rarest) // (n-1)  # e.g. (240-48)/3 = 64

print(f"\nRarest label has {rarest} examples → capping others at {others_cap} (total ~{total_cap})")

# Take top cap per label by score
chunks = []
for lbl in LABELS:
    cap    = rarest if counts[lbl] == rarest else others_cap
    subset = valid[valid["label"] == lbl].sort_values("score", ascending=False).head(cap)
    chunks.append(subset)

out = pd.concat(chunks).sample(frac=1, random_state=42).reset_index(drop=True)

# Colab notebook needs: text, label, and optionally: notes, annotation_source
cols = ["text", "label", "annotation_source", "notes", "url"]
cols = [c for c in cols if c in out.columns]
out = out[cols]

# Check balance
pct = out["label"].value_counts(normalize=True) * 100
print(f"\nFinal dataset: {len(out)} rows")
print(pct.round(1).to_string())

max_pct = pct.max()
if max_pct > 70:
    print(f"\nWARNING: one label is {max_pct:.0f}% of dataset (should be <70%).")

out.to_csv(OUT_PATH, index=False)
print(f"\nSaved to {OUT_PATH} — upload this file to Colab.")

"""
Pre-labels data/to_annotate.csv using GPT OSS 120B via NVIDIA NIM.
Saves progress every 5 rows so it can resume if interrupted.

Usage:
    pip install openai python-dotenv pandas
    Add NVIDIA_API_KEY to .env
    python prelabel.py

After running: open data/prelabeled.csv, verify labels, then run finalize.py.
"""

import os
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("NVIDIA_API_KEY", "")
if not API_KEY or "paste" in API_KEY:
    raise SystemExit("Paste your NVIDIA API key into .env as NVIDIA_API_KEY before running.")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://integrate.api.nvidia.com/v1",
)
MODEL  = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are classifying posts and comments from r/OnePiecePowerScaling, a Reddit community that debates the power levels of One Piece characters.

Classify each post based on the TYPE of argument it makes (not which side it takes).

Assign EXACTLY ONE label:

feat_based — A strength argument supported by specific feats: named attacks shown on-panel, damage dealt or taken, speed or combat comparisons across fights, bounty used as a proxy for strength, or any concrete in-story evidence.
Example: "Shanks blocked a blow from Akainu with one arm and stopped Kaido's advance with his Haki alone. Mihawk has never shown anything comparable."

narrative_based — An argument rooted in narrative role rather than feats. The post infers strength from what a character symbolizes, their role in the story, titles, relationships to other characters, or how Oda portrays them.
Example: "Shanks is a Yonko and one of the Four Emperors — Oda wouldn't write him as Mihawk's inferior. Mihawk is a Warlord; the hierarchy is clear."

assertion — A bold strength claim with no supporting reasoning at all. The post asserts who is stronger but provides no feats, no narrative logic, no comparison — just a confident statement.
Example: "Mihawk mid-diffs Shanks, it's not even close."

Decision rules:
- If a post cites even one concrete feat (a named attack, an outcome of a fight, a bounty, a panel) → feat_based
- If a post leans on titles, hierarchy, symbolism, author's intent, or "Oda wouldn't write it this way" → narrative_based
- If a post makes a claim with zero reasoning — just a confident verdict → assertion
- A post can feel like a hot take but still be feat_based if it backs the take with specific evidence; check before labeling assertion

Respond with ONLY the label name. No explanation. No punctuation. One of:
feat_based
narrative_based
assertion"""

LABELS   = {"feat_based", "narrative_based", "assertion"}
IN_PATH  = "data/to_annotate.csv"
OUT_PATH = "data/prelabeled.csv"

df = pd.read_csv(IN_PATH)

if os.path.exists(OUT_PATH):
    done     = pd.read_csv(OUT_PATH)
    df_ids   = set(df["id"])
    done_ids = set(done["id"])
    extra    = done_ids - df_ids
    if extra:
        print(f"Warning: {len(extra)} labeled ids not in {IN_PATH} (stale rows).")
    done_ids = done_ids & df_ids
    pending  = df_ids - done_ids
    print(f"Resuming: {len(done_ids)} already labeled, {len(pending)} remaining.")
else:
    done     = pd.DataFrame()
    done_ids = set()

results = []
errors  = 0

for i, row in df.iterrows():
    if row["id"] in done_ids:
        continue

    text = str(row["text"])[:2000]

    for attempt in range(5):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": text},
                ],
                temperature=0,
                max_tokens=1000,
                reasoning_effort="low",
            )
            raw = (resp.choices[0].message.content or "").strip().lower()
            if not raw:
                print(f"  empty response — finish_reason: {resp.choices[0].finish_reason}")

            cleaned = raw.strip("*_`#\n ").replace(" ", "_")
            label   = cleaned.split()[0].rstrip(".,;:") if cleaned.split() else ""
            if label not in LABELS:
                label = cleaned.rstrip(".,;:")
            if label not in LABELS:
                variants = {
                    "feat_based":      ["feat_based", "feat based", "based on feats"],
                    "narrative_based": ["narrative_based", "narrative based", "narrative argument"],
                    "assertion":       ["assertion", "just a claim", "no reasoning"],
                }
                for canonical, aliases in variants.items():
                    if any(a in raw for a in aliases):
                        label = canonical
                        break
                else:
                    label = "UNCLEAR"
                    errors += 1
                    print(f"  UNCLEAR: {repr(raw[:80])}")

            out_row = row.to_dict()
            out_row["llm_label"]         = label
            out_row["label"]             = label
            out_row["annotation_source"] = "cerebras_assisted"
            out_row["reviewed"]          = 0
            out_row["notes"]             = ""
            results.append(out_row)

            n_done = len(done_ids) + len(results)
            print(f"[{n_done}/{len(df)}] {label:20s}  {text[:60].replace(chr(10), ' ')}")
            time.sleep(0.2)
            break

        except Exception as e:
            print(f"  error attempt {attempt+1}: {e}")
            time.sleep(8 * (attempt + 1))

    if len(results) % 5 == 0 and results:
        batch = pd.DataFrame(results)
        out   = pd.concat([done, batch], ignore_index=True) if not done.empty else batch
        out.to_csv(OUT_PATH, index=False)

if results:
    batch = pd.DataFrame(results)
    out   = pd.concat([done, batch], ignore_index=True) if not done.empty else batch
    out.to_csv(OUT_PATH, index=False)
else:
    out = done

print(f"\nDone. {len(out)} rows -> {OUT_PATH}")
print(f"UNCLEAR count: {errors}")
print(f"\nLabel distribution:")
print(out["llm_label"].value_counts().to_string())
print(f"\nNext step: review {OUT_PATH}, then run python finalize.py")

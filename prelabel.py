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

Classify each post based on its position in the Shanks vs. Mihawk debate.

Assign EXACTLY ONE label:

shanks_stronger — The post argues that Shanks is more powerful than Mihawk, or that Shanks would win a fight against Mihawk. Includes posts saying Mihawk is weaker than Shanks.
Example: "Shanks stopped Kaido's crew with just his presence. His Haki alone puts him above Mihawk."

mihawk_stronger — The post argues that Mihawk is more powerful than Shanks, or that Mihawk would win a fight against Shanks. Includes posts saying Shanks is weaker than Mihawk.
Example: "Mihawk holds the World's Strongest Swordsman title and Shanks is a swordsman. The title is explicitly comparative — Mihawk is above him."

equal — The post argues that Shanks and Mihawk are at the same power level, are rivals of equal strength, or that the debate is genuinely unresolvable.
Example: "Their rivalry is legendary and ongoing. Oda is clearly portraying them as equals — that's the entire point of their dynamic."

unrelated — The post is not primarily about the Shanks vs. Mihawk matchup. Discusses other characters, other matchups, or general power-scaling topics.
Example: "Zoro will surpass Mihawk eventually, but where does that put him relative to current Luffy?"

Decision rules:
- If a post takes a clear side but acknowledges the other (e.g. "Shanks wins but it's close") → label by the conclusion reached, NOT equal
- If a post mentions Shanks and Mihawk only as reference points for a different argument → unrelated
- If a post says "we can't know" but is still engaging with the Shanks/Mihawk matchup → equal

Respond with ONLY the label name. No explanation. No punctuation. One of:
shanks_stronger
mihawk_stronger
equal
unrelated"""

LABELS   = {"shanks_stronger", "mihawk_stronger", "equal", "unrelated"}
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
                    "shanks_stronger": ["shanks_stronger", "shanks stronger", "shanks is stronger"],
                    "mihawk_stronger": ["mihawk_stronger", "mihawk stronger", "mihawk is stronger"],
                    "equal":           ["equal", "they are equal", "same level"],
                    "unrelated":       ["unrelated", "not related"],
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

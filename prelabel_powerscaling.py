"""
Pre-labels data/to_annotate_powerscaling.csv using Gemma 4 31B via Google Gemini API.
Saves progress every 5 rows so it can resume if interrupted.

Usage:
    Add GEMINI_API_KEY to .env
    python prelabel_powerscaling.py
"""

import os
import time
import pandas as pd
from google import genai
from google.genai.types import GenerateContentConfig
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY or "paste" in API_KEY:
    raise SystemExit("Paste your Gemini API key into .env as GEMINI_API_KEY before running.")

client = genai.Client(api_key=API_KEY)
MODEL  = "gemma-4-31b-it"

SYSTEM_PROMPT = """You are classifying posts and comments from r/OnePiecePowerScaling, a Reddit community that debates the power levels of One Piece characters.

Your task: classify each post based on its position in the Shanks vs. Mihawk debate.

Assign EXACTLY ONE label:

shanks_stronger — The post argues that Shanks is more powerful than Mihawk, or that Shanks would win a fight against Mihawk.
Example: "Shanks stopped Kaido's crew with just his presence. His Haki alone puts him above Mihawk."

mihawk_stronger — The post argues that Mihawk is more powerful than Shanks, or that Mihawk would win a fight against Shanks.
Example: "Mihawk holds the World's Strongest Swordsman title and Shanks is a swordsman. The title is explicitly comparative — Mihawk is above him."

equal — The post argues that Shanks and Mihawk are at the same power level, are rivals of equal strength, or that the matchup is genuinely unresolvable.
Example: "Their rivalry is legendary and ongoing. Oda is portraying them as equals — that's the entire point of their dynamic."

unrelated — The post is not primarily about the Shanks vs. Mihawk matchup. It discusses other characters, other matchups, or general power-scaling topics.
Example: "Zoro will surpass Mihawk eventually but where does that put him relative to Luffy?"

Decision rules:
- If a post takes a clear side but acknowledges the other (e.g. "I think Shanks wins but it's close") → label by the conclusion reached, NOT equal
- If a post mentions Shanks and Mihawk only as reference points for a different argument → unrelated
- If a post says "we can't know" or "impossible to say" but is still engaging with the matchup → equal

Respond with ONLY the label name. No explanation. No punctuation. One of:
shanks_stronger
mihawk_stronger
equal
unrelated"""

LABELS   = {"shanks_stronger", "mihawk_stronger", "equal", "unrelated"}
IN_PATH  = "data/to_annotate_powerscaling.csv"
OUT_PATH = "data/prelabeled_powerscaling.csv"

df = pd.read_csv(IN_PATH)

# Resume from existing output
if os.path.exists(OUT_PATH):
    done     = pd.read_csv(OUT_PATH)
    done_ids = set(done["id"])
    print(f"Resuming: {len(done_ids)} already labeled, {len(df) - len(done_ids)} remaining.")
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
            resp = client.models.generate_content(
                model=MODEL,
                contents=text,
                config=GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0,
                    max_output_tokens=1000,
                ),
            )
            raw = (resp.text or "").strip().lower()
            if not raw:
                print(f"  empty response")

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
            out_row["annotation_source"] = "gemma_assisted"
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
print(f"\nNext step: review {OUT_PATH}, then run python finalize_powerscaling.py")

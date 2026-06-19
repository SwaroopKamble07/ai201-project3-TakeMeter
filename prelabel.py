"""
Pre-labels data/to_annotate.csv using Google Gemma 4 31B via the Gemini API.
Saves progress incrementally so it can resume if interrupted.

Usage:
    pip install google-genai pandas python-dotenv
    Paste your Gemini API key into .env as GEMINI_API_KEY
    python prelabel.py

After running: open data/prelabeled.csv, read each row, and verify the label.
The 'llm_label' column is the model's guess. Fill 'label' with your final decision.
Change 'reviewed' from 0 to 1 as you go so you can track progress.
You need ~100 confirmed per label. Aim to review the 400 highest-scoring rows first.
"""

import os
import time
import pandas as pd
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "")
if not API_KEY or API_KEY == "paste_your_key_here":
    raise SystemExit("Paste your Gemini API key into .env before running.")

client = genai.Client(api_key=API_KEY)
MODEL  = "gemma-4-31b-it"

SYSTEM_PROMPT = """You are a precise text classifier for posts and comments from r/OnePieceSpoilers, a Reddit community for discussing One Piece manga spoilers.

Classify each text into EXACTLY ONE of these four labels:

grounded_theory — Makes a specific prediction or interpretive claim backed by explicit evidence: cited chapter numbers, specific panel details, established lore, or demonstrated narrative patterns. The argument would hold even if emotional framing were removed.

speculation — A bold or confident prediction/claim stated WITHOUT supporting evidence. The post asserts rather than argues. May cite one fact decoratively, but the conclusion leaps far beyond what any evidence supports.

reaction — An immediate emotional or evaluative response to spoiler content. Expresses how the person FEELS about a reveal or moment. Little to no argument. The post is processing or sharing an emotional state.

observation — Identifies a specific, verifiable detail, visual pattern, callback, or structural parallel in existing manga panels or chapters. Points something out without making a future prediction or expressing primarily emotional content. Stops at noticing — no claim about what it means.

Decision rules for hard cases:
- If a post notices a detail AND uses it to argue a claim → grounded_theory (not observation)
- If a post cites one chapter number but the conclusion leaps far beyond it → speculation (not grounded_theory)
- If a post is emotional but also contains a prediction → label by DOMINANT intent (reaction if emotion dominates, speculation if prediction dominates)

Respond with ONLY the label name. No explanation. No punctuation. One of:
grounded_theory
speculation
reaction
observation"""

LABELS = {"grounded_theory", "speculation", "reaction", "observation"}

OUT_PATH = "data/prelabeled.csv"

# Load candidates
df = pd.read_csv("data/to_annotate.csv")

# Resume from existing output if it exists
if os.path.exists(OUT_PATH):
    done = pd.read_csv(OUT_PATH)
    done_ids = set(done["id"])
    print(f"Resuming: {len(done_ids)} already labeled, {len(df) - len(done_ids)} remaining.")
else:
    done = pd.DataFrame()
    done_ids = set()
    # Add output columns
    df["llm_label"]        = ""
    df["annotation_source"] = "llm_assisted"
    df["label"]            = ""   # user fills this in after reviewing
    df["reviewed"]         = 0    # user flips to 1 after reading
    df["notes"]            = ""   # user adds notes on hard cases

results = []
errors  = 0

for i, row in df.iterrows():
    if row["id"] in done_ids:
        continue

    text = str(row["text"])[:2000]   # truncate very long posts

    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0,
                    max_output_tokens=1024,
                ),
            )
            raw = (resp.text or "").strip().lower()
            if not raw:
                print(f"  empty response — finish_reason: {resp.candidates[0].finish_reason if resp.candidates else 'unknown'}")
            # Normalize: strip markdown, punctuation, replace spaces with underscores
            cleaned = raw.strip("*_`#\n ").replace(" ", "_")
            # Try first word after stripping
            label = cleaned.split()[0].rstrip(".,;:") if cleaned.split() else ""
            # Also try the whole cleaned string in case it's multi-word with underscores
            if label not in LABELS:
                label = cleaned.rstrip(".,;:")
            # Substring search across common variants
            if label not in LABELS:
                variants = {
                    "grounded_theory": ["grounded_theory", "grounded theory", "groundedtheory"],
                    "speculation":     ["speculation", "speculative"],
                    "reaction":        ["reaction", "react"],
                    "observation":     ["observation", "observe", "nooticing"],
                }
                for canonical, aliases in variants.items():
                    if any(a in raw for a in aliases):
                        label = canonical
                        break
                else:
                    label = "UNCLEAR"
                    errors += 1
                    print(f"  UNCLEAR raw response: {repr(raw[:80])}")

            out_row = row.to_dict()
            out_row["llm_label"]         = label
            out_row["label"]             = label    # pre-filled; user verifies
            out_row["annotation_source"] = "llm_assisted"
            out_row["reviewed"]          = 0
            out_row["notes"]             = ""
            results.append(out_row)

            n_done = len(done_ids) + len(results)
            total  = len(df)
            print(f"[{n_done}/{total}] {label:20s}  {text[:60].replace(chr(10), ' ')}")
            time.sleep(0.15)   # ~6-7 req/s; Groq free tier allows ~30/min
            break

        except Exception as e:
            if "rate" in str(e).lower():
                print(f"  rate limited, waiting 30s...")
                time.sleep(30)
            else:
                print(f"  error on row {i}: {e}")
                time.sleep(2 * (attempt + 1))

    # Save every 5 rows so progress isn't lost
    if len(results) % 5 == 0 and results:
        batch = pd.DataFrame(results)
        out   = pd.concat([done, batch], ignore_index=True) if not done.empty else batch
        out.to_csv(OUT_PATH, index=False)

# Final save
if results:
    batch = pd.DataFrame(results)
    out   = pd.concat([done, batch], ignore_index=True) if not done.empty else batch
    out.to_csv(OUT_PATH, index=False)
else:
    out = done

print(f"\nDone. {len(out)} rows saved to {OUT_PATH}")
print(f"Parse errors (UNCLEAR): {errors}")
print(f"\nLLM label distribution:")
print(out["llm_label"].value_counts().to_string())
print(f"\nNext steps:")
print("  1. Open data/prelabeled.csv in Excel/Sheets")
print("  2. Read each row; change 'label' if you disagree with 'llm_label'")
print("  3. Set 'reviewed' = 1 after reading each row")
print("  4. Add 'notes' for any hard cases (at least 3 required for the README)")
print("  5. When done, run: python finalize.py  (creates the final labeled CSV)")

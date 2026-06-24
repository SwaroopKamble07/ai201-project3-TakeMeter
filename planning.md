# TakeMeter: Planning Document
**Community:** r/OnePiecePowerScaling on Reddit
**Classifier goal:** Classify posts and comments by their position in the Shanks vs. Mihawk power-scaling debate

---

## Community

r/OnePiecePowerScaling is a subreddit dedicated to debating the relative strength of characters in the One Piece manga. Every post is explicitly argumentative — users stake out a position on who would win a fight and defend it with evidence from the manga. The community has strong norms around citing chapters and panels; unsupported claims are routinely challenged.

This community is a strong fit for a classification task for three reasons:
1. **Clear debate structure**: Most posts take an explicit side or make a claim about relative power, making the label signal concrete and text-visible.
2. **Recurring focal debate**: Shanks vs. Mihawk is one of the most contested matchups in the fandom — it has been actively debated for years, producing a large and varied corpus of arguments on all sides.
3. **Necessary filtering**: A real classifier needs to distinguish on-topic Shanks/Mihawk debate posts from unrelated power-scaling posts — that is the `unrelated` label's job.

---

## Labels

### 1. `shanks_stronger`
A post or comment arguing that Shanks is more powerful than Mihawk, or that Shanks would win in a fight against Mihawk. Includes posts framing this as "Mihawk is weaker than Shanks."

**Example A:**
> "Shanks stopped Kaido's entire crew from advancing just by arriving — that's a level of Haki dominance we have never seen from Mihawk. He is clearly in a tier above."

**Example B:**
> "The World Government fears Shanks more than any Warlord including Mihawk. Oda has been consistent about Shanks being above the Shichibukai system."

---

### 2. `mihawk_stronger`
A post or comment arguing that Mihawk is more powerful than Shanks, or that Mihawk would win in a fight against Shanks. Includes posts framing this as "Shanks is weaker than Mihawk."

**Example A:**
> "Mihawk holds the title of World's Strongest Swordsman and Shanks is a swordsman. That title is explicitly comparative. Oda would not give Mihawk that title if Shanks surpassed him."

**Example B:**
> "Mihawk cut a literal ice wave in half as a warmup at Marineford. We have never seen Shanks do anything on that scale."

---

### 3. `equal`
A post or comment arguing that Shanks and Mihawk are at the same power level, are rivals of equal strength, or that the debate is genuinely unresolvable given current evidence.

**Example A:**
> "Their rivalry is explicitly described as legendary and ongoing. Oda is clearly portraying them as equals — that is the entire point of their dynamic."

**Example B:**
> "We do not have enough feats to definitively rank one above the other. They are portrayed as peers and that is intentional."

---

### 4. `unrelated`
A post or comment that is not primarily about the Shanks vs. Mihawk matchup. May discuss other characters, other matchups, general power-scaling methodology, or One Piece lore unrelated to this debate.

**Example A:**
> "Zoro will surpass Mihawk by the end of the series — that is his entire character arc. But where does that put him relative to current Luffy?"

**Example B:**
> "Why does everyone lowball the Admirals? Aokiji froze an entire ocean. That is above anything the Yonko have shown."

---

## Hard Edge Cases

### Edge case 1: post takes a side but acknowledges the other
**Post:** "I think Shanks is stronger, but it is genuinely close. Mihawk's swordsmanship is probably better, but Shanks' Haki tips the scales."

This post takes a clear side but acknowledges the other. It is not `equal` because the poster commits to a conclusion.

**Decision rule:** If the post reaches a conclusion about who is stronger — even tentatively — label by that conclusion. `equal` is reserved for posts that explicitly argue the two are at the same level or that no ranking is possible. "Shanks edges Mihawk" -> `shanks_stronger`.

### Edge case 2: post mentions both as reference points for another argument
**Post:** "Shanks and Mihawk are both massively above Zoro's current level. Zoro needs at least 2 more power-ups."

Both characters are mentioned, but the post is not about the Shanks vs. Mihawk debate.

**Decision rule:** If the post's primary argument is not about the relative strength of Shanks and Mihawk to each other, label it `unrelated`. Using them as reference points for a different argument -> `unrelated`.

### Edge case 3: "impossible to say" posts
**Post:** "We literally do not have enough feats to rank these two. It is impossible to say."

**Decision rule:** If the post is still engaging with the Shanks/Mihawk matchup and framing them as peers (even implicitly), label `equal`. If the post is dismissing the debate entirely or redirecting to another topic, label `unrelated`.

---

## Data Collection Plan

**Source:** Posts and comments from r/OnePiecePowerScaling, collected via the Arctic Shift Reddit archive API (no credentials required). Scraping window: past 12 months.

**Target distribution:** 100 examples per label = 400 total.

| Label | Target count | Primary source |
|-------|-------------|----------------|
| shanks_stronger | 100 | Posts/comments arguing Shanks wins |
| mihawk_stronger | 100 | Posts/comments arguing Mihawk wins |
| equal | 100 | Posts/comments arguing equal/rival tier |
| unrelated | 100 | Posts about other matchups/characters |

**Split:** Handled automatically by Colab notebook (70/15/15).

**Collection strategy:**
- Scrape all posts and comments from r/OnePiecePowerScaling (past 12 months)
- Curate: posts mentioning BOTH Shanks and Mihawk -> debate candidates (shanks_stronger / mihawk_stronger / equal)
- Curate: posts mentioning NEITHER -> unrelated candidates
- Pre-label with Mistral Medium 3.5; review and verify before finalizing

**If a label is underrepresented:** `equal` posts are likely rarest. If short, re-scrape searching specifically for "rivals", "equal", or "same level" in post text.

---

## Evaluation Metrics

**Primary metrics:**
- **Overall accuracy** — percentage of test examples correctly classified.
- **Per-class F1 score** — essential because `equal` may be underrepresented and accuracy alone would hide poor performance on that class.
- **Confusion matrix** — 4x4 table showing which label pairs are confused most.

**Why accuracy alone is insufficient:**
If `unrelated` is easy to classify (different linguistic profile — no Shanks/Mihawk comparison framing), a model could achieve high accuracy by getting `unrelated` right while failing on the three debate labels. Per-class F1 exposes this. The critical boundary is `shanks_stronger` vs. `mihawk_stronger` vs. `equal`.

**Baseline comparison:** Zero-shot Groq llama-3.3-70b-versatile on the same test set.

---

## Definition of Success

**Minimum acceptable:**
- Overall accuracy >= 70%
- Per-class F1 >= 0.60 for all four labels
- Fine-tuned model beats zero-shot baseline by >= 10 percentage points

**Good enough for deployment:**
- Overall accuracy >= 80%
- `shanks_stronger` vs. `mihawk_stronger` F1 >= 0.75 (the critical distinction)
- `equal` F1 >= 0.60 (hardest class)

---

## AI Tool Plan

### Label stress-testing
Give Claude the four label definitions and edge case rules, ask it to generate 8-10 posts that blur `shanks_stronger`/`equal` and `equal`/`mihawk_stronger`. If those cannot be cleanly labeled, tighten the equal definition.

### Annotation assistance
Use Mistral Medium 3.5 to pre-label all scraped candidates. Track pre-labeled rows with `annotation_source = "mistral_assisted"`. Review every label before accepting — especially `equal` vs. `shanks_stronger` boundary calls.

### Failure analysis
After evaluation, give misclassified examples to Claude and ask it to identify patterns. Verify patterns manually before writing the report.

---

## Stretch Features (to be planned before starting)

- [ ] **Inter-annotator reliability** — recruit one other person to label 30 examples independently; compute Cohen's kappa
- [ ] **Confidence calibration** — plot calibration curve (confidence vs. actual accuracy) across confidence bins
- [ ] **Error pattern analysis** — systematic characterization of failure modes beyond individual examples
- [ ] **Deployed interface** — simple Gradio or Streamlit app that accepts a post/comment and returns label + confidence

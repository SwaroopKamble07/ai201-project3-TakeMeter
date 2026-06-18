# TakeMeter: Planning Document
**Community:** r/OnePieceSpoilers on Reddit
**Classifier goal:** Evaluate discourse quality by categorizing the type of "take" a post or comment represents

---

## Community

r/OnePieceSpoilers is a subreddit dedicated to discussing leaked spoilers, raw scans, and summaries of the One Piece manga before the official English release drops each week. The community is highly active every Wednesday through Friday when spoilers circulate, and discourse ranges enormously in quality: some posts cite specific panel details and chapter callbacks to build a careful argument; others are pure hopium ("Zoro is definitely going to fight Saturn next chapter"); others are immediate emotional responses to a big reveal; others simply notice a visual detail or parallel without drawing any conclusion.

This community is a strong fit for a classification task for three reasons:
1. **Volume and recurrence**: Spoiler weeks generate hundreds of comments and posts on a tight schedule, giving consistent data with similar prompts (everyone is reacting to the same chapter).
2. **Genuine quality variance**: The same information (e.g., a leaked panel) can produce a grounded theory citing three chapters of evidence, a baseless hype prediction, an emotional outburst, or a quiet "did anyone notice this detail" — all in the same thread.
3. **Community-legible distinctions**: Regular members of the sub actively distinguish between these types: "that's just hopium," "actually cite your evidence," "good catch" are common responses that map onto our labels.

---

## Labels

### 1. `grounded_theory`
A post or comment making a specific prediction or interpretive claim about One Piece story events, backed by explicit evidence — cited chapter numbers, specific panel details, established lore, or demonstrated narrative patterns. The argument would still hold if you stripped the emotional framing.

**Example A:**
> "Imu is directly connected to Joy Boy. In chapter 1085, the Empty Throne room shows the same symbol that appeared on the Void Century stone in ch 395. Combine that with Imu's reaction to Luffy's laugh in 1060 and it's clear Oda is setting up a mirror relationship between them."

**Example B:**
> "The 'D.' clan theme has consistently shown up whenever someone laughs in the face of death — Roger, Whitebeard, Luffy at Marineford, now Bonney in 1101. This is Oda telling us Bonney carries the Will of D. before he confirms it explicitly."

---

### 2. `speculation`
A bold or confident prediction or claim about One Piece that is stated without supporting evidence. The post asserts rather than argues. The claim may turn out to be correct, but the post provides no reasoning that would survive scrutiny.

**Example A:**
> "Shanks is definitely the final villain. He's been hiding something since chapter 1 and Oda always rewards patience like that."

**Example B:**
> "Zoro is going to 1v1 a Gorosei this arc, calling it now. He's been underutilized for too long and Oda owes him a real fight."

---

### 3. `reaction`
An immediate emotional or evaluative response to current spoiler content — a chapter, a leaked panel, a summary. The post expresses how the person *feels* about a reveal or moment. Little to no argument is made; the post is processing or sharing an emotional state.

**Example A:**
> "I am NOT okay. Oda really just did that to Vegapunk. I've been staring at the panel for 10 minutes. This chapter broke me."

**Example B:**
> "That Luffy panel is the most gorgeous thing Oda has ever drawn. The coloring in the raw, even without official release — peak manga."

---

### 4. `observation`
A post or comment that identifies a specific, verifiable detail, visual pattern, callback, or structural parallel in existing manga panels or chapters. The post points something out without making a future prediction or expressing primarily emotional content. The observation is complete in itself — it stops at noticing.

**Example A:**
> "Did anyone catch that in the chapter 1090 spread, every Straw Hat is positioned in the same order as the crew's wanted poster from chapter 435? Even the angles match."

**Example B:**
> "Oda has drawn Shanks gripping his sword with his right hand in every flashback panel. This week's raw he switched to his left. First time ever."

---

## Hard Edge Cases

### Edge case 1: observation that implies a theory
**Post:** "The shadow behind Imu on the Empty Throne in chapter 1085 has the exact same silhouette proportions as the figure from the Void Century carving in chapter 395."

This could be `observation` (noticing a visual detail) or `grounded_theory` (using that detail to argue Imu's identity or origin).

**Decision rule:** If the post stops at identifying the pattern — "look at this" — without making an explicit claim about what it means or predicts, label it `observation`. If the post uses the pattern as a premise for an argument ("therefore Imu is…" or "this confirms…"), label it `grounded_theory`. In the example above, the post states a parallel and nothing more → `observation`. If the same post added "which confirms Imu is the original Joy Boy's descendant," → `grounded_theory`.

### Edge case 2: speculation with one cited fact
**Post:** "In chapter 1100 Bonney absorbed Kuma's memories, so she's obviously going to be the one to kill Saturn. Calling it."

One chapter citation appears, but the conclusion ("obviously," "calling it") does not follow from the cited evidence — the evidence is decorative, not load-bearing for the claim.

**Decision rule:** If the cited evidence would genuinely support the conclusion even if you removed the opinion framing, label `grounded_theory`. If the evidence is cherry-picked or vague and the conclusion goes far beyond what it supports, label `speculation`. A single cite used to launch a leap → `speculation`.

### Edge case 3: emotional reaction that contains a prediction
**Post:** "OMG THIS CHAPTER WAS INSANE. Zoro is definitely going to beat Lucci next chapter, I can feel it!!!"

This is emotional (reaction) but also contains a future claim (speculation).

**Decision rule:** Label by the *dominant intent*. If the post is primarily venting or celebrating and the prediction is incidental ("I can feel it" is not an argument), label `reaction`. If the primary structure of the post is the prediction — even if expressed excitedly — label `speculation`. The example above is primarily emotional with a throwaway prediction → `reaction`.

---

## Data Collection Plan

**Source:** Both Reddit posts and comments from r/OnePieceSpoilers, collected using the PRAW Python library (Reddit API). Posts will include title + selftext; comments will be collected from weekly spoiler megathreads and high-engagement theory posts.

**Target distribution:** 100 examples per label = 400 total, to give the model enough signal per class and a meaningful test set.

| Label | Target count |
|-------|-------------|
| grounded_theory | 100 |
| speculation | 100 |
| reaction | 100 |
| observation | 100 |

**Split:** 320 train / 40 validation / 40 test (80/10/10). The test set will be held out completely until final evaluation — no peeking to adjust labels or thresholds.

**Collection strategy:**
- Scrape weekly "SPOILERS" megathread comments (reaction and observation labels tend to cluster here)
- Scrape top posts of all time and past 6 months tagged "Theory" or "Discussion" (grounded_theory and speculation)
- Filter out deleted comments, comments under 20 words (too short for a text classifier to learn from), and non-English posts

**If a label is underrepresented:** If after annotation any label has fewer than 80 examples, go back and scrape specifically for that type — e.g., search for "did anyone notice" or "I just realized" for observation; search pinned "Chapter X Spoilers" posts for reactions. Do not simply downsample other labels; add more examples to the underrepresented one.

**Pre-annotation read:** Before labeling, read 30–40 examples from the raw scrape to verify labels apply cleanly. If a label is consistently hard to distinguish from another in practice, revisit the decision rule before annotating all 400.

---

## Evaluation Metrics

**Primary metrics:**
- **Overall accuracy** — percentage of test examples correctly classified. Required by the spec and gives a summary number for comparison.
- **Per-class F1 score** — harmonic mean of precision and recall for each label. This is essential because the class distribution may not be perfectly balanced, and accuracy alone would hide a model that ignores the minority class.
- **Confusion matrix** — full 4×4 table showing what the model predicts for each true label. This is where failure mode analysis starts: which pairs of labels does the model conflate most?

**Why accuracy alone is insufficient:**
If `reaction` accounts for 40% of the test set and the model learns to predict `reaction` constantly, it achieves 40% accuracy without learning anything. Per-class F1 catches this. Additionally, not all errors are equally bad: confusing `grounded_theory` with `observation` (the model misses the predictive intent) is a different kind of failure than confusing `grounded_theory` with `speculation` (the model can't detect whether evidence is present). The confusion matrix makes these asymmetries visible.

**Baseline comparison:** The same test set will be run through Groq's `llama-3.3-70b-versatile` with a zero-shot prompt that includes the four label definitions and asks for a single label per example. Both models are evaluated on the same 20 test examples so the comparison is direct.

---

## Definition of Success

A classifier is **genuinely useful** for this community if it can reliably distinguish evidence-backed posts from unsupported speculation — that is the core quality signal TakeMeter is trying to surface. Secondary to that is separating reaction and observation from theory-type posts.

**Minimum acceptable threshold (for deployment consideration):**
- Overall accuracy ≥ 70% on the held-out test set
- Per-class F1 ≥ 0.60 for every label (no label is being systematically ignored)
- Fine-tuned model outperforms the zero-shot Groq baseline by at least 10 percentage points overall accuracy

**Good enough for a real community tool:**
- Overall accuracy ≥ 80%
- `grounded_theory` vs. `speculation` F1 ≥ 0.75 (the most important distinction for a quality meter)
- Confusion matrix shows no single pair of labels accounts for more than 30% of all errors

If the fine-tuned model does not beat the zero-shot baseline by at least 10 points, that is a meaningful negative result worth reporting — it would suggest the task may require more data, a larger base model, or a revised label taxonomy.

---

## AI Tool Plan

### Label stress-testing
Before annotating 200 examples, give Claude the four label definitions plus the three edge case decision rules and ask it to generate 10–15 posts that sit at the boundary between two labels. Specifically request posts that blur `grounded_theory` / `observation` and `speculation` / `reaction` since those are the two hardest boundaries. If generated posts can't be cleanly labeled using the current decision rules, tighten the rules before committing to annotation.

### Annotation assistance
Use Claude to pre-label a batch of 50 examples before reviewing them manually. Prompt: provide the four definitions and decision rules, then ask for a label and a one-sentence justification for each example. Review every pre-labeled example — accept, reject, or correct. Track which examples were pre-labeled vs. human-only in a column in the CSV (`annotation_source`: `human` or `llm_assisted`). This column will be disclosed in the README.

### Failure analysis
After evaluation, give Claude the list of wrong predictions (true label, predicted label, post text) and ask it to identify systematic patterns — e.g., "the model always predicts speculation when the post is short" or "it can't distinguish observation from reaction when the detail noticed is about a character's appearance." Use this analysis to seed the "wrong predictions" section of the evaluation report, then verify each pattern manually by looking at the actual examples.

---

## Stretch Features (to be planned before starting)

- [ ] **Inter-annotator reliability** — recruit one other person to label 30 examples independently; compute Cohen's kappa
- [ ] **Confidence calibration** — plot calibration curve (confidence vs. actual accuracy) across confidence bins
- [ ] **Error pattern analysis** — systematic characterization of failure modes beyond individual examples
- [ ] **Deployed interface** — simple Gradio or Streamlit app that accepts a post/comment and returns label + confidence
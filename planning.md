# TakeMeter: Planning Document

**Community:** r/OnePiecePowerScaling on Reddit
**Classifier goal:** Classify One Piece power-scaling posts and comments by the type of argument they use.

---

## Community

r/OnePiecePowerScaling is a subreddit dedicated to debating the relative strength of One Piece characters. The community is a good fit for this task because most posts are explicitly argumentative: users compare characters, cite fights, invoke story portrayal, or make confident rankings.

This makes the subreddit useful for an argument-type classifier for three reasons:
1. **Clear argumentative structure:** posts usually make a claim about who is stronger, weaker, overrated, underrated, or in the same tier.
2. **Multiple reasoning styles:** users support claims with feats, narrative logic, titles, character portrayal, or sometimes no evidence at all.
3. **Real boundary cases:** many posts mix evidence types, so the labels require decision rules rather than simple keyword matching.

---

## Labels

### 1. `feat_based`
A post or comment is `feat_based` when it supports a strength claim using concrete in-story evidence. This includes named attacks, fights shown on panel, damage dealt or taken, speed comparisons, durability feats, bounty used as a proxy for strength, or direct comparison across battles.

**Example A:**
> "Shanks blocked Akainu's attack at Marineford and stopped Greenbull with Haki from far away. Mihawk has not shown a comparable combat feat yet."

**Example B:**
> "Kaido tanked attacks from the Scabbards, Yamato, Zoro, Law, Kid, and Luffy before finally going down. His endurance feats are above Big Mom's."

---

### 2. `narrative_based`
A post or comment is `narrative_based` when it argues from story role, portrayal, hierarchy, titles, symbolism, author intent, or relationships between characters rather than from direct combat evidence.

**Example A:**
> "Shanks is being saved for the final saga, so Oda is clearly portraying him as one of the highest-level pirates in the story."

**Example B:**
> "Mihawk has to remain extremely strong because Zoro's dream depends on him being a legitimate final benchmark."

---

### 3. `assertion`
A post or comment is `assertion` when it makes a confident strength claim without giving supporting reasoning. The post may be opinionated or specific, but it does not explain the claim using feats, narrative logic, titles, or other evidence.

**Example A:**
> "Mihawk mid-diffs Shanks and it is not close."

**Example B:**
> "Kaido clears the admirals easily."

---

## Hard Edge Cases

### Edge case 1: a post contains both feats and narrative framing
**Post:** "Shanks is a Yonko and Oda clearly portrays him as a final-saga monster, but he also stopped Greenbull with Haki and one-shot Kid."

This post includes narrative reasoning and concrete evidence.

**Decision rule:** If the post uses at least one concrete in-story feat as part of the argument, label it `feat_based`. The feat gives the model a more specific evidence type than general portrayal.

### Edge case 2: a post uses titles or hierarchy without direct feats
**Post:** "Mihawk is the World's Strongest Swordsman, and Zoro's whole dream depends on that title meaning something."

This post is not simply an unsupported assertion because it explains the claim through a title and narrative role.

**Decision rule:** Label title, hierarchy, portrayal, or author-intent arguments as `narrative_based` unless the post also cites concrete fight evidence.

### Edge case 3: a post sounds like a hot take but gives no support
**Post:** "Loki power-cliffed Kaido. The old top tiers are finished."

This post makes a clear claim but does not explain why.

**Decision rule:** Label confident unsupported takes as `assertion`, even if the claim is specific or controversial.

---

## Data Collection Plan

**Source:** Posts and comments from r/OnePiecePowerScaling, collected through the Arctic Shift Reddit archive API.

**Target distribution:** At least 200 labeled examples total, with no single label above 70% of the final dataset.

| Label | Target count | Primary source |
|-------|--------------|----------------|
| `feat_based` | 200+ | Posts/comments citing fights, attacks, panels, durability, speed, or other concrete evidence |
| `narrative_based` | 200+ | Posts/comments citing story role, portrayal, hierarchy, titles, or author intent |
| `assertion` | 200+ | Posts/comments making strength claims without supporting reasoning |

**Split:** Handled automatically by the Colab notebook.

**Collection strategy:**
- Scrape posts and comments from r/OnePiecePowerScaling.
- Filter for substantive posts that mention common power-scaling characters.
- Pre-label with an LLM using the project label definitions.
- Manually review and correct labels before finalizing the dataset.
- Use `finalize.py` to remove invalid labels and keep the label distribution balanced.

**If a label is underrepresented:** `feat_based` is likely to be hardest to balance because many posts mix concrete evidence with broad narrative claims. If short, prioritize longer analysis posts and comments that mention fights, named attacks, or direct battle outcomes.

---

## Evaluation Metrics

**Primary metrics:**
- **Overall accuracy:** percentage of test examples correctly classified.
- **Per-class F1 score:** required because a model could do reasonably well overall while failing on the hardest label.
- **Confusion matrix:** shows which argument types the model confuses most.

**Why accuracy alone is insufficient:**
The labels are not equally difficult. `assertion` and `narrative_based` can overlap when a post gives vague story logic, and `feat_based` can be missed when a post mentions a feat briefly inside a larger opinion. Per-class F1 and the confusion matrix expose those failures better than overall accuracy alone.

**Baseline comparison:** A zero-shot LLM classifier evaluated on the same test set using the same label definitions.

---

## Definition of Success

**Good enough performance:**
- Overall accuracy >= 70%.
- Per-class F1 >= 0.60 for all three labels.
- Fine-tuned model beats the zero-shot baseline by >= 10 percentage points.

This threshold is concrete enough for the assignment while still leaving room for the task's real ambiguity. A model below 70% can still show useful learning, but it should be described as not yet meeting the planned success bar.

---

## AI Tool Plan

### Label stress-testing
Ask an AI assistant to generate examples that blur `feat_based` vs. `narrative_based` and `narrative_based` vs. `assertion`. Use those examples to tighten the decision rules before final annotation.

### Annotation assistance
Use an LLM to pre-label candidate posts. Track AI-assisted rows with `annotation_source`, then manually review and correct labels before accepting them into `data/labeled.csv`.

### Failure analysis
After evaluation, inspect confusion matrix patterns and wrong predictions. Use AI assistance to suggest possible failure patterns, but verify those patterns manually against the labeled examples.

---

## Stretch Features

- [ ] Inter-annotator reliability: ask another person to label a small sample and compare agreement.
- [ ] Confidence calibration: compare model confidence with actual correctness.
- [ ] Error pattern analysis: group wrong predictions by boundary type.
- [ ] Deployed interface: create a simple app that accepts a post/comment and returns label plus confidence.

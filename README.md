# ai201-project3-TakeMeter

TakeMeter classifies posts and comments from r/OnePiecePowerScaling by the type of argument being made.

## Community

r/OnePiecePowerScaling is a good fit for this project because it is already a highly argumentative community. Posts usually compare characters, justify a claim with feats or story logic, or state a confident ranking with little evidence. That gives the classifier clear label boundaries while still leaving plenty of hard cases where the reasoning style matters more than the topic.

## Labels

The final taxonomy uses three labels.

### `feat_based`
A post is `feat_based` when it supports a strength claim with concrete in-story evidence.

Example A:
> "Shanks blocked Akainu's attack at Marineford and stopped Greenbull with Haki from far away. Mihawk has not shown a comparable combat feat yet."

Example B:
> "Kaido tanked attacks from the Scabbards, Yamato, Zoro, Law, Kid, and Luffy before finally going down. His endurance feats are above Big Mom's."

### `narrative_based`
A post is `narrative_based` when it argues from story role, portrayal, hierarchy, titles, symbolism, author intent, or character relationships rather than direct combat evidence.

Example A:
> "Shanks is being saved for the final saga, so Oda is clearly portraying him as one of the highest-level pirates in the story."

Example B:
> "Mihawk has to remain extremely strong because Zoro's dream depends on him being a legitimate final benchmark."

### `assertion`
A post is `assertion` when it makes a confident strength claim without giving supporting reasoning.

Example A:
> "Mihawk mid-diffs Shanks and it is not close."

Example B:
> "Kaido clears the admirals easily."

## Data

**Source:** r/OnePiecePowerScaling posts and comments collected from the Arctic Shift Reddit archive API.

**Labeling process:** Candidate posts were filtered for substantive One Piece power-scaling content, pre-labeled with an LLM, then reviewed before finalization. The final dataset was produced with `finalize.py`, which drops invalid labels and caps overrepresented labels to keep the dataset balanced.

**Final dataset:** `data/labeled.csv`

| Label | Count | Share |
|-------|------:|------:|
| `assertion` | 416 | 40.4% |
| `narrative_based` | 405 | 39.4% |
| `feat_based` | 208 | 20.2% |
| **Total** | **1029** | **100.0%** |

No single label accounts for more than 70% of the dataset.

## Difficult Labeling Examples

1. **Feat mention inside a broader opinion:** A post saying Loki survived against Imu and therefore should scale above Shanks or Kaido was labeled `feat_based` because the claim depends on a specific in-story survival or combat event, even though the tone is casual.

2. **Title and story role without combat evidence:** A post arguing that Mihawk must be strong because Zoro's dream depends on him was labeled `narrative_based`, not `assertion`, because it gives a story-role justification.

3. **Confident matchup claim with little support:** A post asking how far Kaido gets in an admiral gauntlet was labeled `assertion` because it frames a power claim but does not provide evidence or reasoning in the post itself.

## Fine-Tuning Pipeline

**Base model:** `distilbert-base-uncased`

**Training platform:** Google Colab

**Training setup:** The project fine-tuned `distilbert-base-uncased` for 15 epochs with a learning rate of `1e-5`, train batch size `16`, eval batch size `32`, max sequence length `256`, weight decay `0.01`, and `50` warmup steps. I used a lower learning rate than the common `2e-5` starting point because this is a small, subjective text-classification dataset, so slower updates are less likely to overwrite pretrained language features too aggressively. I evaluated and saved checkpoints every epoch and loaded the best model by validation accuracy.

## Baseline Comparison

The baseline was a zero-shot LLM classifier using the same three label definitions. Baseline predictions were collected on the same 155-example test set used for the fine-tuned model.

Baseline system prompt:

```text
You are classifying posts and comments from r/OnePiecePowerScaling, a Reddit community that debates the power levels of One Piece characters.

Classify each post based on the TYPE of argument it makes (not which side it takes).

Assign EXACTLY ONE label:

feat_based - A strength argument supported by specific feats: named attacks shown on-panel, damage dealt or taken, speed or combat comparisons across fights, bounty used as a proxy for strength, or any concrete in-story evidence.
Example: "Shanks blocked a blow from Akainu with one arm and stopped Kaido's advance with his Haki alone. Mihawk has never shown anything comparable."

narrative_based - An argument rooted in narrative role rather than feats. The post infers strength from what a character symbolizes, their role in the story, titles, relationships to other characters, or how Oda portrays them.
Example: "Shanks is a Yonko and one of the Four Emperors - Oda wouldn't write him as Mihawk's inferior. Mihawk is a Warlord; the hierarchy is clear."

assertion - A bold strength claim with no supporting reasoning at all. The post asserts who is stronger but provides no feats, no narrative logic, no comparison - just a confident statement.
Example: "Mihawk mid-diffs Shanks, it's not even close."

Decision rules:
- If a post cites even one concrete feat (a named attack, an outcome of a fight, a bounty, a panel) -> feat_based
- If a post leans on titles, hierarchy, symbolism, author's intent, or "Oda wouldn't write it this way" -> narrative_based
- If a post makes a claim with zero reasoning - just a confident verdict - -> assertion
- A post can feel like a hot take but still be feat_based if it backs the take with specific evidence; check before labeling assertion

Respond with ONLY the label name. No explanation. No punctuation. One of:
feat_based
narrative_based
assertion
```

| Model | Accuracy |
|-------|---------:|
| Zero-shot baseline | 50.00% |
| Fine-tuned DistilBERT | 64.52% |
| Improvement | +14.52 percentage points |

The fine-tuned model beat the baseline by more than 10 percentage points, which meets the planned baseline-improvement target.

## Evaluation Report

Evaluation artifacts are in `colab_results/`.

- Results JSON: `colab_results/evaluation_results.json`
- Confusion matrix image: `colab_results/confusion_matrix.png`
- Test set size: 155 examples

### Fine-Tuned Model Metrics

| Label | Precision | Recall | F1 |
|-------|----------:|-------:|---:|
| `assertion` | 0.66 | 0.68 | 0.67 |
| `narrative_based` | 0.60 | 0.72 | 0.66 |
| `feat_based` | 0.76 | 0.42 | 0.54 |

Overall accuracy was 64.52%.

### Confusion Matrix

Rows are true labels and columns are predicted labels.

| True \ Predicted | `assertion` | `narrative_based` | `feat_based` |
|------------------|------------:|------------------:|-------------:|
| `assertion` | 43 | 17 | 3 |
| `narrative_based` | 16 | 44 | 1 |
| `feat_based` | 6 | 12 | 13 |

### Sample Classifications

| Post | Predicted | Confidence | Why It Makes Sense |
|------|-----------|-----------:|--------------------|
| "Shanks stopped Greenbull with Haki from far away." | `feat_based` | 0.91 | The post names a concrete combat event, so the model is right to treat it as feat evidence. |
| "Shanks is being saved for the final saga, so Oda is clearly portraying him as one of the highest-level pirates." | `narrative_based` | 0.87 | This is a portrayal-based argument, not a direct feat comparison. |
| "Mihawk mid-diffs Shanks and it is not close." | `assertion` | 0.84 | The claim is strong but gives no supporting reasoning. |
| "Kaido tanked attacks from the Scabbards, Yamato, Zoro, Law, Kid, and Luffy." | `feat_based` | 0.89 | The post relies on explicit fight outcomes and durability feats. |

The first row is the clearest correct example because it directly cites an in-story event rather than a vague impression.

## Error Analysis

The main failure pattern is that the model under-detects `feat_based` examples. It correctly predicted only 13 of 31 true `feat_based` test examples, with 12 mislabeled as `narrative_based` and 6 mislabeled as `assertion`.

This suggests the model learned broad argumentative tone better than it learned the evidence boundary. A post can contain a concrete feat but still sound like a general opinion, and the model often follows the tone instead of noticing the specific evidence.

Three specific wrong predictions:

1. **True: `assertion`, predicted: `narrative_based`**
   Text: "Oda if you're listening, I'm willing to give you my savings, car, house and even first-born if you make Luffy underperform in Elbaf."
   Analysis: The model reads the post as story-portrayal talk because it is wrapped in fandom and arc speculation, but the label should stay `assertion` because there is no real reasoning beyond a strong wish or take.

2. **True: `narrative_based`, predicted: `assertion`**
   Text: "No agenda here, how the fuck did this not split the sky? You mean to tell me that Cancerbeard and Shanks can split the sky but not Loki and Imu?"
   Analysis: The post is trying to argue from narrative comparison and power portrayal, but the model collapses it into a hot take because the evidence is compressed and informal.

3. **True: `feat_based`, predicted: `narrative_based`**
   Text: "God Valley will show why Old Gen Haki is built different, Roger Haki will send IMU back to Mariejoa like Joyboy did to Gorosei."
   Analysis: The model misses the concrete-feat side of the claim and overweights the surrounding story framing. This is the main boundary problem in the project: feat evidence embedded inside narrative language.

## Reflection

The model captured the broad shape of the task, especially the difference between direct unsupported takes and more reasoned posts. What it still misses is the exact boundary between concrete evidence and narrative framing. In practice, it seems to learn tone faster than it learns whether a post is actually using a feat, which is why `feat_based` is the weakest class.

## Definition of Success

The planned success threshold was:

- Overall accuracy >= 70%.
- Per-class F1 >= 0.60 for all three labels.
- Fine-tuned model beats the zero-shot baseline by >= 10 percentage points.

The current model partially meets this definition. It beats the baseline by 14.52 percentage points, but its 64.52% accuracy is below the 70% target and its `feat_based` F1 is 0.54, below the 0.60 target.

## AI Usage and Spec Reflection

AI was used in two main ways:

1. **Annotation assistance:** an LLM pre-labeled candidate posts using the project taxonomy. I reviewed and corrected those labels before they were accepted into the dataset, especially on boundary cases where a post mixed feats and story language.
2. **Documentation support:** AI assistance was used to tighten the README structure, summarize the evaluation results, and turn the confusion matrix into a concrete failure-pattern reflection. I kept the actual thresholds and metric values from my project artifacts instead of inventing new ones.

The assignment spec helped keep the project concrete: it required a clear label taxonomy, a balanced dataset, a baseline comparison, and per-class evaluation rather than only overall accuracy. The implementation diverged from the first planning idea by shifting away from a Shanks-vs-Mihawk stance classifier and toward a more general argument-type classifier. That change made the dataset broader and easier to collect at scale, but it also created a harder boundary between `feat_based` and `narrative_based`.

## Demo Video

The demo video should show 3 to 5 posts with the model's predicted label and confidence visible, then walk through one correct prediction, one incorrect prediction, and a brief evaluation summary using the confusion matrix and metric table above.
Here is the link to the demo video with all of those specified parts that I went over: https://www.youtube.com/watch?v=bCdfnZgBErQ

# ai201-project3-TakeMeter

TakeMeter classifies posts and comments from r/OnePiecePowerScaling by the type of argument being made.

## Labels

The final taxonomy uses three labels:

| Label | Definition |
|-------|------------|
| `feat_based` | A strength argument supported by concrete in-story evidence, such as fights, attacks, damage, durability, speed, panels, or battle outcomes. |
| `narrative_based` | A strength argument based on story role, portrayal, hierarchy, titles, symbolism, author intent, or character relationships. |
| `assertion` | A confident strength claim with no supporting reasoning. |

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

1. **Feat mention inside a broader opinion:** A post saying Loki survived against Imu and therefore should scale above Shanks or Kaido was labeled `feat_based` because the claim depends on a specific in-story survival/combat event, even though the tone is casual.

2. **Title and story role without combat evidence:** A post arguing that Mihawk must be strong because Zoro's dream depends on him was labeled `narrative_based`, not `assertion`, because it gives a story-role justification.

3. **Confident matchup claim with little support:** A post asking how far Kaido gets in an admiral gauntlet was labeled `assertion` because it frames a power claim but does not provide evidence or reasoning in the post itself.

## Fine-Tuning Pipeline

**Base model:** `distilbert-base-uncased`

**Training platform:** Google Colab

**Key training decision:** The project fine-tuned `distilbert-base-uncased` for 15 epochs with a learning rate of `1e-5`, train batch size `16`, eval batch size `32`, max sequence length `256`, weight decay `0.01`, and `50` warmup steps. I used a lower learning rate than the common `2e-5` starting point because this is a small, subjective text-classification dataset, so a slower update rate is less likely to overwrite the pretrained language features too aggressively.

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
- If a post makes a claim with zero reasoning - just a confident verdict -> assertion
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

## Error Analysis

The main failure pattern is that the model under-detects `feat_based` examples. It correctly predicted only 13 of 31 true `feat_based` test examples, with 12 mislabeled as `narrative_based` and 6 mislabeled as `assertion`.

This suggests the model learned broad argumentative tone better than it learned the evidence boundary. A post can contain a concrete feat but still sound like a general opinion, and the model often follows the tone instead of noticing the specific evidence.

Three important wrong-prediction patterns:

1. **`feat_based` -> `narrative_based`:** likely happens when a post mentions a fight or outcome but frames it through portrayal or character status.
2. **`assertion` -> `narrative_based`:** likely happens when an unsupported claim uses story-flavored language without actually giving a reason.
3. **`narrative_based` -> `assertion`:** likely happens when the narrative reasoning is implicit, short, or phrased like a hot take.

The current Colab output does not include row-level wrong predictions, so three exact misclassified post texts still need to be added before final submission to fully satisfy the error-analysis requirement.

Three examples:
--- #1 ---
Text:      Oda if you’re listening, I’m willing to give you my savings, car, house and even first-born if you make Luffy underperform in Elbaf.

As a certified day-one Chapter 1130 Loki glazer please Oda, you ca...
True:      assertion
Predicted: narrative_based  (confidence: 0.72)

Explanation: This seems a bit ambiguous, since it is mainly hype for Luffy and not actually mainly powerscaling. Assertion is a bit more accurate here, but narrative_based is not wrong either.

--- #2 ---
Text:      No agenda here, how the fuck did this not split the sky?

You mean to tell me that Cancerbeard and Shanks can split the sky but not Loki and Imu? 

Yeah Oda does NOT care about clash sky splits lol
True:      narrative_based
Predicted: assertion  (confidence: 0.56)

Explanation: To know that this is narrative_based, the model would need to know details about the story such as why Loki and Imu are as narratively significant as Whitebeard (Cancerbeard) and Shanks.

--- #3 ---
Text:      "God valley will show why Old Gen Haki is built different, Roger Haki will send IMU back to Mariejoa like joyboy did to Gorosei".

They were getting hyped too much just for their haki feats to end up ...
True:      feat_based
Predicted: narrative_based  (confidence: 0.76)

Explanation: The hype around Roger is mainly based on the similar Haki of Joyboy. However, while that is a feat of Joyboy, without knowing what exactly Haki is, the model has no way of knowing that it counts as a feat and not just narrative.

## Definition of Success

The planned success threshold was:

- Overall accuracy >= 70%.
- Per-class F1 >= 0.60 for all three labels.
- Fine-tuned model beats the zero-shot baseline by >= 10 percentage points.

The current model partially meets this definition. It beats the baseline by 14.52 percentage points, but its 64.52% accuracy is below the 70% target and its `feat_based` F1 is 0.54, below the 0.60 target.

## AI Usage and Spec Reflection

AI was used in two main ways:

1. **Annotation assistance:** an LLM pre-labeled candidate posts using the project taxonomy. Those labels were then reviewed before being finalized.
2. **Planning and documentation support:** AI assistance was used to refine the project plan, align the README with the rubric, and describe likely failure patterns from the confusion matrix.

The assignment spec helped keep the project concrete: it required a clear label taxonomy, a balanced dataset, a baseline comparison, and per-class evaluation rather than only overall accuracy. The implementation diverged from the first planning idea by shifting away from a Shanks-vs-Mihawk stance classifier and toward a more general argument-type classifier. That change made the dataset broader and easier to collect at scale, but it also created a harder boundary between `feat_based` and `narrative_based`.

## Groq Llama 3.3 70b System Prompt

You are classifying posts and comments from r/OnePiecePowerScaling, a Reddit community that debates the power levels of One Piece characters.

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
assertion

## Model hyperparameters

MODEL_NAME = "distilbert-base-uncased"
num_train_epochs = 15
per_device_train_batch_size = 16
per_device_eval_batch_size = 32
learning_rate = 1e-5
weight_decay = 0.01
warmup_steps = 50
eval_strategy = "epoch"
save_strategy = "epoch"
save_total_limit = 1
load_best_model_at_end = True
metric_for_best_model = "accuracy"
logging_steps = 10
report_to = "none"
max_length = 256
train/val/test split = 70/15/15
random_state = 42
stratify = label_id

These were the defaults except I decreased the learning rate and increased the number of epochs since I observed better performance this way.

## Rubric Status

The project currently satisfies the dataset size, label balance, baseline comparison, confusion matrix, and per-class metric requirements.

Remaining gaps before submission:

- Ensure the demo video shows 3-5 model classifications, including one correct and one incorrect prediction.



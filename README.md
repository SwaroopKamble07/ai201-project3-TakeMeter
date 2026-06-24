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

**Key training decision:** The project used a train/test evaluation setup with the same held-out test set for both the baseline and the fine-tuned model. This matters because the goal is not just to report a fine-tuned score, but to show whether fine-tuning improves over a comparable zero-shot baseline.

Before final submission, add the exact training hyperparameters from the Colab notebook, such as number of epochs, learning rate, batch size, or maximum sequence length, plus one sentence explaining why that choice was reasonable.

## Baseline Comparison

The baseline was a zero-shot LLM classifier using the same three label definitions. Baseline predictions were collected on the same 155-example test set used for the fine-tuned model. Before final submission, paste the exact baseline prompt from the Colab notebook here so the baseline is reproducible.

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

## Rubric Status

The project currently satisfies the dataset size, label balance, baseline comparison, confusion matrix, and per-class metric requirements.

Remaining gaps before submission:

- Add the exact Colab training hyperparameters and reasoning.
- Add the exact zero-shot baseline prompt.
- Add three exact wrong predictions with post text, predicted label, true label, and explanation.
- Ensure the demo video shows 3-5 model classifications, including one correct and one incorrect prediction.

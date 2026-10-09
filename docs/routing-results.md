# Routing results on our own posts

Measured 8 Oct 2026 on Akshara's laptop (Apple M5, PyTorch on MPS). Every number below comes from `scripts/evaluate_routing.py` and the training scripts on that day.

## Read this first

- **The labels are AI-drafted and reviewed by the authors.** All 734 posts were given a first-pass label by an AI assistant following `docs/label-set.md` and the emergency definition in `docs/labelling.md`, then reviewed by the authors and used as the gold labels (`python scripts/merge_labels.py --from-drafts`). The scores below measure agreement with these labels, not with a clinician, and there is no Cohen's κ.
- **The sets are small.** 50 dev posts and 115 test posts, so the 95% intervals are about ±9–15 points and most differences between routers are inside them.
- **The test split was read twice.** Once on 8 Oct during a dry run that checked the code works, for the TF-IDF router only and with arbitrary cutoffs, and once for the results below. Nothing was chosen or changed after the dry run. Every choice (which router, which version, the cutoffs) was made on dev.

## The data

| Split | Posts | How it's drawn |
|---|---:|---|
| Train | 362 | the rest of the train pool: mostly posts a quick router rated likely for each label, so rare specialties get examples, plus random ones |
| Dev | 50 | from the 100 randomly drawn train posts only (75 fixed candidates, minus Skip and Emergency), so it has the same label mix as test |
| Test | 115 | a plain random sample (190 drawn, minus Skip and Emergency) |
| Emergency | 54 | kept out of the router; used to test the emergency rules |
| Skip | 153 | not a "which doctor" question |

527 posts are usable by the router (train + dev + test).

| Label | Train | Dev | Test |
|---|---:|---:|---:|
| Dermatology | 28 | 1 | 5 |
| Orthopedics | 27 | 3 | 9 |
| ENT | 42 | 2 | 10 |
| Gastroenterology | 29 | 6 | 11 |
| Neurology | 29 | 2 | 14 |
| Urology | 22 | 3 | 5 |
| Ob-Gyn | 27 | 6 | 6 |
| Mental health | 20 | 2 | 1 |
| Cardiology | 14 | 2 | 5 |
| Eye care | 29 | 0 | 1 |
| Dentistry | 7 | 1 | 1 |
| Start with a GP | 88 | 22 | 47 |

"Start with a GP" is 41% of the test posts and 44% of dev, so "always GP" is the baseline every router has to beat. Mental health, Eye care and Dentistry have one test post each, so their per-label scores mean nothing.

## How the routers were trained

- **Stage 1 (public only):** retrained on this laptop from the public Patient Comments set. On its 938 held-out comments: TF-IDF 94.0% top-1, DistilRoBERTa 95.0%, BiomedBERT 94.3%. (Sohum's run got 94.3% for DistilRoBERTa; training on a different machine is not bit-for-bit repeatable.)
- **Ours only:** TF-IDF + logistic regression, and each encoder from its original weights, on our 362 train posts.
- **Public, then ours:** each encoder continued from its stage-1 checkpoint on our train posts. For TF-IDF there is no second stage, so this row is one model trained on our posts and the public set together.
- Encoders: all weights trained, 6 epochs, learning rate 2e-5, the epoch with the best dev macro-F1 kept. Posts were cut to **384 tokens** (the plan said 512) and trained in batches of 4 with gradients added over 2 steps, so training fits in the laptop's memory. 28% of train and dev posts are longer than 256 tokens; none is longer than 512. Scoring uses up to 512 tokens, as the app does.

## Dev: picking the version of each router

Our 50 dev posts. "Top-1, alternate counts" scores a hit when the top choice is the primary or the alternate label.

| Router | Top-1 (95% CI) | Top-3 | Top-1, alternate counts | Macro-F1 |
|---|---|---|---|---|
| Always "Start with a GP" | 44.0% (30.0–58.7%) | 52.0% | 72.0% | 0.051 |
| TF-IDF, public only | 32.0% (19.5–46.7%) | 68.0% | 68.0% | 0.160 |
| TF-IDF, ours only | 50.0% (35.5–64.5%) | 84.0% | 80.0% | 0.217 |
| TF-IDF, public and ours | 46.0% (31.8–60.7%) | 78.0% | 70.0% | 0.263 |
| DistilRoBERTa, public only | 42.0% (28.2–56.8%) | 90.0% | 66.0% | 0.312 |
| DistilRoBERTa, ours only | 44.0% (30.0–58.7%) | 80.0% | 76.0% | 0.407 |
| DistilRoBERTa, public then ours | 56.0% (41.3–70.0%) | 96.0% | 84.0% | 0.419 |
| BiomedBERT, public only | 44.0% (30.0–58.7%) | 88.0% | 74.0% | 0.180 |
| BiomedBERT, ours only | 54.0% (39.3–68.2%) | 90.0% | 80.0% | **0.473** |
| BiomedBERT, public then ours | 52.0% (37.4–66.3%) | 98.0% | 78.0% | 0.378 |

- **Training on our posts helps every router**, most clearly in macro-F1 (TF-IDF 0.160 → 0.263, DistilRoBERTa 0.312 → 0.419, BiomedBERT 0.180 → 0.473). Public data alone transfers poorly: the public comments are one short line, our posts are paragraphs.
- **Public first, then ours, is mixed.** It is the best version of DistilRoBERTa and of TF-IDF on macro-F1, but not of BiomedBERT. With 50 dev posts these gaps are within the intervals.
- Picked on dev macro-F1, one per family: **TF-IDF public and ours, DistilRoBERTa public then ours, BiomedBERT ours only**. BiomedBERT ours only is the one the app ships (`ROUTER_ORDER` in `doccompass/pipeline.py`).

## Dev: the "unsure" cutoffs

For the shipped router, 133 pairs of TAU (0–0.90) and MARGIN (0–0.30) were tried on dev. A result shows two options when the top confidence is below TAU or the top two are closer than MARGIN. The choice: the pair whose shown answer is most often right (one answer: it matches the primary or alternate; two options: either does), with two options on at most 30% of posts.

**TAU = 0.25, MARGIN = 0.05** (now in `doccompass/pipeline.py`): two options on 18% of dev posts, the shown answer right on 86%, single answers right on 83%.

## Test: the result

Our 115 test posts, scored once.

| Router | Top-1 (95% CI) | Top-3 | Top-1, alternate counts | Macro-F1 | Time per post |
|---|---|---|---|---|---|
| Always "Start with a GP" | 40.9% (31.8–50.4%) | 53.0% | 88.7% | 0.048 | – |
| TF-IDF, public and ours (from scratch) | 48.7% (39.3–58.2%) | 84.3% | 80.0% | 0.428 | 0.2 ms |
| DistilRoBERTa, public then ours (fine-tuned) | 59.1% (49.6–68.2%) | 91.3% | 81.7% | 0.523 | 37 ms |
| **BiomedBERT, ours only (fine-tuned, shipped)** | **60.9% (51.3–69.8%)** | **90.4%** | **83.5%** | **0.611** | 78 ms |

Time per post is the average when scoring all 115 test posts on the laptop, in batches of 32 for the encoders. A single request in the app takes longer.

- **Both fine-tuned routers beat "always GP" on top-1**, by 18–20 points. BiomedBERT's interval is clear of the baseline's; DistilRoBERTa's just touches it; TF-IDF's overlaps it.
- **Macro-F1 separates the routers more than top-1 does**: "always GP" scores 0.048 because it never names a specialty.
- **"Always GP" wins on top-1 when the alternate counts (88.7%)**, because the AI labeller often gave "Start with a GP" as the alternate. Read that column with care.
- **Biomedical vs general encoder:** BiomedBERT (pretrained on biomedical papers) and DistilRoBERTa (general) are tied on top-1 (60.9% vs 59.1%, intervals overlap). BiomedBERT is ahead on macro-F1, but it is also twice as deep (12 layers to 6), so this is not a like-for-like test.

**Clear vs ambiguous posts (top-1):**

| Router | Clear (n = 106) | Ambiguous (n = 9) |
|---|---|---|
| TF-IDF | 48.1% | 55.6% |
| DistilRoBERTa | 60.4% | 44.4% |
| BiomedBERT | 62.3% | 44.4% |

**The two-option state on test**, with the cutoffs tuned on dev: two options on 16% of test posts; the shown answer was right on 83% of those and on 86% of single answers.

**Per label on test, BiomedBERT ours only (top-1):**

| Label | Test posts | Right |
|---|---:|---|
| Dermatology | 5 | 5 |
| Orthopedics | 9 | 8 |
| ENT | 10 | 10 |
| Gastroenterology | 11 | 8 |
| Neurology | 14 | 10 |
| Urology | 5 | 3 |
| Ob-Gyn | 6 | 5 |
| Mental health | 1 | 1 |
| Cardiology | 5 | 4 |
| Eye care | 1 | 1 |
| Dentistry | 1 | 0 |
| Start with a GP | 47 | 15 (32%) |

The router is strong on posts with a clear specialty and weak on "Start with a GP": it names a specialty for two thirds of the posts the labeller sent to a GP. For a routing tool that is the less harmful error when the specialty is plausible, and the two-option sign plus "Start with a GP is always a reasonable first step" covers part of it, but it is the main thing to improve.

## The emergency rules on our labelled posts

The 11 written rules only; the Qwen check is not run here.

| Posts | Rules fire | 95% CI |
|---|---|---|
| Not labelled Emergency (527 routable posts) | 45 (8.5%) | 6.3–11.3% |
| Labelled Emergency (54 posts) | 21 (38.9%) | 25.9–53.1% |

About 1 in 12 ordinary posts would be stopped by the rules before reaching the router, and the rules catch about 2 in 5 of the posts the labeller marked Emergency. The labeller was told to choose Emergency when unsure, and 44 of the 54 are marked ambiguous, so many of those may not be emergencies at all. This agrees with `docs/emergency-check-results.md`: the rules catch clearly stated warning signs and miss paraphrases.

## Reproduce

```bash
python scripts/merge_labels.py --from-drafts
python scripts/train_tfidf.py --stage 2
python scripts/train_encoder.py --model distilroberta --stage 2
python scripts/train_encoder.py --model distilroberta --stage 2 --from-base
python scripts/train_encoder.py --model biomedbert --stage 2
python scripts/train_encoder.py --model biomedbert --stage 2 --from-base
python scripts/evaluate_routing.py tune
python scripts/evaluate_routing.py test --tau 0.25 --margin 0.05
python scripts/evaluate_routing.py emergency
```

Stage 1 must be trained first (`scripts/train_tfidf.py`, `scripts/train_encoder.py --model …`). On a laptop with little free memory, set `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.5 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.4`.

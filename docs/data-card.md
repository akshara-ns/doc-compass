# Data card: Doc Compass routing labels

Labels saying which kind of doctor to book for 734 real patient posts, used to train and test the Doc Compass router. Draft, 8 Oct 2026.

| | |
|---|---|
| Maintained by | Akshara N.S. and Sohum Goel, CMU 24-679 Project 1 |
| What we release | Post ids and labels only, never post text |
| Posts | 734 r/AskDocs posts from `stellalisy/MediQ_AskDocs` |
| Labels | 12 router labels (11 specialties and "Start with a GP"), plus Emergency and Skip |
| How labelled | Drafted by an AI assistant from a written guideline; reviewed by authors |
| Splits | 362 train, 50 dev, 115 test; 54 Emergency and 153 Skip kept out of the router |
| Licence for our labels | CC BY-NC 4.0 (non-commercial, since the posts come from Reddit) |

## Why it exists

No public dataset pairs real, patient-written health concerns with the kind of doctor to book. Clinician notes use doctors' language, triage datasets are machine-written textbook cases, and subreddit names say where someone chose to post, not where they should book. We built this set to train and test a router that suggests a door to knock on, never a diagnosis.

## What's in the repo

| File | What it holds |
|---|---|
| `data/manual/pool.ids.csv` | The 734 posts we label: `id`, `part` (test or trainval), `annotators`, `draw` (random or targeted) |
| `data/manual/draft.labels.csv` | The AI-drafted label for every post: `id`, `primary`, `alternate`, `urgency`, `ambiguous` |
| `data/manual/gold.labels.csv` | The labels we train and test on, one per post, with `part`, `split` and `source` |
| `data/synthetic/emergency_cases.csv` | 80 short messages we wrote ourselves to test the emergency check (40 emergencies). Text included; no real person |

Post text is never committed. `scripts/prepare_data.py` downloads it from the pinned dataset revision and writes it to `data/`, which git ignores.

### Fields

| Field | Values |
|---|---|
| `primary` | One router label, or `Emergency` (a published warning sign happening now) or `Skip` (not a "which doctor" question) |
| `alternate` | Optional second router label that would also be reasonable |
| `urgency` | `routine`, `soon` or `emergency`; empty for Skip |
| `ambiguous` | `True` when the labeller couldn't really decide |
| `split` | `train`, `dev`, `test`, `emergency` or `skip` |
| `source` | `draft` for every row in this version |

The label definitions are in `docs/label-set.md`. The Emergency definition, the 22 warning signs from MedlinePlus and the CDC, is in `LABELLING.md`.

### Counts

| Label | Train | Dev | Test |
|---|---:|---:|---:|
| Start with a GP | 88 | 22 | 47 |
| ENT | 42 | 2 | 10 |
| Gastroenterology | 29 | 6 | 11 |
| Neurology | 29 | 2 | 14 |
| Eye care | 29 | 0 | 1 |
| Dermatology | 28 | 1 | 5 |
| Orthopedics | 27 | 3 | 9 |
| Ob-Gyn | 27 | 6 | 6 |
| Urology | 22 | 3 | 5 |
| Mental health | 20 | 2 | 1 |
| Cardiology | 14 | 2 | 5 |
| Dentistry | 7 | 1 | 1 |
| **Total** | **362** | **50** | **115** |

85 of the 734 posts are marked ambiguous, including 44 of the 54 Emergency posts.

## Where the data comes from

| Source | Used for | Size | Licence and terms |
|---|---|---:|---|
| `stellalisy/MediQ_AskDocs`, revision `f215fd4` | The posts we label | 10,366 unique posts (2013–2021) | MIT on the dataset card. The posts were written by Reddit users; Reddit's terms restrict training models on its content, and our instructor agreed that using this researcher-released dataset is acceptable for the course. We did not scrape Reddit. |
| Patient Comments and Specialist Types (Mendeley Data, DOI 10.17632/2twgjzpn82.2) | Stage-1 training only | 6,252 unique comments | CC BY 4.0. The comments appear to be generated rather than written by patients (emoji matched to each symptom, inserted typos), so we treat them as synthetic. |
| PMR-Reddit test pairs (`PortalPal-AI/PMR-Reddit-Test-Pairs`) | Testing the emergency check only | 362 posts | CC BY-NC 4.0. Urgency read from verified clinicians' replies. |
| Our written cases | Testing the emergency check only | 80 messages | Ours. |

## How the posts were chosen

1. Keep MediQ's real posts only (skip its `synthetic/` folder), remove repeats by post text, and keep one id per post.
2. Remove Reddit handles and links; keep posts of 25–400 words (9,118 posts).
3. **Test:** 190 posts drawn at random (seed 24679), so test scores reflect posts as they come.
4. **Train and dev:** 444 posts that a router trained on the public set rated most likely for each label (37 per label, so rare specialties get examples), plus 100 at random.
5. **Dev:** 75 of the 100 random train posts, fixed in advance, so dev has the same label mix as test. After Skip and Emergency are removed, 50 remain.

The targeted draw makes the train split richer in rare specialties than real posts are. Dev and test are random and are not affected.

## How the labels were made

Every post was labelled by an AI assistant. It worked in six batches, each given the same written guideline: the 12 labels and what each covers, the 22 emergency warning signs, when to Skip, and rules of thumb ("when unsure between doors, choose Start with a GP and mark it ambiguous; when unsure whether it's an emergency, choose Emergency").

The drafts were reviewed by the authors and used as the gold labels. Scores on this set measure agreement with these labels, not with a clinician, and there is no inter-annotator agreement score (Cohen's κ).

## Known problems and biases

- **Not clinically validated.** The labeller is not a clinician, and neither are the authors who reviewed its labels.
- **Emergency is over-labelled.** The guideline said to choose Emergency when unsure, and 44 of the 54 Emergency labels are marked ambiguous.
- **"Start with a GP" dominates** (41% of test, 44% of dev), and Dentistry, Eye care and Mental health have one test post each.
- **Who posts on r/AskDocs.** English-speaking, self-selected people who post health questions online, mostly 2013–2021. Conditions people are comfortable posting about are over-represented.
- **US-centred routing.** The labels assume US outpatient care, where patients often book specialists directly.
- **Many posts aren't routing questions.** 21% of posts (153) are Skip: medication questions, lab results, people already under a specialist.

## Privacy and ethics

- The posts are real people's health questions. They are public, but health information is sensitive, so we never redistribute the text, never quote posts verbatim in our reports (we paraphrase), and use only made-up examples in the app.
- We remove Reddit handles and links before labelling, and we share only post ids and labels.
- Don't try to identify the people who wrote these posts.
- This is a course project meant to teach methods, not a research study. Anyone building on it for research or publication should seek ethics review first.

## Intended use

- **For:** training and testing the Doc Compass router in CMU 24-679, and comparing routing models on patient-written text.
- **Not for:** diagnosis, clinical triage or emergency detection; any decision about a real person's care; commercial use (the posts come from Reddit, and the emergency test set is non-commercial).

## Reproduce

```bash
python scripts/prepare_data.py                 # downloads the posts, builds data/manual/pool.csv
python scripts/merge_labels.py --from-drafts   # writes data/manual/gold.labels.csv
```

The pool itself came from `python scripts/select_pool.py` (seed 24679) and does not need to be rebuilt.

## Versions

| Date | Change |
|---|---|
| 8 Oct 2026 | First version: 734 posts, reviewed AI-drafted labels used |

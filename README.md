# Doc Compass

*Which doctor do I book?*

Describe a health concern in plain language. The app checks for emergency symptoms and suggests which kind of doctor to book (top 3, with "Start with a GP" always an option). It routes; it does not diagnose.

CMU 24-679 Project 1

## User flow

```mermaid
flowchart LR
    A([Student types a concern<br/>in plain language]) --> B{Written<br/>emergency rules}
    B -- rule fires --> E[["Seek emergency care now"]]
    B -- no rule fires --> Q{Language-model<br/>emergency check}
    Q -- flags it --> E
    Q -- clear --> F[Top-3 specialties<br/>with confidence]
    F -- unsure --> U[Two options shown,<br/>student decides]
    F --> G[Short reason +<br/>questions to bring]
    U --> G
    G --> H([Student books a visit<br/>outside the app])
    classDef stop fill:#fbe9e6,stroke:#c0392b,color:#c0392b
    class E stop
```

"Start with a GP" is always one of the options shown. Nothing the student types is stored.

## Results so far

**Routers, stage 1.** Trained on the public Patient Comments set and scored on the same 938 held-out comments from it. The three are tied, and this is an easy score because the comments are short and alike. Stage 2 (training on our own labelled posts) and the test on our own posts are still to come.

| Router | Type | Top-1 (95% CI) | Top-3 | Macro-F1 |
|---|---|---|---|---|
| TF-IDF + logistic regression | from scratch | 94.0% (92.3–95.5) | 98.6% | 0.902 |
| DistilRoBERTa | fine-tuned | 94.3% (92.7–95.7) | 99.0% | 0.908 |
| BiomedBERT | fine-tuned | 94.2% (92.6–95.6) | 98.8% | 0.904 |

**Emergency check.** Two layers since 5 Oct: the written rules, then a Qwen check for wording the rules miss. A missed emergency is the costly error, so it is reported first.

| Tested on | Option | Missed emergencies | False alarms |
|---|---|---|---|
| 362 real posts with clinician-derived urgency, 38 emergencies | Rules alone | 26 of 38 (68%) | 33 of 293 (11%) |
| | **Rules plus Qwen (the app)** | **13 of 38 (34%)** | **58 of 293 (20%)** |
| 80 short cases we wrote, 40 emergencies | Rules alone | 25 of 40 (62%) | 4 of 40 (10%) |
| | **Rules plus Qwen (the app)** | **1 of 40 (2%)** | **4 of 40 (10%)** |

The check catches clearly stated warning signs; it does not detect emergencies. Full tables, the datasets and classifiers we tried, and why this is hard: [docs/emergency-check-results.md](docs/emergency-check-results.md).

**Explanation.** On 16 test inputs, Qwen wrote 15 explanations that passed every check; the other fell back to fixed wording.

## Set up

Needs Python 3.11 or newer.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/prepare_data.py     # downloads both datasets and builds the local files
python scripts/train_tfidf.py      # trains the from-scratch router on the public set
python scripts/train_encoder.py --model distilroberta   # fine-tuned router, a few minutes on a laptop
python scripts/train_encoder.py --model biomedbert
pytest                             # checks the rules, the scrub and the pipeline
python scripts/check_emergency.py --llm --real   # missed emergencies and false alarms for the emergency check
```

## Run

```bash
python -m doccompass.app                    # the app, at http://127.0.0.1:7860
python -m doccompass.app --llm              # the same, with Qwen writing the explanation (about 3 GB the first time)
python tools/annotate.py --annotator NAME   # the labelling tool (NAME is sohum or akshara)
```

The labelling tool shows one post at a time and saves to `data/manual/NAME.labels.csv`. That file holds ids and labels only, so commit and push it when you stop. You can close the tool at any time; it resumes at your next unlabelled post.

## How it works

1. **Emergency check**: 11 written rules, each citing a published warning sign (MedlinePlus, CDC). If none fires and Qwen is loaded, Qwen is shown the full published list and asked whether the message describes any of those signs happening now. Either one firing goes straight to "Seek emergency care now"
2. **Scrub**: simple rules remove handles, emails, phone numbers and links
3. **Route**: TF-IDF + logistic regression, and fine-tuned DistilRoBERTa vs BiomedBERT. When the router is unsure it shows two options instead of one
4. **Explain**: Qwen2.5-1.5B-Instruct writes a one-sentence reason and three questions, from the concern and the routing result only. Its text is checked before it is shown, and fixed wording is the fallback

## Demo notebook

`notebooks/doc_compass_app.ipynb` runs the app in Colab and prints a public link with a QR code. It downloads the code and models from a public Hugging Face repo, which `python scripts/publish_bundle.py` uploads (run `hf auth login` first).

Use a T4 GPU runtime: without a GPU, Qwen isn't loaded, so only the written rules check for emergencies and the explanation uses fixed wording. The notebook is pinned to one version of the app, so after the app changes, upload the notebook again, restart the runtime and run all cells. The public link and QR code are new on every run.

| Path | What it holds |
|---|---|
| `doccompass/` | the package: labels, data loading, rules, routers, pipeline, app |
| `scripts/` | data prep, pool selection, training, publishing the app bundle |
| `notebooks/` | the Colab demo notebook |
| `tools/annotate.py` | the labelling tool |
| `tests/` | pytest checks |
| `docs/label-set.md` | the label set and the public-data mapping |
| `LABELLING.md` | who labels which posts, and how |
| `docs/emergency-check-results.md` | missed emergencies and false alarms for the emergency check |
| `doc-compass-plan.md` | the full plan |
| `docs/checkin/` | system figures |

## Data rules

- Never commit post text. Labelled data is shared as labels + MediQ ids only.
- Public and synthetic data are kept apart from our manual labels.
- Keep API keys and tokens out of the repo.

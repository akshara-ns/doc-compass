# Doc Compass

*Which doctor do I book?*

Describe a health concern in plain language. The app checks for emergency symptoms and suggests which kind of doctor to book (top 3, with "Start with a GP" always an option). It routes; it does not diagnose.

CMU 24-679 Project 1

## User flow

```mermaid
flowchart LR
    A([Student types a concern<br/>in plain language]) --> B{Red-flag<br/>rules}
    B -- emergency --> E[["Seek emergency care now"]]
    B -- no flag --> F[Top-3 specialties<br/>with confidence]
    F -- unsure --> U[Two options shown,<br/>student decides]
    F --> G[Short reason +<br/>questions to bring]
    U --> G
    G --> H([Student books a visit<br/>outside the app])
    classDef stop fill:#fbe9e6,stroke:#c0392b,color:#c0392b
    class E stop
```

"Start with a GP" is always one of the options shown. Nothing the student types is stored.

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
```

## Run

```bash
python -m doccompass.app                    # the app, at http://127.0.0.1:7860
python -m doccompass.app --llm              # the same, with Qwen writing the explanation (about 3 GB the first time)
python tools/annotate.py --annotator NAME   # the labelling tool (NAME is sohum or akshara)
```

The labelling tool shows one post at a time and saves to `data/manual/NAME.labels.csv`. That file holds ids and labels only, so commit and push it when you stop. You can close the tool at any time; it resumes at your next unlabelled post.

## How it works

1. **Red-flag check**: written rules, each citing a published warning sign; emergencies go straight to "Seek emergency care now"
2. **Scrub**: simple rules remove handles, emails, phone numbers and links
3. **Route**: TF-IDF + logistic regression, and fine-tuned DistilRoBERTa vs BiomedBERT. When the router is unsure it shows two options instead of one
4. **Explain**: Qwen2.5-1.5B-Instruct writes a one-sentence reason and three questions, from the concern and the routing result only. Its text is checked before it is shown, and fixed wording is the fallback

## Demo notebook

`notebooks/doc_compass_app.ipynb` runs the app in Colab and prints a public link with a QR code. It downloads the code and models from a public Hugging Face repo, which `python scripts/publish_bundle.py` uploads (run `hf auth login` first).

| Path | What it holds |
|---|---|
| `doccompass/` | the package: labels, data loading, rules, routers, pipeline, app |
| `scripts/` | data prep, pool selection, training, publishing the app bundle |
| `notebooks/` | the Colab demo notebook |
| `tools/annotate.py` | the labelling tool |
| `tests/` | pytest checks |
| `docs/label-set.md` | the label set and the public-data mapping |
| `which-doctor-do-i-book.md` | the full plan |
| `docs/checkin/` | system figures |

## Data rules

- Never commit post text. Labelled data is shared as labels + MediQ ids only.
- Public and synthetic data are kept apart from our manual labels.
- Keep API keys and tokens out of the repo.

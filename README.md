# Doc Compass

*Which doctor do I book?*

Describe a health concern in plain language. The app checks for emergency symptoms and suggests which kind of doctor to book: the top 3, with "Start with a GP" always an option. It routes; it does not diagnose. Nothing you type is stored.

CMU 24-679 Project 1

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

## How it works

1. **Emergency check:** 11 written rules, each citing a published warning sign (MedlinePlus, CDC), then a Qwen check for wording the rules miss. Either one firing shows "Seek emergency care now".
2. **Scrub:** removes handles, emails, phone numbers and links.
3. **Route:** BiomedBERT fine-tuned on our labelled posts; when it is unsure it shows two options.
4. **Explain:** Qwen2.5-1.5B-Instruct writes a one-sentence reason and three questions to bring. Its text is checked, and fixed wording is the fallback.

## Results

On 115 of our own test posts, scored once. Labels were drafted by an AI assistant and reviewed by the authors.

| Router | Type | Top-1 (95% CI) | Top-3 | Macro-F1 |
|---|---|---|---|---|
| Always "Start with a GP" | baseline | 40.9% (31.8–50.4) | – | 0.048 |
| TF-IDF + logistic regression | from scratch | 48.7% (39.3–58.2) | 84.3% | 0.428 |
| DistilRoBERTa | fine-tuned | 59.1% (49.6–68.2) | 91.3% | 0.523 |
| **BiomedBERT (shipped)** | fine-tuned | **60.9% (51.3–69.8)** | **90.4%** | **0.611** |

The emergency check (rules plus Qwen) misses 13 of 38 emergencies in real posts and flags 20% of ordinary ones: it catches clearly stated warning signs, it does not detect emergencies.


**Models and data:** router and app code at [`akshara-ns/doc-compass`](https://huggingface.co/akshara-ns/doc-compass) · labels (ids only), splits and EDA at [`akshara-ns/doc-compass-labels`](https://huggingface.co/datasets/akshara-ns/doc-compass-labels)

## To run the app

The app runs in Google Colab; there is no permanent hosted link, because Gradio Spaces on Hugging Face need a paid plan. Nothing to install, and nothing you type is stored.

1. Open [`notebooks/doc_compass_app.ipynb`](notebooks/doc_compass_app.ipynb) in [Google Colab](https://colab.research.google.com): download the file, then in Colab choose **File → Upload notebook**.
2. Choose **Runtime → Change runtime type → T4 GPU**, then **Save**. Without a GPU the app still works, but the language model isn't loaded: emergencies are checked by the written rules only, and explanations use fixed wording.
3. Choose **Runtime → Run all**. The first run takes a few minutes: it downloads the app and routers from [`akshara-ns/doc-compass`](https://huggingface.co/akshara-ns/doc-compass) and the language model (about 3 GB).
4. The last cell opens the app inside the notebook and prints a public link and QR code. The link works while the notebook is running and is new on every run.
5. Try the made-up examples under the text box, or your own wording. For example:
   - an itchy rash → a blue sign, Dermatology
   - "my gums bleed when I brush my teeth" → an amber sign with two options, because the router is unsure
   - sudden crushing chest pain → a red "Seek emergency care now" sign, and the router doesn't run

To stop the app, run `import gradio; gradio.close_all()` or disconnect the runtime.

## Run it locally

Needs Python 3.11 or newer.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/prepare_data.py     # downloads the posts; text stays local
python -m doccompass.app --llm     # the app at http://127.0.0.1:7860, with Qwen (about 3 GB the first time)
pytest
```

The routers must be trained first; the commands are in [docs/routing-results.md](docs/routing-results.md#reproduce).

## Repo

| Path | What it holds |
|---|---|
| `doccompass/` | the app: rules, routers, pipeline, Gradio interface |
| `scripts/` | data prep, training, evaluation, publishing |
| `tools/annotate.py` | the labelling tool (see `docs/labelling.md`) |
| `docs/` | detailed documentation (see below) |

## Documentation

The `docs/` folder holds the detail behind this README:

- [`data-card.md`](docs/data-card.md): where the posts come from, how they were chosen and labelled, licences, known problems and privacy
- [`label-set.md`](docs/label-set.md): the 12 labels and how the public data maps onto them
- [`labelling.md`](docs/labelling.md): the labelling process and the 22 emergency warning signs
- [`routing-results.md`](docs/routing-results.md): every router on dev and test, the cutoff tuning and per-label scores
- [`emergency-check-results.md`](docs/emergency-check-results.md): the emergency check's misses and false alarms on real and written cases
- [`plan.md`](docs/plan.md): the project plan and decisions
- [`system-figure.png`](docs/system-figure.png): the whole system in one figure

## Data rules

- Never commit post text: labelled data is shared as post ids and labels only.
- Keep public and synthetic data apart from our labels.
- Keep API keys and tokens out of the repo.

## How we used AI tools

- **Claude Code** helped check the plan against the real datasets, write and debug the code, build the slides and figures, and draft the docs. **Gemini** was used early on to brainstorm.
- **Labels:** an AI assistant drafted the labels from our written guideline, and the authors reviewed them.
- **Checks:** every number in the docs comes from a run of the scripts in this repo, and the core app logic (rules, pipeline, label merging) is covered by tests (`pytest`).
- **In the app itself**, Qwen2.5-1.5B-Instruct writes the explanations and double-checks for emergencies; it never chooses the doctor.

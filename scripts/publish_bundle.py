"""Upload the app bundle to a public Hugging Face model repo, so the Colab notebook can run it.

The bundle is the doccompass package plus the trained routers. No post text is included.
Log in first with:  hf auth login      Then run:  python scripts/publish_bundle.py
"""

import json
import sys
from pathlib import Path

from huggingface_hub import HfApi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass import paths
from doccompass.labels import LABELS

ENCODER = "biomedbert_gold"  # best on our dev posts (docs/routing-results.md)
FILES = ["doccompass/*.py", f"checkpoints/{ENCODER}/*", "checkpoints/tfidf_stage2.joblib", "requirements.txt"]
SKIP = ["**/__pycache__/**", "**/training_args.bin"]

# Scored once on our 115 test posts on 8 Oct (scripts/evaluate_routing.py test --tau 0.25 --margin 0.05).
TEST = {"n": 115, "top1": 0.609, "top1_ci": (0.513, 0.698), "top3": 0.904, "macro_f1": 0.611,
        "always_gp_top1": 0.409, "tfidf_top1": 0.487}


def model_card(repo_id: str) -> str:
    metrics = json.loads((paths.MODELS / ENCODER / "metrics.json").read_text())
    dev = metrics["dev"]
    low, high = TEST["top1_ci"]
    return f"""---
license: apache-2.0
language: en
library_name: transformers
pipeline_tag: text-classification
base_model: {metrics['model']['repo']}
---

# Doc Compass

Routes a plain-language health concern to a kind of doctor to book. It suggests a door to
knock on; it does not diagnose and is not medical advice.

This repo holds the app code (`doccompass/`) and its routers, so the demo notebook can run
without access to the project's GitHub repo.

## What is here

| File | What it is |
|---|---|
| `checkpoints/{ENCODER}/` | `{metrics['model']['repo']}` fine-tuned (all weights) to route concerns to {len(LABELS)} labels |
| `checkpoints/tfidf_stage2.joblib` | TF-IDF + logistic regression router, trained from scratch; the fallback when PyTorch isn't available |
| `doccompass/` | emergency rules, routers, explanation and the Gradio app |

Labels: {", ".join(LABELS)}.

## Training data

{metrics['train_rows']} real r/AskDocs posts from `stellalisy/MediQ_AskDocs` (MIT on the dataset card; the posts
come from Reddit), each labelled with the kind of doctor to book. The labels were drafted by an AI
assistant from a written guideline and reviewed by the authors. No post text is in this repo.

The TF-IDF router was trained on the same posts plus *Patient Comments and Specialist Types*
(Mendeley Data, DOI 10.17632/2twgjzpn82.2, CC BY 4.0), a public set of short comments that
appear to be generated, with its symptom categories remapped to the labels above.

## Results

On {dev['n']} dev posts the router scores {dev['top1']:.1%} top-1 and {dev['macro_f1']:.3f} macro-F1; that is
where it was chosen. On {TEST['n']} test posts, scored once, it scores {TEST['top1']:.1%} top-1
(95% CI {low:.1%}–{high:.1%}), {TEST['top3']:.1%} top-3 and {TEST['macro_f1']:.3f} macro-F1, against {TEST['always_gp_top1']:.1%}
for always answering "Start with a GP" and {TEST['tfidf_top1']:.1%} for the TF-IDF router. The test labels are
the same labels, so this measures agreement with them, not with a clinician.

## Limits

- English only, and trained on {metrics['train_rows']} posts, so some labels have few examples (Dentistry has 7).
- It often names a specialty where the labeller said "Start with a GP" (right on 15 of 47 such test posts).
- Short or vague messages get low confidence; the app then shows two options instead of one.
- The emergency check is a short list of written rules, plus a language-model check when one is
  loaded. It will miss emergencies phrased in ways it doesn't anticipate. In an emergency call 911.
- Not clinically validated.
"""


def main() -> None:
    api = HfApi()
    repo_id = f"{api.whoami()['name']}/doc-compass"
    api.create_repo(repo_id, repo_type="model", private=False, exist_ok=True)
    api.upload_folder(folder_path=str(paths.ROOT), repo_id=repo_id, allow_patterns=FILES, ignore_patterns=SKIP,
                      commit_message="Upload the Doc Compass app bundle")
    commit = api.upload_file(path_or_fileobj=model_card(repo_id).encode(), path_in_repo="README.md", repo_id=repo_id,
                             commit_message="Add the model card")
    print(f"Published https://huggingface.co/{repo_id}")
    print(f"Revision to pin in the notebook: {commit.oid}")


if __name__ == "__main__":
    main()

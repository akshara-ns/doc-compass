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

ENCODER = "distilroberta_stage1"
FILES = ["doccompass/*.py", f"checkpoints/{ENCODER}/*", "checkpoints/tfidf_stage1.joblib", "requirements.txt"]
SKIP = ["**/__pycache__/**", "**/training_args.bin"]


def model_card(repo_id: str) -> str:
    metrics = json.loads((paths.MODELS / ENCODER / "metrics.json").read_text())
    held = metrics["held_out"]
    low, high = held["top1_ci"]
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
| `checkpoints/tfidf_stage1.joblib` | TF-IDF + logistic regression router, trained from scratch on the same data |
| `doccompass/` | emergency rules, routers, explanation and the Gradio app |

Labels: {", ".join(LABELS)}.

## Training data

Stage 1 only: 6,252 unique comments from *Patient Comments and Specialist Types*
(Mendeley Data, DOI 10.17632/2twgjzpn82.2, CC BY 4.0), with its 68 symptom categories
remapped to the labels above. These are short, one-sentence comments.

## Results

On {held['n']} held-out comments from that same public set, the fine-tuned router scores
{held['top1']:.1%} top-1 (95% CI {low:.1%}–{high:.1%}), {held['top3']:.1%} top-3 and
{held['macro_f1']:.3f} macro-F1. This says how well it fits the public data, not how it
does on longer real-world posts.

## Limits

- English only, and trained on short comments. It can be confidently wrong on wording the
  public set doesn't cover: "my gums bleed when I brush" is routed to Ob-Gyn.
- The emergency check is a short list of written rules and will miss emergencies phrased
  in ways the rules don't anticipate. In an emergency call 911.
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

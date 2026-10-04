"""Train the from-scratch router (TF-IDF + logistic regression) and save it.

Stage 1 uses the public Patient Comments set only. A held-out share of that set gives a
first score; it says how well the router fits the public data, not our own posts.

Run:  python scripts/train_tfidf.py
"""

import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass import paths
from doccompass.labels import LABEL2ID, LABELS
from doccompass.metrics import describe, score
from doccompass.router import TfidfRouter

SEED = 24679


def main() -> None:
    comments = pd.read_csv(paths.PATIENT_COMMENTS)
    train, held_out = train_test_split(comments, test_size=0.15, stratify=comments["label"], random_state=SEED)

    router = TfidfRouter().fit(train["text"], train["label"])
    held_ids = held_out["label"].map(LABEL2ID).to_numpy()
    proba = router.predict_proba(held_out["text"])
    print(describe("Public held-out", score(proba, held_ids)))

    majority = train["label"].mode()[0]
    print(f"Always '{majority}': top-1 {(held_out['label'] == majority).mean():.1%}")
    per_label = pd.DataFrame({"label": held_out["label"], "correct": proba.argmax(axis=1) == held_ids})
    print(per_label.groupby("label")["correct"].agg(["size", "mean"]).reindex(LABELS).round(2).to_string())

    # The saved model uses every public comment.
    TfidfRouter().fit(comments["text"], comments["label"]).save(paths.MODELS / "tfidf_stage1.joblib")
    print("Saved checkpoints/tfidf_stage1.joblib")


if __name__ == "__main__":
    main()

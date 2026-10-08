"""Train the from-scratch router (TF-IDF + logistic regression) and save it.

Stage 1 uses the public Patient Comments set only. A held-out share of that set gives a
first score; it says how well the router fits the public data, not our own posts.
Stage 2 trains on our gold training posts alone, and on them plus the public set, and scores
both on our dev posts. Our test posts are never used here.

Run:  python scripts/train_tfidf.py
      python scripts/train_tfidf.py --stage 2
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass import paths
from doccompass.labels import LABEL2ID, LABELS
from doccompass.metrics import describe, score
from doccompass.router import TfidfRouter
from doccompass.splits import gold_split, public_split


def stage1() -> None:
    train_part, val_part, held_out = public_split()
    train = pd.concat([train_part, val_part])  # nothing to tune here, so val is training data too

    router = TfidfRouter().fit(train["text"], train["label"])
    held_ids = held_out["label"].map(LABEL2ID).to_numpy()
    proba = router.predict_proba(held_out["text"])
    print(describe("Public held-out", score(proba, held_ids)))

    majority = train["label"].mode()[0]
    print(f"Always '{majority}': top-1 {(held_out['label'] == majority).mean():.1%}")
    per_label = pd.DataFrame({"label": held_out["label"], "correct": proba.argmax(axis=1) == held_ids})
    print(per_label.groupby("label")["correct"].agg(["size", "mean"]).reindex(LABELS).round(2).to_string())

    # The saved model uses every public comment.
    comments = pd.concat([train, held_out])
    TfidfRouter().fit(comments["text"], comments["label"]).save(paths.MODELS / "tfidf_stage1.joblib")
    print("Saved checkpoints/tfidf_stage1.joblib")


def stage2() -> None:
    gold = gold_split()
    train, dev = gold["train"], gold["dev"]
    public = pd.concat(public_split())
    dev_ids = dev["label"].map(LABEL2ID).to_numpy()
    for name, texts, labels in [("tfidf_gold", train["text"], train["label"]),
                                ("tfidf_stage2", pd.concat([train["text"], public["text"]]), pd.concat([train["label"], public["label"]]))]:
        router = TfidfRouter().fit(texts, labels)
        print(describe(f"{name}, our dev posts", score(router.predict_proba(dev["text"]), dev_ids)))
        router.save(paths.MODELS / f"{name}.joblib")
        print(f"Saved checkpoints/{name}.joblib")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stage", type=int, choices=(1, 2), default=1)
    if parser.parse_args().stage == 1:
        stage1()
    else:
        stage2()


if __name__ == "__main__":
    main()

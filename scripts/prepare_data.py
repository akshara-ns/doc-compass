"""Download the two datasets and build the local data files.

Run once after cloning:  python scripts/prepare_data.py
Post text is written under data/, which git ignores.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass import paths
from doccompass.mediq import load_mediq_posts
from doccompass.patient_comments import load_patient_comments


def main() -> None:
    paths.PUBLIC.mkdir(parents=True, exist_ok=True)
    paths.MANUAL.mkdir(parents=True, exist_ok=True)

    posts = load_mediq_posts()
    posts.to_csv(paths.MEDIQ_POSTS, index=False)
    print(f"MediQ_AskDocs: {len(posts):,} unique posts -> {paths.MEDIQ_POSTS.relative_to(paths.ROOT)}")

    comments = load_patient_comments()
    comments.to_csv(paths.PATIENT_COMMENTS, index=False)
    print(f"Patient Comments: {len(comments):,} unique comments -> {paths.PATIENT_COMMENTS.relative_to(paths.ROOT)}")
    print(comments["label"].value_counts().to_string())

    if paths.POOL_IDS.exists():  # attach text to the posts chosen for labelling
        pool = pd.read_csv(paths.POOL_IDS).merge(posts, on="id", how="left", validate="one_to_one")
        if pool["text"].isna().any():
            raise ValueError("Some pool ids are missing from MediQ_AskDocs; check the pinned revision.")
        pool.to_csv(paths.POOL, index=False)
        print(f"Labelling pool: {len(pool):,} posts -> {paths.POOL.relative_to(paths.ROOT)}")


if __name__ == "__main__":
    main()

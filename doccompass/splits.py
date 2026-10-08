"""Fixed splits, so every router is trained and scored on the same rows."""

import pandas as pd
from sklearn.model_selection import train_test_split

from .paths import GOLD, PATIENT_COMMENTS, POOL

SEED = 24679


def public_split() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Patient Comments as (train, val, held_out): about 76.5% / 8.5% / 15%, stratified by label.

    val picks the best epoch when fine-tuning; held_out is only ever scored.
    """
    comments = pd.read_csv(PATIENT_COMMENTS)
    rest, held_out = train_test_split(comments, test_size=0.15, stratify=comments["label"], random_state=SEED)
    train, val = train_test_split(rest, test_size=0.10, stratify=rest["label"], random_state=SEED)
    return train, val, held_out


def gold_split() -> dict[str, pd.DataFrame]:
    """Our labelled posts as {"train", "dev", "test", "emergency"}, each with text and labels.

    Built from data/manual/gold.labels.csv (scripts/merge_labels.py) and the local post text.
    Skip posts are left out; Emergency posts are kept apart to test the emergency check.
    """
    gold = pd.read_csv(GOLD, dtype=str).fillna("")
    text = pd.read_csv(POOL, usecols=["id", "text"], dtype=str)
    gold = gold.merge(text, on="id", how="left", validate="one_to_one").rename(columns={"primary": "label"})
    if gold["text"].isna().any():
        raise ValueError("Some labelled posts have no text; run scripts/prepare_data.py first.")
    return {split: gold[gold["split"] == split].reset_index(drop=True) for split in ("train", "dev", "test", "emergency")}

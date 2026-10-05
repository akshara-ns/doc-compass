"""Fixed splits, so every router is trained and scored on the same rows."""

import pandas as pd
from sklearn.model_selection import train_test_split

from .paths import PATIENT_COMMENTS

SEED = 24679


def public_split() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Patient Comments as (train, val, held_out): about 76.5% / 8.5% / 15%, stratified by label.

    val picks the best epoch when fine-tuning; held_out is only ever scored.
    """
    comments = pd.read_csv(PATIENT_COMMENTS)
    rest, held_out = train_test_split(comments, test_size=0.15, stratify=comments["label"], random_state=SEED)
    train, val = train_test_split(rest, test_size=0.10, stratify=rest["label"], random_state=SEED)
    return train, val, held_out

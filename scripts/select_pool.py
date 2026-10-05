"""Choose which posts we label and who labels them. Run once; the result is committed.

Writes data/manual/pool.ids.csv (ids only). Everyone else gets the same posts by running
scripts/prepare_data.py, which attaches the text.

- test: a plain random sample, so test scores reflect the posts as they come.
- trainval: mostly posts a quick router rates as likely for each label ("targeted"), so
  that rare specialties get enough examples, plus a "random" share.

The draw column records which is which. The dev split is taken from the random trainval
posts only, so the cutoffs tuned on dev see the same label mix as the test set.
"""

import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass import paths
from doccompass.labels import LABELS
from doccompass.router import TfidfRouter

SEED = 24679
ANNOTATORS = ("sohum", "akshara")
MIN_WORDS, MAX_WORDS = 25, 400
# About 1 in 6 posts is not a "which doctor" question, so we draw more than we need.
N_TEST, N_TEST_SHARED = 190, 60  # aiming for 150 usable; the first 60 are labelled by both of us
N_PER_LABEL, N_RANDOM = 37, 100  # trainval: 12 x 37 targeted + 100 random, aiming for 450 usable


def main() -> None:
    posts = pd.read_csv(paths.MEDIQ_POSTS)
    words = posts["text"].str.split().str.len()
    posts = posts[words.between(MIN_WORDS, MAX_WORDS)].reset_index(drop=True)

    rng = random.Random(SEED)
    order = list(range(len(posts)))
    rng.shuffle(order)
    test, rest = order[:N_TEST], order[N_TEST:]

    comments = pd.read_csv(paths.PATIENT_COMMENTS)
    router = TfidfRouter().fit(comments["text"], comments["label"])
    proba = router.predict_proba(posts["text"].iloc[rest])

    # Take turns across labels, each taking the post it rates highest among those still free.
    picked: list[tuple[int, str]] = []
    taken: set[int] = set()
    ranked = np.argsort(-proba, axis=0)
    cursor = [0] * len(LABELS)
    for _ in range(N_PER_LABEL):
        for label in range(len(LABELS)):
            while ranked[cursor[label], label] in taken:
                cursor[label] += 1
            choice = int(ranked[cursor[label], label])
            taken.add(choice)
            picked.append((rest[choice], "targeted"))
    free = [rest[i] for i in range(len(rest)) if i not in taken]
    trainval = picked + [(index, "random") for index in rng.sample(free, N_RANDOM)]
    rng.shuffle(trainval)

    rows = []
    for position, index in enumerate(test):
        who = "+".join(ANNOTATORS) if position < N_TEST_SHARED else ANNOTATORS[position % 2]
        rows.append((posts["id"][index], "test", who, "random"))
    for position, (index, draw) in enumerate(trainval):
        rows.append((posts["id"][index], "trainval", ANNOTATORS[position % 2], draw))

    pool = pd.DataFrame(rows, columns=["id", "part", "annotators", "draw"])
    assert pool["id"].is_unique
    paths.POOL_IDS.parent.mkdir(parents=True, exist_ok=True)
    pool.to_csv(paths.POOL_IDS, index=False)
    print(f"{len(posts):,} posts of {MIN_WORDS}-{MAX_WORDS} words; chose {len(pool)}:")
    print(pool.groupby(["part", "draw", "annotators"]).size().to_string())


if __name__ == "__main__":
    main()

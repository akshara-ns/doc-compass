"""Checks on merging two label files into gold labels. Run: pytest"""

import pandas as pd

from doccompass.gold import DEV_DRAW, agreement, dev_candidates, merge
from doccompass.labels import GP


def frame(rows):
    columns = ["id", "primary", "alternate", "urgency", "ambiguous", "draft_primary", "changed_from_draft"]
    return pd.DataFrame([dict(zip(columns, row)) for row in rows], columns=columns).fillna("").set_index("id")


POOL = pd.DataFrame([
    ("s1", "test", "akshara+sohum", "random"),
    ("s2", "test", "akshara+sohum", "random"),
    ("s3", "test", "akshara+sohum", "random"),
    ("a1", "test", "akshara", "random"),
    ("t1", "trainval", "sohum", "targeted"),
    ("t2", "trainval", "sohum", "targeted"),
], columns=["id", "part", "annotators", "draw"])

AKSHARA = frame([
    ("s1", "Dermatology", "", "routine", "False", "", ""),
    ("s2", "ENT", GP, "soon", "False", "", ""),
    ("s3", "Skip", "", "", "False", "", ""),
    ("a1", "Emergency", "", "emergency", "False", "", ""),
])
SOHUM = frame([
    ("s1", "Dermatology", "", "soon", "True", "", ""),
    ("s2", GP, "", "routine", "False", "", ""),
    ("s3", "Skip", "", "", "False", "", ""),
    ("t1", "Urology", "", "routine", "False", "Urology", "False"),
    ("t2", "Neurology", "", "routine", "False", "Orthopedics", "True"),
])


def test_agreement_counts_alternates_as_lenient_matches():
    result = agreement(AKSHARA, SOHUM)
    assert result["n"] == 3
    assert round(result["exact"], 2) == 0.67  # s1 and s3 match, s2 doesn't
    assert result["lenient"] == 1.0  # Sohum's GP is Akshara's alternate on s2
    assert result["disagreements"] == [("s2", "ENT", GP)]


def test_merge_keeps_agreements_and_holds_back_disagreements():
    gold, unresolved = merge(POOL, {"akshara": AKSHARA, "sohum": SOHUM}, pd.DataFrame())
    by_id = gold.set_index("id")
    assert list(unresolved["id"]) == ["s2"] and "s2" not in by_id.index
    assert by_id.loc["s1", "split"] == "test" and by_id.loc["s1", "source"] == "agreed"
    assert by_id.loc["s1", "urgency"] == "soon" and by_id.loc["s1", "ambiguous"] == "True"  # the more cautious of the two
    assert by_id.loc["s3", "split"] == "skip" and by_id.loc["a1", "split"] == "emergency"
    assert by_id.loc["t2", "changed_from_draft"] == "True" and by_id.loc["t1", "changed_from_draft"] == "False"


def test_adjudicated_label_resolves_a_disagreement():
    agreed = frame([("s2", GP, "ENT", "routine", "True", "", "")])
    gold, unresolved = merge(POOL, {"akshara": AKSHARA, "sohum": SOHUM}, agreed)
    row = gold.set_index("id").loc["s2"]
    assert unresolved.empty and row["primary"] == GP and row["source"] == "adjudicated"


def test_shared_post_waits_for_both_labels():
    gold, _ = merge(POOL, {"akshara": AKSHARA}, pd.DataFrame())
    assert not set(gold["id"]) & {"s1", "s2", "s3"}


def test_dev_comes_from_random_train_posts_only_and_is_fixed():
    pool = pd.DataFrame({"id": [f"p{i}" for i in range(200)], "part": "trainval", "annotators": "sohum",
                         "draw": ["random" if i % 2 else "targeted" for i in range(200)]})
    dev = dev_candidates(pool)
    assert len(dev) == DEV_DRAW
    assert set(pool[pool["id"].isin(dev)]["draw"]) == {"random"}
    assert dev == dev_candidates(pool.sample(frac=1, random_state=1))  # order of the pool doesn't matter

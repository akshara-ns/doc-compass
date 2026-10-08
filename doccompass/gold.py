"""Turn our two label files into one gold label per post, with its split.

The 60 test posts we both label give Cohen's κ. Where we agree, that label stands; where we
disagree, the post waits for the label we agree on in data/manual/adjudicated.labels.csv.
"""

import hashlib

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from .labels import EMERGENCY, SKIP, URGENCY

DEV_DRAW = 60  # random train posts set aside as dev candidates; about 50 survive the skips


def annotators(pool: pd.DataFrame) -> list[str]:
    return sorted(set("+".join(pool["annotators"]).split("+")))


def _rank(post_id: str) -> str:
    """A fixed order that doesn't depend on how far labelling has got."""
    return hashlib.sha256(post_id.encode()).hexdigest()


def dev_candidates(pool: pd.DataFrame) -> set[str]:
    """The dev posts: the first DEV_DRAW random train posts in a fixed order.

    Taken from the random draw only, so cutoffs tuned on dev see the same label mix as test.
    """
    random_train = pool[(pool["part"] == "trainval") & (pool["draw"] == "random")]["id"]
    return set(sorted(random_train, key=_rank)[:DEV_DRAW])


def agreement(first: pd.DataFrame, second: pd.DataFrame) -> dict:
    """Agreement on the primary label for posts both of us labelled. Frames are indexed by id."""
    shared = first.index.intersection(second.index)
    a, b = first.loc[shared], second.loc[shared]
    exact = a["primary"] == b["primary"]
    lenient = exact | (a["primary"] == b["alternate"]) | (b["primary"] == a["alternate"])
    result = {"n": len(shared), "exact": float(exact.mean()) if len(shared) else float("nan"),
              "lenient": float(lenient.mean()) if len(shared) else float("nan"), "kappa": float("nan"),
              "disagreements": list(zip(shared[~exact], a["primary"][~exact], b["primary"][~exact]))}
    if len(shared) >= 2 and len(set(a["primary"]) | set(b["primary"])) > 1:
        result["kappa"] = float(cohen_kappa_score(a["primary"], b["primary"]))
    return result


def _combine(rows: list[pd.Series]) -> dict:
    """Two agreeing labels as one: keep any alternate, the more urgent tier, and any ambiguous tick."""
    primary = rows[0]["primary"]
    alternate = next((r["alternate"] for r in rows if r["alternate"] and r["alternate"] != primary), "")
    tiers = [r["urgency"] for r in rows if r["urgency"] in URGENCY]
    return {"primary": primary, "alternate": alternate,
            "urgency": max(tiers, key=URGENCY.index) if tiers else "",
            "ambiguous": str(any(r["ambiguous"] == "True" for r in rows))}


def merge(pool: pd.DataFrame, labels: dict[str, pd.DataFrame], adjudicated: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (gold, unresolved).

    gold has one row per labelled post: id, split, primary, alternate, urgency, ambiguous,
    source, changed_from_draft. split is test, dev or train for router labels, and emergency or
    skip otherwise. unresolved lists shared posts where we disagree and have no agreed label yet.
    """
    dev = dev_candidates(pool)
    agreed = adjudicated[adjudicated["primary"] != ""] if len(adjudicated) else adjudicated
    gold, unresolved = [], []
    for post in pool.itertuples():
        names = post.annotators.split("+")
        rows = [labels[name].loc[post.id] for name in names if name in labels and post.id in labels[name].index]
        if len(rows) < len(names):  # not labelled yet, or a shared post only one of us has done
            continue
        if len(rows) == 1:
            final, source = _combine(rows), "single"
        elif rows[0]["primary"] == rows[1]["primary"]:
            final, source = _combine(rows), "agreed"
        elif post.id in agreed.index:
            row = agreed.loc[post.id]
            final, source = {key: row[key] for key in ("primary", "alternate", "urgency", "ambiguous")}, "adjudicated"
        else:
            unresolved.append({"id": post.id, **{f"{name}_{key}": labels[name].loc[post.id][key]
                                                 for name in names for key in ("primary", "alternate")}})
            continue
        if final["primary"] == SKIP:
            split = "skip"
        elif final["primary"] == EMERGENCY:
            split = "emergency"
        elif post.part == "test":
            split = "test"
        else:
            split = "dev" if post.id in dev else "train"
        changed = [r.get("changed_from_draft", "") for r in rows if r.get("draft_primary", "")]
        gold.append({"id": post.id, "split": split, **final, "source": source,
                     "changed_from_draft": str(any(c == "True" for c in changed)) if changed else ""})
    columns = ["id", "split", "primary", "alternate", "urgency", "ambiguous", "source", "changed_from_draft"]
    return pd.DataFrame(gold, columns=columns), pd.DataFrame(unresolved)

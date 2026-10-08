"""Score the routers on our own labelled posts.

  python scripts/evaluate_routing.py dev        # compare every trained router on our dev posts
  python scripts/evaluate_routing.py tune       # pick TAU and MARGIN on dev for the best router
  python scripts/evaluate_routing.py test       # score once on our test posts (run this last)
  python scripts/evaluate_routing.py emergency  # how often the written rules fire on our labelled posts

Each command prints Markdown tables. Only `test` reads the test split, and nothing here trains.
"""

import argparse
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass.labels import GP, LABEL2ID, LABELS
from doccompass.metrics import exact_interval, score
from doccompass.pipeline import load_router
from doccompass.redflags import find_flags
from doccompass.splits import gold_split

FAMILIES = ["tfidf", "distilroberta", "biomedbert"]
VERSIONS = {"stage1": "public only", "gold": "ours only", "stage2": "public, then ours"}
MAX_UNSURE = 0.30  # the app should give one answer for most posts


def available_routers() -> dict[str, object]:
    routers = {}
    for family, version in product(FAMILIES, VERSIONS):
        router = load_router(f"{family}_{version}")
        if router is not None:
            routers[f"{family}_{version}"] = router
    return routers


def lenient_top1(proba: np.ndarray, frame: pd.DataFrame) -> float:
    """Top choice matches the primary or the alternate label."""
    top = [LABELS[i] for i in proba.argmax(axis=1)]
    return float(np.mean([t in (row.label, row.alternate) for t, row in zip(top, frame.itertuples())]))


def always_gp(frame: pd.DataFrame) -> np.ndarray:
    proba = np.zeros((len(frame), len(LABELS)))
    proba[:, LABEL2ID[GP]] = 1.0
    return proba


def row(name: str, proba: np.ndarray, frame: pd.DataFrame) -> str:
    result = score(proba, frame["label"].map(LABEL2ID).to_numpy())
    low, high = result["top1_ci"]
    return (f"| {name} | {result['top1']:.1%} ({low:.1%}–{high:.1%}) | {result['top3']:.1%} | "
            f"{lenient_top1(proba, frame):.1%} | {result['macro_f1']:.3f} |")


HEADER = "| Router | Top-1 (95% CI) | Top-3 | Top-1, alternate counts | Macro-F1 |\n|---|---|---|---|---|"


def describe_router(name: str) -> str:
    family, version = name.rsplit("_", 1)
    return f"{family}, {VERSIONS[version]}"


def dev_table(routers: dict, dev: pd.DataFrame) -> dict[str, float]:
    print(f"Our dev posts, n = {len(dev)}\n\n{HEADER}")
    print(row("Always “Start with a GP”", always_gp(dev), dev))
    macro = {}
    for name, router in routers.items():
        proba = router.predict_proba(dev["text"])
        macro[name] = score(proba, dev["label"].map(LABEL2ID).to_numpy())["macro_f1"]
        print(row(describe_router(name), proba, dev))
    return macro


def best_trained_on_ours(macro: dict[str, float]) -> str:
    """The router to ship: best dev macro-F1 among those that have seen our posts."""
    ours = {name: value for name, value in macro.items() if not name.endswith("_stage1")}
    return max(ours, key=ours.get)


def unsure_mask(proba: np.ndarray, tau: float, margin: float) -> np.ndarray:
    top2 = np.sort(proba, axis=1)[:, -2:]
    return (top2[:, 1] < tau) | (top2[:, 1] - top2[:, 0] < margin)


def shown_correct(proba: np.ndarray, frame: pd.DataFrame, unsure: np.ndarray) -> np.ndarray:
    """One answer: right if it matches primary or alternate. Two options: right if either does."""
    order = np.argsort(-proba, axis=1)
    hits = []
    for i, post in enumerate(frame.itertuples()):
        shown = [LABELS[j] for j in order[i, :2 if unsure[i] else 1]]
        hits.append(bool({post.label, post.alternate} & set(shown)))
    return np.array(hits)


def tune(router, dev: pd.DataFrame) -> tuple[float, float]:
    proba = router.predict_proba(dev["text"])
    rows = []
    for tau, margin in product(np.arange(0.0, 0.91, 0.05), np.arange(0.0, 0.31, 0.05)):
        unsure = unsure_mask(proba, tau, margin)
        rows.append((round(tau, 2), round(margin, 2), unsure.mean(), shown_correct(proba, dev, unsure).mean(),
                     shown_correct(proba, dev, np.zeros(len(dev), bool))[~unsure].mean() if (~unsure).any() else float("nan")))
    grid = pd.DataFrame(rows, columns=["tau", "margin", "unsure_rate", "shown_correct", "confident_correct"])
    allowed = grid[grid["unsure_rate"] <= MAX_UNSURE]
    best = allowed.sort_values(["shown_correct", "unsure_rate", "tau"], ascending=[False, True, True]).iloc[0]
    print(f"Grid of {len(grid)} cutoff pairs on {len(dev)} dev posts; two options shown on at most {MAX_UNSURE:.0%} of posts.")
    print(f"Chosen: TAU = {best.tau:.2f}, MARGIN = {best.margin:.2f}: two options on {best.unsure_rate:.0%} of dev posts, "
          f"shown answer right {best.shown_correct:.0%}, single answers right {best.confident_correct:.0%}")
    return float(best.tau), float(best.margin)


def test_report(routers: dict, choices: list[str], test: pd.DataFrame, tau: float, margin: float) -> None:
    print(f"Our test posts, n = {len(test)} (read once)\n\n{HEADER}")
    print(row("Always “Start with a GP”", always_gp(test), test))
    probas = {}
    for name in choices:
        started = time.time()
        probas[name] = routers[name].predict_proba(test["text"])
        ms = 1000 * (time.time() - started) / len(test)
        print(row(f"{describe_router(name)} ({ms:.1f} ms per post)", probas[name], test))

    ambiguous = test["ambiguous"] == "True"
    print("\nTop-1 by how clear the post was\n\n| Router | Clear | Ambiguous |\n|---|---|---|")
    for name in choices:
        hits = probas[name].argmax(axis=1) == test["label"].map(LABEL2ID).to_numpy()
        print(f"| {describe_router(name)} | {hits[~ambiguous].mean():.1%} (n = {(~ambiguous).sum()}) | "
              f"{hits[ambiguous].mean():.1%} (n = {ambiguous.sum()}) |")

    shipped = choices[-1]
    unsure = unsure_mask(probas[shipped], tau, margin)
    right = shown_correct(probas[shipped], test, unsure)
    print(f"\nShipped router ({describe_router(shipped)}), TAU = {tau:.2f}, MARGIN = {margin:.2f}: two options on "
          f"{unsure.mean():.0%} of test posts; right in {right[unsure].mean():.0%} of those and "
          f"{right[~unsure].mean():.0%} of single answers." if unsure.any() else
          f"\nShipped router ({describe_router(shipped)}): one answer on every test post; right {right.mean():.0%}.")

    hits = probas[shipped].argmax(axis=1) == test["label"].map(LABEL2ID).to_numpy()
    per_label = pd.DataFrame({"label": test["label"], "hit": hits}).groupby("label")["hit"].agg(["size", "sum"])
    print(f"\nPer label on test ({describe_router(shipped)})\n\n| Label | Test posts | Top-1 right |\n|---|---|---|")
    for label in LABELS:
        n, k = (int(per_label.loc[label, "size"]), int(per_label.loc[label, "sum"])) if label in per_label.index else (0, 0)
        print(f"| {label} | {n} | {f'{k} ({k / n:.0%})' if n else '–'} |")


def emergency_report(gold: dict[str, pd.DataFrame]) -> None:
    labelled = pd.concat([gold[split] for split in ("train", "dev", "test")])
    emergencies = gold["emergency"]
    fired_ordinary = labelled["text"].map(lambda text: bool(find_flags(text)))
    fired_emergency = emergencies["text"].map(lambda text: bool(find_flags(text)))
    k, n = int(fired_ordinary.sum()), len(labelled)
    low, high = exact_interval(k, n)
    print("Written emergency rules on our labelled posts (rules only; the Qwen check is not run here)\n")
    print("| Posts | Rules fire | 95% CI |\n|---|---|---|")
    print(f"| Not labelled Emergency (routable posts) | {k} of {n} ({k / n:.1%}) | {low:.1%}–{high:.1%} |")
    if len(emergencies):
        k, n = int(fired_emergency.sum()), len(emergencies)
        low, high = exact_interval(k, n)
        print(f"| Labelled Emergency | {k} of {n} ({k / n:.1%}) | {low:.1%}–{high:.1%} |")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["dev", "tune", "test", "emergency"])
    parser.add_argument("--tau", type=float, help="test only: the cutoffs chosen on dev")
    parser.add_argument("--margin", type=float)
    args = parser.parse_args()
    gold = gold_split()
    if args.command == "emergency":
        emergency_report(gold)
        return
    routers = available_routers()
    if args.command in ("dev", "tune"):
        macro = dev_table(routers, gold["dev"])
        shipped = best_trained_on_ours(macro)
        print(f"\nBest on dev among routers trained on our posts: {describe_router(shipped)}")
        if args.command == "tune":
            tune(routers[shipped], gold["dev"])
        return
    if args.tau is None or args.margin is None:
        sys.exit("Pass the cutoffs chosen on dev: --tau T --margin M")
    with np.errstate(all="ignore"):
        macro = {name: score(router.predict_proba(gold["dev"]["text"]), gold["dev"]["label"].map(LABEL2ID).to_numpy())["macro_f1"]
                 for name, router in routers.items()}
    # One router per family, each picked on dev; the shipped one goes last.
    choices = [max((n for n in macro if n.startswith(family) and not n.endswith("_stage1")), key=macro.get)
               for family in FAMILIES if any(n.startswith(family) and not n.endswith("_stage1") for n in macro)]
    shipped = best_trained_on_ours(macro)
    choices = [c for c in choices if c != shipped] + [shipped]
    test_report(routers, choices, gold["test"], args.tau, args.margin)


if __name__ == "__main__":
    main()

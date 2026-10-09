"""Merge our label files into one gold label per post, and report how often we agree.

Run any time:  python scripts/merge_labels.py
Reads data/manual/<name>.labels.csv for each of us and writes data/manual/gold.labels.csv.
Shared test posts where we disagree are added to data/manual/adjudicated.labels.csv: fill in
the primary (and optionally alternate, urgency, ambiguous) we agree on, then run this again.
All three files hold ids and labels only, so they are safe to commit.

With --from-drafts, the first-pass labels in data/manual/draft.labels.csv are used as the gold
labels for every post, as they are. There is then no agreement to report.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass import paths
from doccompass.gold import agreement, annotators, dev_candidates, merge
from doccompass.labels import LABELS

FLOOR = 500  # the brief's minimum number of manual samples


def read_labels(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("").set_index("id") if path.exists() else pd.DataFrame()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-drafts", action="store_true", help="use the first-pass labels as the gold labels, unchanged")
    pool = pd.read_csv(paths.POOL_IDS, dtype=str)
    from_drafts = parser.parse_args().from_drafts
    if from_drafts:
        pool["annotators"] = "draft"
        labels = {"draft": read_labels(paths.DRAFT_LABELS)}
        names = ["draft"]
    else:
        names = annotators(pool)
        labels = {name: read_labels(paths.MANUAL / f"{name}.labels.csv") for name in names}
    labels = {name: frame for name, frame in labels.items() if len(frame)}
    if not labels:
        sys.exit("No label files yet. Label with: python tools/annotate.py --annotator NAME")

    print("Labelled so far")
    for name in names:
        assigned = pool["annotators"].str.split("+").map(lambda who: name in who).sum()
        print(f"  {name}: {len(labels.get(name, [])):>3} of {assigned}")

    if len(labels) == 2:
        first, second = (labels[name] for name in names)
        result = agreement(first, second)
        print(f"\nShared test posts labelled by both of us: {result['n']}")
        if result["n"]:
            print(f"  same primary label: {result['exact']:.0%}")
            print(f"  same, counting either alternate: {result['lenient']:.0%}")
            print(f"  Cohen's kappa: {result['kappa']:.2f}")

    adjudicated = read_labels(paths.ADJUDICATED)
    gold, unresolved = merge(pool, labels, adjudicated)
    if from_drafts:
        gold["source"] = "draft"

    if len(unresolved):  # add new disagreements to the file we fill in, keeping what's there
        template = unresolved.set_index("id")
        for column in ("primary", "alternate", "urgency", "ambiguous"):
            template[column] = ""
        if len(adjudicated):
            template = pd.concat([adjudicated, template[~template.index.isin(adjudicated.index)]])
        template.reset_index().to_csv(paths.ADJUDICATED, index=False)
        print(f"\n{len(unresolved)} shared posts need an agreed label: fill in the primary column in "
              f"{paths.ADJUDICATED.relative_to(paths.ROOT)}, then run this again.")

    gold.to_csv(paths.GOLD, index=False)
    usable = gold[gold["split"].isin(["train", "dev", "test"])]
    print(f"\nGold labels -> {paths.GOLD.relative_to(paths.ROOT)}")
    print(gold["split"].value_counts().reindex(["test", "dev", "train", "emergency", "skip"], fill_value=0).to_string())
    print(f"Usable for the router: {len(usable)} of the {FLOOR} the brief asks for")

    dev = dev_candidates(pool)
    waiting = len(dev - set(gold["id"]))
    if waiting:
        print(f"{waiting} of the {len(dev)} dev candidates are not labelled yet (the labelling tool shows them first).")

    reviewed = gold[gold["changed_from_draft"] != ""]
    if len(reviewed):
        print(f"First-pass labels reviewed: {len(reviewed)}, changed: {(reviewed['changed_from_draft'] == 'True').mean():.0%}")

    if len(usable):
        counts = usable.groupby(["primary", "split"]).size().unstack(fill_value=0)
        counts = counts.reindex(index=LABELS, columns=["train", "dev", "test"], fill_value=0)
        print("\nPosts per label\n" + counts.to_string())


if __name__ == "__main__":
    main()

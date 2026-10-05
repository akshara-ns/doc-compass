"""Measure the emergency check on cases we wrote ourselves.

A missed emergency (false negative) is the costly error, so it is reported first, for
the written rules alone and, with --llm, for the rules plus the language-model check.

Run:  python scripts/check_emergency.py           # rules only
      python scripts/check_emergency.py --llm     # also the model check (loads Qwen)
      python scripts/check_emergency.py --llm --real   # and on real posts with clinician-derived urgency

--real uses the test posts of PMR-Reddit (PortalPal-AI, CC BY-NC 4.0): 362 r/AskDocs posts
whose urgency level, 1 (emergency attention needed) to 6 (no attention needed), was read
off replies from verified clinicians. Level 1 is our "emergency"; levels 4-6 should not flag.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doccompass import paths
from doccompass.mediq import clean_text
from doccompass.metrics import exact_interval
from doccompass.redflags import find_flags

PMR_TEST = {"repo_id": "PortalPal-AI/PMR-Reddit-Test-Pairs", "revision": "f72f5fe3d322397505ebc3bcb216c5f86af14c04", "filename": "data/test-00000-of-00001.parquet"}


def real_posts() -> pd.DataFrame:
    """The unique PMR-Reddit test posts with their urgency level."""
    pairs = pd.read_parquet(hf_hub_download(repo_type="dataset", **PMR_TEST))
    posts = pd.concat([pairs[[side, f"{side}_level"]].set_axis(["text", "level"], axis=1) for side in ("chosen", "rejected")])
    posts = posts.drop_duplicates("text").reset_index(drop=True)
    posts["text"] = posts["text"].map(clean_text)
    return posts


def report_real(name: str, posts: pd.DataFrame, flagged: pd.Series) -> None:
    emergencies, calm = posts["level"] < 2, posts["level"] >= 4
    print(f"\n{name}")
    print(f"  missed emergencies (level 1): {rate(int((emergencies & ~flagged).sum()), int(emergencies.sum()))}")
    print(f"  flagged among levels 4-6:     {rate(int((calm & flagged).sum()), int(calm.sum()))}")


def rate(count: int, total: int) -> str:
    low, high = exact_interval(count, total)
    return f"{count} of {total} ({count / total:.0%}, 95% CI {low:.0%}-{high:.0%})"


def report(name: str, cases: pd.DataFrame, flagged: pd.Series) -> None:
    emergencies, others = cases["emergency"] == 1, cases["emergency"] == 0
    print(f"\n{name}")
    print(f"  missed emergencies:   {rate(int((emergencies & ~flagged).sum()), int(emergencies.sum()))}")
    for kind in ("direct", "paraphrase"):
        subset = emergencies & (cases["kind"] == kind)
        print(f"    {kind + ' wording:':<20}{int((subset & ~flagged).sum())} of {int(subset.sum())} missed")
    print(f"  false alarms:         {rate(int((others & flagged).sum()), int(others.sum()))}")
    for kind in ("ordinary", "tricky"):
        subset = others & (cases["kind"] == kind)
        print(f"    {kind + ' concerns:':<20}{int((subset & flagged).sum())} of {int(subset.sum())} flagged")
    for text in cases.loc[emergencies & ~flagged, "text"]:
        print(f"    MISSED  {text}")
    for text in cases.loc[others & flagged, "text"]:
        print(f"    ALARM   {text}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--llm", action="store_true", help="also run the language-model check")
    parser.add_argument("--real", action="store_true", help="also score real posts with clinician-derived urgency (PMR-Reddit)")
    args = parser.parse_args()

    cases = pd.read_csv(paths.EMERGENCY_CASES)
    by_rules = cases["text"].map(lambda text: bool(find_flags(text)))
    report("Written rules alone", cases, by_rules)

    checker = None
    if args.llm:
        from doccompass.explain import QwenExplainer
        checker = QwenExplainer()
        by_model = cases["text"].map(lambda text: checker.emergency_sign(text) is not None)
        report("Language-model check alone", cases, by_model)
        report("Rules, then the model check (what the app does)", cases, by_rules | by_model)

    if args.real:
        posts = real_posts()
        print(f"\nReal posts: {len(posts)} from PMR-Reddit")
        rules = posts["text"].map(lambda text: bool(find_flags(text)))
        report_real("Written rules alone", posts, rules)
        if checker:
            model = posts["text"].map(lambda text: checker.emergency_sign(text) is not None)
            report_real("Language-model check alone", posts, model)
            report_real("Rules, then the model check (what the app does)", posts, rules | model)


if __name__ == "__main__":
    main()

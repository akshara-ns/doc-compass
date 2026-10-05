"""Scores we report for a router, with exact intervals for small test sets."""

import numpy as np
from scipy.stats import beta
from sklearn.metrics import f1_score

from .labels import LABELS


def exact_interval(correct: int, total: int, level: float = 0.95) -> tuple[float, float]:
    """Clopper-Pearson interval for a proportion; stays honest at 0% and 100%."""
    alpha = 1 - level
    low = 0.0 if correct == 0 else float(beta.ppf(alpha / 2, correct, total - correct + 1))
    high = 1.0 if correct == total else float(beta.ppf(1 - alpha / 2, correct + 1, total - correct))
    return low, high


def top_k_hits(proba: np.ndarray, label_ids, k: int) -> np.ndarray:
    """True where the right label is among the k most probable."""
    top = np.argsort(-proba, axis=1)[:, :k]
    return (top == np.asarray(label_ids)[:, None]).any(axis=1)


def score(proba: np.ndarray, label_ids) -> dict:
    """Top-1 and top-3 accuracy with intervals, and macro-F1 over all labels."""
    label_ids = np.asarray(label_ids)
    total = len(label_ids)
    result = {"n": total}
    for k in (1, 3):
        correct = int(top_k_hits(proba, label_ids, k).sum())
        low, high = exact_interval(correct, total)
        result[f"top{k}"] = correct / total
        result[f"top{k}_ci"] = (low, high)
    result["macro_f1"] = float(f1_score(label_ids, proba.argmax(axis=1), labels=range(len(LABELS)), average="macro", zero_division=0))
    return result


def describe(name: str, result: dict) -> str:
    low1, high1 = result["top1_ci"]
    return (f"{name}: top-1 {result['top1']:.1%} (95% CI {low1:.1%}-{high1:.1%}), "
            f"top-3 {result['top3']:.1%}, macro-F1 {result['macro_f1']:.3f}, n={result['n']}")

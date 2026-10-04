"""One request, start to finish: red flags, scrub, route, explain.

route_concern always returns the same keys, whatever happens, so the interface never has
to guess what it received.
"""

from .explain import headline, template_explanation
from .labels import GP, LABELS
from .paths import MODELS
from .redflags import emergency_message, find_flags
from .router import TfidfRouter
from .scrub import scrub

# Provisional cutoffs for the "unsure" state; tuned on the dev split once our labels exist.
TAU = 0.50  # top confidence below this is unsure
MARGIN = 0.15  # top two closer than this is unsure
MIN_WORDS, MAX_CHARS = 3, 6000


def load_router():
    """The best router available on disk, or None if nothing has been trained yet."""
    for name in ("tfidf_stage2.joblib", "tfidf_stage1.joblib"):
        if (MODELS / name).exists():
            return TfidfRouter.load(MODELS / name)
    return None


def route_concern(text: str, router) -> dict:
    result = {"status": "invalid", "message": "", "flags": [], "text": "", "removed": [],
              "options": [], "unsure": False, "evidence": [], "headline": "", "explanation": ""}
    text = (text or "").strip()
    if len(text.split()) < MIN_WORDS:
        result["message"] = "Describe what you are feeling in a sentence or two, and we'll suggest a kind of doctor."
        return result
    text = text[:MAX_CHARS]

    # 1. Red flags run first, on the raw text. An emergency stops everything else.
    result["flags"] = find_flags(text)
    if result["flags"]:
        result["status"] = "emergency"
        result["message"] = emergency_message(result["flags"])
        return result

    # 2. Optional scrub of obvious identifiers.
    result["text"], result["removed"] = scrub(text)
    result["status"] = "routed"

    # 3. Route. Without a trained router the safe answer is a GP.
    if router is None:
        result["options"] = [{"label": GP, "confidence": 1.0}]
        result["message"] = "The router isn't available right now, so we can only suggest starting with a GP."
    else:
        proba = router.predict_proba([result["text"]])[0]
        top = proba.argsort()[::-1][:3]
        result["options"] = [{"label": LABELS[i], "confidence": float(proba[i])} for i in top]
        first, second = result["options"][0]["confidence"], result["options"][1]["confidence"]
        result["unsure"] = first < TAU or first - second < MARGIN
        best = result["options"][0]["label"]
        if hasattr(router, "evidence") and best != GP and not result["unsure"]:
            result["evidence"] = router.evidence(result["text"], best)

    # 4. Explain, from the record above and nothing else.
    result["headline"] = headline(result)
    result["explanation"] = template_explanation(result)
    return result

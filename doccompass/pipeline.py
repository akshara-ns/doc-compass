"""One request, start to finish: red flags, scrub, route, explain.

route_concern always returns the same keys, whatever happens, so the interface never has
to guess what it received.
"""

import os

from .explain import headline, template_explanation
from .labels import GP, LABELS
from .paths import MODELS
from .redflags import emergency_message, find_flags
from .router import EncoderRouter, TfidfRouter
from .scrub import scrub

# Provisional cutoffs for the "unsure" state; tuned on the dev split once our labels exist.
TAU = 0.50  # top confidence below this is unsure
MARGIN = 0.15  # top two closer than this is unsure
MIN_WORDS, MAX_CHARS = 3, 6000


# Tried in order; stage 2 (trained on our posts) beats stage 1 (public data only).
ROUTER_ORDER = ["distilroberta_stage2", "biomedbert_stage2", "tfidf_stage2",
                "distilroberta_stage1", "biomedbert_stage1", "tfidf_stage1"]


def load_router(name: str | None = None):
    """The first router that loads, or None if nothing has been trained yet.

    Pass a name, or set DOCCOMPASS_ROUTER, to pick one. A fine-tuned router that fails to
    load (for example PyTorch isn't installed) is skipped in favour of the next one.
    """
    name = name or os.environ.get("DOCCOMPASS_ROUTER")
    for candidate in [name] if name else ROUTER_ORDER:
        try:
            if (MODELS / candidate).is_dir():
                return EncoderRouter(MODELS / candidate)
            if (MODELS / f"{candidate}.joblib").exists():
                return TfidfRouter.load(MODELS / f"{candidate}.joblib")
        except Exception:
            continue
    return None


def route_concern(text: str, router, explainer=None) -> dict:
    result = {"status": "invalid", "message": "", "flags": [], "text": "", "removed": [],
              "options": [], "unsure": False, "evidence": [], "headline": "", "explanation": "", "explained_by": ""}
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

    # 4. Explain, from the record above and nothing else. The template is the fallback
    #    whenever the language model is absent, fails, or writes something that fails its checks.
    result["headline"] = headline(result)
    result["explanation"], result["explained_by"] = template_explanation(result), "template"
    if explainer is not None and router is not None:
        try:
            generated = explainer(result)
        except Exception:
            generated = None
        if generated:
            result["explanation"], result["explained_by"] = generated, explainer.name
    return result

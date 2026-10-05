"""Checks on the rules, the scrub and the shape of the pipeline's answer. Run: pytest"""

import numpy as np
import pytest

from doccompass.explain import check_generated
from doccompass.labels import GP, LABELS
from doccompass.pipeline import route_concern
from doccompass.redflags import find_flags
from doccompass.scrub import scrub

KEYS = {"status", "message", "flags", "text", "removed", "options", "unsure", "evidence", "headline", "explanation", "explained_by"}


class FixedRouter:
    """Stands in for a trained router: always returns the same probabilities."""

    def __init__(self, proba):
        self.proba = np.asarray(proba, dtype=float)

    def predict_proba(self, texts):
        return np.tile(self.proba, (len(texts), 1))


def confident():
    proba = np.full(len(LABELS), 0.02)
    proba[0] = 1 - 0.02 * (len(LABELS) - 1)
    return FixedRouter(proba)


def torn():
    proba = np.full(len(LABELS), 0.01)
    proba[0], proba[1] = 0.46, 0.44
    return FixedRouter(proba)


@pytest.mark.parametrize("text", [
    "I have crushing chest pain and my arm is numb",
    "I can't breathe properly since this morning",
    "her face is drooping and she has slurred speech",
    "I have been thinking about killing myself",
    "my tongue is swelling after eating peanuts",
    "he passed out and hit his head",
    "I took an overdose of my pills",
    "my chest hurts really badly",
    "I can barely breathe",
    "thoughts of ending it all",
    "worst headache ever, came on suddenly",
    "I don't want to live anymore",
    "I don't know why but I have chest pain",
    "not sure why my chest pain started an hour ago",
])
def test_emergencies_are_flagged(text):
    assert find_flags(text)
    assert route_concern(text, confident())["status"] == "emergency"


@pytest.mark.parametrize("text", [
    "itchy rash on both shins for three weeks",
    "no chest pain, just a sore knee after running",
    "I think I had food poisoning last week and my stomach is still off",
    "my tooth hurts when I drink something cold",
    "I don't want to die from this, should I see a dermatologist",
    "I have never had chest pain, only a sore shoulder",
    "there was no shortness of breath, just a cough",
])
def test_ordinary_concerns_are_not_flagged(text):
    assert not find_flags(text)


def test_scrub_removes_identifiers_and_reports_them():
    text, removed = scrub("email me at jo@example.com or 412-555-0199, see https://x.io, thanks u/somebody")
    assert "jo@example.com" not in text and "412-555-0199" not in text and "u/somebody" not in text
    assert {item["kind"] for item in removed} == {"email", "phone", "link", "handle"}


@pytest.mark.parametrize("text,router", [
    ("", confident()), ("hi", confident()), ("itchy rash on my arm for weeks", confident()),
    ("itchy rash on my arm for weeks", torn()), ("itchy rash on my arm for weeks", None),
    ("I have chest pain right now", confident()),
])
def test_answer_always_has_the_same_keys(text, router):
    assert set(route_concern(text, router)) == KEYS


def test_confident_and_unsure_states():
    sure = route_concern("itchy rash on my arm for weeks", confident())
    assert sure["status"] == "routed" and not sure["unsure"] and len(sure["options"]) == 3
    unsure = route_concern("itchy rash on my arm for weeks", torn())
    assert unsure["unsure"] and "Two kinds of doctor" in unsure["explanation"]


def test_unsure_with_gp_leads_with_gp():
    proba = np.full(len(LABELS), 0.01)
    proba[LABELS.index(GP)], proba[0] = 0.45, 0.40
    result = route_concern("itchy rash on my arm for weeks", FixedRouter(proba))
    assert result["unsure"] and GP in result["headline"] and LABELS[0] in result["headline"]


def test_no_router_falls_back_to_gp():
    result = route_concern("itchy rash on my arm for weeks", None)
    assert result["options"][0]["label"] == GP and result["explanation"]


GOOD = {"why": "You described an itchy rash on your arm, and Dermatology looks after skin, hair and nails.",
        "questions": ["When did the rash start?", "Has it spread?", "Have you tried any creams?"]}


@pytest.mark.parametrize("change", [
    {"why": "This sounds like eczema, so see a skin doctor soon."},
    {"why": "You described a sore knee, which is consistent with a ligament tear, and Orthopedics looks after joints."},
    {"why": "You described a rash, and a cardiologist looks after skin, hair and nails."},
    {"why": "You described a rash for 3 weeks, and Dermatology looks after skin."},
    {"questions": ["Should you take 200 mg of ibuprofen?"]},
    {"questions": ["When did it start"]},
    {"questions": ["Have you tried antihistamines or steroids?", "When did it start?"]},
])
def test_generated_explanation_is_rejected(change):
    assert check_generated({**GOOD, **change}, ["Dermatology"])


def test_generated_explanation_checks():
    assert check_generated(GOOD, ["Dermatology"]) == []
    assert check_generated("not json", ["Dermatology"])
    neurology = {"why": "You described headaches every afternoon, and Neurology looks after headaches, numbness and memory.",
                 "questions": ["How long do they last?", "What helps?"]}
    assert check_generated(neurology, ["Neurology"]) == []  # "Neurology" must not read as "Urology"
    assert check_generated({**GOOD, "questions": ["Do you take any medicines or supplements?", "When did it start?"]}, ["Dermatology"]) == []


def test_failed_explainer_falls_back_to_template():
    class Broken:
        name = "broken"

        def __call__(self, record):
            raise RuntimeError("model unavailable")

    result = route_concern("itchy rash on my arm for weeks", confident(), Broken())
    assert result["explained_by"] == "template" and result["explanation"]

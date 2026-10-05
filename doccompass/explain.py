"""The plain-language explanation shown under a result.

The template below is always available. A language model can replace it later, but it
only ever sees the same record the template uses, and the template stays as the fallback.
"""

import json
import re

from .labels import GP, SCOPE
from .redflags import WARNING_SIGNS

COMMON_QUESTIONS = [
    "When did it start, and is it getting better, worse or staying the same?",
    "What makes it better or worse?",
    "What have you already tried, including any medicines?",
]
QUESTIONS = {  # one or two extra questions worth having an answer to before the visit
    "Dermatology": ["Has it spread or changed in size, shape or colour?", "Any new soaps, medicines, foods or plants before it started?"],
    "Orthopedics": ["Was there an injury or a change in activity before it started?", "Which movements or positions hurt most?"],
    "ENT": ["Is it on one side or both?", "Any fever, hearing change or trouble swallowing?"],
    "Gastroenterology": ["How does it relate to eating, and to which foods?", "Any change in bowel habits or weight?"],
    "Neurology": ["How often does it happen and how long does it last?", "Any numbness, weakness or vision change with it?"],
    "Urology": ["Any pain, urgency or change in how often you go?", "Any fever or back pain with it?"],
    "Ob-Gyn": ["When was your last period, and is your cycle regular?", "Could you be pregnant?"],
    "Mental health": ["How is it affecting sleep, study or work?", "Have you had support or treatment for this before?"],
    "Cardiology": ["Does it come on with exertion or at rest?", "Any family history of heart problems?"],
    "Eye care": ["Is it one eye or both?", "Do you wear glasses or contacts, and when was your last eye exam?"],
    "Dentistry": ["Is it sensitive to hot, cold or biting?", "When was your last dental visit?"],
    GP: ["Which symptom bothers you most?", "Is there anything you are most worried it could be?"],
}


def _closest_specialty(options: list[dict]) -> dict | None:
    """The most likely option that isn't the GP, if there is one."""
    return next((option for option in options if option["label"] != GP), None)


def headline(record: dict) -> str:
    """One line for the top of the result: one answer when confident, two options when unsure."""
    options = record["options"]
    first = options[0]
    if not record["unsure"] or len(options) < 2:
        return f"<strong>{GP}</strong>" if first["label"] == GP else f"Book: <strong>{first['label']}</strong>"
    if GP in (first["label"], options[1]["label"]):
        closest = _closest_specialty(options)
        return f"Not clear-cut: <strong>{GP}</strong>" + (f", or <strong>{closest['label']}</strong> if that fits better. You decide." if closest else ".")
    return f"<strong>{first['label']}</strong> or <strong>{options[1]['label']}</strong>: either could fit. You decide."


def _lead(record: dict) -> tuple[list[str], str]:
    """The opening paragraphs, which state the result, and the label the questions are for.

    These come from code, never from a language model, so the stated choice and its
    confidence always match what the router returned.
    """
    options = record["options"]
    first = options[0]
    if not record["unsure"] or len(options) < 2:
        return [f"**{first['label']}** looks like the best fit ({first['confidence']:.0%}). It covers {SCOPE[first['label']]}."], first["label"]
    if GP in (first["label"], options[1]["label"]):
        paragraphs = ["**Nothing stands out clearly, so a GP is the safe first step.** A GP can treat common problems and refer you on."]
        closest = _closest_specialty(options)
        if closest:
            paragraphs.append(f"The closest specialty was {closest['label']} ({closest['confidence']:.0%}), which covers {SCOPE[closest['label']]}. If that matches what you are feeling, you could book it directly.")
        return paragraphs, GP
    second = options[1]
    return [
        "**Two kinds of doctor could fit, and the choice is yours.** "
        f"{first['label']} ({first['confidence']:.0%}) covers {SCOPE[first['label']]}. "
        f"{second['label']} ({second['confidence']:.0%}) covers {SCOPE[second['label']]}.",
        "If neither clearly matches what you are feeling, start with a GP, who can refer you on.",
    ], first["label"]


def _questions_block(questions: list[str]) -> str:
    return "**Questions worth having answers to before the visit**\n" + "\n".join(f"- {question}" for question in questions)


def template_explanation(record: dict) -> str:
    """Markdown built only from the routing record: options, confidences and matched words."""
    paragraphs, lead_label = _lead(record)
    if record.get("evidence"):
        paragraphs.append("Words in your description that pointed there: " + ", ".join(f"“{word}”" for word in record["evidence"]) + ".")
    paragraphs.append(_questions_block(COMMON_QUESTIONS + QUESTIONS[lead_label]))
    return "\n\n".join(paragraphs)


# ---------- the off-the-shelf language model ----------

QWEN = {"repo": "Qwen/Qwen2.5-1.5B-Instruct", "revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"}

_SYSTEM = """You help a student get ready for a doctor's visit. Another system has already chosen which kind of doctor to suggest. You never change, question or add to that choice.

Reply with JSON only, with two fields.

"why": ONE sentence in exactly this pattern:
"You described <what the student said, in their own words>, and <doctor> looks after <the matching part of what that doctor covers>."
Do not say what might be causing it. Never name a disease, condition, injury, test or medicine.

"questions": exactly three short questions the doctor is likely to ask, which the student can think about beforehand. A question must not name a disease or a medicine."""

_EXAMPLES = [  # made up; they show the sentence pattern, including the GP case
    ({"concern": "My ankle has been swollen and sore since I twisted it playing football last week.",
      "doctor": "Orthopedics", "covers": SCOPE["Orthopedics"]},
     {"why": "You described a swollen, sore ankle after twisting it playing football, and Orthopedics looks after joints and sports injuries.",
      "questions": ["Can you put weight on the ankle?", "Has the swelling gone down or got worse since last week?", "Have you rested or iced it, and did that help?"]}),
    ({"concern": "For two weeks I've felt tired and a bit dizzy and I don't know why.",
      "doctor": "a GP", "covers": SCOPE[GP]},
     {"why": "You described feeling tired and dizzy for two weeks without knowing why, and a GP looks after problems with no clear single cause and can refer you on.",
      "questions": ["When do you feel most tired or dizzy?", "Has anything changed in your sleep, eating or stress lately?", "Do you take any medicines or supplements?"]}),
]

# Wording that would turn the reason into a diagnosis, a guess at the cause, or advice.
_WHY_FORBIDDEN = re.compile(
    r"\bdiagnos\w*|\bsounds like\b|\bsymptoms? of\b|\bsuch as\b|\bconsistent with\b|\bsuggest\w*|\bindicat\w*"
    r"|\b(?:could|may|might|must) (?:be|have|indicate)\b|\brelated to\b|\blikely\b|\bpossibl\w*|\bprobabl\w*"
    r"|\bdue to\b|\bcaused? by\b|\bsign of\b|\bprescri\w*|\bmedication\w*|\bantibiotic\w*|\binfection\w*|\bcancer\w*|\btumou?r\w*|\d",
    re.IGNORECASE)
_QUESTION_FORBIDDEN = re.compile(
    r"\bdiagnos\w*|\bprescri\w*|\byou should\b|\bcancer\w*|\btumou?r\w*|\d"
    r"|\bantihistamin\w*|\b(?:cortico)?steroids?\b|\bantibiotic\w*|\bibuprofen\b|\bparacetamol\b|\bacetaminophen\b|\baspirin\b|\bantidepress\w*",
    re.IGNORECASE)
_LABEL_STEMS = {  # how each label is written in running text; \b stops "Neurology" matching "urolog"
    "Dermatology": r"\bdermatolog", "Orthopedics": r"\borthop", "ENT": r"\bent\b|\botolaryng",
    "Gastroenterology": r"\bgastroenter", "Neurology": r"\bneurolog", "Urology": r"\burolog",
    "Ob-Gyn": r"\bob-?gyn|\bgyn(?:a)?ecolog|\bobstetric", "Mental health": r"\bpsychiatr|\bpsycholog|\bmental health",
    "Cardiology": r"\bcardiolog", "Eye care": r"\bophthalm|\boptometr|\beye care", "Dentistry": r"\bdentist",
    GP: r"\bgp\b|\bgeneral practi",
}


def check_generated(parsed, allowed_labels: list[str]) -> list[str]:
    """Why a generated explanation can't be shown; an empty list means it passed."""
    if not isinstance(parsed, dict) or not isinstance(parsed.get("why"), str) or not isinstance(parsed.get("questions"), list):
        return ["not in the requested form"]
    why, questions = parsed["why"].strip(), parsed["questions"]
    problems = []
    if not why.startswith("You described") or not 8 <= len(why.split()) <= 45:
        problems.append("the reason does not follow the sentence pattern")
    if _WHY_FORBIDDEN.search(why):
        problems.append("the reason diagnoses, guesses at a cause, advises or uses numbers")
    if not 2 <= len(questions) <= 4 or not all(isinstance(q, str) and q.strip().endswith("?") and len(q.split()) <= 25 for q in questions):
        problems.append("the questions are not two to four short questions")
    elif any(_QUESTION_FORBIDDEN.search(q) for q in questions):
        problems.append("a question diagnoses, advises or uses numbers")
    text = " ".join([why, *map(str, questions)])
    for label, stem in _LABEL_STEMS.items():
        if label not in allowed_labels and re.search(stem, text, re.IGNORECASE):
            problems.append(f"it mentions {label}, which was not suggested")
    return problems


_SAFETY_SYSTEM = """You are a safety check in front of an app that suggests which kind of doctor to book. You do one thing: decide whether a message describes a medical emergency happening NOW, to the writer or to someone who is with them.

It is an emergency if the message describes any of these warning signs happening now:
{signs}

It is NOT an emergency when the event is in the past and over, when it happened to someone who is not with the writer now, when the message says the sign is absent, or when the wording is a figure of speech.

Reply with JSON only: {{"emergency": true or false, "sign": the number of the matching warning sign, or 0}}"""

_SAFETY_EXAMPLES = [  # made up; none of these appear in the evaluation cases
    ("My brother just fell down the stairs and now he is talking nonsense and can't stay awake.", {"emergency": True, "sign": 3}),
    ("I broke my wrist skiing three years ago and it still aches when it rains.", {"emergency": False, "sign": 0}),
    ("There is a piece of food stuck in my wife's throat and she can't get any air in.", {"emergency": True, "sign": 5}),
    ("I have had dry, flaky skin on my elbows for a few months.", {"emergency": False, "sign": 0}),
    ("My aunt had a heart attack in 2019. I want to know which doctor can check my own heart.", {"emergency": False, "sign": 0}),
    ("These exams are killing me and I can't sleep.", {"emergency": False, "sign": 0}),
]


class QwenExplainer:
    """Writes the reason and the questions with Qwen2.5-1.5B-Instruct, used as downloaded.

    It sees only the concern text and the doctor type the router chose. Its output is
    checked by check_generated; anything that fails is dropped and the template is used.
    """

    name = "Qwen2.5-1.5B-Instruct"

    def __init__(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        dtype = torch.float32 if self.device == "cpu" else torch.float16
        self.tokenizer = AutoTokenizer.from_pretrained(QWEN["repo"], revision=QWEN["revision"])
        self.model = AutoModelForCausalLM.from_pretrained(QWEN["repo"], revision=QWEN["revision"], dtype=dtype).to(self.device).eval()

    def _chat(self, messages: list[dict], max_new_tokens: int, sample: bool = False) -> str:
        inputs = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt", return_dict=True).to(self.device)
        settings = {"do_sample": True, "temperature": 0.7, "top_p": 0.9} if sample else {"do_sample": False}
        with self.torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=max_new_tokens, pad_token_id=self.tokenizer.eos_token_id, **settings)
        return self.tokenizer.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    def emergency_sign(self, text: str) -> dict | None:
        """A second emergency check for wording the written rules don't cover.

        Returns a flag naming the published warning sign the model matched, or None.
        A reply that can't be read counts as no flag: the rules have already run.
        """
        signs = "\n".join(f"{number}. {sign}" for number, (sign, _) in enumerate(WARNING_SIGNS, start=1))
        messages = [{"role": "system", "content": _SAFETY_SYSTEM.format(signs=signs)}]
        for example, reply in _SAFETY_EXAMPLES:
            messages += [{"role": "user", "content": example}, {"role": "assistant", "content": json.dumps(reply)}]
        messages.append({"role": "user", "content": text[:1500]})
        match = re.search(r"\{.*?\}", self._chat(messages, max_new_tokens=24), re.DOTALL)
        try:
            reply = json.loads(match.group(0)) if match else {}
        except json.JSONDecodeError:
            return None
        if reply.get("emergency") is not True:
            return None
        number = reply.get("sign")
        sign, source = WARNING_SIGNS[number - 1] if isinstance(number, int) and 1 <= number <= len(WARNING_SIGNS) else ("a warning sign", WARNING_SIGNS[0][1])
        return {"rule": "language-model check", "matched": "", "sign": sign, "source": source[0], "url": source[1]}

    def _generate(self, record: dict, label: str, sample: bool) -> str:
        request = {"concern": record["text"][:1500], "doctor": "a GP" if label == GP else label, "covers": SCOPE[label]}
        messages = [{"role": "system", "content": _SYSTEM}]
        for example_request, example_reply in _EXAMPLES:
            messages += [{"role": "user", "content": json.dumps(example_request)},
                         {"role": "assistant", "content": json.dumps(example_reply)}]
        messages.append({"role": "user", "content": json.dumps(request)})
        return self._chat(messages, max_new_tokens=200, sample=sample)

    def __call__(self, record: dict) -> str | None:
        """Markdown for a routed record, or None when two attempts both fail the checks."""
        paragraphs, lead_label = _lead(record)
        allowed = [lead_label]  # the reason may only mention the doctor it is written for
        for sample in (False, True):  # a greedy try, then one sampled retry
            raw = self._generate(record, lead_label, sample)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            try:
                parsed = json.loads(match.group(0)) if match else None
            except json.JSONDecodeError:
                parsed = None
            if not check_generated(parsed, allowed):
                return "\n\n".join([*paragraphs, parsed["why"].strip(), _questions_block([q.strip() for q in parsed["questions"]])])
        return None

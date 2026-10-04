"""The plain-language explanation shown under a result.

The template below is always available. A language model can replace it later, but it
only ever sees the same record the template uses, and the template stays as the fallback.
"""

from .labels import GP, SCOPE

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
        return f"Book: <strong>{first['label']}</strong>"
    if GP in (first["label"], options[1]["label"]):
        closest = _closest_specialty(options)
        return f"Not clear-cut: <strong>{GP}</strong>" + (f", or <strong>{closest['label']}</strong> if that fits better. You decide." if closest else ".")
    return f"<strong>{first['label']}</strong> or <strong>{options[1]['label']}</strong>: either could fit. You decide."


def template_explanation(record: dict) -> str:
    """Markdown built only from the routing record: options, confidences and matched words."""
    options = record["options"]
    first = options[0]
    lead = first
    if not record["unsure"] or len(options) < 2:
        paragraphs = [f"**{first['label']}** looks like the best fit ({first['confidence']:.0%}). It covers {SCOPE[first['label']]}."]
    elif GP in (first["label"], options[1]["label"]):
        lead = {"label": GP}
        closest = _closest_specialty(options)
        paragraphs = ["**Nothing stands out clearly, so a GP is the safe first step.** A GP can treat common problems and refer you on."]
        if closest:
            paragraphs.append(f"The closest specialty was {closest['label']} ({closest['confidence']:.0%}), which covers {SCOPE[closest['label']]}. If that matches what you are feeling, you could book it directly.")
    else:
        second = options[1]
        paragraphs = [
            "**Two kinds of doctor could fit, and the choice is yours.** "
            f"{first['label']} ({first['confidence']:.0%}) covers {SCOPE[first['label']]}. "
            f"{second['label']} ({second['confidence']:.0%}) covers {SCOPE[second['label']]}.",
            "If neither clearly matches what you are feeling, start with a GP, who can refer you on.",
        ]
    if record.get("evidence"):
        paragraphs.append("Words in your description that pointed there: " + ", ".join(f"“{word}”" for word in record["evidence"]) + ".")
    questions = COMMON_QUESTIONS + QUESTIONS[lead["label"]]
    paragraphs.append("**Questions worth having answers to before the visit**\n" + "\n".join(f"- {question}" for question in questions))
    return "\n\n".join(paragraphs)

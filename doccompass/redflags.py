"""Emergency rules. They run first, on the raw text, and are written by hand, never learned.

Each rule quotes the warning sign it implements and where that sign is published.
Sources (read 4 Oct 2026):
- MedlinePlus, "Recognizing medical emergencies" (US National Library of Medicine)
- CDC, "Signs and Symptoms of Stroke"
"""

import re
from dataclasses import dataclass

MEDLINEPLUS = ("MedlinePlus: Recognizing medical emergencies", "https://medlineplus.gov/ency/article/001927.htm")
CDC_STROKE = ("CDC: Signs and Symptoms of Stroke", "https://www.cdc.gov/stroke/signs-symptoms/index.html")

# Every adult warning sign on the two source pages, as published. The rules below cover the
# ones that can be matched by wording; the language-model check is given the whole list.
WARNING_SIGNS = [(sign, MEDLINEPLUS) for sign in (
    "Bleeding that will not stop",
    "Breathing problems (difficulty breathing, shortness of breath)",
    "Change in mental status (such as unusual behavior, confusion, difficulty arousing)",
    "Chest pain or discomfort lasting for two minutes or more",
    "Choking",
    "Coughing up or vomiting blood",
    "Fainting or loss of consciousness",
    "Feeling of committing suicide or murder",
    "Head or spine injury",
    "Inability to speak",
    "Severe abdominal pain or pressure",
    "Severe or persistent vomiting or diarrhea",
    "Sudden injury from a motor vehicle accident, burns, smoke inhalation, near drowning, or a deep or large wound",
    "Sudden, severe pain anywhere in the body",
    "Sudden dizziness, weakness, or change in vision",
    "Swallowing a poisonous substance",
    "Swelling of the face, eyes, or tongue",
)] + [(sign, CDC_STROKE) for sign in (
    "Sudden numbness or weakness in the face, arm, or leg, especially on one side",
    "Sudden confusion, trouble speaking, or difficulty understanding speech",
    "Sudden trouble seeing",
    "Sudden trouble walking, dizziness, loss of balance, or lack of coordination",
    "Sudden severe headache with no known cause",
)]

EMERGENCY_MESSAGE = "This may be an emergency. Call 911 or go to the nearest emergency room now."
CRISIS_MESSAGE = "You can also call or text 988 (Suicide & Crisis Lifeline), free and open at any time."


@dataclass(frozen=True)
class Rule:
    name: str
    sign: str  # the warning sign as the source words it
    source: tuple[str, str]  # (title, url)
    pattern: re.Pattern


def _rule(name: str, sign: str, source: tuple[str, str], pattern: str) -> Rule:
    return Rule(name, sign, source, re.compile(pattern, re.IGNORECASE))


_CANT = r"(?:can'?t|cannot|can not|unable to|couldn'?t)"

RULES = [
    _rule("chest pain", "Chest pain or discomfort lasting for two minutes or more", MEDLINEPLUS,
          r"\bchest (?:pain|pressure|tightness|discomfort)\b|\bpain in (?:my|the|his|her) chest\b"
          r"|\bchest (?:hurts|is hurting|feels tight|feels heavy)\b"),
    _rule("breathing", "Breathing problems (difficulty breathing, shortness of breath)", MEDLINEPLUS,
          rf"\b(?:{_CANT}|can barely|barely able to|struggling to|hard to|trouble|difficulty) breath(?:e|ing)\b|\bshort(?:ness)? of breath\b|\bgasping for (?:air|breath)\b"),
    _rule("stroke signs", "Sudden numbness or weakness in the face, arm, or leg; sudden confusion or trouble speaking", CDC_STROKE,
          rf"\bface (?:is |was )?drooping\b|\bslurred speech\b|\b(?:{_CANT}|trouble) (?:speak|speaking|talk|talking)\b"
          r"|\bsudden(?:ly)? (?:numb|weak|confus)\w*|\b(?:numb|weak)\w* on (?:one|the left|the right|my left|my right) side\b"
          # the word itself, and one-sided or facial numbness, drooping or weakness
          r"|\bstrokes?\b(?! of (?:luck|genius))"
          r"|\bface (?:is |was |feels |went |has gone )?(?:numb|droopy|drooped|weak|paraly[sz]ed)\b"
          r"|\bfacial (?:droop\w*|paralysis|numbness|weakness)\b"
          r"|\b(?:left|right|one|half|side) (?:side )?of (?:my|the|his|her) (?:face|body)\b[^.!?]{0,25}\b(?:numb|droop\w*|weak|paraly[sz]ed|tingl\w*)"),
    _rule("bleeding", "Bleeding that will not stop; coughing up or vomiting blood", MEDLINEPLUS,
          rf"\bbleeding (?:that )?(?:won'?t|will not|doesn'?t|does not) stop\b|\b{_CANT} stop (?:the )?bleeding\b"
          r"|\b(?:coughing|coughed|vomiting|vomited|throwing|threw) up blood\b"),
    _rule("loss of consciousness", "Fainting or loss of consciousness", MEDLINEPLUS,
          r"\b(?:passed out|fainted|lost consciousness|unconscious|unresponsive)\b"),
    _rule("suicidal thoughts", "Feeling of committing suicide or murder", MEDLINEPLUS,
          r"\bsuicid\w*|\bkill(?:ing)? myself\b|\bend(?:ing)? my (?:own )?life\b|\bwant(?:ed)? to die\b|\bdon'?t want to (?:live|be alive)\b"
          r"|\bend(?:ing)? it all\b|\btake my (?:own )?life\b"),
    _rule("face or throat swelling", "Swelling of the face, eyes, or tongue", MEDLINEPLUS,
          r"\b(?:throat|tongue|lips?|face) (?:is |are |was |were )?(?:swelling|swollen|closing)\b"
          r"|\bswelling (?:of|in) (?:my |the )?(?:face|tongue|throat|lips?)\b|\banaphyla\w*"),
    _rule("head or spine injury", "Head or spine injury", MEDLINEPLUS,
          r"\b(?:hit|banged|bumped|struck|cracked) (?:my|his|her|the) head\b|\b(?:head|spine|spinal) injury\b"),
    _rule("poisoning or overdose", "Swallowing poisonous substances", MEDLINEPLUS,
          r"\boverdos\w*|(?<!food )\bpoison(?:ed|ing)\b|\b(?:swallowed|drank|ingested) (?:bleach|poison|detergent|antifreeze)\b"),
    _rule("sudden severe pain", "Sudden, severe pain anywhere in the body; sudden severe headache with no known cause", MEDLINEPLUS,
          r"\bsudden(?:ly)?\b[^.!?]{0,40}\b(?:severe|excruciating|unbearable|worst)\b[^.!?]{0,25}\b(?:pain|headache)\b"
          r"|\bworst (?:headache|pain) (?:of my life|ever)\b"),
    _rule("sudden vision change", "Sudden trouble seeing", CDC_STROKE,
          rf"\bsudden(?:ly)? (?:lost|loss of|blurred|blurry|double) vision\b|\bsuddenly {_CANT} see\b|\bsudden(?:ly)? (?:went )?blind\b"),
]

# A match is ignored when a negation governs it: "no chest pain", "I don't want to die",
# "never had any trouble breathing". Only short filler words may sit between the two, so
# "not sure why my chest pain started" and "I don't know why but my chest hurts" still flag.
_NEGATION = re.compile(
    r"\b(?:no|not|never|without|denies|deny|didn'?t|don'?t|doesn'?t|haven'?t|hasn'?t|isn'?t|wasn'?t)"
    r"(?:\s+(?:have|had|has|having|got|get|getting|any|a|an|the|real|really|much|more|been|"
    r"experienced|experiencing|feel|felt|noticed|want|wanted|to|this|that|such)){0,4}\s*$", re.IGNORECASE)


def find_flags(text: str) -> list[dict]:
    """Every rule that fires, with the words that triggered it."""
    flags = []
    for rule in RULES:
        for match in rule.pattern.finditer(text):
            if _NEGATION.search(text[max(0, match.start() - 60):match.start()]):
                continue
            flags.append({"rule": rule.name, "matched": match.group(0), "sign": rule.sign,
                          "source": rule.source[0], "url": rule.source[1]})
            break
    return flags


def emergency_message(flags: list[dict]) -> str:
    message = EMERGENCY_MESSAGE
    if any("suicide" in flag["sign"].lower() for flag in flags):
        message += " " + CRISIS_MESSAGE
    return message

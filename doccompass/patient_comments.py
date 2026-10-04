"""The public stage-1 training set: Patient Comments and Specialist Types, remapped to our labels.

Source: Mendeley Data, DOI 10.17632/2twgjzpn82.2, CC BY 4.0. Each comment has a symptom
category; CATEGORY_MAP sends each category to one of our labels, or drops it.
See docs/label-set.md for the reasoning behind each choice.
"""

import hashlib
import re
import ssl
import urllib.request
from pathlib import Path

import certifi
import pandas as pd

from .labels import GP, LABELS
from .mediq import dedupe_key
from .paths import PUBLIC

_URL = "https://data.mendeley.com/public-files/datasets/2twgjzpn82/files/{file_id}/file_downloaded"
_FILES = {  # name: (Mendeley file id, sha256). We ignore the source's own train/test split.
    "HealthCare Data.xlsx": ("c6bdc6b5-c848-4570-a55f-aa522ecd4a4d", "d26f45970e538306125ff633f07a91344d09609355a311e2c3072766bbf66ca1"),
    "Test_data.xlsx": ("b22a38f6-d8a9-4754-9cf2-4d6585a19ab2", "176866719dc580d8ccaeaba5a114f5b83c5848642da253d7c35001368555e155"),
}

DROP = None  # category left out: about infants or the elderly, out of scope, or mixes in emergencies
CATEGORY_MAP = {
    "Acne": "Dermatology", "Skin issue": "Dermatology", "Hair falling out": "Dermatology",
    "Changes in Skin": "Dermatology", "Nails issue": "Dermatology",
    "Knee pain": "Orthopedics", "Joint pain": "Orthopedics", "Shoulder pain": "Orthopedics",
    "Muscle pain": "Orthopedics", "Back pain": "Orthopedics", "Neck pain": "Orthopedics",
    "Injury from sports": "Orthopedics", "Foot ache": "Orthopedics", "Ankle pain": "Orthopedics",
    "Foot pain": "Orthopedics", "Arthralgia": "Orthopedics",
    "Ear ache": "ENT",
    "Stomach ache": "Gastroenterology", "Liver issues": "Gastroenterology",
    "Head ache": "Neurology", "Memory disturbance": "Neurology", "Difficulty speaking": "Neurology",
    "Seizures": "Neurology", "Dementia": "Neurology", "Brain tumors": "Neurology",
    "Urinary issue": "Urology", "Infertility in men": "Urology",
    "Pregnancy issues": "Ob-Gyn", "Abnormal bleeding": "Ob-Gyn", "Infertility": "Ob-Gyn",
    "Emotional pain": "Mental health", "Mood swing": "Mental health",
    "Behavioral issues": "Mental health", "Addiction": "Mental health",
    "Heart hurts": "Cardiology",
    "Blurry vision": "Eye care", "Eye Infection": "Eye care",
    "Bad breath": "Dentistry", "Toothache": "Dentistry",
    "Cough": GP, "Feeling dizzy": GP, "Feeling cold": GP, "Body feels weak": GP,
    "Hard to breath": GP, "Internal pain": GP, "Infected wound": GP, "Diabetes": GP,
    "Blood related": GP, "Allergic reactions": GP, "Asthma": GP, "Lower back or pelvic pain": GP,
    "Autoimmune diseases": GP, "Swelling": GP, "Unexplained Fever/Bruising": GP, "Persistent fatigue": GP,
    "Open wound": DROP, "Vaccinations": DROP, "Growth issue": DROP, "Old age": DROP,
    "Spinal cord injuries": DROP, "Face deformation": DROP, "Accidents": DROP,
    "Neonatal infections": DROP, "Jaundice": DROP, "Premature birth": DROP,
    "Movement problems": DROP, "Cardiac issues in newborns": DROP, "Burns": DROP,
}
assert set(CATEGORY_MAP.values()) <= set(LABELS) | {DROP}

_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")


def _category_key(category: str) -> str:
    """The source spells categories inconsistently ("mood swing", "Unexplained Fever/ Bruising")."""
    return re.sub(r"\s+", "", str(category)).lower()


_MAP_BY_KEY = {_category_key(category): label for category, label in CATEGORY_MAP.items()}


def _download(name: str, folder: Path) -> Path:
    """Fetch one source file if it isn't already there, and check its hash."""
    path = folder / name
    file_id, sha256 = _FILES[name]
    if not path.exists():
        folder.mkdir(parents=True, exist_ok=True)
        context = ssl.create_default_context(cafile=certifi.where())
        # Mendeley rejects Python's default user agent.
        request = urllib.request.Request(_URL.format(file_id=file_id), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, context=context, timeout=60) as response:
            path.write_bytes(response.read())
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha256:
        raise ValueError(f"{name} does not match its expected hash; delete it and run again.")
    return path


def load_patient_comments() -> pd.DataFrame:
    """Return unique comments as (text, label) in our label set, with emoji removed."""
    folder = PUBLIC / "patient_comments_source"
    rows = pd.concat([pd.read_excel(_download(name, folder)) for name in _FILES], ignore_index=True)
    rows["label"] = rows["Patient_Category"].map(lambda category: _MAP_BY_KEY[_category_key(category)])
    rows = rows.dropna(subset=["label"])
    rows["text"] = rows["Patient_comment"].astype(str).map(lambda t: re.sub(r"\s+", " ", _EMOJI.sub("", t)).strip())
    rows["key"] = rows["text"].map(dedupe_key)
    # The same comment can sit under two categories; drop it when they map to different labels.
    consistent = rows.groupby("key")["label"].transform("nunique") == 1
    rows = rows[consistent & (rows["key"] != "")].drop_duplicates("key")
    return rows[["text", "label"]].sort_values(["label", "text"]).reset_index(drop=True)

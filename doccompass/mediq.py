"""The post pool: unique real posts from MediQ_AskDocs."""

import html
import json
import re

import pandas as pd
from huggingface_hub import hf_hub_download

# Pinned so everyone builds the same pool.
MEDIQ = {"repo_id": "stellalisy/MediQ_AskDocs", "revision": "f215fd4d70e15298d71ae56330ac349c5720e0bf"}
MEDIQ_FILES = [f"original/{split}.jsonl" for split in ("train", "validation", "test")]  # skips synthetic/

_HANDLE = re.compile(r"/?\bu/[\w-]+")
_URL = re.compile(r"https?://\S+|www\.\S+")


def clean_text(text: str) -> str:
    """Drop Reddit handles, links and HTML entities; tidy whitespace but keep line breaks."""
    text = html.unescape(text).replace("​", " ")
    text = _URL.sub(" ", _HANDLE.sub(" ", text))
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\s*\n\s*", "\n", text).strip()


def dedupe_key(text: str) -> str:
    """Two posts are the same post if they match after lower-casing and dropping punctuation."""
    return re.sub(r"\W+", " ", text.lower()).strip()


def load_mediq_posts() -> pd.DataFrame:
    """Return unique posts as (id, text), sorted by id.

    MediQ repeats each post once per doctor question, and some posts carry several ids,
    so we keep one row per post text and its smallest id.
    """
    posts: dict[str, tuple[str, str]] = {}
    for name in MEDIQ_FILES:
        path = hf_hub_download(repo_type="dataset", filename=name, **MEDIQ)
        with open(path, encoding="utf-8") as lines:
            for line in lines:
                row = json.loads(line)
                text = clean_text(row["messages"][0]["content"])
                post_id = row["id"].split("-")[0]
                key = dedupe_key(text)
                if key not in posts or post_id < posts[key][0]:
                    posts[key] = (post_id, text)
    return pd.DataFrame(sorted(posts.values()), columns=["id", "text"])

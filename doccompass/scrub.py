"""Optional scrub: remove obvious identifiers with simple rules and report what was removed.

This is not full redaction. It only catches handles, emails, phone numbers and links.
"""

import re

_PATTERNS = [  # order matters: emails before handles, links before phone numbers
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("link", re.compile(r"https?://\S+|www\.\S+")),
    ("handle", re.compile(r"(?<!\w)/?u/[\w-]+|(?<!\w)@\w{2,}")),
    ("phone", re.compile(r"(?<!\d)(?:\+?\d{1,2}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")),
]


def scrub(text: str) -> tuple[str, list[dict]]:
    """Return the text with identifiers replaced by [kind], and the list of what was removed."""
    removed = []
    for kind, pattern in _PATTERNS:
        def replace(match, kind=kind):
            removed.append({"kind": kind, "text": match.group(0)})
            return f"[{kind}]"
        text = pattern.sub(replace, text)
    return text, removed

"""Redact personal data and secrets before text reaches the LLM or the user."""
from __future__ import annotations

import re

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("AWS_ACCESS_KEY", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("AWS_SECRET", re.compile(r"(?<![A-Za-z0-9/+])[A-Za-z0-9/+]{40}(?![A-Za-z0-9/+])")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)")),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


def redact(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    for label, pattern in PATTERNS:
        text, n = pattern.subn(f"[REDACTED_{label}]", text)
        if n:
            counts[label] = counts.get(label, 0) + n
    return text, counts


def contains_pii(text: str) -> bool:
    return any(p.search(text) for _, p in PATTERNS)

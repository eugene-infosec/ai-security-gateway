from __future__ import annotations
import re
from typing import Any, Mapping

def tokenize(q: str) -> list[str]:
    q = q.lower()
    parts = re.split(r"[^a-z0-9]+", q)
    return [p for p in parts if p]

def score_doc(doc: Mapping[str, Any], q_tokens: list[str]) -> int:
    """
    Deterministic lexical scoring: counts token occurrences in title+body.
    """
    title = str(doc.get("title") or "").lower()
    body = str(doc.get("body") or "").lower()
    text = title + " " + body

    score = 0
    for t in q_tokens:
        # Count non-overlapping occurrences
        score += text.count(t)
    return score
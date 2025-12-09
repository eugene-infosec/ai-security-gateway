from __future__ import annotations

import re
from typing import Any, Mapping

from app.auth import Principal
from app.policy import is_allowed

MAX_SNIPPET = 160

# Simple “token-like” redactions (The "Leakage Surface" Defense)
TOKEN_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",                  # OpenAI-like keys
    r"AKIA[0-9A-Z]{16}",                     # AWS access key id
    r"-----BEGIN [A-Z ]+-----",              # PEM headers
    r"SECRET_SHOULD_NEVER_APPEAR",           # explicit canary for tests
]
TOKEN_RE = re.compile("|".join(TOKEN_PATTERNS))

def _redact(s: str) -> str:
    return TOKEN_RE.sub("[REDACTED]", s)

def _tokenize(q: str) -> list[str]:
    q = q.lower()
    parts = re.split(r"[^a-z0-9]+", q)
    return [p for p in parts if p]

def make_snippet(principal: Principal, doc: Mapping[str, Any], query: str) -> str:
    """
    Snippets are a leakage surface. This function is policy-aware:
    - If doc is not allowed: returns empty string (defense-in-depth).
    - Redacts token-like strings.
    - Caps length.
    """
    # 1. Double-Check Policy (Defense in Depth)
    allowed, _reason = is_allowed(principal, doc)
    if not allowed:
        return ""

    body = str(doc.get("body") or "")
    if not body:
        return ""

    q_tokens = _tokenize(query)
    haystack = body

    # 2. Find Window
    start = 0
    if q_tokens:
        low = haystack.lower()
        for t in q_tokens:
            idx = low.find(t)
            if idx != -1:
                start = max(0, idx - 40)
                break

    snippet = haystack[start : start + MAX_SNIPPET]
    
    # 3. Clean up
    snippet = " ".join(snippet.split())
    
    # 4. Redact Secrets (The "Senior" Move)
    snippet = _redact(snippet)
    
    return f"...{snippet}..."
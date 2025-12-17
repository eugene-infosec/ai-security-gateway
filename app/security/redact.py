from __future__ import annotations
import re

# Regex patterns for common secrets (simplified for demo)
PATTERNS = {
    # AWS Access Key ID (e.g., AKIA...)
    "AWS_KEY": r"(AKIA[0-9A-Z]{16})",
    # Stripe Secret Key (e.g., sk_live_...)
    "STRIPE_SECRET": r"(sk_live_[0-9a-zA-Z]{24})",
    # Generic "secret =" pattern
    "GENERIC_SECRET": r"(?i)(secret|password|token|key)\s*[:=]\s*([^\s]+)",
}


def redact_text(text: str) -> str:
    """
    Scrub known sensitive patterns from text.
    Replaces matches with [REDACTED].
    """
    cleaned = text
    for _, pattern in PATTERNS.items():
        # Replace the capturing group or the whole match
        cleaned = re.sub(pattern, "[REDACTED]", cleaned)
    return cleaned

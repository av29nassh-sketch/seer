"""
Sensitive-data redaction for UIA tree output.

We pattern-match common secret formats and replace them with [REDACTED] before
returning element names/values to the AI agent. Goal: agent never sees credentials
sitting in window titles, tab names, or input values.

Conservative on purpose — we only redact patterns that have very low false-positive risk:
  - Provider API keys (Anthropic, OpenAI, GitHub, AWS, Google, Stripe)
  - Bearer tokens (Authorization: Bearer ...)
  - JWT tokens (three base64url segments)
  - Generic high-entropy `sk_*` / `pk_*` keys
  - SSN-style (US) and PAN (Indian tax ID)

Not redacted (high false-positive risk without context):
  - Credit card numbers (need Luhn validation + context)
  - Aadhaar (12-digit numbers — too many false positives)
  - Phone numbers (often legitimate UI content)
"""

from __future__ import annotations
import re

# Order matters: more specific patterns first to avoid double-redaction.
_PATTERNS = [
    # Anthropic
    re.compile(r"\b(?:sk-)?an[t]?_sk_[A-Za-z0-9_\-]{16,}\b"),
    # OpenAI
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}\b"),
    # GitHub PAT (classic + fine-grained)
    re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
    # AWS access key
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # Google API key
    re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b"),
    # Stripe
    re.compile(r"\b(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{20,}\b"),
    # JWT (three base64url segments separated by dots)
    re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
    # Authorization: Bearer ...
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[A-Za-z0-9_\-\.]{20,}", ),
    # Generic high-entropy sk_ / pk_ tokens (catch-all after specific ones)
    re.compile(r"\b(?:sk|pk)_[A-Za-z0-9_\-]{24,}\b"),
    # US SSN
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # Indian PAN
    re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
]

_REDACTED = "[REDACTED]"


def redact(text: str) -> str:
    """Return text with any sensitive-looking substring replaced by [REDACTED]."""
    if not text:
        return text
    out = text
    for pat in _PATTERNS:
        out = pat.sub(_REDACTED, out)
    return out

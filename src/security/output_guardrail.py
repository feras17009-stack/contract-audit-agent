"""
Output Guardrail: PII & Sensitive Data Redaction / Masking.
Satisfies Deliverable 4 (Security, Guardrails & Observability).
"""

import re
from typing import Dict, Any

# Regex patterns for common PII and sensitive data
PII_PATTERNS = {
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "PHONE_US": r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b",
    "CONFIDENTIAL_KEY": r"\b(?:sk_[a-zA-Z0-9]{24,}|api[_-]key[_-][a-zA-Z0-9]{16,})\b",
}


def mask_sensitive_data(text: str) -> Dict[str, Any]:
    """
    Redacts PII and sensitive credentials from output text summaries or audit logs.
    
    Returns:
        Dict containing:
            - masked_text (str): Output text with sensitive items redacted.
            - pii_redacted_count (int): Total number of PII items masked.
            - redactions_by_type (Dict[str, int]): Count of redactions per category.
    """
    if not text:
        return {
            "masked_text": "",
            "pii_redacted_count": 0,
            "redactions_by_type": {}
        }

    masked = text
    redactions = {}
    total_count = 0

    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, masked)
        count = len(matches)
        if count > 0:
            redactions[pii_type] = count
            total_count += count
            masked = re.sub(pattern, f"[{pii_type}_REDACTED]", masked)

    return {
        "masked_text": masked,
        "pii_redacted_count": total_count,
        "redactions_by_type": redactions
    }

"""
Input Guardrail: Detects prompt injection attacks and malicious instruction overrides in untrusted text.
Satisfies Deliverable 4 (Security, Guardrails & Observability).
"""

import re
from typing import Dict, Any, List

# Common prompt injection pattern signatures
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"system\s*:\s*",
    r"you\s+are\s+now\s+a",
    r"disregard\s+(all\s+)?guidelines",
    r"bypass\s+security",
    r"override\s+safety",
    r"do\s+not\s+enforce",
    r"grant\s+full\s+compliance",
    r"mark\s+as\s+(100%|fully)\s+compliant",
    r"return\s+only\s+['\"]?compliant['\"]?",
    r"eval\(",
    r"exec\(",
    r"<script\b",
]


def validate_input_security(text: str) -> Dict[str, Any]:
    """
    Scans untrusted input (e.g. text extracted from a PDF contract) for prompt-injection attacks.
    
    Returns:
        Dict containing:
            - is_safe (bool): True if no malicious patterns detected.
            - detected_patterns (List[str]): List of matched attack signatures.
            - sanitized_text (str): Input text wrapped safely within strict XML delimiters.
    """
    if not text or not text.strip():
        return {
            "is_safe": True,
            "detected_patterns": [],
            "sanitized_text": "<UNTRUSTED_DOCUMENT_CONTENT></UNTRUSTED_DOCUMENT_CONTENT>"
        }

    detected = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            detected.append(pattern)

    is_safe = len(detected) == 0

    # Wrap in explicit boundary delimiters so the LLM treats it as data, not instructions
    safe_wrapper = (
        f"<UNTRUSTED_DOCUMENT_CONTENT>\n"
        f"{text.strip()}\n"
        f"</UNTRUSTED_DOCUMENT_CONTENT>"
    )

    return {
        "is_safe": is_safe,
        "detected_patterns": detected,
        "sanitized_text": safe_wrapper
    }

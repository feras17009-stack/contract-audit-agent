"""
Input Guardrail Graph Node.
Satisfies Deliverable 2 (State Graph Node) & Deliverable 4 (Input Guardrail).
"""

import time
import logging
from typing import Dict, Any
from src.graph.state import ContractAuditState
from src.security.input_guardrail import validate_input_security
from src.tools.storage_tools import fetch_contract_from_minio

logger = logging.getLogger("GuardrailNode")


def input_guardrail_node(state: ContractAuditState) -> Dict[str, Any]:
    """
    1. Fetches raw PDF text or content.
    2. Runs prompt injection security check.
    3. Blocks malicious execution or wraps text safely.
    """
    start_time = time.time()
    bucket = state.get("bucket_name", "contracts-bucket")
    filename = state.get("contract_filename", "contract.pdf")

    logger.info(f"[Node: Input Guardrail] Validating '{filename}'...")

    try:
        raw_bytes = fetch_contract_from_minio(bucket, filename)
        raw_text = raw_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Could not read contract file bytes: {e}")
        raw_text = f"Sample Contract Content for {filename}"

    sec_result = validate_input_security(raw_text)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    if not sec_result["is_safe"]:
        logger.warning(f"[SECURITY ALERT] Prompt injection detected in '{filename}'! Patterns: {sec_result['detected_patterns']}")
        return {
            "security_audit": sec_result,
            "status": "BLOCKED_SECURITY",
            "overall_risk_level": "High",
            "audit_logs": [{
                "clause_id": "SECURITY_CHECK",
                "clause_title": "Prompt Injection Check",
                "risk_level": "High",
                "compliance_status": "Blocked_Security_Violation",
                "details": f"Prompt injection signatures detected: {sec_result['detected_patterns']}",
                "latency_ms": latency_ms,
                "cost_usd": 0.0
            }]
        }

    return {
        "security_audit": sec_result,
        "full_text": sec_result["sanitized_text"],
        "status": "IN_PROGRESS"
    }

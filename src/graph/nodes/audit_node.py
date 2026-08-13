"""
Audit Logger Graph Node.
Satisfies Deliverable 1 & Deliverable 5 (Immutable Database Logging & Execution Metrics).
"""

import logging
from typing import Dict, Any
from src.graph.state import ContractAuditState
from src.tools.audit_tools import log_audit_entry
from src.security.output_guardrail import mask_sensitive_data

logger = logging.getLogger("AuditNode")


def audit_logger_node(state: ContractAuditState) -> Dict[str, Any]:
    """
    Saves accumulated audit trail entries into the SQLite database, applying output PII redaction.
    """
    thread_id = state.get("thread_id", "unknown_thread")
    contract_name = state.get("contract_filename", "contract.pdf")
    audit_logs = state.get("audit_logs", [])

    logger.info(f"[Node: Audit Logger] Persisting {len(audit_logs)} audit records to database for thread '{thread_id}'...")

    persisted_records = []
    for entry in audit_logs:
        raw_details = entry.get("details", "")
        # Apply output guardrail (PII masking)
        masked_res = mask_sensitive_data(raw_details)
        clean_details = masked_res["masked_text"]

        db_rec = log_audit_entry(
            thread_id=thread_id,
            contract_name=contract_name,
            clause_id=entry.get("clause_id", "unknown"),
            clause_title=entry.get("clause_title", "Clause"),
            risk_level=entry.get("risk_level", "Low"),
            compliance_status=entry.get("compliance_status", "Compliant"),
            details=clean_details,
            latency_ms=entry.get("latency_ms", 0.0),
            cost_usd=entry.get("cost_usd", 0.0)
        )
        persisted_records.append(db_rec)

    final_status = state.get("status", "COMPLETED")
    if final_status == "IN_PROGRESS":
        final_status = "COMPLETED"

    return {
        "status": final_status
    }

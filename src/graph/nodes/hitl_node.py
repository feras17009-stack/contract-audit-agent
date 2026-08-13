"""
Human-in-the-Loop (HITL) Graph Node.
Satisfies Deliverable 5 (Production Readiness: HITL Interrupt & Pause/Resume).
"""

import logging
from typing import Dict, Any
from src.graph.state import ContractAuditState

logger = logging.getLogger("HITLNode")


def human_approval_node(state: ContractAuditState) -> Dict[str, Any]:
    """
    Interrupt/approval node where the graph execution pauses for manual reviewer decision.
    Upon resume, checks human_approved boolean in state.
    """
    thread_id = state.get("thread_id", "unknown_thread")
    human_approved = state.get("human_approved")

    logger.info(f"[Node: Human Approval] Checking HITL approval state for thread '{thread_id}' (Approved={human_approved})...")

    if human_approved is True:
        status = "COMPLETED"
        log_detail = f"Human reviewer APPROVED contract audit (Notes: {state.get('human_comments', 'No comments')})."
    elif human_approved is False:
        status = "REJECTED"
        log_detail = f"Human reviewer REJECTED contract audit (Notes: {state.get('human_comments', 'No comments')})."
    else:
        status = "PAUSED_HITL"
        log_detail = "Graph execution paused awaiting human approval."

    return {
        "status": status,
        "audit_logs": [{
            "clause_id": "HITL_DECISION",
            "clause_title": "Human Review Decision",
            "risk_level": state.get("overall_risk_level", "Medium"),
            "compliance_status": status,
            "details": log_detail,
            "latency_ms": 10.0,
            "cost_usd": 0.0
        }]
    }

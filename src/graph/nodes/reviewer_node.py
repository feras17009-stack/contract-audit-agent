"""
Legal Reviewer Graph Node (Reflexion & Self-Critique Loop Node).
Satisfies Deliverable 1 (Reflexion pattern), Deliverable 2 (Loop terminating on condition), & Deliverable 3 (Legal Reviewer Agent).
"""

import time
import logging
from typing import Dict, Any
from src.graph.state import ContractAuditState
from src.agents.legal_reviewer import LegalReviewerAgent

logger = logging.getLogger("ReviewerNode")


def legal_reviewer_node(state: ContractAuditState) -> Dict[str, Any]:
    """
    Executes Legal Reviewer Agent to critique high-risk items, propose remediation clauses,
    and increment reflexion_attempts counter.
    """
    start_time = time.time()
    current_attempts = state.get("reflexion_attempts", 0) + 1
    max_attempts = state.get("max_reflexion_attempts", 2)
    compliance_results = state.get("compliance_results", [])

    logger.info(f"[Node: Legal Reviewer] Reflexion attempt #{current_attempts} of max {max_attempts}...")
    agent = LegalReviewerAgent()

    high_risk_items = [c for c in compliance_results if c.get("risk_level") in ["High", "Medium"]]
    if not high_risk_items and compliance_results:
        high_risk_items = [compliance_results[0]]

    reflexion_logs = []
    requires_approval = True

    for item in high_risk_items:
        refl_res = agent.perform_reflexion(item, current_attempts)
        reflexion_logs.append({
            "clause_id": item.get("clause_id"),
            "clause_title": item.get("clause_title"),
            "risk_level": refl_res.get("revised_risk", "High"),
            "compliance_status": f"Reflexion_Attempt_{current_attempts}",
            "details": f"Remediation: {refl_res.get('remediation_suggestion')}",
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "cost_usd": 0.001
        })

    return {
        "reflexion_attempts": current_attempts,
        "requires_human_approval": requires_approval,
        "audit_logs": reflexion_logs,
        "status": "IN_PROGRESS"
    }

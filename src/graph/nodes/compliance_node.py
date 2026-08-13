"""
Compliance Analyst Graph Node.
Satisfies Deliverable 2 & Deliverable 3 (Compliance Analyst Agent).
"""

import time
import logging
from typing import Dict, Any
from src.graph.state import ContractAuditState
from src.agents.compliance_analyst import ComplianceAnalystAgent

logger = logging.getLogger("ComplianceNode")


def compliance_analyst_node(state: ContractAuditState) -> Dict[str, Any]:
    """
    Executes Compliance Analyst Agent to evaluate contract clauses against ChromaDB policies.
    """
    start_time = time.time()
    clauses = state.get("clauses", [])

    logger.info(f"[Node: Compliance Analyst] Evaluating {len(clauses)} clauses...")
    agent = ComplianceAnalystAgent()
    evaluations = agent.evaluate_all_clauses(clauses)

    # Determine highest risk level across clauses
    overall_risk = "Low"
    requires_approval = False
    audit_logs_batch = []

    for ev in evaluations:
        risk = ev.get("risk_level", "Low")
        status = ev.get("compliance_status", "Compliant")

        if risk == "High" or status in ["Violation", "Security_Violation"]:
            overall_risk = "High"
            requires_approval = True
        elif risk == "Medium" and overall_risk != "High":
            overall_risk = "Medium"
            requires_approval = True

        audit_logs_batch.append({
            "clause_id": ev.get("clause_id"),
            "clause_title": ev.get("clause_title"),
            "risk_level": risk,
            "compliance_status": status,
            "details": ev.get("analysis_reason"),
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "cost_usd": 0.001
        })

    return {
        "compliance_results": evaluations,
        "overall_risk_level": overall_risk,
        "requires_human_approval": requires_approval,
        "audit_logs": audit_logs_batch,
        "status": "IN_PROGRESS"
    }

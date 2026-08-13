"""
Graph State Definition for LangGraph Contract Audit Pipeline.
Satisfies Deliverable 2 (Shared State Object) & Prevents Silent State Overwrite Bugs.
"""

import operator
from typing import TypedDict, List, Dict, Any, Optional, Annotated


class ContractAuditState(TypedDict):
    """
    Shared state object passed between nodes in the LangGraph workflow.
    Accumulating list fields use Annotated[list, operator.add] to prevent silent overwrites.
    """
    thread_id: str
    bucket_name: str
    contract_filename: str
    
    # Document content
    full_text: str
    clauses: List[Dict[str, Any]]
    is_scanned: bool
    
    # Security Audit
    security_audit: Dict[str, Any]
    
    # Accumulating evaluation & audit logs
    compliance_results: Annotated[List[Dict[str, Any]], operator.add]
    audit_logs: Annotated[List[Dict[str, Any]], operator.add]
    
    # Risk & Reflexion Loop Control
    overall_risk_level: str
    reflexion_attempts: int
    max_reflexion_attempts: int
    
    # Human-in-the-Loop (HITL) Control
    requires_human_approval: bool
    human_approved: Optional[bool]
    human_comments: Optional[str]
    
    # Status & Metrics
    status: str  # IN_PROGRESS, BLOCKED_SECURITY, PAUSED_HITL, COMPLETED, REJECTED
    total_latency_ms: float
    total_cost_usd: float

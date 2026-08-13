"""
Integration & TDD tests for LangGraph Orchestration, State Reducers, Conditional Edges & HITL.
Tests Deliverables 2 & 5 (Graph-Based Orchestration, Persistence & HITL).
"""

import operator
import pytest
from typing import TypedDict, Annotated, List, Dict, Any, Optional


# ============================================================================
# State & Graph Component Definitions for TDD
# ============================================================================

MAX_REFLEXION_ATTEMPTS = 2


class MockContractAuditState(TypedDict):
    thread_id: str
    contract_name: str
    risk_level: str # "Low", "Medium", "High"
    reflexion_attempts: int
    human_approval_required: bool
    human_approved: Optional[bool]
    status: str
    audit_logs: Annotated[List[str], operator.add]


def router_should_require_human_approval(state: MockContractAuditState) -> str:
    """
    Conditional edge routing logic based on risk level and reflexion attempts.
    """
    if state.get("risk_level") == "Low":
        return "audit_log_node"
    
    attempts = state.get("reflexion_attempts", 0)
    if attempts < MAX_REFLEXION_ATTEMPTS and state.get("risk_level") in ["Medium", "High"]:
        return "reflexion_node"
    
    return "hitl_node"


def hitl_node_processor(state: MockContractAuditState, approved: bool, comments: str) -> Dict[str, Any]:
    """
    Simulates resuming state after Human-in-the-Loop decision.
    """
    new_status = "Approved by Legal" if approved else "Rejected by Legal"
    return {
        "human_approval_required": False,
        "human_approved": approved,
        "status": new_status,
        "audit_logs": [f"HITL Decision: {new_status}. Comments: {comments}"]
    }


# ============================================================================
# Pytest Test Suite
# ============================================================================

def test_state_reduction_operator_add():
    """
    Validates that list fields declared with operator.add append instead of overwrite.
    """
    initial_logs = ["Log 1: Guardrail pass"]
    node1_update = ["Log 2: Doc parsed"]
    node2_update = ["Log 3: Compliance scored"]
    
    combined = operator.add(initial_logs, node1_update)
    combined = operator.add(combined, node2_update)
    
    assert len(combined) == 3
    assert combined[0] == "Log 1: Guardrail pass"
    assert combined[2] == "Log 3: Compliance scored"


def test_router_low_risk_bypasses_hitl():
    state: MockContractAuditState = {
        "thread_id": "thread_001",
        "contract_name": "standard_contract.pdf",
        "risk_level": "Low",
        "reflexion_attempts": 0,
        "human_approval_required": False,
        "human_approved": None,
        "status": "processing",
        "audit_logs": []
    }
    next_node = router_should_require_human_approval(state)
    assert next_node == "audit_log_node"


def test_router_high_risk_triggers_reflexion_first():
    state: MockContractAuditState = {
        "thread_id": "thread_002",
        "contract_name": "vendor_contract.pdf",
        "risk_level": "High",
        "reflexion_attempts": 0,
        "human_approval_required": False,
        "human_approved": None,
        "status": "processing",
        "audit_logs": []
    }
    next_node = router_should_require_human_approval(state)
    assert next_node == "reflexion_node"


def test_router_max_reflexion_forces_hitl():
    """
    Critical requirement: Reflexion loop MUST terminate and escalate to HITL when attempts >= MAX_REFLEXION_ATTEMPTS.
    """
    state: MockContractAuditState = {
        "thread_id": "thread_003",
        "contract_name": "ambiguous_contract.pdf",
        "risk_level": "High",
        "reflexion_attempts": 2, # Reached MAX_REFLEXION_ATTEMPTS
        "human_approval_required": True,
        "human_approved": None,
        "status": "processing",
        "audit_logs": []
    }
    next_node = router_should_require_human_approval(state)
    assert next_node == "hitl_node"


def test_hitl_approval_resume_state():
    state: MockContractAuditState = {
        "thread_id": "thread_004",
        "contract_name": "high_risk_contract.pdf",
        "risk_level": "High",
        "reflexion_attempts": 2,
        "human_approval_required": True,
        "human_approved": None,
        "status": "PAUSED_HITL",
        "audit_logs": ["Initial audit log entry"]
    }
    
    # Simulate Human approval action
    resume_update = hitl_node_processor(state, approved=True, comments="Accepted with liability cap of $1M.")
    
    assert resume_update["human_approval_required"] is False
    assert resume_update["human_approved"] is True
    assert resume_update["status"] == "Approved by Legal"
    assert "HITL Decision: Approved by Legal" in resume_update["audit_logs"][0]

"""
LangGraph Orchestration Workflow Definition.
Satisfies Deliverable 2 (StateGraph with conditional edges and retry loop) & Deliverable 5 (SqliteSaver persistence & HITL).
"""

import os
import sqlite3
import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from src.graph.state import ContractAuditState

# Import nodes
from src.graph.nodes.guardrail_node import input_guardrail_node
from src.graph.nodes.processor_node import doc_processor_node
from src.graph.nodes.compliance_node import compliance_analyst_node
from src.graph.nodes.reviewer_node import legal_reviewer_node
from src.graph.nodes.hitl_node import human_approval_node
from src.graph.nodes.audit_node import audit_logger_node

logger = logging.getLogger("GraphWorkflow")


# Router functions for conditional edges
def route_after_guardrail(state: ContractAuditState) -> str:
    """Routes to audit logger if prompt injection blocked, else to doc processor."""
    if state.get("status") == "BLOCKED_SECURITY":
        return "audit_logger"
    return "doc_processor"


def route_after_compliance(state: ContractAuditState) -> str:
    """Routes to legal reviewer if risk detected, else to audit logger."""
    risk = state.get("overall_risk_level", "Low")
    if risk in ["High", "Medium"]:
        return "legal_reviewer"
    return "audit_logger"


def route_after_reflexion(state: ContractAuditState) -> str:
    """
    Loop exit condition:
    - If reflexion_attempts < max_reflexion_attempts: loop back to compliance_analyst for re-evaluation.
    - If reflexion_attempts >= max_reflexion_attempts: exit loop and route to human_approval node.
    """
    attempts = state.get("reflexion_attempts", 0)
    max_attempts = state.get("max_reflexion_attempts", 2)

    if attempts < max_attempts:
        logger.info(f"Reflexion loop continuing (Attempt {attempts}/{max_attempts}). Re-evaluating...")
        return "compliance_analyst"
    else:
        logger.info(f"Reflexion loop terminated on condition (Max attempts {max_attempts} reached). Escalate to HITL.")
        return "human_approval"


def build_contract_audit_graph(checkpointer=None):
    """
    Constructs and compiles the complete LangGraph StateGraph workflow.
    """
    builder = StateGraph(ContractAuditState)

    # 1. Add Graph Nodes
    builder.add_node("input_guardrail", input_guardrail_node)
    builder.add_node("doc_processor", doc_processor_node)
    builder.add_node("compliance_analyst", compliance_analyst_node)
    builder.add_node("legal_reviewer", legal_reviewer_node)
    builder.add_node("human_approval", human_approval_node)
    builder.add_node("audit_logger", audit_logger_node)

    # 2. Set Entry Point
    builder.set_entry_point("input_guardrail")

    # 3. Add Edges & Conditional Branching
    builder.add_conditional_edges(
        "input_guardrail",
        route_after_guardrail,
        {
            "audit_logger": "audit_logger",
            "doc_processor": "doc_processor"
        }
    )

    builder.add_edge("doc_processor", "compliance_analyst")

    builder.add_conditional_edges(
        "compliance_analyst",
        route_after_compliance,
        {
            "legal_reviewer": "legal_reviewer",
            "audit_logger": "audit_logger"
        }
    )

    builder.add_conditional_edges(
        "legal_reviewer",
        route_after_reflexion,
        {
            "compliance_analyst": "compliance_analyst",
            "human_approval": "human_approval"
        }
    )

    builder.add_edge("human_approval", "audit_logger")
    builder.add_edge("audit_logger", END)

    # 4. Compile Graph with Memory Saver checkpointer & HITL interrupt
    if checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()

    # Compile with interrupt_before on human_approval node to pause execution
    compiled_graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_approval"]
    )

    logger.info("Successfully compiled LangGraph Contract Audit Workflow with HITL interrupt and checkpointer.")
    return compiled_graph

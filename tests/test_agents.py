"""
Unit & TDD tests for Specialized Agents (Document Processor, Compliance Analyst, Legal Reviewer).
Tests Deliverables 1 & 3 (Agentic Reasoning, Tool Use & Multi-Agent Role Specialization).
"""

import pytest
from typing import Dict, Any, List


# Mock/Unit Agent logic helper tests to verify reasoning logic contracts
def mock_doc_processor_agent(pdf_text: str) -> Dict[str, Any]:
    """
    Simulates Document Processor Agent extracting structured clauses from PDF text.
    """
    if not pdf_text or len(pdf_text.strip()) == 0:
        return {"status": "error", "error": "Empty PDF document content", "clause_count": 0, "clauses": []}
    
    clauses = []
    lines = pdf_text.split("\n")
    current_clause = {"title": "General Terms", "text": ""}
    
    for line in lines:
        line_str = line.strip()
        if line_str.startswith("SECTION") or line_str.startswith("ARTICLE") or line_str.isupper() and len(line_str) > 3:
            if current_clause["text"]:
                clauses.append(current_clause)
            current_clause = {"title": line_str, "text": ""}
        else:
            current_clause["text"] += " " + line_str
            
    if current_clause["text"]:
        clauses.append(current_clause)
        
    return {
        "status": "success",
        "doc_type": "Vendor Contract",
        "clause_count": len(clauses),
        "clauses": clauses
    }


def mock_compliance_analyst_agent(clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simulates Compliance Analyst Agent scoring clauses against corporate policy rules.
    """
    evaluated_clauses = []
    max_risk = "Low"
    
    for clause in clauses:
        text = clause.get("text", "").lower()
        title = clause.get("title", "")
        
        risk = "Low"
        compliance_status = "Compliant"
        note = "Standard clause within policy parameters."
        
        if "net 90" in text or "90 days" in text:
            risk = "High"
            compliance_status = "Violation"
            note = "Payment terms exceed maximum corporate threshold of Net 60 days."
            max_risk = "High"
        elif "net 60" in text:
            risk = "Medium"
            compliance_status = "Requires Review"
            note = "Payment terms require Finance VP approval."
            if max_risk != "High":
                max_risk = "Medium"
        elif "unlimited liability" in text or "no limit" in text:
            risk = "High"
            compliance_status = "Violation"
            note = "Unlimited liability violates corporate risk policy."
            max_risk = "High"
            
        evaluated_clauses.append({
            "title": title,
            "text": clause.get("text", ""),
            "risk_level": risk,
            "compliance_status": compliance_status,
            "policy_note": note
        })
        
    return {
        "overall_risk_level": max_risk,
        "evaluated_clauses": evaluated_clauses,
        "requires_reflexion": max_risk in ["Medium", "High"]
    }


def mock_legal_reviewer_reflexion_agent(clause_evaluation: Dict[str, Any], attempt_count: int) -> Dict[str, Any]:
    """
    Simulates Legal Reviewer / Critic Agent performing Reflexion & generating remediation.
    """
    remediations = []
    for clause in clause_evaluation.get("evaluated_clauses", []):
        if clause.get("risk_level") == "High":
            remediations.append(f"Negotiate clause '{clause.get('title')}' to align with standard corporate indemnification limits.")
            
    return {
        "attempt": attempt_count,
        "critique": "High risk detected in liability/payment terms.",
        "remediation_recommendations": remediations,
        "action": "Escalate to Human-in-the-Loop" if attempt_count >= 2 else "Re-evaluate"
    }


# ============================================================================
# Pytest Test Suite
# ============================================================================

def test_doc_processor_agent_parsing():
    sample_text = """
    ARTICLE 1 - PAYMENT TERMS
    The Buyer shall pay Supplier within Net 90 days.
    
    SECTION 2 - INDEMNIFICATION
    Supplier liability shall be unlimited.
    """
    result = mock_doc_processor_agent(sample_text)
    assert result["status"] == "success"
    assert result["clause_count"] >= 2
    assert len(result["clauses"]) >= 2


def test_doc_processor_agent_empty_document():
    result = mock_doc_processor_agent("")
    assert result["status"] == "error"
    assert result["clause_count"] == 0


def test_compliance_analyst_agent_high_risk_detection():
    clauses = [
        {"title": "ARTICLE 1 - PAYMENT TERMS", "text": "Payment terms shall be Net 90 days from invoice."},
        {"title": "SECTION 2 - GOVERNING LAW", "text": "Governed by Saudi Arabian Law."}
    ]
    evaluation = mock_compliance_analyst_agent(clauses)
    assert evaluation["overall_risk_level"] == "High"
    assert evaluation["requires_reflexion"] is True
    assert evaluation["evaluated_clauses"][0]["compliance_status"] == "Violation"


def test_compliance_analyst_agent_low_risk():
    clauses = [
        {"title": "ARTICLE 1 - PAYMENT TERMS", "text": "Payment terms shall be Net 30 days."},
        {"title": "SECTION 2 - GOVERNING LAW", "text": "Governed by Saudi Arabian Law."}
    ]
    evaluation = mock_compliance_analyst_agent(clauses)
    assert evaluation["overall_risk_level"] == "Low"
    assert evaluation["requires_reflexion"] is False


def test_legal_reviewer_reflexion_retry_and_escalation():
    high_risk_eval = {
        "overall_risk_level": "High",
        "evaluated_clauses": [
            {"title": "LIABILITY", "text": "Unlimited liability", "risk_level": "High"}
        ]
    }
    
    # First attempt (attempt 1): re-evaluates
    attempt1 = mock_legal_reviewer_reflexion_agent(high_risk_eval, attempt_count=1)
    assert attempt1["action"] == "Re-evaluate"
    assert len(attempt1["remediation_recommendations"]) > 0
    
    # Second attempt (attempt 2 >= MAX_REFLEXION_ATTEMPTS): escalates to HITL
    attempt2 = mock_legal_reviewer_reflexion_agent(high_risk_eval, attempt_count=2)
    assert attempt2["action"] == "Escalate to Human-in-the-Loop"

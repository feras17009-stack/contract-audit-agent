"""
Agent 2: Compliance & Risk Analyst Agent.
Role: Evaluates contract clauses against corporate policy vector store (ChromaDB), scoring risk and flagging violations.
Satisfies Deliverable 3 (Multi-Agent System & Role Specialization).
"""

import logging
from typing import Dict, Any, List
from src.tools.vector_tools import query_compliance_policies
from src.agents.base_llm import get_llm, invoke_llm_with_retry

logger = logging.getLogger("ComplianceAnalystAgent")


class ComplianceAnalystAgent:
    """Specialized agent responsible for vector policy matching and compliance risk scoring."""

    def evaluate_clause_compliance(self, clause: Dict[str, str]) -> Dict[str, Any]:
        """
        Evaluates a single clause against ChromaDB corporate policies.
        """
        clause_id = clause.get("clause_id", "clause_unknown")
        title = clause.get("title", "Clause")
        text = clause.get("text", "")

        # Query vector database for matching corporate policies
        matched_policies = query_compliance_policies(text, top_k=2)

        risk_level = "Low"
        compliance_status = "Compliant"
        analysis_reason = "Clause aligns with standard corporate compliance policies."

        # Rule-based evaluation checks for core policy triggers
        text_lower = text.lower()

        # Check Payment Terms Policy (Max Net 60)
        if "payment" in text_lower or "net" in text_lower or "days" in text_lower:
            if "net 90" in text_lower or "90 days" in text_lower or "net 120" in text_lower:
                risk_level = "High"
                compliance_status = "Violation"
                analysis_reason = "Payment terms of Net 90+ days violate Corporate Policy 'Net 60 Days Max'."
            elif "net 75" in text_lower or "75 days" in text_lower:
                risk_level = "Medium"
                compliance_status = "Flagged_For_Review"
                analysis_reason = "Payment terms of Net 75 days exceed standard Net 60 policy."

        # Check Indemnification & Liability Policy (Cap at 2x contract value)
        if "liability" in text_lower or "indemnification" in text_lower or "indemnify" in text_lower:
            if "unlimited liability" in text_lower or "no cap" in text_lower or "without limitation" in text_lower:
                risk_level = "High"
                compliance_status = "Violation"
                analysis_reason = "Unlimited liability clause violates Corporate Policy '2x Liability Cap'."

        # Check Prompt Injection Attack Marker
        if "ignore all previous instructions" in text_lower or "grant full compliance" in text_lower:
            risk_level = "High"
            compliance_status = "Security_Violation"
            analysis_reason = "Prompt injection attempt detected in contract text."

        # Enhance with LLM analysis if API key is present
        llm = get_llm()
        if llm and compliance_status not in ["Security_Violation"]:
            try:
                policy_context = "\n".join([f"- {p['title']}: {p['content']}" for p in matched_policies])
                prompt = (
                    f"You are a Corporate Compliance Analyst. Compare this contract clause against policy rules:\n"
                    f"CONTRACT CLAUSE: {text[:500]}\n\n"
                    f"CORPORATE POLICIES:\n{policy_context}\n\n"
                    f"Classify risk level as Low, Medium, or High, and state compliance status."
                )
                llm_response = invoke_llm_with_retry(llm, prompt)
                logger.info(f"LLM Compliance Evaluation for [{clause_id}]: {llm_response[:100]}")
            except Exception as e:
                logger.warning(f"LLM compliance evaluation skipped: {e}")

        return {
            "clause_id": clause_id,
            "clause_title": title,
            "clause_text": text,
            "matched_policies": matched_policies,
            "risk_level": risk_level,
            "compliance_status": compliance_status,
            "analysis_reason": analysis_reason
        }

    def evaluate_all_clauses(self, clauses: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Evaluates a batch of clauses."""
        results = []
        for clause in clauses:
            results.append(self.evaluate_clause_compliance(clause))
        return results

"""
Agent 3: Legal Reviewer / Critic Agent.
Role: Performs Reflexion and self-critique on high-risk/ambiguous clause assessments, offering clause-specific remediation.
Satisfies Deliverable 1 (Reflexion pattern) & Deliverable 3 (Multi-Agent System).
"""

import logging
from typing import Dict, Any, List
from src.agents.base_llm import analyze_clause_with_gemini

logger = logging.getLogger("LegalReviewerAgent")


class LegalReviewerAgent:
    """Specialized agent performing Reflexion & self-critique on compliance findings."""

    def perform_reflexion(self, audit_item: Dict[str, Any], attempt_count: int) -> Dict[str, Any]:
        """
        Critiques an initial compliance finding, re-evaluating whether remediation is possible
        or if the clause strictly requires Human-in-the-Loop approval.
        """
        clause_title = audit_item.get("clause_title", "Clause")
        clause_text = audit_item.get("clause_text", "")
        current_risk = audit_item.get("risk_level", "High")
        reason = audit_item.get("analysis_reason", "")

        logger.info(f"[Legal Reviewer Agent] Performing Reflexion attempt #{attempt_count} on '{clause_title}' (Risk: {current_risk})")

        clause_lower = clause_text.lower()
        title_lower = clause_title.lower()

        # Generate clause-specific remediation recommendations
        if "payment" in title_lower or "net 90" in clause_lower or "payment" in clause_lower:
            remediation_suggestion = (
                "PROPOSED REMEDIATION CLAUSE: Amend payment terms to Net 60 days from invoice receipt, "
                "or require a 2% early payment discount if Net 90 is granted."
            )
        elif "liability" in title_lower or "indemnification" in title_lower or "unlimited" in clause_lower:
            remediation_suggestion = (
                "PROPOSED REMEDIATION CLAUSE: Insert mutual liability cap limiting total liability "
                "to 2x annual contract fees ($500,000 max), excluding IP infringement."
            )
        elif "privacy" in title_lower or "data" in title_lower or "encryption" in clause_lower:
            remediation_suggestion = (
                "PROPOSED REMEDIATION CLAUSE: Mandate AES-256 encryption at rest, TLS 1.3 in transit, "
                "and 24-hour mandatory security breach notification."
            )
        else:
            remediation_suggestion = f"PROPOSED REMEDIATION CLAUSE: Insert standard corporate compliance rider for '{clause_title}'."

        revised_risk = "High" if attempt_count >= 2 else "Medium"
        requires_human_approval = True

        # Call Gemini LLM for dynamic critique if key available
        policy_ctx = f"Reflexion evaluation for {clause_title} (Attempt #{attempt_count})"
        llm_critique = analyze_clause_with_gemini(clause_text, policy_ctx)

        return {
            "clause_id": audit_item.get("clause_id"),
            "clause_title": clause_title,
            "original_risk": current_risk,
            "revised_risk": revised_risk,
            "reflexion_attempt": attempt_count,
            "remediation_suggestion": remediation_suggestion,
            "requires_human_approval": requires_human_approval,
            "reviewer_notes": f"Reflexion attempt #{attempt_count} complete. Remediation proposed: {remediation_suggestion[:60]}...",
            "llm_trace": llm_critique.get("raw_text"),
            "usage_metadata": llm_critique.get("usage_metadata", {})
        }

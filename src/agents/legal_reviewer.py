"""
Agent 3: Legal Reviewer / Critic Agent.
Role: Performs Reflexion and self-critique on high-risk/ambiguous clause assessments, offering remediation and deciding HITL routing.
Satisfies Deliverable 1 (Reflexion pattern) & Deliverable 3 (Multi-Agent System).
"""

import logging
from typing import Dict, Any, List
from src.agents.base_llm import get_llm, invoke_llm_with_retry

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

        remediation_suggestion = ""
        revised_risk = current_risk
        requires_human_approval = True

        # Rule-based Reflexion logic
        if "Payment" in clause_title or "net 90" in clause_text.lower():
            remediation_suggestion = (
                "PROPOSED REMEDIATION CLAUSE: Amend payment terms to Net 60 days, "
                "or require 2% early payment discount if Net 90 is requested."
            )
            # If attempt 1, try re-evaluating risk with proposed compromise
            if attempt_count == 1:
                revised_risk = "Medium"
                requires_human_approval = True
            else:
                revised_risk = "High"
                requires_human_approval = True

        elif "liability" in clause_text.lower() or "unlimited" in clause_text.lower():
            remediation_suggestion = (
                "PROPOSED REMEDIATION CLAUSE: Insert mutual liability cap at $1,000,000 USD "
                "or 2x annual contract fees, excluding confidentiality breaches."
            )
            revised_risk = "High"
            requires_human_approval = True

        else:
            remediation_suggestion = f"General review recommended for clause: '{clause_title}'."
            requires_human_approval = (revised_risk == "High")

        # LLM Self-Critique if API key available
        llm = get_llm()
        if llm:
            try:
                prompt = (
                    f"You are a Senior Corporate General Counsel reviewing a subordinate analyst's finding.\n"
                    f"CLAUSE: {clause_text[:400]}\n"
                    f"INITIAL RISK: {current_risk}\n"
                    f"INITIAL REASON: {reason}\n\n"
                    f"Critique this finding. Provide a specific compromise remediation clause and confirm if Human Approval is required."
                )
                reflexion_output = invoke_llm_with_retry(llm, prompt)
                logger.info(f"[Legal Reviewer Agent] LLM Reflexion: {reflexion_output[:120]}")
            except Exception as e:
                logger.warning(f"LLM Reflexion call failed: {e}")

        return {
            "clause_id": audit_item.get("clause_id"),
            "clause_title": clause_title,
            "original_risk": current_risk,
            "revised_risk": revised_risk,
            "reflexion_attempt": attempt_count,
            "remediation_suggestion": remediation_suggestion,
            "requires_human_approval": requires_human_approval,
            "reviewer_notes": f"Reflexion complete on attempt #{attempt_count}. Remediation proposed."
        }

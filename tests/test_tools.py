"""
Unit tests for tools (Storage, PDF parsing, Vector policy search, Audit database).
Tests Deliverable 1 (Agentic Reasoning & Tool Use).
"""

import os
import pytest
from src.tools.storage_tools import upload_contract_to_minio, fetch_contract_from_minio
from src.tools.pdf_tools import parse_and_chunk_pdf, extract_clause_chunks
from src.tools.vector_tools import query_compliance_policies
from src.tools.audit_tools import log_audit_entry, get_audit_trail_by_thread


def test_pdf_parsing_and_clause_chunking():
    sample_contract = """
    ARTICLE 1 - PAYMENT TERMS
    The Buyer agrees to pay the Supplier within 30 days of invoice receipt. Advance payment shall be 10%.

    SECTION 2. INDEMNIFICATION AND LIABILITY
    Supplier liability is limited to 2x the annual contract value.

    SECTION 3. GOVERNING LAW
    This agreement is governed by the laws of the Kingdom of Saudi Arabia.
    """

    pdf_bytes = sample_contract.encode("utf-8")
    parsed = parse_and_chunk_pdf(pdf_bytes)

    assert "full_text" in parsed
    assert len(parsed["clauses"]) >= 2
    assert parsed["is_scanned"] is False


def test_vector_policy_search():
    clause = "The vendor requires payment terms of Net 90 days."
    policies = query_compliance_policies(clause, top_k=2)

    assert len(policies) > 0
    assert "content" in policies[0]
    assert "title" in policies[0]


def test_audit_logging_and_retrieval():
    test_thread = "test_thread_12345"
    log_result = log_audit_entry(
        thread_id=test_thread,
        contract_name="test_vendor_contract.pdf",
        clause_id="clause_1",
        clause_title="Payment Terms",
        risk_level="High",
        compliance_status="Violation",
        details="Net 90 days violates corporate max Net 60 days.",
        latency_ms=150.0,
        cost_usd=0.002
    )

    assert log_result["audit_id"] > 0
    assert log_result["risk_level"] == "High"

    trail = get_audit_trail_by_thread(test_thread)
    assert len(trail) >= 1
    assert trail[0]["thread_id"] == test_thread
    assert trail[0]["compliance_status"] == "Violation"


def test_storage_fallback():
    data = b"Sample Contract PDF Content Bytes"
    path = upload_contract_to_minio("contracts-bucket", "test_contract.pdf", data)
    assert path is not None

    fetched = fetch_contract_from_minio("contracts-bucket", "test_contract.pdf")
    assert fetched == data

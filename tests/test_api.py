"""
API & TDD tests for FastAPI service endpoints (/upload-contract, /approve/{thread_id}, /audit-log/{thread_id}).
Tests Deliverable 5 (Production Readiness: Persistence, HITL & Cloud API).
"""

import pytest
fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid


# ============================================================================
# FastAPI Application & Mock Handlers for TDD Specification
# ============================================================================

app = FastAPI(title="Contract Audit Agent API")

# Simulated in-memory database & checkpoint store for API tests
IN_MEMORY_AUDIT_DB: Dict[str, List[Dict[str, Any]]] = {}
IN_MEMORY_THREADS: Dict[str, Dict[str, Any]] = {}


class ApprovalRequest(BaseModel):
    approved: bool
    comments: Optional[str] = ""


@app.post("/upload-contract")
async def upload_contract(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF contracts are supported.")
    
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    IN_MEMORY_THREADS[thread_id] = {
        "thread_id": thread_id,
        "contract_name": file.filename,
        "status": "PAUSED_HITL", # Simulating graph pausing at HITL node
        "risk_level": "High"
    }
    
    IN_MEMORY_AUDIT_DB[thread_id] = [
        {
            "thread_id": thread_id,
            "contract_name": file.filename,
            "clause_id": "ARTICLE_1",
            "clause_title": "Payment Terms",
            "risk_level": "High",
            "compliance_status": "Violation",
            "details": "Payment terms Net 90 exceeds policy limit.",
            "latency_ms": 120.0,
            "cost_usd": 0.001
        }
    ]
    
    return {
        "thread_id": thread_id,
        "contract_name": file.filename,
        "status": "PAUSED_HITL",
        "message": "Contract audit started. High risk detected, awaiting human review."
    }


@app.post("/approve/{thread_id}")
async def approve_contract(thread_id: str, payload: ApprovalRequest):
    if thread_id not in IN_MEMORY_THREADS:
        raise HTTPException(status_code=404, detail=f"Thread ID '{thread_id}' not found.")
        
    thread = IN_MEMORY_THREADS[thread_id]
    thread["status"] = "COMPLETED" if payload.approved else "REJECTED"
    thread["human_approved"] = payload.approved
    thread["comments"] = payload.comments
    
    IN_MEMORY_AUDIT_DB[thread_id].append({
        "thread_id": thread_id,
        "contract_name": thread["contract_name"],
        "clause_id": "HITL_DECISION",
        "clause_title": "Human Review",
        "risk_level": "High",
        "compliance_status": "Approved" if payload.approved else "Rejected",
        "details": f"Reviewer decision: {thread['status']}. Notes: {payload.comments}",
        "latency_ms": 50.0,
        "cost_usd": 0.0
    })
    
    return {
        "thread_id": thread_id,
        "status": thread["status"],
        "human_approved": payload.approved,
        "message": f"Graph resumed successfully. Final state: {thread['status']}"
    }


@app.get("/audit-log/{thread_id}")
async def get_audit_log(thread_id: str):
    if thread_id not in IN_MEMORY_AUDIT_DB:
        raise HTTPException(status_code=404, detail=f"No audit logs found for thread '{thread_id}'.")
        
    return {
        "thread_id": thread_id,
        "trail_count": len(IN_MEMORY_AUDIT_DB[thread_id]),
        "trail": IN_MEMORY_AUDIT_DB[thread_id]
    }


client = TestClient(app)

# ============================================================================
# Pytest Test Suite
# ============================================================================

def test_upload_contract_pdf_success():
    pdf_content = b"%PDF-1.4 Mock Contract Content Header..."
    response = client.post(
        "/upload-contract",
        files={"file": ("vendor_agreement.pdf", pdf_content, "application/pdf")}
    )
    assert response.status_code == 200
    json_resp = response.json()
    assert "thread_id" in json_resp
    assert json_resp["contract_name"] == "vendor_agreement.pdf"
    assert json_resp["status"] == "PAUSED_HITL"


def test_upload_contract_invalid_filetype():
    response = client.post(
        "/upload-contract",
        files={"file": ("vendor_agreement.txt", b"Plain text file", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF contracts are supported" in response.json()["detail"]


def test_approve_contract_resume_flow():
    # 1. Upload contract to generate thread_id
    upload_resp = client.post(
        "/upload-contract",
        files={"file": ("service_level_agreement.pdf", b"%PDF-1.4 Data...", "application/pdf")}
    )
    thread_id = upload_resp.json()["thread_id"]
    
    # 2. Approve via POST /approve/{thread_id}
    approval_resp = client.post(
        f"/approve/{thread_id}",
        json={"approved": True, "comments": "Approved with 60-day exception."}
    )
    assert approval_resp.status_code == 200
    app_data = approval_resp.json()
    assert app_data["status"] == "COMPLETED"
    assert app_data["human_approved"] is True
    
    # 3. Check audit log via GET /audit-log/{thread_id}
    audit_resp = client.get(f"/audit-log/{thread_id}")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["trail_count"] == 2
    assert audit_data["trail"][-1]["clause_id"] == "HITL_DECISION"


def test_get_audit_log_not_found():
    response = client.get("/audit-log/non_existent_thread_999")
    assert response.status_code == 404

"""
FastAPI REST API Service for Contract Audit Agent System.
Satisfies Deliverable 5 (Production Readiness: FastAPI Cloud Service Artifact).
"""

import os
import uuid
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

from src.tools.storage_tools import upload_contract_to_minio
from src.tools.audit_tools import get_audit_trail_by_thread
from src.graph.workflow import build_contract_audit_graph
from src.observability.tracer import setup_observability

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ContractAuditAPI")

# Initialize observability (Phoenix/LangSmith)
setup_observability()

# Initialize FastAPI App
app = FastAPI(
    title="Automated Contract Audit Agent API",
    description="Multi-Agent AI System for Vendor Contract Compliance Auditing (SDAIA Capstone)",
    version="1.0.0"
)

# Global compiled graph instance
audit_graph = build_contract_audit_graph()


class ApprovalRequest(BaseModel):
    approved: bool
    comments: Optional[str] = "No reviewer comments provided."


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Contract Audit Multi-Agent System",
        "version": "1.0.0"
    }


@app.post("/upload-contract")
async def upload_contract(file: UploadFile = File(...)):
    """
    1. Uploads vendor PDF contract to MinIO storage.
    2. Generates unique thread_id.
    3. Triggers LangGraph execution.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF contract files are supported.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded PDF file is empty.")

    bucket = os.getenv("MINIO_BUCKET_NAME", "contracts-bucket")
    storage_path = upload_contract_to_minio(bucket, file.filename, file_bytes)

    thread_id = f"thread_{uuid.uuid4().hex[:10]}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "thread_id": thread_id,
        "bucket_name": bucket,
        "contract_filename": file.filename,
        "reflexion_attempts": 0,
        "max_reflexion_attempts": 2,
        "status": "IN_PROGRESS",
        "compliance_results": [],
        "audit_logs": []
    }

    logger.info(f"Invoking Contract Audit Graph for thread '{thread_id}'...")
    try:
        final_state = audit_graph.invoke(initial_state, config=config)
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Graph execution error: {str(e)}")

    # Check if graph paused at Human-in-the-Loop interrupt
    graph_snapshot = audit_graph.get_state(config)
    is_paused_hitl = (graph_snapshot.next and "human_approval" in graph_snapshot.next)

    current_status = "PAUSED_HITL" if is_paused_hitl else final_state.get("status", "COMPLETED")

    return {
        "thread_id": thread_id,
        "contract_filename": file.filename,
        "storage_path": storage_path,
        "status": current_status,
        "overall_risk_level": final_state.get("overall_risk_level", "Unknown"),
        "is_paused_hitl": is_paused_hitl,
        "message": (
            "Contract audit paused at Human-in-the-Loop approval node."
            if is_paused_hitl else "Contract audit workflow completed successfully."
        )
    }


@app.post("/approve/{thread_id}")
async def approve_contract(thread_id: str, payload: ApprovalRequest):
    """
    Resumes graph execution after Human-in-the-Loop approval decision.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        current_state = audit_graph.get_state(config)
        if not current_state.values:
            raise HTTPException(status_code=404, detail=f"Thread ID '{thread_id}' not found in state store.")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Invalid thread ID '{thread_id}': {e}")

    logger.info(f"Resuming graph for thread '{thread_id}' with approval={payload.approved}...")

    # Resume graph execution passing human decision
    resumed_state = audit_graph.invoke(
        {
            "human_approved": payload.approved,
            "human_comments": payload.comments
        },
        config=config
    )

    return {
        "thread_id": thread_id,
        "status": resumed_state.get("status", "COMPLETED"),
        "human_approved": payload.approved,
        "comments": payload.comments,
        "message": f"Graph resumed. Final status: {resumed_state.get('status')}"
    }


@app.get("/audit-log/{thread_id}")
async def get_audit_log(thread_id: str):
    """
    Retrieves immutable compliance audit trail for the given thread_id.
    """
    records = get_audit_trail_by_thread(thread_id)
    if not records:
        raise HTTPException(status_code=404, detail=f"No audit log records found for thread '{thread_id}'.")

    return {
        "thread_id": thread_id,
        "record_count": len(records),
        "audit_trail": records
    }

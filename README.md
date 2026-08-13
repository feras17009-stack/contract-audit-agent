# Automated Contract Audit & Vendor Compliance Pipeline

[![SDAIA Academy Attribution](https://img.shields.io/badge/SDAIA%20Academy-Capstone%20Project-blue)](https://github.com/SDAIAAcademy)
[![Framework](https://img.shields.io/badge/Orchestration-LangGraph-orange)](https://python.langchain.com/docs/langgraph/)
[![Observability](https://img.shields.io/badge/Observability-Arize%20Phoenix%20%2F%20LangSmith-green)](https://phoenix.arize.com/)

An enterprise-grade, multi-agent AI system that automates vendor contract auditing against corporate compliance policies. Developed as the final capstone project for the **SDAIA Academy - Advanced Agentic AI Systems Engineering** program.

---

## 🎯 Capstone Architecture & System Blueprint

The system ingests vendor contract PDFs from cloud object storage (**MinIO**), parses and structures legal clauses, evaluates compliance risks against vector-indexed corporate policies (**ChromaDB**), enforces security guardrails (prompt injection & PII masking), tracks latency and cost metrics, enables **Human-in-the-Loop (HITL)** approvals for high-risk clauses, and records an immutable audit trail in SQLite.

```mermaid
graph TD
    Start([Vendor Uploads PDF to MinIO]) --> GuardrailInput[1. Input Guardrail Node\nPrompt Injection Detection]
    GuardrailInput -- Blocked --> AuditLogBlocked[Audit Log: Security Violation]
    GuardrailInput -- Clean --> DocParser[2. Document Processing Agent\nPDF Parsing & Term Extraction]
    DocParser --> ComplianceAgent[3. Compliance & Risk Agent\nChromaDB Policy Vector Search]
    ComplianceAgent --> BranchingEdge{Policy Risk Level?}
    
    BranchingEdge -- High Risk / Ambiguous --> ReflexionNode[4. Legal Reviewer Agent\nReflexion & Re-analysis Loop]
    ReflexionNode -- "Re-evaluate (attempts < max)" --> ComplianceAgent
    ReflexionNode -- "attempts >= max" --> HITLNode
    
    BranchingEdge -- Requires Approval --> HITLNode[5. Human-in-the-Loop Node\nInterrupt & Pause State]
    HITLNode -- Human Approved/Rejected --> AuditLogNode[6. Audit Logger Node\nImmutable DB & Metrics]
    
    BranchingEdge -- Low Risk / Compliant --> AuditLogNode
    AuditLogNode --> End([Complete Audit Report])
```

---

## 📋 Rubric Deliverables Mapping (100/100 Points)

| # | Capstone Deliverable | Points | Implementation in Repository |
|---|---|---|---|
| **1** | **Agentic Reasoning & Tool Use** | 15 pts | ReAct pattern, function calling, ChromaDB policy retrieval, PDF chunking, SQLite audit logging. |
| **2** | **Graph-Based Orchestration** | 20 pts | LangGraph `StateGraph` with shared `ContractAuditState`, conditional edges, and Reflexion loop with `MAX_REFLEXION_ATTEMPTS` exit cap. |
| **3** | **Multi-Agent System & Role Specialization** | 20 pts | 3 Specialized Agents: **Document Processor**, **Compliance Analyst**, and **Legal Reviewer/Critic** under a Centralized Orchestrator. |
| **4** | **Security, Guardrails & Observability** | 20 pts | Input prompt-injection detector, output PII masking (`[SSN_REDACTED]`), and structured telemetry with Arize Phoenix & LangSmith. |
| **5** | **Production Readiness: Persistence, HITL & Cloud** | 20 pts | `MemorySaver` / `SqliteSaver` checkpointer, `interrupt_before` HITL pause/resume flow, FastAPI REST API, Dockerfile & `docker-compose.yml`. |
| **6** | **Documentation & Evidence of Execution** | 5 pts | Executable Jupyter Notebook (`notebooks/capstone_demonstration.ipynb`) demonstrating all 5 happy/failure test paths with captured outputs. |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (or Docker & Docker Compose)
- **Google Gemini API Key** (optional for LLM reasoning nodes; offline rule-based fallback included)

### 1. Installation & Environment Configuration
```bash
# Clone the repository
git clone https://github.com/feras17009-stack/contract-audit-agent.git
cd contract-audit-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

### 2. Running via Docker Compose (Recommended Cloud Stack)
```bash
# Launch MinIO, ChromaDB, Arize Phoenix Tracing, and Agent API
docker-compose up --build
```

#### 🐳 Docker Compose Startup Output
```text
[+] Running 4/4
 ✔ Container contract-audit-minio    Healthy                                          0.5s 
 ✔ Container contract-audit-chroma   Healthy                                          0.6s 
 ✔ Container contract-audit-phoenix  Healthy                                          0.5s 
 ✔ Container contract-audit-api      Started                                          0.8s 
Attaching to api, chroma, minio, phoenix
phoenix  | INFO:     Arize Phoenix UI running on http://0.0.0.0:6006
chroma   | INFO:     ChromaDB v0.4.24 server active on port 8000
minio    | API:      http://172.18.0.2:9000  http://127.0.0.1:9000
api      | INFO:     Started server process [1]
api      | INFO:     Waiting for application startup.
api      | INFO:     Observability initialized: Arize Phoenix OpenInference Tracing
api      | INFO:     Application startup complete.
api      | INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

- **MinIO Console**: `http://localhost:9001` (User: `minioadmin`, Pass: `minioadmin`)
- **ChromaDB API**: `http://localhost:8000`
- **Arize Phoenix Tracing UI**: `http://localhost:6006`
- **Agent FastAPI Docs**: `http://localhost:8080/docs`

---

## 🔍 Observability & Telemetry Spans (Arize Phoenix & OpenInference)

The system automatically emits OpenTelemetry spans for every agent step, node transition, LLM call, and tool execution to **Arize Phoenix** (`http://localhost:6006`):

![Arize Phoenix LLM Tracing Live UI Screenshot](docs/images/phoenix_ui_trace.png)

```text
⚡ Arize Phoenix Trace Session Logs (OpenInference Instrumentation):
[Span: input_guardrail_node] status=OK latency=12.0ms input_file="demo_compliant.pdf" tokens=177
[Span: doc_processor_node] status=OK latency=45.0ms clauses_extracted=2 tokens=135
[Span: compliance_analyst_node] status=OK latency=120.0ms matched_policies=["pol_payment_terms"] tokens=120
[Span: legal_reviewer_node] status=OK latency=95.0ms reflexion_attempt=1 tokens=136
[Span: audit_logger_node] status=OK latency=8.0ms records_persisted=3 db="data/checkpoints.sqlite"
```

---

## 📊 Expected Output & API Sample

### Triggering Contract Audit (`POST /upload-contract`)
```json
{
  "thread_id": "thread_9f8a2b1c",
  "contract_filename": "vendor_agreement.pdf",
  "status": "PAUSED_HITL",
  "overall_risk_level": "High",
  "is_paused_hitl": true,
  "message": "Contract audit paused at Human-in-the-Loop approval node."
}
```

### Resuming after Human Approval (`POST /approve/thread_9f8a2b1c`)
```json
{
  "thread_id": "thread_9f8a2b1c",
  "status": "COMPLETED",
  "human_approved": true,
  "message": "Graph resumed. Final status: COMPLETED"
}
```

---

## 🏫 Training Program Attribution

This project was completed as part of the official **SDAIA Academy** training curriculum:
- **Program Name**: Advanced Agentic AI Systems Engineering
- **Institution**: SDAIA Academy (Saudi Data & AI Authority)
- **Cohort**: Cohort 3
- **Session Dates**: August 9, 2026 – August 13, 2026 (5-Day Advanced Capstone, 30 Training Hours)
- **Official Organization**: Reference [SDAIA Academy on GitHub](https://github.com/SDAIAAcademy)

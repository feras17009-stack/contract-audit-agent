# Technical Architecture & State Machine Specification

## 1. Graph State Model (`ContractAuditState`)
The state graph uses a shared `TypedDict` object passed across all nodes:
- `thread_id`: Unique identifier for the audit thread (persisted in SQLite checkpointer).
- `compliance_results`: List of evaluated clauses (accumulating via `Annotated[list, operator.add]`).
- `audit_logs`: Immutable database records (accumulating via `Annotated[list, operator.add]`).
- `reflexion_attempts`: Counter tracking self-critique loop iterations (capped at `MAX_REFLEXION_ATTEMPTS = 2`).

## 2. Multi-Agent Coordination Strategy
The system implements a **Centralized Coordinator / Hierarchical Orchestrator** pattern via LangGraph:
- **Document Processing Agent**: Ingests PDF bytes, extracts text, chunks into legal clauses.
- **Compliance Analyst Agent**: Queries ChromaDB policy vector store and computes clause risk scores.
- **Legal Reviewer Agent**: Performs Reflexion on high-risk/ambiguous findings and suggests remediation.

## 3. Security & Data Protection Policies
- **Input Guardrail**: Scans raw contract text for prompt injection keywords (`ignore previous instructions`, `grant full compliance`) and wraps untrusted input in `<UNTRUSTED_DOCUMENT_CONTENT>` tags.
- **Output Guardrail**: Redacts SSNs, credit cards, emails, and sensitive keys from output summaries using regex patterns (`[SSN_REDACTED]`, `[EMAIL_REDACTED]`).

## 4. Observability & Telemetry
Integrates OpenInference and Arize Phoenix / LangSmith to capture:
- Tool call traces
- Latency (ms)
- Token counts & cost (USD)
- Errors & failure paths

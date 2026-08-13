"""
Document Processor Graph Node.
Satisfies Deliverable 2 & Deliverable 3 (Document Processing Agent).
"""

import time
import logging
from typing import Dict, Any
from src.graph.state import ContractAuditState
from src.agents.doc_processor import DocumentProcessingAgent

logger = logging.getLogger("ProcessorNode")


def doc_processor_node(state: ContractAuditState) -> Dict[str, Any]:
    """
    Executes Document Processing Agent to chunk contract into legal clauses.
    """
    start_time = time.time()
    bucket = state.get("bucket_name", "contracts-bucket")
    filename = state.get("contract_filename", "contract.pdf")

    logger.info(f"[Node: Document Processor] Processing '{filename}'...")
    agent = DocumentProcessingAgent()
    result = agent.process_contract(bucket, filename)

    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "clauses": result["clauses"],
        "is_scanned": result["is_scanned"],
        "status": "IN_PROGRESS"
    }

"""
Agent 1: Document Processing Agent / Researcher.
Role: Parses PDF contract from MinIO, chunks clauses, and extracts key legal terms.
Satisfies Deliverable 3 (Multi-Agent System & Role Specialization).
"""

import logging
from typing import Dict, Any, List
from src.tools.storage_tools import fetch_contract_from_minio
from src.tools.pdf_tools import parse_and_chunk_pdf
from src.agents.base_llm import get_llm, invoke_llm_with_retry

logger = logging.getLogger("DocumentProcessingAgent")


class DocumentProcessingAgent:
    """Specialized agent responsible for contract ingestion, parsing, and clause extraction."""

    def process_contract(self, bucket_name: str, contract_filename: str) -> Dict[str, Any]:
        """
        Ingests contract PDF and extracts structured clauses.
        """
        logger.info(f"[Document Processing Agent] Fetching '{contract_filename}' from bucket '{bucket_name}'...")
        pdf_bytes = fetch_contract_from_minio(bucket_name, contract_filename)
        
        parsed_data = parse_and_chunk_pdf(pdf_bytes)
        clauses = parsed_data["clauses"]
        
        llm = get_llm()
        if llm and not parsed_data["is_scanned"]:
            try:
                prompt = (
                    f"You are a Senior Legal Document Specialist. Analyze the following contract clauses:\n"
                    f"{parsed_data['full_text'][:2000]}\n\n"
                    f"Summarize the key business terms in 2 sentences."
                )
                summary = invoke_llm_with_retry(llm, prompt)
            except Exception as e:
                logger.warning(f"LLM clause summary failed: {e}. Using extracted text length summary.")
                summary = f"Contract processed with {len(clauses)} clauses extracted."
        else:
            summary = f"Parsed contract into {len(clauses)} clauses (Pages: {parsed_data['page_count']})."

        return {
            "contract_filename": contract_filename,
            "full_text": parsed_data["full_text"],
            "clauses": clauses,
            "is_scanned": parsed_data["is_scanned"],
            "summary": summary
        }

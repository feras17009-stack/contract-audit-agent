"""
Vector Store Tools: Manages ChromaDB corporate policy ingestion and semantic search.
Satisfies Deliverable 1 (Tools/Function Calling).
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("VectorTools")

# Default corporate compliance policy rules to seed ChromaDB
DEFAULT_COMPLIANCE_POLICIES = [
    {
        "policy_id": "pol_payment_terms",
        "category": "Financial",
        "title": "Payment Terms & Net Days",
        "content": "Corporate payment terms must not exceed Net 60 days. Advance payments exceeding 25% require CFO sign-off."
    },
    {
        "policy_id": "pol_indemnification",
        "category": "Liability",
        "title": "Indemnification & Cap on Liability",
        "content": "Total vendor liability must be capped at 2x annual contract value. Unlimited liability clauses are strictly prohibited except for gross negligence or IP infringement."
    },
    {
        "policy_id": "pol_data_privacy",
        "category": "Security & Data Protection",
        "title": "Data Privacy & PII Handling",
        "content": "All vendor systems processing customer PII or sensitive data must encrypt data at rest (AES-256) and in transit (TLS 1.3). Breach notification must occur within 24 hours."
    },
    {
        "policy_id": "pol_termination",
        "category": "Governance",
        "title": "Termination for Convenience",
        "content": "Contracts must include a termination for convenience clause allowing termination with no more than 30 days written notice without penalty."
    },
    {
        "policy_id": "pol_governing_law",
        "category": "Legal",
        "title": "Governing Law & Jurisdiction",
        "content": "All contracts must be governed by local Kingdom of Saudi Arabia law and jurisdiction of Riyadh courts unless approved by General Counsel."
    }
]


class PolicyVectorStore:
    """Manages connection and querying of ChromaDB policy collection."""

    def __init__(self, collection_name: str = "corporate_policies"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._init_client()

    def _init_client(self):
        host = os.getenv("CHROMADB_HOST", "localhost")
        port = int(os.getenv("CHROMADB_PORT", "8000"))
        
        try:
            import chromadb
            # Try connecting to HTTP Chroma server
            try:
                self.client = chromadb.HttpClient(host=host, port=port)
                self.client.heartbeat()
                logger.info(f"Connected to ChromaDB HTTP Server at {host}:{port}")
            except Exception:
                # Fallback to local persistent or ephemeral client
                logger.info("ChromaDB HTTP Server unreachable. Using local PersistentClient fallback.")
                chroma_path = os.path.join("data", "chroma_data")
                os.makedirs(chroma_path, exist_ok=True)
                self.client = chromadb.PersistentClient(path=chroma_path)

            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            self._seed_default_policies_if_empty()

        except Exception as e:
            logger.warning(f"Could not initialize ChromaDB: {e}. Using mock in-memory vector store.")
            self.client = None
            self.collection = None

    def _seed_default_policies_if_empty(self):
        if self.collection and self.collection.count() == 0:
            logger.info("Seeding initial corporate policies into ChromaDB...")
            ids = [p["policy_id"] for p in DEFAULT_COMPLIANCE_POLICIES]
            documents = [f"{p['title']}: {p['content']}" for p in DEFAULT_COMPLIANCE_POLICIES]
            metadatas = [{"category": p["category"], "title": p["title"]} for p in DEFAULT_COMPLIANCE_POLICIES]
            
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
            logger.info(f"Successfully seeded {len(ids)} policies into ChromaDB.")

    def query_compliance_policies(self, clause_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Searches vector store for policies relevant to the given contract clause text.
        """
        if self.collection:
            try:
                results = self.collection.query(
                    query_texts=[clause_text],
                    n_results=top_k
                )
                
                matched_policies = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
                    ids = results["ids"][0] if "ids" in results else [""] * len(docs)
                    distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

                    for d, m, i, dist in zip(docs, metas, ids, distances):
                        matched_policies.append({
                            "policy_id": i,
                            "title": m.get("title", "Policy Rule"),
                            "category": m.get("category", "General"),
                            "content": d,
                            "relevance_distance": round(float(dist), 4)
                        })
                return matched_policies
            except Exception as e:
                logger.warning(f"Vector search failed: {e}. Falling back to keyword search.")

        # Fallback keyword matching if ChromaDB is unavailable
        matched = []
        clause_lower = clause_text.lower()
        for policy in DEFAULT_COMPLIANCE_POLICIES:
            if any(term in clause_lower for term in policy["title"].lower().split() if len(term) > 3):
                matched.append({
                    "policy_id": policy["policy_id"],
                    "title": policy["title"],
                    "category": policy["category"],
                    "content": f"{policy['title']}: {policy['content']}",
                    "relevance_distance": 0.1
                })
        return matched[:top_k] if matched else DEFAULT_COMPLIANCE_POLICIES[:top_k]


# Shared instance helper
_vector_store_instance = None

def get_policy_vector_store() -> PolicyVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = PolicyVectorStore()
    return _vector_store_instance


def query_compliance_policies(clause_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """Tool wrapper function for querying policies."""
    store = get_policy_vector_store()
    return store.query_compliance_policies(clause_text, top_k=top_k)

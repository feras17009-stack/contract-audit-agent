"""
Audit Tools: Saves immutable audit trail entries to SQLite database with metrics.
Satisfies Deliverable 1 & Production/Secure Elements (Audit Trail, Latency, Cost).
"""

import os
import sqlite3
import datetime
import logging
from typing import Dict, Any, List

logger = logging.getLogger("AuditTools")

DB_PATH = os.path.join("data", "compliance_audit.db")


def init_audit_database():
    """Ensures SQLite audit trail database table exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            contract_name TEXT NOT NULL,
            clause_id TEXT,
            clause_title TEXT,
            risk_level TEXT NOT NULL,
            compliance_status TEXT NOT NULL,
            details TEXT,
            latency_ms REAL,
            cost_usd REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def log_audit_entry(
    thread_id: str,
    contract_name: str,
    clause_id: str,
    clause_title: str,
    risk_level: str,
    compliance_status: str,
    details: str,
    latency_ms: float = 0.0,
    cost_usd: float = 0.0
) -> Dict[str, Any]:
    """
    Writes an immutable compliance audit record to the SQLite database.
    """
    init_audit_database()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO compliance_audit_log (
            thread_id, contract_name, clause_id, clause_title,
            risk_level, compliance_status, details, latency_ms, cost_usd
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        thread_id, contract_name, clause_id, clause_title,
        risk_level, compliance_status, details, latency_ms, cost_usd
    ))

    audit_id = cursor.lastrowid
    conn.commit()
    conn.close()

    logger.info(f"AUDIT LOG SAVED [ID #{audit_id}]: Thread={thread_id}, Risk={risk_level}, Status={compliance_status}")

    return {
        "audit_id": audit_id,
        "thread_id": thread_id,
        "contract_name": contract_name,
        "clause_id": clause_id,
        "risk_level": risk_level,
        "compliance_status": compliance_status,
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


def get_audit_trail_by_thread(thread_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all compliance audit log records for a given thread_id.
    """
    init_audit_database()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM compliance_audit_log WHERE thread_id = ? ORDER BY audit_id ASC
    """, (thread_id,))

    rows = cursor.fetchall()
    conn.close()

    records = []
    for r in rows:
        records.append(dict(r))

    return records

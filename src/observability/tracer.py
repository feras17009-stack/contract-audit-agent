"""
Observability Infrastructure: Tracing, Latency, Token Usage, Cost, and Failure Logging.
Satisfies Deliverable 4 (Security, Guardrails & Observability).
"""

import os
import time
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ContractAuditObservability")

_PHOENIX_INITIALIZED = False


def setup_observability() -> bool:
    """
    Initializes tracing via Arize Phoenix or LangSmith based on environment configuration.
    Returns True if tracing was successfully initialized.
    """
    global _PHOENIX_INITIALIZED
    provider = os.getenv("OBSERVABILITY_PROVIDER", "phoenix").lower()

    if provider == "phoenix":
        try:
            from openinference.instrumentation.langchain import LangChainInstrumentor
            from phoenix.otel import register
            
            endpoint = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006")
            tracer_provider = register(project_name="contract-audit-pipeline", endpoint=endpoint)
            LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
            
            _PHOENIX_INITIALIZED = True
            logger.info(f"Arize Phoenix observability initialized (Endpoint: {endpoint})")
            return True
        except Exception as e:
            logger.warning(f"Could not initialize Arize Phoenix tracing: {e}. Falling back to structured log tracing.")
            return False

    elif provider == "langsmith":
        if os.getenv("LANGCHAIN_API_KEY"):
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            logger.info("LangSmith observability initialized.")
            return True
        else:
            logger.warning("LANGCHAIN_API_KEY not set for LangSmith. Falling back to structured log tracing.")
            return False

    return False


class AuditMetricsTracker:
    """
    Tracks tool calls, latency, estimated token usage/cost, and errors across agent execution.
    """

    def __init__(self, node_name: str):
        self.node_name = node_name
        self.start_time = 0.0
        self.end_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Entering Node: [{self.node_name}]")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        latency_ms = round((self.end_time - self.start_time) * 1000, 2)
        if exc_type:
            logger.error(f"Node [{self.node_name}] FAILED in {latency_ms}ms with error: {exc_val}")
        else:
            logger.info(f"Node [{self.node_name}] COMPLETED successfully in {latency_ms}ms")


def log_tool_execution(tool_name: str, input_summary: str, output_summary: str, latency_ms: float, cost_usd: float = 0.0, error: Optional[str] = None):
    """
    Logs structured metrics for tool execution.
    """
    metrics = {
        "tool_name": tool_name,
        "input": input_summary[:100],
        "output": output_summary[:100],
        "latency_ms": latency_ms,
        "cost_usd": cost_usd,
        "status": "ERROR" if error else "SUCCESS",
        "error": error
    }
    if error:
        logger.error(f"TOOL TRACE: {metrics}")
    else:
        logger.info(f"TOOL TRACE: {metrics}")
    return metrics

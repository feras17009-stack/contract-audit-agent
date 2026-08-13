"""
Base LLM Integration: Initializes Google Gemini or fallback LLM with retries.
Supports offline deterministic evaluation for testing without API keys.
"""

import os
import time
import logging
from typing import Optional, Any, Callable

logger = logging.getLogger("BaseLLM")

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False


def get_llm():
    """
    Initializes ChatGoogleGenerativeAI model with API key from environment.
    Falls back to mock/rule-based engine if GOOGLE_API_KEY is not set.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")

    if api_key and api_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.1,
                max_retries=3
            )
            logger.info(f"Initialized ChatGoogleGenerativeAI with model: {model_name}")
            return llm
        except Exception as e:
            logger.warning(f"Could not initialize ChatGoogleGenerativeAI: {e}. Using rule-based fallback LLM.")
    else:
        logger.info("GOOGLE_API_KEY not set. Operating in offline rule-based agent mode.")

    return None


def invoke_llm_with_retry(llm: Any, prompt: str, max_retries: int = 3) -> str:
    """Invokes LLM with retry-with-backoff handling API quota/rate limits."""
    if llm is None:
        raise ValueError("LLM instance is None")
    
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = llm.invoke(prompt)
            if hasattr(response, "content"):
                return response.content
            return str(response)
        except Exception as e:
            last_error = e
            logger.warning(f"LLM call attempt #{attempt} failed: {e}. Retrying...")
            time.sleep(attempt * 2)

    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")

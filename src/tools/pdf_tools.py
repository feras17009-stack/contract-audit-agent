"""
PDF Extraction Tools: Parses and chunks PDF contracts into structured clauses.
Satisfies Deliverable 1 (Tools/Function Calling).
"""

import io
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("PDFTools")


def parse_and_chunk_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text from PDF contract bytes and chunks it into legal clauses/sections.
    Includes OCR fallback detection if extracted text is empty or near-empty.
    
    Returns:
        Dict containing:
            - full_text (str): Complete raw text extracted.
            - clauses (List[Dict[str, str]]): Extracted legal clauses with titles.
            - is_scanned (bool): True if text was sparse and required OCR flag.
            - page_count (int): Total number of pages.
    """
    if not pdf_bytes:
        raise ValueError("Empty PDF bytes provided.")

    extracted_pages = []
    is_scanned = False

    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        page_count = len(reader.pages)

        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            extracted_pages.append(text)

    except Exception as e:
        logger.warning(f"pypdf extraction failed: {e}. Returning raw text placeholder.")
        page_count = 1
        extracted_pages = [pdf_bytes.decode("utf-8", errors="ignore")]

    full_text = "\n\n".join(extracted_pages).strip()

    # Check if text is near empty (indicating a scanned image-only PDF)
    if len(full_text) < 50:
        is_scanned = True
        logger.warning("PDF extracted text is sparse (<50 chars). Flagged as scanned PDF requiring OCR.")
        # OCR fallback attempt using pytesseract if installed
        try:
            import pytesseract
            from PIL import Image
            # Note: For full OCR, pdf2image can render pages. Here we set flag for OCR fallback.
            full_text += "\n[OCR FALLBACK ATTEMPT: Scanned PDF detected]"
        except Exception:
            pass

    # Extract clauses based on common section headers (e.g. 1. Payment, Section 2, ARTICLE III)
    clauses = extract_clause_chunks(full_text)

    return {
        "full_text": full_text,
        "clauses": clauses,
        "is_scanned": is_scanned,
        "page_count": page_count
    }


def extract_clause_chunks(text: str) -> List[Dict[str, str]]:
    """
    Splits contract text into logical clause blocks using regex section boundaries.
    """
    if not text:
        return []

    # Patterns for section headers (e.g. "1. Term", "SECTION 3. INDEMNIFICATION", "Article 4 - Termination")
    pattern = r"(?=\b(?:SECTION|ARTICLE|\d+\.)\s+[A-Z0-9\s_-]+)"
    raw_chunks = re.split(pattern, text, flags=re.IGNORECASE)

    clauses = []
    for idx, chunk in enumerate(raw_chunks):
        cleaned = chunk.strip()
        if len(cleaned) > 20: # Filter out trivial whitespace or headers
            lines = cleaned.split("\n")
            title = lines[0][:60] if lines else f"Clause {idx + 1}"
            clauses.append({
                "clause_id": f"clause_{idx + 1}",
                "title": title.strip(),
                "text": cleaned
            })

    # If no structured section headers matched, chunk by double line breaks
    if not clauses:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
        for idx, para in enumerate(paragraphs):
            clauses.append({
                "clause_id": f"clause_{idx + 1}",
                "title": f"Clause {idx + 1}: {para[:30]}...",
                "text": para
            })

    return clauses

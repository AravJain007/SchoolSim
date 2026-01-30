"""
Document Parser
Extracts text from PDF, PPT/PPTX, and DOC/DOCX files.
Returns list of ChunkDetails objects (1 slide/page/paragraph = 1 chunk).
"""

import os
import re
from typing import List

from pydantic_classes import ChunkDetails


def parse_document(file_path: str) -> List[ChunkDetails]:
    """
    Parse document and return list of ChunkDetails objects.
    For PPTs: 1 slide = 1 chunk
    For PDFs/DOCs: 1 page or 1 paragraph = 1 chunk

    Args:
        file_path: Path to the document file

    Returns:
        List of ChunkDetails objects
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _parse_pdf(file_path)
    elif ext in [".ppt", ".pptx"]:
        return _parse_ppt(file_path)
    elif ext in [".doc", ".docx"]:
        return _parse_doc(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(file_path: str) -> List[ChunkDetails]:
    """Parse PDF file using PyMuPDF. Returns chunks (1 page = 1 chunk)."""
    import fitz

    doc = fitz.open(file_path)
    chunks = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            chunk_id = f"chunk_{page_num}"
            page_range = f"Page {page_num}"
            chunks.append(_create_chunk_details(chunk_id, text.strip(), page_range))

    doc.close()
    return chunks


def _parse_ppt(file_path: str) -> List[ChunkDetails]:
    """Parse PowerPoint file using python-pptx. Returns chunks (1 slide = 1 chunk)."""
    from pptx import Presentation

    prs = Presentation(file_path)
    chunks = []

    for slide_num, slide in enumerate(prs.slides, start=1):
        slide_text = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_text.append(shape.text.strip())
        if slide_text:
            content = "\n".join(slide_text)
            chunk_id = f"chunk_{slide_num}"
            page_range = f"Slide {slide_num}"
            chunks.append(_create_chunk_details(chunk_id, content, page_range))

    return chunks


def _parse_doc(file_path: str) -> List[ChunkDetails]:
    """Parse Word document using python-docx. Returns chunks (1 paragraph = 1 chunk)."""
    from docx import Document

    doc = Document(file_path)
    chunks = []

    for para_num, para in enumerate(doc.paragraphs, start=1):
        if para.text.strip():
            chunk_id = f"chunk_{para_num}"
            page_range = f"Page {para_num}"  # Using paragraph number as page reference
            chunks.append(
                _create_chunk_details(chunk_id, para.text.strip(), page_range)
            )

    return chunks


def _create_chunk_details(chunk_id: str, content: str, page_range: str) -> ChunkDetails:
    """Create ChunkDetails object with extracted metadata."""
    # Extract new terms (kept for metadata, but not used for density calculation)
    words = re.findall(r"\b[A-Z][a-z]+\b|\b[a-z]+[A-Z][a-z]*\b", content)
    new_terms = list(set(words))[:10]

    # Check for formulas and code (useful metadata)
    has_formula = bool(re.search(r"[=+\-*/^()]+", content))
    has_code = bool(re.search(r"[{};]|def |class |import |print\(", content))

    return ChunkDetails(
        chunk_id=chunk_id,
        content=content,
        difficulty_index=0.0,  # Placeholder - will be populated post-simulation
        new_terms=new_terms,
        page_range=page_range,
        has_formula=has_formula,
        has_code=has_code,
    )

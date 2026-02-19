"""
Simple Structural Chunker
Chunks documents by structure: 1 slide = 1 chunk for PPTs, 1 page/paragraph = 1 chunk for PDFs/DOCs.
"""

import re
from typing import List

from pydantic_classes import ChunkDetails


def chunk_by_structure(
    paragraphs: List[str], is_presentation: bool = False
) -> List[ChunkDetails]:
    """
    Chunk paragraphs by structure (1 slide/paragraph = 1 chunk).

    Args:
        paragraphs: List of text paragraphs/slides
        is_presentation: If True, use "Slide" prefix for page_range, else "Page"

    Returns:
        List of ChunkDetails objects
    """
    chunks = []
    page_prefix = "Slide" if is_presentation else "Page"

    for idx, para in enumerate(paragraphs, start=1):
        chunk_id = f"chunk_{idx}"
        page_range = f"{page_prefix} {idx}"

        chunks.append(_create_chunk_details(chunk_id, para, page_range))

    return chunks


def _create_chunk_details(chunk_id: str, content: str, page_range: str) -> ChunkDetails:
    """Create ChunkDetails object with extracted metadata."""
    # Check for formulas and code (useful metadata)
    has_formula = bool(re.search(r"[=+\-*/^()]+", content))
    has_code = bool(re.search(r"[{};]|def |class |import |print\(", content))

    return ChunkDetails(
        chunk_id=chunk_id,
        content=content,
        difficulty_index=0.0,  # Placeholder - will be populated post-simulation
        page_range=page_range,
        has_formula=has_formula,
        has_code=has_code,
    )

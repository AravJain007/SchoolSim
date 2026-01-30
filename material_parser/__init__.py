"""
Material Parser Module
Extracts and chunks course materials by structure (1 slide/page/paragraph = 1 chunk).
"""

from material_parser.chunker import chunk_by_structure
from material_parser.parser import parse_document

__all__ = ["parse_document", "chunk_by_structure"]

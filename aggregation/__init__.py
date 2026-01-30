"""
Aggregation Module

This module handles multi-run simulation execution, difficulty calculation,
gap detection, and report generation.
"""

from aggregation.analyzer import calculate_irf_plus, find_common_doubts
from aggregation.difficulty_calculator import (
    compute_difficulty_index,
    populate_chunk_difficulty,
)
from aggregation.gap_detector import detect_gaps
from aggregation.multi_run import MultiRunExecutor
from aggregation.report_generator import generate_gap_report, generate_principal_summary

__all__ = [
    "MultiRunExecutor",
    "calculate_irf_plus",
    "find_common_doubts",
    "compute_difficulty_index",
    "populate_chunk_difficulty",
    "detect_gaps",
    "generate_gap_report",
    "generate_principal_summary",
]

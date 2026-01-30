"""
Analyzer Module

Contains functions for IRF+ metric calculation and doubt analysis
across simulation runs.
"""

from typing import Dict, List

from pydantic_classes import SimulationRun, StudentResponse


def calculate_irf_plus(student_responses: List[StudentResponse]) -> float:
    """
    Calculate IRF R+ metric: proportion of doubts that led to understanding improvement.

    The IRF (Initiation-Response-Feedback) R+ metric measures teaching effectiveness
    by tracking how often a teacher's response to a doubt actually improves
    the student's understanding.

    R+ = (number of resolved doubts) / (total doubts asked)

    A doubt is "resolved" if understanding_after > understanding_before

    Parameters
    ----------
    student_responses : List[StudentResponse]
        List of student responses (can be from one run or aggregated)

    Returns
    -------
    float
        R+ score between 0.0 and 1.0 (1.0 = all doubts resolved)
    """
    # Count doubts (responses where a doubt was asked)
    total_doubts = sum(1 for r in student_responses if r.doubt_asked is not None)

    if total_doubts == 0:
        return 0.0

    # Count resolved doubts (where understanding improved after teacher response)
    resolved = sum(1 for r in student_responses if r.doubt_resolved is True)

    return resolved / total_doubts


def calculate_irf_plus_from_runs(all_runs: List[SimulationRun]) -> float:
    """
    Calculate overall IRF R+ metric across all simulation runs.

    Parameters
    ----------
    all_runs : List[SimulationRun]
        All simulation runs to analyze

    Returns
    -------
    float
        Overall R+ score between 0.0 and 1.0
    """
    all_responses: List[StudentResponse] = []

    for run in all_runs:
        for chunk_result in run.chunk_results:
            responses = chunk_result.get("student_responses", [])
            for resp_dict in responses:
                # Convert dict back to StudentResponse if needed
                if isinstance(resp_dict, dict):
                    all_responses.append(StudentResponse(**resp_dict))
                else:
                    all_responses.append(resp_dict)

    return calculate_irf_plus(all_responses)


def find_common_doubts(all_runs: List[SimulationRun]) -> Dict[str, List[str]]:
    """
    Group doubts by chunk_id across all simulation runs.

    This helps identify recurring confusion points in the material
    by collecting all doubts asked about each chunk.

    Parameters
    ----------
    all_runs : List[SimulationRun]
        All simulation runs to analyze

    Returns
    -------
    Dict[str, List[str]]
        Mapping of chunk_id to list of doubts asked about that chunk
    """
    doubts_by_chunk: Dict[str, List[str]] = {}

    for run in all_runs:
        for chunk_result in run.chunk_results:
            chunk_id = chunk_result.get("chunk_id")
            if chunk_id is None:
                continue

            responses = chunk_result.get("student_responses", [])

            for resp in responses:
                # Handle both dict and StudentResponse objects
                if isinstance(resp, dict):
                    doubt = resp.get("doubt_asked")
                else:
                    doubt = resp.doubt_asked

                if doubt:
                    if chunk_id not in doubts_by_chunk:
                        doubts_by_chunk[chunk_id] = []
                    doubts_by_chunk[chunk_id].append(doubt)

    return doubts_by_chunk


def get_per_chunk_avg_understanding(all_runs: List[SimulationRun]) -> Dict[str, float]:
    """
    Calculate average understanding score per chunk across all runs.

    Parameters
    ----------
    all_runs : List[SimulationRun]
        All simulation runs to analyze

    Returns
    -------
    Dict[str, float]
        Mapping of chunk_id to average understanding (1-5 scale)
    """
    # chunk_id -> list of all understanding scores
    scores_by_chunk: Dict[str, List[int]] = {}

    for run in all_runs:
        for chunk_result in run.chunk_results:
            chunk_id = chunk_result.get("chunk_id")
            if chunk_id is None:
                continue

            responses = chunk_result.get("student_responses", [])

            for resp in responses:
                if isinstance(resp, dict):
                    score = resp.get("understanding_after")
                else:
                    score = resp.understanding_after

                if score is not None:
                    if chunk_id not in scores_by_chunk:
                        scores_by_chunk[chunk_id] = []
                    scores_by_chunk[chunk_id].append(score)

    # Calculate averages
    avg_by_chunk: Dict[str, float] = {}
    for chunk_id, scores in scores_by_chunk.items():
        if scores:
            avg_by_chunk[chunk_id] = sum(scores) / len(scores)

    return avg_by_chunk

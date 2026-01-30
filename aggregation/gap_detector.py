"""
Gap Detector Module

Identifies chunks where students consistently struggle across
multiple simulation runs.
"""

from typing import Dict, List, Tuple

from pydantic_classes import SimulationRun


def detect_gaps(
    all_runs: List[SimulationRun],
    threshold: float = 0.4,
) -> List[str]:
    """
    Detect chunks where students struggle across multiple runs.

    A chunk is flagged as a "gap" if:
    - avg_understanding < 3 in >= threshold (default 40%) of runs

    Parameters
    ----------
    all_runs : List[SimulationRun]
        All simulation runs to analyze
    threshold : float
        Minimum failure rate to flag as gap (0.0 to 1.0, default 0.4)

    Returns
    -------
    List[str]
        List of chunk_ids identified as teaching gaps
    """
    if not all_runs:
        return []

    # Collect all unique chunk_ids
    chunk_ids = set()
    for run in all_runs:
        for chunk_result in run.chunk_results:
            chunk_id = chunk_result.get("chunk_id")
            if chunk_id:
                chunk_ids.add(chunk_id)

    gap_chunks: List[str] = []

    for chunk_id in chunk_ids:
        failure_runs = 0
        total_runs = 0

        for run in all_runs:
            for chunk_result in run.chunk_results:
                if chunk_result.get("chunk_id") != chunk_id:
                    continue

                total_runs += 1
                responses = chunk_result.get("student_responses", [])

                if not responses:
                    continue

                # Calculate average understanding for this chunk in this run
                scores = []
                for resp in responses:
                    if isinstance(resp, dict):
                        score = resp.get("understanding_after")
                    else:
                        score = resp.understanding_after

                    if score is not None:
                        scores.append(score)

                if scores:
                    avg = sum(scores) / len(scores)
                    if avg < 3:
                        failure_runs += 1

        # Check if failure rate exceeds threshold
        if total_runs > 0:
            failure_rate = failure_runs / total_runs
            if failure_rate >= threshold:
                gap_chunks.append(chunk_id)

    return gap_chunks


def detect_gaps_with_details(
    all_runs: List[SimulationRun],
    threshold: float = 0.4,
) -> List[Dict]:
    """
    Detect chunks where students struggle, with detailed statistics.

    Parameters
    ----------
    all_runs : List[SimulationRun]
        All simulation runs to analyze
    threshold : float
        Minimum failure rate to flag as gap (0.0 to 1.0)

    Returns
    -------
    List[Dict]
        List of gap details containing chunk_id, failure_rate, avg_understanding
    """
    if not all_runs:
        return []

    # Collect all unique chunk_ids
    chunk_ids = set()
    for run in all_runs:
        for chunk_result in run.chunk_results:
            chunk_id = chunk_result.get("chunk_id")
            if chunk_id:
                chunk_ids.add(chunk_id)

    gap_details: List[Dict] = []

    for chunk_id in chunk_ids:
        all_scores: List[int] = []
        failure_runs = 0
        total_runs = 0

        for run in all_runs:
            for chunk_result in run.chunk_results:
                if chunk_result.get("chunk_id") != chunk_id:
                    continue

                total_runs += 1
                responses = chunk_result.get("student_responses", [])

                run_scores = []
                for resp in responses:
                    if isinstance(resp, dict):
                        score = resp.get("understanding_after")
                    else:
                        score = resp.understanding_after

                    if score is not None:
                        run_scores.append(score)
                        all_scores.append(score)

                if run_scores:
                    avg = sum(run_scores) / len(run_scores)
                    if avg < 3:
                        failure_runs += 1

        if total_runs > 0:
            failure_rate = failure_runs / total_runs
            avg_understanding = sum(all_scores) / len(all_scores) if all_scores else 0.0

            if failure_rate >= threshold:
                gap_details.append(
                    {
                        "chunk_id": chunk_id,
                        "failure_rate": round(failure_rate, 3),
                        "avg_understanding": round(avg_understanding, 2),
                        "total_runs": total_runs,
                        "failure_runs": failure_runs,
                    }
                )

    # Sort by failure rate (highest first)
    gap_details.sort(key=lambda x: x["failure_rate"], reverse=True)

    return gap_details


def get_chunk_failure_rates(all_runs: List[SimulationRun]) -> Dict[str, float]:
    """
    Calculate failure rate for each chunk across all runs.

    Failure rate = proportion of runs where avg_understanding < 3

    Parameters
    ----------
    all_runs : List[SimulationRun]
        All simulation runs to analyze

    Returns
    -------
    Dict[str, float]
        Mapping of chunk_id to failure rate (0.0 to 1.0)
    """
    if not all_runs:
        return {}

    # chunk_id -> (failure_count, total_count)
    chunk_stats: Dict[str, Tuple[int, int]] = {}

    for run in all_runs:
        for chunk_result in run.chunk_results:
            chunk_id = chunk_result.get("chunk_id")
            if not chunk_id:
                continue

            if chunk_id not in chunk_stats:
                chunk_stats[chunk_id] = (0, 0)

            responses = chunk_result.get("student_responses", [])
            scores = []

            for resp in responses:
                if isinstance(resp, dict):
                    score = resp.get("understanding_after")
                else:
                    score = resp.understanding_after

                if score is not None:
                    scores.append(score)

            failures, total = chunk_stats[chunk_id]
            total += 1

            if scores and (sum(scores) / len(scores)) < 3:
                failures += 1

            chunk_stats[chunk_id] = (failures, total)

    # Convert to failure rates
    return {
        chunk_id: failures / total if total > 0 else 0.0
        for chunk_id, (failures, total) in chunk_stats.items()
    }

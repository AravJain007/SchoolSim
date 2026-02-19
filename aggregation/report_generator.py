"""
Report Generator Module

Generates final JSON reports in the format specified in FinalPlanAgents.md
Sections 5.2 (Gap Report) and 5.3 (Principal Summary).
"""

from typing import Dict, List, Optional

from aggregation.analyzer import find_common_doubts, get_per_chunk_avg_understanding
from aggregation.difficulty_calculator import compute_difficulty_index
from aggregation.gap_detector import detect_gaps_with_details
from pydantic_classes import (
    AggregatedResults,
    ChunkDetails,
    PrincipalAnalysis,
    SimulationRun,
)


def generate_gap_report(
    gaps: List[str],
    runs: List[SimulationRun],
    chunks: Optional[List[ChunkDetails]] = None,
) -> dict:
    """
    Generate gap report per FinalPlanAgents.md Section 5.2.

    Output format:
    {
        "gaps": [
            {
                "chunk_id": "C005",
                "topic": "Recursive Case Explanation",
                "avg_understanding": 2.1,
                "difficulty_index": 58.0,
                "failure_rate": 0.45,
                "common_doubts": [...],
                "principal_notes": "..."
            }
        ]
    }

    Parameters
    ----------
    gaps : List[str]
        List of chunk_ids identified as gaps
    runs : List[SimulationRun]
        All simulation runs for extracting details
    chunks : Optional[List[ChunkDetails]]
        Original chunks for topic/content info

    Returns
    -------
    dict
        Gap report in specified format
    """
    # Get common doubts grouped by chunk
    all_doubts = find_common_doubts(runs)

    # Get avg understanding per chunk
    avg_understanding = get_per_chunk_avg_understanding(runs)

    # Get gap details (includes failure_rate)
    gap_details = detect_gaps_with_details(runs)
    gap_details_map = {g["chunk_id"]: g for g in gap_details}

    # Build chunk content map if chunks provided
    chunk_content_map: Dict[str, ChunkDetails] = {}
    if chunks:
        chunk_content_map = {c.chunk_id: c for c in chunks}

    # Collect per-chunk KLI scores from each run's session-level principal_summary
    principal_notes_map: Dict[str, List[str]] = {}
    for run in runs:
        summary = run.principal_summary
        if not summary:
            continue
        for chunk_id, score in summary.per_chunk_scores.items():
            if chunk_id not in principal_notes_map:
                principal_notes_map[chunk_id] = []
            # Attach the session notes once per run (score context)
            note = (
                f"KLI score: {score:.2f} — {summary.notes[:120]}..."
                if summary.notes
                else f"KLI score: {score:.2f}"
            )
            principal_notes_map[chunk_id].append(note)

    # Build gap entries
    gap_entries: List[dict] = []

    for chunk_id in gaps:
        difficulty = compute_difficulty_index(chunk_id, runs)
        avg_und = avg_understanding.get(chunk_id, 0.0)
        doubts = all_doubts.get(chunk_id, [])
        notes = principal_notes_map.get(chunk_id, [])

        # Get failure rate from gap details
        gap_info = gap_details_map.get(chunk_id, {})
        failure_rate = gap_info.get("failure_rate", 0.0)

        # Try to extract topic from chunk content
        topic = f"Chunk {chunk_id}"
        if chunk_id in chunk_content_map:
            chunk = chunk_content_map[chunk_id]
            # Use first 50 chars of content as topic, or page_range
            content_preview = chunk.content[:50].strip()
            if content_preview:
                topic = (
                    content_preview + "..."
                    if len(chunk.content) > 50
                    else content_preview
                )
            else:
                topic = chunk.page_range

        gap_entries.append(
            {
                "chunk_id": chunk_id,
                "topic": topic,
                "avg_understanding": round(avg_und, 2),
                "difficulty_index": difficulty,
                "failure_rate": round(failure_rate, 3),
                "common_doubts": doubts[:5],  # Top 5 doubts
                "principal_notes": notes[0] if notes else "",
            }
        )

    # Sort by failure rate (highest first)
    gap_entries.sort(key=lambda x: x["failure_rate"], reverse=True)

    return {"gaps": gap_entries}


def generate_principal_summary(runs: List[SimulationRun]) -> dict:
    """
    Generate principal summary per FinalPlanAgents.md Section 5.3.

    Output format:
    {
        "overall_alignment": 0.72,
        "critical_misalignments": [
            {
                "chunk_id": "C005",
                "issue": "Used lecture for practice-required content",
                "suggestion": "Add live coding demonstration"
            }
        ],
        "missing_prerequisites": ["stack_memory", "function_scope"],
        "bloom_progression": "Covers Remember/Understand, missing Apply/Analyze"
    }

    Parameters
    ----------
    runs : List[SimulationRun]
        All simulation runs containing principal analyses

    Returns
    -------
    dict
        Principal summary in specified format
    """
    all_alignment_scores: List[float] = []
    all_prerequisites: List[str] = []
    all_suggested_methods: List[str] = []
    all_notes: List[str] = []

    # Critical misalignments (alignment_score < 0.5)
    critical_misalignments: List[dict] = []

    for run in runs:
        summary = run.principal_summary
        if not summary:
            continue

        all_alignment_scores.append(summary.alignment_score)
        all_prerequisites.extend(summary.missing_prerequisites)
        all_suggested_methods.extend(summary.suggested_methods)
        if summary.notes:
            all_notes.append(summary.notes)

        # Derive critical misalignments from per-chunk scores in the session summary
        for chunk_id, score in summary.per_chunk_scores.items():
            if score < 0.5:
                suggestion = (
                    summary.suggested_methods[0]
                    if summary.suggested_methods
                    else "Review teaching method"
                )
                critical_misalignments.append(
                    {
                        "chunk_id": chunk_id,
                        "issue": f"Low KLI alignment ({score:.2f}) detected for this chunk",
                        "suggestion": suggestion,
                    }
                )

    # Calculate overall alignment
    overall_alignment = 0.0
    if all_alignment_scores:
        overall_alignment = sum(all_alignment_scores) / len(all_alignment_scores)

    # Deduplicate prerequisites and methods
    unique_prerequisites = list(set(all_prerequisites))
    unique_methods = list(set(all_suggested_methods))

    # Simple Bloom's progression analysis
    # (In a full implementation, this would analyze the content more deeply)
    bloom_progression = _analyze_bloom_progression(unique_methods)

    return {
        "overall_alignment": round(overall_alignment, 3),
        "critical_misalignments": critical_misalignments[:10],  # Top 10
        "missing_prerequisites": unique_prerequisites,
        "bloom_progression": bloom_progression,
    }


def _analyze_bloom_progression(suggested_methods: List[str]) -> str:
    """
    Analyze Bloom's Taxonomy progression based on suggested methods.

    Very simplified heuristic - in production, this would be more sophisticated.
    """
    method_str = " ".join(suggested_methods).lower()

    has_remember = any(w in method_str for w in ["explain", "lecture", "definition"])
    has_understand = any(w in method_str for w in ["example", "analogy", "diagram"])
    has_apply = any(w in method_str for w in ["practice", "exercise", "coding", "demo"])
    has_analyze = any(w in method_str for w in ["compare", "analyze", "discuss"])

    covered = []
    missing = []

    if has_remember:
        covered.append("Remember")
    else:
        missing.append("Remember")

    if has_understand:
        covered.append("Understand")
    else:
        missing.append("Understand")

    if has_apply:
        covered.append("Apply")
    else:
        missing.append("Apply")

    if has_analyze:
        covered.append("Analyze")
    else:
        missing.append("Analyze")

    if covered and missing:
        return f"Covers {'/'.join(covered)}, missing {'/'.join(missing)}"
    elif covered:
        return f"Covers {'/'.join(covered)}"
    elif missing:
        return f"Missing {'/'.join(missing)}"
    else:
        return "Unable to determine progression"


def generate_aggregated_results(
    runs: List[SimulationRun],
    gap_threshold: float = 0.4,
) -> AggregatedResults:
    """
    Generate complete AggregatedResults from simulation runs.

    This is the main entry point for generating all aggregated data.

    Parameters
    ----------
    runs : List[SimulationRun]
        All simulation runs
    gap_threshold : float
        Threshold for gap detection (default 0.4 = 40%)

    Returns
    -------
    AggregatedResults
        Complete aggregated results model
    """
    from aggregation.gap_detector import detect_gaps

    # Get average understanding per chunk
    per_chunk_avg = get_per_chunk_avg_understanding(runs)

    # Detect gap chunks
    gap_chunks = detect_gaps(runs, threshold=gap_threshold)

    # Get common doubts
    common_doubts = find_common_doubts(runs)

    # Collect principal notes
    principal_notes: List[str] = []
    for run in runs:
        if run.principal_summary and run.principal_summary.notes:
            principal_notes.append(run.principal_summary.notes)

    return AggregatedResults(
        total_runs=len(runs),
        per_chunk_avg_understanding=per_chunk_avg,
        gap_chunks=gap_chunks,
        common_doubts=common_doubts,
        principal_notes=principal_notes,
    )

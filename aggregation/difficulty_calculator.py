"""
Difficulty Calculator Module

Computes difficulty_index for each chunk AFTER simulation based on
actual student understanding scores, not pre-computed NLP metrics.
"""

from typing import List

from pydantic_classes import ChunkDetails, SimulationRun


def compute_difficulty_index(chunk_id: str, all_runs: List[SimulationRun]) -> float:
    """
    Calculate difficulty_index for a chunk based on student understanding scores.

    Formula: difficulty_index = (1 - avg_understanding / 5) * 100

    This ensures difficulty reflects actual student struggle:
    - Low understanding (1-2) → High difficulty (60-80)
    - High understanding (4-5) → Low difficulty (0-20)

    Parameters
    ----------
    chunk_id : str
        ID of the chunk to calculate difficulty for
    all_runs : List[SimulationRun]
        All simulation runs containing student responses

    Returns
    -------
    float
        Difficulty index on 0-100 scale (higher = more difficult)
    """
    all_scores: List[int] = []

    for run in all_runs:
        for chunk_result in run.chunk_results:
            if chunk_result.get("chunk_id") != chunk_id:
                continue

            responses = chunk_result.get("student_responses", [])

            for resp in responses:
                # Handle both dict and StudentResponse objects
                if isinstance(resp, dict):
                    score = resp.get("understanding_after")
                else:
                    score = resp.understanding_after

                if score is not None:
                    all_scores.append(score)

    if not all_scores:
        return 0.0

    avg_understanding = sum(all_scores) / len(all_scores)
    difficulty_index = (1 - avg_understanding / 5) * 100

    return round(difficulty_index, 2)


def populate_chunk_difficulty(
    chunks: List[ChunkDetails],
    all_runs: List[SimulationRun],
) -> List[ChunkDetails]:
    """
    Update each chunk's difficulty_index field based on simulation results.

    This function should be called after all simulation runs complete to
    fill in the difficulty_index field that was left as None during parsing.

    Parameters
    ----------
    chunks : List[ChunkDetails]
        Original chunks from material parsing (with difficulty_index as None/0)
    all_runs : List[SimulationRun]
        All completed simulation runs

    Returns
    -------
    List[ChunkDetails]
        New list with updated difficulty_index values
    """
    updated_chunks: List[ChunkDetails] = []

    for chunk in chunks:
        difficulty = compute_difficulty_index(chunk.chunk_id, all_runs)

        # Create new chunk with updated difficulty_index
        updated_chunk = chunk.model_copy(update={"difficulty_index": difficulty})
        updated_chunks.append(updated_chunk)

    return updated_chunks


def get_difficulty_summary(
    chunks: List[ChunkDetails],
    all_runs: List[SimulationRun],
) -> dict:
    """
    Generate a summary of difficulty across all chunks.

    Parameters
    ----------
    chunks : List[ChunkDetails]
        Original chunks from material parsing
    all_runs : List[SimulationRun]
        All completed simulation runs

    Returns
    -------
    dict
        Summary containing per-chunk difficulty and overall stats
    """
    difficulties: dict = {}

    for chunk in chunks:
        difficulty = compute_difficulty_index(chunk.chunk_id, all_runs)
        difficulties[chunk.chunk_id] = {
            "difficulty_index": difficulty,
            "page_range": chunk.page_range,
            "has_formula": chunk.has_formula,
            "has_code": chunk.has_code,
        }

    # Calculate overall stats
    all_difficulties = [d["difficulty_index"] for d in difficulties.values()]

    if all_difficulties:
        avg_difficulty = sum(all_difficulties) / len(all_difficulties)
        max_difficulty = max(all_difficulties)
        min_difficulty = min(all_difficulties)
    else:
        avg_difficulty = max_difficulty = min_difficulty = 0.0

    return {
        "per_chunk": difficulties,
        "overall": {
            "average": round(avg_difficulty, 2),
            "max": round(max_difficulty, 2),
            "min": round(min_difficulty, 2),
            "total_chunks": len(chunks),
        },
    }

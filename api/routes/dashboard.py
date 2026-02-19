"""
Dashboard Routes
Handles dashboard and analytics data for teachers.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.db import get_simulations_collection
from api.dependencies import get_simulation_store

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class SimulationListItem(BaseModel):
    """A simulation item for listing."""

    id: str
    topic: str
    timestamp: str
    status: str
    student_count: int = 0
    average_understanding: float = 0
    effectiveness_score: float = 0


class SimulationDetailResponse(BaseModel):
    """Detailed simulation data."""

    id: str
    topic: str
    timestamp: str
    status: str
    total_runs: int = 0
    student_count: int = 0
    per_chunk_understanding: dict = {}
    gap_chunks: list = []
    common_doubts: dict = {}
    principal_notes: list = []


class CommonGap(BaseModel):
    gap: str
    count: int


class TrendPoint(BaseModel):
    date: str
    score: float


class AnalyticsResponse(BaseModel):
    """Analytics summary for teacher dashboard."""

    total_simulations: int
    total_time_spent: int  # minutes
    average_effectiveness: float
    common_gaps: List[CommonGap]
    improvement_trend: List[TrendPoint]


@router.get("/simulations", response_model=List[SimulationListItem])
async def get_simulations(
    teacher_id: Optional[str] = Query(None, description="Filter by teacher ID")
):
    """
    List simulations, optionally filtered by teacher_id.

    Merges in-memory (live/recent) and MongoDB (historical) data.
    """
    merged = _get_merged_simulations(teacher_id=teacher_id)

    simulations = []
    for sim_id, sim_data in merged.items():
        request_data = sim_data.get("request", {})
        topic = request_data.get("class_name", "Unknown Topic")
        results = sim_data.get("results") or {}

        # Prefer created_at from the document; fall back to utcnow
        ts = (
            sim_data.get("created_at") or sim_data.get("timestamp") or datetime.utcnow()
        )
        timestamp_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)

        simulations.append(
            SimulationListItem(
                id=sim_id,
                topic=topic,
                timestamp=timestamp_str,
                status=sim_data.get("status", "unknown"),
                student_count=results.get("student_count", 0),
                average_understanding=_calculate_avg_understanding(results),
                effectiveness_score=_calculate_effectiveness(results),
            )
        )

    # Sort by timestamp descending (most recent first)
    simulations.sort(key=lambda x: x.timestamp, reverse=True)
    return simulations


@router.get("/simulation/{simulation_id}", response_model=SimulationDetailResponse)
async def get_simulation_detail(simulation_id: str):
    """
    Get detailed data for a specific simulation.

    Falls back to MongoDB if not found in the in-memory store.
    """
    store = get_simulation_store()
    sim_data = store.get(simulation_id)

    if sim_data is None:
        try:
            col = get_simulations_collection()
            if col is not None:
                doc = col.find_one({"simulation_id": simulation_id}, {"_id": 0})
                if doc:
                    sim_data = doc
        except Exception:
            pass

    if sim_data is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    request_data = sim_data.get("request", {})
    results = sim_data.get("results") or {}

    ts = sim_data.get("created_at") or sim_data.get("timestamp") or ""
    timestamp_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)

    return SimulationDetailResponse(
        id=simulation_id,
        topic=request_data.get("class_name", "Unknown"),
        timestamp=timestamp_str,
        status=sim_data.get("status", "unknown"),
        total_runs=results.get("total_runs", 0),
        student_count=0,
        per_chunk_understanding=results.get("per_chunk_avg_understanding", {}),
        gap_chunks=results.get("gap_chunks", []),
        common_doubts=results.get("common_doubts", {}),
        principal_notes=results.get("principal_notes", []),
    )


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    teacher_id: Optional[str] = Query(None, description="Filter by teacher ID")
):
    """
    Get aggregated analytics data.

    Merges in-memory and MongoDB data for full historical analytics.
    """
    merged = _get_merged_simulations(teacher_id=teacher_id)

    # Filter simulations
    filtered_sims = [
        (sim_id, sim_data)
        for sim_id, sim_data in merged.items()
        if sim_data.get("status") == "completed"
    ]

    total_simulations = len(filtered_sims)

    # Calculate average effectiveness
    effectiveness_scores = []
    gap_counter = {}
    trend_data = []

    for sim_id, sim_data in filtered_sims:
        results = sim_data.get("results", {})
        if results:
            # Calculate effectiveness from understanding scores
            eff = _calculate_effectiveness(results)
            effectiveness_scores.append(eff)

            # Count gaps
            for gap in results.get("gap_chunks", []):
                gap_name = (
                    gap.get("reason", str(gap)) if isinstance(gap, dict) else str(gap)
                )
                gap_counter[gap_name] = gap_counter.get(gap_name, 0) + 1

            # Trend data
            ts = (
                sim_data.get("created_at")
                or sim_data.get("timestamp")
                or datetime.utcnow()
            )
            ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
            trend_data.append({"date": ts_str[:10], "score": eff})  # Just date part

    avg_effectiveness = (
        sum(effectiveness_scores) / len(effectiveness_scores)
        if effectiveness_scores
        else 0
    )

    # Build common gaps list (sorted by count)
    common_gaps = [
        CommonGap(gap=gap, count=count)
        for gap, count in sorted(gap_counter.items(), key=lambda x: x[1], reverse=True)
    ][
        :10
    ]  # Top 10 gaps

    # Build trend (sorted by date)
    improvement_trend = [
        TrendPoint(date=t["date"], score=t["score"])
        for t in sorted(trend_data, key=lambda x: x["date"])
    ]

    return AnalyticsResponse(
        total_simulations=total_simulations,
        total_time_spent=total_simulations * 30,  # Estimate 30 min per simulation
        average_effectiveness=round(avg_effectiveness, 1),
        common_gaps=common_gaps,
        improvement_trend=improvement_trend,
    )


def _get_merged_simulations(teacher_id: Optional[str] = None) -> Dict[str, dict]:
    """
    Return a merged dict of simulation data from both in-memory store and MongoDB.

    In-memory entries take precedence (they hold live progress info).
    MongoDB entries fill in historical simulations not present in-memory.

    Parameters
    ----------
    teacher_id : Optional[str]
        If provided, only return simulations belonging to this teacher.

    Returns
    -------
    Dict[str, dict]
        Mapping of simulation_id -> simulation data dict.
    """
    store = get_simulation_store()

    # Start with in-memory entries
    merged: Dict[str, dict] = {}
    for sim_id, sim_data in store.items():
        request_data = sim_data.get("request", {})
        if teacher_id and request_data.get("teacher_id") != teacher_id:
            continue
        merged[sim_id] = sim_data

    # Overlay with MongoDB entries that are not already in-memory
    try:
        col = get_simulations_collection()
        if col is not None:
            query: dict = {}
            if teacher_id:
                query["teacher_id"] = teacher_id
            for doc in col.find(query, {"_id": 0}):
                sim_id = doc.get("simulation_id")
                if sim_id and sim_id not in merged:
                    merged[sim_id] = doc
    except Exception:
        pass  # MongoDB unavailable -- return in-memory data only

    return merged


def _calculate_avg_understanding(results: dict) -> float:
    """Calculate average understanding from results."""
    if not results:
        return 0.0

    chunk_understanding = results.get("per_chunk_avg_understanding", {})
    if not chunk_understanding:
        return 0.0

    values = list(chunk_understanding.values())
    if not values:
        return 0.0

    return sum(values) / len(values)


def _calculate_effectiveness(results: dict) -> float:
    """Calculate effectiveness score from results."""
    if not results:
        return 0.0

    # Effectiveness is based on average understanding
    avg = _calculate_avg_understanding(results)

    # Penalize for gaps
    gap_count = len(results.get("gap_chunks", []))
    penalty = min(gap_count * 2, 20)  # Max 20% penalty

    return max(0, avg - penalty)

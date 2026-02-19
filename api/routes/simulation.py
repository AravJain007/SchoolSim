"""
Simulation Routes
Handles simulation lifecycle: start, status, stream, and results.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from aggregation.analyzer import find_common_doubts, get_per_chunk_avg_understanding
from aggregation.gap_detector import detect_gaps, detect_gaps_with_details
from aggregation.multi_run import MultiRunExecutor
from aggregation.report_generator import generate_aggregated_results
from api.db import get_chat_history_collection, get_simulations_collection
from api.dependencies import generate_simulation_id, get_simulation_store
from material_parser.parser import parse_document
from pydantic_classes import Provider, SimulationRun, TeacherAgentConfig
from simulation.principal_agent import PrincipalAgent

router = APIRouter(prefix="/simulation", tags=["simulation"])
logger = logging.getLogger(__name__)


class StartSimulationRequest(BaseModel):
    class_name: str = Field(..., description="Name/location of the classroom")
    teacher_id: str = Field(..., description="Teacher ID")
    teacher_name: str = Field(..., description="Teacher name")
    teacher_personality: str = Field(..., description="Teacher personality prompt")
    teacher_big5: dict = Field(..., description="Teacher Big5 personality scores")
    material_file_path: str = Field(..., description="Path to course material file")
    professor_name: str = Field(..., description="Name of the professor")
    num_runs: int = Field(
        default=1, ge=1, le=100, description="Number of simulation runs"
    )
    model_provider: str = Field(default="lightning", description="LLM provider")
    model_name: str = Field(
        default="lightning-ai/gpt-oss-120b", description="Model name"
    )


class SimulationStatusResponse(BaseModel):
    simulation_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: Optional[str] = None
    message: Optional[str] = None
    principal_retrying: Optional[bool] = None


class SimulationResultResponse(BaseModel):
    simulation_id: str
    total_runs: int
    per_chunk_avg_understanding: dict
    gap_chunks: list
    gap_chunk_details: list = []  # [{chunk_id, failure_rate, avg_understanding, ...}]
    common_doubts: dict
    principal_notes: list
    principal_retrying: Optional[bool] = None


def _persist_chat_history_to_mongo(simulation_id: str, messages: list) -> None:
    """
    Persist all live-chat messages for a simulation to the chat_history collection.

    Stored separately from the simulation document to keep that doc lean.
    Each message already carries a run_index tag set by MultiRunExecutor.
    """
    try:
        col = get_chat_history_collection()
        if col is None:
            logger.warning(
                "MongoDB not available -- chat history for %s not persisted",
                simulation_id,
            )
            return

        doc = {
            "simulation_id": simulation_id,
            "messages": messages,
            "total_messages": len(messages),
            "saved_at": datetime.utcnow(),
        }
        col.replace_one({"simulation_id": simulation_id}, doc, upsert=True)
        logger.info(
            "Chat history for simulation %s persisted (%d messages)",
            simulation_id,
            len(messages),
        )
    except Exception as exc:
        logger.error(
            "Failed to persist chat history for simulation %s: %s", simulation_id, exc
        )


def _persist_simulation_to_mongo(simulation_id: str, sim_data: dict) -> None:
    """
    Persist a completed/failed simulation document to MongoDB.

    Chat messages are stored in the separate chat_history collection (via
    _persist_chat_history_to_mongo) to keep this document lean.

    Called once per simulation after it finishes. Errors are logged but
    never re-raised so a DB outage never breaks the simulation response.
    """
    try:
        col = get_simulations_collection()
        if col is None:
            logger.warning(
                "MongoDB not available -- simulation %s not persisted", simulation_id
            )
            return

        request_data = sim_data.get("request", {})
        doc = {
            "simulation_id": simulation_id,
            "status": sim_data.get("status"),
            "teacher_id": request_data.get("teacher_id"),
            "request": request_data,
            "results": sim_data.get("results"),
            "runs": sim_data.get("runs", []),
            "error": sim_data.get("error"),
            "principal_retrying": sim_data.get("principal_retrying"),
            "created_at": sim_data.get("created_at", datetime.utcnow()),
            "completed_at": datetime.utcnow(),
        }
        col.replace_one({"simulation_id": simulation_id}, doc, upsert=True)
        logger.info("Simulation %s persisted to MongoDB", simulation_id)
    except Exception as exc:
        logger.error(
            "Failed to persist simulation %s to MongoDB: %s", simulation_id, exc
        )


async def _retry_principal_task(
    simulation_id: str,
    runs_raw: list,
    material_path: Optional[str],
):
    """
    Re-run principal KLI analysis on stored run data without re-running the simulation.
    Updates results.principal_notes and each run's principal_summary in store and MongoDB.
    """
    store = get_simulation_store()
    col = get_simulations_collection()

    if simulation_id in store:
        store[simulation_id]["principal_retrying"] = True
    if col is not None:
        col.update_one(
            {"simulation_id": simulation_id},
            {"$set": {"principal_retrying": True}},
        )

    try:
        chunks = parse_document(material_path) if material_path else []
        agent = PrincipalAgent()
        new_principal_notes: list = []
        updated_runs: list = []

        for run_dict in runs_raw:
            run = SimulationRun(**run_dict)
            summary = await agent.analyze_session(
                chunks=chunks,
                chunk_results=run.chunk_results,
            )
            run.principal_summary = summary
            if summary.notes:
                new_principal_notes.append(summary.notes)
            updated_runs.append(run.model_dump())

        if simulation_id in store:
            store[simulation_id]["results"]["principal_notes"] = new_principal_notes
            store[simulation_id]["runs"] = updated_runs
            store[simulation_id]["principal_retrying"] = False
            _persist_simulation_to_mongo(simulation_id, store[simulation_id])
        if col is not None:
            col.update_one(
                {"simulation_id": simulation_id},
                {
                    "$set": {
                        "results.principal_notes": new_principal_notes,
                        "runs": updated_runs,
                        "principal_retrying": False,
                    }
                },
            )
            logger.info("Principal retry for %s persisted to MongoDB", simulation_id)

    except Exception as e:
        logger.error(
            "Principal retry failed for %s: %s", simulation_id, e, exc_info=True
        )
        if simulation_id in store:
            store[simulation_id]["principal_retrying"] = False
            store[simulation_id]["results"]["principal_notes"] = store[simulation_id][
                "results"
            ].get("principal_notes", []) + [f"Retry failed: {str(e)}"]
        if col is not None:
            col.update_one(
                {"simulation_id": simulation_id},
                {"$set": {"principal_retrying": False}},
            )


async def run_simulation_task(
    simulation_id: str,
    request: StartSimulationRequest,
):
    """
    Background task to run the simulation.
    Updates simulation_store with progress and results.
    """
    store = get_simulation_store()

    try:
        # Update status to running
        store[simulation_id]["status"] = "running"
        store[simulation_id]["progress"] = "Initializing simulation..."

        # Create teacher config
        teacher_config = TeacherAgentConfig(
            teacher_id=request.teacher_id,
            name=request.teacher_name,
            personality_prompt=request.teacher_personality,
            big5_scores=request.teacher_big5,
        )

        # Map provider string to enum
        provider_map = {
            "gemini": Provider.GEMINI,
            "lmstudio": Provider.LMSTUDIO,
            "lightning": Provider.LIGHTNING,
        }
        provider = provider_map.get(request.model_provider.lower(), Provider.LIGHTNING)

        # Callback to push chat messages to store for SSE stream
        def on_message(msg: dict):
            store[simulation_id]["messages"].append(msg)

        # Callback to update progress percentage during multi-run
        def on_run_progress(run_index: int, total_runs: int):
            pct = int(100 * (run_index + 1) / total_runs) if total_runs else 0
            store[simulation_id][
                "progress"
            ] = f"Run {run_index + 1}/{total_runs} complete"
            store[simulation_id]["progress_pct"] = pct
            store[simulation_id]["current_run"] = run_index + 1

        # Create multi-run executor
        executor = MultiRunExecutor(
            material_file_path=request.material_file_path,
            teacher_config=teacher_config,
            class_name=request.class_name,
            professor_name=request.professor_name,
            model_provider=provider,
            model_name=request.model_name,
            on_message=on_message,
            on_run_progress=on_run_progress,
        )

        # Run simulations
        store[simulation_id]["progress"] = f"Running {request.num_runs} simulations..."
        store[simulation_id]["progress_pct"] = 5
        runs = await executor.run_multiple(request.num_runs)

        if not runs:
            store[simulation_id]["status"] = "failed"
            store[simulation_id]["error"] = (
                "All simulation runs failed. Check the material file format "
                "(e.g. use .pptx not old .ppt) and try again."
            )
            store[simulation_id]["progress"] = "Failed: no successful runs"
            logger.warning(
                f"Simulation {simulation_id} failed: 0/{request.num_runs} runs succeeded"
            )
            _persist_chat_history_to_mongo(
                simulation_id, store[simulation_id].get("messages", [])
            )
            _persist_simulation_to_mongo(simulation_id, store[simulation_id])
            return

        # Generate aggregated results (final report)
        store[simulation_id]["progress"] = "Generating final report..."
        store[simulation_id]["progress_pct"] = 92
        aggregated = generate_aggregated_results(runs)
        gap_details = detect_gaps_with_details(runs)

        # Store results
        store[simulation_id]["status"] = "completed"
        store[simulation_id]["results"] = {
            "total_runs": aggregated.total_runs,
            "per_chunk_avg_understanding": aggregated.per_chunk_avg_understanding,
            "gap_chunks": aggregated.gap_chunks,
            "gap_chunk_details": gap_details,
            "common_doubts": aggregated.common_doubts,
            "principal_notes": aggregated.principal_notes,
        }
        store[simulation_id]["runs"] = [run.model_dump() for run in runs]
        store[simulation_id]["progress"] = "Completed"
        store[simulation_id]["progress_pct"] = 100

        logger.info(f"Simulation {simulation_id} completed successfully")

        # Persist chat history to dedicated collection, then persist simulation doc
        _persist_chat_history_to_mongo(
            simulation_id, store[simulation_id].get("messages", [])
        )
        _persist_simulation_to_mongo(simulation_id, store[simulation_id])

    except Exception as e:
        logger.error(f"Simulation {simulation_id} failed: {e}", exc_info=True)
        store[simulation_id]["status"] = "failed"
        store[simulation_id]["error"] = str(e)
        store[simulation_id]["progress"] = f"Failed: {str(e)}"
        _persist_chat_history_to_mongo(
            simulation_id, store[simulation_id].get("messages", [])
        )
        _persist_simulation_to_mongo(simulation_id, store[simulation_id])


@router.post("/start", response_model=dict)
async def start_simulation(
    request: StartSimulationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a new simulation.

    Returns simulation_id that can be used to check status and retrieve results.
    """
    simulation_id = generate_simulation_id()
    store = get_simulation_store()

    # Initialize simulation entry
    store[simulation_id] = {
        "status": "pending",
        "progress": "Queued",
        "request": request.model_dump(),
        "results": None,
        "error": None,
        "messages": [],  # Chat messages for live stream (Teacher/Student/Principal)
        "progress_pct": 0,  # 0-100 for progress bar
        "total_runs": request.num_runs,
        "current_run": 0,
        "created_at": datetime.utcnow(),
    }

    # Start simulation in background
    background_tasks.add_task(run_simulation_task, simulation_id, request)

    logger.info(f"Started simulation {simulation_id}")

    return {
        "simulation_id": simulation_id,
        "status": "pending",
        "message": "Simulation queued successfully",
    }


@router.get("/{simulation_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status(simulation_id: str):
    """
    Check the status of a simulation.

    Falls back to MongoDB for simulations not in the current server session.
    """
    store = get_simulation_store()

    sim_data = store.get(simulation_id)

    if sim_data is None:
        col = get_simulations_collection()
        if col is not None:
            doc = col.find_one(
                {"simulation_id": simulation_id},
                {
                    "_id": 0,
                    "status": 1,
                    "error": 1,
                    "principal_retrying": 1,
                    "progress": 1,
                },
            )
            if doc:
                sim_data = doc

    if sim_data is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return SimulationStatusResponse(
        simulation_id=simulation_id,
        status=sim_data["status"],
        progress=sim_data.get("progress"),
        message=sim_data.get("error") if sim_data["status"] == "failed" else None,
        principal_retrying=sim_data.get("principal_retrying"),
    )


@router.get("/{simulation_id}/stream")
async def stream_simulation_progress(simulation_id: str):
    """
    Server-Sent Events (SSE) endpoint for real-time simulation updates.
    """
    store = get_simulation_store()

    if simulation_id not in store:
        raise HTTPException(status_code=404, detail="Simulation not found")

    async def event_generator():
        """Generate SSE events with simulation progress and chat messages."""
        last_progress = None
        last_message_count = 0

        while True:
            if simulation_id not in store:
                yield f"data: {json.dumps({'type': 'error', 'payload': {'message': 'Simulation not found'}})}\n\n"
                break

            sim_data = store[simulation_id]
            current_progress = sim_data.get("progress")
            progress_pct = sim_data.get("progress_pct", 0)
            status = sim_data["status"]
            messages = sim_data.get("messages", [])

            # Send new chat messages
            if len(messages) > last_message_count:
                for msg in messages[last_message_count:]:
                    yield f"data: {json.dumps({'type': 'message', 'payload': msg})}\n\n"
                last_message_count = len(messages)

            # Send progress/status update when changed
            if current_progress != last_progress:
                yield f"data: {json.dumps({'type': 'progress', 'payload': {'percentage': progress_pct, 'currentChunk': current_progress or '', 'totalRuns': sim_data.get('total_runs', 1), 'currentRun': sim_data.get('current_run', 0)}})}\n\n"
                yield f"data: {json.dumps({'type': 'status', 'payload': {'status': status}})}\n\n"
                last_progress = current_progress

            # Stop streaming if completed or failed
            if status in ["completed", "failed"]:
                break

            await asyncio.sleep(1)  # Poll every second

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.post("/{simulation_id}/stop")
async def stop_simulation(simulation_id: str):
    """
    Stop a running simulation.
    """
    store = get_simulation_store()

    if simulation_id not in store:
        raise HTTPException(status_code=404, detail="Simulation not found")

    sim_data = store[simulation_id]

    if sim_data["status"] not in ["pending", "running"]:
        return {
            "simulation_id": simulation_id,
            "status": sim_data["status"],
            "message": f"Simulation already {sim_data['status']}",
        }

    # Mark as stopped
    store[simulation_id]["status"] = "stopped"
    store[simulation_id]["progress"] = "Stopped by user"

    logger.info(f"Simulation {simulation_id} stopped by user")

    return {
        "simulation_id": simulation_id,
        "status": "stopped",
        "message": "Simulation stopped successfully",
    }


@router.get("/{simulation_id}/results", response_model=SimulationResultResponse)
async def get_simulation_results(simulation_id: str):
    """
    Get the final aggregated results of a completed simulation.

    Checks the in-memory store first (for simulations completed in this
    server session), then falls back to MongoDB for historical simulations.
    """
    store = get_simulation_store()

    sim_data = store.get(simulation_id)

    # Fall back to MongoDB if not found in-memory
    if sim_data is None:
        col = get_simulations_collection()
        if col is not None:
            doc = col.find_one({"simulation_id": simulation_id}, {"_id": 0})
            if doc:
                sim_data = doc

    if sim_data is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if sim_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation is not completed. Current status: {sim_data['status']}",
        )

    results = sim_data["results"]

    return SimulationResultResponse(
        simulation_id=simulation_id,
        total_runs=results["total_runs"],
        per_chunk_avg_understanding=results["per_chunk_avg_understanding"],
        gap_chunks=results["gap_chunks"],
        gap_chunk_details=results.get("gap_chunk_details", []),
        common_doubts=results["common_doubts"],
        principal_notes=results["principal_notes"],
        principal_retrying=sim_data.get("principal_retrying"),
    )


@router.post("/{simulation_id}/retry-principal")
async def retry_principal_analysis(
    simulation_id: str,
    background_tasks: BackgroundTasks,
):
    """
    Re-run the principal KLI analysis on stored run data without re-running the simulation.
    Use when principal observations failed or are incomplete.
    """
    store = get_simulation_store()
    sim_data = store.get(simulation_id)

    if sim_data is None:
        col = get_simulations_collection()
        if col is not None:
            doc = col.find_one({"simulation_id": simulation_id}, {"_id": 0})
            if doc:
                sim_data = doc

    if sim_data is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Simulation must be completed first",
        )
    if sim_data.get("principal_retrying"):
        raise HTTPException(
            status_code=400,
            detail="Principal analysis retry already in progress",
        )

    runs_raw = sim_data.get("runs", [])
    if not runs_raw:
        raise HTTPException(
            status_code=400,
            detail="No run data found to retry",
        )

    request_data = sim_data.get("request", {})
    material_path = request_data.get("material_file_path")

    background_tasks.add_task(
        _retry_principal_task,
        simulation_id,
        runs_raw,
        material_path,
    )

    return {
        "simulation_id": simulation_id,
        "message": "Principal analysis retry started",
    }

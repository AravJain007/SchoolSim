"""
Heatmap and Report Routes
Handles downloading annotated PDFs/PPTs and reports.
"""

import os

from dependencies import get_simulation_store
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from aggregation.report_generator import generate_aggregated_results
from api.db import get_simulations_collection
from output import export_json_report, export_pdf_report, generate_heatmap
from output.annotation_writer import add_gap_annotations
from pydantic_classes import AggregatedResults, SimulationRun

router = APIRouter(tags=["heatmap"])


def _get_sim_data(simulation_id: str) -> dict | None:
    """
    Look up simulation data from in-memory store, then fall back to MongoDB.
    Returns None if not found in either source.
    """
    store = get_simulation_store()
    sim_data = store.get(simulation_id)
    if sim_data is not None:
        return sim_data
    try:
        col = get_simulations_collection()
        if col is not None:
            doc = col.find_one({"simulation_id": simulation_id}, {"_id": 0})
            if doc:
                return doc
    except Exception:
        pass
    return None


@router.get("/heatmap/{simulation_id}")
async def download_heatmap(simulation_id: str):
    """
    Download annotated PDF/PPT with heatmap overlay.

    Falls back to MongoDB for simulations not in the current server session.
    The heatmap highlights difficult chunks based on student understanding.
    """
    sim_data = _get_sim_data(simulation_id)

    if sim_data is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if sim_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation not completed. Status: {sim_data['status']}",
        )

    # Get material file path from request
    request_data = sim_data.get("request", {})
    material_path = request_data.get("material_file_path")

    if not material_path or not os.path.exists(material_path):
        raise HTTPException(status_code=404, detail="Original material file not found")

    # Build AggregatedResults from stored results
    results_data = sim_data.get("results", {})
    if not results_data:
        raise HTTPException(
            status_code=400, detail="No aggregated results found for this simulation"
        )

    try:
        aggregated_results = AggregatedResults(**results_data)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to parse simulation results: {str(e)}"
        )

    try:
        # generate_heatmap copies the original, overlays colors, and returns the new file path
        output_path = generate_heatmap(
            original_file=material_path,
            aggregated_results=aggregated_results,
        )

        # Add gap annotations (footer notes for each gap chunk)
        add_gap_annotations(output_path, aggregated_results)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate heatmap: {str(e)}"
        )

    if not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Heatmap generation failed")

    ext = os.path.splitext(material_path)[1].lower()
    media_types = {
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".ppt": "application/vnd.ms-powerpoint",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    return FileResponse(
        output_path,
        media_type=media_type,
        filename=f"heatmap_{simulation_id}{ext}",
    )


@router.get("/report/{simulation_id}")
async def download_report(simulation_id: str, format: str = "json"):
    """
    Download simulation report.

    Falls back to MongoDB for simulations not in the current server session.
    Supports JSON and PDF formats.
    """
    sim_data = _get_sim_data(simulation_id)

    if sim_data is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    if sim_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Simulation not completed. Status: {sim_data['status']}",
        )

    # Get runs data and build aggregated results
    runs_data = sim_data.get("runs", [])
    runs = [SimulationRun(**run) for run in runs_data]
    aggregated_results = generate_aggregated_results(runs)

    try:
        if format.lower() == "json":
            output_path = f"/tmp/report_{simulation_id}.json"
            export_json_report(aggregated_results, output_path)
            media_type = "application/json"
            filename = f"report_{simulation_id}.json"

        elif format.lower() == "pdf":
            output_path = f"/tmp/report_{simulation_id}.pdf"
            export_pdf_report(aggregated_results, output_path)
            media_type = "application/pdf"
            filename = f"report_{simulation_id}.pdf"

        else:
            raise HTTPException(
                status_code=400, detail="Invalid format. Use 'json' or 'pdf'"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}"
        )

    if not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Report generation failed")

    return FileResponse(
        output_path,
        media_type=media_type,
        filename=filename,
    )

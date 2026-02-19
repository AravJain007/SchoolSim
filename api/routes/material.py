"""
Material Routes
Handles course material upload and chunk preview.
"""

import os
import shutil
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from material_parser.parser import parse_document
from pydantic_classes import ChunkDetails

router = APIRouter(prefix="/material", tags=["material"])

# Directory for uploaded materials
UPLOAD_DIR = "/tmp/sims_teacher_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ChunkPreviewResponse(BaseModel):
    material_id: str
    file_path: str
    total_chunks: int
    chunks: List[dict]


@router.post("/upload")
async def upload_material(file: UploadFile = File(...)):
    """
    Upload a course material file (PDF, PPT, PPTX, DOC, DOCX).

    Returns the file path that can be used in simulation requests.
    """
    # Validate file extension
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".pdf", ".ppt", ".pptx", ".doc", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: PDF, PPT, PPTX, DOC, DOCX",
        )

    # Save file with unique name
    import uuid

    material_id = str(uuid.uuid4())
    safe_filename = f"{material_id}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    return {
        "material_id": material_id,
        "filename": filename,
        "file_path": file_path,
        "message": "File uploaded successfully",
    }


@router.get("/{material_id}/chunks", response_model=ChunkPreviewResponse)
async def get_material_chunks(material_id: str):
    """
    Get parsed chunks for preview.

    Note: material_id is the file path returned from upload endpoint.
    For simplicity, we accept the full file path here.
    """
    # In a real implementation, you'd look up the file path from material_id
    # For simplicity, we'll treat material_id as the file path or search for it

    # Check if material_id is a full path
    if os.path.exists(material_id):
        file_path = material_id
    else:
        # Search in upload directory
        matching_files = [
            f for f in os.listdir(UPLOAD_DIR) if f.startswith(material_id)
        ]

        if not matching_files:
            raise HTTPException(status_code=404, detail="Material not found")

        file_path = os.path.join(UPLOAD_DIR, matching_files[0])

    try:
        chunks = parse_document(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to parse document: {str(e)}"
        )

    return ChunkPreviewResponse(
        material_id=material_id,
        file_path=file_path,
        total_chunks=len(chunks),
        chunks=[chunk.model_dump() for chunk in chunks],
    )

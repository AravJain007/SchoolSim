"""
Teacher Routes
Handles teacher registration, listing, and class management.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient

from api.db import get_simulations_collection
from api.lib.teacher_models import TeacherCreate, TeacherListItem, TeacherResponse

router = APIRouter(prefix="/teacher", tags=["teacher"])

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_SERVER")
DB_NAME = "b5"
TEACHERS_COLLECTION = "teachers"


def get_teachers_collection():
    """Get the teachers collection from MongoDB."""
    if not MONGO_URI:
        return None
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME][TEACHERS_COLLECTION]


class ClassInfo(BaseModel):
    location: str
    total_students: int = 0


class SimulationInfo(BaseModel):
    simulation_id: str
    status: str
    timestamp: str


class DashboardResponse(BaseModel):
    teacher_id: str
    total_classes: int
    total_simulations: int
    recent_simulations: List[SimulationInfo]


@router.post("/register", response_model=TeacherResponse)
async def register_teacher(teacher: TeacherCreate):
    """
    Register a new teacher with their classes.
    """
    collection = get_teachers_collection()

    if collection is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available. Check MONGO_SERVER environment variable.",
        )

    # Check if teacher with same name already exists
    existing = collection.find_one({"name": teacher.name})
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Teacher with name '{teacher.name}' already exists.",
        )

    # Create teacher document
    teacher_id = str(uuid.uuid4())
    teacher_doc = {
        "teacher_id": teacher_id,
        "name": teacher.name,
        "email": teacher.email,
        "department": teacher.department,
        "classes": teacher.classes,
        "created_at": datetime.utcnow(),
    }

    try:
        collection.insert_one(teacher_doc)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to register teacher: {str(e)}"
        )

    return TeacherResponse(
        teacher_id=teacher_id,
        name=teacher.name,
        email=teacher.email,
        department=teacher.department,
        classes=teacher.classes,
    )


@router.get("/list", response_model=List[TeacherListItem])
async def list_teachers():
    """
    Returns a list of registered teachers.
    """
    collection = get_teachers_collection()

    if collection is None:
        # Return empty list if DB not available
        return []

    try:
        teachers = collection.find({}, {"teacher_id": 1, "name": 1, "_id": 0})
        return [TeacherListItem(**t) for t in teachers]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch teachers: {str(e)}"
        )


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(teacher_id: str):
    """
    Get a specific teacher by ID.
    """
    collection = get_teachers_collection()

    if collection is None:
        raise HTTPException(status_code=503, detail="Database not available")

    teacher = collection.find_one({"teacher_id": teacher_id})

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return TeacherResponse(
        teacher_id=teacher["teacher_id"],
        name=teacher["name"],
        email=teacher.get("email"),
        department=teacher.get("department"),
        classes=teacher.get("classes", []),
    )


@router.get("/{teacher_id}/classes", response_model=List[str])
async def get_teacher_classes(teacher_id: str):
    """
    List classes registered by a teacher.
    Returns a simple list of class location strings.
    """
    collection = get_teachers_collection()

    if collection is None:
        raise HTTPException(status_code=503, detail="Database not available")

    teacher = collection.find_one({"teacher_id": teacher_id})

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return teacher.get("classes", [])


class ClassWithStudents(BaseModel):
    name: str
    student_count: int


def get_results_collection():
    """Get the Big5 results collection from MongoDB."""
    if not MONGO_URI:
        return None
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME]["results"]


@router.get(
    "/{teacher_id}/classes-with-students", response_model=List[ClassWithStudents]
)
async def get_teacher_classes_with_students(teacher_id: str):
    """
    List classes registered by a teacher with the number of students in each.
    Student count is based on Big5 results submitted for that class location.
    """
    teachers_collection = get_teachers_collection()
    results_collection = get_results_collection()

    if teachers_collection is None:
        raise HTTPException(status_code=503, detail="Database not available")

    teacher = teachers_collection.find_one({"teacher_id": teacher_id})

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    classes = teacher.get("classes", [])
    classes_with_counts = []

    for class_name in classes:
        student_count = 0
        if results_collection is not None:
            try:
                # Count unique students by collegeId for this class location
                student_count = results_collection.count_documents(
                    {"classLocation": class_name}
                )
            except Exception:
                pass  # If count fails, default to 0

        classes_with_counts.append(
            ClassWithStudents(name=class_name, student_count=student_count)
        )

    return classes_with_counts


@router.get("/{teacher_id}/simulations", response_model=List[SimulationInfo])
async def get_teacher_simulations(teacher_id: str):
    """
    List past simulations for a teacher.

    Merges in-memory (live/recent) and MongoDB (historical) data so that
    simulations from previous server sessions are included.
    """
    from api.dependencies import get_simulation_store

    store = get_simulation_store()

    # Collect in-memory simulations for this teacher
    seen_ids: set = set()
    teacher_simulations: List[SimulationInfo] = []

    for sim_id, sim_data in store.items():
        request_data = sim_data.get("request", {})
        if request_data.get("teacher_id") == teacher_id:
            ts = sim_data.get("created_at") or sim_data.get("timestamp") or ""
            ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
            teacher_simulations.append(
                SimulationInfo(
                    simulation_id=sim_id,
                    status=sim_data["status"],
                    timestamp=ts_str,
                )
            )
            seen_ids.add(sim_id)

    # Add historical simulations from MongoDB not already in-memory
    try:
        col = get_simulations_collection()
        if col is not None:
            for doc in col.find(
                {"teacher_id": teacher_id},
                {"simulation_id": 1, "status": 1, "created_at": 1, "_id": 0},
            ):
                sim_id = doc.get("simulation_id")
                if sim_id and sim_id not in seen_ids:
                    ts = doc.get("created_at") or ""
                    ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
                    teacher_simulations.append(
                        SimulationInfo(
                            simulation_id=sim_id,
                            status=doc.get("status", "unknown"),
                            timestamp=ts_str,
                        )
                    )
    except Exception:
        pass  # MongoDB unavailable -- return in-memory data only

    return teacher_simulations


@router.get("/{teacher_id}/dashboard", response_model=DashboardResponse)
async def get_teacher_dashboard(teacher_id: str):
    """
    Get dashboard summary data for a teacher.

    Simulation counts and recent-simulation lists include historical data
    from MongoDB in addition to any in-memory (live/current-session) entries.
    """
    from api.dependencies import get_simulation_store

    store = get_simulation_store()
    collection = get_teachers_collection()

    # Get teacher's classes count
    total_classes = 0
    if collection is not None:
        teacher = collection.find_one({"teacher_id": teacher_id})
        if teacher:
            total_classes = len(teacher.get("classes", []))

    # Collect in-memory simulations for this teacher
    seen_ids: set = set()
    all_sims: List[dict] = []

    for sim_id, sim_data in store.items():
        if sim_data.get("request", {}).get("teacher_id") == teacher_id:
            ts = sim_data.get("created_at") or sim_data.get("timestamp") or ""
            ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
            all_sims.append(
                {
                    "simulation_id": sim_id,
                    "status": sim_data["status"],
                    "timestamp": ts_str,
                }
            )
            seen_ids.add(sim_id)

    # Merge historical simulations from MongoDB
    try:
        col = get_simulations_collection()
        if col is not None:
            for doc in col.find(
                {"teacher_id": teacher_id},
                {"simulation_id": 1, "status": 1, "created_at": 1, "_id": 0},
            ):
                sim_id = doc.get("simulation_id")
                if sim_id and sim_id not in seen_ids:
                    ts = doc.get("created_at") or ""
                    ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
                    all_sims.append(
                        {
                            "simulation_id": sim_id,
                            "status": doc.get("status", "unknown"),
                            "timestamp": ts_str,
                        }
                    )
    except Exception:
        pass

    # Get recent simulations (last 5, sorted by timestamp descending)
    recent = sorted(all_sims, key=lambda x: x["timestamp"], reverse=True)[:5]

    return DashboardResponse(
        teacher_id=teacher_id,
        total_classes=total_classes,
        total_simulations=len(all_sims),
        recent_simulations=[SimulationInfo(**sim) for sim in recent],
    )

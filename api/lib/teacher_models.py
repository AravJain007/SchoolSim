"""
Teacher Models
Pydantic models for teacher registration and management.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TeacherCreate(BaseModel):
    """Request model for creating a new teacher."""

    name: str = Field(..., description="Full name of the teacher")
    email: Optional[str] = Field(None, description="Email address (optional)")
    department: Optional[str] = Field(None, description="Department name (optional)")
    classes: List[str] = Field(
        default_factory=list,
        description="List of class locations this teacher teaches (e.g., ['SJT301', 'CDMM102'])",
    )


class TeacherInDB(BaseModel):
    """Model representing a teacher as stored in MongoDB."""

    teacher_id: str
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    classes: List[str] = []
    created_at: datetime


class TeacherResponse(BaseModel):
    """Response model for teacher data."""

    teacher_id: str
    name: str
    email: Optional[str] = None
    department: Optional[str] = None
    classes: List[str] = []


class TeacherListItem(BaseModel):
    """Simplified teacher info for list endpoints."""

    teacher_id: str
    name: str

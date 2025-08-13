from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Optional

import gridfs
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo import MongoClient


def _parse_resume_from_pdf_bytes(pdf_bytes: bytes) -> Optional[str]:
    """Extract text from a PDF resume.

    Attempts to use MarkItDown first, then falls back to PyPDF.
    Returns plain text (or markdown) if extracted, else None.
    """
    # Try MarkItDown (rich, LaTeX-aware where applicable)
    try:
        from markitdown import MarkItDown  # type: ignore

        md = MarkItDown()
        text_content: Optional[str] = None

        # Different versions expose different helpers; try a few.
        try:
            result = md.convert(pdf_bytes)  # some versions accept raw bytes
            text_content = getattr(result, "text_content", None) or (
                result if isinstance(result, str) else None
            )
        except Exception:
            try:
                # common signature: convert_bytes(bytes, mime=...)
                result = md.convert_bytes(pdf_bytes, mime="application/pdf")  # type: ignore[attr-defined]
                text_content = getattr(result, "text_content", None) or (
                    result if isinstance(result, str) else None
                )
            except Exception:
                text_content = None

        if text_content:
            return text_content.strip()
    except Exception:
        pass

    # Fallback: PyPDF text extraction
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages_text: List[str] = []
        for page in reader.pages:
            try:
                pages_text.append(page.extract_text() or "")
            except Exception:
                pages_text.append("")
        text = "\n\n".join(t for t in pages_text if t)
        return text.strip() if text else None
    except Exception:
        return None


class StudentDetails(BaseModel):
    name: str = Field(default="", description="Student full name")
    college_id: str = Field(default="", description="College ID")
    info: Dict[str, Optional[str]]
    domain_results: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of Big Five domain title to the language-based result text.",
    )
    personality_text: str = Field(
        default="",
        description="Concatenated textual summary across domains for easy display.",
    )
    resume_text: Optional[str] = Field(
        default=None,
        description="Plain text (or markdown) extracted from the PDF resume",
    )


class ClassroomDetails(BaseModel):
    location: str
    students: List[StudentDetails]
    total: int


class ClassroomService:
    """Synchronous service to fetch classroom details by location from MongoDB.

    This service expects documents shaped like the ones saved by `app.py`:
    - Collection: b5.results
    - Each document includes `userName`, `collegeId`, `teacherName`, `classLocation`,
      `resultSummary` (per-domain details including `title` and `resultText`), and
      `resume.fileId` (GridFS id).
    """

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "b5",
        results_collection: str = "results",
    ) -> None:
        self._client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        self._db = self._client[db_name]
        self._col = self._db[results_collection]
        self._fs = gridfs.GridFS(self._db)

    def get_classroom_details(
        self, location: str, limit: Optional[int] = None
    ) -> ClassroomDetails:
        query = {"classLocation": location}
        cursor = self._col.find(query).sort("dateStamp", 1)
        if limit is not None:
            cursor = cursor.limit(int(limit))

        students: List[StudentDetails] = []
        for doc in cursor:
            # Build domain -> text mapping from the stored resultSummary
            domain_results: Dict[str, str] = {}
            result_summary: Dict[str, Any] = doc.get("resultSummary", {}) or {}
            for _domain_letter, domain_data in result_summary.items():
                title = domain_data.get("title") or _domain_letter
                text = domain_data.get("resultText") or ""
                if text:
                    domain_results[str(title)] = str(text)

            personality_text = "\n\n".join(
                f"{title}: {text}" for title, text in domain_results.items() if text
            )

            # Get resume text from GridFS when available
            resume_text: Optional[str] = None
            resume_info: Dict[str, Any] = doc.get("resume", {}) or {}
            file_id_str: Optional[str] = resume_info.get("fileId") or None
            if file_id_str:
                try:
                    file_obj = self._fs.get(ObjectId(file_id_str))
                    resume_bytes = file_obj.read()
                    resume_text = _parse_resume_from_pdf_bytes(resume_bytes)
                except Exception:
                    resume_text = None

            info: Dict[str, Optional[str]] = {
                "teacherName": doc.get("teacherName"),
                "classLocation": doc.get("classLocation"),
                "sessionId": doc.get("sessionId"),
                "dateStamp": doc.get("dateStamp").isoformat()
                if isinstance(doc.get("dateStamp"), datetime)
                else (
                    str(doc.get("dateStamp"))
                    if doc.get("dateStamp") is not None
                    else None
                ),
                "resultVersion": str(doc.get("version"))
                if doc.get("version") is not None
                else None,
            }

            students.append(
                StudentDetails(
                    name=str(doc.get("userName", "")),
                    college_id=str(doc.get("collegeId", "")),
                    info=info,
                    domain_results=domain_results,
                    personality_text=personality_text,
                    resume_text=resume_text,
                )
            )

        return ClassroomDetails(
            location=location, students=students, total=len(students)
        )


__all__ = [
    "ClassroomService",
    "ClassroomDetails",
    "StudentDetails",
]

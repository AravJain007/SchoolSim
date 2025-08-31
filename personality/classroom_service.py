from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

import gridfs
from bson import ObjectId
from markitdown import MarkItDown
from pymongo import MongoClient
from sympy import Domain

from pydantic_classes import ClassroomDetails, DomainScore, StudentDetails


def _parse_resume_from_pdf_bytes(pdf_bytes: bytes) -> Optional[str]:
    """Extract text from a PDF resume. Attempts to use MarkItDown first, then falls back to PyPDF.
    Returns plain text (or markdown) if extracted, else None.
    """
    try:
        md = MarkItDown()
        result = md.convert_stream(io.BytesIO(pdf_bytes))
        text_content: Optional[str] = result.text_content

        if text_content:
            return text_content.strip()
    except Exception as e:
        print("Using markitdown did not work")
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
    ):
        """Initializes the MongoDB client and database connections once."""
        self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        self.db = self.mongo_client[db_name]
        self._col = self.db[results_collection]
        self._fs = gridfs.GridFS(self.db)
        print("MongoDB client initialized.")

    def close_client(self):
        """Closes the MongoDB connection."""
        self.mongo_client.close()
        print("MongoDB client closed.")

    # Implement context manager for automatic connection closing
    def __enter__(self):
        return self

    def __exit__(self):
        self.close_client()

    def get_classroom_details(
        self,
        location: str,
        professor_name: str,
        limit: Optional[int] = None,
    ) -> ClassroomDetails:
        """This function is used to fetch all the details of the entire classroom.

        Parameters
        ----------
            location: str
                Location of the classroom
            professor_name: str
                Name of the professor who teaches that class
            limit: Optional[int]
                Limit the number of students returned on the basis of timestamp (LIFO)

        Returns
        -------
            ClassroomDetails
                Returns the StudentDetails of the entire class
        """
        query = {"classLocation": location, "teacherName": professor_name}
        cursor = self._col.find(query).sort("dateStamp", 1)
        if limit is not None:
            cursor = cursor.limit(int(limit))

        students: List[StudentDetails] = []

        for doc in cursor:
            domain_results: List[DomainScore] = []
            personality_text: str = ""
            result_summary: Dict[str, Any] = doc.get("resultSummary")
            for index, (_, domain_data) in enumerate(result_summary.items(), 1):
                domain_title = domain_data.get("title")
                domain_result_text = domain_data.get("resultText")
                domain_result = domain_data.get("result")
                domain_score = domain_data.get("score")
                domain_count = domain_data.get("count") * 5
                personality_text += f"""### {index}. {domain_title}\n- Score: {domain_score} out of {domain_count}, which is a {domain_result} score.\n- Definition: {domain_result_text}\n- Facets:\n"""
                facet = domain_data.get("facets")
                facet_score_dictionary = {}
                for _, facet_data in facet.items():
                    facet_description = facet_data.get("description")
                    facet_score = facet_data.get("score")
                    facet_title = facet_data.get("title")
                    facet_result = facet_data.get("result")
                    facet_count = facet_data.get("count") * 5
                    facet_score_dictionary[facet_title] = facet_score
                    personality_text += f"""\t- {facet_title}: {facet_description} Your score is {facet_score} out of {facet_count} which is {facet_result}.\n"""
                domain_results.append(
                    DomainScore(score=domain_score, facet_scores=facet_score_dictionary)
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

            info: Dict[str, Any] = {
                "teacherName": doc.get("teacherName"),
                "classLocation": doc.get("classLocation"),
                "sessionId": doc.get("sessionId"),
                "dateStamp": doc.get("dateStamp"),
                "resultVersion": doc.get("version"),
            }

            students.append(
                StudentDetails(
                    name=str(doc.get("userName", "")),
                    college_id=str(doc.get("collegeId", "")),
                    info=info,
                    domain_score=domain_results,
                    personality_text=personality_text,
                    resume_text=resume_text,
                )
            )

        return ClassroomDetails(
            location=location, students=students, total=len(students)
        )

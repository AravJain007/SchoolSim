import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient

from api.lib.big5.big5_results import BIG5_RESULTS

router = APIRouter(prefix="/big5", tags=["student_big5"])

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_SERVER")
DB_NAME = "b5"


def get_db():
    if not MONGO_URI:
        return None
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME]


# -----------------------------------------------------------
# Pydantic Models for Self-Report (new approach)
# -----------------------------------------------------------


class DomainScoreInput(BaseModel):
    """Single domain score with required facet breakdown."""

    score: int = Field(..., ge=0, le=120, description="Total domain score (0-120)")
    facets: Dict[int, int] = Field(
        ..., description="Required facet scores (1-6), each 0-20"
    )


class SelfReportSubmission(BaseModel):
    """Self-report submission for students."""

    session_id: str
    user_name: str
    college_id: str
    teacher_name: str
    class_location: str
    domain_scores: Dict[str, DomainScoreInput]  # Keys: O, C, E, A, N


class TeacherSelfReportSubmission(BaseModel):
    """Self-report submission for teachers."""

    session_id: str
    teacher_id: str
    teacher_name: str
    domain_scores: Dict[str, DomainScoreInput]  # Keys: O, C, E, A, N


class Big5Response(BaseModel):
    result_summary: Dict[str, Any]
    inserted_id: str


# -----------------------------------------------------------
# Self-Report Endpoints (Primary - New Approach)
# -----------------------------------------------------------


def calculate_result_category(score: int, question_count: int = 24) -> str:
    """
    Calculate high/neutral/low based on domain score.

    Uses bigfive-web's average-based thresholds:
    - Average > 3.5 => HIGH
    - Average < 2.5 => LOW
    - Average 2.5-3.5 => NEUTRAL

    For self-reported scores:
    - Domain score is 0-120 from 24 questions (avg = score/24)

    Args:
        score: The total score (0-120 for domains)
        question_count: Number of questions (default 24 for domains)
    """
    avg_score = score / question_count
    if avg_score > 3.5:
        return "high"
    elif avg_score < 2.5:
        return "low"
    return "neutral"


def calculate_facet_category(score: int, question_count: int = 4) -> str:
    """
    Calculate high/neutral/low based on facet score.

    Uses bigfive-web's average-based thresholds:
    - Average > 3.5 => HIGH
    - Average < 2.5 => LOW
    - Average 2.5-3.5 => NEUTRAL

    For self-reported scores:
    - Facet score is 0-20 from 4 questions (avg = score/4)

    Args:
        score: The total score (0-20 for facets)
        question_count: Number of questions (default 4 for facets)
    """
    avg_score = score / question_count
    if avg_score > 3.5:
        return "high"
    elif avg_score < 2.5:
        return "low"
    return "neutral"


def build_result_summary(domain_scores: Dict[str, DomainScoreInput]) -> Dict[str, Any]:
    """Build the result summary from self-reported domain scores."""
    results = BIG5_RESULTS
    results_by_domain_letter = {v["domain"]: v for v in results.values()}

    # Build facet details lookup
    domain_facet_details = {}
    for d_letter, meta in results_by_domain_letter.items():
        facet_detail_map = {
            f["facet"]: {
                "title": f.get("title"),
                "description": f.get("text"),
            }
            for f in meta.get("facets", [])
        }
        domain_facet_details[d_letter] = {
            "title": meta.get("title"),
            "shortDescription": meta.get("shortDescription"),
            "facets": facet_detail_map,
        }

    result_summary = {}

    for domain_letter, domain_input in domain_scores.items():
        meta = results_by_domain_letter.get(domain_letter, {})
        domain_score = domain_input.score
        domain_result = calculate_result_category(domain_score)

        # Get the result text for this category
        domain_text = ""
        for r in meta.get("results", []):
            if r.get("score") == domain_result:
                domain_text = r.get("text", "")
                break

        # Build facet breakdown (required)
        facet_breakdown = {}
        facet_details_map = domain_facet_details.get(domain_letter, {}).get(
            "facets", {}
        )

        for facet_num, facet_score in domain_input.facets.items():
            facet_result = calculate_facet_category(facet_score)
            facet_breakdown[str(facet_num)] = {
                "score": facet_score,
                "result": facet_result,
                "title": facet_details_map.get(int(facet_num), {}).get("title"),
                "description": facet_details_map.get(int(facet_num), {}).get(
                    "description"
                ),
            }

        result_summary[domain_letter] = {
            "title": meta.get("title"),
            "shortDescription": meta.get("shortDescription"),
            "score": domain_score,
            "resultText": domain_text,
            "facets": facet_breakdown,
        }

    return result_summary


@router.post("/self-report")
async def submit_self_report(submission: SelfReportSubmission):
    """
    Submit self-reported Big 5 scores for students.
    This is the primary endpoint - scores are entered directly without taking the test.
    All domain scores and facet scores are required.
    """
    # Validate required domains
    required_domains = {"O", "C", "E", "A", "N"}
    provided_domains = set(submission.domain_scores.keys())
    if not required_domains.issubset(provided_domains):
        missing = required_domains - provided_domains
        raise HTTPException(
            status_code=400,
            detail=f"Missing required domain scores: {', '.join(missing)}",
        )

    # Validate all facets are provided (1-6 for each domain)
    for domain_letter, domain_input in submission.domain_scores.items():
        if not domain_input.facets:
            raise HTTPException(
                status_code=400,
                detail=f"Missing facet scores for domain {domain_letter}",
            )
        provided_facets = set(domain_input.facets.keys())
        required_facets = {1, 2, 3, 4, 5, 6}
        if not required_facets.issubset(provided_facets):
            missing = required_facets - provided_facets
            raise HTTPException(
                status_code=400,
                detail=f"Missing facets {missing} for domain {domain_letter}",
            )
        # Validate facet score range
        for facet_num, facet_score in domain_input.facets.items():
            if facet_score < 0 or facet_score > 20:
                raise HTTPException(
                    status_code=400,
                    detail=f"Facet {facet_num} score for {domain_letter} must be between 0 and 20",
                )

    # Build result summary
    result_summary = build_result_summary(submission.domain_scores)

    # Persist to MongoDB
    db = get_db()
    inserted_id = "mock_id_no_db"

    if db is not None:
        try:
            collection_name = "results"

            # Build domain scores for storage (simplified - no question-level data)
            stored_domain_scores = {}
            for domain_letter, domain_input in submission.domain_scores.items():
                stored_domain_scores[domain_letter] = {
                    "score": domain_input.score,
                    "facets": {
                        str(k): v for k, v in domain_input.facets.items()
                    },  # Convert int keys to strings for MongoDB
                }

            doc = {
                "sessionId": submission.session_id,
                "userName": submission.user_name,
                "collegeId": submission.college_id,
                "teacherName": submission.teacher_name,
                "classLocation": submission.class_location,
                "domainScores": stored_domain_scores,  # Simplified storage
                "resultSummary": result_summary,
                "submissionType": "self-report",  # Mark as self-reported
                "dateStamp": datetime.utcnow(),
                "app": "sims-teacher-big5-api",
                "version": 2,  # New version for self-report format
            }
            result = db[collection_name].insert_one(doc)
            inserted_id = str(result.inserted_id)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to save results: {str(e)}"
            )

    return {"result_summary": result_summary, "inserted_id": inserted_id}


@router.post("/teacher/self-report")
async def submit_teacher_self_report(submission: TeacherSelfReportSubmission):
    """
    Submit self-reported Big 5 scores for teachers.
    All domain scores and facet scores are required.
    """
    # Validate required domains
    required_domains = {"O", "C", "E", "A", "N"}
    provided_domains = set(submission.domain_scores.keys())
    if not required_domains.issubset(provided_domains):
        missing = required_domains - provided_domains
        raise HTTPException(
            status_code=400,
            detail=f"Missing required domain scores: {', '.join(missing)}",
        )

    # Validate all facets are provided (1-6 for each domain)
    for domain_letter, domain_input in submission.domain_scores.items():
        if not domain_input.facets:
            raise HTTPException(
                status_code=400,
                detail=f"Missing facet scores for domain {domain_letter}",
            )
        provided_facets = set(domain_input.facets.keys())
        required_facets = {1, 2, 3, 4, 5, 6}
        if not required_facets.issubset(provided_facets):
            missing = required_facets - provided_facets
            raise HTTPException(
                status_code=400,
                detail=f"Missing facets {missing} for domain {domain_letter}",
            )
        # Validate facet score range
        for facet_num, facet_score in domain_input.facets.items():
            if facet_score < 0 or facet_score > 20:
                raise HTTPException(
                    status_code=400,
                    detail=f"Facet {facet_num} score for {domain_letter} must be between 0 and 20",
                )

    # Build result summary
    result_summary = build_result_summary(submission.domain_scores)

    # Persist to MongoDB
    db = get_db()
    inserted_id = "mock_id_no_db"

    if db is not None:
        try:
            collection_name = "teacher_results"

            # Build domain scores for storage
            stored_domain_scores = {}
            for domain_letter, domain_input in submission.domain_scores.items():
                stored_domain_scores[domain_letter] = {
                    "score": domain_input.score,
                    "facets": {
                        str(k): v for k, v in domain_input.facets.items()
                    },  # Convert int keys to strings for MongoDB
                }

            doc = {
                "sessionId": submission.session_id,
                "teacherId": submission.teacher_id,
                "teacherName": submission.teacher_name,
                "domainScores": stored_domain_scores,
                "resultSummary": result_summary,
                "submissionType": "self-report",
                "dateStamp": datetime.utcnow(),
                "app": "sims-teacher-big5-api",
                "version": 2,
                "type": "teacher",
            }
            result = db[collection_name].insert_one(doc)
            inserted_id = str(result.inserted_id)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to save results: {str(e)}"
            )

    return {"result_summary": result_summary, "inserted_id": inserted_id}

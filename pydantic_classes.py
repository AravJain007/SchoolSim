from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, input_prompt: str, model_name: str):
        ...


class Provider(str, Enum):
    GEMINI = "gemini"
    LMSTUDIO = "lmstudio"
    LIGHTNING = "lightning"


class ReasoningEffort(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class LLMCallInput(BaseModel):
    developer_prompt_provided: bool = Field(
        default=False, description="Have you provided a developer prompt"
    )
    system_prompt_provided: bool = Field(
        default=False, description="Have you provided a system prompt"
    )
    system_prompt_to_llm: Optional[str] = Field(
        default=None, description="The system prompt to provide to the GPT OSS Model"
    )
    developer_prompt_to_llm: Optional[str] = Field(
        default=None, description="Developer Prompt to the GPT OSS Model"
    )
    user_prompt_to_llm: str = Field(
        ..., min_length=1, description="The prompt provided as an input to the LLM"
    )
    model_provider: Provider = Field(
        ...,
        description="""Choose on of the available providers.
        If the provider of your choice has not been provided kindly create a custom class and add it to llm_call.py file.""",
    )
    model_name: str = Field(
        ..., min_length=1, description="Name of the model available from the provider"
    )
    reasoning_effort: ReasoningEffort = Field(
        default=ReasoningEffort.HIGH,
        description="Specifies the reasoning effort for the LLM",
    )


class LLMResult(BaseModel):
    status: int = Field(
        ...,
        description="Response code from LLM. Tells us if we were successfully able to get an output from the LLM",
    )
    response: str | Any = Field(..., description="Response from the LLM")
    response_reasoning: str | Any = Field(..., description="Reasoning for response")
    cost: Optional[float] = Field(
        default=None, description="Cost of the call in US Dollars"
    )


class DomainScore(BaseModel):
    score: int = Field(..., description="Total Score for the domain")
    facet_scores: Dict[str, int] = Field(..., description="Facet wise score")


class StudentDetails(BaseModel):
    name: str = Field(default="", description="Student full name")
    college_id: str = Field(default="", description="College ID")
    info: Dict[str, Any]
    domain_score: List[DomainScore] = Field(
        ...,
        description="Mapping of Big Five domain title to the language-based result text.",
    )
    personality_text: str = Field(
        default="",
        description="Concatenated textual summary across domains for easy display.",
    )


class ClassroomDetails(BaseModel):
    location: str
    students: List[StudentDetails]
    total: int


class PersonalitiesOfStudents(BaseModel):
    location: str = Field(..., description="The class room where the students study")
    prof_name: str = Field(
        ..., description="Name of the Professor who teaches the class"
    )
    personalities_of_students: List[str] = Field(
        ..., description="Prompt containing the personality details of the student"
    )


class ChunkDetails(BaseModel):
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    content: str = Field(..., description="Content of the chunk")
    difficulty_index: Optional[float] = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Semantic density on 0-100 scale (populated post-simulation based on student understanding scores)",
    )

    page_range: str = Field(
        ...,
        description="Location reference (e.g., 'Slide 3', 'Page 2', or 'Paragraph 5')",
    )
    has_formula: bool = Field(
        default=False, description="Whether the chunk contains formulas"
    )
    has_code: bool = Field(default=False, description="Whether the chunk contains code")


class CognitiveState(BaseModel):
    fatigue: int = Field(
        default=0,
        ge=0,
        description="Fatigue level (starts at 0, increases by 5 per chunk)",
    )
    cognitive_load: int = Field(
        default=0, ge=0, description="Cognitive load (increases based on chunk density)"
    )
    understanding: int = Field(
        default=3, ge=1, le=5, description="Understanding level on 1-5 scale"
    )


class StudentAgentState(BaseModel):
    student_id: str = Field(..., description="Unique identifier for the student")
    name: str = Field(..., description="Student name")
    personality_prompt: str = Field(
        ..., description="Personality prompt for the student agent"
    )
    cognitive_state: CognitiveState = Field(..., description="Current cognitive state")
    doubts_asked: List[str] = Field(
        default_factory=list, description="List of doubts asked by the student"
    )


class TeacherAgentConfig(BaseModel):
    teacher_id: str = Field(..., description="Unique identifier for the teacher")
    name: str = Field(..., description="Teacher name")
    personality_prompt: str = Field(
        ..., description="Personality prompt for the teacher agent"
    )
    big5_scores: Dict[str, int] = Field(
        ..., description="Big Five personality scores (O, C, E, A, N)"
    )


class TeachingOutput(BaseModel):
    chunk_id: str = Field(..., description="Chunk identifier")
    teaching_transcript: str = Field(
        ..., description="Transcript of the teaching session"
    )
    teaching_method_used: Literal[
        "direct_explanation", "analogy", "example", "question"
    ] = Field(..., description="Teaching method used")


class StudentResponse(BaseModel):
    student_id: str = Field(..., description="Student identifier")
    chunk_id: str = Field(..., description="Chunk identifier")
    understanding_before: int = Field(
        ..., ge=1, le=5, description="Understanding level before teaching (1-5)"
    )
    understanding_after: int = Field(
        ..., ge=1, le=5, description="Understanding level after teaching (1-5)"
    )
    doubt_asked: Optional[str] = Field(
        default=None, description="Doubt asked by the student"
    )
    doubt_resolved: Optional[bool] = Field(
        default=None, description="Whether the doubt was resolved"
    )


class PrincipalAnalysis(BaseModel):
    chunk_id: str = Field(
        default="session",
        description="'session' for end-of-session analysis, or chunk id for legacy per-chunk use",
    )
    alignment_score: float = Field(
        ..., ge=0, le=1, description="Overall alignment score (0-1)"
    )
    per_chunk_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-chunk KLI alignment scores keyed by chunk_id",
    )
    missing_prerequisites: List[str] = Field(
        default_factory=list,
        description="List of missing prerequisites identified across the session",
    )
    suggested_methods: List[str] = Field(
        default_factory=list, description="Suggested teaching method improvements"
    )
    notes: str = Field(default="", description="Full KLI analysis text")


class SimulationRun(BaseModel):
    run_id: str = Field(..., description="Unique identifier for the simulation run")
    timestamp: datetime = Field(..., description="Timestamp of the simulation run")
    teacher_config: TeacherAgentConfig = Field(..., description="Teacher configuration")
    students_selected: List[str] = Field(
        ..., description="List of selected student IDs"
    )
    chunk_results: List[Dict[str, Any]] = Field(
        ..., description="Per-chunk results data"
    )
    principal_summary: PrincipalAnalysis = Field(
        ..., description="Principal's analysis summary"
    )


class AggregatedResults(BaseModel):
    total_runs: int = Field(..., ge=0, description="Total number of simulation runs")
    per_chunk_avg_understanding: Dict[str, float] = Field(
        ..., description="Average understanding per chunk"
    )
    gap_chunks: List[str] = Field(
        default_factory=list, description="Chunks with >40% failure rate"
    )
    common_doubts: Dict[str, List[str]] = Field(
        default_factory=dict, description="Common doubts organized by chunk"
    )
    principal_notes: List[str] = Field(
        default_factory=list, description="Principal's notes"
    )

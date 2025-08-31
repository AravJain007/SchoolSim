from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

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
    reasoning_effort: str = Field(
        default="high", description="Specifies the reasoning effort for the LLM"
    )


class LLMResult(BaseModel):
    status: int = Field(
        ...,
        description="Response code from LLM. Tells us if we were successfully able to get an output from the LLM",
    )
    response: str | Any = Field(..., description="Response from the LLM")
    response_reasoning: str | Any = Field(..., description="Reasoning for response")


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
    resume_text: Optional[str] = Field(
        default=None,
        description="Plain text (or markdown) extracted from the PDF resume",
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

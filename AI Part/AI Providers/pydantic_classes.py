from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

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


class LLMCallResponseInput(BaseModel):
    input_prompt_to_llm: str = Field(
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


class LLMResult(BaseModel):
    status: int = Field(
        ...,
        description="Response code from LLM. Tells us if we were successfully able to get an output from the LLM",
    )
    response: str | Any = Field(..., description="Response from the LLM")

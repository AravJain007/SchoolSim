from typing import Literal

from pydantic import BaseModel, Field


class LLMCallResponseInput(BaseModel):
    input_prompt_to_llm: str = Field(
        ..., min_length=1, description="The prompt provided as an input to the LLM"
    )
    model_provider: Literal[
        "google", "openai", "anthropic", "vllm", "ollama", "custom"
    ] = Field(
        ...,
        description="""Choose on of the available providers.
        If the provider of your choice has not been provided kindly create a custom class and add it to llm_call.py file.""",
    )
    model_name: str = Field(
        ..., min_length=1, description="Name of the model available from the provider"
    )

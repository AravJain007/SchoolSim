from datetime import date

import pytest
from sympy import false, true

from llm_provider.creation_prompt import (
    CHARACTER_IMPERSONATION_PROMPT,
    SITUATION_PROMPT,
)
from llm_provider.llm_call import LLMCall
from llm_provider.test_personality import BIG5_PERSONALITY, BIOGRAPHY, SITUATION
from pydantic_classes import LLMCallInput, Provider, ReasoningEffort

pytest_plugins = ("pytest_asyncio",)
llm_call_class = LLMCall()

developer_message = (
    CHARACTER_IMPERSONATION_PROMPT.format(
        name="Arav", big5_personality_text=BIG5_PERSONALITY, biography=BIOGRAPHY
    )
    .replace("{{", "{")
    .replace("}}", "}")
)

user_message = SITUATION_PROMPT.format(situation_description=SITUATION, name="Arav")


class TestLLMCall:
    @pytest.mark.asyncio
    async def test_llm_call_lightning(self):
        input_to_function = LLMCallInput(
            developer_prompt_provided=True,
            developer_prompt_to_llm=developer_message,
            user_prompt_to_llm=user_message,
            model_provider=Provider.LIGHTNING,
            model_name="lightning-ai/gpt-oss-120b",
            reasoning_effort=ReasoningEffort.HIGH,
        )
        response = await llm_call_class.generate(input_to_function)
        print(
            f"""The output from the Lightning is:
            {response.response}"""
        )
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_llm_call_google(self):
        input_to_function = LLMCallInput(
            user_prompt_to_llm="Tell me about yourself",
            model_provider=Provider.GEMINI,
            model_name="gemini-2.5-flash-lite",
        )
        response = await llm_call_class.generate(input_to_function)
        print(
            f"""The output from the Gemini model is:
            {response.response}"""
        )
        assert response.status == 200

    # @pytest.mark.asyncio
    # async def test_llm_call_ollama(self):

    # TODO: Write a test for semaphores type shi on both google and lmstudio

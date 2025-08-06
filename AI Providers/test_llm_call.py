import logging

import pytest
from llm_call import LLMCall
from pydantic_classes import LLMCallResponseInput

pytest_plugins = ("pytest_asyncio",)
llm_call_class = LLMCall()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestLLMCall:
    @pytest.mark.asyncio
    async def test_llm_call_ollama(self):
        input_to_function = LLMCallResponseInput(
            input_prompt_to_llm="Yo waddup buddy. Temme bout yourself.",
            model_provider="lmstudio",
            model_name="openai/gpt-oss-20b",
        )
        response = await llm_call_class.generate(input_to_function)
        logger.info(
            f"""The output from the Ollama model is:
                    {response.response}"""
        )
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_llm_call_google(self):
        input_to_function = LLMCallResponseInput(
            input_prompt_to_llm="Yo waddup buddy. Temme bout yourself.",
            model_provider="gemini",
            model_name="gemini-2.5-flash-lite",
        )
        response = await llm_call_class.generate(input_to_function)
        logger.info(
            f"""The output from the Gemini model is:
                    {response.response}"""
        )
        assert response.status == 200

    # TODO: Write a test for semaphores type shi on both google and lmstudio

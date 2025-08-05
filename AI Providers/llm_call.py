import logging
import os
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types
from ollama import AsyncClient
from openai import OpenAI
from pydantic_classes import LLMCallResponseInput


class LLMCall:
    def __init__(self) -> None:
        """
        This function is used to initialize all the clients and the logger.
        """
        load_dotenv()
        self.google_available = False
        if os.getenv("GEMINI_API_KEY") is not None:
            self.google_client = genai.Client(
                api_key=os.getenv("GEMINI_API_KEY"),
                http_options=types.HttpOptions(api_version="v1alpha"),
            )
            self.google_available = True
        vllm_api_key = "EMPTY"
        vllm_api_base = os.getenv("VLLM_SERVER")
        self.vllm_client = OpenAI(
            api_key=vllm_api_key,
            base_url=vllm_api_base,
        )
        self.ollama_client = AsyncClient()
        self.logger = logging.getLogger(__name__)

    async def generate(self, response_input: LLMCallResponseInput) -> Dict[str, Any]:
        """This function is to get a response from a LLM or a SLM based on the provider and model input provided.

        Args:
            response_input (LLMCallResponseInput): This is a PyDantic Class which keeps input in check. Contains:
            1. input_prompt_to_llm (str): The prompt provided as an input to the LLM
            2. model_provider (Literal["google", "openai", "anthropic", "vllm", "ollama", "custom"]): Choose on of the available providers.
                If the provider of your choice has not been provided kindly create a custom class and add it to llm_call.py file.
            3. model_name (str): Name of the model available from the provider

        Returns:
            Dict[str, Any]: Output dictionary which contains the status of the function call and the response received from the Language Models.
        """
        if response_input.model_provider == "google" and self.google_available:
            reply_from_llm = await self.generate_google(
                response_input.input_prompt_to_llm, response_input.model_name
            )
        elif response_input.model_provider == "vllm":
            reply_from_llm = await self.generate_vllm(
                response_input.input_prompt_to_llm, response_input.model_name
            )
        elif response_input.model_provider == "ollama":
            reply_from_llm = await self.generate_ollama(
                response_input.input_prompt_to_llm, response_input.model_name
            )
        else:
            reply_from_llm = {"status": 400, "response": ""}
            self.logger.error(
                "You have chosen a wrong model provider. Kindly choose either 'google' or 'vllm'."
            )
        return reply_from_llm

    async def generate_google(
        self, input_prompt: str, model_name: str
    ) -> Dict[str, Any]:
        """Given function is to generate a response using Gemini series of models

        Args:
            input_prompt (str): The prompt provided as an input to the LLM
            model_name (str): Name of the model available from the provider

        Returns:
            Dict[str, Any]: Output dictionary which contains the status of the function call and the response received from the Language Models.
        """ """"""
        try:
            response = self.google_client.models.generate_content(
                model=model_name,
                contents=input_prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=0
                    )  # Disables thinking
                ),
            )
            return {"status": 200, "response": response}
        except Exception as e:
            self.logger.error(
                f"""You have encountered the error:
                {e}
                This error is due to no response from the Gemini API.
                Kindly check if you have hit the rate limit if you are using the free tier of Gemini API.
                """
            )
            return {"status": 500, "response": ""}

    async def generate_vllm(self, input_prompt: str, model_name: str) -> Dict[str, Any]:
        """Used to generate response using the vLLM library. Useful only on Linux based machine as it does not natively support Windows.

        Args:
            input_prompt (str): The prompt provided as an input to the LLM
            model_name (str): Name of the model available from the provider

        Returns:
            Dict[str, Any]: Output dictionary which contains the status of the function call and the response received from the Language Models.
        """
        try:
            chat_response = self.vllm_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": input_prompt},
                ],
            )
            return {"status": 200, "response": chat_response}
        except Exception as e:
            self.logger.error(
                f"""You have encountered the error:
                {e}
                This error is due to no response from the vLLM API.
                Kindly check if:
                1. You are using Linux as vLLM does not natively support Windows.
                2. You have the vLLM server running in the background.
                3. You have the model that you are trying to use installed and that it is accessible by vLLM.
                """
            )
            return {"status": 500, "response": ""}

    async def generate_ollama(self, input_prompt: str, model_name: str):
        try:
            chat_response = await self.ollama_client.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": input_prompt},
                ],
            )
            return {"status": 200, "response": chat_response["message"]["content"]}
        except Exception as e:
            self.logger.error(
                f"""You have encountered the error:
                {e}
                This error is due to no response from the VLLM API.
                Kindly check if you have the vLLM server running in the background.
                """
            )
            return {"status": 500, "response": ""}

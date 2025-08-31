import logging
import os
from ast import Dict, List
from asyncio import Semaphore
from email import message

from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import AsyncClient, api_key

from pydantic_classes import LLMCallInput, LLMProvider, LLMResult

load_dotenv()


class LLMCall:
    def __init__(self) -> None:
        """
        This function is used to initialize all the clients and the logger.
        """
        self.api_keys = {
            "gemini_api_key": os.getenv("GEMINI_API_KEY"),
            "lms_base_server": os.getenv("LMSTUDIO_SERVER_BASE_URL"),
            "lightning_base_server": os.getenv("LIGHTNING_SERVER_BASE_URL"),
            "lightning_api_key": os.getenv("LIGHTNING_STUDIO_API"),
        }
        self.logger = logging.getLogger(__name__)
        self.generation_function: dict[str, LLMProvider] = {
            "gemini": GeminiProvider(self.logger, self.api_keys["gemini_api_key"]),
            "lmstudio": LMStudioProvider(self.logger, self.api_keys["lms_base_server"]),
            "lightning": LightningProvider(
                self.logger,
                self.api_keys["lightning_base_server"],
                self.api_keys["lightning_api_key"],
            ),
        }

    async def generate(
        self, input_to_llm: LLMCallInput, semaphore: Semaphore = Semaphore(1)
    ) -> LLMResult:
        """This function is to get a response from a LLM or a SLM based on the provider and model input provided.

        Parameters
        ----------
        input_to_llm :  LLMCallInput
            This is a PyDantic Class which keeps input in check. Contains user_prompt_to_llm (str), model_provider (Literal["google", "openai", "anthropic", "vllm", "ollama", "custom"]) and model_name (str).

        Returns
        -------
        LLMResult
            Dictionary containing ``status`` and the textual ``response``.
        """
        try:
            async with semaphore:
                reply_from_llm = await self.generation_function[
                    input_to_llm.model_provider
                ].generate(input_to_llm)
                return reply_from_llm
        except Exception as e:
            self.logger.error("Error:  {e}")
            return LLMResult(status=400, response="")


class GeminiProvider(LLMProvider):
    def __init__(self, logger, gemini_api_key):
        self.google_client = genai.Client(
            api_key=gemini_api_key,
            http_options=types.HttpOptions(api_version="v1alpha"),
        )
        self.logger = logger

    async def generate(self, input_prompt: LLMCallInput) -> LLMResult:
        """Given function is to generate a response using Gemini series of models

        Parameters
        ----------
        input_prompt :  str
            The prompt provided as an input to the LLM
        model_name :  str
            Name of the model available from the provider

        Returns
        -------
        LLMResult
            Output dictionary which contains the status of the function call and the response received from the Language Models.
        """
        try:
            messages = ""
            if input_prompt.system_prompt_provided:
                messages += input_prompt.system_prompt_to_llm
            if input_prompt.developer_prompt_provided:
                messages += input_prompt.developer_prompt_to_llm
            messages += input_prompt.user_prompt_to_llm
            response = self.google_client.models.generate_content(
                model=input_prompt.model_name, contents=messages
            )
            return LLMResult(
                status=200, response=response.text, response_reasoning="NA"
            )
        except Exception as e:
            self.logger.error(
                f"""You have encountered the error:
                {e}
                This error is due to no response from the Gemini API.
                Kindly check if you have hit the rate limit if you are using the free tier of Gemini API.
                """
            )
            return LLMResult(status=500, response="", response_reasoning="")


class LightningProvider(LLMProvider):
    def __init__(self, logger, base_url, api_key):
        self.lightning_client = AsyncClient(
            base_url=base_url,
            api_key=api_key,
        )
        self.logger = logger

    async def generate(self, input_prompt: LLMCallInput) -> LLMResult:
        """Given function is to generate a response using Gemini series of models

        Parameters
        ----------
        input_prompt :  str
            The prompt provided as an input to the LLM
        model_name :  str
            Name of the model available from the provider

        Returns
        -------
        LLMResult
            Output dictionary which contains the status of the function call and the response received from the Language Models.
        """
        try:
            messages: List[Dict] = []
            if input_prompt.system_prompt_provided:
                messages.append(
                    {
                        "role": "system",
                        "content": [
                            {"type": "text", "text": input_prompt.system_prompt_to_llm}
                        ],
                    }
                )
            if input_prompt.developer_prompt_provided:
                messages.append(
                    {
                        "role": "developer",
                        "content": [
                            {
                                "type": "text",
                                "text": input_prompt.developer_prompt_to_llm,
                            }
                        ],
                    }
                )
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": input_prompt.user_prompt_to_llm}
                    ],
                }
            )
            completion = await self.lightning_client.chat.completions.create(
                model=input_prompt.model_name,
                messages=messages,
                reasoning_effort=input_prompt.reasoning_effort,
            )
            return LLMResult(
                status=200,
                response=completion.choices[0].message.content,
                response_reasoning=completion.choices[0].message.reasoning_content,
            )
        except Exception as e:
            self.logger.error(
                f"""You have encountered the error:
                {e}
                This error is due to no response from the Lightning API.
                Kindly check if you have hit the rate limit.
                """
            )
            return LLMResult(status=500, response="", response_reasoning="")


class LMStudioProvider(LLMProvider):
    def __init__(self, logger, base_url):
        self.lms_client = AsyncClient(base_url=base_url, api_key="lm-studio")
        self.logger = logger

    async def generate(self, input_prompt: LLMCallInput) -> LLMResult:
        """Given function is to generate a response using Gemini series of models

        Parameters
        ----------
        input_prompt :  str
            The prompt provided as an input to the LLM
        model_name :  str
            Name of the model available from the provider

        Returns
        -------
        LLMResult
            Output dictionary which contains the status of the function call and the response received from the Language Models.
        """
        try:
            messages = []
            if input_prompt.system_prompt_provided:
                messages.append(
                    {
                        "role": "system",
                        "content": [
                            {"type": "text", "text": input_prompt.system_prompt_to_llm}
                        ],
                    }
                )
            if input_prompt.developer_prompt_provided:
                messages.append(
                    {
                        "role": "developer",
                        "content": [
                            {
                                "type": "text",
                                "text": input_prompt.developer_prompt_to_llm,
                            }
                        ],
                    }
                )
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": input_prompt.user_prompt_to_llm}
                    ],
                }
            )
            response = await self.lms_client.chat.completions.create(
                messages=messages,
                model=input_prompt.model_name,
                reasoning_effort=input_prompt.reasoning_effort,
            )
            return LLMResult(
                status=200,
                response=response.choices[0].message,
                response_reasoning="NA",
            )
        except Exception as e:
            self.logger.error(
                """You have encountered the error:
                {e}
                This error is due to no response from LM Studio.
                Kindly check if you have started the LM Studio server and set the server path properly.
                """
            )
            return LLMResult(status=500, response="", response_reasoning="")

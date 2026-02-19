import asyncio
import logging
import os
import random
from asyncio import Semaphore
from typing import Dict, List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import AsyncClient

from pydantic_classes import LLMCallInput, LLMProvider, LLMResult

load_dotenv()

PROVIDER_COST: Dict[str, Dict[str, List[float]]] = {
    "gemini": {
        "gemini-2.5-pro": [1.25 / 1e6, 10 / 1e6],
        "gemini-2.5-flash": [0.3 / 1e6, 2.5 / 1e6],
        "gemini-2.5-flash-lite": [0.1 / 1e6, 0.40 / 1e6],
    },
    "lightning": {"lightning-ai/gpt-oss-120b": [0.05 / 1e6, 0.20 / 1e6]},
}


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
        self, input_to_llm: LLMCallInput, semaphore: Optional[Semaphore] = None
    ) -> LLMResult:
        """This function is to get a response from a LLM or a SLM based on the provider and model input provided.

        Parameters
        ----------
        input_to_llm : LLMCallInput
            This is a PyDantic Class which keeps input in check.
        semaphore : Optional[Semaphore]
            Semaphore for controlling concurrency. If None, no concurrency control is applied.

        Returns
        -------
        LLMResult
            Dictionary containing ``status`` and the textual ``response``.
        """
        try:
            if semaphore is not None:
                async with semaphore:
                    reply_from_llm = await self.generation_function[
                        input_to_llm.model_provider
                    ].generate(input_to_llm)
            else:
                # No semaphore control - run without concurrency limits
                reply_from_llm = await self.generation_function[
                    input_to_llm.model_provider
                ].generate(input_to_llm)

            return reply_from_llm

        except KeyError as e:
            self.logger.error(f"Unknown model provider: {e}")
            return LLMResult(
                status=400, response="", response_reasoning="Unknown provider"
            )


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
            cost_list = PROVIDER_COST["gemini"][input_prompt.model_name]
            cost_of_call = (
                cost_list[0] * response.usage_metadata.prompt_token_count
                + cost_list[1] * response.usage_metadata.candidates_token_count
            )
            return LLMResult(
                status=200,
                response=response.text,
                response_reasoning="NA",
                cost=cost_of_call,
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
        # Delay between requests to avoid rate limiting (seconds)
        self._request_delay = float(os.getenv("LIGHTNING_REQUEST_DELAY", "3"))

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
        # Lightning is more stable with OpenAI-compatible plain-string messages.
        # Avoid developer role and typed content arrays for maximum compatibility.
        messages = []
        system_parts = []
        if input_prompt.system_prompt_provided and input_prompt.system_prompt_to_llm:
            system_parts.append(input_prompt.system_prompt_to_llm)
        if (
            input_prompt.developer_prompt_provided
            and input_prompt.developer_prompt_to_llm
        ):
            system_parts.append(input_prompt.developer_prompt_to_llm)
        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})
        messages.append({"role": "user", "content": input_prompt.user_prompt_to_llm})

        # Throttle requests to avoid rate limiting
        if self._request_delay > 0:
            await asyncio.sleep(self._request_delay)

        max_retries = 5
        include_reasoning_effort = True
        for attempt in range(max_retries):
            try:
                request_kwargs = dict(
                    model=input_prompt.model_name,
                    messages=messages,
                )
                if include_reasoning_effort:
                    request_kwargs["reasoning_effort"] = input_prompt.reasoning_effort

                completion = await self.lightning_client.chat.completions.create(
                    **request_kwargs
                )
                message = completion.choices[0].message
                response_text = message.content
                if isinstance(response_text, list):
                    response_text = "".join(
                        part.get("text", "")
                        for part in response_text
                        if isinstance(part, dict)
                    )

                response_reasoning = getattr(message, "reasoning_content", "NA") or "NA"
                cost_list = PROVIDER_COST["lightning"][input_prompt.model_name]
                cost_of_call = (
                    cost_list[0] * completion.usage.prompt_tokens
                    + cost_list[1] * completion.usage.completion_tokens
                )
                return LLMResult(
                    status=200,
                    response=response_text or "",
                    response_reasoning=response_reasoning,
                    cost=cost_of_call,
                )
            except Exception as e:
                status_code = getattr(e, "status_code", None)
                is_rate_limit = (
                    status_code == 429
                    or "429" in str(e)
                    or "rate limit" in str(e).lower()
                )
                is_server_error = (
                    (isinstance(status_code, int) and status_code >= 500)
                    or "internal server error" in str(e).lower()
                    or "invalid character 'i' looking for beginning of value"
                    in str(e).lower()
                )

                # Lightning can reject reasoning_effort and return 500.
                # Fallback once to the same request without reasoning_effort.
                if is_server_error and include_reasoning_effort:
                    include_reasoning_effort = False
                    self.logger.warning(
                        "Lightning returned server error with reasoning_effort. "
                        "Retrying without reasoning_effort."
                    )
                    await asyncio.sleep(random.uniform(1, 2))
                    continue

                if is_rate_limit and attempt < max_retries - 1:
                    delay = random.uniform(15, 20)
                    self.logger.warning(
                        f"Rate limit hit. Pausing {delay:.1f}s (15-20s random) before retry "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                elif is_server_error and attempt < max_retries - 1:
                    delay = random.uniform(3, 6)
                    self.logger.warning(
                        f"Lightning server error. Retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
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

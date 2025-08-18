import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import AsyncClient, api_key
from pydantic_classes import LLMCallResponseInput, LLMProvider, LLMResult

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

    async def generate(self, response_input: LLMCallResponseInput) -> LLMResult:
        """This function is to get a response from a LLM or a SLM based on the provider and model input provided.

        Parameters
        ----------
        response_input :  LLMCallResponseInput
            This is a PyDantic Class which keeps input in check. Contains input_prompt_to_llm (str), model_provider (Literal["google", "openai", "anthropic", "vllm", "ollama", "custom"]) and model_name (str).

        Returns
        -------
        LLMResult
            Dictionary containing ``status`` and the textual ``response``.
        """
        try:
            reply_from_llm = await self.generation_function[
                response_input.model_provider
            ].generate(response_input.input_prompt_to_llm, response_input.model_name)
            return reply_from_llm
        except Exception as e:
            self.logger.error(f"Error:  {e}")
            return LLMResult(status=400, response="")


class GeminiProvider(LLMProvider):
    def __init__(self, logger, gemini_api_key):
        self.google_client = genai.Client(
            api_key=gemini_api_key,
            http_options=types.HttpOptions(api_version="v1alpha"),
        )
        self.logger = logger

    async def generate(self, input_prompt: str, model_name: str) -> LLMResult:
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
            response = self.google_client.models.generate_content(
                model=model_name, contents=input_prompt
            )
            return LLMResult(status=200, response=response.text)
        except Exception as e:
            self.logger.error(
                """You have encountered the error:
                {e}
                This error is due to no response from the Gemini API.
                Kindly check if you have hit the rate limit if you are using the free tier of Gemini API.
                """
            )
            return LLMResult(status=500, response="")


class LMStudioProvider(LLMProvider):
    def __init__(self, logger, base_url):
        self.lms_client = AsyncClient(base_url=base_url, api_key="lm-studio")
        self.logger = logger

    async def generate(
        self, input_prompt: str, model_name: str = "openai/gpt-oss-20b"
    ) -> LLMResult:
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
            response = await self.lms_client.chat.completions.create(
                messages=[{"role": "user", "content": input_prompt}], model=model_name
            )
            return LLMResult(status=200, response=response.choices[0].message)
        except Exception as e:
            self.logger.error(
                """You have encountered the error:
                {e}
                This error is due to no response from LM Studio.
                Kindly check if you have started the LM Studio server and set the server path properly.
                """
            )
            return LLMResult(status=500, response="")


class LightningProvider(LLMProvider):
    def __init__(self, logger, base_url):
        self.lightning_client = AsyncClient(
            base_url=base_url,
            api_key=api_key,
        )
        self.logger = logger

    async def generate(
        self, input_prompt: str, model_name: str = "lightning-ai/gpt-oss-20b"
    ) -> LLMResult:
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
            completion = self.lightning_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": input_prompt}],
                    },
                ],
            )
            print(completion)
            return LLMResult(status=200, response=completion.choices[0].message.content)
        except Exception as e:
            self.logger.error(
                """You have encountered the error:
                {e}
                This error is due to no response from the Gemini API.
                Kindly check if you have hit the rate limit if you are using the free tier of Gemini API.
                """
            )
            return LLMResult(status=500, response="")

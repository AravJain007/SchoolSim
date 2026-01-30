"""
Teacher Agent Implementation

This module implements the TeacherAgent class that teaches course material chunks
and responds to student doubts based on personality-driven teaching behaviors.
"""

import json
import logging
from typing import Optional

from llm_provider.llm_call import LLMCall
from llm_provider.teacher_prompt import (
    RESPOND_TO_DOUBT_PROMPT,
    TEACH_CHUNK_PROMPT,
    TEACHER_SYSTEM_PROMPT,
)
from pydantic_classes import (
    ChunkDetails,
    LLMCallInput,
    Provider,
    ReasoningEffort,
    TeacherAgentConfig,
    TeachingOutput,
)


class TeacherAgent:
    """
    Teacher Agent that teaches course material and responds to student doubts
    based on Big Five personality traits.
    """

    def __init__(self, config: TeacherAgentConfig):
        """
        Initialize the Teacher Agent.

        Parameters
        ----------
        config : TeacherAgentConfig
            Configuration containing teacher ID, name, personality prompt, and Big5 scores
        """
        self.config = config
        self.llm_client = LLMCall()
        self.logger = logging.getLogger(__name__)

    async def teach_chunk(
        self,
        chunk: ChunkDetails,
        model_provider: Provider = Provider.LIGHTNING,
        model_name: str = "lightning-ai/gpt-oss-20b",
        reasoning_effort: ReasoningEffort = ReasoningEffort.HIGH,
    ) -> TeachingOutput:
        """
        Teach a specific content chunk to the class.

        Parameters
        ----------
        chunk : ChunkDetails
            The content chunk to teach
        model_provider : Provider, optional
            LLM provider to use (default: LIGHTNING)
        model_name : str, optional
            Model name to use (default: "lightning-ai/gpt-oss-20b")
        reasoning_effort : ReasoningEffort, optional
            Reasoning effort level (default: HIGH)

        Returns
        -------
        TeachingOutput
            Structured output containing teaching transcript and method used
        """
        try:
            # Format the system prompt with teacher personality
            system_prompt = TEACHER_SYSTEM_PROMPT.format(
                name=self.config.name,
                big5_personality_text=self.config.personality_prompt,
            )

            # Format the user prompt with chunk details
            user_prompt = TEACH_CHUNK_PROMPT.format(
                chunk_id=chunk.chunk_id,
                page_range=chunk.page_range,
                content=chunk.content,
                has_formula=chunk.has_formula,
                has_code=chunk.has_code,
                new_terms=", ".join(chunk.new_terms) if chunk.new_terms else "None",
                name=self.config.name,
            )

            # Create LLM call input
            llm_input = LLMCallInput(
                system_prompt_provided=True,
                system_prompt_to_llm=system_prompt,
                user_prompt_to_llm=user_prompt,
                model_provider=model_provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
            )

            # Generate teaching response
            result = await self.llm_client.generate(llm_input)

            if result.status != 200:
                self.logger.error(
                    f"Failed to generate teaching for chunk {chunk.chunk_id}: {result.response_reasoning}"
                )
                # Return default output on error
                return TeachingOutput(
                    chunk_id=chunk.chunk_id,
                    teaching_transcript="Error generating teaching content.",
                    teaching_method_used="direct_explanation",
                )

            # Parse JSON response
            try:
                response_text = result.response.strip()
                # Remove markdown code blocks if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]  # Remove ```json
                if response_text.startswith("```"):
                    response_text = response_text[3:]  # Remove ```
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Remove closing ```
                response_text = response_text.strip()

                teaching_data = json.loads(response_text)

                return TeachingOutput(
                    chunk_id=chunk.chunk_id,
                    teaching_transcript=teaching_data.get("teaching_transcript", ""),
                    teaching_method_used=teaching_data.get(
                        "teaching_method_used", "direct_explanation"
                    ),
                )
            except json.JSONDecodeError as e:
                self.logger.error(
                    f"Failed to parse teaching response for chunk {chunk.chunk_id}: {e}"
                )
                self.logger.debug(f"Response text: {result.response}")
                # Return response as transcript with default method
                return TeachingOutput(
                    chunk_id=chunk.chunk_id,
                    teaching_transcript=result.response,
                    teaching_method_used="direct_explanation",
                )

        except Exception as e:
            self.logger.error(
                f"Error teaching chunk {chunk.chunk_id}: {e}", exc_info=True
            )
            return TeachingOutput(
                chunk_id=chunk.chunk_id,
                teaching_transcript=f"Error: {str(e)}",
                teaching_method_used="direct_explanation",
            )

    async def respond_to_doubt(
        self,
        doubt: str,
        chunk: ChunkDetails,
        model_provider: Provider = Provider.LIGHTNING,
        model_name: str = "lightning-ai/gpt-oss-20b",
        reasoning_effort: ReasoningEffort = ReasoningEffort.HIGH,
    ) -> str:
        """
        Respond to a student's doubt about the content.

        Parameters
        ----------
        doubt : str
            The student's question or doubt
        chunk : ChunkDetails
            The content chunk the doubt is about
        model_provider : Provider, optional
            LLM provider to use (default: LIGHTNING)
        model_name : str, optional
            Model name to use (default: "lightning-ai/gpt-oss-20b")
        reasoning_effort : ReasoningEffort, optional
            Reasoning effort level (default: HIGH)

        Returns
        -------
        str
            The teacher's response to the student's doubt
        """
        try:
            # Format the system prompt with teacher personality
            system_prompt = TEACHER_SYSTEM_PROMPT.format(
                name=self.config.name,
                big5_personality_text=self.config.personality_prompt,
            )

            # Format the user prompt with doubt and chunk details
            user_prompt = RESPOND_TO_DOUBT_PROMPT.format(
                doubt=doubt,
                chunk_id=chunk.chunk_id,
                page_range=chunk.page_range,
                content=chunk.content,
                name=self.config.name,
            )

            # Create LLM call input
            llm_input = LLMCallInput(
                system_prompt_provided=True,
                system_prompt_to_llm=system_prompt,
                user_prompt_to_llm=user_prompt,
                model_provider=model_provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
            )

            # Generate response
            result = await self.llm_client.generate(llm_input)

            if result.status != 200:
                self.logger.error(
                    f"Failed to generate doubt response: {result.response_reasoning}"
                )
                return "I apologize, but I'm having trouble processing your question right now. Could you please rephrase it?"

            return result.response.strip()

        except Exception as e:
            self.logger.error(f"Error responding to doubt: {e}", exc_info=True)
            return f"I apologize, but I encountered an error: {str(e)}"

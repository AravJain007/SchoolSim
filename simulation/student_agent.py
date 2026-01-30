"""
Student Agent Implementation

This module implements the StudentAgent class that rates understanding,
generates doubts, and re-rates understanding after teacher responses,
based on personality-driven student behaviors.
"""

import json
import logging
from typing import Optional

from llm_provider.llm_call import LLMCall
from llm_provider.student_prompt import (
    STUDENT_DOUBT_PROMPT,
    STUDENT_RERATING_PROMPT,
    STUDENT_UNDERSTANDING_PROMPT,
)
from pydantic_classes import (
    ChunkDetails,
    CognitiveState,
    LLMCallInput,
    Provider,
    ReasoningEffort,
    StudentAgentState,
    StudentDetails,
)


class StudentAgent:
    """
    Student Agent that rates understanding, generates doubts, and re-rates
    understanding after teacher responses based on Big Five personality traits.
    """

    def __init__(
        self,
        student_details: StudentDetails,
        personality_prompt: Optional[str] = None,
        biography: Optional[str] = None,
    ):
        """
        Initialize the Student Agent.

        Parameters
        ----------
        student_details : StudentDetails
            Student details containing name, personality info, etc.
        personality_prompt : Optional[str]
            Full personality prompt (if None, will be created from student_details)
        biography : Optional[str]
            Student biography text (needed if personality_prompt is None)
        """
        self.student_details = student_details
        self.student_id = student_details.college_id
        self.name = student_details.name

        # Use provided personality prompt or create from student_details
        if personality_prompt:
            self.personality_prompt = personality_prompt
        else:
            # Extract biography from resume_text if available
            if biography is None:
                biography = student_details.resume_text or ""

            # Create personality prompt from student details
            from llm_provider.creation_prompt import CHARACTER_IMPERSONATION_PROMPT

            self.personality_prompt = CHARACTER_IMPERSONATION_PROMPT.format(
                name=self.name,
                big5_personality_text=student_details.personality_text,
                biography=biography,
            )

        # Initialize cognitive state
        self.state = StudentAgentState(
            student_id=self.student_id,
            name=self.name,
            personality_prompt=self.personality_prompt,
            cognitive_state=CognitiveState(),
        )

        self.llm_client = LLMCall()
        self.logger = logging.getLogger(__name__)

    async def rate_understanding(
        self,
        chunk: ChunkDetails,
        teaching_transcript: str,
        model_provider: Provider = Provider.LIGHTNING,
        model_name: str = "lightning-ai/gpt-oss-20b",
        reasoning_effort: ReasoningEffort = ReasoningEffort.HIGH,
    ) -> int:
        """
        Rate understanding of a chunk after hearing the teacher's explanation.

        Parameters
        ----------
        chunk : ChunkDetails
            The content chunk that was taught
        teaching_transcript : str
            The teacher's explanation transcript
        model_provider : Provider, optional
            LLM provider to use (default: LIGHTNING)
        model_name : str, optional
            Model name to use (default: "lightning-ai/gpt-oss-20b")
        reasoning_effort : ReasoningEffort, optional
            Reasoning effort level (default: HIGH)

        Returns
        -------
        int
            Understanding rating from 1-5
        """
        try:
            # Extract biography from personality prompt if available
            biography = ""
            if "### Life Experience Context" in self.personality_prompt:
                parts = self.personality_prompt.split("### Life Experience Context")
                if len(parts) > 1:
                    biography = parts[1].split("---")[0].strip()

            # Format the user prompt
            user_prompt = STUDENT_UNDERSTANDING_PROMPT.format(
                name=self.name,
                big5_personality_text=self.student_details.personality_text,
                biography=biography,
                chunk_id=chunk.chunk_id,
                page_range=chunk.page_range,
                content=chunk.content,
                teaching_transcript=teaching_transcript,
                fatigue=self.state.cognitive_state.fatigue,
                cognitive_load=self.state.cognitive_state.cognitive_load,
            )

            # Create LLM call input
            llm_input = LLMCallInput(
                system_prompt_provided=False,
                user_prompt_to_llm=user_prompt,
                model_provider=model_provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
            )

            # Generate understanding rating
            result = await self.llm_client.generate(llm_input)

            if result.status != 200:
                self.logger.error(
                    f"Failed to rate understanding for student {self.student_id}: {result.response_reasoning}"
                )
                # Return default rating on error
                return 3

            # Parse rating (should be a single integer 1-5)
            try:
                rating_text = result.response.strip()
                # Remove any markdown formatting
                rating_text = rating_text.replace("```", "").strip()
                rating = int(rating_text)

                # Ensure rating is in valid range
                rating = max(1, min(5, rating))

                # Update cognitive state
                self.state.cognitive_state.understanding = rating

                return rating
            except (ValueError, TypeError) as e:
                self.logger.error(
                    f"Failed to parse understanding rating for student {self.student_id}: {e}"
                )
                self.logger.debug(f"Response text: {result.response}")
                return 3

        except Exception as e:
            self.logger.error(
                f"Error rating understanding for student {self.student_id}: {e}",
                exc_info=True,
            )
            return 3

    async def generate_doubt(
        self,
        chunk: ChunkDetails,
        teaching_transcript: str,
        model_provider: Provider = Provider.LIGHTNING,
        model_name: str = "lightning-ai/gpt-oss-20b",
        reasoning_effort: ReasoningEffort = ReasoningEffort.HIGH,
    ) -> str:
        """
        Generate a doubt/question about the chunk based on personality and cognitive state.

        Parameters
        ----------
        chunk : ChunkDetails
            The content chunk the doubt is about
        teaching_transcript : str
            The teacher's explanation transcript
        model_provider : Provider, optional
            LLM provider to use (default: LIGHTNING)
        model_name : str, optional
            Model name to use (default: "lightning-ai/gpt-oss-20b")
        reasoning_effort : ReasoningEffort, optional
            Reasoning effort level (default: HIGH)

        Returns
        -------
        str
            The student's doubt/question
        """
        try:
            # Extract biography from personality prompt if available
            biography = ""
            if "### Life Experience Context" in self.personality_prompt:
                parts = self.personality_prompt.split("### Life Experience Context")
                if len(parts) > 1:
                    biography = parts[1].split("---")[0].strip()

            # Format the user prompt
            user_prompt = STUDENT_DOUBT_PROMPT.format(
                name=self.name,
                big5_personality_text=self.student_details.personality_text,
                biography=biography,
                chunk_id=chunk.chunk_id,
                page_range=chunk.page_range,
                content=chunk.content,
                teaching_transcript=teaching_transcript,
                understanding=self.state.cognitive_state.understanding,
                fatigue=self.state.cognitive_state.fatigue,
                cognitive_load=self.state.cognitive_state.cognitive_load,
            )

            # Create LLM call input
            llm_input = LLMCallInput(
                system_prompt_provided=False,
                user_prompt_to_llm=user_prompt,
                model_provider=model_provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
            )

            # Generate doubt
            result = await self.llm_client.generate(llm_input)

            if result.status != 200:
                self.logger.error(
                    f"Failed to generate doubt for student {self.student_id}: {result.response_reasoning}"
                )
                return "I'm not sure I understand this concept. Could you explain it again?"

            doubt = result.response.strip()

            # Store the doubt
            self.state.doubts_asked.append(doubt)

            return doubt

        except Exception as e:
            self.logger.error(
                f"Error generating doubt for student {self.student_id}: {e}",
                exc_info=True,
            )
            return "I have a question about this concept."

    async def rerate_after_response(
        self,
        chunk: ChunkDetails,
        doubt: str,
        teacher_response: str,
        model_provider: Provider = Provider.LIGHTNING,
        model_name: str = "lightning-ai/gpt-oss-20b",
        reasoning_effort: ReasoningEffort = ReasoningEffort.HIGH,
    ) -> int:
        """
        Re-rate understanding after teacher responds to doubt (IRF R+ metric).

        Parameters
        ----------
        chunk : ChunkDetails
            The content chunk
        doubt : str
            The doubt that was asked
        teacher_response : str
            The teacher's response to the doubt
        model_provider : Provider, optional
            LLM provider to use (default: LIGHTNING)
        model_name : str, optional
            Model name to use (default: "lightning-ai/gpt-oss-20b")
        reasoning_effort : ReasoningEffort, optional
            Reasoning effort level (default: HIGH)

        Returns
        -------
        int
            New understanding rating from 1-5
        """
        try:
            understanding_before = self.state.cognitive_state.understanding

            # Extract biography from personality prompt if available
            biography = ""
            if "### Life Experience Context" in self.personality_prompt:
                parts = self.personality_prompt.split("### Life Experience Context")
                if len(parts) > 1:
                    biography = parts[1].split("---")[0].strip()

            # Format the user prompt
            user_prompt = STUDENT_RERATING_PROMPT.format(
                name=self.name,
                big5_personality_text=self.student_details.personality_text,
                biography=biography,
                chunk_id=chunk.chunk_id,
                page_range=chunk.page_range,
                content=chunk.content,
                doubt=doubt,
                understanding_before=understanding_before,
                teacher_response=teacher_response,
            )

            # Create LLM call input
            llm_input = LLMCallInput(
                system_prompt_provided=False,
                user_prompt_to_llm=user_prompt,
                model_provider=model_provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
            )

            # Generate re-rating
            result = await self.llm_client.generate(llm_input)

            if result.status != 200:
                self.logger.error(
                    f"Failed to re-rate understanding for student {self.student_id}: {result.response_reasoning}"
                )
                return understanding_before

            # Parse rating
            try:
                rating_text = result.response.strip()
                rating_text = rating_text.replace("```", "").strip()
                rating = int(rating_text)

                # Ensure rating is in valid range
                rating = max(1, min(5, rating))

                # Update cognitive state
                self.state.cognitive_state.understanding = rating

                return rating
            except (ValueError, TypeError) as e:
                self.logger.error(
                    f"Failed to parse re-rating for student {self.student_id}: {e}"
                )
                self.logger.debug(f"Response text: {result.response}")
                return understanding_before

        except Exception as e:
            self.logger.error(
                f"Error re-rating understanding for student {self.student_id}: {e}",
                exc_info=True,
            )
            return self.state.cognitive_state.understanding

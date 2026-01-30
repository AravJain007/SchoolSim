"""
Cognitive State Management

This module manages cognitive state (fatigue, cognitive_load, understanding) for students
during the simulation, implementing the CIE (Cognitive, Information, Engagement) architecture.
"""

from pydantic_classes import CognitiveState, StudentAgentState


class CognitiveStateManager:
    """
    Manages cognitive state for students during simulation.

    Tracks fatigue, cognitive load, and understanding levels,
    and determines when students should ask doubts.
    """

    @staticmethod
    def update_after_chunk(student_state: StudentAgentState) -> None:
        """
        Update cognitive state after a chunk is taught.

        Parameters
        ----------
        student_state : StudentAgentState
            The student's current state to update
        """
        # Increase fatigue by 5 per chunk
        student_state.cognitive_state.fatigue += 5

        # Increase cognitive load by 10 per chunk (flat increment)
        # Note: difficulty_index is computed post-aggregation in Task 7,
        # so we use a flat increment here
        student_state.cognitive_state.cognitive_load += 10

        # Ensure values don't exceed reasonable bounds
        student_state.cognitive_state.fatigue = min(
            student_state.cognitive_state.fatigue, 100
        )
        student_state.cognitive_state.cognitive_load = min(
            student_state.cognitive_state.cognitive_load, 100
        )

    @staticmethod
    def should_ask_doubt(student_state: StudentAgentState, openness: int = 60) -> bool:
        """
        Determine if a student should ask a doubt based on their cognitive state.

        Parameters
        ----------
        student_state : StudentAgentState
            The student's current state
        openness : int, optional
            Openness score (0-120 scale) for curiosity questions (default: 60)

        Returns
        -------
        bool
            True if the student should ask a doubt, False otherwise
        """
        understanding = student_state.cognitive_state.understanding
        fatigue = student_state.cognitive_state.fatigue

        # If understanding is low (<= 2) and fatigue is manageable (< 80), ask doubt
        if understanding <= 2 and fatigue < 80:
            return True

        # If understanding is perfect (5) and openness is high (> 70),
        # maybe ask a curiosity question
        if understanding == 5 and openness > 70:
            return True

        return False

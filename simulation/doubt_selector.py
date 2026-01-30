"""
Doubt Selector

This module selects which students should ask doubts based on their cognitive state
and understanding levels.
"""

import random
import re
from typing import List

from simulation.cognitive_state import CognitiveStateManager
from simulation.student_agent import StudentAgent


def _extract_openness_score(student: StudentAgent) -> int:
    """
    Extract openness score from student's personality text.

    The personality text contains lines like:
    "### {index}. Openness To Experience\n- Score: {score} out of {max}"

    Parameters
    ----------
    student : StudentAgent
        The student agent

    Returns
    -------
    int
        Openness score (0-120 scale), defaults to 60 if not found
    """
    personality_text = student.student_details.personality_text

    # Look for "Openness To Experience" section
    pattern = r"### \d+\. Openness To Experience\s*\n- Score: (\d+) out of (\d+)"
    match = re.search(pattern, personality_text, re.IGNORECASE)

    if match:
        score = int(match.group(1))
        max_score = int(match.group(2))
        # The score is on a 0-120 scale (max is typically 120)
        return score

    # Default to 60 if not found (middle of 0-120 scale)
    return 60


def select_doubt_askers(students: List[StudentAgent]) -> List[StudentAgent]:
    """
    Select 2-5 students who should ask doubts based on understanding, fatigue, and openness.

    Uses CognitiveStateManager.should_ask_doubt to filter students, which includes:
    - Students with understanding <= 2 AND fatigue < 80 (struggling students)
    - Students with understanding == 5 AND openness > 70 (curious students)

    Then randomly selects 2-5 students from the filtered list.

    Parameters
    ----------
    students : List[StudentAgent]
        List of all student agents in the class

    Returns
    -------
    List[StudentAgent]
        List of selected students who should ask doubts (2-5 students)
    """
    # Filter students using the same logic as CognitiveStateManager.should_ask_doubt
    eligible_students = []
    for student in students:
        openness = _extract_openness_score(student)
        if CognitiveStateManager.should_ask_doubt(student.state, openness):
            eligible_students.append(student)

    # If no eligible students, return empty list
    if not eligible_students:
        return []

    # Randomly select 1-2 students
    num_to_select = min(random.randint(1, 2), len(eligible_students))
    selected = random.sample(eligible_students, num_to_select)

    return selected

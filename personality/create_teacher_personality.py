"""
Teacher Personality Creation

This module creates teacher personality prompts from Big Five personality scores,
mapping traits to teaching behaviors and generating system prompts for the teacher agent.
"""

from typing import Dict

from pydantic_classes import TeacherAgentConfig

# Import domain result dictionaries for generating personality text
from student_big5_website.domain_results import (
    AGREEABLENESS,
    CONSCIENTIOUSNESS,
    EXTRAVERSION,
    NEUROCRITSISM,
    OPENNESS,
)

# Mapping of domain letters to domain dictionaries
DOMAIN_MAP = {
    "O": OPENNESS,
    "C": CONSCIENTIOUSNESS,
    "E": EXTRAVERSION,
    "A": AGREEABLENESS,
    "N": NEUROCRITSISM,
}


def _calculate_score_category(score: int, max_score: int = 60) -> str:
    """
    Calculate the category (low/neutral/high) for a Big Five score.

    Parameters
    ----------
    score : int
        The raw score
    max_score : int, optional
        Maximum possible score (default: 120 for 24 questions * 5 max)

    Returns
    -------
    str
        "low", "neutral", or "high"
    """
    if score < max_score * 0.4:
        return "low"
    elif score > max_score * 0.6:
        return "high"
    else:
        return "neutral"


def _generate_personality_text(big5_scores: Dict[str, int]) -> str:
    """
    Generate personality text from Big Five scores.

    Parameters
    ----------
    big5_scores : Dict[str, int]
        Dictionary with keys "O", "C", "E", "A", "N" and integer scores

    Returns
    -------
    str
        Formatted personality text similar to student personality text format
    """
    personality_text = ""
    domain_order = ["O", "C", "E", "A", "N"]

    for index, domain_letter in enumerate(domain_order, 1):
        if domain_letter not in big5_scores:
            continue

        domain_data = DOMAIN_MAP[domain_letter]
        domain_title = domain_data["title"]
        score = big5_scores[domain_letter]
        max_score = 120  # Assuming 24 questions per domain, max 5 per question
        category = _calculate_score_category(score, max_score)

        # Find the result text for this category
        result_text = ""
        for result in domain_data["results"]:
            if result["score"] == category:
                result_text = result["text"]
                break

        personality_text += f"""### {index}. {domain_title}
- Score: {score} out of {max_score}, which is a {category} score.
- Definition: {result_text}
- Facets:
"""

        # Add facet information (simplified - just domain description)
        personality_text += f"\t- {domain_data['shortDescription']}\n"

    return personality_text


def _map_big5_to_teaching_style(big5_scores: Dict[str, int]) -> Dict[str, str]:
    """
    Map Big Five scores to teaching style descriptors.

    Parameters
    ----------
    big5_scores : Dict[str, int]
        Dictionary with keys "O", "C", "E", "A", "N" and integer scores

    Returns
    -------
    Dict[str, str]
        Dictionary mapping each trait to teaching style description
    """
    max_score = 120
    teaching_styles = {}

    for domain_letter, score in big5_scores.items():
        category = _calculate_score_category(score, max_score)
        domain_data = DOMAIN_MAP[domain_letter]

        if category == "low":
            if domain_letter == "O":
                teaching_styles[
                    "O"
                ] = "Sticks to textbook examples, prefers conventional methods"
            elif domain_letter == "C":
                teaching_styles["C"] = "Summarizes quickly, focuses on key points"
            elif domain_letter == "E":
                teaching_styles[
                    "E"
                ] = "Lecture-heavy, minimal interaction, comfortable with silence"
            elif domain_letter == "A":
                teaching_styles[
                    "A"
                ] = "May dismiss 'silly' questions, prioritizes efficiency"
            elif domain_letter == "N":
                teaching_styles[
                    "N"
                ] = "Calm and composed under pressure, handles confusion well"
        elif category == "high":
            if domain_letter == "O":
                teaching_styles[
                    "O"
                ] = "Uses creative analogies, explores diverse examples"
            elif domain_letter == "C":
                teaching_styles[
                    "C"
                ] = "Covers every detail systematically, well-organized"
            elif domain_letter == "E":
                teaching_styles[
                    "E"
                ] = "Frequently asks questions, animated explanations, high energy"
            elif domain_letter == "A":
                teaching_styles[
                    "A"
                ] = "Patiently re-explains, validates all questions, supportive"
            elif domain_letter == "N":
                teaching_styles[
                    "N"
                ] = "May get flustered with persistent doubts, shows frustration"
        else:  # neutral
            teaching_styles[
                domain_letter
            ] = "Balanced approach, moderate expression of trait"

    return teaching_styles


def create_teacher_prompt(
    teacher_id: str,
    teacher_name: str,
    teacher_big5_data: Dict[str, int],
) -> TeacherAgentConfig:
    """
    Create a TeacherAgentConfig from Big Five personality data.

    This function maps Big Five scores to teaching style descriptors and generates
    a personality prompt for the teacher agent.

    Parameters
    ----------
    teacher_id : str
        Unique identifier for the teacher
    teacher_name : str
        Name of the teacher
    teacher_big5_data : Dict[str, int]
        Dictionary with keys "O", "C", "E", "A", "N" and integer scores (0-120 range)

    Returns
    -------
    TeacherAgentConfig
        Configuration object for the teacher agent with personality prompt

    Examples
    --------
    >>> big5_scores = {"O": 45, "C": 55, "E": 30, "A": 50, "N": 25}
    >>> config = create_teacher_prompt("T001", "Dr. Smith", big5_scores)
    >>> print(config.personality_prompt)
    """
    # Generate personality text
    personality_text = _generate_personality_text(teacher_big5_data)

    # Map to teaching styles (for reference, included in personality text)
    teaching_styles = _map_big5_to_teaching_style(teacher_big5_data)

    # Create the personality prompt (similar to student personality prompt format)
    # The personality_text already contains the formatted Big5 information
    # This will be used in the TEACHER_SYSTEM_PROMPT template

    return TeacherAgentConfig(
        teacher_id=teacher_id,
        name=teacher_name,
        personality_prompt=personality_text,
        big5_scores=teacher_big5_data,
    )

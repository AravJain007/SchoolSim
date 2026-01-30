"""
Principal Agent Implementation using KLI Framework

This module implements the PrincipalAgent class that analyzes teaching effectiveness
using the KLI (Knowledge-Learning-Instruction) Framework and Bloom's Taxonomy.

The agent acts as an expert pedagogical observer, evaluating how well instruction
aligns with evidence-based learning science principles.

References:
- KLI Framework: Koedinger, K. R., Corbett, A. T., & Perfetti, C. (2012).
  The Knowledge-Learning-Instruction Framework. Cognitive Science, 36(5), 757-798.
  https://onlinelibrary.wiley.com/doi/10.1111/j.1551-6709.2012.01245.x

- Bloom's Taxonomy: Anderson, L. W., & Krathwohl, D. R. (2001).
  A Taxonomy for Learning, Teaching, and Assessing.
  https://www.buffalo.edu/catt/teach/develop/design/learning-outcomes/blooms.html
"""

import json
import logging
from typing import List, Optional

from llm_provider.llm_call import LLMCall
from llm_provider.principal_prompt import (
    PRINCIPAL_ANALYSIS_PROMPT,
    PRINCIPAL_SUMMARY_PROMPT,
    PRINCIPAL_SYSTEM_PROMPT,
)
from pydantic_classes import (
    ChunkDetails,
    LLMCallInput,
    PrincipalAnalysis,
    Provider,
    ReasoningEffort,
    StudentResponse,
)


class PrincipalAgent:
    """
    Principal Agent for pedagogical analysis using the KLI Framework.

    This agent does not have a personality; it operates as an objective expert
    in educational assessment, applying research-based frameworks to evaluate
    teaching effectiveness.

    The KLI Framework evaluates three dimensions:
    - K (Knowledge): Type of knowledge and prerequisites
    - L (Learning): Appropriate learning phase and opportunities
    - I (Instruction): Teaching method alignment with content

    Source: https://eric.ed.gov/?id=ED535880
    """

    def __init__(self):
        """
        Initialize the Principal Agent.

        No personality configuration needed - operates with fixed pedagogical expertise
        based on the KLI Framework and Bloom's Taxonomy.
        """
        self.llm_client = LLMCall()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Principal Agent initialized with KLI Framework expertise")

    async def analyze_chunk(
        self,
        chunk: ChunkDetails,
        teaching_transcript: str,
        student_responses: List[StudentResponse],
        model_provider: Provider = Provider.GEMINI,
        model_name: str = "gemini-2.5-flash",
        reasoning_effort: ReasoningEffort = ReasoningEffort.HIGH,
    ) -> PrincipalAnalysis:
        """
        Analyze a single teaching chunk using the KLI Framework.

        This method evaluates:
        1. Knowledge taxonomy - What type of knowledge is being taught?
        2. Learning event alignment - Is the learning phase appropriate?
        3. Instructional method match - Does teaching method fit content type?

        Parameters
        ----------
        chunk : ChunkDetails
            The content chunk that was taught
        teaching_transcript : str
            Complete transcript of how the teacher explained the chunk
        student_responses : List[StudentResponse]
            List of student understanding scores and doubts for this chunk
        model_provider : Provider, optional
            LLM provider to use (default: GEMINI for better reasoning)
        model_name : str, optional
            Model name to use (default: "gemini-2.5-flash")
        reasoning_effort : ReasoningEffort, optional
            Reasoning effort level (default: HIGH for deep analysis)

        Returns
        -------
        PrincipalAnalysis
            Structured analysis containing alignment score, missing prerequisites,
            suggested alternative methods, and detailed notes

        Notes
        -----
        Alignment scoring (based on KLI Framework principles):
        - 1.0: Perfect alignment - method matches content type, appropriate learning phase
        - 0.7-0.9: Good alignment - minor mismatches or missed opportunities
        - 0.4-0.6: Moderate alignment - some mismatches, could be more effective
        - 0.0-0.3: Poor alignment - significant mismatch between method and content

        Source: https://pact.cs.cmu.edu/pubs/Koedinger,%20Corbett,%20Perfetti%202012-KLI.pdf
        """
        try:
            # Format student responses as readable text
            student_responses_text = self._format_student_responses(student_responses)

            # Create the analysis prompt with all context
            user_prompt = PRINCIPAL_ANALYSIS_PROMPT.format(
                chunk_content=chunk.content,
                teaching_transcript=teaching_transcript,
                student_responses=student_responses_text,
            )

            # Create LLM call input
            llm_input = LLMCallInput(
                system_prompt_provided=True,
                system_prompt_to_llm=PRINCIPAL_SYSTEM_PROMPT,
                user_prompt_to_llm=user_prompt,
                model_provider=model_provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
            )

            # Generate analysis
            result = await self.llm_client.generate(llm_input)

            if result.status != 200:
                self.logger.error(
                    f"Failed to generate analysis for chunk {chunk.chunk_id}: "
                    f"{result.response_reasoning}"
                )
                # Return default low-quality analysis on error
                return PrincipalAnalysis(
                    chunk_id=chunk.chunk_id,
                    alignment_score=0.5,
                    missing_prerequisites=["Analysis failed - error in LLM call"],
                    suggested_methods=["Unable to analyze"],
                    notes=f"Error: {result.response_reasoning}",
                )

            # Parse the response to extract structured data
            analysis = self._parse_analysis_response(
                result.response, chunk.chunk_id, student_responses
            )

            self.logger.info(
                f"Completed KLI analysis for chunk {chunk.chunk_id}: "
                f"alignment_score={analysis.alignment_score:.2f}"
            )

            return analysis

        except Exception as e:
            self.logger.error(
                f"Error analyzing chunk {chunk.chunk_id}: {e}", exc_info=True
            )
            return PrincipalAnalysis(
                chunk_id=chunk.chunk_id,
                alignment_score=0.5,
                missing_prerequisites=[],
                suggested_methods=[],
                notes=f"Exception during analysis: {str(e)}",
            )

    def _format_student_responses(
        self, student_responses: List[StudentResponse]
    ) -> str:
        """
        Format student responses into readable text for analysis.

        Parameters
        ----------
        student_responses : List[StudentResponse]
            List of student responses to format

        Returns
        -------
        str
            Formatted text representation of student responses
        """
        if not student_responses:
            return "No student responses available for this chunk."

        formatted = []
        for i, response in enumerate(student_responses, 1):
            formatted.append(f"Student {i} (ID: {response.student_id}):")
            formatted.append(
                f"  - Understanding before: {response.understanding_before}/5"
            )
            formatted.append(
                f"  - Understanding after: {response.understanding_after}/5"
            )
            formatted.append(
                f"  - Improvement: {response.understanding_after - response.understanding_before}"
            )

            if response.doubt_asked:
                formatted.append(f"  - Doubt: {response.doubt_asked}")
                resolved_text = "Yes" if response.doubt_resolved else "No"
                formatted.append(f"  - Doubt resolved: {resolved_text}")
            else:
                formatted.append("  - No doubt asked")
            formatted.append("")

        return "\n".join(formatted)

    def _parse_analysis_response(
        self,
        response_text: str,
        chunk_id: str,
        student_responses: List[StudentResponse],
    ) -> PrincipalAnalysis:
        """
        Parse the LLM's analysis response into a structured PrincipalAnalysis object.

        The LLM response should contain alignment score, prerequisites, methods, and notes.
        We use heuristics and keyword extraction to parse the unstructured response.

        Parameters
        ----------
        response_text : str
            Raw text response from the LLM
        chunk_id : str
            Chunk identifier
        student_responses : List[StudentResponse]
            Student responses (used for fallback scoring)

        Returns
        -------
        PrincipalAnalysis
            Structured analysis object
        """
        # Default values
        alignment_score = 0.5
        missing_prerequisites = []
        suggested_methods = []
        notes = response_text

        try:
            # Try to extract alignment score
            # Look for patterns like "0.8", "Score: 0.7", "alignment: 0.9"
            import re

            score_patterns = [
                r"alignment[:\s]+([0-9]\.[0-9]+)",
                r"score[:\s]+([0-9]\.[0-9]+)",
                r"([0-9]\.[0-9]+)\s*(?:/|out of)\s*1\.0",
                r"(?:^|\n)([0-9]\.[0-9]+)(?:\s|$)",  # Standalone decimal
            ]

            for pattern in score_patterns:
                match = re.search(pattern, response_text.lower())
                if match:
                    try:
                        score = float(match.group(1))
                        if 0.0 <= score <= 1.0:
                            alignment_score = score
                            break
                    except (ValueError, IndexError):
                        continue

            # If no explicit score found, infer from student performance
            if alignment_score == 0.5 and student_responses:
                avg_improvement = sum(
                    r.understanding_after - r.understanding_before
                    for r in student_responses
                ) / len(student_responses)

                # Map improvement to alignment score
                # Improvement range: -4 to +4 (1-5 scale)
                # Strong positive improvement (3-4) → high alignment (0.8-1.0)
                # Moderate improvement (1-2) → medium alignment (0.6-0.7)
                # No change (0) → moderate alignment (0.5)
                # Negative (-1 or worse) → poor alignment (0.2-0.4)
                if avg_improvement >= 3:
                    alignment_score = 0.9
                elif avg_improvement >= 2:
                    alignment_score = 0.75
                elif avg_improvement >= 1:
                    alignment_score = 0.6
                elif avg_improvement >= 0:
                    alignment_score = 0.5
                elif avg_improvement >= -1:
                    alignment_score = 0.4
                else:
                    alignment_score = 0.3

            # Extract missing prerequisites
            # Look for sections with headers like "Missing Prerequisites", "Prerequisites:"
            prereq_section = re.search(
                r"(?:missing\s+)?prerequisites?[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)",
                response_text,
                re.IGNORECASE | re.DOTALL,
            )
            if prereq_section:
                prereq_text = prereq_section.group(1)
                # Extract bullet points or numbered items
                prereq_items = re.findall(
                    r"[-•*]\s*(.+?)(?=\n[-•*]|\n\n|$)", prereq_text, re.DOTALL
                )
                if prereq_items:
                    missing_prerequisites = [item.strip() for item in prereq_items]
                else:
                    # Try numbered list
                    prereq_items = re.findall(
                        r"\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)", prereq_text
                    )
                    if prereq_items:
                        missing_prerequisites = [item.strip() for item in prereq_items]

            # Extract suggested methods
            methods_section = re.search(
                r"(?:suggested|alternative)\s+methods?[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)",
                response_text,
                re.IGNORECASE | re.DOTALL,
            )
            if methods_section:
                methods_text = methods_section.group(1)
                # Extract bullet points or numbered items
                method_items = re.findall(
                    r"[-•*]\s*(.+?)(?=\n[-•*]|\n\n|$)", methods_text, re.DOTALL
                )
                if method_items:
                    suggested_methods = [item.strip() for item in method_items]
                else:
                    # Try numbered list
                    method_items = re.findall(
                        r"\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)", methods_text
                    )
                    if method_items:
                        suggested_methods = [item.strip() for item in method_items]

        except Exception as e:
            self.logger.warning(f"Error parsing analysis response: {e}")
            # Keep defaults

        return PrincipalAnalysis(
            chunk_id=chunk_id,
            alignment_score=alignment_score,
            missing_prerequisites=missing_prerequisites,
            suggested_methods=suggested_methods,
            notes=notes,
        )

    async def generate_summary(
        self,
        all_analyses: List[PrincipalAnalysis],
        model_provider: Provider = Provider.GEMINI,
        model_name: str = "gemini-2.5-flash",
        reasoning_effort: ReasoningEffort = ReasoningEffort.HIGH,
    ) -> str:
        """
        Generate a comprehensive summary across all chunk analyses.

        This summary provides:
        - Overall alignment score across all chunks
        - Critical misalignments that need addressing
        - Bloom's Taxonomy progression assessment
        - Top recommendations for improvement

        Parameters
        ----------
        all_analyses : List[PrincipalAnalysis]
            List of all chunk analyses from the teaching session
        model_provider : Provider, optional
            LLM provider to use (default: GEMINI)
        model_name : str, optional
            Model name to use (default: "gemini-2.5-flash")
        reasoning_effort : ReasoningEffort, optional
            Reasoning effort level (default: HIGH)

        Returns
        -------
        str
            Comprehensive summary text with actionable recommendations

        Notes
        -----
        The summary synthesizes all individual analyses to identify patterns,
        systemic issues, and highest-priority improvements based on KLI Framework
        principles and Bloom's Taxonomy progression.
        """
        try:
            if not all_analyses:
                return "No analyses available to summarize."

            # Format all analyses as text
            analyses_text = self._format_analyses_for_summary(all_analyses)

            # Create the summary prompt
            user_prompt = PRINCIPAL_SUMMARY_PROMPT.format(all_analyses=analyses_text)

            # Create LLM call input
            llm_input = LLMCallInput(
                system_prompt_provided=True,
                system_prompt_to_llm=PRINCIPAL_SYSTEM_PROMPT,
                user_prompt_to_llm=user_prompt,
                model_provider=model_provider,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
            )

            # Generate summary
            result = await self.llm_client.generate(llm_input)

            if result.status != 200:
                self.logger.error(
                    f"Failed to generate summary: {result.response_reasoning}"
                )
                # Return basic summary on error
                return self._generate_basic_summary(all_analyses)

            self.logger.info("Generated comprehensive KLI Framework summary")
            return result.response.strip()

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}", exc_info=True)
            return self._generate_basic_summary(all_analyses)

    def _format_analyses_for_summary(
        self, all_analyses: List[PrincipalAnalysis]
    ) -> str:
        """
        Format all chunk analyses into readable text for summary generation.

        Parameters
        ----------
        all_analyses : List[PrincipalAnalysis]
            List of all analyses to format

        Returns
        -------
        str
            Formatted text representation of all analyses
        """
        formatted = []

        for i, analysis in enumerate(all_analyses, 1):
            formatted.append(f"=== Chunk {i}: {analysis.chunk_id} ===")
            formatted.append(f"Alignment Score: {analysis.alignment_score:.2f}/1.0")

            if analysis.missing_prerequisites:
                formatted.append("\nMissing Prerequisites:")
                for prereq in analysis.missing_prerequisites:
                    formatted.append(f"  - {prereq}")
            else:
                formatted.append("\nMissing Prerequisites: None identified")

            if analysis.suggested_methods:
                formatted.append("\nSuggested Alternative Methods:")
                for method in analysis.suggested_methods:
                    formatted.append(f"  - {method}")
            else:
                formatted.append("\nSuggested Methods: None")

            formatted.append(
                f"\nNotes: {analysis.notes[:300]}..."
            )  # Truncate long notes
            formatted.append("\n")

        return "\n".join(formatted)

    def _generate_basic_summary(self, all_analyses: List[PrincipalAnalysis]) -> str:
        """
        Generate a basic statistical summary when LLM call fails.

        Parameters
        ----------
        all_analyses : List[PrincipalAnalysis]
            List of all analyses to summarize

        Returns
        -------
        str
            Basic statistical summary
        """
        if not all_analyses:
            return "No analyses available."

        avg_score = sum(a.alignment_score for a in all_analyses) / len(all_analyses)

        excellent = sum(1 for a in all_analyses if a.alignment_score >= 0.8)
        good = sum(1 for a in all_analyses if 0.6 <= a.alignment_score < 0.8)
        moderate = sum(1 for a in all_analyses if 0.4 <= a.alignment_score < 0.6)
        poor = sum(1 for a in all_analyses if a.alignment_score < 0.4)

        summary = [
            "=== PRINCIPAL'S PEDAGOGICAL SUMMARY ===",
            f"\nTotal Chunks Analyzed: {len(all_analyses)}",
            f"Average KLI Alignment Score: {avg_score:.2f}/1.0",
            f"\nAlignment Distribution:",
            f"  - Excellent (0.8-1.0): {excellent} chunks",
            f"  - Good (0.6-0.8): {good} chunks",
            f"  - Moderate (0.4-0.6): {moderate} chunks",
            f"  - Poor (0.0-0.4): {poor} chunks",
        ]

        if poor > 0:
            summary.append(
                f"\n⚠️  {poor} chunk(s) with poor alignment need immediate attention."
            )
            low_scoring = [a for a in all_analyses if a.alignment_score < 0.4]
            summary.append("\nCritical Issues:")
            for analysis in low_scoring:
                summary.append(
                    f"  - {analysis.chunk_id}: Score {analysis.alignment_score:.2f}"
                )

        return "\n".join(summary)

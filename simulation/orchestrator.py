"""
Simulation Orchestrator

This module implements the main engine that runs a single classroom simulation
from start to finish, coordinating teacher, student, and principal agents.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from material_parser.parser import parse_document
from personality.classroom_service import ClassroomService
from personality.create_class_personalities import CreatePersonalities
from pydantic_classes import (
    ChunkDetails,
    CognitiveState,
    PrincipalAnalysis,
    Provider,
    ReasoningEffort,
    SimulationRun,
    StudentAgentState,
    StudentResponse,
    TeacherAgentConfig,
    TeachingOutput,
)
from simulation.cognitive_state import CognitiveStateManager
from simulation.doubt_selector import select_doubt_askers
from simulation.principal_agent import PrincipalAgent
from simulation.student_agent import StudentAgent
from simulation.teacher_agent import TeacherAgent


class SimulationOrchestrator:
    """
    Main engine that runs a single classroom simulation.

    Coordinates the teaching-doubt-analysis cycle for each chunk of material,
    collecting results for post-simulation analysis.
    """

    def __init__(
        self,
        material_file_path: str,
        teacher_config: TeacherAgentConfig,
        class_name: str,
        professor_name: str,
        student_limit: Optional[int] = None,
        selected_student_ids: Optional[List[str]] = None,
        model_provider: Provider = Provider.LIGHTNING,
        model_name: str = "lightning-ai/gpt-oss-20b",
    ):
        """
        Initialize the Simulation Orchestrator.

        Parameters
        ----------
        material_file_path : str
            Path to the course material file (PDF, PPT, PPTX, DOC, DOCX)
        teacher_config : TeacherAgentConfig
            Configuration for the teacher agent including personality
        class_name : str
            Name/location of the classroom (used to fetch students from MongoDB)
        professor_name : str
            Name of the professor (used to fetch students from MongoDB)
        student_limit : Optional[int]
            Maximum number of students to include in simulation
        selected_student_ids : Optional[List[str]]
            If provided, only include students with these IDs (for multi-run subset selection)
        model_provider : Provider
            LLM provider to use for agent calls
        model_name : str
            Model name to use for agent calls
        """
        self.material_file_path = material_file_path
        self.teacher_config = teacher_config
        self.class_name = class_name
        self.professor_name = professor_name
        self.student_limit = student_limit
        self.selected_student_ids = selected_student_ids
        self.model_provider = model_provider
        self.model_name = model_name

        self.logger = logging.getLogger(__name__)

        # These will be initialized in run_single_simulation
        self.chunks: List[ChunkDetails] = []
        self.teacher_agent: Optional[TeacherAgent] = None
        self.student_agents: List[StudentAgent] = []
        self.principal_agent: Optional[PrincipalAgent] = None

    async def run_single_simulation(self) -> SimulationRun:
        """
        Execute the complete simulation loop.

        Implements the loop from FinalPlanAgents.md Section 4.1:
        1. Teacher teaches chunk
        2. All students rate understanding
        3. Select doubt askers (understanding <= 2, fatigue < 80)
        4. Teacher responds to doubts
        5. Askers re-rate understanding (IRF check)
        6. Principal analyzes chunk
        7. Update all student cognitive states

        Returns
        -------
        SimulationRun
            Complete results of the simulation including all chunk data
        """
        run_id = str(uuid.uuid4())
        timestamp = datetime.now()

        self.logger.info(f"Starting simulation run {run_id}")

        # Initialize all components
        await self._initialize_simulation()

        chunk_results: List[Dict[str, Any]] = []
        all_principal_analyses: List[PrincipalAnalysis] = []

        # Main simulation loop
        for chunk_index, chunk in enumerate(self.chunks):
            self.logger.info(
                f"Processing chunk {chunk_index + 1}/{len(self.chunks)}: {chunk.chunk_id}"
            )

            try:
                result = await self._process_chunk(chunk)
                chunk_results.append(result)

                if result.get("principal_analysis"):
                    all_principal_analyses.append(result["principal_analysis"])

            except Exception as e:
                self.logger.error(f"Error processing chunk {chunk.chunk_id}: {e}")
                # Continue with next chunk on error
                chunk_results.append(
                    {
                        "chunk_id": chunk.chunk_id,
                        "error": str(e),
                    }
                )

        # Generate principal summary
        principal_summary = await self._generate_principal_summary(
            all_principal_analyses
        )

        # Collect student IDs
        students_selected = [agent.state.student_id for agent in self.student_agents]

        self.logger.info(f"Simulation run {run_id} completed")

        return SimulationRun(
            run_id=run_id,
            timestamp=timestamp,
            teacher_config=self.teacher_config,
            students_selected=students_selected,
            chunk_results=chunk_results,
            principal_summary=principal_summary,
        )

    async def _initialize_simulation(self) -> None:
        """Initialize all agents and parse material."""
        self.logger.info("Initializing simulation components...")

        # Parse material into chunks
        self.chunks = parse_document(self.material_file_path)
        self.logger.info(f"Parsed {len(self.chunks)} chunks from material")

        # Initialize teacher agent
        self.teacher_agent = TeacherAgent(self.teacher_config)

        # Initialize principal agent (no config needed)
        self.principal_agent = PrincipalAgent()

        # Initialize student agents
        await self._initialize_students()

        self.logger.info(f"Initialized {len(self.student_agents)} student agents")

    async def _initialize_students(self) -> None:
        """Fetch students from database and create student agents."""
        # Create personalities service
        personality_service = CreatePersonalities()

        try:
            # Get student personalities (this creates biographies via LLM)
            student_personalities = await personality_service.create_personalities(
                class_number=self.class_name,
                professor_name=self.professor_name,
                limit=self.student_limit,
            )

            # Fetch raw student details for StudentAgent initialization
            classroom_service = ClassroomService()
            classroom_details = classroom_service.get_classroom_details(
                location=self.class_name,
                professor_name=self.professor_name,
                limit=self.student_limit,
            )

            # Filter students if selected_student_ids is provided
            students_to_use = classroom_details.students
            if self.selected_student_ids is not None:
                students_to_use = [
                    s
                    for s in classroom_details.students
                    if s.college_id in self.selected_student_ids
                ]
                self.logger.info(
                    f"Filtered to {len(students_to_use)} students from selected_student_ids"
                )

            # Create StudentAgent for each student
            for i, student_details in enumerate(students_to_use):
                # Match personality prompt from created personalities
                personality_prompt = None
                if i < len(student_personalities):
                    personality_prompt = student_personalities[i].get("prompt")

                agent = StudentAgent(
                    student_details=student_details,
                    personality_prompt=personality_prompt,
                )
                self.student_agents.append(agent)

        finally:
            personality_service.close_client()

    async def _process_chunk(self, chunk: ChunkDetails) -> Dict[str, Any]:
        """
        Process a single chunk through the complete teaching cycle.

        Parameters
        ----------
        chunk : ChunkDetails
            The chunk to process

        Returns
        -------
        Dict[str, Any]
            Results including teaching output, student responses, and principal analysis
        """
        # Step 1: Teacher teaches chunk
        teaching_output = await self.teacher_agent.teach_chunk(
            chunk=chunk,
            model_provider=self.model_provider,
            model_name=self.model_name,
        )

        # Step 2: All students rate understanding
        student_responses: List[StudentResponse] = []
        for student in self.student_agents:
            understanding = await student.rate_understanding(
                chunk=chunk,
                teaching_transcript=teaching_output.teaching_transcript,
                model_provider=self.model_provider,
                model_name=self.model_name,
            )

            # Update the student's cognitive state with initial understanding
            student.state.cognitive_state.understanding = understanding

            # Create initial response (will be updated if student asks doubt)
            student_responses.append(
                StudentResponse(
                    student_id=student.state.student_id,
                    chunk_id=chunk.chunk_id,
                    understanding_before=understanding,
                    understanding_after=understanding,
                )
            )

        # Step 3: Select doubt askers
        doubt_askers = select_doubt_askers(self.student_agents)

        # Steps 4-5: Handle doubts for selected students
        for asker in doubt_askers:
            await self._handle_student_doubt(
                student=asker,
                chunk=chunk,
                teaching_output=teaching_output,
                student_responses=student_responses,
            )

        # Step 6: Principal analyzes chunk
        principal_analysis = await self.principal_agent.analyze_chunk(
            chunk=chunk,
            teaching_transcript=teaching_output.teaching_transcript,
            student_responses=student_responses,
        )

        # Step 7: Update all student cognitive states
        for student in self.student_agents:
            CognitiveStateManager.update_after_chunk(student.state)

        return {
            "chunk_id": chunk.chunk_id,
            "teaching_output": teaching_output.model_dump(),
            "student_responses": [r.model_dump() for r in student_responses],
            "principal_analysis": principal_analysis,
        }

    async def _handle_student_doubt(
        self,
        student: StudentAgent,
        chunk: ChunkDetails,
        teaching_output: TeachingOutput,
        student_responses: List[StudentResponse],
    ) -> None:
        """
        Handle doubt generation and response for a single student.

        Parameters
        ----------
        student : StudentAgent
            The student asking the doubt
        chunk : ChunkDetails
            Current chunk being taught
        teaching_output : TeachingOutput
            Teacher's explanation of the chunk
        student_responses : List[StudentResponse]
            List to update with doubt information
        """
        try:
            # Step 4: Generate doubt
            doubt = await student.generate_doubt(
                chunk=chunk,
                teaching_transcript=teaching_output.teaching_transcript,
                model_provider=self.model_provider,
                model_name=self.model_name,
            )

            # Record the doubt
            student.state.doubts_asked.append(doubt)

            # Teacher responds to doubt
            response = await self.teacher_agent.respond_to_doubt(
                doubt=doubt,
                chunk=chunk,
                model_provider=self.model_provider,
                model_name=self.model_name,
            )

            # Step 5: Student re-rates understanding (IRF check)
            understanding_after = await student.rerate_after_response(
                chunk=chunk,
                doubt=doubt,
                teacher_response=response,
                model_provider=self.model_provider,
                model_name=self.model_name,
            )

            # Find and update this student's response
            for resp in student_responses:
                if resp.student_id == student.state.student_id:
                    resp.doubt_asked = doubt
                    resp.understanding_after = understanding_after
                    resp.doubt_resolved = (
                        understanding_after > resp.understanding_before
                    )
                    break

        except Exception as e:
            self.logger.error(
                f"Error handling doubt for student {student.state.student_id}: {e}"
            )

    async def _generate_principal_summary(
        self,
        all_analyses: List[PrincipalAnalysis],
    ) -> PrincipalAnalysis:
        """
        Generate a summary analysis from all chunk analyses.

        Parameters
        ----------
        all_analyses : List[PrincipalAnalysis]
            All per-chunk principal analyses

        Returns
        -------
        PrincipalAnalysis
            Summary analysis for the entire simulation
        """
        if not all_analyses:
            return PrincipalAnalysis(
                chunk_id="summary",
                alignment_score=0.0,
                notes="No chunks were analyzed.",
            )

        # Calculate average alignment score
        avg_alignment = sum(a.alignment_score for a in all_analyses) / len(all_analyses)

        # Collect all missing prerequisites
        all_prerequisites = []
        for analysis in all_analyses:
            all_prerequisites.extend(analysis.missing_prerequisites)
        unique_prerequisites = list(set(all_prerequisites))

        # Collect all suggested methods
        all_methods = []
        for analysis in all_analyses:
            all_methods.extend(analysis.suggested_methods)
        unique_methods = list(set(all_methods))

        # Generate summary notes using principal agent
        summary_text = await self.principal_agent.generate_summary(all_analyses)

        return PrincipalAnalysis(
            chunk_id="summary",
            alignment_score=avg_alignment,
            missing_prerequisites=unique_prerequisites,
            suggested_methods=unique_methods,
            notes=summary_text,
        )

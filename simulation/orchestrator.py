"""
Simulation Orchestrator

This module implements the main engine that runs a single classroom simulation
from start to finish, coordinating teacher, student, and principal agents.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from material_parser.parser import parse_document
from personality.classroom_service import ClassroomService
from personality.create_class_personalities import CreatePersonalities
from pydantic_classes import (
    ChunkDetails,
    CognitiveState,
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
        model_name: str = "lightning-ai/gpt-oss-120b",
        on_message: Optional[Callable[[dict], None]] = None,
        prebuilt_personalities: Optional[List[Dict[str, Any]]] = None,
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
        prebuilt_personalities : Optional[List[Dict[str, Any]]]
            Pre-generated personality prompts (keyed by college_id) to avoid
            redundant work across multi-run simulations.
            Each dict should contain at least 'college_id' and 'prompt'.
        """
        self.material_file_path = material_file_path
        self.teacher_config = teacher_config
        self.class_name = class_name
        self.professor_name = professor_name
        self.student_limit = student_limit
        self.selected_student_ids = selected_student_ids
        self.model_provider = model_provider
        self.model_name = model_name
        self.on_message = on_message
        self.prebuilt_personalities = prebuilt_personalities

        self.logger = logging.getLogger(__name__)

        # These will be initialized in run_single_simulation
        self.chunks: List[ChunkDetails] = []
        self.teacher_agent: Optional[TeacherAgent] = None
        self.student_agents: List[StudentAgent] = []
        self.principal_agent: Optional[PrincipalAgent] = None

    async def run_single_simulation(self) -> SimulationRun:
        """
        Execute the complete simulation loop.

        Per-chunk loop:
        1. Teacher teaches chunk
        2. All students rate understanding
        3. Select doubt askers (understanding <= 2, fatigue < 80)
        4. Teacher responds to doubts
        5. Askers re-rate understanding (IRF check)
        6. Update all student cognitive states

        After all chunks:
        7. Principal runs one holistic KLI analysis over the entire session

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

        # Main simulation loop
        total_chunks = len(self.chunks)
        for chunk_index, chunk in enumerate(self.chunks):
            self.logger.info(
                f"Processing chunk {chunk_index + 1}/{total_chunks}: {chunk.chunk_id}"
            )

            try:
                result = await self._process_chunk(
                    chunk,
                    chunk_number=chunk_index + 1,
                    total_chunks=total_chunks,
                )
                chunk_results.append(result)

            except Exception as e:
                self.logger.error(f"Error processing chunk {chunk.chunk_id}: {e}")
                # Continue with next chunk on error
                chunk_results.append(
                    {
                        "chunk_id": chunk.chunk_id,
                        "error": str(e),
                    }
                )

        # Run principal KLI analysis once over the entire session
        self.logger.info("Running end-of-session KLI analysis...")
        principal_summary = await self.principal_agent.analyze_session(
            chunks=self.chunks,
            chunk_results=chunk_results,
        )

        # Stream principal's end-of-session report to live chat
        if self.on_message and principal_summary.notes:
            self.on_message(
                {
                    "id": str(uuid.uuid4()),
                    "sender": "Principal",
                    "name": "Principal",
                    "content": principal_summary.notes,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "type": "principal_summary",
                }
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
        """Fetch students from database and create student agents.

        If prebuilt_personalities were supplied at construction time they are
        used directly, avoiding redundant DB and personality-building calls
        across multi-run simulations.
        """
        if self.prebuilt_personalities is not None:
            # Use cached personalities — no extra work needed
            student_personalities = self.prebuilt_personalities
            self.logger.info("Using prebuilt personalities")
        else:
            # Generate personalities via LLM (original path for single runs)
            personality_service = CreatePersonalities()
            try:
                student_personalities = await personality_service.create_personalities(
                    class_number=self.class_name,
                    professor_name=self.professor_name,
                    limit=self.student_limit,
                )
            finally:
                personality_service.close_client()

        # Build a lookup dict keyed by college_id for reliable matching
        personality_lookup: Dict[str, str] = {
            p["college_id"]: p.get("prompt")
            for p in student_personalities
            if "college_id" in p
        }

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
        for student_details in students_to_use:
            # Match personality by college_id (reliable) with name fallback
            personality_prompt = personality_lookup.get(student_details.college_id)

            if personality_prompt is None:
                # Fallback: match by name for legacy personality dicts
                for p in student_personalities:
                    if p.get("name") == student_details.name:
                        personality_prompt = p.get("prompt")
                        break

            agent = StudentAgent(
                student_details=student_details,
                personality_prompt=personality_prompt,
            )
            self.student_agents.append(agent)

    async def _process_chunk(
        self,
        chunk: ChunkDetails,
        chunk_number: int = 1,
        total_chunks: int = 1,
    ) -> Dict[str, Any]:
        """
        Process a single chunk through the complete teaching cycle.

        Parameters
        ----------
        chunk : ChunkDetails
            The chunk to process
        chunk_number : int
            1-based index of this chunk (e.g. 3 means "3rd chunk")
        total_chunks : int
            Total number of chunks in the session

        Returns
        -------
        Dict[str, Any]
            Results including teaching output and student responses for the chunk
        """
        # Step 1: Teacher teaches chunk
        teaching_output = await self.teacher_agent.teach_chunk(
            chunk=chunk,
            chunk_number=chunk_number,
            total_chunks=total_chunks,
            model_provider=self.model_provider,
            model_name=self.model_name,
        )

        # Stream teacher message to live chat
        if self.on_message and teaching_output.teaching_transcript:
            self.on_message(
                {
                    "id": str(uuid.uuid4()),
                    "sender": "Teacher",
                    "name": self.teacher_config.name,
                    "content": teaching_output.teaching_transcript,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
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

        # Emit voting summary so the frontend can display student understanding scores
        if self.on_message:
            votes = [
                {
                    "name": s.name,
                    "student_id": s.state.student_id,
                    "understanding": s.state.cognitive_state.understanding,
                }
                for s in self.student_agents
            ]
            self.on_message(
                {
                    "id": str(uuid.uuid4()),
                    "sender": "System",
                    "name": "Student Voting",
                    "content": "",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "type": "voting",
                    "chunk_id": chunk.chunk_id,
                    "votes": votes,
                }
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
                chunk_number=chunk_number,
                total_chunks=total_chunks,
            )

        # Step 6: Update all student cognitive states
        for student in self.student_agents:
            CognitiveStateManager.update_after_chunk(student.state)

        return {
            "chunk_id": chunk.chunk_id,
            "teaching_output": teaching_output.model_dump(),
            "student_responses": [r.model_dump() for r in student_responses],
        }

    async def _handle_student_doubt(
        self,
        student: StudentAgent,
        chunk: ChunkDetails,
        teaching_output: TeachingOutput,
        student_responses: List[StudentResponse],
        chunk_number: int = 1,
        total_chunks: int = 1,
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
        chunk_number : int
            1-based index of this chunk
        total_chunks : int
            Total number of chunks in the session
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

            # Stream student doubt to live chat
            if self.on_message and doubt:
                self.on_message(
                    {
                        "id": str(uuid.uuid4()),
                        "sender": "Student",
                        "name": student.name,
                        "content": doubt,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    }
                )

            # Teacher responds to doubt
            response = await self.teacher_agent.respond_to_doubt(
                doubt=doubt,
                chunk=chunk,
                chunk_number=chunk_number,
                total_chunks=total_chunks,
                model_provider=self.model_provider,
                model_name=self.model_name,
            )

            # Stream teacher response to live chat
            if self.on_message and response:
                self.on_message(
                    {
                        "id": str(uuid.uuid4()),
                        "sender": "Teacher",
                        "name": self.teacher_config.name,
                        "content": response,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    }
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

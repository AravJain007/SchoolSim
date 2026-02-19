"""
Multi-Run Executor

Orchestrates multiple simulation runs with random student subset selection
to gather statistically meaningful aggregated results.

Runs are executed SEQUENTIALLY (one at a time) to avoid overwhelming the LLM provider.
A short delay between runs helps prevent rate limiting.
"""

import asyncio
import logging
import random
from typing import Callable, Dict, List, Optional

from personality.classroom_service import ClassroomService
from personality.create_class_personalities import CreatePersonalities
from pydantic_classes import Provider, SimulationRun, StudentDetails, TeacherAgentConfig
from simulation.orchestrator import SimulationOrchestrator


class MultiRunExecutor:
    """
    Executes multiple simulation runs with random student subsets.

    Each run uses a randomly selected subset of students (50-100% of class size)
    to provide statistical variance and expose different failure modes.
    """

    def __init__(
        self,
        material_file_path: str,
        teacher_config: TeacherAgentConfig,
        class_name: str,
        professor_name: str,
        model_provider: Provider = Provider.LIGHTNING,
        model_name: str = "lightning-ai/gpt-oss-120b",
        on_message: Optional[Callable[[dict], None]] = None,
        on_run_progress: Optional[Callable[[int, int], None]] = None,
    ):
        """
        Initialize the Multi-Run Executor.

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
        model_provider : Provider
            LLM provider to use for agent calls
        model_name : str
            Model name to use for agent calls
        """
        self.material_file_path = material_file_path
        self.teacher_config = teacher_config
        self.class_name = class_name
        self.professor_name = professor_name
        self.model_provider = model_provider
        self.model_name = model_name
        self.on_message = on_message
        self.on_run_progress = on_run_progress

        self.logger = logging.getLogger(__name__)

        # Cache all students for subset selection
        self._all_students: Optional[List[StudentDetails]] = None

    def _calculate_sample_range(self, total_students: int) -> tuple[int, int]:
        """
        Calculate the min/max sample size for random student selection.

        Rules:
        - Sample between 50-100% of class size per run
        - Minimum 5 students regardless of class size

        Parameters
        ----------
        total_students : int
            Total number of students in the class

        Returns
        -------
        tuple[int, int]
            (min_sample, max_sample) range for random selection
        """
        min_sample = max(5, int(total_students * 0.5))
        max_sample = total_students
        return (min_sample, max_sample)

    def _select_students_for_run(self, all_students: List[StudentDetails]) -> List[str]:
        """
        Randomly select a subset of students for a single run.

        Parameters
        ----------
        all_students : List[StudentDetails]
            All available students in the class

        Returns
        -------
        List[str]
            List of selected student IDs (college_id)
        """
        total = len(all_students)
        min_sample, max_sample = self._calculate_sample_range(total)
        sample_size = random.randint(min_sample, max_sample)

        selected = random.sample(all_students, sample_size)
        return [s.college_id for s in selected]

    def _fetch_all_students(self) -> List[StudentDetails]:
        """
        Fetch all students from the database (cached).

        Returns
        -------
        List[StudentDetails]
            All students in the class
        """
        if self._all_students is None:
            classroom_service = ClassroomService()
            classroom_details = classroom_service.get_classroom_details(
                location=self.class_name,
                professor_name=self.professor_name,
                limit=None,  # Get all students
            )
            self._all_students = classroom_details.students
            self.logger.info(
                f"Fetched {len(self._all_students)} students from database"
            )

        return self._all_students

    async def _generate_all_personalities(self) -> List[Dict]:
        """
        Build personality prompts for ALL students once before the run loop.

        Calling this once avoids redundant DB queries and prompt construction
        across runs.

        Returns
        -------
        List[Dict]
            List of personality dicts (each with 'college_id', 'name', 'prompt', etc.)
        """
        self.logger.info("Building personalities for all students (once)...")
        personality_service = CreatePersonalities()
        try:
            all_personalities = await personality_service.create_personalities(
                class_number=self.class_name,
                professor_name=self.professor_name,
                limit=None,  # Generate for ALL students
            )
            self.logger.info(
                f"Generated {len(all_personalities)} student personalities"
            )
            return all_personalities
        finally:
            personality_service.close_client()

    async def run_multiple(self, n_runs: int) -> List[SimulationRun]:
        """
        Execute multiple simulation runs with random student subsets.

        For each run:
        1. Randomly select subset of students (50-100% of class)
        2. Create new SimulationOrchestrator with selected students
        3. Execute simulation (reusing pre-generated personalities)
        4. Collect results

        Parameters
        ----------
        n_runs : int
            Number of simulation runs to execute

        Returns
        -------
        List[SimulationRun]
            Results from all simulation runs
        """
        self.logger.info(f"Starting multi-run execution with {n_runs} runs")

        # Fetch all students once
        all_students = self._fetch_all_students()
        total_students = len(all_students)

        if total_students == 0:
            self.logger.error("No students found in class")
            return []

        min_sample, max_sample = self._calculate_sample_range(total_students)
        self.logger.info(
            f"Class has {total_students} students. "
            f"Each run will sample {min_sample}-{max_sample} students."
        )

        # Build all student personalities ONCE before the run loop.
        all_personalities = await self._generate_all_personalities()

        runs: List[SimulationRun] = []
        first_error: Optional[Exception] = None

        for run_index in range(n_runs):
            self.logger.info(f"Starting run {run_index + 1}/{n_runs}")

            # Select random subset of students for this run
            selected_student_ids = self._select_students_for_run(all_students)
            self.logger.info(
                f"Run {run_index + 1}: Selected {len(selected_student_ids)} students"
            )

            try:
                # Tag every message with the current run_index before forwarding
                def tagged_on_message(msg: dict, _idx: int = run_index) -> None:
                    msg["run_index"] = _idx
                    if self.on_message:
                        self.on_message(msg)

                # Create orchestrator with selected students and prebuilt personalities
                orchestrator = SimulationOrchestrator(
                    material_file_path=self.material_file_path,
                    teacher_config=self.teacher_config,
                    class_name=self.class_name,
                    professor_name=self.professor_name,
                    selected_student_ids=selected_student_ids,
                    model_provider=self.model_provider,
                    model_name=self.model_name,
                    on_message=tagged_on_message,
                    prebuilt_personalities=all_personalities,
                )

                # Execute simulation
                result = await orchestrator.run_single_simulation()
                runs.append(result)

                self.logger.info(f"Run {run_index + 1} completed successfully")

                if self.on_run_progress:
                    self.on_run_progress(run_index, n_runs)

                # Pause between runs to avoid overwhelming LLM provider (15-20s random)
                if run_index < n_runs - 1:
                    delay = random.uniform(15, 20)
                    self.logger.info(f"Pausing {delay:.1f}s before next run...")
                    await asyncio.sleep(delay)

            except Exception as e:
                self.logger.error(f"Run {run_index + 1} failed: {e}")
                if first_error is None:
                    first_error = e
                # Continue with next run on error

        self.logger.info(
            f"Multi-run execution completed. {len(runs)}/{n_runs} runs successful."
        )

        if not runs and n_runs > 0 and first_error is not None:
            raise first_error

        return runs

"""
Test Aggregation Module

Integration tests for the aggregation module including multi-run execution,
difficulty calculation, gap detection, and report generation.

Run with: python -m pytest aggregation/test_aggregation.py -v
"""

import asyncio
from datetime import datetime
from typing import List

import pytest

# Import aggregation functions
from aggregation.analyzer import (
    calculate_irf_plus,
    calculate_irf_plus_from_runs,
    find_common_doubts,
    get_per_chunk_avg_understanding,
)
from aggregation.difficulty_calculator import (
    compute_difficulty_index,
    get_difficulty_summary,
    populate_chunk_difficulty,
)
from aggregation.gap_detector import (
    detect_gaps,
    detect_gaps_with_details,
    get_chunk_failure_rates,
)
from aggregation.multi_run import MultiRunExecutor
from aggregation.report_generator import (
    generate_aggregated_results,
    generate_gap_report,
    generate_principal_summary,
)
from pydantic_classes import (
    AggregatedResults,
    ChunkDetails,
    PrincipalAnalysis,
    SimulationRun,
    StudentResponse,
    TeacherAgentConfig,
)

# =============================================================================
# Test Fixtures - Mock Data
# =============================================================================


def create_mock_student_responses(
    chunk_id: str,
    num_students: int = 5,
    avg_understanding: float = 3.0,
    num_doubts: int = 2,
    doubts_resolved: int = 1,
) -> List[dict]:
    """Create mock student responses for testing."""
    responses = []

    for i in range(num_students):
        # Vary understanding around the average
        understanding_before = max(1, min(5, int(avg_understanding - 1)))
        understanding_after = max(1, min(5, int(avg_understanding + (i % 2))))

        response = {
            "student_id": f"student_{i}",
            "chunk_id": chunk_id,
            "understanding_before": understanding_before,
            "understanding_after": understanding_after,
            "doubt_asked": None,
            "doubt_resolved": None,
        }

        # Add doubts for first few students
        if i < num_doubts:
            response["doubt_asked"] = f"What does concept {i} mean in chunk {chunk_id}?"
            response["doubt_resolved"] = i < doubts_resolved

        responses.append(response)

    return responses


def create_mock_simulation_run(
    run_id: str,
    num_chunks: int = 3,
    avg_understanding: float = 3.0,
) -> SimulationRun:
    """Create a mock SimulationRun for testing."""
    chunk_results = []

    for i in range(num_chunks):
        chunk_id = f"chunk_{i + 1}"

        # Vary understanding per chunk
        chunk_avg = (
            avg_understanding + (i - 1) * 0.5
        )  # chunk_1: avg-0.5, chunk_2: avg, chunk_3: avg+0.5
        chunk_avg = max(1.0, min(5.0, chunk_avg))

        responses = create_mock_student_responses(
            chunk_id=chunk_id,
            num_students=5,
            avg_understanding=chunk_avg,
            num_doubts=2 if chunk_avg < 3 else 1,
            doubts_resolved=1,
        )

        chunk_results.append(
            {
                "chunk_id": chunk_id,
                "teaching_output": {
                    "chunk_id": chunk_id,
                    "teaching_transcript": f"Explanation for {chunk_id}",
                    "teaching_method_used": "direct_explanation",
                },
                "student_responses": responses,
                "principal_analysis": {
                    "chunk_id": chunk_id,
                    "alignment_score": 0.7 + (i * 0.1),
                    "missing_prerequisites": [],
                    "suggested_methods": ["example", "practice"] if i == 0 else [],
                    "notes": f"Notes for {chunk_id}",
                },
            }
        )

    return SimulationRun(
        run_id=run_id,
        timestamp=datetime.now(),
        teacher_config=TeacherAgentConfig(
            teacher_id="teacher_1",
            name="Test Teacher",
            personality_prompt="A helpful teacher",
            big5_scores={"O": 70, "C": 65, "E": 60, "A": 75, "N": 40},
        ),
        students_selected=[f"student_{i}" for i in range(5)],
        chunk_results=chunk_results,
        principal_summary=PrincipalAnalysis(
            chunk_id="summary",
            alignment_score=0.75,
            missing_prerequisites=["prerequisite_1"],
            suggested_methods=["practice", "example"],
            notes="Overall good alignment with room for improvement.",
        ),
    )


def create_mock_chunks(num_chunks: int = 3) -> List[ChunkDetails]:
    """Create mock chunks for testing."""
    return [
        ChunkDetails(
            chunk_id=f"chunk_{i + 1}",
            content=f"Content for chunk {i + 1}. This explains concept {i + 1}.",
            difficulty_index=None,
            page_range=f"Slide {i + 1}",
            has_formula=i == 1,
            has_code=i == 2,
        )
        for i in range(num_chunks)
    ]


# =============================================================================
# Unit Tests - Analyzer
# =============================================================================


class TestAnalyzer:
    """Tests for aggregation/analyzer.py functions."""

    def test_calculate_irf_plus_all_resolved(self):
        """Test IRF+ calculation when all doubts are resolved."""
        responses = [
            StudentResponse(
                student_id="s1",
                chunk_id="c1",
                understanding_before=2,
                understanding_after=4,
                doubt_asked="What is X?",
                doubt_resolved=True,
            ),
            StudentResponse(
                student_id="s2",
                chunk_id="c1",
                understanding_before=2,
                understanding_after=4,
                doubt_asked="What is Y?",
                doubt_resolved=True,
            ),
        ]

        result = calculate_irf_plus(responses)
        assert result == 1.0  # All doubts resolved

    def test_calculate_irf_plus_none_resolved(self):
        """Test IRF+ calculation when no doubts are resolved."""
        responses = [
            StudentResponse(
                student_id="s1",
                chunk_id="c1",
                understanding_before=2,
                understanding_after=2,
                doubt_asked="What is X?",
                doubt_resolved=False,
            ),
            StudentResponse(
                student_id="s2",
                chunk_id="c1",
                understanding_before=2,
                understanding_after=2,
                doubt_asked="What is Y?",
                doubt_resolved=False,
            ),
        ]

        result = calculate_irf_plus(responses)
        assert result == 0.0  # No doubts resolved

    def test_calculate_irf_plus_partial(self):
        """Test IRF+ calculation with partial resolution."""
        responses = [
            StudentResponse(
                student_id="s1",
                chunk_id="c1",
                understanding_before=2,
                understanding_after=4,
                doubt_asked="What is X?",
                doubt_resolved=True,
            ),
            StudentResponse(
                student_id="s2",
                chunk_id="c1",
                understanding_before=2,
                understanding_after=2,
                doubt_asked="What is Y?",
                doubt_resolved=False,
            ),
        ]

        result = calculate_irf_plus(responses)
        assert result == 0.5  # 1 of 2 resolved

    def test_calculate_irf_plus_no_doubts(self):
        """Test IRF+ calculation when no doubts were asked."""
        responses = [
            StudentResponse(
                student_id="s1",
                chunk_id="c1",
                understanding_before=4,
                understanding_after=5,
            ),
        ]

        result = calculate_irf_plus(responses)
        assert result == 0.0  # No doubts to evaluate

    def test_find_common_doubts(self):
        """Test grouping doubts by chunk."""
        runs = [
            create_mock_simulation_run("run_1"),
            create_mock_simulation_run("run_2"),
        ]

        result = find_common_doubts(runs)

        assert "chunk_1" in result
        assert len(result["chunk_1"]) > 0
        assert all(isinstance(d, str) for d in result["chunk_1"])

    def test_get_per_chunk_avg_understanding(self):
        """Test calculating average understanding per chunk."""
        runs = [create_mock_simulation_run("run_1", avg_understanding=3.0)]

        result = get_per_chunk_avg_understanding(runs)

        assert "chunk_1" in result
        assert "chunk_2" in result
        assert "chunk_3" in result
        assert all(1.0 <= v <= 5.0 for v in result.values())


# =============================================================================
# Unit Tests - Difficulty Calculator
# =============================================================================


class TestDifficultyCalculator:
    """Tests for aggregation/difficulty_calculator.py functions."""

    def test_compute_difficulty_index_high_understanding(self):
        """Test difficulty is low when understanding is high."""
        runs = [create_mock_simulation_run("run_1", avg_understanding=5.0)]

        result = compute_difficulty_index("chunk_2", runs)

        # High understanding (5) -> Low difficulty (0)
        assert result <= 20.0  # Should be close to 0

    def test_compute_difficulty_index_low_understanding(self):
        """Test difficulty is high when understanding is low."""
        runs = [create_mock_simulation_run("run_1", avg_understanding=1.5)]

        result = compute_difficulty_index("chunk_2", runs)

        # Low understanding (1.5) -> High difficulty
        assert result >= 50.0  # Should be high

    def test_compute_difficulty_index_missing_chunk(self):
        """Test difficulty for non-existent chunk."""
        runs = [create_mock_simulation_run("run_1")]

        result = compute_difficulty_index("nonexistent_chunk", runs)

        assert result == 0.0

    def test_populate_chunk_difficulty(self):
        """Test populating difficulty for all chunks."""
        chunks = create_mock_chunks(3)
        runs = [create_mock_simulation_run("run_1")]

        result = populate_chunk_difficulty(chunks, runs)

        assert len(result) == 3
        assert all(c.difficulty_index is not None for c in result)

    def test_get_difficulty_summary(self):
        """Test generating difficulty summary."""
        chunks = create_mock_chunks(3)
        runs = [create_mock_simulation_run("run_1")]

        result = get_difficulty_summary(chunks, runs)

        assert "per_chunk" in result
        assert "overall" in result
        assert "average" in result["overall"]
        assert "max" in result["overall"]
        assert "min" in result["overall"]


# =============================================================================
# Unit Tests - Gap Detector
# =============================================================================


class TestGapDetector:
    """Tests for aggregation/gap_detector.py functions."""

    def test_detect_gaps_with_low_understanding(self):
        """Test gap detection when understanding is low."""
        # Create runs with very low understanding
        runs = [
            create_mock_simulation_run("run_1", avg_understanding=1.5),
            create_mock_simulation_run("run_2", avg_understanding=1.5),
        ]

        result = detect_gaps(runs, threshold=0.4)

        # With avg understanding of 1.5, most chunks should be gaps
        assert len(result) > 0

    def test_detect_gaps_with_high_understanding(self):
        """Test gap detection when understanding is high."""
        runs = [
            create_mock_simulation_run("run_1", avg_understanding=4.5),
            create_mock_simulation_run("run_2", avg_understanding=4.5),
        ]

        result = detect_gaps(runs, threshold=0.4)

        # With high understanding, should have no/few gaps
        assert len(result) <= 1  # May still have chunk_1 which has lower avg

    def test_detect_gaps_empty_runs(self):
        """Test gap detection with empty runs list."""
        result = detect_gaps([], threshold=0.4)

        assert result == []

    def test_detect_gaps_with_details(self):
        """Test gap detection with detailed output."""
        runs = [create_mock_simulation_run("run_1", avg_understanding=2.0)]

        result = detect_gaps_with_details(runs, threshold=0.3)

        if result:  # May have gaps depending on avg understanding
            assert all("chunk_id" in g for g in result)
            assert all("failure_rate" in g for g in result)
            assert all("avg_understanding" in g for g in result)

    def test_get_chunk_failure_rates(self):
        """Test calculating failure rates per chunk."""
        runs = [create_mock_simulation_run("run_1")]

        result = get_chunk_failure_rates(runs)

        assert "chunk_1" in result
        assert all(0.0 <= v <= 1.0 for v in result.values())


# =============================================================================
# Unit Tests - Report Generator
# =============================================================================


class TestReportGenerator:
    """Tests for aggregation/report_generator.py functions."""

    def test_generate_gap_report(self):
        """Test gap report generation."""
        runs = [create_mock_simulation_run("run_1", avg_understanding=2.0)]
        chunks = create_mock_chunks(3)
        gaps = ["chunk_1"]  # Simulate detecting chunk_1 as a gap

        result = generate_gap_report(gaps, runs, chunks)

        assert "gaps" in result
        if result["gaps"]:
            gap = result["gaps"][0]
            assert "chunk_id" in gap
            assert "avg_understanding" in gap
            assert "difficulty_index" in gap

    def test_generate_principal_summary(self):
        """Test principal summary generation."""
        runs = [create_mock_simulation_run("run_1")]

        result = generate_principal_summary(runs)

        assert "overall_alignment" in result
        assert "critical_misalignments" in result
        assert "missing_prerequisites" in result
        assert "bloom_progression" in result
        assert 0.0 <= result["overall_alignment"] <= 1.0

    def test_generate_aggregated_results(self):
        """Test complete aggregated results generation."""
        runs = [
            create_mock_simulation_run("run_1"),
            create_mock_simulation_run("run_2"),
        ]

        result = generate_aggregated_results(runs)

        assert isinstance(result, AggregatedResults)
        assert result.total_runs == 2
        assert len(result.per_chunk_avg_understanding) > 0


# =============================================================================
# Unit Tests - Multi-Run Executor
# =============================================================================


class TestMultiRunExecutor:
    """Tests for aggregation/multi_run.py MultiRunExecutor class."""

    def test_calculate_sample_range_large_class(self):
        """Test sample range calculation for large class."""
        executor = MultiRunExecutor(
            material_file_path="test.pdf",
            teacher_config=TeacherAgentConfig(
                teacher_id="t1",
                name="Test",
                personality_prompt="Test",
                big5_scores={"O": 50, "C": 50, "E": 50, "A": 50, "N": 50},
            ),
            class_name="test_class",
            professor_name="test_prof",
        )

        min_s, max_s = executor._calculate_sample_range(100)

        assert min_s == 50  # 50% of 100
        assert max_s == 100

    def test_calculate_sample_range_small_class(self):
        """Test sample range calculation for small class."""
        executor = MultiRunExecutor(
            material_file_path="test.pdf",
            teacher_config=TeacherAgentConfig(
                teacher_id="t1",
                name="Test",
                personality_prompt="Test",
                big5_scores={"O": 50, "C": 50, "E": 50, "A": 50, "N": 50},
            ),
            class_name="test_class",
            professor_name="test_prof",
        )

        min_s, max_s = executor._calculate_sample_range(8)

        assert min_s == 5  # Minimum is 5
        assert max_s == 8

    def test_calculate_sample_range_minimum_floor(self):
        """Test that minimum is always at least 5."""
        executor = MultiRunExecutor(
            material_file_path="test.pdf",
            teacher_config=TeacherAgentConfig(
                teacher_id="t1",
                name="Test",
                personality_prompt="Test",
                big5_scores={"O": 50, "C": 50, "E": 50, "A": 50, "N": 50},
            ),
            class_name="test_class",
            professor_name="test_prof",
        )

        min_s, max_s = executor._calculate_sample_range(6)

        # 50% of 6 = 3, but minimum is 5
        assert min_s == 5
        assert max_s == 6


# =============================================================================
# Integration Test - Full Pipeline (Manual Run)
# =============================================================================


def manual_integration_test():
    """
    Manual integration test - run this directly if you have DB connection.

    This test requires:
    1. MongoDB connection configured in .env
    2. A valid class with students in the database
    3. A test material file

    To run: python -c "from aggregation.test_aggregation import manual_integration_test; manual_integration_test()"
    """
    import os
    from pathlib import Path

    print("=" * 60)
    print("INTEGRATION TEST - Multi-Run Aggregation")
    print("=" * 60)

    # Check for test material
    test_material = Path("test_data/simple.pdf")
    if not test_material.exists():
        print(f"⚠️  Test material not found: {test_material}")
        print(
            "   Create a test_data/ directory with a simple.pdf file to run this test."
        )
        return

    # Create executor
    executor = MultiRunExecutor(
        material_file_path=str(test_material),
        teacher_config=TeacherAgentConfig(
            teacher_id="integration_test_teacher",
            name="Integration Test Teacher",
            personality_prompt="A patient and thorough teacher for testing.",
            big5_scores={"O": 70, "C": 65, "E": 60, "A": 75, "N": 40},
        ),
        class_name=os.getenv("TEST_CLASS_NAME", "test_class"),
        professor_name=os.getenv("TEST_PROFESSOR_NAME", "test_prof"),
    )

    print(f"Material: {test_material}")
    print(f"Class: {executor.class_name}")
    print(f"Professor: {executor.professor_name}")
    print()

    # Run 3 simulations
    n_runs = 3
    print(f"Running {n_runs} simulation runs...")

    try:
        runs = asyncio.run(executor.run_multiple(n_runs=n_runs))

        print(f"\n✅ Completed {len(runs)}/{n_runs} runs")

        if runs:
            # Analyze results
            from aggregation.gap_detector import detect_gaps
            from aggregation.report_generator import generate_aggregated_results

            gaps = detect_gaps(runs)
            results = generate_aggregated_results(runs)

            print(f"\n📊 Results:")
            print(f"   Total runs: {results.total_runs}")
            print(f"   Gap chunks: {gaps}")
            print(
                f"   Avg understanding per chunk: {results.per_chunk_avg_understanding}"
            )

            # Check student selection variance
            student_sets = [set(r.students_selected) for r in runs]
            print(f"\n👥 Student Selection:")
            for i, ss in enumerate(student_sets):
                print(f"   Run {i+1}: {len(ss)} students")

            # Check if any runs used different student sets
            if len(student_sets) > 1:
                all_same = all(s == student_sets[0] for s in student_sets)
                if all_same:
                    print(
                        "   ⚠️ All runs used identical student sets (may happen with small classes)"
                    )
                else:
                    print("   ✅ Different student subsets used across runs")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()


# =============================================================================
# Run tests with pytest or directly
# =============================================================================


if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    pytest.main([__file__, "-v", "--tb=short"])

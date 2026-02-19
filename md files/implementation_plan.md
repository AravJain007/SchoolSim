# SIMS Teacher - Implementation Plan

**Created:** January 27, 2026
**Approach:** Build on existing infrastructure (Option 1)
**Estimated Completion:** 12 Tasks, logically ordered with dependencies

---

## Executive Summary

This plan builds the remaining 65-70% of SIMS Teacher while fully leveraging the existing 30-35% infrastructure. The existing LLM provider system, student personality pipeline, and database services remain untouched and serve as the foundation.

---

## What We're Keeping (Do Not Modify)

| File/Module                                 | Purpose                                       | Status                    |
| ------------------------------------------- | --------------------------------------------- | ------------------------- |
| `llm_provider/llm_call.py`                  | LLM abstraction for Gemini/Lightning/LMStudio | ✅ Ready                  |
| `llm_provider/creation_prompt.py`           | Biography + character impersonation prompts   | ✅ Ready                  |
| `personality/classroom_service.py`          | Fetches student data from MongoDB             | ✅ Ready                  |
| `personality/create_class_personalities.py` | Creates student agent prompts                 | ✅ Ready                  |
| `pydantic_classes.py`                       | Base Pydantic models                          | ✅ Extend (don't replace) |
| `student_big5_website/`                     | Big5 personality test website                 | ✅ Ready                  |

---

## Task Overview

| Task | Name                       | Depends On | Priority    |
| ---- | -------------------------- | ---------- | ----------- |
| 1    | Extend Pydantic Models     | None       | 🔴 Critical |
| 2    | Material Parser & Chunker  | Task 1     | 🔴 Critical |
| 3    | Teacher Agent              | Task 1     | 🔴 Critical |
| 4    | Student Agent (CIE)        | Task 1     | 🔴 Critical |
| 5    | Principal Agent (KLI)      | Task 1     | 🔴 Critical |
| 6    | Simulation Orchestrator    | Tasks 2-5  | 🔴 Critical |
| 7    | Multi-Run Aggregation      | Task 6     | 🟡 High     |
| 8    | Heatmap & Report Generator | Task 7     | 🟡 High     |
| 9    | FastAPI Backend            | Tasks 6-8  | 🟡 High     |
| 10   | Frontend - Setup & Chat    | Task 9     | 🟢 Medium   |
| 11   | Frontend - Dashboard       | Task 10    | 🟢 Medium   |
| 12   | Docker Deployment          | Tasks 9-11 | 🔵 Low      |

---

## Task 1: Extend Pydantic Models

**Location:** `pydantic_classes.py`
**Action:** ADD new models (do not remove existing ones)

### New Models Required

1. **ChunkDetails**
   - `chunk_id`: str
   - `content`: str
   - `difficulty_index`: Optional[float] (0-100 scale, **populated post-simulation** based on student understanding scores — NOT pre-computed)
   - `page_range`: str (e.g., "Slide 5", "Page 3", or "Paragraph 7")
   - `has_formula`: bool
   - `has_code`: bool

2. **CognitiveState**
   - `fatigue`: int (starts at 0, increases by 5 per chunk)
   - `cognitive_load`: int (increases based on chunk count, +10 per chunk)
   - `understanding`: int (1-5 scale, default 3)

3. **StudentAgentState**
   - `student_id`: str
   - `name`: str
   - `personality_prompt`: str
   - `cognitive_state`: CognitiveState
   - `doubts_asked`: List[str]

4. **TeacherAgentConfig**
   - `teacher_id`: str
   - `name`: str
   - `personality_prompt`: str
   - `big5_scores`: Dict[str, int] (O, C, E, A, N scores)

5. **TeachingOutput**
   - `chunk_id`: str
   - `teaching_transcript`: str
   - `teaching_method_used`: Literal["direct_explanation", "analogy", "example", "question"]

6. **StudentResponse**
   - `student_id`: str
   - `chunk_id`: str
   - `understanding_before`: int
   - `understanding_after`: int
   - `doubt_asked`: Optional[str]
   - `doubt_resolved`: Optional[bool]

7. **PrincipalAnalysis**
   - `chunk_id`: str
   - `alignment_score`: float (0-1)
   - `missing_prerequisites`: List[str]
   - `suggested_methods`: List[str]
   - `notes`: str

8. **SimulationRun**
   - `run_id`: str
   - `timestamp`: datetime
   - `teacher_config`: TeacherAgentConfig
   - `students_selected`: List[str]
   - `chunk_results`: List of per-chunk data
   - `principal_summary`: PrincipalAnalysis

9. **AggregatedResults**
   - `total_runs`: int
   - `per_chunk_avg_understanding`: Dict[str, float]
   - `gap_chunks`: List[str] (chunks with >40% failure rate)
   - `common_doubts`: Dict[str, List[str]]
   - `principal_notes`: List[str]

### Implementation Notes

- Use Pydantic's `Field()` with descriptions for documentation
- Add validators where needed (e.g., understanding must be 1-5)
- These models will be used throughout the system

---

## Task 2: Material Parser (Structural Chunking)

**Location:** New module `material_parser/`

### Design Philosophy

**We do NOT pre-compute difficulty/density via NLP.** The simulation will empirically discover which chunks are difficult based on student understanding scores. This avoids redundant gatekeeping — the "difficulty_index" is populated **post-simulation** in the aggregation phase.

### Chunking Strategy (Structural, Not Cognitive)

- **PPT/PPTX:** 1 slide = 1 chunk
- **PDF:** 1 page = 1 chunk
- **DOC/DOCX:** 1 paragraph = 1 chunk

This keeps chunk boundaries predictable and makes it easy to annotate the original file with heatmap overlays later.

### Files to Create

1. **`material_parser/__init__.py`**
   - Export: `parse_and_chunk`

2. **`material_parser/parser.py`**
   - Function: `parse_and_chunk(file_path: str) -> List[ChunkDetails]`
   - Support file types: PDF, PPT/PPTX, DOC/DOCX
   - Use libraries:
     - PDF: PyMuPDF (`fitz`)
     - PPT: `python-pptx`
     - DOC: `python-docx`
   - Returns list of `ChunkDetails` with:
     - `chunk_id`: auto-generated (e.g., "chunk_1", "chunk_2")
     - `content`: extracted text
     - `page_range`: "Slide 3", "Page 5", or "Paragraph 7" (for annotation later)
     - `has_formula`: detected via regex (useful metadata)
     - `has_code`: detected via regex (useful metadata)
     - `difficulty_index`: **None** (populated post-simulation)

### Dependencies to Install

- `pymupdf` (PyMuPDF)
- `python-pptx`
- `python-docx`

> **Note:** `textstat` is no longer needed since we're not pre-computing readability scores.

---

## Task 3: Teacher Agent

**Location:** New files in `simulation/` and `llm_provider/`

### Files to Create

1. **`llm_provider/teacher_prompt.py`**
   - `TEACHER_SYSTEM_PROMPT`: Template that takes Big5 scores and maps to teaching behavior
   - Reference the behavior mapping table from FinalPlanAgents.md:
     - Low Openness → sticks to textbook
     - High Openness → creative analogies
     - Low Conscientiousness → summarizes quickly
     - High Conscientiousness → covers every detail
     - etc.
   - `TEACH_CHUNK_PROMPT`: Template for teaching a specific chunk
   - `RESPOND_TO_DOUBT_PROMPT`: Template for answering student doubts

2. **`simulation/teacher_agent.py`**
   - Class: `TeacherAgent`
   - Constructor takes `TeacherAgentConfig`
   - Method: `teach_chunk(chunk: ChunkDetails) -> TeachingOutput`
     - Uses LLMCall to generate teaching transcript
     - Returns structured output with method used
   - Method: `respond_to_doubt(doubt: str, chunk: ChunkDetails) -> str`
     - Uses LLMCall to generate response
     - Teaching style influenced by personality

3. **`personality/create_teacher_personality.py`**
   - Reuse existing Big5 infrastructure
   - Function: `create_teacher_prompt(teacher_big5_data: dict) -> TeacherAgentConfig`
   - Map Big5 scores to teaching style descriptors
   - Generate system prompt for teacher agent

### Key Design Decisions

- Teacher personality affects: pacing, explanation depth, patience with doubts, use of examples
- Teaching method selection should be probabilistic based on personality
- Store teaching transcripts for Principal analysis

---

## Task 4: Student Agent with CIE Architecture

**Location:** Modify/extend `simulation/`

### Files to Create

1. **`llm_provider/student_prompt.py`**
   - `STUDENT_UNDERSTANDING_PROMPT`: After hearing chunk explanation, rate understanding (1-5)
   - `STUDENT_DOUBT_PROMPT`: Given low understanding, generate a doubt
   - `STUDENT_RERATING_PROMPT`: After teacher responds to doubt, re-rate understanding

2. **`simulation/cognitive_state.py`**
   - Class: `CognitiveStateManager`
   - Manages fatigue, cognitive_load, understanding for each student
   - Method: `update_after_chunk()`:
     - `fatigue += 5`
     - `cognitive_load += 10` _(flat increment — difficulty_index is not available during simulation, it's computed post-aggregation in Task 7)_
   - Method: `should_ask_doubt(student: StudentAgentState) -> bool`:
     - If understanding <= 2 AND fatigue < 80: return True
     - If understanding == 5 AND openness > 70: maybe curiosity question
     - Else: return False

3. **`simulation/student_agent.py`**
   - Class: `StudentAgent`
   - Constructor takes `StudentDetails` (from existing code), initializes `CognitiveState`
   - Method: `rate_understanding(chunk: ChunkDetails, teaching_transcript: str) -> int`
     - Uses LLMCall to get 1-5 rating
   - Method: `generate_doubt(chunk: ChunkDetails) -> str`
     - Uses personality + cognitive state to generate authentic doubt
   - Method: `rerate_after_response(response: str) -> int`
     - Check if understanding improved (IRF R+ metric)

4. **`simulation/doubt_selector.py`**
   - Function: `select_doubt_askers(students: List[StudentAgent]) -> List[StudentAgent]`
   - Filter by understanding <= 2 AND fatigue < 80
   - Randomly pick 2-5 students from filtered list

### Integration with Existing Code

- Use `personality/create_class_personalities.py` to create student prompts
- Use `personality/classroom_service.py` to fetch student data
- Extend, don't replace, existing personality infrastructure

---

## Task 5: Principal Agent with KLI Framework

**Location:** New files in `simulation/` and `llm_provider/`

### Files to Create

1. **`llm_provider/principal_prompt.py`**
   - `PRINCIPAL_SYSTEM_PROMPT`: Expert pedagogical observer using KLI Framework
   - `PRINCIPAL_ANALYSIS_PROMPT`: Template for analyzing a chunk's teaching
   - Include KLI Framework details:
     - **K (Knowledge)**: Are prerequisites covered? Is knowledge structure sound?
     - **L (Learning)**: Is learning phase appropriate? (Exposure → Practice → Application)
     - **I (Instruction)**: Does teaching method match content type?
   - Include Bloom's Taxonomy levels for content classification

2. **`simulation/principal_agent.py`**
   - Class: `PrincipalAgent`
   - Constructor: No personality needed, uses fixed pedagogical expertise
   - Method: `analyze_chunk(chunk: ChunkDetails, teaching_transcript: str, student_responses: List[StudentResponse]) -> PrincipalAnalysis`
     - Checks KLI alignment
     - Outputs alignment_score (0-1)
     - Lists missing prerequisites
     - Suggests alternative methods
   - Method: `generate_summary(all_analyses: List[PrincipalAnalysis]) -> str`
     - Overall alignment score
     - Critical misalignments
     - Bloom's progression assessment

### KLI Alignment Scoring Logic

- Content type detection: lecture, coding exercise, case study, etc.
- Method match: direct explanation for concepts, demo for procedures, practice for skills
- Score: 1.0 if perfect match, 0.3-0.7 for partial, 0.0-0.3 for mismatch

---

## Task 6: Simulation Orchestrator

**Location:** `simulation/orchestrator.py`

### What It Does

This is the main engine that runs a single simulation from start to finish.

### Class: `SimulationOrchestrator`

**Constructor:**

- Takes: material file path, teacher config, class name, professor name

**Method: `run_single_simulation() -> SimulationRun`**

Implements this loop (from FinalPlanAgents.md Section 4.1):

```
FOR each chunk in material:
    1. Teacher Agent teaches chunk
       -> Output: teaching_transcript, method_used

    2. ALL Student Agents rate understanding (1-5)
       -> Output: understanding_score per student

    3. SELECT students with understanding <= 2
       -> Filter by fatigue < 80
       -> Randomly pick 1-2 to ask doubts

    4. Teacher Agent responds to doubt
       -> Output: response_transcript

    5. Asker re-rates understanding (IRF Check)
       -> IF understanding_after > understanding_before: R+ = 1
       -> ELSE: R+ = 0

    6. Principal Agent analyzes chunk
       -> Output: alignment_score, notes

    7. UPDATE all student cognitive states
       -> fatigue += 5
       -> cognitive_load += 10
END FOR
```

**Key Responsibilities:**

- Initialize all agents (teacher, students, principal)
- Fetch students from MongoDB using existing `ClassroomService`
- Parse and chunk material using Task 2 components
- Orchestrate the teaching-doubt-analysis cycle
- Collect all outputs into `SimulationRun` object
- Handle errors gracefully (LLM failures, timeouts)

### Integration Points

- Uses `ClassroomService` from existing code
- Uses `LLMCall` from existing code
- Uses all new agents from Tasks 3-5
- Uses chunker from Task 2

---

## Task 7: Multi-Run Aggregation & Difficulty Index Calculation

**Location:** New module `aggregation/`

### Key Concept: Post-Simulation Difficulty Index

The `difficulty_index` for each chunk is **computed here**, after all simulation runs complete. It is NOT pre-computed via NLP during parsing.

**Formula:**

```python
difficulty_index = (1 - avg_understanding / 5) * 100
# Where avg_understanding is the mean across all students and all runs
# Low understanding (1-2) → High difficulty_index (60-80)
# High understanding (4-5) → Low difficulty_index (0-20)
```

This approach ensures the difficulty score reflects **actual student struggle**, not heuristic predictions.

### Key Concept: Random Student Subset Selection

Each simulation run uses a **randomly selected subset** of students from the full class, not the entire class every time. This provides:

1. **Statistical Variance:** Different student combinations expose different failure modes
2. **Realistic Sampling:** Real classes rarely have 100% attendance
3. **Faster Runs:** Fewer students per run = faster LLM processing

**Subset Selection Rules:**

```python
def calculate_sample_range(total_students: int) -> tuple[int, int]:
    """
    Returns (min_sample, max_sample) for random selection.
    Sample between 50-100% of class size.
    """
    min_sample = max(5, int(total_students * 0.5))  # At least 5 students
    max_sample = total_students
    return (min_sample, max_sample)

# Example: Class of 100 students → sample 50-100 students per run
# Example: Class of 20 students  → sample 10-20 students per run
# Example: Class of 8 students   → sample 5-8 students per run (minimum 5)
```

**Selection Logic in `multi_run.py`:**

```python
import random

def select_students_for_run(all_students: List[StudentDetails],
                            total_students: int) -> List[StudentDetails]:
    min_sample, max_sample = calculate_sample_range(total_students)
    sample_size = random.randint(min_sample, max_sample)
    return random.sample(all_students, sample_size)
```

**Important:** The `students_selected` field in `SimulationRun` must record which student IDs were used for that run (already defined in Task 1 Pydantic models).

### Files to Create

1. **`aggregation/__init__.py`**

2. **`aggregation/multi_run.py`**
   - Class: `MultiRunExecutor`
   - Method: `run_multiple(n_runs: int) -> List[SimulationRun]`
     - For each run: randomly sample subset of students
     - Execute orchestrator
     - Store all outputs

3. **`aggregation/analyzer.py`**
   - Function: `calculate_irf_plus(student_responses: List[StudentResponse]) -> float`
     - Count how many doubts led to understanding improvement
     - R+ = (improvements / total_doubts)
   - Function: `find_common_doubts(all_runs: List[SimulationRun]) -> Dict[str, List[str]]`
     - Group doubts by chunk_id
     - Find recurring themes

4. **`aggregation/difficulty_calculator.py`** _(NEW)_
   - Function: `compute_difficulty_index(chunk_id: str, all_runs: List[SimulationRun]) -> float`
     - Collect all understanding scores for this chunk across runs
     - Calculate: `(1 - mean(scores) / 5) * 100`
     - Returns 0-100 score (higher = more difficult)
   - Function: `populate_chunk_difficulty(chunks: List[ChunkDetails], all_runs: List[SimulationRun]) -> List[ChunkDetails]`
     - Updates each chunk's `difficulty_index` field
     - Called after aggregation is complete

5. **`aggregation/gap_detector.py`**
   - Function: `detect_gaps(all_runs: List[SimulationRun], threshold: float = 0.4) -> List[str]`
     - For each chunk: calculate failure rate (avg_understanding < 3)
     - If failure_rate >= threshold across runs: FLAG as gap
     - Return list of gap chunk_ids

6. **`aggregation/report_generator.py`**
   - Function: `generate_gap_report(gaps: List[str], runs: List[SimulationRun]) -> dict`
     - Per gap: topic, avg_understanding, **difficulty_index**, failure_rate, common_doubts, principal_notes
   - Function: `generate_principal_summary(runs: List[SimulationRun]) -> dict`
     - Overall alignment, critical misalignments, Bloom's progression

### Output Format

Reference FinalPlanAgents.md Sections 5.2 and 5.3 for exact JSON structure. Note that `difficulty_index` replaces the old `semantic_density` field.

---

## Task 8: Heatmap & Report Generator

**Location:** New module `output/`

### Annotation Granularity by File Type

Different file types have different chunking strategies, which affects annotation granularity:

| File Type | Chunk Unit | Heatmap Method | Annotation Method |
|-----------|------------|----------------|-------------------|
| **PDF** | 1 page = 1 chunk | Full-page semi-transparent color overlay | Footer text box at page bottom |
| **PPT/PPTX** | 1 slide = 1 chunk | Full-slide semi-transparent rectangle | Footer text box at slide bottom |
| **DOC/DOCX** | 1 paragraph = 1 chunk | **Paragraph-level text highlighting** | **Word comment on specific paragraph** |

> **Note:** DOCX files have **finer granularity** than PDF/PPT. Each paragraph is individually highlighted based on its understanding score, allowing teachers to see exactly which paragraphs caused confusion.

### Files to Create

1. **`output/__init__.py`**

2. **`output/heatmap_generator.py`**
   - Function: `generate_heatmap(original_file: str, aggregated_results: AggregatedResults) -> str`
   - Logic:
     - For each chunk: determine color based on avg_understanding
       - < 2: RED (critical confusion)
       - < 3: ORANGE/YELLOW (caution)
       - >= 3: GREEN (clear)
     - **PDF**: Full-page overlay using PyMuPDF's `draw_rect` with `fill_opacity`
     - **PPT**: Full-slide rectangle shape moved to back layer
     - **DOCX**: Per-paragraph text run highlighting using `WD_COLOR_INDEX`
   - Return path to annotated file

3. **`output/annotation_writer.py`**
   - Function: `add_footer_notes(file_path: str, chunk: str, annotation: str) -> None`
   - **PDF/PPT**: Adds text box at bottom of relevant page/slide
   - **DOCX**: Adds Word comment anchored to the specific paragraph
   - Format: "⚠️ GAP: X% failed. Note: [principal_notes]"

4. **`output/report_exporter.py`**
   - Function: `export_json_report(results: AggregatedResults, path: str) -> None`
   - Function: `export_pdf_report(results: AggregatedResults, path: str) -> None`
   - Creates downloadable summary document

### Dependencies to Install

- `reportlab` (for PDF report generation)
- `pymupdf` (for PDF heatmap overlays)
- `python-pptx` (for PPT heatmap and annotations)
- `python-docx` (for DOCX highlighting and comments)

---

## Task 9: FastAPI Backend

**Location:** New module `api/`

### Files to Create

1. **`api/__init__.py`**

2. **`api/main.py`**
   - FastAPI app initialization
   - CORS middleware
   - Include routers

3. **`api/routes/simulation.py`**
   - `POST /simulation/start` - Start new simulation
     - Body: class_name, teacher_id, material_file, num_runs
     - Returns: simulation_id
   - `GET /simulation/{id}/status` - Check simulation status
   - `GET /simulation/{id}/stream` - SSE endpoint for real-time updates
   - `GET /simulation/{id}/results` - Get final aggregated results

4. **`api/routes/material.py`**
   - `POST /material/upload` - Upload course material file
   - `GET /material/{id}/chunks` - Get parsed chunks for preview

5. **`api/routes/teacher.py`**
   - `GET /teacher/{id}/classes` - List classes teacher can select
   - `GET /teacher/{id}/simulations` - List past simulations
   - `GET /teacher/{id}/dashboard` - Dashboard summary data

6. **`api/routes/heatmap.py`**
   - `GET /heatmap/{simulation_id}` - Download annotated PDF/PPT
   - `GET /report/{simulation_id}` - Download JSON/PDF report

7. **`api/dependencies.py`**
   - Database connections
   - Authentication (if needed)

### Background Tasks

- Simulations run as background tasks (FastAPI BackgroundTasks or Celery)
- Real-time updates via Server-Sent Events (SSE)

---

## Task 10: Frontend - Setup & Chat Interface

**Location:** New `frontend/` directory

### Technology

- React (as specified in FinalPlanAgents.md)
- Vite for build tooling
- CSS for styling (per frontend_code_rules.md)

### Pages to Create

1. **`/setup`** - Simulation Setup Page
   - Class name dropdown (fetched from API)
   - Material upload (drag & drop)
   - Number of runs slider (1-10)
   - Start simulation button
   - Shows uploaded material preview (chunks)

2. **`/simulation/:id`** - Live Chat Interface
   - Real-time message stream (SSE)
   - Messages styled by speaker:
     - Teacher: blue bubble
     - Student: green bubble
     - Principal (notes): gray/italic
   - Progress indicator (current chunk / total chunks)
   - Stop simulation button

3. **`/results/:id`** - Results Page
   - Gap summary with color indicators
   - Heatmap viewer (embedded PDF/image)
   - Download buttons (annotated file, JSON report)
   - Common doubts list per topic
   - Principal's overall notes

### Components to Create

- `ChatMessage.jsx` - Single message bubble
- `ChunkProgress.jsx` - Progress indicator
- `GapCard.jsx` - Displays single gap finding
- `HeatmapViewer.jsx` - PDF/image viewer with annotations

---

## Task 11: Frontend - Teacher Dashboard

**Location:** `frontend/` (same React app)

### Pages to Create

1. **`/dashboard`** - Overview
   - List of past simulations with status
   - Quick stats: total runs, avg effectiveness, common gaps
   - Recent activity feed

2. **`/simulation/:id/detail`** - Detailed View
   - Full transcript viewer
   - Per-chunk analysis accordion
   - Student-by-student breakdown
   - Principal's analysis panel

3. **`/analytics`** - Cross-Simulation Analytics
   - Trends across multiple simulations
   - Most common gaps in teacher's materials
   - Improvement tracking over time

### Components to Create

- `SimulationCard.jsx` - Summary card for simulation list
- `ChunkAnalysis.jsx` - Expandable chunk details
- `EffectivenessChart.jsx` - IRF R+ metric visualization
- `StudentGrid.jsx` - Grid of student understanding scores

---

## Task 12: Docker Deployment

**Location:** Root directory

### Files to Create

1. **`docker-compose.yml`**
   - Services: api, frontend, mongodb
   - Volumes for persistent data
   - Network configuration

2. **`Dockerfile.api`**
   - Python 3.11+ base
   - Install requirements
   - Copy backend code
   - Expose port 8000

3. **`Dockerfile.frontend`**
   - Node.js base
   - Build React app
   - Serve with nginx

4. **`.env.example`**
   - Template for all required environment variables
   - LLM API keys, MongoDB URI, etc.

5. **`README.md` update**
   - Docker quickstart instructions
   - Environment setup guide

---

## Dependency Graph

```
Task 1 (Models)
    ├── Task 2 (Parser/Chunker)
    ├── Task 3 (Teacher Agent)
    ├── Task 4 (Student Agent)
    └── Task 5 (Principal Agent)
            │
            └── Task 6 (Orchestrator)
                    │
                    └── Task 7 (Aggregation)
                            │
                            └── Task 8 (Heatmap/Reports)
                                    │
                                    └── Task 9 (FastAPI)
                                            │
                                            ├── Task 10 (Frontend Setup/Chat)
                                            │
                                            └── Task 11 (Frontend Dashboard)
                                                    │
                                                    └── Task 12 (Docker)
```

---

## Estimated Effort Per Task

| Task                     | Complexity | Estimated Time |
| ------------------------ | ---------- | -------------- |
| 1. Pydantic Models       | Low        | 1-2 hours      |
| 2. Material Parser       | Medium     | 3-4 hours      |
| 3. Teacher Agent         | Medium     | 3-4 hours      |
| 4. Student Agent (CIE)   | High       | 4-5 hours      |
| 5. Principal Agent (KLI) | High       | 4-5 hours      |
| 6. Orchestrator          | High       | 5-6 hours      |
| 7. Aggregation           | Medium     | 3-4 hours      |
| 8. Heatmap/Reports       | Medium     | 3-4 hours      |
| 9. FastAPI Backend       | Medium     | 4-5 hours      |
| 10. Frontend Setup/Chat  | Medium     | 5-6 hours      |
| 11. Frontend Dashboard   | Medium     | 4-5 hours      |
| 12. Docker               | Low        | 2-3 hours      |

**Total Estimated: 42-53 hours of implementation work**

---

## Testing Strategy

### Unit Tests

- Each agent should have tests with mocked LLM responses
- Chunker should be tested with sample documents
- Aggregation functions tested with synthetic data

### Integration Tests

- Full orchestrator run with small material
- API endpoints with test data

### End-to-End Tests

- Browser automation for frontend flows
- Full simulation with real LLM calls (use cheap model)

---

## Notes for Implementation

1. **Start with Task 1** - All other tasks depend on having the models defined
2. **Tasks 2-5 can be parallelized** once Task 1 is done
3. **Task 6 is the integration point** - ensure Tasks 2-5 are solid before starting
4. **Test each agent independently** before integrating into orchestrator
5. **Use existing `LLMCall` pattern** for all LLM interactions
6. **Keep prompts in separate files** for easy iteration
7. **Log everything** during development for debugging

---

## Success Criteria

The system is complete when:

- [ ] Teacher can upload material and select class
- [ ] Simulation runs with personality-driven agents
- [ ] CIE states update correctly throughout simulation
- [ ] Principal analyzes using KLI framework
- [ ] Multiple runs produce aggregated insights
- [ ] Gaps are detected with 40% threshold
- [ ] Heatmap overlays on original material
- [ ] Real-time chat shows simulation progress
- [ ] Dashboard displays historical simulations
- [ ] System deploys via Docker

---

_This plan should be followed sequentially, with each task building on previous ones. Do not skip tasks or attempt parallel development of dependent tasks._

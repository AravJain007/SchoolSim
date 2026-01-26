# Code Todo - File Structure

## Backend (Python)

### Course Material Processing

| File | Description |
|------|-------------|
| `material_parser/__init__.py` | Module init |
| `material_parser/parser.py` | Extracts text from PDF, PPT, DOC files |
| `material_parser/chunker.py` | **Semantic Density Chunking** - Splits content based on cognitive load (new terminology count, formula presence, Flesch-Kincaid difficulty) rather than just paragraphs |
| `material_parser/density_calculator.py` | Calculates semantic density score per paragraph (new terms +5, formulas +10, abstract concepts +8) |

### Agent Prompts

| File | Description |
|------|-------------|
| `llm_provider/teacher_prompt.py` | System prompt for teacher agent - integrates teacher's Big5 personality to determine teaching style, pacing, doubt handling |
| `llm_provider/student_prompt.py` | System prompt for student agent - includes CIE cognitive state variables (fatigue, cognitive_load, understanding) |
| `llm_provider/principal_prompt.py` | System prompt for principal agent - **KLI Framework** (Knowledge structure, Learning process, Instruction alignment) + Bloom's taxonomy |


### Simulation Engine

| File | Description |
|------|-------------|
| `simulation/__init__.py` | Module init (exists) |
| `simulation/orchestrator.py` | Main simulation loop - runs multiple simulations, handles chunk-by-chunk teaching cycle |
| `simulation/teacher_agent.py` | Teacher agent class - uses teacher's Big5 to shape teaching style, handles material delivery and doubt responses |
| `simulation/student_agent.py` | Student agent class - manages CIE cognitive states (fatigue, cognitive_load), outputs understanding score (1-5) |
| `simulation/principal_agent.py` | Principal agent class - **KLI alignment check** per chunk, observes session, generates suggestions |
| `simulation/doubt_selector.py` | Selects students with understanding <= 2 AND fatigue < 80 to ask doubts |
| `simulation/cognitive_state.py` | Manages CIE state updates: fatigue += 5 per chunk, cognitive_load += density * 0.2 |
| `simulation/session_state.py` | Maintains state of a single simulation session (transcript, notes, current topic) |

### Aggregation

| File | Description |
|------|-------------|
| `aggregation/__init__.py` | Module init |
| `aggregation/multi_run.py` | Runs simulation multiple times with different random seeds |
| `aggregation/analyzer.py` | Finds common patterns across runs, calculates **IRF R+ metrics** (understanding improvement per doubt) |
| `aggregation/gap_detector.py` | **Gap Detection** - flags chunks where avg_understanding < 3 across 40%+ runs |
| `aggregation/report_generator.py` | Creates final structured report for teacher |


### API Layer

| File | Description |
|------|-------------|
| `api/__init__.py` | Module init |
| `api/main.py` | FastAPI app entry point |
| `api/routes/simulation.py` | Endpoints for starting/monitoring simulations |

| `api/routes/teacher.py` | Endpoints for teacher dashboard data |
| `api/routes/material.py` | Endpoints for material upload and processing |

### Database

| File | Description |
|------|-------------|
| `db/__init__.py` | Module init |
| `db/models.py` | Pydantic models for simulation sessions, reports |
| `db/service.py` | MongoDB operations for all new collections |

---

### Teacher Personality

| File | Description |
|------|-------------|
| `personality/create_teacher_personality.py` | Creates teacher agent prompt from teacher's Big5 results (reuses existing Big5 infrastructure) |

---

## Frontend (React)

### Simulation Monitor

| File | Description |
|------|-------------|
| `frontend/simulation/src/App.jsx` | Main app with routing |
| `frontend/simulation/src/pages/Setup.jsx` | Teacher setup screen - class name selection, material upload, number of runs input |
| `frontend/simulation/src/pages/SimulationChat.jsx` | Chat interface showing simulation as it runs in real-time |
| `frontend/simulation/src/pages/Results.jsx` | Displays aggregated results from all simulation runs |
| `frontend/simulation/src/components/ChatMessage.jsx` | Single message in simulation stream (teacher/student/principal) |


### Teacher Dashboard

| File | Description |
|------|-------------|
| `frontend/dashboard/src/App.jsx` | Main dashboard app |
| `frontend/dashboard/src/pages/Overview.jsx` | Summary of all simulations |
| `frontend/dashboard/src/pages/SimulationDetail.jsx` | Detailed view of one simulation run |

| `frontend/dashboard/src/pages/StudentView.jsx` | Individual student performance |
| `frontend/dashboard/src/components/Chart.jsx` | Reusable chart component |
| `frontend/dashboard/src/components/InsightCard.jsx` | Displays single insight/suggestion |

---

## Configuration

| File | Description |
|------|-------------|
| `.env.example` | Template for environment variables |
| `docker-compose.yml` | Container setup for API, frontend, MongoDB |
| `Dockerfile.api` | Docker image for backend |
| `Dockerfile.frontend` | Docker image for frontend apps |

---

### Heatmap Generation

| File | Description |
|------|-------------|
| `output/__init__.py` | Module init |
| `output/heatmap_generator.py` | Overlays color (Red/Orange/Green) on original PDF/PPT based on avg_understanding per chunk |
| `output/annotation_writer.py` | Adds footer remarks to confused slides (gap report + principal notes) |

---

## Order of Implementation

1. Material parser + **Semantic Density Chunker**
2. Teacher personality prompt (reuse Big5 system)
3. Teacher agent + prompt
4. **Student agent + CIE cognitive state management**
5. **Principal agent + KLI Framework prompt**
6. Simulation orchestrator (with multi-run support + **1-5 scale collection**)
7. API layer (simulation endpoints)
8. Simulation frontend (setup + chat interface)
9. **Aggregation system + IRF R+ metrics + Gap Detection**
10. **Heatmap Generator + Annotation Writer**
11. Teacher dashboard
12. Docker deployment

# Code Todo - File Structure

## Backend (Python)

### Course Material Processing

| File | Description |
|------|-------------|
| `material_parser/__init__.py` | Module init |
| `material_parser/parser.py` | Extracts text from PDF, PPT, DOC files and structures into teachable chunks |
| `material_parser/chunker.py` | Splits parsed content into logical teaching segments with topic labels |

### Agent Prompts

| File | Description |
|------|-------------|
| `llm_provider/teacher_prompt.py` | System prompt for teacher agent - integrates teacher's Big5 personality to determine teaching style, pacing, doubt handling |
| `llm_provider/principal_prompt.py` | System prompt for principal agent - pedagogical observation, Bloom's taxonomy awareness, improvement suggestions |
| `llm_provider/quiz_prompt.py` | System prompt for quiz generation - creates holistic questions covering all syllabus concepts |

### Simulation Engine

| File | Description |
|------|-------------|
| `simulation/__init__.py` | Module init (exists) |
| `simulation/orchestrator.py` | Main simulation loop - runs multiple simulations based on teacher-specified count, random student selection each run |
| `simulation/teacher_agent.py` | Teacher agent class - uses teacher's Big5 to shape teaching style, handles material delivery and doubt responses |
| `simulation/principal_agent.py` | Principal agent class - observes session, maintains notes, generates final suggestions |
| `simulation/doubt_selector.py` | Probabilistic selection of which students ask doubts based on personality traits |
| `simulation/session_state.py` | Maintains state of a single simulation session (transcript, notes, current topic) |

### Aggregation

| File | Description |
|------|-------------|
| `aggregation/__init__.py` | Module init |
| `aggregation/multi_run.py` | Runs simulation multiple times with different random seeds |
| `aggregation/analyzer.py` | Finds common patterns across simulation runs (frequent doubts, problematic topics) |
| `aggregation/report_generator.py` | Creates final structured report for teacher |

### Quiz System

| File | Description |
|------|-------------|
| `quiz/__init__.py` | Module init |
| `quiz/question_generator.py` | Generates unified quiz from syllabus - covers all key concepts holistically, same for all students |
| `quiz/grader.py` | Evaluates student responses, generates individual analysis |
| `quiz/class_analyzer.py` | Aggregates all student responses into class-wide insights, identifies common weak areas |

### API Layer

| File | Description |
|------|-------------|
| `api/__init__.py` | Module init |
| `api/main.py` | FastAPI app entry point |
| `api/routes/simulation.py` | Endpoints for starting/monitoring simulations |
| `api/routes/quiz.py` | Endpoints for quiz creation, submission, results |
| `api/routes/teacher.py` | Endpoints for teacher dashboard data |
| `api/routes/material.py` | Endpoints for material upload and processing |

### Database

| File | Description |
|------|-------------|
| `db/__init__.py` | Module init |
| `db/models.py` | Pydantic models for simulation sessions, quiz results, reports |
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

### Quiz Interface (Student)

| File | Description |
|------|-------------|
| `frontend/quiz/src/App.jsx` | Main quiz app |
| `frontend/quiz/src/pages/Login.jsx` | Student login with college ID |
| `frontend/quiz/src/pages/Quiz.jsx` | Quiz taking interface |
| `frontend/quiz/src/pages/Results.jsx` | Individual results and analysis |
| `frontend/quiz/src/components/Question.jsx` | Single question component |

### Teacher Dashboard

| File | Description |
|------|-------------|
| `frontend/dashboard/src/App.jsx` | Main dashboard app |
| `frontend/dashboard/src/pages/Overview.jsx` | Summary of all simulations and quizzes |
| `frontend/dashboard/src/pages/SimulationDetail.jsx` | Detailed view of one simulation run |
| `frontend/dashboard/src/pages/QuizAnalysis.jsx` | Class-wide quiz analysis |
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

## Order of Implementation

1. Material parser
2. Teacher personality prompt (reuse Big5 system)
3. Teacher agent + prompt
4. Principal agent + prompt
5. Simulation orchestrator (with multi-run support)
6. API layer (simulation endpoints)
7. Simulation frontend (setup + chat interface)
8. Quiz generator (unified quiz from syllabus)
9. Quiz API endpoints
10. Quiz frontend
11. Aggregation system
12. Teacher dashboard
13. Docker deployment

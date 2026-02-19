# FastAPI Backend

This module provides a REST API for the Simulation Teacher system.

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the API

Start the development server:

```bash
python -m api.main
```

Or using uvicorn directly:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Simulation

- `POST /simulation/start` - Start new simulation
- `GET /simulation/{id}/status` - Check simulation status
- `GET /simulation/{id}/stream` - SSE endpoint for real-time updates
- `GET /simulation/{id}/results` - Get final aggregated results

### Material

- `POST /material/upload` - Upload course material file
- `GET /material/{id}/chunks` - Get parsed chunks for preview

### Teacher

- `GET /teacher/{id}/classes` - List classes teacher can select
- `GET /teacher/{id}/simulations` - List past simulations
- `GET /teacher/{id}/dashboard` - Dashboard summary data

### Heatmap & Reports

- `GET /heatmap/{simulation_id}` - Download annotated PDF/PPT
- `GET /report/{simulation_id}?format=json|pdf` - Download JSON/PDF report

## Example Usage

### Start a Simulation

```bash
curl -X POST "http://localhost:8000/simulation/start" \
  -H "Content-Type: application/json" \
  -d '{
    "class_name": "CS101",
    "teacher_id": "teacher_001",
    "teacher_name": "Dr. Smith",
    "teacher_personality": "High openness, moderate extraversion...",
    "teacher_big5": {"O": 85, "C": 70, "E": 60, "A": 75, "N": 40},
    "material_file_path": "/path/to/material.pdf",
    "professor_name": "Dr. Smith",
    "num_runs": 5,
    "model_provider": "lightning",
    "model_name": "lightning-ai/gpt-oss-20b"
  }'
```

### Check Status

```bash
curl "http://localhost:8000/simulation/{simulation_id}/status"
```

### Get Results

```bash
curl "http://localhost:8000/simulation/{simulation_id}/results"
```

## Architecture

The API uses:
- **FastAPI** for the web framework
- **BackgroundTasks** for running simulations asynchronously
- **Server-Sent Events (SSE)** for real-time progress updates
- **In-memory storage** for simulation state (can be replaced with Redis/DB)

## Production Considerations

For production deployment:
1. Replace in-memory storage with Redis or a database
2. Use Celery for distributed task processing
3. Add authentication and authorization
4. Configure proper CORS origins
5. Add rate limiting
6. Set up proper logging and monitoring
7. Use a production ASGI server (e.g., Gunicorn with Uvicorn workers)

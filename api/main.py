"""
FastAPI Main Application
Entry point for the Simulation Teacher API.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path to allow imports from root-level modules
# This enables imports like: from material_parser.parser import parse_document
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

load_dotenv(parent_dir / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import dashboard, heatmap, material, simulation, student_big5, teacher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Simulation Teacher API")
    yield
    # Shutdown
    logger.info("Shutting down Simulation Teacher API")


# Create FastAPI app
app = FastAPI(
    title="Simulation Teacher API",
    description="API for running classroom teaching simulations with AI agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Include routers
app.include_router(simulation.router)
app.include_router(material.router)
app.include_router(teacher.router)
app.include_router(heatmap.router)
app.include_router(student_big5.router)
app.include_router(dashboard.router)


@app.get("/")
async def root():
    """
    Root endpoint - API health check.
    """
    return {
        "message": "Simulation Teacher API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

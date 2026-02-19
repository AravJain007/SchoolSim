"""
API Dependencies
Provides shared dependencies for FastAPI routes.
"""

import uuid
from typing import Dict

# In-memory storage for simulation states
# In production, this could be Redis or a database
simulation_store: Dict[str, dict] = {}


def get_simulation_store() -> Dict[str, dict]:
    """Get the simulation store."""
    return simulation_store


def generate_simulation_id() -> str:
    """Generate a unique simulation ID."""
    return str(uuid.uuid4())

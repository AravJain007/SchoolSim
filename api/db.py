"""
Shared MongoDB helpers for the API.

Provides accessors for all collections used by the application.
Connection details are read from the MONGO_SERVER environment variable.
"""

import os
from typing import Optional

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

MONGO_URI = os.getenv("MONGO_SERVER")
DB_NAME = "b5"


def get_db() -> Optional[Database]:
    """Return the b5 database, or None if MONGO_SERVER is not set."""
    if not MONGO_URI:
        return None
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME]


def get_simulations_collection() -> Optional[Collection]:
    """
    Return the simulations collection, creating indexes on first access.

    Indexes:
    - simulation_id (unique) -- primary lookup key
    - teacher_id             -- per-teacher queries
    """
    db = get_db()
    if db is None:
        return None
    col = db["simulations"]
    # create_index is idempotent; safe to call on every startup
    col.create_index([("simulation_id", ASCENDING)], unique=True, background=True)
    col.create_index([("teacher_id", ASCENDING)], background=True)
    return col


def get_teachers_collection() -> Optional[Collection]:
    """Return the teachers collection."""
    db = get_db()
    if db is None:
        return None
    return db["teachers"]


def get_results_collection() -> Optional[Collection]:
    """Return the Big5 results collection."""
    db = get_db()
    if db is None:
        return None
    return db["results"]


def get_chat_history_collection() -> Optional[Collection]:
    """
    Return the chat_history collection, creating indexes on first access.

    Each document holds all live-chat messages for one simulation run,
    keeping the simulations collection lean.

    Indexes:
    - simulation_id (unique) -- primary lookup key
    """
    db = get_db()
    if db is None:
        return None
    col = db["chat_history"]
    col.create_index([("simulation_id", ASCENDING)], unique=True, background=True)
    return col

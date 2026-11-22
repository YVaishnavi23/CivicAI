"""SQLite persistence for CivicFlow AI (single `complaints` table)."""
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    original_language TEXT NOT NULL DEFAULT 'en',
    location TEXT NOT NULL,
    category TEXT NOT NULL,
    severity INTEGER NOT NULL,
    priority TEXT NOT NULL,
    priority_score INTEGER NOT NULL,
    priority_reasons TEXT NOT NULL,
    department TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Received',
    cluster_id TEXT NOT NULL,
    ai_mode TEXT NOT NULL,
    image_path TEXT,
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_complaints_ticket ON complaints(ticket_id);
CREATE INDEX IF NOT EXISTS idx_complaints_cluster ON complaints(cluster_id);
CREATE INDEX IF NOT EXISTS idx_complaints_created ON complaints(created_at);
"""


def db_path() -> str:
    return os.getenv("DATABASE_PATH") or str(BASE_DIR / "civicflow.db")


def upload_dir() -> Path:
    return Path(os.getenv("UPLOAD_DIR") or BASE_DIR / "uploads")


def connect() -> sqlite3.Connection:
    # autocommit mode; write paths open an explicit BEGIN IMMEDIATE transaction
    conn = sqlite3.connect(db_path(), timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    Path(db_path()).parent.mkdir(parents=True, exist_ok=True)
    upload_dir().mkdir(parents=True, exist_ok=True)
    conn = connect()
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()

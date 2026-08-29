"""SQLite storage for profile data."""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

@dataclass
class Profile:
    profile_link: str
    target_dir: str
    updated_at: str
    files: list[str]


DB_PATH = os.getenv("AI_SERVICE_DB_PATH", "/tmp/ai-service.db")

_memory_connection = None


def _get_memory_connection():
    """Get shared connection for in-memory database."""
    global _memory_connection
    if _memory_connection is None:
        _memory_connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        _memory_connection.row_factory = sqlite3.Row
    return _memory_connection


def init_db():
    """Initialize database and create tables."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            profile_link TEXT PRIMARY KEY,
            target_dir TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            files TEXT
        )
    """)
    conn.commit()


def get_connection():
    """Get database connection."""
    if DB_PATH == ":memory:":
        return _get_memory_connection()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_profile(profile_link: str) -> Optional[Profile]:
    """Get profile by link."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT profile_link, target_dir, updated_at, files FROM profiles WHERE profile_link = ?",
        (profile_link,)
    )
    row = cursor.fetchone()
    
    if row is None:
        return None
    
    return Profile(
        profile_link=row["profile_link"],
        target_dir=row["target_dir"],
        updated_at=row["updated_at"],
        files=json.loads(row["files"]) if row["files"] else []
    )


def save_profile(profile_link: str, target_dir: str, files: list[str]):
    """Save or update profile record."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO profiles (profile_link, target_dir, updated_at, files)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(profile_link) DO UPDATE SET
            target_dir = excluded.target_dir,
            updated_at = excluded.updated_at,
            files = excluded.files
    """, (profile_link, target_dir, datetime.now().isoformat(), json.dumps(files)))
    conn.commit()


def get_all_profiles() -> list[Profile]:
    """Get all profiles."""
    conn = get_connection()
    cursor = conn.execute("SELECT profile_link, target_dir, updated_at, files FROM profiles")
    rows = cursor.fetchall()
    
    return [
        Profile(
            profile_link=row["profile_link"],
            target_dir=row["target_dir"],
            updated_at=row["updated_at"],
            files=json.loads(row["files"]) if row["files"] else []
        )
        for row in rows
    ]
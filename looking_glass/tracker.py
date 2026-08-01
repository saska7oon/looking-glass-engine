"""
Synchronicity Tracker for the Looking Glass Engine.

Logs all sessions to SQLite for long-term pattern analysis.
Tracks the relationship between consciousness states and AI responses.
"""

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from looking_glass.config import config

logger = logging.getLogger(__name__)


class SynchronicityTracker:
    """Tracks sessions and synchronicities in SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.db_path_expanded
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                question TEXT,
                state_arousal REAL,
                state_depth REAL,
                state_openness REAL,
                state_magnitude REAL,
                state_region TEXT,
                backend TEXT,
                model TEXT,
                response TEXT,
                response_length INTEGER,
                user_feedback TEXT
            );

            CREATE TABLE IF NOT EXISTS synchronicities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TEXT NOT NULL,
                event_type TEXT,
                description TEXT,
                state_arousal REAL,
                state_depth REAL,
                state_openness REAL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS field_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TEXT NOT NULL,
                x REAL,
                y REAL,
                z REAL,
                label TEXT,
                intensity REAL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
            """
        )
        self._conn.commit()

    def log_session(
        self,
        question: str,
        state_arousal: float,
        state_depth: float,
        state_openness: float,
        state_magnitude: float,
        state_region: str,
        backend: str,
        model: str,
        response: str,
        user_feedback: Optional[str] = None,
    ) -> int:
        """Log a complete session and return the session ID."""
        cursor = self._conn.execute(
            """
            INSERT INTO sessions (
                timestamp, question, state_arousal, state_depth,
                state_openness, state_magnitude, state_region,
                backend, model, response, response_length, user_feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                question,
                state_arousal,
                state_depth,
                state_openness,
                state_magnitude,
                state_region,
                backend,
                model,
                response,
                len(response),
                user_feedback,
            ),
        )
        self._conn.commit()
        rowid = cursor.lastrowid
        return rowid if rowid is not None else 0

    def log_field_point(
        self,
        session_id: int,
        x: float,
        y: float,
        z: float,
        label: str,
        intensity: float,
    ):
        """Log a field position for a session."""
        self._conn.execute(
            """
            INSERT INTO field_history (session_id, timestamp, x, y, z, label, intensity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                datetime.now().isoformat(),
                x,
                y,
                z,
                label,
                intensity,
            ),
        )
        self._conn.commit()

    def log_synchronicity(
        self,
        session_id: int,
        event_type: str,
        description: str,
        state_arousal: float,
        state_depth: float,
        state_openness: float,
    ):
        """Log a synchronicity event."""
        self._conn.execute(
            """
            INSERT INTO synchronicities (
                session_id, timestamp, event_type, description,
                state_arousal, state_depth, state_openness
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                datetime.now().isoformat(),
                event_type,
                description,
                state_arousal,
                state_depth,
                state_openness,
            ),
        )
        self._conn.commit()

    def get_session_history(self, limit: int = 20) -> list[dict]:
        """Return recent sessions."""
        cursor = self._conn.execute(
            """
            SELECT id, timestamp, question, state_arousal, state_depth,
                   state_openness, state_region, backend, model,
                   response_length, user_feedback
            FROM sessions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_field_trajectory(self, session_id: int) -> list[dict]:
        """Return the field trajectory for a session."""
        cursor = self._conn.execute(
            """
            SELECT x, y, z, label, intensity, timestamp
            FROM field_history
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_pattern_regions(self, min_visits: int = 3) -> list[dict]:
        """Return regions the user visits frequently (patterns)."""
        cursor = self._conn.execute(
            """
            SELECT state_region as label, COUNT(*) as visits,
                   AVG(state_arousal) as avg_arousal,
                   AVG(state_depth) as avg_depth,
                   AVG(state_openness) as avg_openness
            FROM sessions
            WHERE state_region IS NOT NULL AND state_region != 'Unmapped'
            GROUP BY state_region
            HAVING visits >= ?
            ORDER BY visits DESC
            """,
            (min_visits,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_synchronicities(self, limit: int = 10) -> list[dict]:
        """Return recent synchronicity events."""
        cursor = self._conn.execute(
            """
            SELECT s.timestamp, s.event_type, s.description,
                   s.state_arousal, s.state_depth, s.state_openness,
                   sess.question, sess.response
            FROM synchronicities s
            JOIN sessions sess ON s.session_id = sess.id
            ORDER BY s.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close the database connection."""
        self._conn.close()
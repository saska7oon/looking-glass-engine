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
                user TEXT DEFAULT 'default',
                backend TEXT,
                model TEXT,
                response TEXT,
                response_length INTEGER,
                user_feedback TEXT,
                persona TEXT
            );
            """
        )
        # Migrate existing DBs: add persona/user columns if missing.
        cols = [r[1] for r in self._conn.execute("PRAGMA table_info(sessions)")]
        if "persona" not in cols:
            self._conn.execute("ALTER TABLE sessions ADD COLUMN persona TEXT")
        if "user" not in cols:
            self._conn.execute("ALTER TABLE sessions ADD COLUMN user TEXT DEFAULT 'default'")

        self._conn.executescript(
            """
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

            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
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
        persona: Optional[str] = None,
        user: str = "default",
    ) -> int:
        """Log a complete session and return the session ID."""
        cursor = self._conn.execute(
            """
            INSERT INTO sessions (
                timestamp, question, state_arousal, state_depth,
                state_openness, state_magnitude, state_region, user,
                backend, model, response, response_length, user_feedback, persona
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                question,
                state_arousal,
                state_depth,
                state_openness,
                state_magnitude,
                state_region,
                user,
                backend,
                model,
                response,
                len(response),
                user_feedback,
                persona,
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

    def get_session_history(self, limit: int = 20, user: str = "default") -> list[dict]:
        """Return recent sessions (optionally scoped to one user)."""
        cursor = self._conn.execute(
            """
            SELECT id, timestamp, question, state_arousal, state_depth,
                   state_openness, state_region, user, backend, model,
                   response_length, user_feedback, persona
            FROM sessions
            WHERE user = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_users(self) -> list[str]:
        """Return the distinct users who have accounts."""
        cursor = self._conn.execute(
            "SELECT DISTINCT username FROM users ORDER BY username COLLATE NOCASE"
        )
        return [row["username"] for row in cursor.fetchall()]

    def create_user(self, username: str, password: str) -> bool:
        """Create a user account with a password. Returns False if exists."""
        username = (username or "").strip()
        if not username or not password:
            return False
        exists = self._conn.execute(
            "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE", (username,)
        ).fetchone()
        if exists:
            return False
        salt, pwd_hash = self._hash_password(password)
        self._conn.execute(
            "INSERT INTO users (username, password_hash, salt, created_at) "
            "VALUES (?, ?, ?, ?)",
            (username, pwd_hash, salt, datetime.now().isoformat()),
        )
        self._conn.commit()
        return True

    def authenticate_user(self, username: str, password: str) -> bool:
        """Verify a username/password pair. Return True if valid."""
        username = (username or "").strip()
        row = self._conn.execute(
            "SELECT password_hash, salt FROM users WHERE username = ? COLLATE NOCASE",
            (username,),
        ).fetchone()
        if not row:
            return False
        return self._verify_password(password, row["salt"], row["password_hash"])

    @staticmethod
    def _hash_password(password: str) -> tuple[str, str]:
        """PBKDF2-SHA256 hash with a random salt. Salt stored next to hash."""
        import hashlib
        import secrets
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 120_000
        ).hex()
        return salt, digest

    @staticmethod
    def _verify_password(password: str, salt: str, expected_hash: str) -> bool:
        import hashlib
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 120_000
        ).hex()
        return digest == expected_hash

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

    def get_pattern_regions(self, min_visits: int = 3, user: str = "default") -> list[dict]:
        """Return regions the user visits frequently (patterns)."""
        cursor = self._conn.execute(
            """
            SELECT state_region as label, COUNT(*) as visits,
                   AVG(state_arousal) as avg_arousal,
                   AVG(state_depth) as avg_depth,
                   AVG(state_openness) as avg_openness
            FROM sessions
            WHERE user = ? AND state_region IS NOT NULL AND state_region != 'Unmapped'
            GROUP BY state_region
            HAVING visits >= ?
            ORDER BY visits DESC
            """,
            (user, min_visits),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_recurring_themes(self, user: str = "default", limit: int = 8) -> list[dict]:
        """Aggregate recurring words/themes across a user's questions."""
        import re
        from collections import Counter

        rows = self._conn.execute(
            "SELECT question FROM sessions WHERE user = ? AND question IS NOT NULL",
            (user,),
        ).fetchall()

        # A small function-word stoplist to surface meaningful themes.
        STOP = {
            "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at",
            "for", "with", "about", "is", "am", "are", "was", "were", "be", "been",
            "being", "i", "me", "my", "myself", "we", "our", "us", "you", "your",
            "it", "its", "this", "that", "these", "those", "what", "why", "how",
            "when", "where", "who", "which", "do", "does", "did", "have", "has",
            "had", "can", "could", "will", "would", "should", "might", "may",
            "not", "no", "so", "if", "then", "than", "as", "just", "really",
            "feel", "feels", "feeling", "want", "wants", "need", "needs", "get",
            "keep", "make", "take", "tell", "ask", "life", "day", "days", "time",
        }
        counter = Counter()
        for row in rows:
            q = (row["question"] or "").lower()
            for w in re.findall(r"\b[a-z]{3,}\b", q):
                if w not in STOP:
                    counter[w] += 1
        total = counter.total() or 1
        out = []
        for word, count in counter.most_common(limit):
            if count < 2:
                break
            out.append({"word": word, "count": count, "share": round(count / total, 3)})
        return out

    def get_state_delta(self, user: str = "default") -> dict:
        """Compare earliest vs most recent sessions to surface change over time."""
        rows = self._conn.execute(
            """
            SELECT id, state_arousal, state_depth, state_openness, timestamp
            FROM sessions
            WHERE user = ?
            ORDER BY id ASC
            """,
            (user,),
        ).fetchall()
        if len(rows) < 2:
            return {"has_delta": False}
        first = rows[0]
        last = rows[-1]
        def d(key): return round(float(last[key]) - float(first[key]), 1)
        return {
            "has_delta": True,
            "sessions": len(rows),
            "from": first["timestamp"][:10],
            "to": last["timestamp"][:10],
            "arousal_delta": d("state_arousal"),
            "depth_delta": d("state_depth"),
            "openness_delta": d("state_openness"),
        }

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
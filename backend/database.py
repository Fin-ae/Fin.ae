"""
database.py
SQLite database connection and table setup for Fin.ae.

Uses a module-level singleton so the connection is created once
and reused across all requests — the FastAPI equivalent of
Streamlit's @st.cache_resource pattern from Guide Book 2.
"""

import sqlite3
import logging

log = logging.getLogger(__name__)

# Module-level singleton — created once when the module is first imported
_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """
    Return the shared SQLite connection, creating it if it doesn't exist yet.
    check_same_thread=False is required because FastAPI handles requests
    on multiple threads.
    """
    global _connection
    if _connection is None:
        _connection = sqlite3.connect(
            "finae.db",
            check_same_thread=False
        )
        _connection.row_factory = sqlite3.Row  # lets us access columns by name
        _create_tables(_connection)
        log.info("SQLite connection established and tables created.")
    return _connection


def _create_tables(conn: sqlite3.Connection) -> None:
    """Create all required tables if they don't already exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS applications (
            id          TEXT PRIMARY KEY,
            session_id  TEXT NOT NULL,
            product_id  TEXT NOT NULL,
            product_name TEXT NOT NULL,
            applicant_name TEXT NOT NULL,
            phone       TEXT NOT NULL,
            email       TEXT,
            preferred_time TEXT,
            notes       TEXT,
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  TEXT NOT NULL,
            updated_at  TEXT
        );
    """)
    conn.commit()

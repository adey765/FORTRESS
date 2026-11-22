import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "fortress.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter_id TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash BLOB NOT NULL,
                role TEXT NOT NULL DEFAULT 'voter'
                    CHECK (role IN ('voter', 'admin')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS elections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                is_open INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                election_id INTEGER NOT NULL REFERENCES elections(id),
                name TEXT NOT NULL
            )
            """
        )
        # Identity side: WHO has voted (not WHAT they chose).
        # UNIQUE(election_id, user_id) = one person, one vote, enforced by DB.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voter_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                election_id INTEGER NOT NULL REFERENCES elections(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                UNIQUE (election_id, user_id)
            )
            """
        )
        # Ballot side: WHAT was chosen. No user_id and no timestamp on purpose.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ballots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                election_id INTEGER NOT NULL REFERENCES elections(id),
                candidate_id INTEGER NOT NULL REFERENCES candidates(id)
            )
            """
        )
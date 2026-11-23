import hashlib
import json
from datetime import datetime, timezone

from app.db import get_conn

GENESIS = "0" * 64


def init_audit():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event TEXT NOT NULL,
                details TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                this_hash TEXT NOT NULL
            )
            """
        )


def _hash(created_at, event, details, prev_hash):
    payload = json.dumps(
        [created_at, event, details, prev_hash], separators=(",", ":")
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def log_event(event, details=""):
    init_audit()
    conn = get_conn()
    try:
        with conn:
            last = conn.execute(
                "SELECT this_hash FROM audit_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
            prev = last["this_hash"] if last else GENESIS
            ts = datetime.now(timezone.utc).isoformat()
            h = _hash(ts, event, details, prev)
            conn.execute(
                "INSERT INTO audit_log (created_at, event, details,"
                " prev_hash, this_hash) VALUES (?, ?, ?, ?, ?)",
                (ts, event, details, prev, h),
            )
    finally:
        conn.close()


def verify_chain():
    """Returns (True, None) or (False, id_of_first_bad_record)."""
    init_audit()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id"
        ).fetchall()
    prev = GENESIS
    for r in rows:
        expected = _hash(r["created_at"], r["event"], r["details"], prev)
        if r["prev_hash"] != prev or r["this_hash"] != expected:
            return False, r["id"]
        prev = r["this_hash"]
    return True, None
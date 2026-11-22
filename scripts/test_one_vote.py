import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import get_conn, init_db

init_db()
with get_conn() as conn:
    conn.execute("INSERT INTO elections (title) VALUES ('Test election')")
    eid = conn.execute("SELECT MAX(id) FROM elections").fetchone()[0]
    uid = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

def cast(election_id, user_id):
    conn = get_conn()
    try:
        with conn:  # one transaction: both inserts or neither
            conn.execute(
                "INSERT INTO voter_status (election_id, user_id) VALUES (?, ?)",
                (election_id, user_id),
            )
        return "VOTE ACCEPTED"
    except sqlite3.IntegrityError:
        return "BLOCKED: already voted"
    finally:
        conn.close()

print("1st attempt:", cast(eid, uid))
print("2nd attempt:", cast(eid, uid))
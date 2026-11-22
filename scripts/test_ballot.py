import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import get_conn, init_db

init_db()
with get_conn() as conn:
    conn.execute("INSERT INTO elections (title) VALUES ('Ballot test')")
    eid = conn.execute("SELECT MAX(id) FROM elections").fetchone()[0]
    conn.execute("INSERT INTO candidates (election_id, name) VALUES (?, 'Candidate A')", (eid,))
    cid = conn.execute("SELECT MAX(id) FROM candidates").fetchone()[0]
    uid = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]


def cast_vote(election_id, user_id, candidate_id):
    conn = get_conn()
    try:
        with conn:  # one transaction: both inserts or neither
            conn.execute(
                "INSERT INTO voter_status (election_id, user_id) VALUES (?, ?)",
                (election_id, user_id),
            )
            conn.execute(
                "INSERT INTO ballots (election_id, candidate_id) VALUES (?, ?)",
                (election_id, candidate_id),
            )
        return "VOTE ACCEPTED"
    except sqlite3.IntegrityError:
        return "BLOCKED: already voted (ballot also rolled back)"
    finally:
        conn.close()


print("1st attempt:", cast_vote(eid, uid, cid))
print("2nd attempt:", cast_vote(eid, uid, cid))

with get_conn() as conn:
    n = conn.execute(
        "SELECT COUNT(*) FROM ballots WHERE election_id = ?", (eid,)
    ).fetchone()[0]
print("Ballots stored for this election:", n, "(must be 1)")
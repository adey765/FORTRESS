import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import get_conn, init_db

init_db()
with get_conn() as conn:
    row = conn.execute(
        "SELECT id FROM elections WHERE title = 'Demo Election'"
    ).fetchone()
    if row:
        print("Demo Election already exists, id =", row["id"])
    else:
        cur = conn.execute("INSERT INTO elections (title) VALUES ('Demo Election')")
        eid = cur.lastrowid
        for name in ("Candidate A", "Candidate B", "Candidate C"):
            conn.execute(
                "INSERT INTO candidates (election_id, name) VALUES (?, ?)",
                (eid, name),
            )
        print("Created Demo Election, id =", eid)
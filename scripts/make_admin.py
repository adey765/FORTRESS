import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import get_conn

with get_conn() as conn:
    conn.execute("UPDATE users SET role = 'admin' WHERE voter_id = ?", ("ankita2026",))
    row = conn.execute(
        "SELECT voter_id, role FROM users WHERE voter_id = ?", ("ankita2026",)
    ).fetchone()
print(dict(row))
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.audit import log_event, verify_chain
from app.db import get_conn

log_event("TEST_LOGIN", "user=demo")
log_event("TEST_VOTE", "election=1")
log_event("TEST_BLOCKED", "duplicate vote")
print("Before tampering:", verify_chain())

with get_conn() as conn:
    first = conn.execute(
        "SELECT id FROM audit_log WHERE event = 'TEST_VOTE' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.execute(
        "UPDATE audit_log SET details = 'election=999' WHERE id = ?",
        (first["id"],),
    )

print("After tampering: ", verify_chain())
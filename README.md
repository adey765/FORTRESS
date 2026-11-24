# FORTRESS

Educational face-recognition e-voting prototype (Python, OpenCV, Flask, SQLite).
Not certified and not suitable for real elections.

## What works
- Fisherface face recognition (OpenCV contrib) with distance-threshold unknown rejection, evaluated on a held-out test set
- Flask web app: registration, login (bcrypt, CSRF protection), admin role
- Voting page with one-person-one-vote enforced by a database UNIQUE constraint
- Atomic ballot transaction; ballots table has no user_id
- Hash-chained audit log with admin integrity page (tamper detection)

## Known limitations
- Fisherface is a closed-set classifier; the threshold was calibrated without impostor data, so unknown faces can still be accepted
- No presentation-attack (photo/screen) detection
- Face verification is not yet connected to the web voting flow
- Ballot secrecy is not guaranteed (timing and logs can leak correlations)
- The hash chain is tamper-evident, not tamper-proof: an attacker who controls the database can recompute it
- Small dataset (2 people), so metrics are indicative only

## Future work
Image quality checks, anti-spoofing, Isolation Forest anomaly detection, WebAuthn fingerprint, attack-simulation tests.

## Run
py -3.11 run.py   (then open http://127.0.0.1:5000)
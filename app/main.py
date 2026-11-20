import os
import re
import secrets

import bcrypt
from flask import (Flask, flash, redirect, render_template, request,
                   session, url_for)
from flask_wtf.csrf import CSRFProtect

from app.db import get_conn, init_db

app = Flask(__name__)
# Dev only: random key each start. Later move to .env
app.config["SECRET_KEY"] = os.environ.get("FORTRESS_SECRET") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
CSRFProtect(app)
init_db()

VOTER_ID_RE = re.compile(r"^[A-Za-z0-9]{6,20}$")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        voter_id = request.form.get("voter_id", "").strip()
        name = request.form.get("full_name", "").strip()
        pw = request.form.get("password", "")
        if not VOTER_ID_RE.match(voter_id):
            flash("Voter ID must be 6-20 letters/digits.")
        elif not (2 <= len(name) <= 80):
            flash("Name must be 2-80 characters.")
        elif len(pw) < 10:
            flash("Password must be at least 10 characters.")
        else:
            hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt())
            try:
                with get_conn() as conn:
                    conn.execute(
                        "INSERT INTO users (voter_id, full_name, password_hash)"
                        " VALUES (?, ?, ?)",
                        (voter_id, name, hashed),
                    )
                flash("Registered. Please log in.")
                return redirect(url_for("login"))
            except Exception:
                flash("Could not register (ID may already exist).")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        voter_id = request.form.get("voter_id", "").strip()
        pw = request.form.get("password", "")
        with get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE voter_id = ?", (voter_id,)
            ).fetchone()
        if row and bcrypt.checkpw(pw.encode(), row["password_hash"]):
            session.clear()  # prevents session fixation
            session["user_id"] = row["id"]
            session["role"] = row["role"]
            return redirect(url_for("dashboard"))
        flash("Invalid voter ID or password.")  # same message on purpose
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    with get_conn() as conn:
        row = conn.execute(
            "SELECT full_name, voter_id, role FROM users WHERE id = ?",
            (session["user_id"],),
        ).fetchone()
    return render_template("dashboard.html", user=row)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))
from datetime import datetime, timedelta, timezone
from functools import wraps
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "radian-cash-secret-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

SESSION_TIMEOUT_MINUTES = 30


def get_db_connection():
    from db_connection.connection import get_connection as connection_factory

    return connection_factory()


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def get_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime) -> datetime:
    if value is None:
        return get_now()
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_session_expired(last_activity: datetime) -> bool:
    last_activity = normalize_datetime(last_activity)
    return get_now() - last_activity > timedelta(minutes=SESSION_TIMEOUT_MINUTES)


def login_required(route_function):
    @wraps(route_function)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))

        last_activity = session.get("last_activity")
        if last_activity and is_session_expired(last_activity):
            session.clear()
            flash("Your session expired due to inactivity. Please log in again.", "warning")
            return redirect(url_for("login"))

        session["last_activity"] = get_now()
        return route_function(*args, **kwargs)

    return decorated_function


@app.before_request
def refresh_session_activity():
    if "user_id" not in session:
        return

    last_activity = session.get("last_activity")
    if last_activity is None:
        session["last_activity"] = get_now()
        return

    if is_session_expired(last_activity):
        session.clear()
        flash("Your session expired due to inactivity. Please log in again.", "warning")


@app.route("/", methods=["GET"])
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        middle_name = request.form.get("middle_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone_number = request.form.get("phone_number", "").strip()
        password = request.form.get("password", "").strip()

        if not all([first_name, middle_name, last_name, email, phone_number, password]):
            flash("All fields are required.", "danger")
            return render_template("signup.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("signup.html")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM users WHERE email = %s OR phone_number = %s",
                (email, phone_number),
            )
            existing_user = cur.fetchone()
            if existing_user:
                flash("A user with that email or phone number already exists.", "danger")
                cur.close()
                conn.close()
                return render_template("signup.html")

            hashed_password = hash_password(password)
            cur.execute(
                """
                INSERT INTO users (first_name, middle_name, last_name, email, phone_number, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (first_name, middle_name, last_name, email, phone_number, hashed_password),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as exc:
            flash(f"Signup failed: {exc}", "danger")
            return render_template("signup.html")

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/log-in", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("log-in.html")

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, first_name, middle_name, last_name, email, password_hash FROM users WHERE email = %s",
                (email,),
            )
            user = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as exc:
            flash(f"Login failed: {exc}", "danger")
            return render_template("log-in.html")

        if user and verify_password(password, user[5]):
            session.clear()
            session["user_id"] = user[0]
            session["first_name"] = user[1]
            session["email"] = user[4]
            session["last_activity"] = get_now()
            flash("You are now logged in.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return render_template("log-in.html")

    return render_template("log-in.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", first_name=session.get("first_name", "User"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))





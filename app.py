from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
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


def get_user_transactions(user_id: int) -> list[dict]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                t.id,
                t.transaction_date,
                n.name AS network_name,
                t.transaction_type,
                t.service_name,
                t.amount,
                t.commission,
                t.reference_number,
                t.customer_phone,
                t.notes
            FROM transactions t
            JOIN networks n ON t.network_id = n.id
            WHERE t.user_id = %s
            ORDER BY t.transaction_date DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cur.close()
        conn.close()


def get_all_networks() -> list[dict]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, agent_number, lipa_number FROM networks ORDER BY name"
        )
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cur.close()
        conn.close()


def add_transaction_for_user(
    user_id: int,
    network_id: int,
    transaction_type: str,
    service_name: str | None,
    amount: Decimal,
    commission: Decimal,
    reference_number: str | None,
    customer_phone: str | None,
    notes: str | None,
) -> None:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM networks WHERE id = %s",
            (network_id,),
        )
        if cur.fetchone() is None:
            raise ValueError("Selected network does not exist.")

        cur.execute(
            """
            INSERT INTO transactions (
                network_id,
                transaction_type,
                service_name,
                amount,
                commission,
                reference_number,
                customer_phone,
                notes,
                user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                network_id,
                transaction_type,
                service_name,
                amount,
                commission,
                reference_number,
                customer_phone,
                notes,
                user_id,
            ),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


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


@app.route("/transactions/new", methods=["POST"])
@login_required
def create_transaction():
    network_id_text = request.form.get("network_id", "").strip()
    transaction_type = request.form.get("transaction_type", "").strip()
    service_name = request.form.get("service_name", "").strip() or None
    amount_text = request.form.get("amount", "").strip()
    commission_text = request.form.get("commission", "").strip()
    reference_number = request.form.get("reference_number", "").strip() or None
    customer_phone = request.form.get("customer_phone", "").strip() or None
    notes = request.form.get("notes", "").strip() or None

    if not network_id_text or not transaction_type or not amount_text:
        flash("Network, transaction type, and amount are required.", "danger")
        return redirect(url_for("dashboard"))

    try:
        network_id = int(network_id_text)
    except ValueError:
        flash("Please select a valid network from the list.", "danger")
        return redirect(url_for("dashboard"))

    try:
        amount = Decimal(amount_text.replace(",", ""))
    except (InvalidOperation, ValueError):
        flash("Please enter a valid numeric amount.", "danger")
        return redirect(url_for("dashboard"))

    if commission_text:
        try:
            commission = Decimal(commission_text.replace(",", ""))
        except (InvalidOperation, ValueError):
            flash("Please enter a valid numeric commission.", "danger")
            return redirect(url_for("dashboard"))
    else:
        commission = Decimal("0")

    try:
        add_transaction_for_user(
            user_id=session["user_id"],
            network_id=network_id,
            transaction_type=transaction_type,
            service_name=service_name,
            amount=amount,
            commission=commission,
            reference_number=reference_number,
            customer_phone=customer_phone,
            notes=notes,
        )
        flash("Transaction added successfully.", "success")
    except Exception as exc:
        flash(f"Failed to add transaction: {exc}", "danger")

    return redirect(url_for("dashboard"))


@app.route("/networks/new", methods=["POST"])
@login_required
def create_network():
    name = request.form.get("network_name", "").strip()
    agent_number_text = request.form.get("agent_number", "").strip()
    lipa_number_text = request.form.get("lipa_number", "").strip()

    if not name or not agent_number_text or not lipa_number_text:
        flash("Network name, agent number, and lipa number are required.", "danger")
        return redirect(url_for("dashboard"))

    try:
        agent_number = int(agent_number_text)
        lipa_number = int(lipa_number_text)
    except ValueError:
        flash("Agent number and lipa number must be whole numbers.", "danger")
        return redirect(url_for("dashboard"))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM networks WHERE LOWER(name) = LOWER(%s)",
            (name.lower(),),
        )
        if cur.fetchone():
            flash("A network with that name already exists.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for("dashboard"))

        cur.execute(
            "INSERT INTO networks (name, agent_number, lipa_number) VALUES (%s, %s, %s)",
            (name, agent_number, lipa_number),
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Network added successfully.", "success")
    except Exception as exc:
        flash(f"Failed to add network: {exc}", "danger")

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    transactions = get_user_transactions(session["user_id"])
    networks = get_all_networks()
    return render_template(
        "dashboard.html",
        first_name=session.get("first_name", "User"),
        transactions=transactions,
        networks=networks,
    )


if __name__ == "__main__":
    app.run(debug=True)

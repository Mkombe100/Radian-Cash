from flask import flash, redirect, render_template, request, session, url_for

from db_connection.connection import get_connection as get_db_connection
from systemFunctionalities.auth import hash_password, verify_password
from systemFunctionalities.session_utils import get_now


def handle_signup():
    if request.method == "GET":
        return render_template("signup.html")

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
        if cur.fetchone():
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


def handle_login():
    if request.method == "GET":
        return render_template("log-in.html")

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


def handle_logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

from datetime import timedelta
import os

from flask import Flask, redirect, render_template, session, url_for

from systemFunctionalities.session_utils import login_required, refresh_session_activity
from systemFunctionalities.users import handle_signup, handle_login, handle_logout
from systemFunctionalities.transactions import get_user_transactions, handle_create_transaction
from systemFunctionalities.networks import get_all_networks, handle_create_network

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "radian-cash-secret-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)


@app.before_request
def before_request():
    refresh_session_activity()


@app.route("/", methods=["GET"])
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    return handle_signup()


@app.route("/log-in", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    return handle_login()


@app.route("/logout")
def logout():
    return handle_logout()


@app.route("/transactions/new", methods=["POST"])
@login_required
def create_transaction():
    return handle_create_transaction()


@app.route("/networks/new", methods=["POST"])
@login_required
def create_network():
    return handle_create_network()


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

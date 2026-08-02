from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import flash, redirect, session, url_for

SESSION_TIMEOUT_MINUTES = 30


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

from flask import flash, redirect, request, url_for

from db_connection.connection import get_connection as get_db_connection


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


def create_network(name: str, agent_number: int, lipa_number: int) -> None:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM networks WHERE LOWER(name) = LOWER(%s)",
            (name,),
        )
        if cur.fetchone():
            raise ValueError("A network with that name already exists.")

        cur.execute(
            "INSERT INTO networks (name, agent_number, lipa_number) VALUES (%s, %s, %s)",
            (name, agent_number, lipa_number),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def handle_create_network():
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
        create_network(name, agent_number, lipa_number)
        flash("Network added successfully.", "success")
    except Exception as exc:
        flash(f"Failed to add network: {exc}", "danger")

    return redirect(url_for("dashboard"))

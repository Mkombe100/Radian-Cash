from decimal import Decimal, InvalidOperation

from flask import flash, redirect, request, session, url_for

from db_connection.connection import get_connection as get_db_connection


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
        cur.execute("SELECT id FROM networks WHERE id = %s", (network_id,))
        if cur.fetchone() is None:
            raise ValueError("Selected network does not exist.")

        cur.execute(
            """
            INSERT INTO transactions (
                network_id, transaction_type, service_name, amount,
                commission, reference_number, customer_phone, notes, user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                network_id, transaction_type, service_name, amount,
                commission, reference_number, customer_phone, notes, user_id,
            ),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def handle_create_transaction():
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

from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, jsonify
from app.db import get_conn

bp = Blueprint("transactions", __name__)

@bp.route("/transactions", methods=["GET"])
def list_transactions():
    account_id = request.args.get("account_id", type=int)
    if account_id is None:
        return jsonify({"error": "account_id is required"}), 400
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT transaction_id, account_id, amount, tx_type, created_at "
            "FROM transactions WHERE account_id = %s ORDER BY transaction_id",
            (account_id,),
        ).fetchall()
    return jsonify([
        {"id": r[0], "account_id": r[1], "amount": str(r[2]),
         "tx_type": r[3], "created_at": r[4].isoformat()}
        for r in rows
    ])

@bp.route("/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json(force=True)
    account_id = data.get("account_id")
    tx_type = data.get("tx_type")

    if not isinstance(account_id, int):
        return jsonify({"error": "account_id must be an integer"}), 400
    if tx_type not in ("debit", "credit"):
        return jsonify({"error": "tx_type must be 'debit' or 'credit'"}), 400
    try:
        amount = Decimal(str(data.get("amount")))
    except InvalidOperation:
        return jsonify({"error": "amount must be a number"}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    with get_conn() as conn:
        row = conn.execute(
            "SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE",
            (account_id,),
        ).fetchone()
        if row is None:
            return jsonify({"error": "Account not found"}), 404

        delta = -amount if tx_type == "debit" else amount
        if row[0] + delta < 0:
            return jsonify({"error": "Insufficient funds"}), 400

        conn.execute(
            "UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
            (delta, account_id),
        )
        tid = conn.execute(
            "INSERT INTO transactions (account_id, amount, tx_type) "
            "VALUES (%s, %s, %s) RETURNING transaction_id",
            (account_id, amount, tx_type),
        ).fetchone()[0]
        conn.commit()
    return jsonify({"transaction_id": tid}), 201

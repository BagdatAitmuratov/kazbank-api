import random
import time
from decimal import Decimal, InvalidOperation

import psycopg
from flask import Blueprint, request, jsonify
from psycopg import IsolationLevel, errors
from app.db import get_conn

bp = Blueprint("transfer", __name__)

# Қайталауға болатын қателер: SERIALIZABLE конфликті (40001) және deadlock (40P01)
RETRYABLE = (errors.SerializationFailure, errors.DeadlockDetected)


class TransferError(Exception):
    """Бизнес-қате: қайталаудың қажеті жоқ, сол күйінде клиентке қайтарылады."""
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def with_retry(fn, max_retries=10):
    """Step 5 Task 3: SerializationFailure/Deadlock кезінде қайталау (jitter-мен backoff)."""
    for attempt in range(max_retries):
        try:
            return fn()
        except RETRYABLE:
            if attempt == max_retries - 1:
                raise
            time.sleep(random.uniform(0, 0.02 * 2 ** min(attempt, 5)))


def _do_transfer(from_acc, to_acc, amount):
    # Әр әрекетте жаңа транзакция; қате болса with блогы автоматты rollback жасайды
    with get_conn() as conn:
        try:
            # Task 3: SERIALIZABLE (транзакция басталмай тұрып қойылады)
            conn.isolation_level = IsolationLevel.SERIALIZABLE

            # Task 5: құлыптарды әрқашан бірдей ретпен алу (кіші id бірінші)
            for acc in sorted([from_acc, to_acc]):
                row = conn.execute(
                    "SELECT 1 FROM accounts WHERE account_id = %s FOR UPDATE", (acc,)
                ).fetchone()
                if row is None:
                    raise TransferError(f"Account {acc} not found", 404)

            # Task 2: SAVEPOINT, қате болуы мүмкін қадамды бөлек қорғау
            conn.execute("SAVEPOINT sp_debit")
            try:
                conn.execute(
                    "UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                    (amount, from_acc),
                )
            except errors.CheckViolation:  # balance >= 0 шектеуі бұзылды
                conn.execute("ROLLBACK TO SAVEPOINT sp_debit")
                raise TransferError("Insufficient funds", 400)

            conn.execute(
                "UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
                (amount, to_acc),
            )
            conn.execute(
                "INSERT INTO transactions (account_id, amount, tx_type) VALUES (%s, %s, 'debit')",
                (from_acc, amount),
            )
            conn.execute(
                "INSERT INTO transactions (account_id, amount, tx_type) VALUES (%s, %s, 'credit')",
                (to_acc, amount),
            )
            conn.commit()  # Task 1: екі UPDATE бірге сақталады
        finally:
            # Қосылым пулға қайтарылады, сондықтан деңгейді қалпына келтіреміз,
            # әйтпесе SERIALIZABLE басқа сұраныстарға өтіп кетеді
            conn.rollback()  # commit болған болса, ештеңе істемейді
            conn.isolation_level = None




@bp.route("/transfer", methods=["POST"])
def transfer():
    data = request.get_json(force=True)
    from_acc = data.get("from_account")
    to_acc = data.get("to_account")

    if not isinstance(from_acc, int) or not isinstance(to_acc, int):
        return jsonify({"error": "from_account and to_account must be integers"}), 400
    if from_acc == to_acc:
        return jsonify({"error": "Accounts must be different"}), 400
    try:
        amount = Decimal(str(data.get("amount")))
    except InvalidOperation:
        return jsonify({"error": "amount must be a number"}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    try:
        with_retry(lambda: _do_transfer(from_acc, to_acc, amount))
        return jsonify({"status": "ok", "from": from_acc, "to": to_acc,
                        "amount": str(amount)}), 200
    except TransferError as e:
        return jsonify({"error": e.message}), e.status
    except RETRYABLE:
        # барлық қайталау таусылғаннан кейін ғана
        return jsonify({"error": "Concurrent update, please retry"}), 409
    except psycopg.OperationalError:
        # RETRYABLE-дан кейін тұруы маңызды: SerializationFailure өзі OperationalError-дың ұрпағы
        return jsonify({"error": "Database unavailable"}), 503
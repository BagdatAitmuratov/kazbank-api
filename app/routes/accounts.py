from flask import Blueprint, request, jsonify
from app.db import get_conn

bp = Blueprint("accounts", __name__)

@bp.route("/accounts", methods=["GET"])
def list_accounts():
    customer_id = request.args.get("customer_id", type=int)
    if customer_id is not None:
        sql = ("SELECT account_id, customer_id, account_number, balance "
               "FROM accounts WHERE customer_id = %s ORDER BY account_id")
        args = (customer_id,)
    else:
        sql = ("SELECT account_id, customer_id, account_number, balance "
               "FROM accounts ORDER BY account_id")
        args = ()
    with get_conn() as conn:
        rows = conn.execute(sql, args).fetchall()
    return jsonify([
        {"account_id": r[0], "customer_id": r[1],
         "account_number": r[2], "balance": str(r[3])}
        for r in rows
    ])

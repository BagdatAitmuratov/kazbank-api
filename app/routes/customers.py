import psycopg
from flask import Blueprint, request, jsonify
from psycopg import errors as pg_errors
from app.db import get_conn

bp = Blueprint("customers", __name__)

@bp.route("/customers", methods=["GET"])
def list_customers():
    city = request.args.get("city")
    if city:
        sql = "SELECT customer_id, full_name, city FROM customers WHERE city = %s ORDER BY customer_id"
        args = (city,)
    else:
        sql = "SELECT customer_id, full_name, city FROM customers ORDER BY customer_id"
        args = ()
    with get_conn() as conn:
        rows = conn.execute(sql, args).fetchall()
    return jsonify([{"id": r[0], "name": r[1], "city": r[2]} for r in rows])

@bp.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json(force=True)
    try:
        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO customers (full_name, city, email) "
                "VALUES (%s, %s, %s) RETURNING customer_id",
                (data.get("full_name"), data.get("city", "Almaty"), data.get("email")),
            )
            new_id = cur.fetchone()[0]
            conn.commit()
        return jsonify({"customer_id": new_id}), 201
    except pg_errors.UniqueViolation:
        return jsonify({"error": "Email already registered"}), 409
    except pg_errors.NotNullViolation as e:
        return jsonify({"error": f"Missing required field: {e.diag.column_name}"}), 400
    except psycopg.OperationalError:
        return jsonify({"error": "Database unavailable"}), 503

@bp.route("/customers/<int:cid>", methods=["PUT"])
def update_customer(cid):
    data = request.get_json(force=True)
    with get_conn() as conn:
        conn.execute(
            "UPDATE customers SET full_name = %s, city = %s WHERE customer_id = %s",
            (data["full_name"], data["city"], cid),
        )
        conn.commit()
    return jsonify({"updated": cid})

@bp.route("/customers/<int:cid>", methods=["DELETE"])
def delete_customer(cid):
    with get_conn() as conn:
        conn.execute("DELETE FROM customers WHERE customer_id = %s", (cid,))
        conn.commit()
    return jsonify({"deleted": cid})

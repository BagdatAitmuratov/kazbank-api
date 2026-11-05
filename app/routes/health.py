from flask import Blueprint, jsonify
from app.db import pool

bp = Blueprint("health", __name__)


@bp.route("/health")
def health():
    try:
        pool.check()  # барлық қосылымның тірі екенін тексереді
        return jsonify({"status": "ok", "pool": pool.get_stats()})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 503
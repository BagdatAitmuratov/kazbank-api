import psycopg
from psycopg import errors
from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)

    from .routes.customers import bp as customers_bp
    from .routes.accounts import bp as accounts_bp
    from .routes.transactions import bp as transactions_bp
    from .routes.transfer import bp as transfer_bp
    from .routes.health import bp as health_bp

    app.register_blueprint(customers_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(transfer_bp)
    app.register_blueprint(health_bp)

    # Барлық endpoint үшін ортақ қате өңдеу (Step 7 талабы)
    @app.errorhandler(errors.UniqueViolation)
    def handle_unique(e):
        return jsonify({"error": "Duplicate value (already exists)"}), 409

    @app.errorhandler(errors.NotNullViolation)
    def handle_not_null(e):
        return jsonify({"error": f"Missing required field: {e.diag.column_name}"}), 400

    @app.errorhandler(psycopg.OperationalError)
    def handle_operational(e):
        return jsonify({"error": "Database unavailable"}), 503

    return app
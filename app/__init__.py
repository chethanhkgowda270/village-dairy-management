import os

from flask import Flask, jsonify

from . import db
from .routes import bp


def create_app(database=None):
    app = Flask(__name__)
    app.url_map.strict_slashes = False  # /farmers and /farmers/ both work
    if database is None:
        database = os.path.join(os.path.dirname(app.root_path), "dairy.db")
    app.config["DATABASE"] = database
    db.init_app(app)
    app.register_blueprint(bp)

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api")
    def api_info():
        return jsonify(
            name="Village Dairy Management System",
            try_these=["/health", "/farmers", "/collections", "/reports/daily"],
        )

    @app.get("/favicon.ico")
    def favicon():
        return "", 204

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    return app

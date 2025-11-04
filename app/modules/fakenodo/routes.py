from flask import Blueprint, jsonify


# Minimal placeholder blueprint to satisfy ModuleManager's dynamic import.
# fakenodo runs as a standalone dev service (python3 app/modules/fakenodo/app.py)
# and is NOT integrated into the main app's routes. This blueprint only exists to
# avoid noisy import errors during app startup (e.g., `flask db upgrade`).

fakenodo_module = Blueprint("fakenodo_module", __name__, url_prefix="/fakenodo")


@fakenodo_module.route("/status", methods=["GET"])
def status():
    return jsonify(
        {
            "module": "fakenodo",
            "status": "ok",
            "mode": "standalone",
            "hint": "Run: python3 app/modules/fakenodo/app.py",
        }
    )

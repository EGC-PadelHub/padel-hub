"""Ultra-simplified in-process fake Zenodo (fakenodo) endpoints.

Replaces previous standalone mini-app. Registered automatically; no separate
process. Always returns success; keeps only ephemeral in-memory state.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request

fakenodo_module = Blueprint("fakenodo", __name__, url_prefix="/fakenodo")

_STATE: Dict[str, object] = {
    "next_id": itertools.count(1),
    "records": {},
}


def _new_id() -> int:
    return next(_STATE["next_id"])  # type: ignore[arg-type]


def _get_record(rec_id: int) -> Optional[Dict]:
    return _STATE["records"].get(rec_id)  # type: ignore[index]


@fakenodo_module.route("/depositions", methods=["GET"])
def list_depositions():
    records: Dict[int, Dict] = _STATE["records"]  # type: ignore[assignment]
    return jsonify([r.copy() for r in records.values()]), 200


@fakenodo_module.route("/depositions", methods=["POST"])
def create_deposition():
    payload = request.get_json(silent=True) or {}
    metadata = payload.get("metadata", {})
    rec_id = _new_id()
    record = {
        "id": rec_id,
        "conceptrecid": rec_id,
        "metadata": metadata,
        "files": [],
        "doi": None,
        "state": "draft",
    }
    _STATE["records"][rec_id] = record  # type: ignore[index]
    return (
        jsonify(
            {
                **record,
                "links": {
                    "files": f"/fakenodo/depositions/{rec_id}/files",
                    "publish": f"/fakenodo/depositions/{rec_id}/actions/publish",
                    "self": f"/fakenodo/depositions/{rec_id}",
                },
            }
        ),
        201,
    )


@fakenodo_module.route("/depositions/<int:rec_id>", methods=["GET"])
def get_deposition(rec_id: int):
    record = _get_record(rec_id)
    if not record:
        return jsonify({"message": "Not found"}), 404
    return jsonify(record), 200


@fakenodo_module.route("/depositions/<int:rec_id>/files", methods=["POST"])
def upload_file(rec_id: int):
    record = _get_record(rec_id)
    if not record:
        return jsonify({"message": "Not found"}), 404
    if request.files:
        file_obj = request.files.get("file")
        filename = request.form.get("name") or (file_obj.filename if file_obj else None)
    else:
        data = request.get_json(silent=True) or {}
        filename = data.get("name") or request.form.get("name")
    if not filename:
        return jsonify({"message": "Missing file name"}), 400
    files: List[Dict] = record["files"]  # type: ignore[assignment]
    files[:] = [f for f in files if f.get("name") != filename]
    files.append({"name": filename})
    return jsonify({"filename": filename, "links": {"self": f"/fakenodo/depositions/{rec_id}/files/{filename}"}}), 201


@fakenodo_module.route("/depositions/<int:rec_id>/actions/publish", methods=["POST"])
def publish_deposition(rec_id: int):
    record = _get_record(rec_id)
    if not record:
        return jsonify({"message": "Not found"}), 404
    if not record.get("doi"):
        record["doi"] = f"10.5072/fakenodo.{rec_id}"
        record["state"] = "published"
    return jsonify({"id": rec_id, "doi": record.get("doi"), "conceptrecid": rec_id}), 202


@fakenodo_module.route("/status", methods=["GET"])
def status():
    return jsonify({"module": "fakenodo", "mode": "in-process", "records": len(_STATE["records"])})

"""Basic fakenodo mock: simulate minimal Zenodo-like API behaviour.

Meets the requested behaviours:
- Create record, publish, list versions
- Edit metadata only → no new DOI/version
- Change/add files and publish → new DOI/version
- Configurable via FAKENODO_URL (prefix /fakenodo/api)
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, request

fakenodo_module = Blueprint("fakenodo", __name__, url_prefix="/fakenodo/api")

_STATE: Dict[str, object] = {
    "next_id": itertools.count(1),
    "records": {},          # rec_id -> record dict
    "versions": {},         # conceptrecid -> list of rec_ids
}


def _new_id() -> int:
    return next(_STATE["next_id"])  # type: ignore[arg-type]


def _get_record(rec_id: int) -> Optional[Dict]:
    return _STATE["records"].get(rec_id)  # type: ignore[index]


def _add_version(conceptrecid: int, rec_id: int) -> None:
    versions: Dict = _STATE["versions"]  # type: ignore[assignment]
    versions.setdefault(conceptrecid, []).append(rec_id)


def _get_versions(conceptrecid: int) -> List[int]:
    versions: Dict = _STATE["versions"]  # type: ignore[assignment]
    return versions.get(conceptrecid, [])


# Test connection (GET /fakenodo/api)
@fakenodo_module.route("", methods=["GET"])
def test_connection_fakenodo():
    response = {"status": "success", "message": "Connected to FakenodoAPI"}
    return jsonify(response), 200


# List all depositions (return list directly as Zenodo does)
@fakenodo_module.route("/deposit/depositions", methods=["GET"])
def get_all_depositions():
    return jsonify(list(_STATE["records"].values())), 200


# Create deposition
@fakenodo_module.route("/deposit/depositions", methods=["POST"])
def create_new_deposition():
    payload = request.get_json(silent=True) or {}
    metadata = payload.get("metadata", {})
    rec_id = _new_id()
    record = {
        "id": rec_id,
        "conceptrecid": rec_id,  # first version = concept id
        "metadata": metadata,
        "files": [],
        "doi": None,
        "published": False,
        "files_modified": False,
    }
    _STATE["records"][rec_id] = record
    _add_version(rec_id, rec_id)
    return jsonify(record), 201


# Get deposition
@fakenodo_module.route("/deposit/depositions/<int:deposition_id>", methods=["GET"])
def get_deposition(deposition_id):
    record = _get_record(deposition_id)
    if not record:
        return jsonify({"message": "Deposition not found"}), 404
    return jsonify(record), 200


# Update metadata only (no new DOI/version)
@fakenodo_module.route("/deposit/depositions/<int:deposition_id>", methods=["PUT"])
def update_metadata(deposition_id):
    record = _get_record(deposition_id)
    if not record:
        return jsonify({"message": "Deposition not found"}), 404

    payload = request.get_json(silent=True) or {}
    new_metadata = payload.get("metadata", {})
    record["metadata"].update(new_metadata)
    return jsonify(record), 200


# Delete deposition
@fakenodo_module.route("/deposit/depositions/<deposition_id>", methods=["DELETE"])
def delete_deposition_fakenodo(deposition_id):
    deposition_id_int = int(deposition_id)
    if deposition_id_int in _STATE["records"]:
        del _STATE["records"][deposition_id_int]
        return jsonify({"message": "Deposition deleted"}), 200
    return jsonify({"message": "Deposition not found"}), 404


# Upload file
@fakenodo_module.route("/deposit/depositions/<int:deposition_id>/files", methods=["POST"])
def upload_file(deposition_id):
    record = _get_record(deposition_id)
    if not record:
        return jsonify({"message": "Deposition not found"}), 404

    # Get filename from form data or from uploaded file
    filename = request.form.get("filename") or request.form.get("name")
    if not filename and request.files:
        # If filename not in form, get it from the uploaded file
        file = list(request.files.values())[0] if request.files else None
        filename = file.filename if file else "unnamed_file"
    if not filename:
        filename = "unnamed_file"
    
    # dedupe by filename
    record["files"] = [f for f in record["files"] if f.get("filename") != filename]
    record["files"].append({"filename": filename})
    record["files_modified"] = True

    return jsonify({"filename": filename, "link": f"http://fakenodo.org/files/{deposition_id}/files/{filename}"}), 201


# Publish deposition
@fakenodo_module.route("/deposit/depositions/<int:deposition_id>/actions/publish", methods=["POST"])
def publish_deposition(deposition_id):
    record = _get_record(deposition_id)
    if not record:
        return jsonify({"message": "Deposition not found"}), 404

    # If already published and files changed -> new version with new DOI
    if record.get("published") and record.get("files_modified"):
        conceptrecid = record["conceptrecid"]
        new_rec_id = _new_id()
        new_record = {
            "id": new_rec_id,
            "conceptrecid": conceptrecid,
            "metadata": record["metadata"].copy(),
            "files": record["files"].copy(),
            "doi": f"10.5072/fakenodo.{new_rec_id}",
            "published": True,
            "files_modified": False,
        }
        _STATE["records"][new_rec_id] = new_record
        _add_version(conceptrecid, new_rec_id)
        # Return the full new record as Zenodo does
        return jsonify(new_record), 202

    # First publish or metadata-only change
    if not record.get("doi"):
        record["doi"] = f"10.5072/fakenodo.{deposition_id}"
    record["published"] = True
    record["files_modified"] = False
    # Return the full record as Zenodo does, which includes id, doi, conceptrecid and metadata
    return jsonify(record), 202


# List versions for a concept
@fakenodo_module.route("/deposit/depositions/<int:deposition_id>/versions", methods=["GET"])
def list_versions(deposition_id):
    record = _get_record(deposition_id)
    if not record:
        return jsonify({"message": "Deposition not found"}), 404

    conceptrecid = record["conceptrecid"]
    version_ids = _get_versions(conceptrecid)
    records: Dict[int, Dict] = _STATE["records"]  # type: ignore[assignment]
    versions = [records[vid] for vid in version_ids if vid in records]
    return jsonify({"versions": versions}), 200

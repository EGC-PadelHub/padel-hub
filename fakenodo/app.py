import hashlib
import html
import json
import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, List

from flask import Flask, jsonify, request


APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
STORE_PATH = os.path.join(DATA_DIR, "store.json")


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    if not os.path.exists(STORE_PATH):
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump({"next_id": 1, "records": {}}, f)


_store_lock = threading.Lock()


def _load_store() -> Dict[str, Any]:
    with _store_lock:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)


def _save_store(store: Dict[str, Any]):
    with _store_lock:
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, sort_keys=True)


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _md5_bytes(data: bytes) -> str:
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()


def _record_dir(rec_id: int) -> str:
    d = os.path.join(UPLOADS_DIR, str(rec_id))
    os.makedirs(d, exist_ok=True)
    return d


def _draft_dir(rec_id: int) -> str:
    d = os.path.join(_record_dir(rec_id), "draft")
    os.makedirs(d, exist_ok=True)
    return d


def _version_dir(rec_id: int, version: int) -> str:
    d = os.path.join(_record_dir(rec_id), f"v{version}")
    os.makedirs(d, exist_ok=True)
    return d


def _files_signature(files: List[Dict[str, Any]]) -> List[str]:
    # signature list for simple comparison
    return sorted([f"{f['name']}:{f.get('checksum', '')}:{f.get('size', 0)}" for f in files])


def create_app():
    ensure_dirs()
    app = Flask(__name__)

    BASE_DOI_PREFIX = os.environ.get("FAKENODO_DOI_PREFIX", "10.5072/fakenodo")

    def _concept_doi(rec_id: int) -> str:
        return f"{BASE_DOI_PREFIX}.{rec_id}"

    def _version_doi(rec_id: int, version: int) -> str:
        return f"{BASE_DOI_PREFIX}.{rec_id}.v{version}"

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "time": _now_iso()})

    @app.route("/", methods=["GET"])
    def index():
        return (
            jsonify(
                {
                    "service": "fakenodo",
                    "status": "running",
                    "health": "/health",
                    "ui": "/ui",
                    "api": {
                        "list": "/api/deposit/depositions",
                        "create": "/api/deposit/depositions",
                        "item": "/api/deposit/depositions/<id>",
                        "update": "/api/deposit/depositions/<id>",
                        "delete": "/api/deposit/depositions/<id>",
                        "upload_file": "/api/deposit/depositions/<id>/files",
                        "edit": "/api/deposit/depositions/<id>/actions/edit",
                        "publish": "/api/deposit/depositions/<id>/actions/publish",
                        "versions": "/api/deposit/depositions/<id>/versions",
                    },
                }
            ),
            200,
        )

        # Very simple HTML UI to inspect data while developing
        @app.route("/ui", methods=["GET"])
        def ui_index():
                store = _load_store()
                rows = []
                for rid, rec in store.get("records", {}).items():
                        rid_int = rec.get("id")
                        conceptdoi = html.escape(rec.get("conceptdoi", ""))
                        current_doi = html.escape(rec.get("current_doi", ""))
                        versions = rec.get("versions", [])
                        vcount = len(versions)
                        rows.append(
                                f"<tr>\n"
                                f"  <td>{rid_int}</td>\n"
                                f"  <td>{conceptdoi}</td>\n"
                                f"  <td>{current_doi}</td>\n"
                                f"  <td>{vcount}</td>\n"
                                f"  <td><a href=\"/ui/{rid_int}\">ver</a></td>\n"
                                f"</tr>"
                        )
                body = f"""
                <html>
                <head>
                    <meta charset=\"utf-8\" />
                    <title>fakenodo UI</title>
                    <style>
                        body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; }}
                        th {{ background: #f5f5f5; text-align: left; }}
                        caption {{ text-align: left; font-weight: 600; margin-bottom: .5rem; }}
                        .muted {{ color: #666; }}
                    </style>
                </head>
                <body>
                    <h1>fakenodo <span class=\"muted\">(local)</span></h1>
                    <p>Endpoints API: <code>/api/deposit/depositions</code></p>
                    <table>
                        <caption>Depositions</caption>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Concept DOI</th>
                                <th>Current DOI</th>
                                <th>Versions</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows)}
                        </tbody>
                    </table>
                </body>
                </html>
                """
                return body, 200, {"Content-Type": "text/html; charset=utf-8"}

        @app.route("/ui/<int:rec_id>", methods=["GET"])
        def ui_detail(rec_id: int):
                store = _load_store()
                rec = store.get("records", {}).get(str(rec_id))
                if not rec:
                        return f"<h1>Not found: {rec_id}</h1>", 404

                def pre(obj):
                        return f"<pre>{html.escape(json.dumps(obj, indent=2, ensure_ascii=False))}</pre>"

                versions = rec.get("versions", [])
                vrows = []
                for v in versions:
                        vrows.append(
                                f"<tr>\n"
                                f"  <td>{v.get('version')}</td>\n"
                                f"  <td>{html.escape(v.get('doi',''))}</td>\n"
                                f"  <td>{html.escape(v.get('published_at',''))}</td>\n"
                                f"  <td>{len(v.get('files', []))}</td>\n"
                                f"</tr>"
                        )

                body = f"""
                <html>
                <head>
                    <meta charset=\"utf-8\" />
                    <title>deposition {rec_id}</title>
                    <style>
                        body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; }}
                        th {{ background: #f5f5f5; text-align: left; }}
                        h1 {{ margin-bottom: .5rem; }}
                        .muted {{ color: #666; }}
                    </style>
                </head>
                <body>
                    <p><a href=\"/ui\">← back</a></p>
                    <h1>Deposition {rec_id}</h1>
                    <p class=\"muted\">conceptdoi: {html.escape(rec.get('conceptdoi',''))} · current doi: {html.escape(rec.get('current_doi','') or '')}</p>
                    <h2>Draft metadata</h2>
                    {pre(rec.get('draft', {}).get('metadata', {}))}
                    <h2>Draft files</h2>
                    {pre(rec.get('draft', {}).get('files', []))}
                    <h2>Versions</h2>
                    <table>
                        <thead>
                            <tr><th>Version</th><th>DOI</th><th>Published at</th><th>#Files</th></tr>
                        </thead>
                        <tbody>
                            {''.join(vrows)}
                        </tbody>
                    </table>
                </body>
                </html>
                """
                return body, 200, {"Content-Type": "text/html; charset=utf-8"}

    # Minimal Zenodo-like endpoints under /api/deposit/depositions
    @app.route("/api/deposit/depositions", methods=["GET"])
    def list_depositions():
        store = _load_store()
        items = []
        for rid, rec in store["records"].items():
            items.append(
                {
                    "id": rec["id"],
                    "conceptdoi": rec.get("conceptdoi"),
                    "doi": rec.get("current_doi"),
                    "metadata": rec.get("draft", {}).get("metadata", {}),
                    "files": rec.get("draft", {}).get("files", []),
                    "versions": [
                        {"version": v["version"], "doi": v["doi"], "published_at": v["published_at"]}
                        for v in rec.get("versions", [])
                    ],
                }
            )
        return jsonify(items), 200

    @app.route("/api/deposit/depositions", methods=["POST"])
    def create_deposition():
        payload = request.get_json(silent=True) or {}
        metadata = payload.get("metadata", {})

        store = _load_store()
        rec_id = store["next_id"]
        store["next_id"] = rec_id + 1

        record = {
            "id": rec_id,
            "conceptdoi": _concept_doi(rec_id),
            "current_doi": None,
            "versions": [],
            "draft": {"metadata": metadata, "files": []},
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }

        store["records"][str(rec_id)] = record
        _save_store(store)

        response = {
            "id": rec_id,
            "conceptdoi": record["conceptdoi"],
            "links": {
                "files": f"/api/deposit/depositions/{rec_id}/files",
                "publish": f"/api/deposit/depositions/{rec_id}/actions/publish",
                "self": f"/api/deposit/depositions/{rec_id}",
            },
            "metadata": metadata,
            "state": "draft",
        }
        return jsonify(response), 201

    @app.route("/api/deposit/depositions/<int:rec_id>", methods=["GET"])
    def get_deposition(rec_id: int):
        store = _load_store()
        rec = store["records"].get(str(rec_id))
        if not rec:
            return jsonify({"message": "Not found"}), 404
        payload = {
            "id": rec["id"],
            "conceptdoi": rec.get("conceptdoi"),
            "doi": rec.get("current_doi"),
            "metadata": rec.get("draft", {}).get("metadata", {}),
            "files": rec.get("draft", {}).get("files", []),
            "versions": rec.get("versions", []),
            "state": "draft",
        }
        return jsonify(payload), 200

    @app.route("/api/deposit/depositions/<int:rec_id>", methods=["PUT"])
    def update_deposition(rec_id: int):
        store = _load_store()
        rec = store["records"].get(str(rec_id))
        if not rec:
            return jsonify({"message": "Not found"}), 404
        payload = request.get_json(silent=True) or {}
        metadata = payload.get("metadata", {})
        rec.setdefault("draft", {})["metadata"] = metadata
        rec["updated_at"] = _now_iso()
        _save_store(store)
        return jsonify({"id": rec_id, "metadata": metadata, "state": "draft"}), 200

    @app.route("/api/deposit/depositions/<int:rec_id>", methods=["DELETE"])
    def delete_deposition(rec_id: int):
        store = _load_store()
        if str(rec_id) in store["records"]:
            del store["records"][str(rec_id)]
            _save_store(store)
            # best-effort remove uploads
            try:
                rec_path = _record_dir(rec_id)
                if os.path.exists(rec_path):
                    # remove tree
                    for root, dirs, files in os.walk(rec_path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(rec_path)
            except Exception:
                pass
            return ("", 204)
        return jsonify({"message": "Not found"}), 404

    @app.route("/api/deposit/depositions/<int:rec_id>/actions/edit", methods=["POST"])
    def action_edit(rec_id: int):
        # In Zenodo, this switches to editable draft; here always OK
        store = _load_store()
        if str(rec_id) not in store["records"]:
            return jsonify({"message": "Not found"}), 404
        return jsonify({"id": rec_id, "state": "draft"}), 201

    @app.route("/api/deposit/depositions/<int:rec_id>/files", methods=["POST"])
    def upload_file(rec_id: int):
        store = _load_store()
        rec = store["records"].get(str(rec_id))
        if not rec:
            return jsonify({"message": "Not found"}), 404

        # Expect multipart form with 'name' and 'file'
        filename = request.form.get("name")
        file = request.files.get("file")
        if not filename or not file:
            return jsonify({"message": "Missing name or file"}), 400

        data = file.read()
        checksum = _md5_bytes(data)
        size = len(data)
        # Save to draft uploads directory
        draft_path = _draft_dir(rec_id)
        with open(os.path.join(draft_path, filename), "wb") as f:
            f.write(data)

        # Update draft file list (replace if same name)
        draft = rec.setdefault("draft", {"metadata": {}, "files": []})
        draft_files = [f for f in draft.get("files", []) if f.get("name") != filename]
        draft_files.append({"name": filename, "checksum": checksum, "size": size})
        draft["files"] = draft_files
        rec["updated_at"] = _now_iso()
        _save_store(store)

        return (
            jsonify(
                {
                    "filename": filename,
                    "checksum": checksum,
                    "size": size,
                    "links": {"self": f"/api/deposit/depositions/{rec_id}/files/{filename}"},
                }
            ),
            201,
        )

    @app.route("/api/deposit/depositions/<int:rec_id>/actions/publish", methods=["POST"])
    def publish(rec_id: int):
        store = _load_store()
        rec = store["records"].get(str(rec_id))
        if not rec:
            return jsonify({"message": "Not found"}), 404

        draft_files = rec.get("draft", {}).get("files", [])
        last_version = rec.get("versions", [])[-1] if rec.get("versions") else None

        should_bump = True
        if last_version:
            should_bump = _files_signature(draft_files) != _files_signature(last_version.get("files", []))

        if not rec.get("versions"):
            # First publish always creates v1 if there is any file or even metadata only.
            version = 1
        else:
            version = last_version["version"] + 1 if should_bump else last_version["version"]

        doi = _version_doi(rec_id, version)

        if not rec.get("versions") or should_bump:
            # persist version files
            vdir = _version_dir(rec_id, version)
            # copy from draft dir to version dir (best-effort)
            ddir = _draft_dir(rec_id)
            for f in draft_files:
                src = os.path.join(ddir, f["name"])
                dst = os.path.join(vdir, f["name"])
                try:
                    with open(src, "rb") as sf, open(dst, "wb") as df:
                        df.write(sf.read())
                except FileNotFoundError:
                    pass

            rec.setdefault("versions", []).append(
                {
                    "version": version,
                    "doi": doi,
                    "metadata": rec.get("draft", {}).get("metadata", {}),
                    "files": draft_files,
                    "published_at": _now_iso(),
                }
            )

        # Update current DOI regardless (if should_bump is False, remains the same value)
        rec["current_doi"] = doi
        rec["updated_at"] = _now_iso()
        _save_store(store)

        return jsonify({"id": rec_id, "doi": doi, "conceptdoi": rec.get("conceptdoi"), "status": "published"}), 202

    @app.route("/api/deposit/depositions/<int:rec_id>/versions", methods=["GET"])
    def list_versions(rec_id: int):
        store = _load_store()
        rec = store["records"].get(str(rec_id))
        if not rec:
            return jsonify({"message": "Not found"}), 404
        versions = rec.get("versions", [])
        return (
            jsonify(
                [
                    {
                        "version": v["version"],
                        "doi": v["doi"],
                        "published_at": v["published_at"],
                        "files": v.get("files", []),
                    }
                    for v in versions
                ]
            ),
            200,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("FAKENODO_PORT", "5055"))
    # bind to all interfaces for local dev; disable reloader to play nice when launched in background
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)

import json
import sys
from pathlib import Path
from typing import Dict

import pytest


@pytest.fixture()
def test_client(tmp_path, monkeypatch):
    """Create a Flask test client with fakenodo data directories isolated per test."""
    # Ensure repo root is on sys.path so `import app.modules.fakenodo` works
    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from app.modules.fakenodo import app as fapp

    data_dir = tmp_path / "data"
    uploads_dir = data_dir / "uploads"
    store_path = data_dir / "store.json"

    monkeypatch.setattr(fapp, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(fapp, "UPLOADS_DIR", str(uploads_dir))
    monkeypatch.setattr(fapp, "STORE_PATH", str(store_path))

    app = fapp.create_app()
    app.testing = True
    with app.test_client() as client:
        yield client


def _post_json(client, url: str, payload: Dict, status: int):
    resp = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == status, resp.data
    return resp


def test_health_and_index(test_client):
    # Health
    r = test_client.get("/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"

    # Index
    r = test_client.get("/")
    assert r.status_code == 200
    idx = r.get_json()
    assert idx["service"] == "fakenodo"
    assert "/api/deposit/depositions" in idx["api"]["list"]


def test_create_and_list_depositions(test_client):
    base = "/api/deposit/depositions"
    payload = {"metadata": {"title": "Test A", "upload_type": "dataset"}}
    r = _post_json(test_client, base, payload, status=201)
    created = r.get_json()
    assert created["id"] >= 1
    # List
    r = test_client.get(base)
    assert r.status_code == 200
    arr = r.get_json()
    assert any(item["id"] == created["id"] for item in arr)


def test_upload_publish_versioning_rules(test_client, tmp_path):
    base = "/api/deposit/depositions"

    # Create deposition
    r = _post_json(
        test_client,
        base,
        {"metadata": {"title": "Versioning", "upload_type": "dataset", "creators": [{"name": "Dario"}]}},
        status=201,
    )
    depo = r.get_json()
    dep_id = depo["id"]

    # Upload first file
    file_path = tmp_path / "a.txt"
    file_path.write_text("hello")
    r = test_client.post(
        f"{base}/{dep_id}/files",
        data={"name": "a.txt", "file": (open(file_path, "rb"), "a.txt")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 201

    # First publish -> v1
    r = test_client.post(f"{base}/{dep_id}/actions/publish")
    assert r.status_code == 202
    p1 = r.get_json()
    assert p1["doi"].endswith(".v1")

    # Update only metadata and publish again -> same DOI (no bump)
    r = test_client.put(
        f"{base}/{dep_id}",
        data=json.dumps({"metadata": {"title": "Versioning updated"}}),
        content_type="application/json",
    )
    assert r.status_code == 200
    r = test_client.post(f"{base}/{dep_id}/actions/publish")
    assert r.status_code == 202
    p2 = r.get_json()
    assert p2["doi"] == p1["doi"]

    # Upload another file and publish -> v2
    file2_path = tmp_path / "b.txt"
    file2_path.write_text("world")
    r = test_client.post(
        f"{base}/{dep_id}/files",
        data={"name": "b.txt", "file": (open(file2_path, "rb"), "b.txt")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 201
    r = test_client.post(f"{base}/{dep_id}/actions/publish")
    assert r.status_code == 202
    p3 = r.get_json()
    assert p3["doi"].endswith(".v2")
    assert p3["doi"] != p2["doi"]

    # Versions list must have 2 entries
    r = test_client.get(f"{base}/{dep_id}/versions")
    assert r.status_code == 200
    versions = r.get_json()
    assert len(versions) == 2


def test_ui_pages_render_even_with_none_doi(test_client):
    # Create a deposition without publishing so current_doi stays None
    base = "/api/deposit/depositions"
    r = _post_json(test_client, base, {"metadata": {"title": "CHEPA CREMA", "upload_type": "dataset"}}, status=201)
    dep_id = r.get_json()["id"]

    # UI index should render
    r = test_client.get("/ui")
    assert r.status_code == 200
    assert b"Depositions" in r.data

    # UI detail should render
    r = test_client.get(f"/ui/{dep_id}")
    assert r.status_code == 200
    assert b"Deposition" in r.data

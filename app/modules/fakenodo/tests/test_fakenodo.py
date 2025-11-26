import json
from flask import Flask
from app.modules.fakenodo.routes import fakenodo_module


def _make_app():
    app = Flask(__name__)
    app.register_blueprint(fakenodo_module)
    return app


def test_basic_flow():
    client = _make_app().test_client()
    base = "/fakenodo/depositions"
    r = client.post(base, data=json.dumps({"metadata": {"title": "T1"}}), content_type="application/json")
    assert r.status_code == 201
    dep = r.get_json()
    dep_id = dep["id"]
    assert dep.get("doi") is None
    r = client.post(f"{base}/{dep_id}/files", data={"name": "a.txt"})
    assert r.status_code == 201
    r = client.post(f"{base}/{dep_id}/actions/publish")
    assert r.status_code == 202
    pub = r.get_json()
    assert pub["doi"].startswith("10.5072/fakenodo.")
    r = client.get(f"{base}/{dep_id}")
    assert r.status_code == 200
    got = r.get_json()
    assert got["doi"].startswith("10.5072/fakenodo.")

def test_list_returns_created_records():
    client = _make_app().test_client()
    base = "/fakenodo/depositions"
    for i in range(3):
        client.post(base, data=json.dumps({"metadata": {"title": f"R{i}"}}), content_type="application/json")
    r = client.get(base)
    assert r.status_code == 200
    arr = r.get_json()
    assert len(arr) >= 3

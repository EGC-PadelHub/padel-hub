import json
from flask import Flask
from app.modules.fakenodo.routes import fakenodo_module


def _make_app():
    app = Flask(__name__)
    app.register_blueprint(fakenodo_module)
    return app


BASE = "/fakenodo/api/deposit/depositions"


def test_basic_flow_and_metadata_only_no_new_doi():
    client = _make_app().test_client()

    # Crear
    r = client.post(BASE, data=json.dumps({"metadata": {"title": "T1"}}), content_type="application/json")
    assert r.status_code == 201
    dep = r.get_json()
    dep_id = dep["id"]
    assert dep.get("doi") is None

    # Publicar (asigna DOI)
    r = client.post(f"{BASE}/{dep_id}/actions/publish")
    assert r.status_code == 202
    pub = r.get_json()
    first_doi = pub["doi"]
    assert first_doi.startswith("10.5072/fakenodo.")

    # Metadata only (PUT) no cambia DOI
    r = client.put(
        f"{BASE}/{dep_id}",
        data=json.dumps({"metadata": {"desc": "meta only"}}),
        content_type="application/json",
    )
    assert r.status_code == 200
    # Republishes metadata-only should keep same DOI (files_modified False)
    r = client.post(f"{BASE}/{dep_id}/actions/publish")
    assert r.status_code == 202
    pub2 = r.get_json()
    assert pub2["doi"] == first_doi


def test_files_change_creates_new_version_and_list():
    client = _make_app().test_client()

    # Crear y publicar
    r = client.post(BASE, data=json.dumps({"metadata": {"title": "R0"}}), content_type="application/json")
    dep_id = r.get_json()["id"]
    client.post(f"{BASE}/{dep_id}/actions/publish")

    # Subir archivo y republicar -> nuevo DOI/version
    r = client.post(f"{BASE}/{dep_id}/files", data={"name": "a.txt"})
    assert r.status_code == 201
    r = client.post(f"{BASE}/{dep_id}/actions/publish")
    assert r.status_code == 202
    pub = r.get_json()
    assert pub["doi"].startswith("10.5072/fakenodo.")

    # Listar versiones
    r = client.get(f"{BASE}/{dep_id}/versions")
    assert r.status_code == 200
    versions = r.get_json().get("versions", [])
    assert len(versions) >= 2  # original + nueva
    dois = [v.get("doi") for v in versions if v.get("doi")]
    assert len(set(dois)) == len(dois)

def test_list_returns_created_records():
    client = _make_app().test_client()
    for i in range(3):
        client.post(BASE, data=json.dumps({"metadata": {"title": f"R{i}"}}), content_type="application/json")
    r = client.get(BASE)
    assert r.status_code == 200
    # Zenodo API returns a list directly, not wrapped in an object
    arr = r.get_json()
    assert isinstance(arr, list)
    assert len(arr) >= 3

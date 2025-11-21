from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, Author, TournamentType
from app.modules.zenodo.services import ZenodoService


def login_client(test_client):
    resp = test_client.post(
        "/login", data={"email": "test@example.com", "password": "test1234"}, follow_redirects=True
    )
    assert resp.status_code in (200, 302)


def _create_dataset_with_metadata(user, anonymous=False, authors=None):
    # Create DSMetaData and DataSet in DB
    dsmeta = DSMetaData(title="T", description="D", tournament_type=TournamentType.NONE, anonymous=anonymous)
    db.session.add(dsmeta)
    db.session.commit()

    # Add authors if provided
    if authors:
        for a in authors:
            auth = Author(name=a.get("name"), affiliation=a.get("affiliation"), orcid=a.get("orcid"))
            dsmeta.authors.append(auth)
    db.session.commit()

    dataset = DataSet(user_id=user.id, ds_meta_data_id=dsmeta.id)
    db.session.add(dataset)
    db.session.commit()
    # reload relationship
    db.session.refresh(dataset)
    return dataset


def test_create_new_deposition_sends_anonymous_creator(monkeypatch, test_client):
    login_client(test_client)

    user = User.query.filter_by(email="test@example.com").first()
    assert user is not None

    dataset = _create_dataset_with_metadata(user, anonymous=True, authors=[{"name": "Alice"}])

    captured = {}

    class FakeResp:
        status_code = 201

        def json(self):
            return {"id": 10, "conceptrecid": 42}

    def fake_post(url, params=None, json=None, headers=None):
        captured['url'] = url
        captured['json'] = json
        captured['params'] = params
        return FakeResp()

    monkeypatch.setattr("requests.post", fake_post)

    svc = ZenodoService()
    resp = svc.create_new_deposition(dataset)

    assert resp.get("id") == 10
    assert captured
    creators = captured['json']['metadata']['creators']
    assert creators == [{"name": "Anonymous"}]


def test_create_new_deposition_includes_real_authors(monkeypatch, test_client):
    login_client(test_client)

    user = User.query.filter_by(email="test@example.com").first()
    assert user is not None

    authors = [{"name": "Alice Smith", "affiliation": "Uni", "orcid": "0000-0001"}]
    dataset = _create_dataset_with_metadata(user, anonymous=False, authors=authors)

    captured = {}

    class FakeResp:
        status_code = 201

        def json(self):
            return {"id": 11}

    def fake_post(url, params=None, json=None, headers=None):
        captured['json'] = json
        return FakeResp()

    monkeypatch.setattr("requests.post", fake_post)

    svc = ZenodoService()
    resp = svc.create_new_deposition(dataset)

    assert resp.get("id") == 11
    creators = captured['json']['metadata']['creators']
    # Should contain the real author name and optional fields
    assert any(c.get("name") == "Alice Smith" for c in creators)


def test_sync_unsynchronized_route_unsets_anonymous_and_sets_doi(monkeypatch, test_client):
    # End-to-end route test: ensure syncing an anonymous dataset toggles anonymous->False and stores DOI
    login_client(test_client)

    user = User.query.filter_by(email="test@example.com").first()
    dataset = _create_dataset_with_metadata(user, anonymous=True, authors=[{"name": "Alice"}])

    # Monkeypatch zenodo_service methods used by the route
    from app.modules.dataset import routes as ds_routes

    monkeypatch.setattr(ds_routes.zenodo_service, "test_connection", lambda: True)
    monkeypatch.setattr(ds_routes.zenodo_service, "create_new_deposition", lambda ds: {"id": 123, "conceptrecid": 123})
    monkeypatch.setattr(ds_routes.zenodo_service, "upload_file", lambda ds, depid, fm: {})
    monkeypatch.setattr(ds_routes.zenodo_service, "publish_deposition", lambda depid: {})
    monkeypatch.setattr(ds_routes.zenodo_service, "get_doi", lambda depid: "doi:10/mock")

    # Call sync endpoint
    resp = test_client.post(f"/dataset/unsynchronized/{dataset.id}/sync", follow_redirects=True)
    assert resp.status_code == 200

    # Reload dataset metadata from DB
    refreshed = DSMetaData.query.get(dataset.ds_meta_data_id)
    assert refreshed is not None
    assert refreshed.anonymous is False
    assert refreshed.dataset_doi == "doi:10/mock"

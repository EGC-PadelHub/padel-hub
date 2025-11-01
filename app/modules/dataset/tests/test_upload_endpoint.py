import io
import os
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService


def login_client(test_client):
    # login with the user created by conftest
    resp = test_client.post("/login", data={"email": "test@example.com", "password": "test1234"}, follow_redirects=True)
    assert resp.status_code in (200, 302)


def test_upload_endpoint_syntax_error(test_client):
    # Login
    login_client(test_client)

    # prepare bad CSV (unclosed quote)
    bad_csv = b'name,score\nJuan,3\nMaria,"4\nPedro,2\n'
    data = {
        'file': (io.BytesIO(bad_csv), 'bad.csv')
    }

    resp = test_client.post('/dataset/file/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400
    js = resp.get_json()
    assert js is not None
    assert 'line' in js or 'error' in js
    assert js.get('snippet') is not None

    # Check temp file was removed for the logged user
    # Find the test user in the DB
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    temp_folder = AuthenticationService().temp_folder_by_user(user)
    # The uploaded filename should not exist in temp folder
    assert not os.path.exists(os.path.join(temp_folder, 'bad.csv'))


def test_upload_endpoint_latin1_accept(test_client):
    # Login
    login_client(test_client)

    # prepare latin1 CSV content (bytes)
    latin1_content = 'name,city\nAlice,Sev\xe9lla\nBob,Malaga\n'.encode('latin-1')
    data = {
        'file': (io.BytesIO(latin1_content), 'latin1.csv')
    }

    resp = test_client.post('/dataset/file/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    js = resp.get_json()
    assert js is not None
    assert js.get('encoding') in ('latin-1', 'cp1252', 'utf-8', 'utf-8-sig', 'utf-16')

    # Cleanup: remove the saved file from temp folder
    user = User.query.filter_by(email='test@example.com').first()
    temp_folder = AuthenticationService().temp_folder_by_user(user)
    saved_path = os.path.join(temp_folder, 'latin1.csv')
    if os.path.exists(saved_path):
        os.remove(saved_path)

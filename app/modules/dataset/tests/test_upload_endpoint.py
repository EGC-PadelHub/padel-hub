import io
import os
import pytest
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


def test_upload_endpoint_success_save(test_client):
    # Login
    login_client(test_client)

    # prepare a valid UTF-8 CSV
    content = 'name,score\nJuan,3\nMaria,4\n'.encode('utf-8')
    data = {
        'file': (io.BytesIO(content), 'good.csv')
    }

    resp = test_client.post('/dataset/file/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200

    # Check the saved file exists in the user's temp folder and its contents match
    user = User.query.filter_by(email='test@example.com').first()
    temp_folder = AuthenticationService().temp_folder_by_user(user)
    saved_path = os.path.join(temp_folder, 'good.csv')
    assert os.path.exists(saved_path)
    with open(saved_path, 'rb') as fh:
        saved = fh.read()
    assert saved == content

    # Cleanup
    os.remove(saved_path)


@pytest.mark.parametrize('text,encoding,filename', [
    # latin-1 with accented characters
    ('name,city\nAlice,Sev\xe9lla\nBob,Malaga\n', 'latin-1', 'latin1_chars.csv'),
    # cp1252 with euro sign
    ('name,price\nItem,\u20ac10\n', 'cp1252', 'cp1252_euro.csv'),
    # utf-8 with emoji
    ('name,fun\nA,😊\nB,🎾\n', 'utf-8', 'emoji.csv'),
    # utf-8 with Cyrillic
    ('name,city\nIvan,Москва\nOlga,Киев\n', 'utf-8', 'cyrillic.csv'),
    # utf-8 with Chinese
    ('name,city\nXiao,北京\nYue,上海\n', 'utf-8', 'chinese.csv'),
])
def test_upload_endpoint_encoding_variants(test_client, text, encoding, filename):
    """Send CSVs encoded with different encodings and characters and assert upload succeeds
    and the service reports an encoding (one of the accepted ones).
    """
    login_client(test_client)

    # If the input text is expressed with escape sequences (like \xe9), we need to
    # convert to bytes using the target encoding. If it's a Python string with
    # actual unicode characters, encoding will work directly.
    if isinstance(text, bytes):
        payload = text
    else:
        # Try to encode the Python string with the requested encoding. If that fails
        # (e.g. the string contains characters not representable in that codec),
        # attempt to interpret escape sequences (useful when literals contain \x.. escapes),
        # and finally fall back to UTF-8 bytes so the test still sends valid data.
        try:
            payload = text.encode(encoding)
        except UnicodeEncodeError:
            try:
                decoded = text.encode('utf-8').decode('unicode_escape')
                payload = decoded.encode(encoding)
            except Exception:
                payload = text.encode('utf-8')

    data = {'file': (io.BytesIO(payload), filename)}
    resp = test_client.post('/dataset/file/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    js = resp.get_json()
    assert js is not None
    # The service typically replies with a detected/accepted encoding; accept common possibilities
    assert js.get('encoding') in ('latin-1', 'cp1252', 'utf-8', 'utf-8-sig', 'utf-16')

    # Cleanup saved file if present
    user = User.query.filter_by(email='test@example.com').first()
    temp_folder = AuthenticationService().temp_folder_by_user(user)
    saved_path = os.path.join(temp_folder, filename)
    if os.path.exists(saved_path):
        os.remove(saved_path)

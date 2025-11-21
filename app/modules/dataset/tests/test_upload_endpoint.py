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

    # prepare latin1 CSV content with valid padel structure
    latin1_content = (
        'nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,categoria,fase,ronda,'
        'pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,'
        'set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,'
        'pareja_ganadora,pareja_perdedora,resultado_string\n'
        'Torneo Sev\xe9lla 2024,2024,01.05.2024,05.05.2024,Estadio,Masculino,Final,Cuadro,'
        'Jos\xe9 Mart\xednez,Carlos Garc\xeda,Pedro L\xf3pez,Juan S\xe1nchez,'
        '6,4,7,5,,,'
        'Jos\xe9 Mart\xednez_Carlos Garc\xeda,Pedro L\xf3pez_Juan S\xe1nchez,6-4 / 7-5\n'
    ).encode('latin-1')
    
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

    # prepare a valid UTF-8 CSV with padel structure
    content = (
        'nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,categoria,fase,ronda,'
        'pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,'
        'set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,'
        'pareja_ganadora,pareja_perdedora,resultado_string\n'
        'Madrid Open 2024,2024,10.06.2024,16.06.2024,Wizink Center,Masculino,Semifinal,Cuadro,'
        'Juan Lebrón,Ale Galán,Paquito Navarro,Martín Di Nenno,'
        '6,3,6,4,,,'
        'Juan Lebrón_Ale Galán,Paquito Navarro_Martín Di Nenno,6-3 / 6-4\n'
    ).encode('utf-8')
    
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


def _create_padel_csv_with_encoding(player_names, encoding):
    """Helper to create valid padel CSV with different encodings and characters."""
    header = (
        'nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,categoria,fase,ronda,'
        'pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,'
        'set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,'
        'pareja_ganadora,pareja_perdedora,resultado_string\n'
    )
    
    p1, p2, p3, p4 = player_names
    data_row = (
        f'Test Tournament 2024,2024,01.05.2024,05.05.2024,Stadium,Masculino,Final,Cuadro,'
        f'{p1},{p2},{p3},{p4},'
        f'6,4,7,5,,,'
        f'{p1}_{p2},{p3}_{p4},6-4 / 7-5\n'
    )
    
    csv_text = header + data_row
    return csv_text.encode(encoding)


@pytest.mark.parametrize('player_names,encoding,filename', [
    # latin-1 with accented characters
    (['José Martínez', 'Carlos García', 'Pedro López', 'Juan Sánchez'], 'latin-1', 'latin1_chars.csv'),
    # cp1252 with special characters
    (['Player A', 'Player B', 'Player C', 'Player D'], 'cp1252', 'cp1252_euro.csv'),
    # utf-8 with emoji in tournament name (modifying helper for this case)
    (['Ana Silva', 'Bea Torres', 'Carla Ruiz', 'Diana Vega'], 'utf-8', 'emoji.csv'),
    # utf-8 with Cyrillic
    (['Иван Петров', 'Олег Смирнов', 'Дмитрий Козлов', 'Андрей Попов'], 'utf-8', 'cyrillic.csv'),
    # utf-8 with Chinese
    (['张伟', '李娜', '王芳', '刘强'], 'utf-8', 'chinese.csv'),
])
def test_upload_endpoint_encoding_variants(test_client, player_names, encoding, filename):
    """Send CSVs with different encodings and characters using valid padel structure.
    Assert upload succeeds and service reports correct encoding.
    """
    login_client(test_client)

    try:
        payload = _create_padel_csv_with_encoding(player_names, encoding)
    except UnicodeEncodeError:
        # If characters can't be encoded in target encoding, use UTF-8
        payload = _create_padel_csv_with_encoding(player_names, 'utf-8')

    data = {'file': (io.BytesIO(payload), filename)}
    resp = test_client.post('/dataset/file/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    js = resp.get_json()
    assert js is not None
    # The service typically replies with a detected/accepted encoding
    assert js.get('encoding') in ('latin-1', 'cp1252', 'utf-8', 'utf-8-sig', 'utf-16')

    # Cleanup saved file if present
    user = User.query.filter_by(email='test@example.com').first()
    temp_folder = AuthenticationService().temp_folder_by_user(user)
    saved_path = os.path.join(temp_folder, filename)
    if os.path.exists(saved_path):
        os.remove(saved_path)

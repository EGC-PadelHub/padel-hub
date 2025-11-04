import pytest

"""
Test configuration for app modules.

Note: This file attempts to import the full application which may require
optional dev dependencies (e.g., python-dotenv). To keep lightweight unit
tests (like fakenodo) runnable without the full stack, we gracefully
degrade when imports fail and skip the app-coupled fixtures.
"""

_APP_IMPORT_OK = True
try:
    from app import create_app, db  # type: ignore
    from app.modules.auth.models import User  # type: ignore
except Exception as exc:  # pragma: no cover - only triggers in minimal envs
    _APP_IMPORT_OK = False
    _APP_IMPORT_ERROR = exc


@pytest.fixture(scope="session")
def test_app():
    """Create and configure a new app instance for each test session."""
    if not _APP_IMPORT_OK:
        pytest.skip(f"Skipping app-coupled fixtures: {_APP_IMPORT_ERROR}")
    test_app = create_app("testing")

    with test_app.app_context():
        # Imprimir los blueprints registrados
        print("TESTING SUITE (1): Blueprints registrados:", test_app.blueprints)
        yield test_app


@pytest.fixture(scope="module")
def test_client(test_app):
    if not _APP_IMPORT_OK:
        pytest.skip(f"Skipping app-coupled fixtures: {_APP_IMPORT_ERROR}")

    with test_app.test_client() as testing_client:
        with test_app.app_context():
            print("TESTING SUITE (2): Blueprints registrados:", test_app.blueprints)

            db.drop_all()
            db.create_all()
            """
            The test suite always includes the following user in order to avoid repetition
            of its creation
            """
            user_test = User(email="test@example.com", password="test1234")
            db.session.add(user_test)
            db.session.commit()

            print("Rutas registradas:")
            for rule in test_app.url_map.iter_rules():
                print(rule)
            yield testing_client

            db.session.remove()
            db.drop_all()


@pytest.fixture(scope="function")
def clean_database():
    if not _APP_IMPORT_OK:
        pytest.skip(f"Skipping app-coupled fixtures: {_APP_IMPORT_ERROR}")
    db.session.remove()
    db.drop_all()
    db.create_all()
    yield
    db.session.remove()
    db.drop_all()
    db.create_all()


def login(test_client, email, password):
    """
    Authenticates the user with the credentials provided.

    Args:
        test_client: Flask test client.
        email (str): User's email address.
        password (str): User's password.

    Returns:
        response: POST login request response.
    """
    response = test_client.post("/login", data=dict(email=email, password=password), follow_redirects=True)
    return response


def logout(test_client):
    """
    Logs out the user.

    Args:
        test_client: Flask test client.

    Returns:
        response: Response to GET request to log out.
    """
    return test_client.get("/logout", follow_redirects=True)

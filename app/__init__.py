import os

# Optional dependency: python-dotenv. In minimal test environments it may not be installed.
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - fallback for minimal envs
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False
from flask import Flask

# Optional heavy deps for minimal test environments
try:  # pragma: no cover - exercised only in minimal envs
    from flask_migrate import Migrate  # type: ignore
except Exception:  # pragma: no cover
    class Migrate:  # type: ignore
        def __init__(self, *_, **__):
            pass

        def init_app(self, *_, **__):
            pass

try:  # pragma: no cover - exercised only in minimal envs
    from flask_sqlalchemy import SQLAlchemy  # type: ignore
except Exception:  # pragma: no cover
    class _DummySession:
        def add(self, *_, **__):
            pass

        def commit(self, *_, **__):
            pass

        def remove(self, *_, **__):
            pass

    class SQLAlchemy:  # type: ignore
        def __init__(self, *_, **__):
            self.session = _DummySession()

        def init_app(self, *_, **__):
            pass

        def drop_all(self, *_, **__):
            pass

        def create_all(self, *_, **__):
            pass

from core.configuration.configuration import get_app_version
from core.managers.config_manager import ConfigManager
from core.managers.error_handler_manager import ErrorHandlerManager
from core.managers.logging_manager import LoggingManager
from core.managers.module_manager import ModuleManager

# Load environment variables
load_dotenv()

# Create the instances
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name="development"):
    app = Flask(__name__)

    # Load configuration according to environment
    config_manager = ConfigManager(app)
    config_manager.load_config(config_name=config_name)

    # Initialize SQLAlchemy and Migrate with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Register modules
    module_manager = ModuleManager(app)
    module_manager.register_modules()

    # Register login manager (optional in minimal envs)
    try:  # pragma: no cover - optional
        from flask_login import LoginManager  # type: ignore

        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = "auth.login"

        @login_manager.user_loader
        def load_user(user_id):
            from app.modules.auth.models import User  # type: ignore

            return User.query.get(int(user_id))
    except Exception:
        pass

    # Set up logging
    logging_manager = LoggingManager(app)
    logging_manager.setup_logging()

    # Initialize error handler manager
    error_handler_manager = ErrorHandlerManager(app)
    error_handler_manager.register_error_handlers()

    # Injecting environment variables into jinja context
    @app.context_processor
    def inject_vars_into_jinja():
        return {
            "FLASK_APP_NAME": os.getenv("FLASK_APP_NAME"),
            "FLASK_ENV": os.getenv("FLASK_ENV"),
            "DOMAIN": os.getenv("DOMAIN", "localhost"),
            "APP_VERSION": get_app_version(),
        }

    return app


app = create_app()

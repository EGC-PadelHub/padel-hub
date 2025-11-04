import os

# Optional dependency: python-dotenv
try:  # pragma: no cover - optional in minimal envs
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

load_dotenv()


def uploads_folder_name():
    return os.getenv("UPLOADS_DIR", "uploads")


def get_app_version():
    version_file_path = os.path.join(os.getenv("WORKING_DIR", ""), ".version")
    try:
        with open(version_file_path, "r") as file:
            return file.readline().strip()
    except FileNotFoundError:
        return "unknown"


def is_develop():
    return os.getenv("FLASK_ENV") == "development"


def is_production():
    return os.getenv("FLASK_ENV") == "production"

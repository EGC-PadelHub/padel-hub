import logging
import os

import requests
from dotenv import load_dotenv
from flask import Response, jsonify
from flask_login import current_user

from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from app.modules.zenodo.repositories import ZenodoRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService
from app.modules.dataset.repositories import DSMetaDataRepository

logger = logging.getLogger(__name__)

load_dotenv()


class ZenodoService(BaseService):

    def get_zenodo_url(self):
        # Decide which API URL to use for uploads. By default we force fakenodo for dataset uploads
        # to avoid ever sending dataset uploads to the real Zenodo API from this app.
        # Control via env var UPLOADS_USE_FAKENODO_ONLY (default: true). When enabled, prefer
        # FAKENODO_URL (if set) or a sensible local default.
        force_fakenodo = os.getenv("UPLOADS_USE_FAKENODO_ONLY", "true").lower() in ("1", "true", "yes")
        fakenodo_url = os.getenv("FAKENODO_URL")
        default_fakenodo = "http://127.0.0.1:5055/api/deposit/depositions"

        if force_fakenodo:
            return fakenodo_url or default_fakenodo

        # Backwards-compatible behaviour if forcing is disabled: keep previous logic
        # Prefer local fakenodo if configured
        if fakenodo_url:
            return fakenodo_url

        # If no explicit fakenodo URL provided, but no access token either, prefer a local fakenodo
        # default. This avoids 403 Permission denied when running locally without Zenodo creds.
        zenodo_token = os.getenv("ZENODO_ACCESS_TOKEN")

        # If user provided explicit ZENODO_API_URL via env, respect it
        explicit = os.getenv("ZENODO_API_URL")
        if explicit:
            return explicit

        FLASK_ENV = os.getenv("FLASK_ENV", "development")
        if not zenodo_token:
            # No token available: try using local fakenodo default
            return default_fakenodo

        # Otherwise, use Zenodo sandbox in development, or production endpoint
        if FLASK_ENV == "development":
            return os.getenv("ZENODO_API_URL", "https://sandbox.zenodo.org/api/deposit/depositions")
        elif FLASK_ENV == "production":
            return os.getenv("ZENODO_API_URL", "https://zenodo.org/api/deposit/depositions")
        else:
            return os.getenv("ZENODO_API_URL", "https://sandbox.zenodo.org/api/deposit/depositions")

    def get_zenodo_access_token(self):
        return os.getenv("ZENODO_ACCESS_TOKEN")

    def __init__(self):
        super().__init__(ZenodoRepository())
        self.ZENODO_ACCESS_TOKEN = self.get_zenodo_access_token()
        self.ZENODO_API_URL = self.get_zenodo_url()
        self.headers = {"Content-Type": "application/json"}
        # Only include access_token param if we have a token AND we're not using fakenodo.
        # When using a local fakenodo we avoid sending access tokens.
        fakenodo_candidates = [os.getenv("FAKENODO_URL"), "http://127.0.0.1:5055/api/deposit/depositions"]
        using_fakenodo = any(self.ZENODO_API_URL and cand and cand in self.ZENODO_API_URL for cand in fakenodo_candidates)
        if self.ZENODO_ACCESS_TOKEN and not using_fakenodo:
            self.params = {"access_token": self.ZENODO_ACCESS_TOKEN}
        else:
            self.params = {}

    def test_connection(self) -> bool:
        """
        Test the connection with Zenodo.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        response = requests.get(self.ZENODO_API_URL, params=self.params, headers=self.headers)
        return response.status_code == 200

    def test_full_connection(self) -> Response:
        """
        Test the connection with Zenodo by creating a deposition, uploading an empty test file, and deleting the
        deposition.

        Returns:
            bool: True if the connection, upload, and deletion are successful, False otherwise.
        """

        success = True

        # Create a test file
        working_dir = os.getenv("WORKING_DIR", "")
        file_path = os.path.join(working_dir, "test_file.txt")
        with open(file_path, "w") as f:
            f.write("This is a test file with some content.")

        messages = []  # List to store messages

        # Step 1: Create a deposition on Zenodo
        data = {
            "metadata": {
                "title": "Test Deposition",
                "upload_type": "dataset",
                "description": "This is a test deposition created via Zenodo API",
                "creators": [{"name": "John Doe"}],
            }
        }

        response = requests.post(self.ZENODO_API_URL, json=data, params=self.params, headers=self.headers)

        if response.status_code != 201:
            return jsonify(
                {
                    "success": False,
                    "messages": f"Failed to create test deposition on Zenodo. Response code: {response.status_code}",
                }
            )

        deposition_id = response.json()["id"]

        # Step 2: Upload an empty file to the deposition
        data = {"name": "test_file.txt"}
        files = {"file": open(file_path, "rb")}
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(publish_url, params=self.params, data=data, files=files)
        files["file"].close()  # Close the file after uploading

        logger.info(f"Publish URL: {publish_url}")
        logger.info(f"Params: {self.params}")
        logger.info(f"Data: {data}")
        logger.info(f"Files: {files}")
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.content}")

        if response.status_code != 201:
            messages.append(f"Failed to upload test file to Zenodo. Response code: {response.status_code}")
            success = False

        # Step 3: Delete the deposition
        response = requests.delete(f"{self.ZENODO_API_URL}/{deposition_id}", params=self.params)

        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": success, "messages": messages})

    def get_all_depositions(self) -> dict:
        """
        Get all depositions from Zenodo.

        Returns:
            dict: The response in JSON format with the depositions.
        """
        response = requests.get(self.ZENODO_API_URL, params=self.params, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Failed to get depositions")
        return response.json()

    def create_new_deposition(self, dataset: DataSet) -> dict:
        """
        Create a new deposition in Zenodo.

        Args:
            dataset (DataSet): The DataSet object containing the metadata of the deposition.

        Returns:
            dict: The response in JSON format with the details of the created deposition.
        """

        logger.info("Dataset sending to Zenodo...")
        logger.info(f"Publication type...{dataset.ds_meta_data.publication_type.value}")

        metadata = {
            "title": dataset.ds_meta_data.title,
            "upload_type": "dataset" if dataset.ds_meta_data.publication_type.value == "none" else "publication",
            "publication_type": (
                dataset.ds_meta_data.publication_type.value
                if dataset.ds_meta_data.publication_type.value != "none"
                else None
            ),
            "description": dataset.ds_meta_data.description,
            # If the dataset metadata marks the dataset as anonymous, avoid exposing real authors here
            # Build creators list. If anonymous -> send Anonymous. Otherwise try to obtain authors
            # from the provided dataset; if they are not loaded for some reason, fetch them
            # from the DSMetaData repository as a fallback.
            "creators": (lambda: (
                [{"name": "Anonymous"}]
                if getattr(dataset.ds_meta_data, "anonymous", False)
                else [
                    {
                        "name": author.name,
                        **({"affiliation": author.affiliation} if author.affiliation else {}),
                        **({"orcid": author.orcid} if author.orcid else {}),
                    }
                    for author in (
                        getattr(dataset.ds_meta_data, "authors", None)
                        or DSMetaDataRepository().get_by_id(dataset.ds_meta_data_id).authors
                    )
                ]
            ))(),
            "keywords": (
                ["padelhub"] if not dataset.ds_meta_data.tags else dataset.ds_meta_data.tags.split(", ") + ["padelhub"]
            ),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

        # Log creators payload for debugging (helps ensure we are not sending 'Anonymous')
        try:
            logger.debug("Zenodo metadata creators payload: %s", metadata.get("creators"))
        except Exception:
            pass

        data = {"metadata": metadata}

        response = requests.post(self.ZENODO_API_URL, params=self.params, json=data, headers=self.headers)
        if response.status_code != 201:
            error_message = f"Failed to create deposition. Error details: {response.json()}"
            raise Exception(error_message)
        return response.json()

    def upload_file(self, dataset: DataSet, deposition_id: int, feature_model: FeatureModel, user=None) -> dict:
        """
        Upload a file to a deposition in Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.
            feature_model (FeatureModel): The FeatureModel object representing the feature model.
            user (FeatureModel): The User object representing the file owner.

        Returns:
            dict: The response in JSON format with the details of the uploaded file.
        """
        uvl_filename = feature_model.fm_meta_data.uvl_filename
        data = {"name": uvl_filename}
        user_id = current_user.id if user is None else user.id
        file_path = os.path.join(uploads_folder_name(), f"user_{str(user_id)}", f"dataset_{dataset.id}/", uvl_filename)
        files = {"file": open(file_path, "rb")}

        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(publish_url, params=self.params, data=data, files=files)
        if response.status_code != 201:
            error_message = f"Failed to upload files. Error details: {response.json()}"
            raise Exception(error_message)
        return response.json()

    def publish_deposition(self, deposition_id: int) -> dict:
        """
        Publish a deposition in Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            dict: The response in JSON format with the details of the published deposition.
        """
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/actions/publish"
        response = requests.post(publish_url, params=self.params, headers=self.headers)
        if response.status_code != 202:
            raise Exception("Failed to publish deposition")
        return response.json()

    def get_deposition(self, deposition_id: int) -> dict:
        """
        Get a deposition from Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            dict: The response in JSON format with the details of the deposition.
        """
        deposition_url = f"{self.ZENODO_API_URL}/{deposition_id}"
        response = requests.get(deposition_url, params=self.params, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Failed to get deposition")
        return response.json()

    def get_doi(self, deposition_id: int) -> str:
        """
        Get the DOI of a deposition from Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            str: The DOI of the deposition.
        """
        return self.get_deposition(deposition_id).get("doi")

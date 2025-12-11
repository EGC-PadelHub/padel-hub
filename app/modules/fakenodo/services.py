"""Fakenodo service for local/development dataset synchronization.

This service provides a simple in-memory mock of Zenodo API functionality
without requiring external API calls or tokens. It communicates with the
fakenodo blueprint API endpoints running in the same Flask application.
"""

import itertools
import logging
import os
from flask_login import current_user

from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


class FakenodoService(BaseService):
    """Service for interacting with the in-process fakenodo API."""

    def __init__(self):
        super().__init__(None)  # No repository needed
        
        # Counter for generating fake DOIs
        self._counter = itertools.count(1)
        
        # Set dummy URL for compatibility (not actually used)
        self.FAKENODO_API_URL = "http://fake-zenodo-simulator/api"
        self.ZENODO_API_URL = self.FAKENODO_API_URL
        self.headers = {"Content-Type": "application/json"}
        logger.info("FakenodoService initialized - NO REAL API CALLS, pure simulation")

    def test_connection(self) -> bool:
        """Test connection to fakenodo API - always returns True (fake)."""
        logger.info("Fakenodo connection test - returning True (simulated)")
        return True

    def create_new_deposition(self, dataset: DataSet) -> dict:
        """Create a fake deposition - NO REAL API CALL."""
        deposition_id = next(self._counter)
        logger.info(f"Creating FAKE deposition for dataset {dataset.id} with ID {deposition_id}")
        
        # Return fake response matching Zenodo format
        return {
            "id": deposition_id,
            "conceptrecid": deposition_id,
            "metadata": {
                "title": dataset.ds_meta_data.title,
                "description": dataset.ds_meta_data.description,
            },
            "files": [],
            "doi": None,
            "published": False,
        }

    def upload_file(self, dataset: DataSet, deposition_id: int, feature_model: FeatureModel, user=None) -> dict:
        """Fake upload file - NO REAL API CALL."""
        uvl_filename = feature_model.fm_meta_data.uvl_filename
        logger.info(f"FAKE upload of {uvl_filename} to deposition {deposition_id}")
        
        # Return fake success response
        return {
            "filename": uvl_filename,
            "link": f"http://fake-zenodo.org/files/{deposition_id}/{uvl_filename}"
        }

    def publish_deposition(self, deposition_id: int) -> dict:
        """Fake publish - NO REAL API CALL."""
        fake_doi = f"10.5072/fakenodo.{deposition_id}"
        logger.info(f"FAKE publish of deposition {deposition_id} with DOI {fake_doi}")
        
        # Return fake published response
        return {
            "id": deposition_id,
            "conceptrecid": deposition_id,
            "doi": fake_doi,
            "published": True,
        }

    def get_deposition(self, deposition_id: int) -> dict:
        """Fake get deposition - NO REAL API CALL."""
        logger.info(f"FAKE get deposition {deposition_id}")
        
        return {
            "id": deposition_id,
            "conceptrecid": deposition_id,
            "doi": f"10.5072/fakenodo.{deposition_id}",
            "published": True,
        }

    def get_doi(self, deposition_id: int) -> str:
        """Get fake DOI - NO REAL API CALL."""
        fake_doi = f"10.5072/fakenodo.{deposition_id}"
        logger.info(f"FAKE DOI returned: {fake_doi}")
        return fake_doi
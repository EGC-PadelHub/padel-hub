"""Base dataset behaviour interface.

This is a light-weight, non-ORM class that encapsulates dataset-type-specific
validation and behaviour. Database models remain in `models.py` (to avoid
schema changes in this patch). Concrete dataset types should inherit from
BaseDataset and implement/extend behaviour.
"""
from typing import Any, Dict, List, Optional


class BaseDataset:
    """Abstract dataset behaviour.

    Implementations should provide:
      - validate_files(files: List[str]) -> Dict[str, Any]
      - preview(file_path: str, rows: int = 5) -> List[List[str]]
    """

    type_name: str = "base"

    def __init__(self, dataset_model: Optional[Any] = None):
        # dataset_model is the ORM object (DataSet) or None for pure behaviour
        self.model = dataset_model

    def validate_files(self, files: List[str]) -> Dict[str, Any]:
        """Validate list of file paths. Return a dict with `valid` and `errors`.

        files: full file paths on disk
        """
        return {"valid": True, "errors": []}

    def preview(self, file_path: str, rows: int = 5) -> List[List[str]]:
        """Return a small preview (list of rows) for the given file path."""
        raise NotImplementedError()

    def common_fields(self) -> Dict[str, Any]:
        """Return the common metadata fields used in templates (title, authors...)."""
        if not self.model:
            return {}
        meta = getattr(self.model, "ds_meta_data", None)
        if not meta:
            return {}
        return {
            "title": meta.title,
            "description": meta.description,
            "authors": [a.name for a in meta.authors],
        }

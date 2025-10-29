"""CSV / Tabular dataset behaviour.

This contains logic specific to tabular datasets (CSV). It validates file
extensions and provides a small preview (head rows) to render in templates.
"""
from typing import List, Dict, Any
import csv
import os

from .base import BaseDataset


class TabularDataset(BaseDataset):
    type_name = "tabular"

    def validate_files(self, files: List[str]) -> Dict[str, Any]:
        errors = []
        for f in files:
            if not os.path.exists(f):
                errors.append(f"File not found: {f}")
                continue
            _, ext = os.path.splitext(f)
            if ext.lower() != ".csv":
                errors.append(f"Invalid extension for tabular dataset: {f}")
        return {"valid": len(errors) == 0, "errors": errors}

    def preview(self, file_path: str, rows: int = 5) -> List[List[str]]:
        """Return first `rows` rows from the CSV as lists of strings.

        This uses the stdlib csv module (no hard dependency on pandas).
        """
        preview_rows: List[List[str]] = []
        if not os.path.exists(file_path):
            return preview_rows

        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            for i, row in enumerate(reader):
                preview_rows.append(row)
                if i + 1 >= rows:
                    break

        return preview_rows

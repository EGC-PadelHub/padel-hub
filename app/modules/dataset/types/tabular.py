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

    def validate_syntax(self, file_path: str) -> Dict[str, Any]:
        """Validate CSV syntax and return a dict with results.

        Returns:
            {"valid": True, "encoding": encoding}
        or
            {"valid": False, "encoding": attempted_encoding, "line": lineno, "message": str}
        """
        encodings_to_try = ["utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252"]
        import csv

        if not os.path.exists(file_path):
            return {"valid": False, "message": "File not found"}

        # Try reading the file with different encodings and parse incrementally
        for enc in encodings_to_try:
            try:
                with open(file_path, "r", encoding=enc, newline="") as f:
                    reader = csv.reader(f)
                    for lineno, _row in enumerate(reader, start=1):
                        # just iterate to trigger parsing; no need to store rows
                        pass
                # If we got here without exceptions, file parsed OK with this encoding
                # Additional heuristic: check for unbalanced quotes which csv.reader
                # may not always surface as csv.Error (e.g. missing closing quote at EOF).
                try:
                    with open(file_path, "r", encoding=enc, errors="replace") as ff:
                        all_text = ff.read()
                        total_quotes = all_text.count('"')
                        if total_quotes % 2 != 0:
                            # Find the line where quotes become unbalanced
                            cum = 0
                            for idx, line in enumerate(all_text.splitlines(), start=1):
                                cum += line.count('"')
                                if cum % 2 != 0:
                                    error_line = idx
                                    break
                            else:
                                error_line = 1
                            # Provide snippet +/-3 lines
                            lines = all_text.splitlines()
                            start = max(0, error_line - 4)
                            end = min(len(lines), error_line + 3)
                            snippet = "\n".join(lines[start:end])
                            # Provide the 1-based starting line number for the snippet
                            snippet_start = start + 1
                            return {
                                "valid": False,
                                "encoding": enc,
                                "line": error_line,
                                "message": "Unbalanced quotes detected",
                                "snippet": snippet,
                                "snippet_start": snippet_start,
                            }
                except Exception:
                    # If snippet extraction fails, still consider the file valid for this encoding
                    pass

                return {"valid": True, "encoding": enc}
            except (UnicodeDecodeError, UnicodeError):
                # Try next encoding
                continue
            except csv.Error as e:
                # csv.Error doesn't always provide the line, so we return the lineno we reached
                # The enumerate will have set lineno to the last parsed line; include message
                # Try to provide a small snippet around the error line to help the user
                snippet = None
                try:
                    with open(file_path, "r", encoding=enc, errors="replace") as ff:
                        all_lines = ff.read().splitlines()
                        # lineno is the line where error occurred (or last parsed). Provide context +/-3 lines
                        start = max(0, lineno - 4)
                        end = min(len(all_lines), lineno + 3)
                        # join with newline for display
                        snippet = "\n".join(all_lines[start:end])
                        # snippet_start is 1-based line number of the first line in the snippet
                        snippet_start = start + 1
                except Exception:
                    snippet = None

                return {
                    "valid": False,
                    "encoding": enc,
                    "line": lineno,
                    "message": str(e),
                    "snippet": snippet,
                    "snippet_start": snippet_start,
                }
            except Exception as e:
                # Other errors (IO etc.) — surface as general error
                return {"valid": False, "encoding": enc, "message": str(e)}

        # If no encoding worked, return a decode error
        return {"valid": False, "message": "Unable to decode file with tried encodings"}

"""CSV / Tabular dataset behaviour.

This contains logic specific to tabular datasets (CSV). It validates file
extensions and provides a small preview (head rows) to render in templates.
"""
from typing import List, Dict, Any
import csv
import os
import re


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

    def validate_padel_structure(self, file_path: str) -> Dict[str, Any]:
        """Validate that the CSV has the specific structure for padel match datasets.

        Returns:
            {"valid": True} if structure is correct
        or
            {"valid": False, "errors": [...], "required_columns": [...]}
        """
        REQUIRED_COLUMNS = [
            'nombre_torneo', 'anio_torneo', 'fecha_inicio_torneo', 'fecha_final_torneo',
            'pista_principal', 'categoria', 'fase', 'ronda',
            'pareja1_jugador1', 'pareja1_jugador2', 'pareja2_jugador1', 'pareja2_jugador2',
            'set1_pareja1', 'set1_pareja2', 'set2_pareja1', 'set2_pareja2',
            'set3_pareja1', 'set3_pareja2',
            'pareja_ganadora', 'pareja_perdedora', 'resultado_string'
        ]

        VALID_CATEGORIES = [
            'Masculino', 'Femenino', 'Mixed',
            'masculino', 'femenino', 'mixed',
            'Mixto', 'mixto'  # Spanish variant for Mixed
        ]

        if not os.path.exists(file_path):
            return {"valid": False, "errors": ["File not found"], "required_columns": REQUIRED_COLUMNS}

        errors = []

        # First, detect encoding
        encodings_to_try = ["utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252"]
        encoding = "utf-8"
        for enc in encodings_to_try:
            try:
                with open(file_path, "r", encoding=enc, newline="") as f:
                    f.read(1024)
                encoding = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        try:
            with open(file_path, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                if not headers:
                    return {
                        "valid": False,
                        "errors": ["CSV file has no headers"],
                        "required_columns": REQUIRED_COLUMNS
                    }

                # Check for missing required columns
                missing_columns = [col for col in REQUIRED_COLUMNS if col not in headers]
                if missing_columns:
                    errors.append(f"Missing required columns: {', '.join(missing_columns)}")

                # Check for extra columns (warning, not error)
                extra_columns = [col for col in headers if col not in REQUIRED_COLUMNS]
                if extra_columns:
                    errors.append(f"Warning: Extra columns found: {', '.join(extra_columns)}")

                # Validate data in each row
                row_number = 1
                for row in reader:
                    row_number += 1

                    # Validate year is numeric
                    if 'anio_torneo' in row and row['anio_torneo']:
                        try:
                            year = int(row['anio_torneo'])
                            if year < 1900 or year > 2100:
                                errors.append(
                                    f"Row {row_number}: Invalid year '{year}' (must be between 1900-2100)"
                                )
                        except ValueError:
                            errors.append(
                                f"Row {row_number}: 'anio_torneo' must be numeric, got '{row['anio_torneo']}'"
                            )

                    # Validate dates format (DD.MM.YYYY)
                    for date_field in ['fecha_inicio_torneo', 'fecha_final_torneo']:
                        if date_field in row and row[date_field]:
                            date_pattern = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')
                            if not date_pattern.match(row[date_field]):
                                errors.append(
                                    f"Row {row_number}: '{date_field}' must be in DD.MM.YYYY format, "
                                    f"got '{row[date_field]}'"
                                )

                    # Validate category
                    if 'categoria' in row and row['categoria']:
                        if row['categoria'] not in VALID_CATEGORIES:
                            errors.append(
                                f"Row {row_number}: 'categoria' must be one of {VALID_CATEGORIES}, "
                                f"got '{row['categoria']}'"
                            )

                    # Validate set scores are numeric (when present)
                    set_fields = [
                        'set1_pareja1', 'set1_pareja2', 'set2_pareja1', 'set2_pareja2',
                        'set3_pareja1', 'set3_pareja2'
                    ]
                    for set_field in set_fields:
                        if set_field in row and row[set_field]:
                            try:
                                score = int(row[set_field])
                                if score < 0 or score > 99:
                                    errors.append(
                                        f"Row {row_number}: '{set_field}' score out of range, got {score}"
                                    )
                            except ValueError:
                                errors.append(
                                    f"Row {row_number}: '{set_field}' must be numeric, "
                                    f"got '{row[set_field]}'"
                                )

                    # Validate that player names are not empty
                    player_fields = [
                        'pareja1_jugador1', 'pareja1_jugador2',
                        'pareja2_jugador1', 'pareja2_jugador2'
                    ]
                    for player_field in player_fields:
                        if player_field in row and not row[player_field]:
                            errors.append(f"Row {row_number}: '{player_field}' cannot be empty")

                    # Only show first 10 errors to avoid overwhelming output
                    if len(errors) >= 10:
                        errors.append("... (more errors may exist, showing first 10)")
                        break

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Error reading CSV: {str(e)}"],
                "required_columns": REQUIRED_COLUMNS
            }

        if errors:
            return {
                "valid": False,
                "errors": errors,
                "required_columns": REQUIRED_COLUMNS
            }

        return {"valid": True}

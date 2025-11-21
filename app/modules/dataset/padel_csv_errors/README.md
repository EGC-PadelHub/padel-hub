# CSV Errors Padel - Test Files

This directory contains CSV files with intentional errors for testing padel structure validation.

## Files Description

### Structure Validation Errors

1. **error_missing_columns.csv**
   - Missing most required padel columns
   - Only has: nombre_torneo, anio_torneo, categoria
   - Should trigger: "Missing required columns" error

2. **error_invalid_year.csv**
   - Contains non-numeric year values
   - Values: "NotAYear", "TwoThousand"
   - Should trigger: "'anio_torneo' must be numeric" error on rows 2 and 3

3. **error_invalid_date_format.csv**
   - Contains dates in wrong format (YYYY-MM-DD and DD/MM/YYYY instead of DD.MM.YYYY)
   - Values: "2024-09-02", "15/04/2023"
   - Should trigger: "must be in DD.MM.YYYY format" error on rows 2 and 3

4. **error_invalid_category.csv**
   - Contains invalid category values
   - Values: "InvalidCategory", "Unisex"
   - Should trigger: "'categoria' must be one of [...]" error on rows 2 and 3

5. **error_non_numeric_score.csv**
   - Contains text instead of numbers in set scores
   - Values: "six", "five", "siete", "seis"
   - Should trigger: "must be numeric" error on rows 2 and 3

6. **error_empty_player_names.csv**
   - Contains empty player name fields
   - Empty values in pareja1_jugador1 and pareja1_jugador2
   - Should trigger: "cannot be empty" error on rows 2 and 3

7. **error_multiple_issues.csv**
   - Combines multiple validation errors in the same file
   - Row 2: invalid year, invalid date format, invalid category, empty player, non-numeric scores
   - Row 3: invalid date format, invalid category, multiple empty players, non-numeric scores
   - Row 4: year out of range, invalid dates, invalid category, all players empty, non-numeric scores
   - Should trigger multiple different error messages

## Usage

These files are intended to test the validation system's ability to:
- Detect and report specific validation errors
- Provide clear error messages with row numbers
- Handle multiple errors in the same file
- Distinguish between syntax errors and structure errors

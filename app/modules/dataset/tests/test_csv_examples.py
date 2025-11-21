"""
Tests to verify that all CSV example files match the required padel structure.
This ensures that the sample datasets provided in padel_csv_examples/ are valid.
"""
import os
import glob
import pytest
from app.modules.dataset.types.tabular import TabularDataset


def get_csv_example_files():
    """Get all CSV files from padel_csv_examples directory."""
    csv_examples_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'padel_csv_examples'
    )
    csv_files = glob.glob(os.path.join(csv_examples_dir, '*.csv'))
    # Return tuples of (filename, full_path) for better test output
    return [(os.path.basename(f), f) for f in csv_files if os.path.isfile(f)]


@pytest.mark.parametrize('filename,filepath', get_csv_example_files())
def test_csv_examples_match_padel_structure(filename, filepath):
    """Test that each CSV example file has valid padel structure."""
    tab = TabularDataset(None)
    
    # First validate syntax
    syntax_result = tab.validate_syntax(filepath)
    assert syntax_result['valid'], (
        f"{filename} has syntax errors: {syntax_result.get('message', 'Unknown error')}"
    )
    
    # Then validate padel structure
    structure_result = tab.validate_padel_structure(filepath)
    
    # If validation fails, print detailed errors
    if not structure_result['valid']:
        errors = structure_result.get('errors', [])
        error_msg = f"\n{filename} does not match padel structure:\n"
        error_msg += "\n".join(f"  - {err}" for err in errors)
        pytest.fail(error_msg)
    
    assert structure_result['valid'], f"{filename} should have valid padel structure"


def test_csv_examples_directory_exists():
    """Verify that padel_csv_examples directory exists and contains files."""
    csv_examples_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'padel_csv_examples'
    )
    assert os.path.exists(csv_examples_dir), "padel_csv_examples directory should exist"
    
    csv_files = glob.glob(os.path.join(csv_examples_dir, '*.csv'))
    assert len(csv_files) > 0, "padel_csv_examples directory should contain at least one CSV file"


def test_csv_examples_all_have_same_columns():
    """Verify that all CSV examples have the same column structure."""
    csv_files = [f for _, f in get_csv_example_files()]
    
    if len(csv_files) < 2:
        pytest.skip("Need at least 2 CSV files to compare columns")
    
    import csv
    
    first_file = csv_files[0]
    with open(first_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        expected_headers = next(reader)
    
    for csv_file in csv_files[1:]:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
        
        assert headers == expected_headers, (
            f"{os.path.basename(csv_file)} has different columns than {os.path.basename(first_file)}"
        )

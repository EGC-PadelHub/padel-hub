"""
Manual validation script for checking error CSV files in Padel-Hub.
This script validates all error CSV files and shows detailed validation messages.
Useful for debugging and verifying error examples.

Run with: python -m app.modules.dataset.tests.check_error_files
"""

import os

from app.modules.dataset.types.tabular import TabularDataset


def print_separator(char="=", length=80):
    print(char * length)


def print_header(text):
    print_separator()
    print(f" {text}")
    print_separator()


def test_csv_file(filepath):
    """Test a single CSV file and display validation results."""
    filename = os.path.basename(filepath)
    
    print(f"\n📄 Testing: {filename}")
    print("-" * 80)
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    # Create TabularDataset instance
    tab = TabularDataset(None)
    
    # First check syntax
    print("🔍 Step 1: Syntax validation...")
    syntax_result = tab.validate_syntax(filepath)
    
    if not syntax_result.get("valid"):
        print("❌ SYNTAX ERROR:")
        print(f"   Message: {syntax_result.get('message', 'Unknown error')}")
        if "line" in syntax_result:
            print(f"   Line: {syntax_result['line']}")
        if "snippet" in syntax_result:
            print(f"   Snippet: {syntax_result['snippet']}")
        return False
    
    print("✅ Syntax is valid")
    
    # Then check padel structure
    print("\n🔍 Step 2: Padel structure validation...")
    padel_result = tab.validate_padel_structure(filepath)
    
    if not padel_result.get("valid"):
        print("❌ STRUCTURE VALIDATION ERRORS:")
        errors = padel_result.get("errors", [])
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
        
        if "required_columns" in padel_result:
            print(f"\n   Required columns: {len(padel_result['required_columns'])} total")
        
        return False
    
    print("✅ Padel structure is valid")
    return True


def main():
    print_header("🧪 Padel-Hub CSV Error Validation Test Suite")
    
    # Define error directory (relative to this file)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    error_dir = os.path.join(current_dir, "..", "padel_csv_errors")
    error_dir = os.path.abspath(error_dir)
    
    if not os.path.exists(error_dir):
        print(f"❌ Error directory not found: {error_dir}")
        return 1
    
    # Get all CSV files
    csv_files = sorted([f for f in os.listdir(error_dir) if f.startswith("error_") and f.endswith(".csv")])
    
    if not csv_files:
        print(f"❌ No error CSV files found in: {error_dir}")
        return 1
    
    print(f"\n📁 Found {len(csv_files)} error CSV files to test")
    print(f"📂 Directory: {error_dir}")
    
    # Test each file
    results = {}
    for csv_filename in csv_files:
        csv_file = os.path.join(error_dir, csv_filename)
        try:
            is_valid = test_csv_file(csv_file)
            results[csv_filename] = "VALID" if is_valid else "INVALID (as expected)"
        except Exception as e:
            print(f"\n💥 Exception occurred: {e}")
            results[csv_file.name] = f"ERROR: {e}"
    
    # Summary
    print_header("📊 TEST SUMMARY")
    print(f"\nTotal files tested: {len(results)}")
    print("\nResults:")
    for filename, result in results.items():
        status_icon = "✅" if "INVALID" in result else "⚠️"
        print(f"  {status_icon} {filename}: {result}")
    
    print_separator()
    print("\n💡 Expected behavior:")
    print("   - All error_*.csv files should show 'INVALID (as expected)'")
    print("   - Each error message should include the row number (e.g., 'Row 2: ...')")
    print("   - Different files should show different types of validation errors")
    print_separator()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

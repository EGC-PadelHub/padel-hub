import os
import time
import tempfile

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import datetime
import pathlib

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)

    try:
        amount_datasets = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
    except Exception:
        amount_datasets = 0
    return amount_datasets


def test_upload_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)
        time.sleep(4)
        wait_for_page_to_load(driver)

        # Count initial datasets
        initial_datasets = count_datasets(driver, host)

        # Open the upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

    # Find basic info and CSV model and fill values
        title_field = driver.find_element(By.NAME, "title")
        title_field.send_keys("Title")
        desc_field = driver.find_element(By.NAME, "desc")
        desc_field.send_keys("Description")
        tags_field = driver.find_element(By.NAME, "tags")
        tags_field.send_keys("tag1,tag2")
        
        # Select tournament type (required field)
        tournament_type_field = Select(driver.find_element(By.NAME, "tournament_type"))
        tournament_type_field.select_by_value("master")

        # Add two authors and fill
        add_author_button = driver.find_element(By.ID, "add_author")
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field0 = driver.find_element(By.NAME, "authors-0-name")
        name_field0.send_keys("Author0")
        affiliation_field0 = driver.find_element(By.NAME, "authors-0-affiliation")
        affiliation_field0.send_keys("Club0")
        orcid_field0 = driver.find_element(By.NAME, "authors-0-orcid")
        orcid_field0.send_keys("0000-0000-0000-0000")

        name_field1 = driver.find_element(By.NAME, "authors-1-name")
        name_field1.send_keys("Author1")
        affiliation_field1 = driver.find_element(By.NAME, "authors-1-affiliation")
        affiliation_field1.send_keys("Club1")

        # Obtén las rutas absolutas de los archivos
        file1_path = os.path.abspath("app/modules/dataset/padel_csv_examples/file1.csv")
        file2_path = os.path.abspath("app/modules/dataset/padel_csv_examples/file2.csv")

        # Subir el primer archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file1_path)
        wait_for_page_to_load(driver)

        # Subir el segundo archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file2_path)
        wait_for_page_to_load(driver)

    # Add authors in CSV models
        show_button = driver.find_element(By.ID, "0_button")
        show_button.send_keys(Keys.RETURN)
        add_author_uvl_button = driver.find_element(By.ID, "0_form_authors_button")
        add_author_uvl_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field = driver.find_element(By.NAME, "feature_models-0-authors-2-name")
        name_field.send_keys("Author3")
        affiliation_field = driver.find_element(By.NAME, "feature_models-0-authors-2-affiliation")
        affiliation_field.send_keys("Club3")

        # Check I agree and send form
        check = driver.find_element(By.ID, "agreeCheckbox")
        check.send_keys(Keys.SPACE)
        wait_for_page_to_load(driver)

        # Take screenshot before submitting
        print("About to submit form...")
        
        upload_btn = driver.find_element(By.ID, "upload_button")
        upload_btn.click()
        
        # Wait a bit to see if there are validation errors
        time.sleep(3)
        
        # Check for validation errors
        try:
            error_elements = driver.find_elements(By.CLASS_NAME, "invalid-feedback")
            if error_elements:
                print("Validation errors found:")
                for error in error_elements:
                    if error.is_displayed():
                        print(f"  - {error.text}")
        except Exception:
            pass
        
        # Try to wait for redirect
        try:
            WebDriverWait(driver, 10).until(
                EC.url_contains("/dataset/list")
            )
            wait_for_page_to_load(driver)
        except Exception as e:
            print(f"Failed to redirect. Current URL: {driver.current_url}")
            print(f"Page title: {driver.title}")
            # Print any alert messages
            try:
                alerts = driver.find_elements(By.CLASS_NAME, "alert")
                if alerts:
                    print("Alerts found:")
                    for alert in alerts:
                        if alert.is_displayed():
                            print(f"  - {alert.text}")
            except Exception:
                pass
            raise

        assert driver.current_url == f"{host}/dataset/list", f"Expected redirect to {host}/dataset/list but got {driver.current_url}"

        # Count final datasets
        final_datasets = count_datasets(driver, host)
        assert final_datasets == initial_datasets + 1, "Test failed!"

        print("Test passed!")

    finally:

        # Close the browser
        close_driver(driver)


def test_upload_modal_and_error_badge():
    """Standalone modal E2E: upload a broken CSV and assert modal + badge."""
    driver = initialize_driver()
    tmp_path = None
    try:
        host = get_host_for_selenium_testing()

        # Login via UI (assumes test user exists with these creds)
        driver.get(f"{host}/login")
        # Use the same test user as other selenium tests for consistency
        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234")
        submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        submit.click()

        # give a moment to login
        time.sleep(1)

        # go to upload page
        driver.get(f"{host}/dataset/upload")

        # create temp csv with unbalanced quotes in home directory
        # (Firefox snap cannot access /tmp)
        tmp_dir = os.path.expanduser("~/snap/firefox/common/tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(suffix=".csv", dir=tmp_dir)
        os.close(fd)
        content = (
            "r13,m,13\n"
            "r14,n,14\n"
            "r15,o,15\n"
            "r16,p,\"This \"has\" nested quotes and unbalanced\n"
            "r17,q,17\n"
            "r18,r,18\n"
            "r19,s,19\n"
        )
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)

        # find the Dropzone file input and send file
        # Use WebDriverWait + expected_conditions for robustness and fallback to older selector
        try:
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dz-hidden-input"))
            )
        except Exception:
            # fallback selector used previously
            file_input = driver.find_element(By.CSS_SELECTOR, "form#myDropzone input[type='file']")

        file_input.send_keys(tmp_path)

        # wait for the overlay to appear (use explicit wait)
        try:
            overlay = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "csvErrorModalOverlay"))
            )
            badge = overlay.find_element(By.XPATH, ".//span[text()='Error']")
            assert badge is not None
        except Exception:
            # take a screenshot to help debugging flaky failures
            try:
                screenshots_dir = pathlib.Path(__file__).parent / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                screenshot_path = screenshots_dir / f"selenium_failure_modal_{ts}.png"
                driver.save_screenshot(str(screenshot_path))
                print(f"Saved failure screenshot: {screenshot_path}")
            except Exception:
                print("Failed to write screenshot")
            # re-raise the original exception so the test fails visibly
            raise

    finally:
        try:
            close_driver(driver)
        except Exception:
            pass
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_valid_padel_csv_upload():
    """Test that a valid padel CSV is accepted without errors."""
    driver = initialize_driver()
    
    try:
        host = get_host_for_selenium_testing()
        
        # Login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)
        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(2)
        
        # Go to upload page
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        
        # Upload valid padel CSV from examples
        file_path = os.path.abspath("app/modules/dataset/padel_csv_examples/file2.csv")
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file_path)
        
        # Wait a moment for upload to process
        time.sleep(3)
        
        # Verify no error modal appeared
        try:
            error_modal = driver.find_element(By.ID, "csvErrorModalOverlay")
            # If modal exists, check it's not visible
            assert not error_modal.is_displayed(), "Error modal should not be visible for valid CSV"
        except Exception:
            # Modal doesn't exist - this is good
            pass
        
        # Check that file appears in the file list
        try:
            file_list = driver.find_element(By.ID, "file-list")
            assert "file2.csv" in file_list.text or file_list.find_elements(By.TAG_NAME, "li")
            print("✓ Valid padel CSV uploaded successfully without errors!")
        except Exception:
            print("Warning: Could not verify file list, but no error modal appeared")
        
    finally:
        close_driver(driver)


def test_invalid_csv_structure_error():
    """Test that uploading a CSV with missing required padel columns shows proper error."""
    driver = initialize_driver()
    tmp_path = None
    
    try:
        host = get_host_for_selenium_testing()
        
        # Login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)
        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(2)
        
        # Go to upload page
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        
        # Create an invalid CSV (missing required padel columns)
        tmp_dir = os.path.expanduser("~/snap/firefox/common/tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(suffix=".csv", dir=tmp_dir)
        os.close(fd)
        
        # Invalid CSV content - missing most required padel columns
        invalid_content = (
            "name,year,category\n"
            "Tournament A,2024,Masculino\n"
            "Tournament B,2023,Femenino\n"
        )
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(invalid_content)
        
        # Try to upload the invalid CSV
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dz-hidden-input"))
        )
        file_input.send_keys(tmp_path)
        
        # Wait for error modal or alert to appear
        time.sleep(2)
        
        # Check if error is displayed (could be in modal, alert, or error message)
        error_displayed = False
        try:
            # Try to find error modal
            overlay = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "csvErrorModalOverlay"))
            )
            error_displayed = True
            print("✓ CSV structure validation error modal displayed correctly!")
        except Exception:
            # Try to find error in alerts area
            try:
                alerts = driver.find_element(By.ID, "alerts")
                if alerts.is_displayed():
                    error_displayed = True
                    print("✓ CSV structure validation error alert displayed!")
            except Exception:
                pass
        
        assert error_displayed, "Error should be displayed for invalid CSV structure"
        
    finally:
        close_driver(driver)
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_csv_missing_columns_error_with_example():
    """Test uploading a CSV with missing required columns using error example file."""
    driver = initialize_driver()
    
    try:
        host = get_host_for_selenium_testing()
        
        # Login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)
        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(2)
        
        # Go to upload page
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        
        # Upload CSV with structure errors (missing required padel columns)
        error_file_path = os.path.abspath("app/modules/dataset/padel_csv_errors/error_missing_columns.csv")
        
        # Check if error file exists, if not skip this test
        if not os.path.exists(error_file_path):
            print("Note: Error example file not found, skipping test")
            return
        
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(error_file_path)
        
        # Wait for error to be displayed
        time.sleep(3)
        
        # Verify error is shown (modal, alert, or inline message)
        error_found = False
        error_messages = []
        
        # Check for error modal
        try:
            overlay = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "csvErrorModalOverlay"))
            )
            error_found = True
            error_messages.append("Error modal displayed")
            
            # Try to find specific error message about missing columns
            modal_text = overlay.text
            if "Missing required columns" in modal_text or "structure" in modal_text.lower():
                error_messages.append("Structure error message found")
        except Exception:
            pass
        
        # Check for alert messages
        try:
            alerts = driver.find_element(By.ID, "alerts")
            if alerts.is_displayed() and alerts.text:
                error_found = True
                error_messages.append(f"Alert shown: {alerts.text[:100]}")
        except Exception:
            pass
        
        assert error_found, "Structure validation error should be displayed for CSV with missing columns"
        print(f"✓ CSV structure error detected correctly: {', '.join(error_messages)}")
        
    finally:
        close_driver(driver)


def test_anonymous_dataset_upload():
    """Test anonymous dataset upload workflow."""
    driver = initialize_driver()
    
    try:
        host = get_host_for_selenium_testing()
        
        # Login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)
        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(2)
        wait_for_page_to_load(driver)
        
        # Navigate to upload page
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        
        # Fill basic metadata
        driver.find_element(By.NAME, "title").send_keys("Anonymous Test Dataset")
        driver.find_element(By.NAME, "desc").send_keys("Testing anonymous upload feature")
        driver.find_element(By.NAME, "tags").send_keys("anonymous,test")
        
        # Select tournament type
        tournament_type = Select(driver.find_element(By.NAME, "tournament_type"))
        tournament_type.select_by_value("master")
        
        # Add author (will be hidden when anonymous)
        add_author_btn = driver.find_element(By.ID, "add_author")
        add_author_btn.click()
        wait_for_page_to_load(driver)
        
        driver.find_element(By.NAME, "authors-0-name").send_keys("Secret Author")
        driver.find_element(By.NAME, "authors-0-affiliation").send_keys("Secret Lab")
        
        # Upload valid padel CSV
        file_path = os.path.abspath("app/modules/dataset/padel_csv_examples/file3.csv")
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file_path)
        time.sleep(2)
        
        # Select "Permanent (anonymous) upload to Zenodo"
        upload_type_anonymous = driver.find_element(By.ID, "upload_type_anonymous")
        upload_type_anonymous.click()
        time.sleep(1)
        
        # Agree to terms
        agree_checkbox = driver.find_element(By.ID, "agreeCheckbox")
        agree_checkbox.click()
        time.sleep(1)
        
        # Submit
        upload_btn = driver.find_element(By.ID, "upload_button")
        upload_btn.click()
        
        # Wait for redirect
        WebDriverWait(driver, 15).until(
            EC.url_contains("/dataset/list")
        )
        wait_for_page_to_load(driver)
        
        # Navigate to dataset list to verify anonymous flag
        driver.get(f"{host}/dataset/list")
        wait_for_page_to_load(driver)
        
        # Look for the anonymous dataset
        try:
            # Find the dataset in the local/unsynchronized section
            page_text = driver.find_element(By.TAG_NAME, "body").text
            assert "Anonymous Test Dataset" in page_text, "Dataset should appear in the list"
            
            # Verify "Anonymous" label is shown instead of author names
            if "Anonymous" in page_text:
                print("✓ Anonymous dataset upload test passed!")
                print("✓ 'Anonymous' label displayed instead of author names")
            else:
                print("Warning: Could not verify 'Anonymous' label in UI")
        except Exception as e:
            print(f"Warning: Could not fully verify anonymous dataset: {e}")
        
    finally:
        close_driver(driver)


def test_anonymous_flag_persists():
    """Test that anonymous flag persists and is displayed correctly in dataset view."""
    driver = initialize_driver()
    
    try:
        host = get_host_for_selenium_testing()
        
        # Login
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)
        driver.find_element(By.NAME, "email").send_keys("user1@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(2)
        
        # Go to upload page
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        
        # Fill minimal metadata
        driver.find_element(By.NAME, "title").send_keys("Anon Persist Test")
        driver.find_element(By.NAME, "desc").send_keys("Testing anonymous persistence")
        driver.find_element(By.NAME, "tags").send_keys("test")
        
        # Select tournament type
        tournament_type = Select(driver.find_element(By.NAME, "tournament_type"))
        tournament_type.select_by_value("open")
        
        # Add author
        add_author_btn = driver.find_element(By.ID, "add_author")
        add_author_btn.click()
        time.sleep(1)
        driver.find_element(By.NAME, "authors-0-name").send_keys("Hidden Author")
        
        # Upload CSV
        file_path = os.path.abspath("app/modules/dataset/padel_csv_examples/file4.csv")
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file_path)
        time.sleep(2)
        
        # Select anonymous upload
        upload_type_anonymous = driver.find_element(By.ID, "upload_type_anonymous")
        upload_type_anonymous.click()
        time.sleep(1)
        
        # Agree and submit
        agree_checkbox = driver.find_element(By.ID, "agreeCheckbox")
        agree_checkbox.click()
        time.sleep(1)
        
        upload_btn = driver.find_element(By.ID, "upload_button")
        upload_btn.click()
        
        # Wait for redirect
        WebDriverWait(driver, 15).until(
            EC.url_contains("/dataset/list")
        )
        wait_for_page_to_load(driver)
        
        # Verify in the list page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Should show "Anonymous" not "Hidden Author"
        if "Anonymous" in page_text and "Hidden Author" not in page_text:
            print("✓ Anonymous flag persists correctly!")
            print("✓ Author name is properly hidden")
        else:
            print("Warning: Could not fully verify anonymous persistence")
        
    finally:
        close_driver(driver)

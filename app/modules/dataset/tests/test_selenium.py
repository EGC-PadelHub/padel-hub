import os
import time
import tempfile

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
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
        file1_path = os.path.abspath("app/modules/dataset/csv_examples/file1.csv")
        file2_path = os.path.abspath("app/modules/dataset/csv_examples/file2.csv")

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

        upload_btn = driver.find_element(By.ID, "upload_button")
        upload_btn.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        time.sleep(2)  # Force wait time

        assert driver.current_url == f"{host}/dataset/list", "Test failed!"

        # Count final datasets
        final_datasets = count_datasets(driver, host)
        assert final_datasets == initial_datasets + 1, "Test failed!"

        print("Test passed!")

    finally:

        # Close the browser
        close_driver(driver)


# Call the test function
test_upload_dataset()


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

        # create temp csv with unbalanced quotes
        fd, tmp_path = tempfile.mkstemp(suffix=".csv")
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


# Run the additional modal test as part of the same invocation so Rosemary picks it up
test_upload_modal_and_error_badge()

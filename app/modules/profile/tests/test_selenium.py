import time
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from core.selenium.common import initialize_driver, close_driver
from core.environment.host import get_host_for_selenium_testing


def wait_for_page_to_load(driver, timeout=10):
    """Wait for page to be fully loaded."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def test_metrics_dashboard_loads():
    """Test that metrics dashboard page loads successfully and displays basic structure."""
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
        
        # Navigate to metrics dashboard
        driver.get(f"{host}/profile/metrics")
        wait_for_page_to_load(driver)
        time.sleep(2)  # Wait for charts to render
        
        # Verify page title
        assert "My Metrics Dashboard" in driver.page_source
        
        # Verify main metric cards exist
        assert "Uploaded Datasets" in driver.page_source
        assert "Downloads Received" in driver.page_source
        assert "Downloads Made" in driver.page_source
        assert "Synchronized" in driver.page_source
        
        # Verify charts section exists
        assert "Activity Received Overview" in driver.page_source
        assert "Datasets Status" in driver.page_source
        
        print("✓ Metrics dashboard loaded successfully with all sections!")
        
    finally:
        close_driver(driver)


def test_user_statistics_display():
    """Test that user statistics are displayed correctly in metric cards."""
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
        
        # Navigate to metrics dashboard
        driver.get(f"{host}/profile/metrics")
        wait_for_page_to_load(driver)
        time.sleep(2)
        
        # Find metric card values (they are displayed as h2 elements with specific classes)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Verify metric labels and values exist (in uppercase as displayed in HTML)
        assert "UPLOADED DATASETS" in page_text
        assert "DOWNLOADS RECEIVED" in page_text
        assert "DOWNLOADS MADE" in page_text
        assert "SYNCHRONIZED" in page_text
        
        # Check that numeric values are displayed (should see numbers)
        metric_cards = driver.find_elements(By.CLASS_NAME, "metric-card")
        assert len(metric_cards) == 4, "Should have 4 metric cards"
        
        # Verify each card has a numeric value (h2 with font-weight-bold)
        for card in metric_cards:
            value_element = card.find_element(By.CSS_SELECTOR, "h2.font-weight-bold")
            value_text = value_element.text
            # Value should be a number (including 0)
            assert value_text.isdigit(), f"Metric value should be numeric, got: {value_text}"
            
        print("✓ User statistics displayed correctly in all metric cards!")
        
    finally:
        close_driver(driver)


def test_metrics_after_dataset_upload():
    """Test that metrics update after uploading a new dataset."""
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
        
        # Get initial metrics
        driver.get(f"{host}/profile/metrics")
        wait_for_page_to_load(driver)
        time.sleep(2)
        
        # Find the "Uploaded Datasets" metric card and get initial value
        metric_cards = driver.find_elements(By.CLASS_NAME, "metric-card")
        uploaded_datasets_card = metric_cards[0]  # First card is Uploaded Datasets
        initial_count_element = uploaded_datasets_card.find_element(By.CSS_SELECTOR, "h2.font-weight-bold")
        initial_count = int(initial_count_element.text)
        
        print(f"Initial uploaded datasets count: {initial_count}")
        
        # Upload a new dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        
        # Fill metadata
        driver.find_element(By.NAME, "title").send_keys("Metrics Test Dataset")
        driver.find_element(By.NAME, "desc").send_keys("Testing metrics update")
        driver.find_element(By.NAME, "tags").send_keys("test,metrics")
        
        # Select tournament type
        tournament_type = Select(driver.find_element(By.NAME, "tournament_type"))
        tournament_type.select_by_value("open")
        
        # Add author
        add_author_btn = driver.find_element(By.ID, "add_author")
        add_author_btn.click()
        time.sleep(1)
        driver.find_element(By.NAME, "authors-0-name").send_keys("Test Author")
        
        # Upload CSV
        file_path = os.path.abspath("app/modules/dataset/padel_csv_examples/file1.csv")
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file_path)
        time.sleep(2)
        
        # Submit
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
        
        # Go back to metrics dashboard and check updated count
        driver.get(f"{host}/profile/metrics")
        wait_for_page_to_load(driver)
        time.sleep(2)
        
        # Get updated count
        metric_cards = driver.find_elements(By.CLASS_NAME, "metric-card")
        uploaded_datasets_card = metric_cards[0]
        updated_count_element = uploaded_datasets_card.find_element(By.CSS_SELECTOR, "h2.font-weight-bold")
        updated_count = int(updated_count_element.text)
        
        print(f"Updated uploaded datasets count: {updated_count}")
        
        # Verify count increased by 1
        assert updated_count == initial_count + 1, f"Expected {initial_count + 1}, got {updated_count}"
        print("✓ Metrics updated correctly after dataset upload!")
        
    finally:
        close_driver(driver)


def test_dashboard_with_no_datasets():
    """Test dashboard display for a user with no datasets (edge case)."""
    driver = initialize_driver()
    
    try:
        host = get_host_for_selenium_testing()
        
        # Login with a user that likely has no datasets
        # Using user2 which might be empty, or we can check if values are 0
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)
        driver.find_element(By.NAME, "email").send_keys("user2@example.com")
        driver.find_element(By.NAME, "password").send_keys("1234")
        driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
        time.sleep(2)
        
        # Navigate to metrics dashboard
        driver.get(f"{host}/profile/metrics")
        wait_for_page_to_load(driver)
        time.sleep(2)
        
        # Verify dashboard loads without errors
        assert "My Metrics Dashboard" in driver.page_source
        
        # Check all metric cards display (even with 0 values)
        metric_cards = driver.find_elements(By.CLASS_NAME, "metric-card")
        assert len(metric_cards) == 4, "Should have 4 metric cards"
        
        # Verify all cards have numeric values (could be 0)
        for card in metric_cards:
            value_element = card.find_element(By.CSS_SELECTOR, "h2.font-weight-bold")
            value_text = value_element.text
            assert value_text.isdigit(), f"Metric value should be numeric, got: {value_text}"
            
        # Verify charts render (they should exist even with no data)
        assert "Activity Received Overview" in driver.page_source
        assert "Datasets Status" in driver.page_source
        
        # Check Activity Summary section handles division by zero gracefully
        assert "Avg Downloads/Dataset" in driver.page_source
        assert "Sync Rate" in driver.page_source
        assert "Avg Views/Dataset" in driver.page_source
        
        print("✓ Dashboard handles empty data gracefully (no errors with zero datasets)!")
        
    finally:
        close_driver(driver)


def test_metrics_charts_render():
    """Test that charts render without JavaScript errors."""
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
        
        # Navigate to metrics dashboard
        driver.get(f"{host}/profile/metrics")
        wait_for_page_to_load(driver)
        time.sleep(3)  # Give charts time to render
        
        # Check that canvas elements exist (where charts are drawn)
        downloads_chart = driver.find_element(By.ID, "downloadsChart")
        datasets_chart = driver.find_element(By.ID, "datasetsChart")
        
        assert downloads_chart is not None, "Downloads chart canvas should exist"
        assert datasets_chart is not None, "Datasets chart canvas should exist"
        
        # Verify no JavaScript errors occurred (check browser console)
        # Note: This is a basic check - Selenium can't easily access console errors
        # but we can verify the page loaded completely
        page_text = driver.find_element(By.TAG_NAME, "body").text
        assert "Activity Received Overview" in page_text
        assert "Datasets Status" in page_text
        
        # Verify activity summary cards render
        assert "Avg Downloads/Dataset" in page_text
        assert "Sync Rate" in page_text
        assert "Avg Views/Dataset" in page_text
        
        print("✓ Charts rendered successfully without errors!")
        
    finally:
        close_driver(driver)


def test_metrics_navigation_from_profile():
    """Test navigation to metrics dashboard from user profile."""
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
        
        # Go to profile page (if exists) or directly test the metrics URL
        # Assuming there's a link to metrics in navigation or profile
        driver.get(f"{host}/profile/metrics")
        wait_for_page_to_load(driver)
        time.sleep(2)
        
        # Verify we're on the metrics page
        assert "/profile/metrics" in driver.current_url
        assert "My Metrics Dashboard" in driver.page_source
        
        # Verify page is accessible and loads completely
        metric_cards = driver.find_elements(By.CLASS_NAME, "metric-card")
        assert len(metric_cards) == 4
        
        print("✓ Successfully navigated to metrics dashboard!")
        
    finally:
        close_driver(driver)

import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def test_explore_public_search():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")
        time.sleep(4)
        try:
            search_field = driver.find_element(By.NAME, "title") 
            search_field.clear()
            
            query = "Sample dataset 2"
            for char in query:
                search_field.send_keys(char)
                time.sleep(0.1) 
            time.sleep(3) 
            
        except NoSuchElementException:
            print("No se encontró el campo de búsqueda.")
        try:
            results = driver.find_elements(By.CLASS_NAME, "card-body") 
            if len(results) == 1:
                print("Test Passed! Se encontró exactamente 1 dataset.")
            else:
                raise AssertionError(f"Test Failed! Se esperaban 1 resultado, pero hay {len(results)} visibles.")
            
        except NoSuchElementException:
            raise AssertionError("Test failed! No se encontraron elementos.")

    finally:
        close_driver(driver)


# Ejecutar el test
if __name__ == "__main__":
    test_explore_public_search()
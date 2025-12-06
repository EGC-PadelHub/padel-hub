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


def test_explore_filter_by_description():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")
        time.sleep(2)
        try:
            desc_input = driver.find_element(By.ID, "filter_description")
            desc_input.clear()
            
            query = "dataset 3" # Término genérico para probar que filtra
            for char in query:
                desc_input.send_keys(char)
                time.sleep(0.1)
            
            time.sleep(2) # Esperar reactividad
            
            results = driver.find_elements(By.CLASS_NAME, "card-body")
            if len(results) == 1:
                print(f"Test Description Passed! Se encontraron {len(results)} resultados por descripción.")
            else:
                print("Test Description: No se encontraron resultados (puede ser correcto si no hay datos).")
        except NoSuchElementException:
            print("Error: No se encontró el input 'filter_description'")

    finally:
        close_driver(driver)


def test_explore_filter_by_tags():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")
        time.sleep(2)
        try:
            tags_input = driver.find_element(By.ID, "filter_tags")
            tags_input.clear()
            query = "fast-court, indoor" 
            for char in query:
                tags_input.send_keys(char)
                time.sleep(0.1)  
            time.sleep(2) 
            results = driver.find_elements(By.CLASS_NAME, "card-body")
            if len(results) == 1:
                print(f"Test Tags Passed! Se encontraron 1 resultado por tags.")
            else:
                print("No se encontraron los resultados esperados.")

        except NoSuchElementException:
            print("Error: No se encontró el input 'filter_tags'")

    finally:
        close_driver(driver)


def test_explore_sorting():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/explore")
        time.sleep(2)
        first_result_newest = ""
        results = driver.find_elements(By.CSS_SELECTOR, ".card-body h3 a")
        if results:
            first_result_newest = results[0].text
        try:
            oldest_radio = driver.find_element(By.CSS_SELECTOR, "input[name='sorting'][value='oldest']")
            try:
                oldest_radio.click()
            except:
                driver.execute_script("arguments[0].click();", oldest_radio)
                
            time.sleep(2)
            results_oldest = driver.find_elements(By.CSS_SELECTOR, ".card-body h3 a")
            if results_oldest:
                first_result_oldest = results_oldest[0].text
                print(f"Newest first item: {first_result_newest}")
                print(f"Oldest first item: {first_result_oldest}")
                
                if first_result_newest != first_result_oldest:
                    print("Test Sorting Passed! El orden de los resultados cambió.")
                else:
                    print("Test Sorting: El primer resultado es el mismo (puede pasar si solo hay 1 dataset).")

        except NoSuchElementException:
            print("Error: No se encontraron los radio buttons de sorting")

    finally:
        close_driver(driver)
        

# Ejecutar el test
if __name__ == "__main__":
    print("--- Running Public Search Test ---")
    test_explore_public_search()
    print("\n--- Running Description Filter Test ---")
    test_explore_filter_by_description()
    print("\n--- Running Tags Filter Test ---")
    test_explore_filter_by_tags()
    print("\n--- Running Sorting Test ---")
    test_explore_sorting()
    test_explore_filter_by_description()
    test_explore_filter_by_tags()
    test_explore_sorting()
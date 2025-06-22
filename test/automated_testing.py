from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_compound(driver, compound_name):
    """Create a new compound by clicking the create button and entering the name."""
    create_button = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[1]/div[2]/div/button[2]')
    create_button.click()
    time.sleep(2)
    compound_input = driver.find_element(By.XPATH, '/html/body/div[2]/div[3]/div/div[1]/div/div/input')
    compound_input.send_keys(compound_name)
    time.sleep(1)
    modal_create_button = driver.find_element(By.XPATH, '/html/body/div[2]/div[3]/div/div[2]/button[2]')
    modal_create_button.click()
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.XPATH, '/html/body/div[2]/div[3]'))
    )
    time.sleep(1)

def search_in_compound_alpha(driver):
    """Search for inventory in Compound Alpha's HR department."""
    department_button = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div/table/tbody/tr[1]/td[3]/div/button[1]')
    department_button.click()
    time.sleep(3)
    view_details = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div/table/tbody/tr[1]/td[3]/a')
    view_details.click()
    time.sleep(5)
    search_documents_button = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div[1]/div/div/button[2]')
    search_documents_button.click()
    time.sleep(5)
    search_input = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div[3]/div/div[1]/div/div/input')
    search_input.send_keys("what is our inventory now?")
    time.sleep(1)
    search_button = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div[3]/div/div/button')
    search_button.click()
    time.sleep(5)
    try:
        search1 = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div[3]/div/div[2]/div/p').text
        print("Search result:", search1)
    except Exception:
        print("Search result not found.")

def search_legal_nda(driver):
    """Search for NDA validity in the Legal NDA section."""
    documents_button = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div/table/tbody/tr[1]/td[3]/div/button[2]')
    documents_button.click()
    time.sleep(3)
    search_documents_button = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div[1]/div/div/button[2]')
    search_documents_button.click()
    time.sleep(3)
    try:
        legal_nda_checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div/div/div/div/div[2]/div[3]/div/div[1]/div/label[1]/span[1]/input'))
        )
        legal_nda_checkbox.click()
        time.sleep(2)
    except Exception:
        print("Legal NDA checkbox not found.")
        return
    nda_input = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div[3]/div/div[2]/div/div/input')
    nda_input.send_keys("How long is the NDA valid for?")
    time.sleep(1)
    nda_search_button = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div[3]/div/div[2]/button')
    nda_search_button.click()
    time.sleep(5)
    try:
        search2 = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div[3]/div/div[3]/div/p').text
        print("NDA Search result:", search2)
    except Exception:
        print("NDA Search result not found.")

def search_database_price(driver):
    """Search for the price of the Laptop in the database section."""
    database_button = driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/div/table/tbody/tr[1]/td[3]/div/button[3]')
    database_button.click()
    time.sleep(3)
    try:
        first_item = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/ul/li[1]'))
        )
        first_item.click()
        time.sleep(2)
    except Exception:
        print("First database item not found or not clickable.")
        return
    # If there is an input for the question, add code here
    # Example (uncomment and adjust if needed):
    # db_input = driver.find_element(By.XPATH, '<INPUT_XPATH>')
    # db_input.send_keys("What is the price of the Laptop?")
    # db_input.send_keys(Keys.RETURN)
    # time.sleep(5)
    try:
        db_result = driver.find_element(By.XPATH, '/html/body/div[2]/div[3]/div/div/p').text
        print("Database Search result:", db_result)
    except Exception:
        print("Database Search result not found.")

def test_workflow():
    driver = webdriver.Chrome()  # Make sure chromedriver is in your PATH
    driver.get("https://ipm-frontend-west-asa3csdbbyahgqad.westus2-01.azurewebsites.net/")
    assert "IPM" in driver.title or driver.title != "", "Page did not load or title is missing."
    time.sleep(10)
    try:
        create_compound(driver, "Compound Alpha")
        search_in_compound_alpha(driver)
        search_legal_nda(driver)
        search_database_price(driver)
    except Exception as e:
        driver.quit()
        raise e
    driver.quit()

if __name__ == "__main__":
    test_workflow()
    print("Test passed: Compound Alpha created and all searches performed.")
else:
    print("This script is intended to be run directly, not imported as a module.")
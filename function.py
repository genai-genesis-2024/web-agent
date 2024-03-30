# functions.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import uuid
import os

def initialize_driver():
    driver = webdriver.Chrome() 
    return driver

def screenshot(URL):
    options = webdriver.ChromeOptions()
    options.headless = True
    # options.add_argument("--headless=false")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    # TODO: The demo person need to update the binary_location and user-data-dir
    options.binary_location = r"C:\Users\vince\AppData\Local\Google\Chrome SxS\Application\chrome.exe"
    # Maybe specify the profile directory "Profile 1"
    options.add_argument(r"user-data-dir=C:\Users\vince\AppData\Local\Google\Chrome SxS\User Data")
    options.add_argument("--profile-directory=Default");

    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    driver.maximize_window()

    os.makedirs("screenshots", exist_ok=True)
    filename = f"screenshots/screenshot_{str(uuid.uuid4())}.png"
    driver.save_screenshot(filename)
    driver.quit()

def click_element(driver, xpath):
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    element.click()

def scroll_page(driver, pixels):
    driver.execute_script(f"window.scrollBy(0, {pixels});")

def type_text(driver, xpath, text):
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    element.send_keys(text)

def press_enter(driver):
    actions = webdriver.ActionChains(driver)
    actions.send_keys(Keys.ENTER)
    actions.perform()

screenshot("https://amazon.ca")
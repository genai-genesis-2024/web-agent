# functions.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def initialize_driver():
    driver = webdriver.Chrome() 
    return driver

def screenshot(URL):
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    driver.set_window_size(1200, 1200)
    driver.save_screenshot("screenshots/screenshot.jpg")
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
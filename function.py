# functions.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import uuid
import os
from google.cloud import storage
from dotenv import load_dotenv
import gemini_vision
import json

load_dotenv()

GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.environ.get("GOOGLE_LOCATION")

def initialize_driver():
    options = webdriver.ChromeOptions()
    options.headless = True
    # options.add_argument("--headless=false")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    # TODO: The demo person need to update the binary_location and user-data-dir
    # options.binary_location = r"C:/Users/vince/AppData/Local/Google/Chrome SxS/Application/chrome.exe"
    # Maybe specify the profile directory "/Profile 1"
    # options.add_argument(r"user-data-dir=C:/Users/vince/AppData/Local/Google/Chrome SxS/User Data")
    # options.add_argument("--profile-directory=Default");

    driver = webdriver.Chrome(options=options)
    return driver

def click_element_by_LLM_link_text(driver, text):
    try:
        # Using XPath to find an element with a specific LLM-link-text attribute
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//*[@LLM-link-text='{text}']"))
        )
        element.click()
    except Exception as e:
        print(f"Error clicking on element with text '{text}': {e}")

def verify_highlights_and_labels(driver):
    modified_elements = driver.find_elements(By.CSS_SELECTOR, 'a, button, input, [role="link"], [role="button"]')
    for element in modified_elements:
        llm_link_text = element.get_attribute('LLM-link-text')
        border_style = element.value_of_css_property('border')
        if llm_link_text:
            print(f"Element text: '{llm_link_text}', Border style: '{border_style}'")

def prepare_element_data_for_gemini(driver):
    modified_elements = driver.find_elements(By.CSS_SELECTOR, 'a, button, input, [role="link"], [role="button"]')
    
    queries = []
    
    for element in modified_elements:
        llm_link_text = element.get_attribute('LLM-link-text')
        if llm_link_text:
            queries.append({
                'type': 'text', 
                'content': llm_link_text.strip()
            })
    return queries

def screenshot_with_highlights_and_labels(URL):
    driver = initialize_driver()
    driver.get(URL)
    driver.maximize_window()

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, "body")))

    highlight_and_label_script = """
    document.querySelectorAll('a, button, input, [role="link"], [role="button"]').forEach(function(element) {
        element.style.border = '2px solid red';
        let linkText = element.textContent.replace(/\\s+/g, ' ').trim();
        element.setAttribute('LLM-link-text', linkText);
    });
    """
    driver.execute_script(highlight_and_label_script) 

    # Test
    verify_highlights_and_labels(driver)

    queries = prepare_element_data_for_gemini(driver)
    # response = gemini_vision.call_gemini_vision(project_id=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION, queries=queries)


    os.makedirs("screenshots", exist_ok=True)
    filename = f"screenshots/screenshot_{str(uuid.uuid4())}.png"
    driver.save_screenshot(filename)

    # upload_to_storage(filename)
    

    ## ToDO: upload each of these screenshots to Google cloud storage 




# this is gor uplpoading to storage 
def upload_to_storage(filename):
    client = storage.Client()
    bucket_name = "bucket-name"
    bucket = client.bucket(bucket_name)

    blob_name = os.path.basename(filename)
    blob = bucket.blob(blob_name)

    with open(filename, "rb") as file:
        blob.upload_from_file(file)

    print(f"Screenshot uploaded to Google Cloud Storage: {blob_name}")


# test this , 
def get_latest_screenshot():
    client = storage.Client()
    bucket_name = "bucket-name"
    bucket = client.bucket(bucket_name)

    blobs = list(bucket.list_blobs(prefix="screenshot_"))
    latest_blob = max(blobs, key=lambda blob: blob.time_created)

    filename = f"screenshots/{latest_blob.name}"
    latest_blob.download_to_filename(filename)

    return filename



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

if __name__ == "__main__":
    screenshot_with_highlights_and_labels( "http://amazon.ca")


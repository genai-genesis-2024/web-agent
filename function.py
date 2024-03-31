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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException

load_dotenv()

GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.environ.get("GOOGLE_LOCATION")

def initialize_driver():
    options = webdriver.ChromeOptions()
    options.headless = True
    # options.add_argument("--headless=false")
    options.add_argument("--disable-extensions")
    # options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    # TODO: The demo person need to update the binary_location and user-data-dir
    options.binary_location = r"C:/Users/vince/AppData/Local/Google/Chrome SxS/Application/chrome.exe"
    # Maybe specify the profile directory "/Profile 1"
    options.add_argument(r"user-data-dir=C:/Users/vince/AppData/Local/Google/Chrome SxS/User Data")
    options.add_argument("--profile-directory=Default");

    driver = webdriver.Chrome(options=options)
    return driver

def generate_simple_xpath(element):
    tag = element.tag_name
    element_id = element.get_attribute('id')
    element_name = element.get_attribute('name')
    class_names = element.get_attribute('class').split() 

    if element_id:
        return f"//*[@id='{element_id}']"
    elif element_name:
        return f"//{tag}[@name='{element_name}']"
    elif class_names:
        return f"//{tag}[contains(@class, '{class_names[0]}')]"
    else:
        return f"//{tag}"

def prepare_element_data_for_gemini(driver):
    modified_elements = driver.find_elements(By.CSS_SELECTOR, 'a, button, input, [role="link"], [role="button"]')
    queries = []
    
    for element in modified_elements:
        element_data = {}
        
        # Attributes that do not require special conditions
        for attr in ['id', 'type', 'placeholder']:
            value = element.get_attribute(attr)
            if value:
                element_data[attr] = value

        element_text = element.text.strip()
        if element_text:
            element_data['text'] = element_text

        # Special handling for 'llm-link-text', check for non-empty value immediately
        llm_link_text = element.get_attribute('llm-link-text')
        if llm_link_text:
            element_data['llm_link_text'] = llm_link_text.strip()
        else:
            continue

        if element_data:
            queries.append(element_data)
    return queries

def navigate_to_URL(driver, URL):
    driver.get(URL)
    driver.maximize_window()

def screenshot_with_highlights_and_labels(driver):
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, "body")))
    highlight_and_label_script = """
    document.querySelectorAll('a, button, input, [role="link"], [role="button"]').forEach(function(element) {
        element.style.border = '2px solid red';
        let idContent = element.id.trim();
        let textContent = element.textContent.replace(/\\s+/g, ' ').trim();
        let placeholderContent = element.placeholder ? element.placeholder.trim() : '';
        // let tagNameContent = element.tagName.toLowerCase();
        let contentToUse = '';

        if (idContent) {
            contentToUse = 'ID:' + idContent; // Prefer ID if available
        } else if (element.tagName.toLowerCase() === 'input' && placeholderContent) {
            contentToUse = 'Placeholder:' + placeholderContent;
        } else if (textContent) {
            contentToUse = 'Text:' + textContent; // Then textContent for other elements
        } 
        // else {
        //     contentToUse = 'Tag:' + tagNameContent; // Fallback to tagName
        // }

        if (contentToUse) {
            element.setAttribute('llm-link-text', contentToUse);
        }
    });
    """
    driver.execute_script(highlight_and_label_script) 
    queries = prepare_element_data_for_gemini(driver)
    # print(queries)
    os.makedirs("screenshots", exist_ok=True)
    filename = f"screenshots/screenshot_{str(uuid.uuid4())}.png"
    driver.save_screenshot(filename)
    # upload_to_storage(filename)
    ## ToDO: upload each of these screenshots to Google cloud storage 
    return queries

def wait_for_custom_event(driver, css_selector, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )
        print(f"Event occurred: element with selector {css_selector} is present.")
    except TimeoutException:
        print(f"Timeout waiting for event: element with selector {css_selector} did not appear within {timeout} seconds.")


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

def click_element_with_LLM_link_text(driver, llm_link_text):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//*[@llm-link-text='{llm_link_text}']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        element.click()
    except Exception as e:
        print(f"Unexpected error clicking on element with llm-link-text '{llm_link_text}': {e}")

# def click_element(driver, xpath):
#     element = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.XPATH, xpath))
#     )
#     element.click()

def type_text_with_LLM_link_text(driver, llm_link_text, text):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//*[@llm-link-text='{llm_link_text}']"))
        )
        element.clear()
        element.send_keys(text)
        print(f"Typed '{text}' into input with llm-link-text: '{llm_link_text}'")
    except Exception as e:
        print(f"Error typing text into input: {e}")

# def type_text(driver, xpath, text):
#     element = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.XPATH, xpath))
#     )
#     element.send_keys(text)

def scroll_page(driver, pixels):
    driver.execute_script(f"window.scrollBy(0, {pixels});")

def press_enter(driver):
    actions = webdriver.ActionChains(driver)
    actions.send_keys(Keys.ENTER)
    actions.perform()




import function
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
import time

def determine_next_click(queries):
    # Implement your user intent
    # replace with actual decision making logic with gemini stuff
    return "Returns & Orders"

def main(driver, initial_url):
    function.navigate_to_URL(driver, initial_url)
    
    # while True:
    try:
        queries = function.screenshot_with_highlights_and_labels(driver)
        print("Screenshot taken with highlights and labels.")
        
        # Here, determine the next action based on `queries` or another condition
        next_click_text = determine_next_click(queries)
        # if not next_click_text:
        #     print("No more actions. Stopping the loop.")
        #     break
        function.type_text_with_LLM_link_text(driver, "ID:twotabsearchtextbox", "book")
        function.press_enter(driver)
        # TODO: Everytime a new page is loaded, we need to re-capture the screenshot
        queries = function.screenshot_with_highlights_and_labels(driver)
        function.scroll_page(driver, 1000)
        time.sleep(5)
        function.click_element_with_LLM_link_text(driver, "ID:nav-orders")
        # print(f"Clicked on element: {next_click_text}")
    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error occurred: {e}. Stopping the loop.")
        # break

if __name__ == "__main__":
    driver = function.initialize_driver()
    try:
        main(driver, "http://amazon.ca")
    finally:
        driver.quit()
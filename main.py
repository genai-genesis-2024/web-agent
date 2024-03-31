import function
from Speech_to_text import start_streaming
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
import re
import json
from pydantic import BaseModel, ValidationError
from typing import List, Dict
from Speech_to_text import start_streaming, delete_last_word
from text_to_speech import speak_text

load_dotenv()

GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.environ.get("GOOGLE_LOCATION")


class GoogleVertexAIModel:
    def __init__(self, project_id: str = GOOGLE_PROJECT_ID, location: str = GOOGLE_LOCATION,
                 model: str = "gemini-1.0-pro"):
        vertexai.init(project=project_id, location=location)
        model_instance = GenerativeModel(model)
        self.client = model_instance.start_chat()
        self.model = model

    def call(self, prompt: str) -> str:
        response = self.client.send_message(prompt)
        return response.text

    def json_call(self, prompt: str, sys_msg: str, model_class, model_instance) -> str:
        model_json_format = GoogleVertexAIModel.model_to_json(model_instance)
        prompt_template = f"""System Instruction:
        {sys_msg}
        Output JSON Format:
        {model_json_format}
        User Instruction:
        {prompt}
        """
        print(prompt_template)
        response = self.client.send_message(prompt_template)
        text_response = response.text
        print("text_response:")
        print(text_response)
        json_response = GoogleVertexAIModel.extract_json(text_response)
        print("json_response:")
        print(json_response)
        validated_data, validation_errors = GoogleVertexAIModel.validate_json_with_model(model_class, json_response)
        if len(validation_errors) == 0:
            return validated_data
        else:
            for error in validation_errors:
                print("Validation error:", error)
            return None

    @staticmethod
    def model_to_json(model_instance):
        return model_instance.model_dump_json()

    @staticmethod
    def extract_json(text_response):
        pattern = r'\{[^{}]*\}'
        matches = re.finditer(pattern, text_response)
        json_objects = []
        for match in matches:
            json_str = match.group(0)
            try:
                json_obj = json.loads(json_str)
                json_objects.append(json_obj)
            except json.JSONDecodeError:
                extended_json_str = GoogleVertexAIModel.extend_search(text_response, match.span())
                try:
                    json_obj = json.loads(extended_json_str)
                    json_objects.append(json_obj)
                except json.JSONDecodeError:
                    continue
        if json_objects:
            return json_objects
        else:
            return None

    @staticmethod
    def extend_search(text, span):
        start, end = span
        nest_count = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                nest_count += 1
            elif text[i] == '}':
                nest_count -= 1
            if nest_count == 0:
                return text[start:i + 1]
        return text[start:end]

    @staticmethod
    def json_to_pydantic(model_class, json_data):
        try:
            model_instance = model_class(**json_data)
            return model_instance
        except ValidationError as e:
            print("Validation error:", e)
            return None

    @staticmethod
    def validate_json_with_model(model_class, json_data):
        validated_data = []
        validation_errors = []
        if isinstance(json_data, list):
            for item in json_data:
                try:
                    model_instance = model_class(**item)
                    validated_data.append(model_instance.dict())
                except ValidationError as e:
                    validation_errors.append({"error": str(e), "data": item})
        elif isinstance(json_data, dict):
            try:
                model_instance = model_class(**json_data)
                validated_data.append(model_instance.dict())
            except ValidationError as e:
                validation_errors.append({"error": str(e), "data": json_data})
        else:
            raise ValueError("Invalid JSON data type. Expected dict or list.")
        return validated_data, validation_errors


def generate_text(prompt: str) -> str:
    gemini_model_instance = GoogleVertexAIModel(project_id=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)
    response = gemini_model_instance.call(prompt=prompt)
    return response


def determine_next_action(queries, user_intent):
    sys_msg = """
    You are an AI assistant that helps users navigate websites based on their intent, and you only return in a JSON formatand only JSON format.
    Analyze the user's intent and the available queries to determine the next action to take on the website.
    Consider the following guidelines:
    - If the user wants to search for something, identify the search input field and return the appropriate 'llm_link_text', 'type' action and the 'data_value', the data_value is what you want to search make it concise . 'type' actions ALWAYS return a data_value. 'type' actions are ALWAYS followed by the 'enter' action
    - If the user wants to navigate to a specific section or product, identify the relevant link or button and return the 'llm_link_text' and 'click' action.
    - If scrolling is required to view more content, return the 'scroll' action.
    - If 'enter' is required to select button, return the 'enter' action.
    - If the user's intent is unclear or cannot be fulfilled with the available queries, return the 'listen' action to get more instructions from the user.
    """

    input_text = f"""
    System Message: {sys_msg}

    User Intent: {user_intent}
    Queries: {queries}

    Determine the next action based on the user intent and the available queries. Return the action type (click, scroll, type, enter, listen) and the corresponding 'llm_link_text' value.
    For example: if the next step is to search for a book, then look for texts that are similar to search and extract the 'llm_link_text' of the search input field.
    Notice that in the queries, there might be an entry like 'id': 'twotabsearchtextbox', 'type': 'text', 'placeholder': 'Search Amazon.ca', 'llm_link_text': 'ID:twotabsearchtextbox'.
    In this case, you would return 'ID:twotabsearchtextbox' as the 'llm_link_text' and 'type' as the 'action_type' and 'book' as the data_value.
    """
    #input_text = f"User Intent: {user_intent}\nQueries: {queries}\n\nDetermine the next action based on the user intent and the available queries. Return the action type (click, scroll, type, enter) and the corresponding 'llm_link_text' value. For example: if the next steps is to search for a book, then look the texts that ae similar to search and then get extract the llm_link_text of the search , notice that is in here 'id': 'twotabsearchtextbox', 'type': 'text', 'placeholder': 'Search Amazon.ca', 'llm_link_text': 'ID:twotabsearchtextbox' so you would return twotabsearchtextbox as the llm_link_text and type in action_type"

    response = generate_text(input_text)
    print(response)

    try:
            json_response = json.loads(response)
            print(json_response)
            action_type = json_response.get("action_type")
            llm_link_text = json_response.get("llm_link_text")
            result = (action_type, llm_link_text)

            # Check if 'data_value' is present in the response
            if 'data_value' in json_response:
                data_value = json_response['data_value']
                result += (data_value,)

            return result

    except json.JSONDecodeError:
        print("Error: Invalid JSON response from LLM")
        return None, None


def agent_text_to_speech(text):  # this function will be called at the beginning of all request, first interaction of agent and user
    speak_text(text)
    user_intent_unclean = start_streaming()
    user_intent = delete_last_word(user_intent_unclean)
    return user_intent


def failed_announcement():  # call this function whenever the agent wants to announce a failure
    speak_text("Action failed")


def complete_announcement(): # call this function whenever the agent wants to announce a complete task
    speak_text("Action completed")


def main(driver, initial_url, user_intent):
    function.navigate_to_URL(driver, initial_url)

    try:
        queries = function.screenshot_with_highlights_and_labels(driver)
        print("Screenshot taken with highlights and labels.")

        # The function might return two or three values depending on the presence of 'data_value'
        action_info = determine_next_action(queries, user_intent)
        action_type, llm_link_text = action_info[:2]  # Always get these two values

        print(action_type)
        print(llm_link_text)

        if action_type == "click":
            function.click_element_with_LLM_link_text(driver, llm_link_text)
            print(f"Clicked on element: {llm_link_text}")
        elif action_type == "scroll":
            function.scroll_page(driver, 1000)
            print("Scrolled the page")
        elif action_type == "type":
            # Check if 'data_value' was returned and use it
            if len(action_info) == 3:
                data_value = action_info[2]
                function.type_text_with_LLM_link_text(driver, llm_link_text, data_value)
                print(f"Typed '{data_value}' into element: {llm_link_text}")
            else:
                print("Data value not provided for typing action.")
        elif action_type == "enter":
            function.press_enter(driver)
            print("Pressed Enter")
        elif action_type == "listen":
            print("No valid action determined. Waiting for user input.")
            user_input = start_streaming()
            print(f"User input: {user_input}")
        else:
            print("No valid action determined. Stopping the loop.")

    except (NoSuchElementException, TimeoutException) as e:
        print(f"Error occurred: {e}. Stopping the loop.")


if __name__ == "__main__":
    driver = function.initialize_driver()
    # user_intent = "Search for a book on Amazon"
    user_intent = agent_text_to_speech("How can I help you? Start saying your request and when you finish, say quit")
    try:
        main(driver, "http://amazon.ca", user_intent)
    finally:
        driver.quit()

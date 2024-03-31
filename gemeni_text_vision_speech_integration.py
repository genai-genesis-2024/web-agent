import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
import re
import json
from pydantic import BaseModel, ValidationError
from typing import List
from function import get_latest_screenshot,screenshot_with_highlights_and_labels,scroll_page,click_element,press_enter,type_text, initialize_driver


load_dotenv()

# NOTE: If you are running the code locally, authenticate with gcloud cli before running the code
GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.environ.get("GOOGLE_LOCATION")

class ActionPlanModel(BaseModel):
    actions: List[str]

class ActionFunctionModel(BaseModel):
    function_name: str
    parameters: dict

class ActionFunctionsModel(BaseModel):
    action_functions: List[ActionFunctionModel]


# we only need to be running gemini vision pro 
class GeminiTextModel:
    def __init__(self, project_id: str = GOOGLE_PROJECT_ID, location: str = GOOGLE_LOCATION, model: str = "gemini-1.0-pro-vision"):
        vertexai.init(project=project_id, location=location)
        model_instance = GenerativeModel(model)
        self.client = model_instance.start_chat()
        self.model = model
      
    def call(self, prompt: str) -> str:
        response = self.client.send_message(prompt)
        return response.text

    def json_call(self, prompt: str, sys_msg: str, model_class, model_instance) -> str:
        model_json_format = GeminiTextModel.model_to_json(model_instance)
        prompt_template = f"""System Instruction:
{sys_msg}

Output JSON Format:
{model_json_format}

User Instruction:
{prompt}
"""
        #print(prompt_template)
        response = self.client.send_message(prompt_template)
        text_response = response.text
        #print("text_response:")
        #print(text_response)
        json_response = GeminiTextModel.extract_json(text_response)
        #print("json_response:")
       # print(json_response)
        validated_data, validation_errors = GeminiTextModel.validate_json_with_model(model_class, json_response)
        if len(validation_errors) == 0:
            return validated_data
        else:
            for error in validation_errors:
                print("Validation error:", error)
            return None

    def model_to_json(model_instance):
        """
        Converts a Pydantic model instance to a JSON string.

        Args:
            model_instance (YourModel): An instance of your Pydantic model.

        Returns:
            str: A JSON string representation of the model.
        """
        return model_instance.model_dump_json()

    def extract_json(text_response):
        # This pattern matches a string that starts with '{' and ends with '}'
        pattern = r'\{[^{}]*\}'

        matches = re.finditer(pattern, text_response)
        json_objects = []

        for match in matches:
            json_str = match.group(0)
            try:
                # Validate if the extracted string is valid JSON
                json_obj = json.loads(json_str)
                json_objects.append(json_obj)
            except json.JSONDecodeError:
                # Extend the search for nested structures
                extended_json_str = GeminiTextModel.extend_search(text_response, match.span())
                try:
                    json_obj = json.loads(extended_json_str)
                    json_objects.append(json_obj)
                except json.JSONDecodeError:
                    # Handle cases where the extraction is not valid JSON
                    continue

        if json_objects:
            return json_objects
        else:
            return None  # Or handle this case as you prefer

    def extend_search(text, span):
        # Extend the search to try to capture nested structures
        start, end = span
        nest_count = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                nest_count += 1
            elif text[i] == '}':
                nest_count -= 1
                if nest_count == 0:
                    return text[start:i+1]
        return text[start:end]


    def json_to_pydantic(model_class, json_data):
        try:
            model_instance = model_class(**json_data)
            return model_instance
        except ValidationError as e:
            print("Validation error:", e)
            return None
        


    

    def generate_action_plan(user_input, screen_shot):
        gemini_model_instance = GeminiTextModel(project_id=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)
        prompt = f"User input: {user_input}\nGenerate an action plan to perform the user's request based on the user input and the screenshot {screen_shot}. Make granulated responses based on the screenshot on the exact action you will take"
        sys_msg = "Output your response as a list of actions in JSON format and don't put ANY other texts"
        
        sample_action_plan = ["Go to amazon.com", "Search for the product in the search bar", "Ask the user which book to buy", "Add the product to the cart", "Proceed to checkout"]
        action_plan_instance = ActionPlanModel(actions=sample_action_plan)
        
        response = gemini_model_instance.json_call(
            prompt=prompt,
            sys_msg=sys_msg,
            model_class=ActionPlanModel,
            model_instance=action_plan_instance
        )
        
        return response

    def map_actions_to_functions(action_plan):
        gemini_model_instance = GeminiTextModel(project_id=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)
        prompt = f"Map each action item in the following action plan to one of the possible action functions (click_element, scroll_page, type_text, press_enter) and provide the necessary parameters for each function:\n\n{action_plan}"
        sys_msg = "Output your response as a list of dictionaries in JSON format, where each dictionary contains the 'function_name' and 'parameters' keys. Don't put ANY other text."
        
        sample_action_functions = [
            {"function_name": "click_element", "parameters": {"xpath": "//a[@href='/']"}},
            {"function_name": "type_text", "parameters": {"xpath": "//input[@id='search']", "text": "book title"}},
            {"function_name": "click_element", "parameters": {"xpath": "//button[@id='add-to-cart']"}},
            {"function_name": "click_element", "parameters": {"xpath": "//a[@href='/checkout']"}}
        ]
        action_functions_instance = ActionFunctionsModel(action_functions=[ActionFunctionModel(**action_function) for action_function in sample_action_functions])
        
        response = gemini_model_instance.json_call(
            prompt=prompt,
            sys_msg=sys_msg,
            model_class=ActionFunctionModel,      
             model_instance=action_functions_instance.action_functions[0]
        )
        
        if response is None:
            return None
        
        action_functions = []
        for action_function in response:
            if not isinstance(action_function, dict):
                print(f"Invalid action function format: {action_function}")
                continue
            
            if "function_name" not in action_function or "parameters" not in action_function:
                print(f"Missing 'function_name' or 'parameters' key in action function: {action_function}")
                continue
            
            try:
                action_functions.append(ActionFunctionModel(**action_function))
            except ValidationError as e:
                print(f"Validation error: {e}")
        
        return action_functions

    def execute_action_functions(action_functions, driver):
        for action_function in action_functions:
            function_name = action_function["function_name"]
            parameters = action_function["parameters"]
            
            if function_name == "click_element":
                click_element(driver, parameters["xpath"])
            elif function_name == "scroll_page":
                scroll_page(driver, parameters["pixels"])
            elif function_name == "type_text":
                type_text(driver, parameters["xpath"], parameters["text"])
            elif function_name == "press_enter":
                press_enter(driver)



    def validate_json_with_model(model_class, json_data):
        """
        Validates JSON data against a specified Pydantic model.

        Args:
            model_class (BaseModel): The Pydantic model class to validate against.
            json_data (dict or list): JSON data to validate. Can be a dict for a single JSON object, 
                                      or a list for multiple JSON objects.

        Returns:
            list: A list of validated JSON objects that match the Pydantic model.
            list: A list of errors for JSON objects that do not match the model.
        """
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

if __name__ == "__main__":
    gemini_model_instance = GeminiTextModel(project_id=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)
    ## test 3 

    user_input =  " i want to buy the graduate texts in mathematics in amazon"

    action_plan =GeminiTextModel.generate_action_plan(user_input, get_latest_screenshot())
    print("Action Plan:")
    print(action_plan)
    
    action_functions = GeminiTextModel.map_actions_to_functions(action_plan)
    print("Action Functions:")
    print(action_functions)
    
    #driver = initialize_driver()  # Initialize the Selenium webdriver
    #GeminiTextModel.execute_action_functions(action_functions, driver)
    #driver.quit()


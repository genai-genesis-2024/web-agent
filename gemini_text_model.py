import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
import re
import json
from pydantic import BaseModel, ValidationError
from typing import List

load_dotenv()

# NOTE: If you are running the code locally, authenticate with gcloud cli before running the code
GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.environ.get("GOOGLE_LOCATION")

class GeminiTextModel:
    def __init__(self, project_id: str = GOOGLE_PROJECT_ID, location: str = GOOGLE_LOCATION, model: str = "gemini-1.0-pro"):
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
        print(prompt_template)
        response = self.client.send_message(prompt_template)
        text_response = response.text
        print("text_response:")
        print(text_response)
        json_response = GeminiTextModel.extract_json(text_response)
        print("json_response:")
        print(json_response)
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
    # Normal Call Test
    prompt = "What is the capital of France?"
    response = gemini_model_instance.call(prompt=prompt)
    print(response)

    # JSON Call Test No.1
    prompt = "Can you generate some fantasy character names?"
    sys_msg = "Output your response as JSON following the specified format."
    # Define your Pydantic model
    class NamesModel(BaseModel):
        names: List[str]
    sample_names = ["Aragorn", "Legolas", "Gandalf"]
    names_model_instance = NamesModel(names=sample_names)
    response = gemini_model_instance.json_call(
        prompt=prompt, sys_msg=sys_msg, model_class=NamesModel, model_instance=names_model_instance
    )
    print(response)

    # JSON Call Test No.2
    prompt = "Can you generate some profiles with \"name\" and \"age\"?"
    sys_msg = "Output your response as JSON following the specified format."
    # Define your Pydantic model
    class ProfileModel(BaseModel):
        name: str
        age: int
    class ProfilesModel(BaseModel):
        profiles: List[ProfileModel]
    sample_profiles = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
    profiles_model_instance = ProfilesModel(profiles=[ProfileModel(**profile) for profile in sample_profiles])
    response = gemini_model_instance.json_call(
        prompt=prompt, sys_msg=sys_msg, model_class=ProfileModel, model_instance=profiles_model_instance
    )
    print(response)

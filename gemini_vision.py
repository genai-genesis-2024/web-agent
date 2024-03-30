import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from typing import List, Dict

load_dotenv()

# NOTE: If you are running the code locally, authenticate with gcloud cli before running the code
GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.environ.get("GOOGLE_LOCATION")

def call_gemini_vision(project_id: str, location: str, queries: List[Dict[str, str]]) -> str:
    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)
    # Load the model
    multimodal_model = GenerativeModel("gemini-1.0-pro-vision")

    contents = []
    for query in queries:
        if query['type'] == 'image':
            contents.append(Part.from_uri(query['content'], mime_type="image/jpeg"))
        elif query['type'] == 'text':
            contents.append(query['content'])
        else:
            raise ValueError(f"Invalid query type: {query['type']}")
    
    # Query the model
    response = multimodal_model.generate_content(contents)
    return response.text

if __name__ == "__main__":
  # Vision Call Test
  queries = [
      {'type': 'image', 'content': 'gs://generativeai-downloads/images/scones.jpg'},
      {'type': 'text', 'content': 'what is shown in this image?'},
  ]
  response = call_gemini_vision(project_id=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION, queries=queries)
  print(response)

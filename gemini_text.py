import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

load_dotenv()

# NOTE: If you are running the code locally, authenticate with gcloud cli before running the code
GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.environ.get("GOOGLE_LOCATION")
vertexai.init(project=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)

class GoogleVertexAIModel:
  def __init__(self, project_id: str = GOOGLE_PROJECT_ID, location: str = GOOGLE_LOCATION, model: str = "gemini-1.0-pro"):
    vertexai.init(project=project_id, location=location)
    model_instance = GenerativeModel(model)
    self.client = model_instance.start_chat()
    self.model = model
  
  def call(self, prompt: str) -> str:
    response = self.client.send_message(prompt)
    return response.text

if __name__ == "__main__":
  gemini_text_instance = GoogleVertexAIModel(project_id=GOOGLE_PROJECT_ID, location=GOOGLE_LOCATION)
  gemini_text_instance.call("Hey Gemini!")

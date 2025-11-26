import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

# Load Environment Variables
load_dotenv()

# --- Configuration ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION")
CREDENTIALS_FILE = 'google_credentials.json'

# Files and Directories
DATA_FILE = "K_research_data.xlsx"
PLOTS_DIR = "plots"
DOCS_DIR = "documents"
OUTPUT_FILE = os.path.join(DOCS_DIR, "evaluation_results.xlsx")

# --- Vertex AI Connection ---
print("Connecting to Vertex AI...")
try:
    # Handle Cloud Deployment (Render/Heroku)
    # If the file doesn't exist, try to create it from the environment variable
    if not os.path.exists(CREDENTIALS_FILE):
        json_creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if json_creds:
            print("Found GOOGLE_CREDENTIALS_JSON env var, creating credentials file...")
            with open(CREDENTIALS_FILE, "w") as f:
                f.write(json_creds)
        else:
            print(f"Warning: {CREDENTIALS_FILE} not found and GOOGLE_CREDENTIALS_JSON not set.")

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_FILE
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print(f"Successfully connected to Vertex AI (Project: {PROJECT_ID})")
except Exception as e:
    print(f"Failed to connect to Vertex AI: {e}")

# --- Model Initialization ---
def get_model():
    return GenerativeModel(
        "gemini-2.5-flash-preview-09-2025",
        generation_config=GenerationConfig(temperature=0.0, top_p=0.8, max_output_tokens=1024)
    )

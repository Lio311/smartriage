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
        generation_config=GenerationConfig(temperature=0.0, top_p=0.8, max_output_tokens=1024)
    )

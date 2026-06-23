# Paths, environment variables, settings

from pathlib import Path
import os

# SRC_DIR is the directory containing this config file
SRC_DIR = Path(__file__).resolve().parent
ROOT_FOLDER = SRC_DIR.parent

# Directories
DATA_FOLDER = ROOT_FOLDER / "data"
VECTOR_STORE_FOLDER = ROOT_FOLDER / "vector_store"
OUTPUT_FOLDER = ROOT_FOLDER / "outputs"

# Files
STAKEHOLDER_REGISTER_PATH = DATA_FOLDER / "Stakeholder_Register.csv"
STAKEHOLDER_PLAN_PATH = DATA_FOLDER / "Stakeholder_Engagement_Plan.md"
MEETING_NOTES_PATH = DATA_FOLDER / "Meeting_Notes.md"
DATABASE_FILE_DESTINATION = VECTOR_STORE_FOLDER / "global_vector_store.json"
STAKEHOLDER_GAP_REPORT_PATH = OUTPUT_FOLDER / "STAKEHOLDER_GAP_REPORT.txt"

# Constants
KNOWN_STAKEHOLDERS = {"Liam Patel", "Fatima Al-Sayed", "John Doe"}
# Keep using os.environ for keys as it's the standard for env vars
API_KEY = os.environ.get("OPENAI_API_KEY", "mock-key-for-local-ui-safety")
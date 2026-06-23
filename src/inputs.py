# File I/O and data loading logic

from src.config import DATA_FOLDER, VECTOR_STORE_FOLDER, OUTPUT_FOLDER, STAKEHOLDER_REGISTER_PATH, MEETING_NOTES_PATH, STAKEHOLDER_PLAN_PATH
import pandas as pd

def initialize_environment():
    """Ensure all required directories exist."""
    for folder in [DATA_FOLDER, VECTOR_STORE_FOLDER, OUTPUT_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)

def populate_sample_data():
    """Populate sample files if they do not exist."""
    if not STAKEHOLDER_REGISTER_PATH.exists():
        pd.DataFrame([
            {"name": "Priya Sharma", "role": "Technical Lead", "influence": "High", "interest": "High", "desired_engagement": "Manage Closely"},
            {"name": "Helen Brooks", "role": "Compliance Director", "influence": "High", "interest": "Medium", "desired_engagement": "Keep Satisfied"},
            {"name": "David Vance", "role": "Operations Manager", "influence": "Medium", "interest": "High", "desired_engagement": "Keep Informed"}
        ]).to_csv(STAKEHOLDER_REGISTER_PATH, index=False)

    if not MEETING_NOTES_PATH.exists():
        MEETING_NOTES_PATH.write_text("# Project Sync Notes\nDate: June 15, 2026\n...", encoding="utf-8")

    if not STAKEHOLDER_PLAN_PATH.exists():
        STAKEHOLDER_PLAN_PATH.write_text("# Stakeholder Engagement Strategy\n...", encoding="utf-8")
import pandas as pd
from pathlib import Path
from src.config import (
    DATA_FOLDER,
    VECTOR_STORE_FOLDER,
    OUTPUT_FOLDER,
    STAKEHOLDER_REGISTER_PATH,
    STAKEHOLDER_PLAN_PATH,
    MEETING_NOTES_PATH
)


# --- Environment Setup ---
def initialize_environment():
    """Ensure all required project directories exist."""
    for folder in [DATA_FOLDER, VECTOR_STORE_FOLDER, OUTPUT_FOLDER]:
        folder.mkdir(parents=True, exist_ok=True)


def populate_sample_data():
    """Populate sample files if they do not exist for testing purposes."""
    if not STAKEHOLDER_REGISTER_PATH.exists():
        sample_df = pd.DataFrame([
            {"stakeholder_name": "Liam Patel", "role": "Technical Lead", "influence": "High", "interest": "High",
             "current_support": "Manage Closely"},
            {"stakeholder_name": "Fatima Al-Sayed", "role": "Compliance Director", "influence": "High",
             "interest": "Medium", "current_support": "Keep Satisfied"},
            {"stakeholder_name": "John Doe", "role": "Operations Manager", "influence": "Medium", "interest": "High",
             "current_support": "Keep Informed"}
        ])
        sample_df.to_csv(STAKEHOLDER_REGISTER_PATH, index=False)

    if not MEETING_NOTES_PATH.exists():
        MEETING_NOTES_PATH.write_text(
            "# Meeting Notes: June 2026\n- Liam Patel raised concerns about latency.\n- Fatima Al-Sayed requested an audit.",
            encoding="utf-8"
        )

    if not STAKEHOLDER_PLAN_PATH.exists():
        STAKEHOLDER_PLAN_PATH.write_text(
            "# Stakeholder Engagement Strategy\nGoal: Maintain high alignment.",
            encoding="utf-8"
        )


# --- Data Extraction (Repository Pattern) ---
def get_raw_register_data() -> pd.DataFrame:
    """Reads the stakeholder registry and standardizes column names."""
    if STAKEHOLDER_REGISTER_PATH.exists():
        # Load with utf-8-sig to handle invisible Byte Order Marks (BOM)
        df = pd.read_csv(STAKEHOLDER_REGISTER_PATH, encoding='utf-8-sig')

        # Standardize: strip whitespace, convert to lowercase, replace spaces with underscores
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        print(f"DEBUG: CSV Columns loaded as: {df.columns.tolist()}")
        return df
    return pd.DataFrame()


def get_raw_plan_text() -> str:
    """Reads the engagement plan as a raw string."""
    return STAKEHOLDER_PLAN_PATH.read_text(encoding="utf-8") if STAKEHOLDER_PLAN_PATH.exists() else ""


def get_raw_meeting_notes() -> list[str]:
    """Reads meeting notes and returns as a list of lines."""
    if MEETING_NOTES_PATH.exists():
        return MEETING_NOTES_PATH.read_text(encoding="utf-8").splitlines()
    return []
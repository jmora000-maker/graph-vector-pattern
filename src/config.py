import os
from datetime import date
from pathlib import Path
import pandas as pd
from openai import OpenAI

# --- PATH & ENVIRONMENT SETUP ---
today_obj = date.today()
today = today_obj.strftime("%B %d, %Y")

src_folder = Path(__file__).resolve().parent
root_folder = src_folder.parent
data_folder = root_folder / "data"
vector_store_folder = root_folder / "vector_store"
output_folder = root_folder / "outputs"

# --- Hardcoding files for demo ---
stakeholder_register_path = data_folder / "Stakeholder_Register.csv"
stakeholder_plan_path = data_folder / "Stakeholder_Engagement_Plan.md"
meeting_notes_path = data_folder / "Meeting_Notes.md"

folder_paths = [data_folder, vector_store_folder, output_folder]
for folder in folder_paths:
    folder.mkdir(parents=True, exist_ok=True)

stakeholder_gap_report_path = output_folder / "STAKEHOLDER_GAP_REPORT.txt"
database_file_destination = vector_store_folder / "global_vector_store.json"

KNOWN_STAKEHOLDERS = {"Liam Patel", "Fatima Al-Sayed", "John Doe"}

# Populate sample data if files do not exist
if not stakeholder_register_path.exists():
    pd.DataFrame([
        {"name": "Priya Sharma", "role": "Technical Lead", "influence": "High", "interest": "High",
         "desired_engagement": "Manage Closely"},
        {"name": "Helen Brooks", "role": "Compliance Director", "influence": "High", "interest": "Medium",
         "desired_engagement": "Keep Satisfied"},
        {"name": "David Vance", "role": "Operations Manager", "influence": "Medium", "interest": "High",
         "desired_engagement": "Keep Informed"}
    ]).to_csv(stakeholder_register_path, index=False)

if not meeting_notes_path.exists():
    meeting_notes_path.write_text("""# Project Sync Notes
Date: June 15, 2026
Attendees: Priya Sharma, David Vance, Liam Patel, Fatima Al-Sayed

## Discussion
- Priya Sharma raised repeated concerns regarding audit logging and access control architectures.
- Liam Patel coordinated infrastructure targets. Note: Liam is driving the vendor handoff framework.
- David Vance noted deep anxieties regarding training readiness and frontline deployment schedules.
- Fatima Al-Sayed flagged missing support scripts and overall enablement blockages.""", encoding="utf-8")

if not stakeholder_plan_path.exists():
    stakeholder_plan_path.write_text("""# Stakeholder Engagement Strategy
- Priya Sharma: Host tailored tech architectural readouts and align on access control mitigation structures. Owner: Tech PM. Cadence: Bi-weekly.
- Helen Brooks: Compliance engagement will be handled through existing governance channels.
- David Vance: Provide weekly hypercare visibility dashboards. Owner: Ops Lead.""", encoding="utf-8")

# --- INITIALIZE OPENAI CLIENT ---
api_key = os.environ.get("OPENAI_API_KEY", "mock-key-for-local-ui-safety")
is_vector_search_enabled = os.environ.get("OPENAI_API_KEY") is not None and os.environ.get(
    "OPENAI_API_KEY") != "mock-key-for-local-ui-safety"
client = OpenAI(api_key=api_key)
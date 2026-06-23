import pandas as pd
import streamlit as st
import contextlib
from src.config import data_folder, stakeholder_register_path, stakeholder_plan_path, meeting_notes_path
from src.pipeline import run_automated_pipeline
from src.utils import StreamlitStdoutRedirector


# --- STREAMLIT DASHBOARD INTERFACE ---
st.set_page_config(page_title="AI Stakeholder Alignment", layout="wide")
st.title("Stakeholder Alignment Dashboard")
st.caption("Real-time diagnostics to bridge the gap between project strategy and operational delivery.")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("System Configuration")

    # --- 2. Hardcoded File Loading Logic ---
    # Check if the data folder exists
    if data_folder.exists():

        st.text(f"Files found in '{data_folder.name}'")
        # iterdir() yields Path objects; we grab .name for just the filename
        files = [f.name for f in data_folder.iterdir()]
        st.write(files)

        # Verify the specific files exist before trying to read them
        if stakeholder_register_path.exists():
            # Read the CSV directly into a DataFrame
            df_register = pd.read_csv(stakeholder_register_path)
            # You can now use df_register throughout your app
        else:
            st.error(f"Missing file: {stakeholder_register_path.name}")

        if stakeholder_plan_path.exists():
            plan_content = stakeholder_plan_path.read_text(encoding="utf-8")

        if meeting_notes_path.exists():
            notes_content = meeting_notes_path.read_text(encoding="utf-8")
    else:
        st.error(f"Data directory '{data_folder}' does not exist. Please create it and add your files.")

    start_pipeline = st.button("Execute Stakeholder Alignment Pipeline", use_container_width=True, type="primary")

    st.subheader("Pipeline Summary")
    console_logs = st.empty()
    console_logs.info("Click 'Execute Stakeholder Alignment Pipeline' button to begin.")

with col2:
    st.subheader("Report Workspace")
    report_placeholder = st.empty()
    report_placeholder.info("The Stakeholder Alignment Report will populate here upon synthesis.")

    if start_pipeline:
        console_logs.empty()
        redirector = StreamlitStdoutRedirector(console_logs)
        redirector.reset()

        with st.spinner("Processing Stakeholder Alignment Pipeline..."):
            with contextlib.redirect_stdout(redirector):
                final_narrative = run_automated_pipeline()

        if final_narrative:
            with report_placeholder.container():
                st.html(
                    f"""
                                <div style="
                                    background-color: #1e293b; 
                                    color: #f8fafc; 
                                    padding: 20px; 
                                    border-radius: 8px; 
                                    height: 550px; 
                                    overflow-y: scroll; 
                                    white-space: pre-wrap; 
                                    font-family: inherit;
                                    border: 1px solid #334155;
                                    line-height: 1.5;
                                ">
                                    <p style="font-size: 16px !important; margin: 0; padding: 0;">{final_narrative}</p>
                                </div>
                                """
                )

                st.download_button(
                    label="Download Stakeholder Alignment Report (.txt)",
                    data=final_narrative,
                    file_name="stakeholder_alignment_report.txt",
                    mime="text/plain",
                    use_container_width=True
                )
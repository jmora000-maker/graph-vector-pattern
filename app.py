# Streamlit UI layer
import sys
from pathlib import Path
import contextlib
import streamlit as st

# Add the project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

# Import your pipeline
from src.inputs import initialize_environment, populate_sample_data, DATA_FOLDER
from src.pipeline import run_automated_pipeline

# --- UI CONFIGURATION ---
st.set_page_config(page_title="AI Stakeholder Alignment", layout="wide")


# --- UI LOGIC ---
class StreamlitStdoutRedirector:
    """Redirects stdout to a Streamlit code block for real-time logging."""

    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.output_str = ""

    def write(self, text):
        self.output_str += str(text)
        self.placeholder.code(self.output_str[-8000:], language="text")

    def flush(self):
        pass


def main():
    st.title("Stakeholder Alignment Dashboard")
    st.caption("Real-time diagnostics to bridge the gap between strategy and delivery.")
    st.markdown("---")

    # Ensure environment is ready
    initialize_environment()
    populate_sample_data()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("System Configuration")
        st.info(f"Data directory initialized at: `{DATA_FOLDER}`")

        start_pipeline = st.button("Execute Stakeholder Alignment Pipeline", type="primary", use_container_width=True)

        st.subheader("Pipeline Logs")
        console_logs = st.empty()

    with col2:
        st.subheader("Report Workspace")
        report_placeholder = st.empty()
        report_placeholder.info("Click 'Execute' to generate the report.")

        if start_pipeline:
            console_logs.info("Starting pipeline...")
            redirector = StreamlitStdoutRedirector(console_logs)

            with st.spinner("Processing..."):
                with contextlib.redirect_stdout(redirector):
                    # Call the stable pipeline
                    findings = run_automated_pipeline()

                    # Convert findings to a string narrative
                    final_narrative = "\n".join([f"{f.finding_id}: {f.observed_gap}" for f in findings])
                    if not findings:
                        final_narrative = "Audit complete: No strategic gaps detected."

            # Display final report
            report_placeholder.markdown("### Latest Report")
            report_placeholder.text_area("Report Content", final_narrative, height=500)

            st.download_button(
                label="Download Report (.txt)",
                data=final_narrative,
                file_name="stakeholder_alignment_report.txt",
                mime="text/plain",
                use_container_width=True
            )


if __name__ == "__main__":
    main()
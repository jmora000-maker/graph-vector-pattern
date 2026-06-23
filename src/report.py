from src.config import STAKEHOLDER_GAP_REPORT_PATH
from src.models import ExecutiveStakeholderGapReport
from datetime import date


def generate_formatted_report(structured_report: ExecutiveStakeholderGapReport) -> str:
    """Converts the structured object into a human-readable string and saves to disk."""
    today = date.today().strftime("%B %d, %Y")

    lines = [
        "================================================================================",
        "STAKEHOLDER ALIGNMENT REPORT",
        f"Report Date: {today}",
        f"Summary: Verified {len(structured_report.findings)} stakeholder alignment findings.",
        "================================================================================",
        "",
        "EXECUTIVE SUMMARY:",
        structured_report.executive_summary,
        "",
        "DETAILED FINDINGS BY CATEGORY",
        ""
    ]

    for finding in structured_report.findings:
        lines.append(f"{finding.gap_category}:")
        lines.append(f"Stakeholder: {finding.stakeholder_name}")
        lines.append(f"Issue: {finding.observed_gap}")
        lines.append(f"Operational Impact: {finding.practical_impact}")
        lines.append(f"Recommendation: {finding.recommended_action}")
        lines.append("")

    final_report_text = "\n".join(lines)

    # Save to disk
    STAKEHOLDER_GAP_REPORT_PATH.write_text(final_report_text, encoding="utf-8")

    return final_report_text
from src.config import stakeholder_gap_report_path, today
from src.models import ExecutiveStakeholderGapReport

def generate_executive_summary(structured_report: ExecutiveStakeholderGapReport) -> str:
    print(f" -> Re-applying structure and saving report to disk.")

    # Correctly access 'findings' instead of 'categories'
    total_findings = len(structured_report.findings)

    lines = [
        "================================================================================",
        "STAKEHOLDER ALIGNMENT REPORT",
        f"Report Date: {today}",
        f"Summary: Verified {total_findings} stakeholder alignment findings.",
        "================================================================================",
        "",
        "EXECUTIVE SUMMARY:",
        structured_report.executive_summary,
        "",
        "DETAILED FINDINGS BY CATEGORY",
        ""
    ]

    # Iterate over 'findings'
    for finding in structured_report.findings:
        lines.append(f"{finding.gap_category}:")
        lines.append(f"Stakeholder: {finding.stakeholder_name}")
        lines.append(f"Issue: {finding.observed_gap}")
        lines.append(f"Operational Impact: {finding.practical_impact}")
        lines.append(f"Recommendation: {finding.recommended_action}")
        lines.append("")

    final_report_text = "\n".join(lines)
    stakeholder_gap_report_path.write_text(final_report_text, encoding="utf-8")

    return final_report_text
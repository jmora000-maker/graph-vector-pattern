# OpenAI client and synthesis logic

import json
from typing import List, Dict
from openai import OpenAI
from src.config import API_KEY
from src.models import ExecutiveStakeholderGapReport, StakeholderGapReport

# Initialize client
client = OpenAI(api_key=API_KEY)
IS_ENABLED = API_KEY != "mock-key-for-local-ui-safety"

def fallback_synthesis(raw_findings: List[Dict]) -> ExecutiveStakeholderGapReport:
    """Provides a structural report when the LLM is unreachable."""
    findings = [StakeholderGapReport(**f) for f in raw_findings]
    return ExecutiveStakeholderGapReport(
        executive_summary="Automated structural diagnostics identified key stakeholder register exclusions, "
                         "strategic alignment gaps, and untracked architectural concerns.",
        findings=findings
    )

def synthesize_report_with_llm(compiled_raw_payload: Dict) -> ExecutiveStakeholderGapReport:
    """Interacts with OpenAI to synthesize the final executive report."""
    if not IS_ENABLED:
        return fallback_synthesis(compiled_raw_payload.get("findings", []))

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert Senior Program Leader. "
                        "1. Identify the top 2-3 'CRITICAL' stakeholders from the heatmap. "
                        "2. In your Executive Summary, explain their risk levels based on Influence vs. Concern count. "
                        "3. Provide a clear prioritization plan."
                    )
                },
                {
                    "role": "user",
                    "content": f"Review these gaps and produce the synthesis report:\n{json.dumps(compiled_raw_payload, indent=2)}"
                }
            ],
            response_format=ExecutiveStakeholderGapReport,
            temperature=0.1
        )
        return response.choices[0].message.parsed
    except Exception as e:
        print(f" -> LLM synthesis failed: {e}. Falling back.")
        return fallback_synthesis(compiled_raw_payload.get("findings", []))
import json
from typing import List, Dict, Set, Optional
from src.config import is_vector_search_enabled, client
from src.rag import SimpleVectorStore
from src.models import GapFinding, StakeholderGapReport, ExecutiveStakeholderGapReport

def compile_raw_payload(internal_findings: List[GapFinding], store: SimpleVectorStore, heatmap: List[Dict]) -> Dict:
    compiled_raw_payload = []

    for f in internal_findings:
        # Use the passed store variable for vector lookups
        vector_support = store.search(f.vector_evidence_queries[0], top_k=1) if f.vector_evidence_queries else []

        combined_evidence_items = []
        for pe in f.primary_deterministic_evidence:
            combined_evidence_items.append({"source": "Deterministic Fact Log", "snippet": pe})
        for vs in vector_support:
            combined_evidence_items.append({"source": f"RAG Context [{vs['source']}]", "snippet": vs["snippet"]})

        if not combined_evidence_items:
            combined_evidence_items.append({"source": "System Record",
                                            "snippet": "Calculated structural omission based on database log evaluation."})

        compiled_raw_payload.append({
            "gap_category": f.gap_category,
            "stakeholder_name": f.stakeholder_name,
            "severity": f.severity,
            "confidence": f.confidence,
            "observed_gap": f.observed_gap,
            "practical_impact": f.practical_impact,
            "recommended_action": f.recommended_action,
            "finding_id": f.finding_id,
            "evidence": combined_evidence_items
        })
    return {
        "findings": compiled_raw_payload,
        "strategic_heatmap": heatmap
    }



def synthesize_report_with_llm(compiled_raw_payload: Dict) -> ExecutiveStakeholderGapReport:
    # Use the globally configured client and capability flag
    print(" -> Sending raw payload to LLM for synthesis.")
    print(" -> Please wait a few moments.")
    if is_vector_search_enabled:
        try:
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                                "You are an expert Senior Program Leader. "
                                "You are provided with stakeholder gap findings and a 'Strategic Risk Heatmap'. "
                                "1. Use the Heatmap to identify the top 2-3 'CRITICAL' stakeholders. "
                                "2. In your Executive Summary, explicitly name these stakeholders and explain why they are at risk based on their Influence vs. Concern count. "
                                "3. Provide a clear prioritization plan."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Review these calculated stakeholder program management gaps and produce the clean final structured synthesis report:\n{json.dumps(compiled_raw_payload, indent=2)}"
                    }
                ],
                response_format=ExecutiveStakeholderGapReport,
                temperature=0.1
            )
            structured_report = response.choices[0].message.parsed
        except Exception as e:
            print(f" -> LLM parsing failed due to error: {e}. Slipping into fallback framework.")
            structured_report = fallback_synthesis(compiled_raw_payload['findings'])
    else:
        print(" -> Vector Search/API Key disabled. Utilizing native fallback framework.")
        structured_report = fallback_synthesis(compiled_raw_payload['findings'])
    return structured_report

def fallback_synthesis(raw_findings: List[Dict]) -> ExecutiveStakeholderGapReport:
    # 'findings' matches the ExecutiveStakeholderGapReport model field
    findings = [StakeholderGapReport(**f) for f in raw_findings]
    return ExecutiveStakeholderGapReport(
        executive_summary="Automated structural diagnostics identified key stakeholder register exclusions, strategic alignment gaps, and untracked architectural concerns.",
        findings=findings
    )

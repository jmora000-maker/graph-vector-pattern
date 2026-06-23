# GapDetector (Rules Engine)

from typing import List, Dict
from src.models import GapFinding
from src.knowledge import StructuredProjectContext, CorporateTaxonomyNormalizer
from src.rag import SimpleVectorStore


class GapDetector:
    def __init__(self, context: StructuredProjectContext, store: SimpleVectorStore,
                 normalizer: CorporateTaxonomyNormalizer):
        self.context = context
        self.store = store
        self.normalizer = normalizer

    def generate_strategic_heatmap(self) -> List[Dict]:
        heatmap_data = []
        for name, stakeholder in self.context.stakeholders.items():
            concern_count = len([c for c in self.context.concerns if c.stakeholder_name == name])

            risk_level = "STABLE"
            if stakeholder.influence == "High" and concern_count > 0:
                risk_level = "CRITICAL - Immediate Action Required"
            elif concern_count > 0:
                risk_level = "ELEVATED - Requires Attention"

            heatmap_data.append({
                "stakeholder": name,
                "influence": stakeholder.influence,
                "concern_count": concern_count,
                "risk_level": risk_level
            })
        return heatmap_data

    def execute_audit_checks(self) -> List[GapFinding]:
        findings = []
        findings.extend(self._check_missing_stakeholders())
        findings.extend(self._check_strategic_execution_gaps())
        findings.extend(self._check_recurrent_concern_mismatches())
        return findings

    def _check_missing_stakeholders(self) -> List[GapFinding]:
        findings = []
        mentioned_names = {m.stakeholder_name for m in self.context.meeting_mentions}
        registered_names = set(self.context.stakeholders.keys())

        for name in mentioned_names:
            if name not in registered_names and name:
                mentions = [m for m in self.context.meeting_mentions if m.stakeholder_name == name]
                primary_evidence = [f"[{m.source_artifact} Line {m.line_number}]: '{m.context_snippet}'" for m in
                                    mentions]

                findings.append(GapFinding(
                    finding_id=f"GAP-MISSING-{name.replace(' ', '-').upper()}",
                    gap_category="MISSING STAKEHOLDER",
                    stakeholder_name=name,
                    severity="High",
                    confidence="High" if len(mentions) > 1 else "Medium",
                    observed_gap=f"Stakeholder '{name}' is active in meeting notes but is not present in the Stakeholder Register.",
                    practical_impact="Lack of formal oversight for active project participants creates a governance blind spot.",
                    recommended_action=f"Add '{name}' to the Stakeholder Register and assign a communication owner.",
                    primary_deterministic_evidence=primary_evidence,
                    vector_evidence_queries=[f"{name} role in project"]
                ))
        return findings

    def _check_strategic_execution_gaps(self) -> List[GapFinding]:
        findings = []
        for name, stakeholder in self.context.stakeholders.items():
            norm_lookup = self.normalizer.normalize_name(name)
            actions = [a for a in self.context.engagement_actions if
                       self.normalizer.normalize_name(a.stakeholder_name) == norm_lookup]

            is_gap = False
            reasons = []

            if not actions:
                is_gap, reasons = True, ["has no actionable engagement entries in the strategy plan"]
            else:
                combined_strategy = " ".join([a.action_strategy.lower() for a in actions])
                if not any(a.has_owner for a in actions):
                    is_gap, reasons = True, ["lacks an explicit engagement owner"]

                # Cadence logic
                if stakeholder.desired_engagement == "Manage Closely" and not any(
                        x in combined_strategy for x in ["weekly", "bi-weekly"]):
                    is_gap, reasons = True, [
                        "requires high-frequency 'Manage Closely' engagement, but only low-frequency cadence is defined"]

            if is_gap:
                findings.append(GapFinding(
                    finding_id=f"GAP-EXEC-{name.replace(' ', '-').upper()}",
                    gap_category="STRATEGIC EXECUTION GAP",
                    stakeholder_name=name,
                    severity="High",
                    confidence="High",
                    observed_gap=f"Stakeholder '{name}' " + " and ".join(reasons) + ".",
                    practical_impact="Failure to maintain appropriate engagement rigor threatens program continuity.",
                    recommended_action=f"Update Engagement Plan for '{name}' to match their '{stakeholder.desired_engagement}' status.",
                    primary_deterministic_evidence=[f"[{a.source_artifact} Line {a.line_number}]: '{a.snippet}'" for a
                                                    in actions],
                    vector_evidence_queries=[f"{name} engagement strategy ownership frequency"]
                ))
        return findings

    def _check_recurrent_concern_mismatches(self) -> List[GapFinding]:
        findings = []
        for concern in self.context.concerns:
            matching_actions = [a for a in self.context.engagement_actions if
                                a.stakeholder_name == concern.stakeholder_name and
                                self.normalizer.classify_concern(a.action_strategy) == concern.normalized_category]

            if not matching_actions:
                findings.append(GapFinding(
                    finding_id=f"GAP-CONCERN-{concern.stakeholder_name.replace(' ', '-').upper()}-{concern.line_number}",
                    gap_category="RECURRENT CONCERN MISMATCH",
                    stakeholder_name=concern.stakeholder_name,
                    severity=concern.severity,
                    confidence="High",
                    observed_gap=f"The concern '{concern.normalized_category}' flagged by '{concern.stakeholder_name}' has no mapped action.",
                    practical_impact="Unaddressed recurrent concerns lead to reduced stakeholder trust.",
                    recommended_action=f"Add a specific mitigation action for '{concern.normalized_category}' to the Engagement Plan.",
                    primary_deterministic_evidence=[
                        f"[{concern.source_artifact} Line {concern.line_number}]: '{concern.snippet}'"],
                    vector_evidence_queries=[
                        f"{concern.stakeholder_name} {concern.normalized_category} mitigation steps"]
                ))
        return findings
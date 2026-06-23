# GapDetector (Rules Engine)

from typing import List
from src.models import GapFinding


class AuditDetector:
    """Orchestrates all automated audit checks against the project context."""

    def __init__(self, context, normalizer):
        self.context = context
        self.normalizer = normalizer

    def execute_audit_checks(self) -> List[GapFinding]:
        """Runs all defined audit rules and aggregates findings."""
        findings = []
        findings.extend(self._check_missing_stakeholders())
        findings.extend(self._check_strategic_execution_gaps())
        return findings

    def _check_missing_stakeholders(self) -> List[GapFinding]:
        """Detects stakeholders mentioned in notes but absent from the formal register."""
        registered_names = {s.name for s in self.context.stakeholders}
        mentioned_names = {m.stakeholder_name for m in self.context.meeting_mentions}
        missing_names = mentioned_names - registered_names

        findings = []
        for name in missing_names:
            findings.append(GapFinding(
                finding_id=f"GAP-MISSING-{name[:3].upper()}",
                gap_category="Missing Stakeholder",
                stakeholder_name=name,
                severity="Medium",
                confidence="High",
                observed_gap=f"Stakeholder '{name}' is active in meetings but not in the formal register.",
                practical_impact="Communication silos and potential loss of alignment.",
                recommended_action="Update Stakeholder Register.",
                primary_deterministic_evidence=[f"Mentioned in notes as {name}"],
                vector_evidence_queries=[f"Find registration record for {name}"]
            ))
        return findings

    def _check_strategic_execution_gaps(self) -> List[GapFinding]:
        """Checks for alignment gaps between engagement strategies and execution actions."""
        findings = []

        for stakeholder in self.context.stakeholders:
            name = stakeholder.name
            norm_lookup = self.normalizer.normalize(name)

            # Filter actions for this specific stakeholder
            actions = [a for a in self.context.engagement_actions if a.stakeholder_name == name]

            is_gap = False
            reasons = []

            # Rule 1: Existence check
            if not actions:
                is_gap, reasons = True, ["has no engagement entries in the strategy plan"]

            # Rule 2: Cadence check for "Manage Closely"
            else:
                combined_strategy = " ".join([a.action_strategy.lower() for a in actions])
                if stakeholder.desired_engagement == "Manage Closely" and not any(
                        x in combined_strategy for x in ["weekly", "bi-weekly"]):
                    is_gap, reasons = True, [
                        "requires high-frequency engagement but only low-frequency cadence is defined"]

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
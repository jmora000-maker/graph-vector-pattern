
from src.rag import SimpleVectorStore
from src.inputs import StructuredProjectContext
from src.taxonomy import CorporateTaxonomyNormalizer
from src.models import GapFinding
from typing import List, Dict, Set, Optional, Any
from src.graph_manager import GraphManager

# --- PIPELINE LAYER: DETERMINISTIC AUDIT RULES ENGINE ---
class GapDetector:
    def __init__(self, context: StructuredProjectContext, store: SimpleVectorStore, normalizer: CorporateTaxonomyNormalizer):
        self.context = context
        self.store = store
        self.normalizer = normalizer
        self.graph = GraphManager(graph_path="knowledge_graph/graph.json")
        try:
            self.graph.load()
        except FileNotFoundError:
            print(" -> Warning: graph.json not found. Rule execution may be degraded.")

    def generate_strategic_heatmap(self) -> List[Dict]:
        print(" -> Generating Strategic Heatmap.")
        heatmap_data = []
        for name, stakeholder in self.context.stakeholders.items():
            concern_count = len([c for c in self.context.concerns if c.stakeholder_name == name])

            # Risk Level: High Influence + Multiple Concerns = CRITICAL
            if stakeholder.influence == "High" and concern_count > 0:
                risk_level = "CRITICAL - Immediate Action Required"
            elif concern_count > 0:
                risk_level = "ELEVATED - Requires Attention"
            else:
                risk_level = "STABLE"

            heatmap_data.append({
                "stakeholder": name,
                "influence": stakeholder.influence,
                "concern_count": concern_count,
                "risk_level": risk_level
            })
        return heatmap_data


    def _create_missing_stakeholder_finding(self, name: str, mentions: List) -> GapFinding:
        f_id = f"GAP-MISSING-{name.replace(' ', '-').upper()}"
        primary_evidence = [f"[{m.source_artifact} Line {m.line_number}]: '{m.context_snippet}'" for m in mentions]
        return GapFinding(
            finding_id=f_id,
            gap_category="MISSING STAKEHOLDER",
            stakeholder_name=name,
            severity="High",
            confidence="High" if len(mentions) > 1 else "Medium",
            observed_gap=f"Stakeholder '{name}' is active in meeting notes but is not present in the Stakeholder Register.",
            practical_impact="Lack of formal oversight for active project participants creates a governance blind spot.",
            recommended_action=f"Add '{name}' to the Stakeholder Register and assign a communication owner.",
            primary_deterministic_evidence=primary_evidence,
            vector_evidence_queries=[f"{name} role in project"]
        )

    def execute_audit_checks(self) -> List[GapFinding]:
        findings: List[GapFinding] = []

        # --- RULE 1: MISSING STAKEHOLDER ---
        print(" -> Executing Rule 1: Missing Stakeholder Detection.")
        mentioned_names = {m.stakeholder_name for m in self.context.meeting_mentions}
        registered_names = set(self.context.stakeholders.keys())

        for name in mentioned_names:
            if name not in registered_names and name:
                mentions = [m for m in self.context.meeting_mentions if m.stakeholder_name == name]
                findings.append(self._create_missing_stakeholder_finding(name, mentions))


        # --- RULE 2: STRATEGIC EXECUTION GAP ---
        print(" -> Executing Rule 2: Strategic Execution Gap Detection.")
        for name, stakeholder in self.context.stakeholders.items():
            # Normalize the lookup name to ensure it matches exactly how the Action was stored
            norm_lookup = self.normalizer.normalize_name(name)

            # Use graph to find actions
            stk_id = f"STK-{norm_lookup.replace(' ', '-').upper()}"
            actions = self.graph.get_related(stk_id, edge_type="owns")

            is_gap = False
            reasons = []
            
            # 1. Actionability Gap
            if not actions:
                is_gap = True
                reasons.append("has no actionable engagement entries in the strategy plan")
            else:
                combined_strategy = " ".join([a['strategy'].lower() for a in actions])

                # 2. Ownership Gap
                if not any(a['has_owner'] for a in actions):
                    is_gap = True
                    reasons.append("lacks an explicit engagement owner")

                # 3. Cadence Gap
                strategy_lower = combined_strategy.lower()
                if stakeholder.desired_engagement == "Manage Closely":
                    if not any(x in strategy_lower for x in ["weekly", "bi-weekly"]):
                        is_gap = True
                        reasons.append(
                            "requires high-frequency 'Manage Closely' engagement, but only low-frequency cadence is defined")

                elif stakeholder.desired_engagement == "Keep Satisfied":
                    if not any(x in strategy_lower for x in ["weekly", "bi-weekly", "monthly"]):
                        is_gap = True
                        reasons.append("requires 'Keep Satisfied' engagement, but cadence is insufficient")

            if is_gap:
                findings.append(self._create_strategic_execution_finding(name, reasons, stakeholder.desired_engagement))

        # --- RULE 3: RECURRENT CONCERN MISMATCH ---
        print(" -> Executing Rule 3: Recurrent Concern Mismatch Detection.")
        for concern in self.context.concerns:
            name = concern.stakeholder_name
            
            # Use graph to find actions
            stk_id = f"STK-{name.replace(' ', '-').upper()}"
            related_actions = self.graph.get_related(stk_id, edge_type="owns")
            
            # Find actions for this stakeholder and check if ANY action covers the concern category
            matching_actions = [
                a for a in related_actions
                if self.normalizer.classify_concern(a['strategy']) == concern.normalized_category
            ]

            if not matching_actions:
                findings.append(self._create_recurrent_concern_finding(name, concern))

        return findings

    def _create_strategic_execution_finding(self, name: str, reasons: List[str], desired_engagement: str) -> GapFinding:
        f_id = f"GAP-EXEC-{name.replace(' ', '-').upper()}"
        return GapFinding(
            finding_id=f_id,
            gap_category="STRATEGIC EXECUTION GAP",
            stakeholder_name=name,
            severity="High",
            confidence="High",
            observed_gap=f"Stakeholder '{name}' " + " and ".join(reasons) + ".",
            practical_impact="Failure to maintain the appropriate engagement rigor for high-influence stakeholders directly threatens program continuity and strategic consensus.",
            recommended_action=f"Update the Engagement Plan to assign a clear owner and increase frequency for '{name}' to match their '{desired_engagement}' status.",
            primary_deterministic_evidence=[],
            vector_evidence_queries=[f"{name} engagement strategy ownership frequency"]
        )

    def _create_recurrent_concern_finding(self, name: str, concern: Any) -> GapFinding:
        f_id = f"GAP-CONCERN-{name.replace(' ', '-').upper()}-{concern.line_number}"
        return GapFinding(
            finding_id=f_id,
            gap_category="RECURRENT CONCERN MISMATCH",
            stakeholder_name=name,
            severity=concern.severity,
            confidence="High",
            observed_gap=f"The concern '{concern.normalized_category}' flagged by '{name}' has no mapped action in the engagement plan.",
            practical_impact="Unaddressed recurrent concerns lead to project friction and reduced stakeholder trust.",
            recommended_action=f"Add a specific mitigation action for '{concern.normalized_category}' to the Engagement Plan.",
            primary_deterministic_evidence=[
                f"[{concern.source_artifact} Line {concern.line_number}]: '{concern.snippet}'"],
            vector_evidence_queries=[f"{name} {concern.normalized_category} mitigation steps"]
        )

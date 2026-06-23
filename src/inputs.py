import pandas as pd
from typing import List, Dict, Set
import re
from src.config import stakeholder_register_path, stakeholder_plan_path, meeting_notes_path
from src.taxonomy import CorporateTaxonomyNormalizer
from src.config import KNOWN_STAKEHOLDERS
from src.models import Stakeholder, Concern, EngagementAction, MeetingMention
from src.rag import chunk_text
from src.graph_manager import GraphManager


# --- PIPELINE LAYER: ARTIFACT-SPECIFIC INGESTION & STRUCTURAL FACTS ENGINE ---
class StructuredProjectContext:
    """Dynamic Document Content Ingestion executing explicit parsers with dense metadata population."""

    def __init__(self, normalizer: CorporateTaxonomyNormalizer):
        self.normalizer = normalizer
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.concerns: List[Concern] = []
        self.engagement_actions: List[EngagementAction] = []
        self.meeting_mentions: List[MeetingMention] = []
        self.discovered_names: Set[str] = set()
        self.raw_chunks: List[Dict] = []

    def ingest_data(self):


        for known_name in KNOWN_STAKEHOLDERS:
            self.discovered_names.add(known_name)

        # 1. Register Discovery
        if stakeholder_register_path.exists():
            print(" -> Pass 1: Discovering stakeholders from register.")
            df = pd.read_csv(stakeholder_register_path)
            for _, row in df.iterrows():
                n = str(row.get("name", "")).strip()
                if n: self.discovered_names.add(self.normalizer.normalize_name(n))

        # 2. Plan Discovery (Update for Markdown Headers)
        if stakeholder_plan_path.exists():
            print(" -> Pass 1: Discovering stakeholders from plan.")
            content = stakeholder_plan_path.read_text(encoding="utf-8")
            # This regex looks for names between "###" and "—"
            matches = re.findall(r"###\s+(.*?)\s+—", content)
            for raw_name in matches:
                norm = self.normalizer.normalize_name(raw_name)
                if norm: self.discovered_names.add(norm)

        # 3. Meeting Discovery (STRICT: ONLY the Attendees line)
        if meeting_notes_path.exists():
            print(" -> Pass 1: Discovering stakeholders from meeting notes.")
            for line in meeting_notes_path.read_text(encoding="utf-8").split("\n"):
                if line.lower().startswith("attendees:"):
                    # Extract only the content after "attendees:"
                    raw_attendees = line.split(":", 1)[1]
                    for name_part in raw_attendees.split(","):
                        n = name_part.strip()
                        if n:
                            norm = self.normalizer.normalize_name(n)
                            # Only add if it's not a common project term
                            # You could add a blacklist here if needed
                            if norm not in ["Actions", "Steering Committee", "Security Review"]:
                                self.discovered_names.add(norm)

        # 1. PARSER SPECIFIC: Stakeholder Register
        if stakeholder_register_path.exists():
            print(" -> Pass 2: Ingesting Stakeholder Register.")
            df = pd.read_csv(stakeholder_register_path)
            for _, row in df.iterrows():
                raw_name = str(row.get("Stakeholder Name", "")).strip()
                if not raw_name: continue

                norm_name = self.normalizer.normalize_name(raw_name)

                # FIX: Add the missing required fields
                self.stakeholders[norm_name] = Stakeholder(
                    stakeholder_id=f"STK-{norm_name.replace(' ', '-').upper()}",  # Generated ID
                    name=norm_name,
                    role=str(row.get("Role", "Unknown")),
                    influence=str(row.get("Influence", "Medium")),
                    interest=str(row.get("Interest", "Medium")),
                    desired_engagement=str(row.get("Preferred Communication", "Keep Informed")),
                    source_artifact="Stakeholder_Register.csv"  # Required field
                )

                self.raw_chunks.append({
                    "text": f"Register entry: {raw_name}, Role: {row.get('Role')}, Dept: {row.get('Department')}",
                    "metadata": {"source": "Stakeholder_Register.csv", "type": "Register"}
                })

        # 2. PARSER SPECIFIC: Engagement Plan
        if stakeholder_plan_path.exists():
            print(" -> Pass 2: Ingesting Engagement Plan.")
            lines = stakeholder_plan_path.read_text(encoding="utf-8").split("\n")
            current_stakeholder = None

            for idx, line in enumerate(lines):
                # Look for the header format "### Name — Role"
                header_match = re.search(r"###\s+(.*?)\s+—", line)
                if header_match:
                    raw_name = header_match.group(1).strip()
                    current_stakeholder = self.normalizer.normalize_name(raw_name)
                    continue  # Move to next line

                # If we are under a stakeholder, look for actions
                if current_stakeholder and line.strip().startswith("-"):
                    strategy_text = line.replace("-", "").strip()

                    # Only add if it's an actual action, not a label
                    if strategy_text.lower() not in ["engagement approach:", "actions:", "desired outcome:"]:
                        has_owner = any(x in strategy_text.lower() for x in ["owner:", "lead", "pm"])
                        has_cadence = any(
                            x in strategy_text.lower() for x in ["weekly", "bi-weekly", "monthly", "quarterly"])

                        self.engagement_actions.append(EngagementAction(
                            action_strategy=strategy_text,
                            stakeholder_name=current_stakeholder,
                            has_owner=has_owner,
                            has_cadence=has_cadence,
                            source_artifact="Stakeholder_Engagement_Plan.md",
                            line_number=idx + 1,
                            snippet=line.strip()
                        ))

        # 3. PARSER SPECIFIC: Meeting Notes (Context-Rich Sweep)
        if meeting_notes_path.exists():
            print(" -> Pass 2: Ingesting Meeting Notes.")
            notes_lines = meeting_notes_path.read_text(encoding="utf-8").split("\n")
            is_attendee_line = False

            for idx, line in enumerate(notes_lines):
                # 1. Skip structural markdown headers
                if line.strip().startswith("#"):
                    continue

                # 2. Reset attendee status on empty lines
                if not line.strip():
                    is_attendee_line = False
                    continue

                lowered_line = line.lower()
                if "attendees:" in lowered_line:
                    is_attendee_line = True

                for target_name in self.discovered_names:
                    # Guard: Skip empty or invalid names
                    if not target_name or target_name in self.normalizer.blocklist:
                        continue

                    # Use Regex Word Boundaries (\b) for precise matching
                    pattern = rf"\b{re.escape(target_name)}\b"

                    if re.search(pattern, line, re.IGNORECASE):
                        # Determine attendee status (only if on the "attendees:" line)
                        is_att = is_attendee_line and (target_name.lower() in lowered_line.split("attendees:")[-1])

                        # --- LOGIC TO DEFINE MENTION TYPE ---
                        if is_att:
                            m_type = "attendee"
                        elif any(k in lowered_line for k in
                                 ["concern", "anxiety", "risk", "issue", "flagged", "stalled", "vulnerability"]):
                            m_type = "concern"
                        else:
                            m_type = "discussion"
                        # ------------------------------------

                        self.meeting_mentions.append(MeetingMention(
                            stakeholder_name=target_name,
                            context_snippet=line.strip(),
                            source_artifact="Meeting_Notes.md",
                            line_number=idx + 1,
                            is_explicit_attendee=is_att,
                            mention_type=m_type
                        ))

                        # Keep concern logic, but only if it's a valid stakeholder name
                        if m_type == "concern":
                            category = self.normalizer.classify_concern(line)
                            severity = "High" if "architecture" in lowered_line or "blockage" in lowered_line else "Medium"
                            self.concerns.append(Concern(
                                description=line.replace("-", "").strip(),
                                stakeholder_name=target_name,
                                normalized_category=category,
                                severity=severity,
                                source_artifact="Meeting_Notes.md",
                                line_number=idx + 1,
                                snippet=line.strip()
                            ))

            # Create chunks for vector search
            for chunk in chunk_text("\n".join(notes_lines)):
                self.raw_chunks.append({
                    "text": chunk,
                    "metadata": {"source": "Meeting_Notes.md", "type": "Notes", "section": "Discussion Logs"}
                })
            self.build_graph()

    def build_graph(self):
        print(" -> Building Knowledge Graph.")
        graph = GraphManager(graph_path="knowledge_graph/graph.json")
        for name, stk in self.stakeholders.items():
            graph.add_node(stk.stakeholder_id, "stakeholder", name=stk.name, influence=stk.influence)
        
        for i, concern in enumerate(self.concerns):
            c_id = f"conc-{i}"
            graph.add_node(c_id, "concern", category=concern.normalized_category, description=concern.description)
            # Find stakeholder ID
            stk_id = f"STK-{concern.stakeholder_name.replace(' ', '-').upper()}"
            graph.add_edge(stk_id, c_id, "raises")
            
        for i, action in enumerate(self.engagement_actions):
            a_id = f"act-{i}"
            graph.add_node(a_id, "action", 
                           strategy=action.action_strategy, 
                           has_owner=action.has_owner, 
                           has_cadence=action.has_cadence)
            stk_id = f"STK-{action.stakeholder_name.replace(' ', '-').upper()}"
            graph.add_edge(stk_id, a_id, "owns")
            
        graph.save()
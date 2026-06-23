# CorporateTaxonomyNormalizer & StructuredProjectContext

import re
import pandas as pd
from typing import Dict, List, Set
from src.models import Stakeholder, Concern, EngagementAction, MeetingMention
from src.inputs import STAKEHOLDER_REGISTER_PATH, STAKEHOLDER_PLAN_PATH, MEETING_NOTES_PATH


class CorporateTaxonomyNormalizer:
    def __init__(self):
        self.blocklist = {"Actions", "Steering Committee", "Security Review", "Discussion"}
        self.identity_map = {
            "maria chen": "Maria Chen",
            "david": "David Okafor",
            "david okafor": "David Okafor",
            "priya": "Priya Nair",
            "priya nair": "Priya Nair",
            "helen brooks": "Helen Brooks",
            "jonas": "Jonas Weber",
            "jonas weber": "Jonas Weber",
            "fatima": "Fatima Hassan",
            "fatima hassan": "Fatima Hassan",
            "fatima al-sayed": "Fatima Hassan"
        }
        self.concern_taxonomy = {
            "audit logging": ["audit logging", "audit log", "logging controls", "access control",
                              "security architecture"],
            "training readiness": ["training readiness", "deployment schedules", "anxieties", "frontline deployment",
                                   "enablement"],
            "support infrastructure": ["support scripts", "vendor handoff", "infrastructure targets",
                                       "enablement blockages", "scripts"]
        }

    def normalize_name(self, name: str) -> str:
        if name.title() in self.blocklist: return ""
        cleaned = str(name).strip().lower().replace("-", " ")
        cleaned = re.sub(r'[:\s*•\-\d)]', ' ', cleaned)
        cleaned = " ".join(cleaned.split())

        # Identity mapping logic
        if cleaned in self.identity_map: return self.identity_map[cleaned]
        for alias, canonical in self.identity_map.items():
            if alias in cleaned or cleaned in alias: return canonical
        return name.title()

    def classify_concern(self, text: str) -> str:
        lowered = text.lower()
        for category, triggers in self.concern_taxonomy.items():
            if any(trigger in lowered for trigger in triggers):
                return category
        return "general operational friction"


class StructuredProjectContext:
    def __init__(self, normalizer: CorporateTaxonomyNormalizer):
        self.normalizer = normalizer
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.concerns: List[Concern] = []
        self.engagement_actions: List[EngagementAction] = []
        self.meeting_mentions: List[MeetingMention] = []
        self.raw_chunks: List[Dict] = []

    def ingest_data(self):
        """Orchestrates parsing across all defined data sources."""
        self._parse_register()
        self._parse_plan()
        self._parse_meeting_notes()

    def _parse_register(self):
        if not STAKEHOLDER_REGISTER_PATH.exists(): return
        df = pd.read_csv(STAKEHOLDER_REGISTER_PATH)
        for _, row in df.iterrows():
            raw_name = str(row.get("name", "")).strip()
            norm = self.normalizer.normalize_name(raw_name)
            if norm:
                self.stakeholders[norm] = Stakeholder(
                    stakeholder_id=f"STK-{norm.replace(' ', '-').upper()}",
                    name=norm,
                    role=row.get("role", "Unknown"),
                    influence=row.get("influence", "Medium"),
                    interest=row.get("interest", "Medium"),
                    desired_engagement=row.get("desired_engagement", "Keep Informed"),
                    source_artifact="Stakeholder_Register.csv"
                )

    def _parse_plan(self):
        """Parses stakeholder engagement plan from Markdown."""
        if not STAKEHOLDER_PLAN_PATH.exists(): return

        lines = STAKEHOLDER_PLAN_PATH.read_text(encoding="utf-8").split("\n")
        current_stakeholder = None

        for idx, line in enumerate(lines):
            # Look for header format: ### Name — Role
            header_match = re.search(r"###\s+(.*?)\s+—", line)
            if header_match:
                current_stakeholder = self.normalizer.normalize_name(header_match.group(1).strip())
                continue

            # Capture bulleted actions
            if current_stakeholder and line.strip().startswith("-"):
                strategy_text = line.replace("-", "").strip()
                if strategy_text.lower() not in ["engagement approach:", "actions:", "desired outcome:"]:
                    self.engagement_actions.append(EngagementAction(
                        action_strategy=strategy_text,
                        stakeholder_name=current_stakeholder,
                        has_owner=any(x in strategy_text.lower() for x in ["owner:", "lead", "pm"]),
                        has_cadence=any(x in strategy_text.lower() for x in ["weekly", "bi-weekly", "monthly"]),
                        source_artifact="Stakeholder_Engagement_Plan.md",
                        line_number=idx + 1,
                        snippet=line.strip()
                    ))

    def _parse_meeting_notes(self):
        """Parses meeting notes and extracts concerns and mentions."""
        if not MEETING_NOTES_PATH.exists(): return

        notes_lines = MEETING_NOTES_PATH.read_text(encoding="utf-8").split("\n")
        is_attendee_line = False

        for idx, line in enumerate(notes_lines):
            if line.strip().startswith("#"): continue
            if not line.strip():
                is_attendee_line = False
                continue

            lowered_line = line.lower()
            if "attendees:" in lowered_line: is_attendee_line = True

            for target_name in self.stakeholders.keys():  # Only track known stakeholders
                pattern = rf"\b{re.escape(target_name)}\b"
                if re.search(pattern, line, re.IGNORECASE):
                    is_att = is_attendee_line and (target_name.lower() in lowered_line.split("attendees:")[-1])

                    # Logic to classify mention type
                    m_type = "attendee" if is_att else ("concern" if any(k in lowered_line for k in
                                                                         ["concern", "anxiety", "risk", "issue",
                                                                          "flagged"]) else "discussion")

                    self.meeting_mentions.append(MeetingMention(
                        stakeholder_name=target_name,
                        context_snippet=line.strip(),
                        source_artifact="Meeting_Notes.md",
                        line_number=idx + 1,
                        is_explicit_attendee=is_att,
                        mention_type=m_type
                    ))

                    if m_type == "concern":
                        self.concerns.append(Concern(
                            description=line.replace("-", "").strip(),
                            stakeholder_name=target_name,
                            normalized_category=self.normalizer.classify_concern(line),
                            severity="High" if "architecture" in lowered_line or "blockage" in lowered_line else "Medium",
                            source_artifact="Meeting_Notes.md",
                            line_number=idx + 1,
                            snippet=line.strip()
                        ))
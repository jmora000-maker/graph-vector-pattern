# CorporateTaxonomyNormalizer & StructuredProjectContext

from typing import List
from pydantic import BaseModel, Field, PrivateAttr
from src.models import Stakeholder, Concern, MeetingMention, EngagementAction
from src.inputs import get_raw_register_data, get_raw_plan_text, get_raw_meeting_notes


class CorporateTaxonomyNormalizer:
    """Standardizes terminology across different source artifacts."""

    def __init__(self):
        self.mapping = {
            "tech lead": "Technical Lead",
            "ops mgr": "Operations Manager",
            "comp dir": "Compliance Director"
        }

    def normalize(self, value: str) -> str:
        return self.mapping.get(value.lower(), value)


class StructuredProjectContext(BaseModel):
    """The central source of truth for project-wide data."""
    # Pydantic models initialize these lists automatically
    stakeholders: List[Stakeholder] = Field(default_factory=list)
    engagement_actions: List[EngagementAction] = Field(default_factory=list)
    meeting_mentions: List[MeetingMention] = Field(default_factory=list)
    raw_chunks: List[str] = Field(default_factory=list)

    # PrivateAttr keeps this out of Pydantic's schema validation
    _normalizer: CorporateTaxonomyNormalizer = PrivateAttr(default_factory=CorporateTaxonomyNormalizer)

    def ingest_data(self):
        """Orchestrates data transformation into structured models."""
        self._process_register(get_raw_register_data())
        self._process_plan(get_raw_plan_text())
        self._process_notes(get_raw_meeting_notes())

    def _process_register(self, df):
        """Converts CSV register data into Stakeholder objects."""
        if df.empty:
            return

        for _, row in df.iterrows():
            self.stakeholders.append(Stakeholder(
                stakeholder_id="N/A",
                name=row["stakeholder_name"],
                role=self._normalizer.normalize(row["role"]),
                influence=row["influence"],
                interest=row["interest"],
                desired_engagement=row["current_support"],
                source_artifact="Stakeholder_Register.csv"
            ))

    def _process_plan(self, text: str):
        """Adds plan content to raw_chunks for vector indexing."""
        if text:
            self.raw_chunks.append(text)

    def _process_notes(self, lines: List[str]):
        """Parses raw text meeting notes into structured mentions."""
        for i, line in enumerate(lines):
            self.raw_chunks.append(line)
            # Basic logic to populate mentions
            if any(name in line for name in ["Liam Patel", "Fatima Al-Sayed"]):
                self.meeting_mentions.append(MeetingMention(
                    stakeholder_name="Extracted Name",
                    context_snippet=line,
                    source_artifact="Meeting_Notes.md",
                    line_number=i,
                    is_explicit_attendee=True,
                    mention_type="Discussion"
                ))
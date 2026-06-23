from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# --- INTERNAL FACT DOMAIN SCHEMAS ---
class Stakeholder(BaseModel):
    stakeholder_id: str
    name: str
    role: str
    influence: str
    interest: str
    desired_engagement: str
    source_artifact: str
    source_row: Optional[int] = None


class Concern(BaseModel):
    description: str
    stakeholder_name: str
    normalized_category: str
    severity: str
    source_artifact: str
    line_number: int
    snippet: str
    concern_keywords: List[str] = []


class EngagementAction(BaseModel):
    action_strategy: str
    stakeholder_name: str
    owner_text: Optional[str] = None
    cadence_text: Optional[str] = None
    has_owner: bool
    has_cadence: bool
    source_artifact: str
    line_number: int
    snippet: str


class MeetingMention(BaseModel):
    stakeholder_name: str
    context_snippet: str
    source_artifact: str
    line_number: int
    is_explicit_attendee: bool
    mention_type: str  # attendee, discussion, concern


class GapFinding(BaseModel):
    finding_id: str
    gap_category: str
    stakeholder_name: str
    severity: str
    confidence: str
    observed_gap: str
    practical_impact: str
    recommended_action: str
    primary_deterministic_evidence: List[str]
    vector_evidence_queries: List[str]


# --- OUTWARD REVENUE-GRADE REPORT SCHEMAS ---
class EvidenceItem(BaseModel):
    source: str
    snippet: str
    line_number: Optional[int] = None
    artifact_type: Optional[str] = None


class StakeholderGapReport(BaseModel):
    gap_category: str = Field(
        description="The gap category in ALL CAPS: MISSING STAKEHOLDER, STRATEGIC EXECUTION GAP, or RECURRENT CONCERN MISMATCH.")
    stakeholder_name: str
    severity: str
    confidence: str
    observed_gap: str
    practical_impact: str
    recommended_action: str
    finding_id: str
    evidence: List[EvidenceItem]


class ExecutiveStakeholderGapReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    executive_summary: str
    findings: List[StakeholderGapReport]
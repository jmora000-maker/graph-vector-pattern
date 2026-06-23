# Pydantic schemas (Schemas Layer)

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class Stakeholder(BaseModel):
    stakeholder_id: str
    name: str
    role: str
    influence: str
    interest: str
    desired_engagement: str
    source_artifact: str

class Concern(BaseModel):
    description: str
    stakeholder_name: str
    normalized_category: str
    severity: str
    source_artifact: str
    line_number: int
    snippet: str

class EngagementAction(BaseModel):
    action_strategy: str
    stakeholder_name: str
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
    mention_type: str

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

class EvidenceItem(BaseModel):
    source: str
    snippet: str

class StakeholderGapReport(BaseModel):
    gap_category: str
    stakeholder_name: str
    severity: str
    confidence: str
    observed_gap: str
    practical_impact: str
    recommended_action: str
    evidence: List[EvidenceItem]

class ExecutiveStakeholderGapReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    executive_summary: str
    findings: List[StakeholderGapReport]
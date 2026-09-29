import json
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict

# API Envelope Response
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, str]] = None

# Incident Schemas
class IncidentCreate(BaseModel):
    title: str
    service_name: str
    environment: str = "production"
    severity: str # CRITICAL, HIGH, MEDIUM, LOW
    alert: str
    logs: str
    created_by: str = "oncall-engineer"

class WebhookAlertPayload(BaseModel):
    title: Optional[str] = None
    alert: Optional[str] = None
    service_name: str
    severity: str = "HIGH"
    environment: str = "production"
    logs: Optional[str] = ""
    summary: Optional[str] = None
    annotations: Optional[Dict[str, Any]] = None

class IncidentResolve(BaseModel):
    root_cause: str
    root_cause_category: str
    resolution_steps: str
    outcome: str = "SUCCESS" # SUCCESS, PARTIAL_SUCCESS, FAILED
    resolution_time_minutes: int
    runbook_name: Optional[str] = None

class FeedbackCreate(BaseModel):
    recommendation: str
    feedback_type: str # WORKED, PARTIALLY_WORKED, DID_NOT_WORK
    feedback_text: Optional[str] = None
    actual_fix: Optional[str] = None

class RecallQuery(BaseModel):
    service_name: str
    alert: str
    logs: str
    severity: Optional[str] = "HIGH"

# Analysis Briefing Response
class AnalysisBriefing(BaseModel):
    likely_root_cause: str
    confidence_score: float
    confidence_level: str # HIGH, MEDIUM, LOW, INSUFFICIENT
    confidence_reasoning: str
    recommended_actions: List[str]
    historical_evidence_used: List[str] # Memory / Incident IDs verified
    shared_patterns: List[str]
    anti_pattern_warnings: List[str]
    runbook_recommendation: Optional[str] = None
    risk_note: Optional[str] = None
    recalled_incidents: List[Dict[str, Any]]
    ranking_breakdown: List[Dict[str, Any]]
    evidence_summary: Dict[str, Any]

class IncidentResponse(BaseModel):
    id: str
    title: str
    service_name: str
    environment: str
    severity: str
    status: str
    alert: str
    logs: str
    root_cause: Optional[str] = None
    root_cause_category: Optional[str] = None
    resolution_steps: Optional[str] = None
    outcome: Optional[str] = None
    resolution_time_minutes: Optional[int] = None
    runbook_name: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    memory_id: Optional[str] = None
    memory_assisted: bool = False
    created_by: str = "oncall-engineer"
    is_eval_held_out: bool = False

    @field_validator('tags', mode='before')
    def parse_tags(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    model_config = ConfigDict(from_attributes=True)

# Feedback Response
class FeedbackResponse(BaseModel):
    id: str
    incident_id: str
    recommendation: str
    feedback_type: str
    feedback_text: Optional[str] = None
    actual_fix: Optional[str] = None
    memory_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

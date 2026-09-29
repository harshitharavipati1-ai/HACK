from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False, index=True)
    service_name = Column(String, nullable=False, index=True)
    environment = Column(String, nullable=False, default="production")
    severity = Column(String, nullable=False, index=True) # CRITICAL, HIGH, MEDIUM, LOW
    status = Column(String, nullable=False, default="OPEN", index=True) # OPEN, INVESTIGATING, RESOLVED, MITIGATED
    alert = Column(Text, nullable=False)
    logs = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    root_cause_category = Column(String, nullable=True, index=True)
    resolution_steps = Column(Text, nullable=True)
    outcome = Column(String, nullable=True) # SUCCESS, PARTIAL_SUCCESS, FAILED
    resolution_time_minutes = Column(Integer, nullable=True)
    runbook_name = Column(String, nullable=True)
    tags = Column(Text, nullable=True) # JSON list string
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    memory_id = Column(String, nullable=True)
    memory_assisted = Column(Boolean, default=False)
    created_by = Column(String, default="oncall-engineer")
    is_eval_held_out = Column(Boolean, default=False)

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String, primary_key=True, default=generate_uuid)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False, index=True)
    recommendation = Column(Text, nullable=False)
    feedback_type = Column(String, nullable=False) # WORKED, PARTIALLY_WORKED, DID_NOT_WORK
    feedback_text = Column(Text, nullable=True)
    actual_fix = Column(Text, nullable=True)
    memory_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RecallTrace(Base):
    __tablename__ = "recall_traces"

    id = Column(String, primary_key=True, default=generate_uuid)
    incident_id = Column(String, nullable=True, index=True)
    query_text = Column(Text, nullable=False)
    provider = Column(String, nullable=False) # Hindsight or Local Fallback
    results_json = Column(Text, nullable=False) # JSON array of recalled items
    latency_ms = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ServiceDependency(Base):
    __tablename__ = "service_dependencies"

    id = Column(String, primary_key=True, default=generate_uuid)
    service = Column(String, nullable=False, index=True)
    depends_on = Column(String, nullable=False)

class LocalMemoryItem(Base):
    __tablename__ = "local_memory_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    bank_id = Column(String, nullable=False, index=True)
    memory_type = Column(String, nullable=False, index=True) # incident_resolution, feedback_outcome, failed_fix_antipattern, pattern_insight
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=False)
    tags_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

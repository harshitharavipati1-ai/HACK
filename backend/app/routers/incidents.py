import json
import time
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Incident, Feedback, RecallTrace, ServiceDependency
from app.schemas import (
    ApiResponse, IncidentCreate, IncidentResponse, IncidentResolve,
    FeedbackCreate, FeedbackResponse, AnalysisBriefing
)
from app.services.memory_factory import get_memory_service
from app.services.redaction_service import redact_secrets
from app.services.ranking_service import rank_recalled_evidence
from app.services.confidence_service import compute_evidence_confidence
from app.services.llm_service import analyze_incident_with_llm
from app.config import settings

router = APIRouter(prefix="/incidents", tags=["Incidents"])

@router.get("", response_model=ApiResponse)
def list_incidents(
    service: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Incident)
    if service and service != "ALL":
        query = query.filter(Incident.service_name == service)
    if severity and severity != "ALL":
        query = query.filter(Incident.severity == severity)
    if status and status != "ALL":
        query = query.filter(Incident.status == status)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Incident.title.like(s)) | (Incident.service_name.like(s)) | (Incident.alert.like(s))
        )
        
    incidents = query.order_by(desc(Incident.created_at)).all()
    results = []
    for inc in incidents:
        t_list = json.loads(inc.tags) if inc.tags else []
        item = IncidentResponse.model_validate(inc)
        item.tags = t_list
        results.append(item.model_dump())
        
    return ApiResponse(success=True, data=results)

@router.post("", response_model=ApiResponse)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    safe_alert = redact_secrets(payload.alert)
    safe_logs = redact_secrets(payload.logs)
    
    # Generate ID
    count = db.query(Incident).count() + 1
    inc_id = f"INC-2026-{count:03d}"
    
    inc = Incident(
        id=inc_id,
        title=payload.title,
        service_name=payload.service_name,
        environment=payload.environment,
        severity=payload.severity,
        status="OPEN",
        alert=safe_alert,
        logs=safe_logs,
        created_by=payload.created_by,
        tags=json.dumps([payload.service_name, payload.severity.lower()])
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    
    res = IncidentResponse.model_validate(inc)
    res.tags = [payload.service_name, payload.severity.lower()]
    return ApiResponse(success=True, data=res.model_dump())

@router.get("/{incident_id}", response_model=ApiResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    res = IncidentResponse.model_validate(inc)
    res.tags = json.loads(inc.tags) if inc.tags else []
    
    # Also fetch feedback records
    feedbacks = db.query(Feedback).filter(Feedback.incident_id == incident_id).all()
    fb_list = [FeedbackResponse.model_validate(fb).model_dump() for fb in feedbacks]
    
    data = res.model_dump()
    data["feedbacks"] = fb_list
    return ApiResponse(success=True, data=data)

@router.post("/{incident_id}/analyze", response_model=ApiResponse)
def analyze_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    start_time = time.time()
    memory_svc = get_memory_service(db)
    
    # 1. Expand query to include service dependencies if present
    deps = db.query(ServiceDependency).filter(ServiceDependency.service == inc.service_name).all()
    dep_names = [d.depends_on for d in deps]
    
    search_query = f"{inc.service_name} {' '.join(dep_names)} {inc.alert} {inc.logs[:300]}"
    
    # 2. Recall similar incidents from memory bank
    try:
        raw_recalled = memory_svc.recall_memories(
            bank_id=settings.HINDSIGHT_BANK_ID,
            query=search_query,
            service_name=inc.service_name,
            top_k=10
        )
    except Exception as e:
        # Fallback if memory service raises unexpected exception
        raw_recalled = []
        
    # 3. Save RecallTrace for Memory Inspector
    latency = round((time.time() - start_time) * 1000, 2)
    trace = RecallTrace(
        incident_id=inc.id,
        query_text=search_query,
        provider=memory_svc.provider_name,
        results_json=json.dumps(raw_recalled),
        latency_ms=latency
    )
    db.add(trace)
    db.commit()
    
    # 4. Evidence Ranking
    ranked_evidence = rank_recalled_evidence(
        recalled_items=raw_recalled,
        current_service=inc.service_name,
        current_logs=inc.logs,
        current_alert=inc.alert
    )
    
    # 5. Evidence-based Confidence Calculation
    conf_score, conf_level, conf_reasoning = compute_evidence_confidence(ranked_evidence)
    
    # 6. LLM Analysis Briefing
    llm_output = analyze_incident_with_llm(
        title=inc.title,
        service_name=inc.service_name,
        alert=inc.alert,
        logs=inc.logs,
        severity=inc.severity,
        ranked_evidence=ranked_evidence
    )
    
    # Combine into comprehensive briefing schema
    briefing = AnalysisBriefing(
        likely_root_cause=llm_output.get("likely_root_cause", "Service operational error"),
        confidence_score=conf_score,
        confidence_level=conf_level,
        confidence_reasoning=conf_reasoning,
        recommended_actions=llm_output.get("recommended_actions", []),
        historical_evidence_used=llm_output.get("historical_evidence_used", []),
        shared_patterns=llm_output.get("shared_patterns", []),
        anti_pattern_warnings=llm_output.get("anti_pattern_warnings", []),
        runbook_recommendation=llm_output.get("runbook_recommendation"),
        risk_note=llm_output.get("risk_note", "Recommendations only — engineer approves and executes."),
        recalled_incidents=ranked_evidence,
        ranking_breakdown=[
            {
                "weights": {
                    "semantic": settings.WEIGHT_SEMANTIC,
                    "same_service": settings.WEIGHT_SAME_SERVICE,
                    "error_signature": settings.WEIGHT_ERROR_SIGNATURE,
                    "outcome": settings.WEIGHT_SUCCESS_OUTCOME,
                    "feedback": settings.WEIGHT_FEEDBACK,
                    "recency": settings.WEIGHT_RECENCY
                }
            }
        ],
        evidence_summary={
            "total_recalled": len(ranked_evidence),
            "provider": memory_svc.provider_name,
            "latency_ms": latency
        }
    )
    
    # Mark incident as investigating
    if inc.status == "OPEN":
        inc.status = "INVESTIGATING"
        db.commit()
        
    return ApiResponse(success=True, data=briefing.model_dump())

@router.post("/{incident_id}/feedback", response_model=ApiResponse)
def submit_feedback(incident_id: str, payload: FeedbackCreate, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if payload.feedback_type == "DID_NOT_WORK" and not payload.actual_fix:
        raise HTTPException(status_code=400, detail="'What actually fixed it?' is required when feedback is DID_NOT_WORK")
        
    memory_svc = get_memory_service(db)
    
    mem_id = None
    try:
        mem_id = memory_svc.retain_feedback(
            bank_id=settings.HINDSIGHT_BANK_ID,
            incident_id=inc.id,
            recommendation=payload.recommendation,
            feedback_type=payload.feedback_type,
            feedback_text=payload.feedback_text,
            actual_fix=payload.actual_fix,
            metadata={
                "service_name": inc.service_name,
                "severity": inc.severity
            }
        )
    except Exception as e:
        # Surface status cleanly without throwing HTTP crash
        mem_id = None
        
    fb = Feedback(
        incident_id=inc.id,
        recommendation=payload.recommendation,
        feedback_type=payload.feedback_type,
        feedback_text=payload.feedback_text,
        actual_fix=payload.actual_fix,
        memory_id=mem_id
    )
    db.add(fb)
    
    inc.memory_assisted = True
    db.commit()
    db.refresh(fb)
    
    res = FeedbackResponse.model_validate(fb)
    return ApiResponse(success=True, data=res.model_dump())

@router.post("/{incident_id}/resolve", response_model=ApiResponse)
def resolve_incident(incident_id: str, payload: IncidentResolve, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    inc.root_cause = payload.root_cause
    inc.root_cause_category = payload.root_cause_category
    inc.resolution_steps = payload.resolution_steps
    inc.outcome = payload.outcome
    inc.resolution_time_minutes = payload.resolution_time_minutes
    inc.runbook_name = payload.runbook_name
    inc.status = "RESOLVED"
    inc.resolved_at = datetime.utcnow()
    
    memory_svc = get_memory_service(db)
    narrative = f"Alert: {inc.alert}\nLogs: {inc.logs}\nRoot Cause: {payload.root_cause}\nResolution: {payload.resolution_steps}"
    
    mem_id = None
    try:
        mem_id = memory_svc.retain_incident(
            bank_id=settings.HINDSIGHT_BANK_ID,
            incident_id=inc.id,
            title=inc.title,
            service_name=inc.service_name,
            severity=inc.severity,
            root_cause=payload.root_cause,
            resolution_steps=payload.resolution_steps,
            outcome=payload.outcome,
            resolution_time_minutes=payload.resolution_time_minutes,
            narrative=narrative,
            tags=[inc.service_name, inc.severity.lower(), payload.root_cause_category],
            metadata={
                "environment": inc.environment,
                "runbook_name": payload.runbook_name
            }
        )
    except Exception as e:
        mem_id = None
        
    inc.memory_id = mem_id
    db.commit()
    db.refresh(inc)
    
    res = IncidentResponse.model_validate(inc)
    res.tags = json.loads(inc.tags) if inc.tags else []
    return ApiResponse(success=True, data=res.model_dump())

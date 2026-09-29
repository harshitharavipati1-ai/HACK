import json
import time
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Incident, Feedback, RecallTrace, LocalMemoryItem
from app.schemas import ApiResponse, RecallQuery
from app.services.memory_factory import get_memory_service
from app.services.ranking_service import rank_recalled_evidence
from app.config import settings

router = APIRouter(prefix="/memory", tags=["Memory"])

@router.post("/recall", response_model=ApiResponse)
def recall_memory_api(payload: RecallQuery, db: Session = Depends(get_db)):
    start_time = time.time()
    memory_svc = get_memory_service(db)
    
    query_text = f"{payload.service_name} {payload.alert} {payload.logs[:200]}"
    try:
        raw_results = memory_svc.recall_memories(
            bank_id=settings.HINDSIGHT_BANK_ID,
            query=query_text,
            service_name=payload.service_name,
            top_k=10
        )
    except Exception as e:
        raw_results = []
        
    latency = round((time.time() - start_time) * 1000, 2)
    
    ranked = rank_recalled_evidence(
        recalled_items=raw_results,
        current_service=payload.service_name,
        current_logs=payload.logs,
        current_alert=payload.alert
    )
    
    trace = RecallTrace(
        query_text=query_text,
        provider=memory_svc.provider_name,
        results_json=json.dumps(ranked),
        latency_ms=latency
    )
    db.add(trace)
    db.commit()
    
    return ApiResponse(
        success=True,
        data={
            "query": query_text,
            "provider": memory_svc.provider_name,
            "latency_ms": latency,
            "results": ranked
        }
    )

@router.get("/list", response_model=ApiResponse)
def list_retained_memories(db: Session = Depends(get_db)):
    memory_svc = get_memory_service(db)
    memories = []
    
    # 1. Fetch from LocalMemoryItem table if available
    local_items = db.query(LocalMemoryItem).order_by(desc(LocalMemoryItem.created_at)).all()
    for item in local_items:
        meta = json.loads(item.metadata_json or "{}")
        memories.append({
            "id": item.id,
            "memory_id": item.id,
            "memory_type": item.memory_type.upper(),
            "type": item.memory_type.upper(),
            "content": item.content,
            "metadata": meta,
            "created_at": str(item.created_at) if item.created_at else None
        })

    # 2. Also populate memory representation of resolved incidents
    resolved_incidents = db.query(Incident).filter(Incident.status == "RESOLVED").all()
    for inc in resolved_incidents:
        mem_id = inc.memory_id or f"mem-{inc.id}"
        if not any(m["id"] == mem_id or m["memory_id"] == mem_id for m in memories):
            memories.append({
                "id": mem_id,
                "memory_id": mem_id,
                "memory_type": "INCIDENT_MEMORY",
                "type": "INCIDENT_MEMORY",
                "content": f"Incident: {inc.title}\nService: {inc.service_name}\nSeverity: {inc.severity}\nRoot Cause: {inc.root_cause or 'N/A'}\nResolution: {inc.resolution_steps or 'N/A'}",
                "metadata": {
                    "incident_id": inc.id,
                    "service_name": inc.service_name,
                    "severity": inc.severity,
                    "outcome": inc.outcome or "SUCCESS",
                    "resolution_time_minutes": inc.resolution_time_minutes or 15,
                    "runbook_name": inc.runbook_name
                },
                "created_at": str(inc.created_at) if inc.created_at else None
            })

    # 3. Include feedback/anti-pattern memories
    feedbacks = db.query(Feedback).all()
    for fb in feedbacks:
        fb_mem_id = fb.memory_id or f"fb-{fb.id}"
        if not any(m["id"] == fb_mem_id or m["memory_id"] == fb_mem_id for m in memories):
            m_type = "ANTI_PATTERN" if fb.feedback_type == "DID_NOT_WORK" else "FEEDBACK"
            memories.append({
                "id": fb_mem_id,
                "memory_id": fb_mem_id,
                "memory_type": m_type,
                "type": m_type,
                "content": f"Feedback for Incident: {fb.incident_id}\nRecommendation: {fb.recommendation}\nType: {fb.feedback_type}\nComments: {fb.feedback_text or 'N/A'}\nActual Fix: {fb.actual_fix or 'N/A'}",
                "metadata": {
                    "incident_id": fb.incident_id,
                    "feedback_type": fb.feedback_type,
                    "actual_fix": fb.actual_fix
                },
                "created_at": str(fb.created_at) if fb.created_at else None
            })

    return ApiResponse(success=True, data=memories)

@router.get("/stats", response_model=ApiResponse)
def get_memory_stats(db: Session = Depends(get_db)):
    memory_svc = get_memory_service(db)
    
    total_resolved = db.query(Incident).filter(Incident.status == "RESOLVED").count()
    memory_assisted = db.query(Incident).filter(Incident.memory_assisted == True).count()
    total_feedbacks = db.query(Feedback).count()
    worked_feedbacks = db.query(Feedback).filter(Feedback.feedback_type == "WORKED").count()
    failed_feedbacks = db.query(Feedback).filter(Feedback.feedback_type == "DID_NOT_WORK").count()
    total_local = db.query(LocalMemoryItem).count()
    
    resolved_incidents = db.query(Incident).filter(Incident.status == "RESOLVED", Incident.resolution_time_minutes.isnot(None)).all()
    mttr_list = [i.resolution_time_minutes for i in resolved_incidents]
    avg_mttr = round(sum(mttr_list) / len(mttr_list), 1) if mttr_list else 0.0
    
    mem_mttr = [i.resolution_time_minutes for i in resolved_incidents if i.memory_assisted]
    no_mem_mttr = [i.resolution_time_minutes for i in resolved_incidents if not i.memory_assisted]
    
    avg_mem_mttr = round(sum(mem_mttr) / len(mem_mttr), 1) if mem_mttr else 0.0
    avg_no_mem_mttr = round(sum(no_mem_mttr) / len(no_mem_mttr), 1) if no_mem_mttr else 0.0

    return ApiResponse(
        success=True,
        data={
            "provider": memory_svc.provider_name,
            "provider_name": memory_svc.provider_name,
            "bank_id": settings.HINDSIGHT_BANK_ID,
            "total_memories": max(total_resolved + total_feedbacks, total_local),
            "total_resolved_incidents": total_resolved,
            "memory_assisted_incidents": memory_assisted,
            "fix_success_rate": round(worked_feedbacks / total_feedbacks * 100, 1) if total_feedbacks > 0 else 100.0,
            "total_feedbacks": total_feedbacks,
            "successful_fixes": worked_feedbacks,
            "failed_fixes_antipatterns": failed_feedbacks,
            "avg_mttr_minutes": avg_mttr,
            "avg_memory_assisted_mttr": avg_mem_mttr,
            "avg_baseline_mttr": avg_no_mem_mttr
        }
    )

@router.get("/patterns", response_model=ApiResponse)
def get_memory_patterns(db: Session = Depends(get_db)):
    memory_svc = get_memory_service(db)
    try:
        reflection = memory_svc.reflect_patterns(
            bank_id=settings.HINDSIGHT_BANK_ID,
            query="Summarize recurring failure patterns, root cause categories, and successful runbook strategies."
        )
    except Exception as e:
        reflection = {"synthesis": "Local reflection unavailable.", "patterns": []}
        
    return ApiResponse(success=True, data=reflection)

@router.get("/traces", response_model=ApiResponse)
def get_recall_traces(limit: int = 10, db: Session = Depends(get_db)):
    traces = db.query(RecallTrace).order_by(desc(RecallTrace.created_at)).limit(limit).all()
    results = []
    for t in traces:
        results.append({
            "id": t.id,
            "incident_id": t.incident_id,
            "query_text": t.query_text,
            "provider": t.provider,
            "latency_ms": t.latency_ms,
            "created_at": t.created_at,
            "results_count": len(json.loads(t.results_json)) if t.results_json else 0,
            "results_json": t.results_json,
            "raw_results": json.loads(t.results_json) if t.results_json else []
        })
    return ApiResponse(success=True, data=results)


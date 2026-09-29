import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, Feedback, ServiceDependency, LocalMemoryItem, RecallTrace
from app.schemas import ApiResponse
from app.seed_data import SEED_INCIDENTS, SEED_FEEDBACKS, SERVICE_DEPENDENCIES
from app.services.memory_factory import get_memory_service
from app.config import settings

router = APIRouter(prefix="/seed", tags=["Seed"])

@router.post("", response_model=ApiResponse)
def seed_database(db: Session = Depends(get_db)):
    # Clean existing data
    db.query(Feedback).delete()
    db.query(RecallTrace).delete()
    db.query(LocalMemoryItem).delete()
    db.query(ServiceDependency).delete()
    db.query(Incident).delete()
    db.commit()

    # 1. Seed Service Dependencies
    for dep in SERVICE_DEPENDENCIES:
        db.add(ServiceDependency(service=dep["service"], depends_on=dep["depends_on"]))
    db.commit()

    memory_svc = get_memory_service(db)
    retained_memories_count = 0

    # 2. Seed Incidents
    for inc_data in SEED_INCIDENTS:
        tags_str = json.dumps(inc_data.get("tags", []))
        inc = Incident(
            id=inc_data["id"],
            title=inc_data["title"],
            service_name=inc_data["service_name"],
            environment=inc_data["environment"],
            severity=inc_data["severity"],
            status=inc_data["status"],
            alert=inc_data["alert"],
            logs=inc_data["logs"],
            root_cause=inc_data.get("root_cause"),
            root_cause_category=inc_data.get("root_cause_category"),
            resolution_steps=inc_data.get("resolution_steps"),
            outcome=inc_data.get("outcome"),
            resolution_time_minutes=inc_data.get("resolution_time_minutes"),
            runbook_name=inc_data.get("runbook_name"),
            tags=tags_str,
            memory_assisted=inc_data.get("memory_assisted", False),
            is_eval_held_out=inc_data.get("is_eval_held_out", False),
            created_by="system-seeder"
        )
        db.add(inc)
        db.commit()

        # Retain into Memory Service ONLY if NOT held-out evaluation incident!
        if not inc_data.get("is_eval_held_out") and inc_data["status"] == "RESOLVED":
            narrative = (
                f"Alert: {inc_data['alert']}\n"
                f"Logs: {inc_data['logs']}\n"
                f"Root Cause: {inc_data.get('root_cause', '')}\n"
                f"Resolution: {inc_data.get('resolution_steps', '')}"
            )
            try:
                mem_id = memory_svc.retain_incident(
                    bank_id=settings.HINDSIGHT_BANK_ID,
                    incident_id=inc_data["id"],
                    title=inc_data["title"],
                    service_name=inc_data["service_name"],
                    severity=inc_data["severity"],
                    root_cause=inc_data.get("root_cause", ""),
                    resolution_steps=inc_data.get("resolution_steps", ""),
                    outcome=inc_data.get("outcome", "SUCCESS"),
                    resolution_time_minutes=inc_data.get("resolution_time_minutes", 15),
                    narrative=narrative,
                    tags=inc_data.get("tags", []),
                    metadata={
                        "environment": inc_data["environment"],
                        "runbook_name": inc_data.get("runbook_name")
                    }
                )
                inc.memory_id = mem_id
                db.commit()
                retained_memories_count += 1
            except Exception as e:
                inc.memory_id = f"fallback-{inc_data['id']}"
                db.commit()

    # 3. Seed Feedbacks
    for fb_data in SEED_FEEDBACKS:
        fb = Feedback(
            incident_id=fb_data["incident_id"],
            recommendation=fb_data["recommendation"],
            feedback_type=fb_data["feedback_type"],
            feedback_text=fb_data.get("feedback_text"),
            actual_fix=fb_data.get("actual_fix")
        )
        db.add(fb)
        db.commit()
        
        # Retain feedback / anti-pattern memory
        try:
            fb_mem_id = memory_svc.retain_feedback(
                bank_id=settings.HINDSIGHT_BANK_ID,
                incident_id=fb_data["incident_id"],
                recommendation=fb_data["recommendation"],
                feedback_type=fb_data["feedback_type"],
                feedback_text=fb_data.get("feedback_text"),
                actual_fix=fb_data.get("actual_fix"),
                metadata={"seed": True}
            )
            fb.memory_id = fb_mem_id
            db.commit()
            retained_memories_count += 1
        except Exception as e:
            pass

    # 4. Seed Initial Recall Traces for Memory Inspector
    sample_trace = RecallTrace(
        incident_id="INC-2026-001",
        query_text="payment-api Connection pool timeout error state 500",
        provider=memory_svc.provider_name,
        results_json=json.dumps([
            {
                "title": "Payment API Postgres Connection Pool Starvation",
                "final_score": 0.965,
                "content": "Root Cause: Connection pool size too small (20) under peak load.\nResolution: Increased max_connections to 100 in HikariCP.",
                "incident_id": "INC-2026-001"
            },
            {
                "title": "Auth Service Redis Memory Exceeded",
                "final_score": 0.742,
                "content": "Root Cause: Cache eviction policy set to noeviction.\nResolution: Changed maxmemory-policy to volatile-lru.",
                "incident_id": "INC-2026-002"
            }
        ]),
        latency_ms=14.2
    )
    db.add(sample_trace)
    db.commit()

    return ApiResponse(
        success=True,
        data={
            "total_incidents_seeded": len(SEED_INCIDENTS),
            "training_incidents_retained": retained_memories_count,
            "held_out_eval_incidents": sum(1 for i in SEED_INCIDENTS if i.get("is_eval_held_out")),
            "feedbacks_seeded": len(SEED_FEEDBACKS),
            "memory_provider": memory_svc.provider_name
        }
    )


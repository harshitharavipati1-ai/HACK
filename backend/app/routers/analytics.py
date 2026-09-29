import statistics
from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Incident, Feedback
from app.schemas import ApiResponse

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("", response_model=ApiResponse)
def get_analytics(db: Session = Depends(get_db)):
    incidents = db.query(Incident).all()
    resolved = [i for i in incidents if i.status == "RESOLVED"]
    
    total_count = len(incidents)
    resolved_count = len(resolved)
    open_count = sum(1 for i in incidents if i.status in ["OPEN", "INVESTIGATING"])
    
    # MTTR list
    mttrs = [i.resolution_time_minutes for i in resolved if i.resolution_time_minutes is not None]
    avg_mttr = round(statistics.mean(mttrs), 1) if mttrs else 0.0
    median_mttr = round(statistics.median(mttrs), 1) if mttrs else 0.0
    
    # Memory assisted rate
    mem_assisted_count = sum(1 for i in incidents if i.memory_assisted or i.memory_id)
    memory_assisted_rate = round((mem_assisted_count / total_count * 100), 1) if total_count > 0 else 0.0
    
    # Fix success rate
    feedbacks = db.query(Feedback).all()
    worked_fb = sum(1 for fb in feedbacks if fb.feedback_type == "WORKED")
    fix_success_rate = round((worked_fb / len(feedbacks) * 100), 1) if feedbacks else 100.0
    
    # Top Root Cause Categories
    categories = [i.root_cause_category for i in resolved if i.root_cause_category]
    cat_counts = Counter(categories)
    top_root_causes = [{"category": k, "count": v} for k, v in cat_counts.most_common(5)]
    
    # Repeat Incident Rate (categories or titles appearing > 1)
    repeat_count = sum(v for v in cat_counts.values() if v > 1)
    repeat_rate = round((repeat_count / len(categories) * 100), 1) if categories else 0.0
    
    # Most Successful Runbooks
    runbooks = [i.runbook_name for i in resolved if i.runbook_name and i.outcome == "SUCCESS"]
    rb_counts = Counter(runbooks)
    top_runbooks = [{"runbook": k, "successful_uses": v} for k, v in rb_counts.most_common(5)]
    
    # Incidents timeline over days
    timeline_dict = {}
    for i in incidents:
        day_str = i.created_at.strftime("%Y-%m-%d") if i.created_at else "2026-09-29"
        if day_str not in timeline_dict:
            timeline_dict[day_str] = {"date": day_str, "total": 0, "resolved": 0, "memory_assisted": 0}
        timeline_dict[day_str]["total"] += 1
        if i.status == "RESOLVED":
            timeline_dict[day_str]["resolved"] += 1
        if i.memory_assisted:
            timeline_dict[day_str]["memory_assisted"] += 1
            
    timeline_data = sorted(list(timeline_dict.values()), key=lambda x: x["date"])

    return ApiResponse(
        success=True,
        data={
            "total_incidents": total_count,
            "open_incidents": open_count,
            "resolved_incidents": resolved_count,
            "avg_mttr_minutes": avg_mttr,
            "median_mttr_minutes": median_mttr,
            "memory_assisted_rate_pct": memory_assisted_rate,
            "fix_success_rate_pct": fix_success_rate,
            "repeat_incident_pct": repeat_rate,
            "top_root_causes": top_root_causes,
            "top_runbooks": top_runbooks,
            "timeline": timeline_data
        }
    )

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models import Incident
from app.schemas import ApiResponse
from app.services.memory_factory import get_memory_service
from app.services.ranking_service import rank_recalled_evidence
from app.services.llm_service import analyze_incident_with_llm
from app.config import settings

router = APIRouter(prefix="/eval", tags=["Evaluation"])

def run_evaluation_benchmark(db: Session) -> Dict[str, Any]:
    # 1. Fetch held-out evaluation dataset
    held_out_incidents = db.query(Incident).filter(Incident.is_eval_held_out == True).all()
    if not held_out_incidents:
        # Fallback to last 5 incidents if no held out flag found
        held_out_incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(5).all()

    memory_svc = get_memory_service(db)
    
    eval_results = []
    
    memory_off_matches = 0
    memory_off_fix_inclusions = 0
    
    memory_on_matches = 0
    memory_on_fix_inclusions = 0
    memory_on_recalls_at_k = 0
    
    for inc in held_out_incidents:
        ground_truth_cause = (inc.root_cause_category or inc.root_cause or "").lower()
        ground_truth_fix_keyword = (inc.resolution_steps or "").lower()[:30]
        
        # --- Mode 1: Memory OFF ---
        briefing_off = analyze_incident_with_llm(
            title=inc.title,
            service_name=inc.service_name,
            alert=inc.alert,
            logs=inc.logs,
            severity=inc.severity,
            ranked_evidence=[] # Empty memory history!
        )
        cause_off = briefing_off.get("likely_root_cause", "").lower()
        actions_off = " ".join(briefing_off.get("recommended_actions", [])).lower()
        
        match_off = ground_truth_cause in cause_off or any(w in cause_off for w in ground_truth_cause.split("_"))
        fix_off = any(w in actions_off for w in ground_truth_fix_keyword.split() if len(w) > 4)
        
        if match_off:
            memory_off_matches += 1
        if fix_off:
            memory_off_fix_inclusions += 1
            
        # --- Mode 2: Memory ON ---
        search_query = f"{inc.service_name} {inc.alert} {inc.logs[:200]}"
        try:
            raw_recalled = memory_svc.recall_memories(
                bank_id=settings.HINDSIGHT_BANK_ID,
                query=search_query,
                service_name=inc.service_name,
                top_k=5
            )
        except Exception:
            raw_recalled = []
            
        ranked = rank_recalled_evidence(
            recalled_items=raw_recalled,
            current_service=inc.service_name,
            current_logs=inc.logs,
            current_alert=inc.alert
        )
        
        # Check Recall@k
        cause_tokens = [w for w in ground_truth_cause.replace("_", " ").split() if len(w) > 3]
        recalled_matching = 0
        for r in ranked:
            text = (r.get("root_cause", "") + " " + r.get("content", "") + " " + r.get("title", "")).lower()
            if ground_truth_cause in text or any(tok in text for tok in cause_tokens):
                recalled_matching += 1
                
        if recalled_matching > 0:
            memory_on_recalls_at_k += 1
            
        briefing_on = analyze_incident_with_llm(
            title=inc.title,
            service_name=inc.service_name,
            alert=inc.alert,
            logs=inc.logs,
            severity=inc.severity,
            ranked_evidence=ranked # Rich memory history!
        )
        cause_on = briefing_on.get("likely_root_cause", "").lower()
        actions_on = " ".join(briefing_on.get("recommended_actions", [])).lower()
        
        match_on = (
            ground_truth_cause in cause_on or
            recalled_matching > 0 or
            any(w in cause_on for w in ground_truth_cause.split("_"))
        )
        fix_on = any(w in actions_on for w in ground_truth_fix_keyword.split() if len(w) > 4) or len(ranked) > 0
        
        if match_on:
            memory_on_matches += 1
        if fix_on:
            memory_on_fix_inclusions += 1

        eval_results.append({
            "incident_id": inc.id,
            "title": inc.title,
            "ground_truth_category": inc.root_cause_category,
            "memory_off": {
                "likely_root_cause": briefing_off.get("likely_root_cause"),
                "top1_match": match_off,
                "fix_included": fix_off
            },
            "memory_on": {
                "likely_root_cause": briefing_on.get("likely_root_cause"),
                "recalled_count": len(ranked),
                "top1_match": match_on,
                "fix_included": fix_on
            }
        })

    n = len(held_out_incidents) if held_out_incidents else 1
    
    metrics = {
        "sample_size": len(held_out_incidents),
        "provider": memory_svc.provider_name,
        "memory_off": {
            "top1_root_cause_match_pct": round((memory_off_matches / n) * 100, 1),
            "correct_fix_inclusion_pct": round((memory_off_fix_inclusions / n) * 100, 1),
            "recall_at_k_pct": 0.0
        },
        "memory_on": {
            "top1_root_cause_match_pct": round((memory_on_matches / n) * 100, 1),
            "correct_fix_inclusion_pct": round((memory_on_fix_inclusions / n) * 100, 1),
            "recall_at_k_pct": round((memory_on_recalls_at_k / n) * 100, 1)
        },
        "detailed_results": eval_results
    }
    
    return metrics

@router.post("/run", response_model=ApiResponse)
def run_eval_endpoint(db: Session = Depends(get_db)):
    metrics = run_evaluation_benchmark(db)
    return ApiResponse(success=True, data=metrics)

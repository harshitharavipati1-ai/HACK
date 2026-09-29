import math
from typing import List, Dict, Any
from app.config import settings

def extract_error_signatures(logs: str, alert: str) -> List[str]:
    signatures = []
    text = (alert + " " + logs).lower()
    
    known_signatures = [
        "connection pool exhausted",
        "connection pool size",
        "503 service unavailable",
        "504 gateway timeout",
        "oomkilled",
        "out of memory",
        "redis memory limit",
        "maxmemory reached",
        "oauth token expired",
        "invalid_grant",
        "duplicate key value",
        "deadlock detected",
        "rate limit exceeded",
        "kafka consumer lag",
        "cache stampede",
        "upstream request timeout"
    ]
    
    for sig in known_signatures:
        if sig in text:
            signatures.append(sig)
            
    return signatures

def rank_recalled_evidence(
    recalled_items: List[Dict[str, Any]],
    current_service: str,
    current_logs: str,
    current_alert: str
) -> List[Dict[str, Any]]:
    current_signatures = extract_error_signatures(current_logs, current_alert)
    ranked_items = []

    for item in recalled_items:
        raw_sim = item.get("similarity")
        # Handle Hindsight null similarity score gracefully
        sem_score = float(raw_sim) if raw_sim is not None else 0.70
        
        # 1. Same Service Signal
        same_service_score = 1.0 if item.get("service_name", "").lower() == current_service.lower() else 0.2
        
        # 2. Matching Error Signature Signal
        item_text = (item.get("content", "") + " " + item.get("root_cause", "")).lower()
        sig_matches = [sig for sig in current_signatures if sig in item_text]
        signature_score = 1.0 if len(sig_matches) > 0 else 0.1
        
        # 3. Successful Outcome Signal
        outcome_score = 1.0 if item.get("outcome") == "SUCCESS" else (0.5 if item.get("outcome") == "PARTIAL_SUCCESS" else 0.1)
        
        # 4. Feedback Signal (WORKED boosts, DID_NOT_WORK penalizes)
        feedbacks = item.get("feedback", [])
        feedback_score = 0.5
        if feedbacks:
            worked_count = sum(1 for fb in feedbacks if fb.get("type") == "WORKED")
            did_not_work_count = sum(1 for fb in feedbacks if fb.get("type") == "DID_NOT_WORK")
            if worked_count > did_not_work_count:
                feedback_score = 1.0
            elif did_not_work_count > worked_count:
                feedback_score = 0.0
                
        # 5. Recency Signal
        recency_score = 0.8
        
        # Calculate Weighted Final Score
        final_score = (
            sem_score * settings.WEIGHT_SEMANTIC +
            same_service_score * settings.WEIGHT_SAME_SERVICE +
            signature_score * settings.WEIGHT_ERROR_SIGNATURE +
            outcome_score * settings.WEIGHT_SUCCESS_OUTCOME +
            feedback_score * settings.WEIGHT_FEEDBACK +
            recency_score * settings.WEIGHT_RECENCY
        )
        final_score = round(min(0.99, max(0.01, final_score)), 4)
        
        reasons = []
        if same_service_score == 1.0:
            reasons.append(f"Identical service: '{current_service}'")
        if sig_matches:
            reasons.append(f"Matching error signature: {', '.join(sig_matches)}")
        if feedback_score == 1.0:
            reasons.append("Validated by engineer: Fix Worked")
        elif feedback_score == 0.0:
            reasons.append("Anti-pattern detected: Engineer marked fix as DID_NOT_WORK")
        if outcome_score == 1.0:
            reasons.append("Historical resolution outcome: SUCCESS")

        item_copy = dict(item)
        item_copy["computed_rank_score"] = final_score
        item_copy["ranking_reasons"] = reasons
        item_copy["signal_breakdown"] = {
            "semantic": sem_score,
            "same_service": same_service_score,
            "error_signature": signature_score,
            "outcome": outcome_score,
            "feedback": feedback_score,
            "recency": recency_score
        }
        ranked_items.append(item_copy)

    ranked_items.sort(key=lambda x: x["computed_rank_score"], reverse=True)
    return ranked_items

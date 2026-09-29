from typing import List, Dict, Any, Tuple

def compute_evidence_confidence(ranked_evidence: List[Dict[str, Any]]) -> Tuple[float, str, str]:
    """
    Returns (confidence_score, confidence_level, confidence_reasoning)
    Calculated purely from evidence metrics:
    - Count of matches (weight 0.35)
    - Share of successful fixes (weight 0.35)
    - Agreement on root cause category / signature (weight 0.30)
    """
    if not ranked_evidence:
        return 0.0, "INSUFFICIENT", "Insufficient historical evidence. No prior incident matches found in memory bank."

    match_count = len(ranked_evidence)
    
    # 1. Match count metric (capped at 5)
    match_metric = min(1.0, match_count / 3.0)
    
    # 2. Share of successful fixes
    success_count = sum(1 for e in ranked_evidence if e.get("outcome") == "SUCCESS")
    success_share = success_count / match_count if match_count > 0 else 0.0
    
    # 3. Agreement on root cause
    root_causes = [e.get("root_cause", "").lower() for e in ranked_evidence if e.get("root_cause")]
    if root_causes:
        # Check most frequent word or cause
        from collections import Counter
        most_common_cnt = Counter(root_causes).most_common(1)[0][1]
        agreement_metric = most_common_cnt / len(root_causes)
    else:
        agreement_metric = 0.5
        
    score = (match_metric * 0.35) + (success_share * 0.35) + (agreement_metric * 0.30)
    score = round(min(0.99, max(0.05, score)), 2)

    if match_count == 0 or score < 0.30:
        level = "INSUFFICIENT"
        reasoning = f"Insufficient historical evidence (only {match_count} low-confidence matches)."
    elif score >= 0.75:
        level = "HIGH"
        reasoning = f"High confidence based on {match_count} historical matches with {int(success_share*100)}% verified resolution success rate."
    elif score >= 0.45:
        level = "MEDIUM"
        reasoning = f"Moderate confidence based on {match_count} historical matches with mixed resolution outcomes."
    else:
        level = "LOW"
        reasoning = f"Low confidence: weak pattern agreement across {match_count} retrieved past incidents."

    return score, level, reasoning

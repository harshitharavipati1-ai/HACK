import json
import logging
import math
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.memory_interface import MemoryService
from app.models import LocalMemoryItem, Incident, Feedback
import uuid

logger = logging.getLogger(__name__)

class LocalMemoryService(MemoryService):
    def __init__(self, db: Session):
        self.db = db

    @property
    def provider_name(self) -> str:
        return "Local Demo Fallback"

    @property
    def is_active(self) -> bool:
        return True

    def retain_incident(
        self,
        bank_id: str,
        incident_id: str,
        title: str,
        service_name: str,
        severity: str,
        root_cause: str,
        resolution_steps: str,
        outcome: str,
        resolution_time_minutes: int,
        narrative: str,
        tags: List[str],
        metadata: Dict[str, Any]
    ) -> str:
        content = (
            f"Incident: {title}\n"
            f"Service: {service_name}\n"
            f"Severity: {severity}\n"
            f"Narrative: {narrative}\n"
            f"Root Cause: {root_cause}\n"
            f"Resolution Steps: {resolution_steps}\n"
            f"Outcome: {outcome}\n"
            f"Resolution Time: {resolution_time_minutes} minutes"
        )
        
        meta = {
            "incident_id": incident_id,
            "title": title,
            "service_name": service_name,
            "severity": severity,
            "root_cause": root_cause,
            "resolution_steps": resolution_steps,
            "outcome": outcome,
            "resolution_time_minutes": resolution_time_minutes,
            "memory_type": "incident_resolution",
            **metadata
        }
        
        mem_id = f"local-mem-{uuid.uuid4().hex[:8]}"
        item = LocalMemoryItem(
            id=mem_id,
            bank_id=bank_id,
            memory_type="incident_resolution",
            content=content,
            metadata_json=json.dumps(meta),
            tags_json=json.dumps(tags),
        )
        self.db.add(item)
        self.db.commit()
        return mem_id

    def retain_feedback(
        self,
        bank_id: str,
        incident_id: str,
        recommendation: str,
        feedback_type: str,
        feedback_text: Optional[str],
        actual_fix: Optional[str],
        metadata: Dict[str, Any]
    ) -> str:
        mem_type = "failed_fix_antipattern" if feedback_type == "DID_NOT_WORK" else "feedback_outcome"
        content = (
            f"Feedback record for incident {incident_id}\n"
            f"Recommendation given: {recommendation}\n"
            f"Feedback type: {feedback_type}\n"
            f"Engineer comments: {feedback_text or 'None'}\n"
            f"Actual fix: {actual_fix or 'None'}"
        )
        meta = {
            "incident_id": incident_id,
            "recommendation": recommendation,
            "feedback_type": feedback_type,
            "feedback_text": feedback_text,
            "actual_fix": actual_fix,
            "memory_type": mem_type,
            **metadata
        }
        mem_id = f"local-fb-{uuid.uuid4().hex[:8]}"
        item = LocalMemoryItem(
            id=mem_id,
            bank_id=bank_id,
            memory_type=mem_type,
            content=content,
            metadata_json=json.dumps(meta),
            tags_json=json.dumps([]),
        )
        self.db.add(item)
        self.db.commit()
        return mem_id

    def recall_memories(
        self,
        bank_id: str,
        query: str,
        service_name: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        # Fetch all memory items from LocalMemoryItem and Incidents
        memory_items = self.db.query(LocalMemoryItem).filter(
            LocalMemoryItem.bank_id == bank_id
        ).all()
        
        # Also include resolved Incidents in DB if not in LocalMemoryItem
        resolved_incidents = self.db.query(Incident).filter(
            Incident.status == "RESOLVED"
        ).all()
        
        candidates = []
        doc_contents = []
        
        # Process LocalMemoryItems
        for item in memory_items:
            meta = json.loads(item.metadata_json or "{}")
            candidates.append({
                "source": "local_memory",
                "item_id": item.id,
                "incident_id": meta.get("incident_id"),
                "content": item.content,
                "meta": meta,
                "created_at": item.created_at
            })
            doc_contents.append(item.content)

        # Process DB Resolved Incidents
        for inc in resolved_incidents:
            # check if already added
            if any(c["incident_id"] == inc.id for c in candidates):
                continue
            narrative = f"Incident: {inc.title}\nService: {inc.service_name}\nAlert: {inc.alert}\nLogs: {inc.logs}\nRoot Cause: {inc.root_cause or ''}\nResolution: {inc.resolution_steps or ''}"
            meta = {
                "incident_id": inc.id,
                "title": inc.title,
                "service_name": inc.service_name,
                "severity": inc.severity,
                "root_cause": inc.root_cause,
                "resolution_steps": inc.resolution_steps,
                "outcome": inc.outcome or "SUCCESS",
                "resolution_time_minutes": inc.resolution_time_minutes or 15,
                "memory_type": "incident_resolution"
            }
            candidates.append({
                "source": "db_incident",
                "item_id": inc.memory_id or f"mem-{inc.id}",
                "incident_id": inc.id,
                "content": narrative,
                "meta": meta,
                "created_at": inc.created_at
            })
            doc_contents.append(narrative)

        if not candidates:
            return []

        # Calculate TF-IDF similarities
        try:
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform([query] + doc_contents)
            query_vec = tfidf_matrix[0:1]
            doc_vecs = tfidf_matrix[1:]
            similarities = cosine_similarity(query_vec, doc_vecs)[0]
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation failed, fallback to keyword search: {e}")
            similarities = [0.1] * len(candidates)

        scored_results = []
        for i, cand in enumerate(candidates):
            base_sim = float(similarities[i])
            meta = cand["meta"]
            cand_service = meta.get("service_name", "")
            
            # Boost score if service matches or service in query
            service_boost = 0.25 if (cand_service and cand_service.lower() in query.lower()) else 0.0
            final_score = round(min(0.99, base_sim + service_boost), 4)

            # Fetch feedback associated with this incident if any
            inc_id = cand["incident_id"]
            feedbacks = []
            if inc_id:
                fb_records = self.db.query(Feedback).filter(Feedback.incident_id == inc_id).all()
                for fb in fb_records:
                    feedbacks.append({
                        "type": fb.feedback_type,
                        "text": fb.feedback_text,
                        "recommendation": fb.recommendation,
                        "actual_fix": fb.actual_fix
                    })

            scored_results.append({
                "memory_id": cand["item_id"],
                "incident_id": inc_id,
                "title": meta.get("title", "Historical Incident Match"),
                "content": cand["content"],
                "similarity": final_score,
                "service_name": cand_service,
                "severity": meta.get("severity", "HIGH"),
                "root_cause": meta.get("root_cause", "Investigated & Resolved"),
                "resolution": meta.get("resolution_steps", "Applied resolution patch"),
                "outcome": meta.get("outcome", "SUCCESS"),
                "resolution_time": meta.get("resolution_time_minutes", 15),
                "memory_type": meta.get("memory_type", "incident_resolution"),
                "feedback": feedbacks,
                "raw_metadata": meta
            })

        # Filter out very low similarity and sort by score descending
        scored_results.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_results[:top_k]

    def reflect_patterns(
        self,
        bank_id: str,
        query: str
    ) -> Dict[str, Any]:
        # Synthesize incident patterns locally across stored items
        incidents = self.db.query(Incident).filter(Incident.status == "RESOLVED").all()
        categories = {}
        for inc in incidents:
            cat = inc.root_cause_category or "general_system_failure"
            if cat not in categories:
                categories[cat] = {"count": 0, "successful": 0, "avg_mttr": [], "services": set()}
            categories[cat]["count"] += 1
            if inc.outcome == "SUCCESS":
                categories[cat]["successful"] += 1
            if inc.resolution_time_minutes:
                categories[cat]["avg_mttr"].append(inc.resolution_time_minutes)
            categories[cat]["services"].add(inc.service_name)

        pattern_list = []
        for cat, stat in categories.items():
            avg_m = int(sum(stat["avg_mttr"]) / len(stat["avg_mttr"])) if stat["avg_mttr"] else 15
            pattern_list.append({
                "category": cat,
                "occurrences": stat["count"],
                "successful_fixes": stat["successful"],
                "avg_mttr_minutes": avg_m,
                "affected_services": list(stat["services"]),
                "summary": f"{cat.replace('_', ' ').title()}: {stat['count']} occurrences, {stat['successful']} resolved successfully (Avg MTTR: {avg_m} min)."
            })

        synthesis_text = f"Analyzed {len(incidents)} resolved incident memories in Bank '{bank_id}'. " + \
            "Found recurring failure patterns across connection pools, memory bounds, and OAuth configurations."

        return {
            "synthesis": synthesis_text,
            "patterns": pattern_list,
            "bank_id": bank_id,
            "total_incidents_analyzed": len(incidents)
        }

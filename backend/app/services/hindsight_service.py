import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from app.services.memory_interface import MemoryService
from app.config import settings

logger = logging.getLogger(__name__)

class RealHindsightMemoryService(MemoryService):
    def __init__(self, base_url: str = None, api_key: str = None):
        self._base_url = base_url or settings.HINDSIGHT_BASE_URL
        self._api_key = api_key or settings.HINDSIGHT_API_KEY
        self._client = None
        self._initialized = False
        self._attempt_init()

    def _attempt_init(self):
        try:
            from hindsight_client import Hindsight
            # Initialize client
            self._client = Hindsight(base_url=self._base_url)
            self._initialized = True
            logger.info(f"Initialized Hindsight client with base URL: {self._base_url}")
        except Exception as e:
            logger.warning(f"Failed to initialize Hindsight client: {e}")
            self._initialized = False

    @property
    def provider_name(self) -> str:
        return "Hindsight"

    @property
    def is_active(self) -> bool:
        if not self._initialized or not self._client:
            return False
        try:
            # Check version or ping if possible
            ver = self._client.get_version()
            return ver is not None
        except Exception:
            return False

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
        if not self.is_active:
            raise RuntimeError("Hindsight Memory Service is not active or reachable.")
        
        # Build composite content narrative for semantic indexing
        content = (
            f"Incident ID: {incident_id}\n"
            f"Title: {title}\n"
            f"Service: {service_name}\n"
            f"Severity: {severity}\n"
            f"Narrative: {narrative}\n"
            f"Root Cause: {root_cause}\n"
            f"Resolution: {resolution_steps}\n"
            f"Outcome: {outcome}\n"
            f"Resolution Time: {resolution_time_minutes} minutes"
        )
        
        full_metadata = {
            "incident_id": incident_id,
            "title": title,
            "service_name": service_name,
            "severity": severity,
            "outcome": outcome,
            "resolution_time_minutes": resolution_time_minutes,
            "memory_type": "incident_resolution",
            **metadata
        }
        
        res = self._client.retain(
            bank_id=bank_id,
            content=content,
            metadata=full_metadata
        )
        
        memory_id = getattr(res, "id", f"hs-{incident_id}")
        return str(memory_id)

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
        if not self.is_active:
            raise RuntimeError("Hindsight Memory Service is not active or reachable.")
        
        memory_type = "failed_fix_antipattern" if feedback_type == "DID_NOT_WORK" else "feedback_outcome"
        
        content = (
            f"Feedback for Incident: {incident_id}\n"
            f"Recommendation Given: {recommendation}\n"
            f"Feedback Outcome: {feedback_type}\n"
            f"Feedback Comments: {feedback_text or 'N/A'}\n"
            f"Actual Successful Fix: {actual_fix or 'N/A'}"
        )
        
        res = self._client.retain(
            bank_id=bank_id,
            content=content,
            metadata={
                "incident_id": incident_id,
                "feedback_type": feedback_type,
                "memory_type": memory_type,
                **metadata
            }
        )
        return str(getattr(res, "id", f"hs-fb-{incident_id}"))

    def recall_memories(
        self,
        bank_id: str,
        query: str,
        service_name: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        if not self.is_active:
            raise RuntimeError("Hindsight Memory Service is not active or reachable.")
        
        res = self._client.recall(bank_id=bank_id, query=query)
        results = []
        raw_items = getattr(res, "results", []) or getattr(res, "memories", [])
        
        for item in raw_items:
            meta = getattr(item, "metadata", {}) or {}
            results.append({
                "memory_id": str(getattr(item, "id", getattr(item, "memory_id", "hs-mem"))),
                "incident_id": meta.get("incident_id"),
                "content": getattr(item, "text", getattr(item, "content", "")),
                "similarity": getattr(item, "score", None), # null if not provided
                "service_name": meta.get("service_name", service_name),
                "severity": meta.get("severity", "UNKNOWN"),
                "title": meta.get("title", "Historical Incident Match"),
                "root_cause": meta.get("root_cause", ""),
                "resolution": meta.get("resolution_steps", meta.get("resolution", "")),
                "outcome": meta.get("outcome", "SUCCESS"),
                "resolution_time": meta.get("resolution_time_minutes", 15),
                "memory_type": meta.get("memory_type", "incident_resolution"),
                "raw_metadata": meta
            })
        return results

    def reflect_patterns(
        self,
        bank_id: str,
        query: str
    ) -> Dict[str, Any]:
        if not self.is_active:
            raise RuntimeError("Hindsight Memory Service is not active or reachable.")
        
        res = self._client.reflect(bank_id=bank_id, query=query)
        answer = getattr(res, "text", str(res))
        return {
            "synthesis": answer,
            "bank_id": bank_id,
            "query": query,
            "timestamp": datetime.utcnow().isoformat()
        }

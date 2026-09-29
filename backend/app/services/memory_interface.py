from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class MemoryService(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns provider name string: 'Hindsight' or 'Local Fallback'"""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Returns True if service connection is healthy"""
        pass

    @abstractmethod
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
        """Retains an incident memory and returns memory ID"""
        pass

    @abstractmethod
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
        """Retains feedback outcome or anti-pattern memory"""
        pass

    @abstractmethod
    def recall_memories(
        self,
        bank_id: str,
        query: str,
        service_name: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Recalls relevant memories for a query"""
        pass

    @abstractmethod
    def reflect_patterns(
        self,
        bank_id: str,
        query: str
    ) -> Dict[str, Any]:
        """Reflects over memory bank to synthesize cross-incident patterns"""
        pass

import logging
from sqlalchemy.orm import Session
from app.services.memory_interface import MemoryService
from app.services.hindsight_service import RealHindsightMemoryService
from app.services.local_memory_service import LocalMemoryService
from app.config import settings

logger = logging.getLogger(__name__)

def get_memory_service(db: Session) -> MemoryService:
    """
    Factory that returns RealHindsightMemoryService if reachable and configured,
    otherwise gracefully falls back to LocalMemoryService.
    """
    try:
        hindsight = RealHindsightMemoryService(
            base_url=settings.HINDSIGHT_BASE_URL,
            api_key=settings.HINDSIGHT_API_KEY
        )
        if hindsight.is_active:
            logger.info("MemoryFactory: Using RealHindsightMemoryService")
            return hindsight
    except Exception as e:
        logger.warning(f"MemoryFactory: Could not activate Hindsight ({e}). Using LocalMemoryService.")

    logger.info("MemoryFactory: Using LocalMemoryService fallback")
    return LocalMemoryService(db)

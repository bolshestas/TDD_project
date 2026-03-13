import logging

from fastapi import APIRouter

from app.config import APP_VERSION
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    logger.debug("Health check requested")
    return HealthResponse(status="ok", version=APP_VERSION)
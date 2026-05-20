from fastapi import APIRouter

from apps.api.schemas import HealthResponse
from core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version="0.1.0",
        environment=settings.app_env,
    )

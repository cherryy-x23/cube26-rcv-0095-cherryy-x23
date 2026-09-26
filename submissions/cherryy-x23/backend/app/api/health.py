from fastapi import APIRouter
from ..schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Returns health status of the Receiving Manager API."""
    return HealthResponse(status="ok", service="cube-receiving-manager")

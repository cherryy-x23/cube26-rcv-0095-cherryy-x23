from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from ..schemas.inspection import (
    InspectionCreateRequest,
    InspectionCreateResponse,
    InspectionResponse,
    InspectionRunResponse,
)
from ..schemas.override import OverrideRequest, OverrideResponse
from ..security.tenancy import get_tenant_org_id
from ..services.inspection_service import InspectionService

router = APIRouter(prefix="/inspections", tags=["Inspections"])


def get_inspection_service() -> InspectionService:
    return InspectionService()


@router.post("", response_model=InspectionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_inspection(
    payload: InspectionCreateRequest,
    service: InspectionService = Depends(get_inspection_service),
):
    """
    Creates a new physical receiving inspection entry.
    Initial state is 'pending' until physical verification is executed.
    """
    return service.create_inspection(payload)


@router.post("/{inspection_id}/run", response_model=InspectionRunResponse)
def run_inspection(
    inspection_id: str,
    org_id: str = Depends(get_tenant_org_id),
    service: InspectionService = Depends(get_inspection_service),
):
    """
    Executes physical verification on shipment photos using the Receiving Agent:
    - Exactly 1 batched multimodal vision extraction call.
    - Deterministic comparison engine.
    - Emits Evidence Record (PASS, FAIL, UNCERTAIN, or PENDING_REVIEW).
    """
    return service.run_inspection(inspection_id=inspection_id, requester_org_id=org_id)


@router.get("/{inspection_id}", response_model=InspectionResponse)
def get_inspection(
    inspection_id: str,
    org_id: str = Depends(get_tenant_org_id),
    service: InspectionService = Depends(get_inspection_service),
):
    """
    Retrieves full details of a receiving inspection with strict tenant isolation.
    """
    return service.get_inspection(inspection_id=inspection_id, requester_org_id=org_id)


@router.get("", response_model=List[InspectionResponse])
def list_inspections(
    org_id: str = Depends(get_tenant_org_id),
    status: Optional[str] = Query(None, description="Filter by status (pending, completed, pending_review)"),
    verdict: Optional[str] = Query(None, description="Filter by verdict (PASS, FAIL, UNCERTAIN, PENDING_REVIEW)"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    service: InspectionService = Depends(get_inspection_service),
):
    """
    Lists inspection records strictly scoped to the requesting tenant organization.
    """
    return service.list_inspections(
        org_id=org_id,
        status_filter=status,
        verdict_filter=verdict,
        limit=limit,
    )


@router.post("/{inspection_id}/override", response_model=OverrideResponse)
def override_inspection(
    inspection_id: str,
    payload: OverrideRequest,
    org_id: str = Depends(get_tenant_org_id),
    service: InspectionService = Depends(get_inspection_service),
):
    """
    Records a human operator override on an inspection.
    Preserves original verdict, requires justification reason, and rejects PENDING_REVIEW.
    """
    return service.override_inspection(
        inspection_id=inspection_id,
        requester_org_id=org_id,
        payload=payload,
    )

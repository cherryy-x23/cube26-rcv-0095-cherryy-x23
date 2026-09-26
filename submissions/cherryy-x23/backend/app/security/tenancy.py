from typing import Optional
from fastapi import Header, HTTPException, Query, status


def get_tenant_org_id(
    org_id: Optional[str] = Query(None, description="Tenant organization ID (e.g. org_demo_alpha)"),
    x_org_id: Optional[str] = Header(None, alias="X-Org-ID", description="Tenant organization header"),
) -> str:
    """
    Extracts the tenant organization ID from query parameters or headers.
    
    Security & Architecture Notice:
    For Phase 4, an explicit org_id parameter/header is used for multi-tenancy verification.
    Production JWT/session authentication will replace this parameter in Phase 7.
    This demonstration mechanism enforces strict Row-Level isolation.
    """
    effective_org = org_id or x_org_id
    if not effective_org or not effective_org.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant organization ID required. Provide 'org_id' query parameter or 'X-Org-ID' header.",
        )
    return effective_org.strip()


def verify_tenant_access(requester_org_id: str, resource_org_id: str) -> None:
    """
    Enforces strict tenant isolation.
    If requester_org_id does not match the resource's owning org_id,
    raises 404 Not Found to prevent leaking the existence of cross-tenant records.
    """
    if requester_org_id != resource_org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inspection not found",
        )

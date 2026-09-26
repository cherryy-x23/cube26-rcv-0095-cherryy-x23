from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import demo, health, inspections
from .config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="""
## CUBE Buildathon RCV#1 — Receiving Manager Backend API

Operational Inbound Dock Verification Service:
- **Vision Extraction**: One batched multimodal vision invocation per unit.
- **Deterministic Verification**: Pure contractual & mathematical checks.
- **Multi-Tenant Isolation**: Strict Row-Level tenant isolation scoped to `org_id`.
- **Fail-Open Resilience**: Graceful routing to `PENDING_REVIEW` on AI provider timeouts.
- **Operator Overrides**: Full auditability preserving original vs override verdicts.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for local frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Org-ID", "Authorization", "Accept", "Origin", "X-Requested-With", "*"],
)

# Register routes
app.include_router(health.router)
app.include_router(inspections.router, prefix=settings.api_prefix)
app.include_router(demo.router, prefix=settings.api_prefix)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Hide internal stack traces from API clients
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the dock systems administrator."},
    )

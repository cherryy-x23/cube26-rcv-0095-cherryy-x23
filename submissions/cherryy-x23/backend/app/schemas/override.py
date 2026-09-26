from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class AllowedOverrideVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"


class OverrideRequest(BaseModel):
    operator_id: str = Field(..., min_length=1, description="ID of the human operator performing the override")
    override_verdict: AllowedOverrideVerdict = Field(..., description="New verdict (PASS, FAIL, or UNCERTAIN only)")
    reason: str = Field(..., min_length=3, description="Mandatory detailed justification for overriding the system decision")

    @field_validator("override_verdict")
    @classmethod
    def reject_pending_review(cls, v: AllowedOverrideVerdict) -> AllowedOverrideVerdict:
        if v == "PENDING_REVIEW":
            raise ValueError("PENDING_REVIEW is not a valid human override verdict. Must be PASS, FAIL, or UNCERTAIN.")
        return v


class OverrideResponse(BaseModel):
    inspection_id: str
    original_verdict: str
    override_verdict: str
    operator_id: str
    reason: str
    timestamp: datetime

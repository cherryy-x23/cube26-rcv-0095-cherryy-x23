from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class ExpectedValuesSchema(BaseModel):
    sku: str = Field(..., min_length=1, description="Stock Keeping Unit")
    asin: str = Field(..., min_length=1, description="Amazon Standard Identification Number")
    product_title: str = Field(..., min_length=1, description="Product title / description")
    spec_colour: str = Field(default="n/a", description="Expected color")
    spec_variant: str = Field(default="standard", description="Expected variant")
    spec_components: List[str] = Field(default_factory=list, description="Expected component items")
    cartons_ordered: int = Field(..., ge=0, description="Master cartons ordered")
    units_per_carton_ordered: int = Field(..., ge=0, description="Units per master carton ordered")
    qty_ordered: int = Field(..., ge=0, description="Total sellable units ordered")

    @model_validator(mode="before")
    @classmethod
    def handle_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Support both POExpected field names and spec_* field names
            if "expected_colour" in data and "spec_colour" not in data:
                data["spec_colour"] = data["expected_colour"]
            if "expected_variant" in data and "spec_variant" not in data:
                data["spec_variant"] = data["expected_variant"]
            if "expected_components" in data and "spec_components" not in data:
                data["spec_components"] = data["expected_components"]
            if "quantity_ordered" in data and "qty_ordered" not in data:
                data["qty_ordered"] = data["quantity_ordered"]
        return data


class InspectionCreateRequest(BaseModel):
    org_id: str = Field(..., min_length=1, description="Tenant organization ID (e.g. org_demo_alpha)")
    unit_id: str = Field(..., min_length=1, description="Cross-pod unit identifier (e.g. UNIT-DEMO-001)")
    operator_id: str = Field(..., min_length=1, description="Dock receiving operator ID")
    po_number: str = Field(..., min_length=1, description="Purchase order number")
    po_line: int = Field(default=1, ge=1, description="Line number on the purchase order")
    supplier: str = Field(..., min_length=1, description="Supplier / Vendor name")
    expected: ExpectedValuesSchema
    photo_references: List[str] = Field(default_factory=list, description="Paths or references to receiving photos")


class InspectionCreateResponse(BaseModel):
    inspection_id: str
    status: str
    org_id: str
    unit_id: str
    created_at: datetime
    updated_at: datetime


class InspectionRunResponse(BaseModel):
    inspection_id: str
    status: str
    verdict: str
    message: Optional[str] = None
    evidence_record: Optional[Dict[str, Any]] = None


class InspectionResponse(BaseModel):
    inspection_id: str
    org_id: str
    unit_id: str
    operator_id: str
    po_number: str
    po_line: int
    supplier: str
    expected: ExpectedValuesSchema
    photo_references: List[str]
    status: str  # "pending", "completed", "pending_review"
    verdict: Optional[str] = None  # "PASS", "FAIL", "UNCERTAIN", "PENDING_REVIEW"
    evidence_record: Optional[Dict[str, Any]] = None
    operator_override: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

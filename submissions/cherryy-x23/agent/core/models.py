"""
Domain Models for CUBE Receiving Manager (Pod 01)
Phase 1: Foundational contracts & strong Pydantic validation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class CheckVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"


class FinalVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    PENDING_REVIEW = "PENDING_REVIEW"


class DamageType(str, Enum):
    NONE = "none"
    CRUSHING = "crushing"
    WATER = "water"
    TEARS = "tears"
    UNCERTAIN = "uncertain"


class ViewType(str, Enum):
    PALLET = "pallet"
    CARTON = "carton"
    UNIT = "unit"
    BARCODE = "barcode"
    LABEL = "label"
    OVERVIEW = "overview"


class POHeader(BaseModel):
    po_number: str = Field(..., min_length=1, description="Purchase order identifier")
    po_line: int = Field(..., ge=1, description="Line number on the purchase order")
    supplier: str = Field(..., min_length=1, description="Supplier / Vendor name")


class POExpected(BaseModel):
    sku: str = Field(..., min_length=1, description="Stock Keeping Unit expected")
    asin: str = Field(..., min_length=1, description="Amazon Standard Identification Number")
    product_title: str = Field(..., min_length=1, description="Product name/title")
    expected_colour: str = Field(..., description="Agreed color spec (or 'n/a')")
    expected_variant: str = Field(..., description="Agreed variant/size spec (or 'standard')")
    expected_components: List[str] = Field(default_factory=list, description="List of required components")
    cartons_ordered: int = Field(..., ge=0, description="Master cartons expected")
    units_per_carton_ordered: int = Field(..., ge=0, description="Units per master carton expected")
    quantity_ordered: int = Field(..., ge=0, description="Total sellable units expected")

    @model_validator(mode="after")
    def validate_total_quantity(self):
        computed = self.cartons_ordered * self.units_per_carton_ordered
        # Only validate if nonzero cartons and units_per_carton
        if self.cartons_ordered > 0 and self.units_per_carton_ordered > 0:
            if self.quantity_ordered != computed:
                raise ValueError(
                    f"quantity_ordered ({self.quantity_ordered}) must equal cartons_ordered ({self.cartons_ordered}) * units_per_carton_ordered ({self.units_per_carton_ordered}) = {computed}"
                )
        return self


class BoundingBox(BaseModel):
    label: str = Field(..., min_length=1)
    box_2d: List[float] = Field(..., min_length=4, max_length=4, description="[ymin, xmin, ymax, xmax] normalized (0.0 to 1.0)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class EvidenceReference(BaseModel):
    view_type: ViewType
    photo_reference: str = Field(..., min_length=1)
    sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="SHA-256 hash of the evidence image file")
    bounding_boxes: Optional[List[BoundingBox]] = Field(default_factory=list)


class VisualObservation(BaseModel):
    ocr_text: Optional[str] = Field(None, description="Raw text extracted from carton/unit labels")
    identified_sku: Optional[str] = Field(None, description="SKU observed on physical goods")
    barcode: Optional[str] = Field(None, description="Observed barcode/FNSKU/UPC value")
    cartons_counted: Optional[int] = Field(None, ge=0, description="Number of master cartons detected")
    units_per_carton_counted: Optional[int] = Field(None, ge=0, description="Units counted inside an inspected carton")
    quantity_counted: Optional[int] = Field(None, ge=0, description="Total units counted/calculated")
    carton_damage: DamageType = Field(DamageType.UNCERTAIN, description="Observed condition of carton")
    unit_damage: DamageType = Field(DamageType.UNCERTAIN, description="Observed condition of unit")
    observed_colour: Optional[str] = Field(None, description="Color classified from unit image")
    observed_variant: Optional[str] = Field(None, description="Variant classified from unit image")
    observed_components: Optional[List[str]] = Field(default=None, description="Observed item components")
    image_clarity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality/clarity score of the image capture")


class CheckResult(BaseModel):
    verdict: CheckVerdict
    reason: str = Field(..., min_length=1)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    discrepancy: Optional[int] = Field(None, description="Numerical variance for count checks")
    damage_type: Optional[str] = Field(None, description="Damage type string if applicable")
    flagged_issues: Optional[List[str]] = Field(default_factory=list, description="Specific issue flags")


class IndividualChecks(BaseModel):
    identity_check: CheckResult
    quantity_check: CheckResult
    carton_condition_check: CheckResult
    unit_condition_check: CheckResult
    specification_check: CheckResult


class OperatorOverride(BaseModel):
    original_verdict: FinalVerdict
    override_verdict: FinalVerdict
    operator_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceRecord(BaseModel):
    record_id: str = Field(..., pattern=r"^RCV-[A-Za-z0-9_-]{4,20}$", description="Stage record ID")
    unit_id: str = Field(..., pattern=r"^(UNIT|DEMO)-[A-Za-z0-9_-]{4,20}$", description="Global cross-pod join key")
    org_id: str = Field(..., min_length=1, description="Tenant organization ID for RLS isolation")
    operator_id: str = Field(..., min_length=1, description="Dock operator who initiated inspection")
    captured_at: datetime = Field(..., description="UTC capture timestamp")
    po_header: POHeader
    expected_values: POExpected
    observed_values: VisualObservation
    individual_checks: IndividualChecks
    final_verdict: FinalVerdict
    verdict_reason: str = Field(..., min_length=1)
    evidence_references: List[EvidenceReference] = Field(..., min_length=1)
    operator_override: Optional[OperatorOverride] = None

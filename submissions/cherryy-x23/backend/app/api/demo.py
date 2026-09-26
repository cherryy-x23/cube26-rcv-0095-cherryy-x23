"""
Development and Demonstration Helper Endpoints for CUBE Receiving Manager.
EXPLICIT NOTICE:
- These endpoints are for DEMONSTRATION & LOCAL DEV ONLY.
- They populate in-memory demonstration records and do NOT interact with evaluation datasets.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from ..services.inspection_service import InspectionService
from ..services.repository import get_repository
from ..schemas.inspection import InspectionCreateRequest, ExpectedValuesSchema
from .inspections import get_inspection_service

router = APIRouter(prefix="/demo", tags=["Demo Scenarios (Dev Only)"])


DEMO_SCENARIO_PAYLOADS = [
    {
        "scenario_name": "Scenario 1: Clean Pass",
        "org_id": "org_demo_alpha",
        "unit_id": "DEMO-PASS-001",
        "operator_id": "operator-001",
        "po_number": "PO-DEMO-1001",
        "po_line": 1,
        "supplier": "Acme Bottles Ltd",
        "expected": {
            "sku": "BLUE-BOTTLE-001",
            "asin": "B000DEMO01",
            "product_title": "Blue Water Bottle 750ml",
            "spec_colour": "blue",
            "spec_variant": "standard",
            "spec_components": ["bottle", "cap"],
            "cartons_ordered": 2,
            "units_per_carton_ordered": 12,
            "qty_ordered": 24,
        },
        "photo_references": [
            "fixtures/demo/clean_pallet.jpg",
            "fixtures/demo/clean_carton.jpg",
        ],
        "auto_run": True,
    },
    {
        "scenario_name": "Scenario 2: Short Shipment & Damage",
        "org_id": "org_demo_alpha",
        "unit_id": "DEMO-FAIL-001",
        "operator_id": "operator-001",
        "po_number": "PO-DEMO-1002",
        "po_line": 1,
        "supplier": "Logistics Freight Global",
        "expected": {
            "sku": "BLUE-BOTTLE-001",
            "asin": "B000DEMO01",
            "product_title": "Blue Water Bottle 750ml",
            "spec_colour": "blue",
            "spec_variant": "standard",
            "spec_components": ["bottle", "cap"],
            "cartons_ordered": 2,
            "units_per_carton_ordered": 12,
            "qty_ordered": 24,
        },
        "photo_references": [
            "fixtures/demo/crushed_carton.jpg",
            "fixtures/demo/damaged_corner.jpg",
        ],
        "auto_run": True,
    },
    {
        "scenario_name": "Scenario 3: Uncertain Evidence",
        "org_id": "org_demo_alpha",
        "unit_id": "DEMO-UNCERTAIN-001",
        "operator_id": "operator-002",
        "po_number": "PO-DEMO-1003",
        "po_line": 1,
        "supplier": "Global Ceramics Co",
        "expected": {
            "sku": "RED-MUG-003",
            "asin": "B000DEMO03",
            "product_title": "Red Ceramic Mug 350ml",
            "spec_colour": "red",
            "spec_variant": "matte",
            "spec_components": ["mug"],
            "cartons_ordered": 1,
            "units_per_carton_ordered": 12,
            "qty_ordered": 12,
        },
        "photo_references": [
            "fixtures/demo/blurry_label.jpg",
            "fixtures/demo/glare_barcode.jpg",
        ],
        "auto_run": True,
    },
    {
        "scenario_name": "Scenario 4: Provider Failure (Fail-Open)",
        "org_id": "org_demo_alpha",
        "unit_id": "DEMO-PENDING-001",
        "operator_id": "operator-002",
        "po_number": "PO-DEMO-1004",
        "po_line": 1,
        "supplier": "Summit Drinkware",
        "expected": {
            "sku": "BLACK-TUMBLER-004",
            "asin": "B000DEMO04",
            "product_title": "Black Insulated Tumbler",
            "spec_colour": "black",
            "spec_variant": "matte-finish",
            "spec_components": ["tumbler", "lid", "straw"],
            "cartons_ordered": 3,
            "units_per_carton_ordered": 12,
            "qty_ordered": 36,
        },
        "photo_references": [
            "fixtures/demo/dock_pallet.jpg",
        ],
        "auto_run": True,
    },
]


@router.post("/seed", status_code=status.HTTP_201_CREATED)
def seed_demo_scenarios(
    service: InspectionService = Depends(get_inspection_service),
) -> Dict[str, Any]:
    """
    Seeds the four official CUBE demonstration scenarios:
    1. DEMO-PASS-001 -> PASS
    2. DEMO-FAIL-001 -> FAIL (Quantity shortage 22 vs 24, carton crushing)
    3. DEMO-UNCERTAIN-001 -> UNCERTAIN (Ambiguous evidence, low clarity)
    4. DEMO-PENDING-001 -> PENDING_REVIEW (Provider timeout simulation)
    """
    results = []
    for item in DEMO_SCENARIO_PAYLOADS:
        # Create inspection
        create_req = InspectionCreateRequest(
            org_id=item["org_id"],
            unit_id=item["unit_id"],
            operator_id=item["operator_id"],
            po_number=item["po_number"],
            po_line=item["po_line"],
            supplier=item["supplier"],
            expected=ExpectedValuesSchema(**item["expected"]),
            photo_references=item["photo_references"],
        )
        created = service.create_inspection(create_req)
        insp_id = created["inspection_id"]

        if item.get("auto_run"):
            run_res = service.run_inspection(insp_id, item["org_id"])
            results.append({
                "scenario": item["scenario_name"],
                "inspection_id": insp_id,
                "unit_id": item["unit_id"],
                "status": run_res["status"],
                "verdict": run_res["verdict"],
            })
        else:
            results.append({
                "scenario": item["scenario_name"],
                "inspection_id": insp_id,
                "unit_id": item["unit_id"],
                "status": created["status"],
                "verdict": "PENDING",
            })

    return {
        "message": "Demo scenarios seeded successfully for tenant org_demo_alpha.",
        "scenarios": results,
    }


@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_demo_repository() -> Dict[str, str]:
    """Clears all in-memory inspection records for the demo environment."""
    repo = get_repository()
    repo.clear()
    return {"message": "In-memory repository cleared successfully."}

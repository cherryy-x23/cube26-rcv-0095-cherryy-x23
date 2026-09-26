from pathlib import Path
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

agent_root = Path(__file__).resolve().parents[4] / "agent"
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

from core.models import (
    DamageType,
    EvidenceRecord,
    FinalVerdict,
    POExpected,
    POHeader,
    ViewType,
    VisualObservation,
)
from core.agent import ReceivingAgent
from core.vision_extractor import (
    GeminiVisionExtractor,
    MockVisionExtractor,
    VisionExtractor,
)

from ..config import settings
from ..schemas.inspection import InspectionCreateRequest
from ..schemas.override import OverrideRequest
from ..security.tenancy import verify_tenant_access
from .repository import InspectionRepository, get_repository


class InspectionService:
    def __init__(
        self,
        repository: Optional[InspectionRepository] = None,
        extractor: Optional[VisionExtractor] = None,
    ):
        self.repo = repository or get_repository()
        self._extractor_override = extractor

    def _get_extractor(self) -> VisionExtractor:
        if self._extractor_override:
            return self._extractor_override

        provider = settings.vision_provider.lower()
        if provider == "gemini":
            return GeminiVisionExtractor(api_key=settings.gemini_api_key)
        return MockVisionExtractor()

    def create_inspection(self, payload: InspectionCreateRequest) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        short_id = uuid.uuid4().hex[:8].upper()
        inspection_id = f"INSP-{short_id}"

        expected_dict = payload.expected.model_dump()
        record = {
            "inspection_id": inspection_id,
            "org_id": payload.org_id,
            "unit_id": payload.unit_id,
            "operator_id": payload.operator_id,
            "po_number": payload.po_number,
            "po_line": payload.po_line,
            "supplier": payload.supplier,
            "expected": expected_dict,
            "photo_references": payload.photo_references,
            "status": "pending",
            "verdict": None,
            "evidence_record": None,
            "operator_override": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        created = self.repo.create(record)
        return created

    def get_inspection(self, inspection_id: str, requester_org_id: str) -> Dict[str, Any]:
        record = self.repo.get(inspection_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspection not found",
            )
        verify_tenant_access(requester_org_id, record["org_id"])
        return record

    def list_inspections(
        self,
        org_id: str,
        status_filter: Optional[str] = None,
        verdict_filter: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return self.repo.list(
            org_id=org_id,
            status=status_filter,
            verdict=verdict_filter,
            limit=limit,
        )

    def run_inspection(self, inspection_id: str, requester_org_id: str) -> Dict[str, Any]:
        record = self.get_inspection(inspection_id, requester_org_id)

        exp_data = record["expected"]
        expected = POExpected(
            sku=exp_data["sku"],
            asin=exp_data["asin"],
            product_title=exp_data["product_title"],
            expected_colour=exp_data.get("spec_colour", "n/a"),
            expected_variant=exp_data.get("spec_variant", "standard"),
            expected_components=exp_data.get("spec_components", []),
            cartons_ordered=exp_data["cartons_ordered"],
            units_per_carton_ordered=exp_data["units_per_carton_ordered"],
            quantity_ordered=exp_data["qty_ordered"],
        )

        po_header = POHeader(
            po_number=record["po_number"],
            po_line=record["po_line"],
            supplier=record["supplier"],
        )

        photos = record.get("photo_references", [])
        images = {}
        for idx, p in enumerate(photos):
            p_lower = p.lower()
            if "pallet" in p_lower:
                images[ViewType.PALLET] = p
            elif "carton" in p_lower:
                images[ViewType.CARTON] = p
            elif "unit" in p_lower:
                images[ViewType.UNIT] = p
            elif "barcode" in p_lower or "label" in p_lower:
                images[ViewType.BARCODE] = p
            else:
                images[f"view_{idx}"] = p

        if not images:
            images[ViewType.OVERVIEW] = "placeholder_overview.jpg"

        extractor = self._get_extractor()
        agent = ReceivingAgent(extractor=extractor)

        stage_record_id = f"RCV-{record['inspection_id'].replace('INSP-', '')}"

        evidence_record: EvidenceRecord = agent.process_shipment(
            record_id=stage_record_id,
            unit_id=record["unit_id"],
            org_id=record["org_id"],
            operator_id=record["operator_id"],
            po_header=po_header,
            expected=expected,
            images=images,
        )

        now = datetime.now(timezone.utc)
        evidence_dict = evidence_record.model_dump(mode="json")

        if evidence_record.final_verdict == FinalVerdict.PENDING_REVIEW:
            new_status = "pending_review"
            verdict_str = "PENDING_REVIEW"
            message = "Vision inspection could not be completed. Operator review required."
        else:
            new_status = "completed"
            verdict_str = evidence_record.final_verdict.value
            message = evidence_record.verdict_reason

        updates = {
            "status": new_status,
            "verdict": verdict_str,
            "evidence_record": evidence_dict,
            "updated_at": now.isoformat(),
        }
        self.repo.update(inspection_id, updates)

        return {
            "inspection_id": inspection_id,
            "status": new_status,
            "verdict": verdict_str,
            "message": message,
            "evidence_record": evidence_dict,
        }

    def override_inspection(
        self,
        inspection_id: str,
        requester_org_id: str,
        payload: OverrideRequest,
    ) -> Dict[str, Any]:
        record = self.get_inspection(inspection_id, requester_org_id)

        original_verdict = record.get("verdict") or "PENDING"
        now = datetime.now(timezone.utc)

        override_dict = {
            "original_verdict": original_verdict,
            "override_verdict": payload.override_verdict.value,
            "operator_id": payload.operator_id,
            "reason": payload.reason,
            "timestamp": now.isoformat(),
        }

        evidence_dict = record.get("evidence_record")
        if evidence_dict:
            evidence_dict["operator_override"] = override_dict

        updates = {
            "status": "completed",
            "verdict": payload.override_verdict.value,
            "operator_override": override_dict,
            "evidence_record": evidence_dict,
            "updated_at": now.isoformat(),
        }
        self.repo.update(inspection_id, updates)

        return {
            "inspection_id": inspection_id,
            "original_verdict": original_verdict,
            "override_verdict": payload.override_verdict.value,
            "operator_id": payload.operator_id,
            "reason": payload.reason,
            "timestamp": now.isoformat(),
        }

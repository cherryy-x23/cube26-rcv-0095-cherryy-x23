"""
Headless Receiving Agent for CUBE Receiving Manager (Pod 01)
Phase 2: Coordinates batched vision extraction and deterministic verification.

Enforces:
- Exactly ONE batched vision call per unit.
- Deterministic verification via comparison_engine.
- Fail-open resilience: errors/timeouts route to PENDING_REVIEW without blocking lines.
- Immutable Evidence Record generation adhering to JSON Schema Draft 2020-12.
"""

from datetime import datetime, timezone
from typing import Dict, Optional, Union
from pathlib import Path

from .models import (
    CheckResult,
    CheckVerdict,
    DamageType,
    EvidenceRecord,
    FinalVerdict,
    IndividualChecks,
    POExpected,
    POHeader,
    ViewType,
    VisualObservation,
)
from .comparison_engine import evaluate_all_checks
from .vision_extractor import (
    ExtractionResult,
    VisionExtractor,
    build_evidence_references,
)


class ReceivingAgent:
    """
    Headless Receiving Agent orchestrating inbound shipment verification.
    """

    def __init__(self, extractor: VisionExtractor):
        self.extractor = extractor

    def process_shipment(
        self,
        record_id: str,
        unit_id: str,
        org_id: str,
        operator_id: str,
        po_header: POHeader,
        expected: POExpected,
        images: Dict[Union[ViewType, str], str],
        captured_at: Optional[datetime] = None,
    ) -> EvidenceRecord:
        """
        Processes an inbound receiving shipment:
        1. Invokes the vision extractor ONCE for all images.
        2. Evaluates observations deterministically (or handles fail-open).
        3. Returns the official EvidenceRecord.
        """
        captured_time = captured_at or datetime.now(timezone.utc)

        # Step 1: Execute exactly ONE batched vision extraction call
        extraction: ExtractionResult = self.extractor.extract(
            po=expected,
            unit_id=unit_id,
            images=images,
        )

        evidence_refs = extraction.evidence_references or build_evidence_references(images)

        # Step 2: Handle Fail-Open Scenarios (timeout, unconfigured, network/model error)
        if extraction.status != "success" or extraction.observation is None:
            fail_reason = extraction.error_message or f"Vision extraction failed ({extraction.status})"
            
            # Construct honest, unverified fallback observation (all damage UNCERTAIN)
            fallback_obs = VisualObservation(
                carton_damage=DamageType.UNCERTAIN,
                unit_damage=DamageType.UNCERTAIN,
                image_clarity=None,
            )

            # Route individual checks to UNCERTAIN with explicit fail-open explanation
            pending_checks = IndividualChecks(
                identity_check=CheckResult(
                    verdict=CheckVerdict.UNCERTAIN,
                    reason=f"Identity unverified due to vision extraction issue: {fail_reason}",
                ),
                quantity_check=CheckResult(
                    verdict=CheckVerdict.UNCERTAIN,
                    reason=f"Count unverified due to vision extraction issue: {fail_reason}",
                ),
                carton_condition_check=CheckResult(
                    verdict=CheckVerdict.UNCERTAIN,
                    damage_type="uncertain",
                    reason=f"Carton condition unverified: {fail_reason}",
                ),
                unit_condition_check=CheckResult(
                    verdict=CheckVerdict.UNCERTAIN,
                    damage_type="uncertain",
                    reason=f"Unit condition unverified: {fail_open_status(extraction.status)}",
                ),
                specification_check=CheckResult(
                    verdict=CheckVerdict.UNCERTAIN,
                    flagged_issues=[],
                    reason=f"Specification unverified: {fail_reason}",
                ),
            )

            return EvidenceRecord(
                record_id=record_id,
                unit_id=unit_id,
                org_id=org_id,
                operator_id=operator_id,
                captured_at=captured_time,
                po_header=po_header,
                expected_values=expected,
                observed_values=fallback_obs,
                individual_checks=pending_checks,
                final_verdict=FinalVerdict.PENDING_REVIEW,
                verdict_reason=f"Shipment placed in PENDING_REVIEW: {fail_reason}. Photos preserved for dock review.",
                evidence_references=evidence_refs,
                operator_override=None,
            )

        # Step 3: Pure Deterministic Verification on Extracted Observations
        individual_checks, final_verdict, verdict_reason = evaluate_all_checks(
            expected=expected,
            observation=extraction.observation,
        )

        # Step 4: Construct and Return Final Evidence Record
        return EvidenceRecord(
            record_id=record_id,
            unit_id=unit_id,
            org_id=org_id,
            operator_id=operator_id,
            captured_at=captured_time,
            po_header=po_header,
            expected_values=expected,
            observed_values=extraction.observation,
            individual_checks=individual_checks,
            final_verdict=final_verdict,
            verdict_reason=verdict_reason,
            evidence_references=evidence_refs,
            operator_override=None,
        )


def fail_open_status(status: str) -> str:
    if status == "timeout":
        return "Provider timeout (>30s)"
    elif status == "unconfigured":
        return "Vision provider credentials missing"
    elif status == "invalid_json":
        return "Non-conforming model output"
    return "Extraction pipeline exception"

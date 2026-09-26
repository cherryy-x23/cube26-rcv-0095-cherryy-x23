"""
Deterministic Comparison Engine for CUBE Receiving Manager (Pod 01)
Phase 1: Pure deterministic verification logic with zero model dependencies.

Guiding Principle:
- Vision AI is restricted to observational extraction (OCR, counts, classifications).
- Deterministic logic performs strict arithmetic, contract matching, and verdict routing.
- UNCERTAIN is treated as a first-class result and is never converted to a weak PASS.
"""

from typing import Tuple, List
from .models import (
    POExpected,
    VisualObservation,
    CheckResult,
    CheckVerdict,
    FinalVerdict,
    DamageType,
    IndividualChecks,
)


def compare_identity(expected: POExpected, observation: VisualObservation) -> CheckResult:
    """
    Compares physical goods identity against the PO expected line item.
    Checks identified SKU, barcode/FNSKU/UPC, and OCR text against PO expected values.
    """
    # If no identity evidence exists in the observation
    if not observation.identified_sku and not observation.barcode and not observation.ocr_text:
        return CheckResult(
            verdict=CheckVerdict.UNCERTAIN,
            reason="Identity evidence missing or unreadable in captured photos.",
            confidence=0.0,
        )

    # 1. Direct SKU match
    if observation.identified_sku:
        if observation.identified_sku.strip().upper() == expected.sku.strip().upper():
            return CheckResult(
                verdict=CheckVerdict.PASS,
                reason=f"Observed SKU '{observation.identified_sku}' matches expected SKU '{expected.sku}'.",
                confidence=1.0,
            )
        else:
            return CheckResult(
                verdict=CheckVerdict.FAIL,
                reason=f"SKU mismatch: expected '{expected.sku}', observed '{observation.identified_sku}'.",
                confidence=1.0,
            )

    # 2. Barcode match against ASIN or SKU
    if observation.barcode:
        b_clean = observation.barcode.strip().upper()
        if b_clean == expected.asin.strip().upper() or b_clean == expected.sku.strip().upper():
            return CheckResult(
                verdict=CheckVerdict.PASS,
                reason=f"Observed barcode '{observation.barcode}' matches expected identifier.",
                confidence=0.95,
            )
        # If barcode is clearly an entirely different SKU/ASIN
        if b_clean.startswith("SKU-") or b_clean.startswith("B0"):
            return CheckResult(
                verdict=CheckVerdict.FAIL,
                reason=f"Observed barcode '{observation.barcode}' does not match expected SKU '{expected.sku}' or ASIN '{expected.asin}'.",
                confidence=0.95,
            )

    # 3. Fallback to OCR text search
    if observation.ocr_text:
        ocr_upper = observation.ocr_text.upper()
        if expected.sku.upper() in ocr_upper:
            return CheckResult(
                verdict=CheckVerdict.PASS,
                reason=f"Expected SKU '{expected.sku}' identified within carton OCR text.",
                confidence=0.90,
            )
        if expected.asin.upper() in ocr_upper:
            return CheckResult(
                verdict=CheckVerdict.PASS,
                reason=f"Expected ASIN '{expected.asin}' identified within carton OCR text.",
                confidence=0.90,
            )

    return CheckResult(
        verdict=CheckVerdict.UNCERTAIN,
        reason="Visible text and markings did not conclusively confirm or reject expected SKU.",
        confidence=0.4,
    )


def compare_carton_count(expected: POExpected, observation: VisualObservation) -> CheckResult:
    """
    Compares master carton count delivered vs master cartons ordered.
    """
    if observation.cartons_counted is None:
        return CheckResult(
            verdict=CheckVerdict.UNCERTAIN,
            reason="Carton count observation is missing or occluded in pallet photos.",
        )

    discrepancy = observation.cartons_counted - expected.cartons_ordered
    if discrepancy == 0:
        return CheckResult(
            verdict=CheckVerdict.PASS,
            discrepancy=0,
            reason=f"Carton count matches expected: {expected.cartons_ordered} cartons.",
        )
    elif discrepancy < 0:
        return CheckResult(
            verdict=CheckVerdict.FAIL,
            discrepancy=discrepancy,
            reason=f"Short carton delivery: expected {expected.cartons_ordered} cartons, observed {observation.cartons_counted} (shortage of {abs(discrepancy)} cartons).",
        )
    else:
        return CheckResult(
            verdict=CheckVerdict.FAIL,
            discrepancy=discrepancy,
            reason=f"Extra carton delivery: expected {expected.cartons_ordered} cartons, observed {observation.cartons_counted} (overage of {discrepancy} cartons).",
        )


def compare_units_per_carton(expected: POExpected, observation: VisualObservation) -> CheckResult:
    """
    Compares packaging density: units per master carton vs specification.
    """
    if observation.units_per_carton_counted is None:
        return CheckResult(
            verdict=CheckVerdict.UNCERTAIN,
            reason="Units-per-carton observation is missing or internal carton uninspected.",
        )

    discrepancy = observation.units_per_carton_counted - expected.units_per_carton_ordered
    if discrepancy == 0:
        return CheckResult(
            verdict=CheckVerdict.PASS,
            discrepancy=0,
            reason=f"Units per carton matches expected: {expected.units_per_carton_ordered} units/carton.",
        )
    elif discrepancy < 0:
        return CheckResult(
            verdict=CheckVerdict.FAIL,
            discrepancy=discrepancy,
            reason=f"Underfilled master carton: expected {expected.units_per_carton_ordered} units/carton, observed {observation.units_per_carton_counted} (deficit of {abs(discrepancy)} units/carton).",
        )
    else:
        return CheckResult(
            verdict=CheckVerdict.FAIL,
            discrepancy=discrepancy,
            reason=f"Overfilled master carton: expected {expected.units_per_carton_ordered} units/carton, observed {observation.units_per_carton_counted} (overage of {discrepancy} units/carton).",
        )


def compare_total_quantity(expected: POExpected, observation: VisualObservation) -> CheckResult:
    """
    Compares total unit count delivered against quantity ordered on PO.
    Uses direct unit count or calculates (cartons_counted * units_per_carton_counted).
    """
    if observation.quantity_counted is not None:
        total_counted = observation.quantity_counted
    elif observation.cartons_counted is not None and observation.units_per_carton_counted is not None:
        total_counted = observation.cartons_counted * observation.units_per_carton_counted
    else:
        return CheckResult(
            verdict=CheckVerdict.UNCERTAIN,
            reason="Insufficient count evidence to determine total quantity received.",
        )

    discrepancy = total_counted - expected.quantity_ordered
    if discrepancy == 0:
        return CheckResult(
            verdict=CheckVerdict.PASS,
            discrepancy=0,
            reason=f"Total quantity matches expected: {expected.quantity_ordered} units.",
        )
    elif discrepancy < 0:
        return CheckResult(
            verdict=CheckVerdict.FAIL,
            discrepancy=discrepancy,
            reason=f"Short shipment: Expected {expected.quantity_ordered} units but observed {total_counted} units (shortage of {abs(discrepancy)} units).",
        )
    else:
        return CheckResult(
            verdict=CheckVerdict.FAIL,
            discrepancy=discrepancy,
            reason=f"Over-shipment: Expected {expected.quantity_ordered} units but observed {total_counted} units (overage of {discrepancy} extra units).",
        )


def evaluate_carton_damage(observation: VisualObservation) -> CheckResult:
    """
    Evaluates master shipping carton condition.
    """
    if observation.carton_damage == DamageType.UNCERTAIN:
        return CheckResult(
            verdict=CheckVerdict.UNCERTAIN,
            damage_type="uncertain",
            reason="Carton condition cannot be reliably verified from available photos.",
        )
    elif observation.carton_damage == DamageType.NONE:
        return CheckResult(
            verdict=CheckVerdict.PASS,
            damage_type="none",
            reason="No carton damage detected; structural integrity verified.",
        )
    else:
        return CheckResult(
            verdict=CheckVerdict.FAIL,
            damage_type=observation.carton_damage.value,
            reason=f"Carton damage detected: {observation.carton_damage.value}.",
        )


def evaluate_unit_damage(observation: VisualObservation) -> CheckResult:
    """
    Evaluates sellable unit retail packaging condition.
    """
    if observation.unit_damage == DamageType.UNCERTAIN:
        return CheckResult(
            verdict=CheckVerdict.UNCERTAIN,
            damage_type="uncertain",
            reason="Unit condition cannot be reliably verified from available photos.",
        )
    elif observation.unit_damage == DamageType.NONE:
        return CheckResult(
            verdict=CheckVerdict.PASS,
            damage_type="none",
            reason="No unit damage detected; retail packaging intact.",
        )
    else:
        return CheckResult(
            verdict=CheckVerdict.FAIL,
            damage_type=observation.unit_damage.value,
            reason=f"Unit packaging damage detected: {observation.unit_damage.value}.",
        )


def compare_colour(expected: POExpected, observation: VisualObservation) -> Tuple[CheckVerdict, str]:
    if not expected.expected_colour or expected.expected_colour.strip().lower() in ["n/a", "none"]:
        return CheckVerdict.PASS, "No color constraint in specification."
    if not observation.observed_colour:
        return CheckVerdict.UNCERTAIN, "Observed color not available in observation."
    if observation.observed_colour.strip().lower() == expected.expected_colour.strip().lower():
        return CheckVerdict.PASS, f"Color matches specification ({expected.expected_colour})."
    return CheckVerdict.FAIL, f"Color mismatch: expected '{expected.expected_colour}', observed '{observation.observed_colour}'."


def compare_variant(expected: POExpected, observation: VisualObservation) -> Tuple[CheckVerdict, str]:
    if not expected.expected_variant or expected.expected_variant.strip().lower() in ["n/a", "standard"]:
        return CheckVerdict.PASS, "Standard variant specification; no constraint."
    if not observation.observed_variant:
        return CheckVerdict.UNCERTAIN, "Observed variant not available in observation."
    if observation.observed_variant.strip().lower() == expected.expected_variant.strip().lower():
        return CheckVerdict.PASS, f"Variant matches specification ({expected.expected_variant})."
    return CheckVerdict.FAIL, f"Variant mismatch: expected '{expected.expected_variant}', observed '{observation.observed_variant}'."


def compare_components(expected: POExpected, observation: VisualObservation) -> Tuple[CheckVerdict, List[str], str]:
    if not expected.expected_components:
        return CheckVerdict.PASS, [], "No individual components mandated by spec."
    if observation.observed_components is None:
        return CheckVerdict.UNCERTAIN, [], "Component presence cannot be verified from observation."

    observed_lower = [c.strip().lower() for c in observation.observed_components]
    missing = []
    for req in expected.expected_components:
        req_clean = req.strip().lower()
        if not any(req_clean in obs for obs in observed_lower):
            missing.append(req)

    if missing:
        flags = [f"missing_{m.replace(' ', '_')}" for m in missing]
        return CheckVerdict.FAIL, flags, f"Missing expected components: {', '.join(missing)}."
    return CheckVerdict.PASS, [], "All expected components confirmed present."


def evaluate_specification(expected: POExpected, observation: VisualObservation) -> CheckResult:
    """
    Evaluates color, variant, and component conformity against PO spec.
    """
    flagged_issues: List[str] = []
    reasons: List[str] = []
    verdicts: List[CheckVerdict] = []

    # Colour check
    c_verdict, c_msg = compare_colour(expected, observation)
    verdicts.append(c_verdict)
    if c_verdict == CheckVerdict.FAIL:
        flagged_issues.append("wrong_colour")
        reasons.append(c_msg)
    elif c_verdict == CheckVerdict.UNCERTAIN:
        reasons.append(c_msg)

    # Variant check
    v_verdict, v_msg = compare_variant(expected, observation)
    verdicts.append(v_verdict)
    if v_verdict == CheckVerdict.FAIL:
        flagged_issues.append("wrong_variant")
        reasons.append(v_msg)
    elif v_verdict == CheckVerdict.UNCERTAIN:
        reasons.append(v_msg)

    # Component check
    comp_verdict, comp_flags, comp_msg = compare_components(expected, observation)
    verdicts.append(comp_verdict)
    if comp_verdict == CheckVerdict.FAIL:
        flagged_issues.extend(comp_flags)
        reasons.append(comp_msg)
    elif comp_verdict == CheckVerdict.UNCERTAIN:
        reasons.append(comp_msg)

    # Aggregate spec verdict
    if CheckVerdict.FAIL in verdicts:
        final_spec_verdict = CheckVerdict.FAIL
        summary_reason = "; ".join(reasons)
    elif CheckVerdict.UNCERTAIN in verdicts:
        final_spec_verdict = CheckVerdict.UNCERTAIN
        summary_reason = "; ".join(reasons)
    else:
        final_spec_verdict = CheckVerdict.PASS
        summary_reason = "All specification attributes (colour, variant, components) match contractual specs."

    return CheckResult(
        verdict=final_spec_verdict,
        flagged_issues=flagged_issues,
        reason=summary_reason,
    )


def evaluate_all_checks(expected: POExpected, observation: VisualObservation) -> Tuple[IndividualChecks, FinalVerdict, str]:
    """
    Runs all 5 core receiving checks deterministically and synthesizes the overall verdict.
    
    Overall Verdict Rules:
    - If ANY check is FAIL -> FinalVerdict.FAIL
    - Else if ANY check is UNCERTAIN -> FinalVerdict.UNCERTAIN
    - Else (all checks PASS) -> FinalVerdict.PASS
    """
    id_check = compare_identity(expected, observation)
    qty_check = compare_total_quantity(expected, observation)
    carton_check = evaluate_carton_damage(observation)
    unit_check = evaluate_unit_damage(observation)
    spec_check = evaluate_specification(expected, observation)

    individual = IndividualChecks(
        identity_check=id_check,
        quantity_check=qty_check,
        carton_condition_check=carton_check,
        unit_condition_check=unit_check,
        specification_check=spec_check,
    )

    all_verdicts = [
        id_check.verdict,
        qty_check.verdict,
        carton_check.verdict,
        unit_check.verdict,
        spec_check.verdict,
    ]

    failed_reasons = []
    uncertain_reasons = []

    if id_check.verdict == CheckVerdict.FAIL:
        failed_reasons.append(f"Identity: {id_check.reason}")
    elif id_check.verdict == CheckVerdict.UNCERTAIN:
        uncertain_reasons.append(f"Identity: {id_check.reason}")

    if qty_check.verdict == CheckVerdict.FAIL:
        failed_reasons.append(f"Quantity: {qty_check.reason}")
    elif qty_check.verdict == CheckVerdict.UNCERTAIN:
        uncertain_reasons.append(f"Quantity: {qty_check.reason}")

    if carton_check.verdict == CheckVerdict.FAIL:
        failed_reasons.append(f"Carton: {carton_check.reason}")
    elif carton_check.verdict == CheckVerdict.UNCERTAIN:
        uncertain_reasons.append(f"Carton: {carton_check.reason}")

    if unit_check.verdict == CheckVerdict.FAIL:
        failed_reasons.append(f"Unit: {unit_check.reason}")
    elif unit_check.verdict == CheckVerdict.UNCERTAIN:
        uncertain_reasons.append(f"Unit: {unit_check.reason}")

    if spec_check.verdict == CheckVerdict.FAIL:
        failed_reasons.append(f"Spec: {spec_check.reason}")
    elif spec_check.verdict == CheckVerdict.UNCERTAIN:
        uncertain_reasons.append(f"Spec: {spec_check.reason}")

    if CheckVerdict.FAIL in all_verdicts:
        final_verdict = FinalVerdict.FAIL
        verdict_reason = "Inspection FAILED. " + "; ".join(failed_reasons)
    elif CheckVerdict.UNCERTAIN in all_verdicts:
        final_verdict = FinalVerdict.UNCERTAIN
        verdict_reason = "Inspection UNCERTAIN (requires manual dock review). " + "; ".join(uncertain_reasons)
    else:
        final_verdict = FinalVerdict.PASS
        verdict_reason = "All inbound checks PASSED. Goods match purchase order and quality specifications without visible damage."

    return individual, final_verdict, verdict_reason

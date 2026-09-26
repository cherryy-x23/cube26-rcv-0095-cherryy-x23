"""
Unit & Integration Tests for Headless Receiving Agent (Phase 2)
Covers mock vision extraction, fail-open resilience, and single-batch invocation verification.
Compatible with pytest and python -m unittest.
"""

import sys
import unittest
from pathlib import Path

agent_root = Path(__file__).resolve().parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

from core.models import (
    DamageType,
    FinalVerdict,
    POExpected,
    POHeader,
    ViewType,
    VisualObservation,
)
from core.vision_extractor import MockVisionExtractor
from core.agent import ReceivingAgent


class TestHeadlessReceivingAgent(unittest.TestCase):
    def setUp(self):
        self.po_header = POHeader(
            po_number="PO-7001",
            po_line=1,
            supplier="Supplier East (DUMMY)",
        )
        self.expected = POExpected(
            sku="SKU-PROT-1KG",
            asin="B0DUMMY357",
            product_title="Whey Protein Vanilla",
            expected_colour="n/a",
            expected_variant="1kg vanilla",
            expected_components=["tub", "scoop"],
            cartons_ordered=2,
            units_per_carton_ordered=12,
            quantity_ordered=24,
        )
        self.sample_images = {
            ViewType.PALLET: "fixtures/receiving/UNIT-0004_pallet.jpg",
            ViewType.CARTON: "fixtures/receiving/UNIT-0004_carton.jpg",
            ViewType.UNIT: "fixtures/receiving/UNIT-0004_unit.jpg",
        }

    # Test 1: Mock vision returns matching evidence -> PASS
    def test_01_matching_evidence_pass(self):
        obs = VisualObservation(
            identified_sku="SKU-PROT-1KG",
            barcode="B0DUMMY357",
            cartons_counted=2,
            units_per_carton_counted=12,
            quantity_counted=24,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
            observed_variant="1kg vanilla",
            observed_components=["tub", "scoop"],
            image_clarity=0.98,
        )
        agent = ReceivingAgent(extractor=MockVisionExtractor(preset_observation=obs))
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.PASS)
        self.assertIn("All inbound checks PASSED", record.verdict_reason)

    # Test 2: Mock vision returns short shipment -> FAIL
    def test_02_short_shipment_fail(self):
        obs = VisualObservation(
            identified_sku="SKU-PROT-1KG",
            cartons_counted=2,
            units_per_carton_counted=10,  # 20 instead of 24
            quantity_counted=20,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
            observed_variant="1kg vanilla",
            observed_components=["tub", "scoop"],
        )
        agent = ReceivingAgent(extractor=MockVisionExtractor(preset_observation=obs))
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.FAIL)
        self.assertEqual(record.individual_checks.quantity_check.discrepancy, -4)
        self.assertIn("short shipment", record.verdict_reason.lower())

    # Test 3: Mock vision returns wrong SKU -> FAIL
    def test_03_wrong_sku_fail(self):
        obs = VisualObservation(
            identified_sku="SKU-WRONG-ITEM",
            cartons_counted=2,
            units_per_carton_counted=12,
            quantity_counted=24,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
            observed_variant="1kg vanilla",
            observed_components=["tub", "scoop"],
        )
        agent = ReceivingAgent(extractor=MockVisionExtractor(preset_observation=obs))
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.FAIL)
        self.assertIn("SKU mismatch", record.individual_checks.identity_check.reason)

    # Test 4: Mock vision returns uncertain SKU -> UNCERTAIN
    def test_04_uncertain_sku(self):
        obs = VisualObservation(
            identified_sku=None,
            barcode=None,
            ocr_text=None,
            cartons_counted=2,
            units_per_carton_counted=12,
            quantity_counted=24,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
            observed_variant="1kg vanilla",
            observed_components=["tub", "scoop"],
        )
        agent = ReceivingAgent(extractor=MockVisionExtractor(preset_observation=obs))
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.UNCERTAIN)
        self.assertIn("Identity: Identity evidence missing", record.verdict_reason)

    # Test 5: Mock vision returns carton crushing -> FAIL
    def test_05_carton_crushing_fail(self):
        obs = VisualObservation(
            identified_sku="SKU-PROT-1KG",
            cartons_counted=2,
            units_per_carton_counted=12,
            quantity_counted=24,
            carton_damage=DamageType.CRUSHING,
            unit_damage=DamageType.NONE,
            observed_variant="1kg vanilla",
            observed_components=["tub", "scoop"],
        )
        agent = ReceivingAgent(extractor=MockVisionExtractor(preset_observation=obs))
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.FAIL)
        self.assertEqual(record.individual_checks.carton_condition_check.damage_type, "crushing")

    # Test 6: Mock vision returns unclear damage -> UNCERTAIN
    def test_06_unclear_damage_uncertain(self):
        obs = VisualObservation(
            identified_sku="SKU-PROT-1KG",
            cartons_counted=2,
            units_per_carton_counted=12,
            quantity_counted=24,
            carton_damage=DamageType.UNCERTAIN,
            unit_damage=DamageType.UNCERTAIN,
            observed_variant="1kg vanilla",
            observed_components=["tub", "scoop"],
        )
        agent = ReceivingAgent(extractor=MockVisionExtractor(preset_observation=obs))
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.UNCERTAIN)
        self.assertIn("UNCERTAIN", record.final_verdict.value)

    # Test 7: Mock vision returns wrong variant -> FAIL
    def test_07_wrong_variant_fail(self):
        obs = VisualObservation(
            identified_sku="SKU-PROT-1KG",
            cartons_counted=2,
            units_per_carton_counted=12,
            quantity_counted=24,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
            observed_variant="500g chocolate",  # expected 1kg vanilla
            observed_components=["tub", "scoop"],
        )
        agent = ReceivingAgent(extractor=MockVisionExtractor(preset_observation=obs))
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.FAIL)
        self.assertIn("wrong_variant", record.individual_checks.specification_check.flagged_issues)

    # Test 8: Mock vision returns missing component -> FAIL
    def test_08_missing_component_fail(self):
        obs = VisualObservation(
            identified_sku="SKU-PROT-1KG",
            cartons_counted=2,
            units_per_carton_counted=12,
            quantity_counted=24,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
            observed_variant="1kg vanilla",
            observed_components=["tub"],  # missing scoop
        )
        agent = ReceivingAgent(extractor=MockVisionExtractor(preset_observation=obs))
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.FAIL)
        self.assertIn("missing_scoop", record.individual_checks.specification_check.flagged_issues)

    # Test 9: Vision provider timeout -> PENDING_REVIEW & no fabricated observation
    def test_09_provider_timeout_pending_review(self):
        extractor = MockVisionExtractor(simulate_timeout=True, error_message="Upstream API Gateway 504 Timeout")
        agent = ReceivingAgent(extractor=extractor)
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.PENDING_REVIEW)
        self.assertIn("PENDING_REVIEW", record.verdict_reason)
        self.assertIn("Timeout", record.verdict_reason)
        # Ensure no fabricated observation was emitted
        self.assertIsNone(record.observed_values.quantity_counted)
        self.assertEqual(record.observed_values.carton_damage, DamageType.UNCERTAIN)

    # Test 10: Invalid provider JSON -> PENDING_REVIEW
    def test_10_invalid_provider_json_pending_review(self):
        extractor = MockVisionExtractor(simulate_invalid_json=True)
        agent = ReceivingAgent(extractor=extractor)
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )
        self.assertEqual(record.final_verdict, FinalVerdict.PENDING_REVIEW)
        self.assertIn("JSON", record.verdict_reason)

    # Test 11: Single Batch Invocations Proof (1 receiving unit = exactly 1 model call)
    def test_11_single_batch_invocation_proof(self):
        extractor = MockVisionExtractor()
        agent = ReceivingAgent(extractor=extractor)
        
        # Verify initial call count is 0
        self.assertEqual(extractor.call_count, 0)

        # Process single shipment which runs 5 checks (Identity, Qty, Carton, Unit, Spec)
        record = agent.process_shipment(
            record_id="RCV-0004",
            unit_id="UNIT-0004",
            org_id="org_demo_alpha",
            operator_id="op_amira",
            po_header=self.po_header,
            expected=self.expected,
            images=self.sample_images,
        )

        # Verify that all 5 individual checks were performed
        self.assertIsNotNone(record.individual_checks.identity_check)
        self.assertIsNotNone(record.individual_checks.quantity_check)
        self.assertIsNotNone(record.individual_checks.carton_condition_check)
        self.assertIsNotNone(record.individual_checks.unit_condition_check)
        self.assertIsNotNone(record.individual_checks.specification_check)

        # CRITICAL TEST: Must be exactly ONE vision extractor call, NOT 5 calls!
        self.assertEqual(
            extractor.call_count,
            1,
            f"Expected exactly 1 batched model invocation for the unit, but observed {extractor.call_count} calls!",
        )


if __name__ == "__main__":
    unittest.main()

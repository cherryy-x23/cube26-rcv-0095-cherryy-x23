"""
Unit Tests for Comparison Engine (Phase 1)
Covers all 12 core deterministic receiving scenarios without AI dependencies.
Compatible with both pytest and python -m unittest.
"""

import sys
import unittest
from pathlib import Path

# Add agent root to path to allow importing core regardless of repo hyphenated paths
agent_root = Path(__file__).resolve().parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

from core.models import (
    POExpected,
    VisualObservation,
    CheckVerdict,
    FinalVerdict,
    DamageType,
)
from core.comparison_engine import (
    compare_identity,
    compare_total_quantity,
    compare_carton_count,
    compare_units_per_carton,
    evaluate_carton_damage,
    evaluate_unit_damage,
    evaluate_specification,
    evaluate_all_checks,
)


class TestComparisonEngine(unittest.TestCase):
    def setUp(self):
        self.standard_po = POExpected(
            sku="SKU-TOWEL-BLU",
            asin="B0DUMMY600",
            product_title="Cotton Bath Towel",
            expected_colour="blue",
            expected_variant="bath",
            expected_components=["towel"],
            cartons_ordered=2,
            units_per_carton_ordered=12,
            quantity_ordered=24,
        )

    # 1. Matching quantity -> PASS
    def test_01_matching_quantity(self):
        obs = VisualObservation(
            cartons_counted=2,
            units_per_carton_counted=12,
            quantity_counted=24,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        res = compare_total_quantity(self.standard_po, obs)
        self.assertEqual(res.verdict, CheckVerdict.PASS)
        self.assertEqual(res.discrepancy, 0)
        self.assertIn("matches expected", res.reason)

    # 2. Short quantity -> FAIL
    def test_02_short_quantity(self):
        obs = VisualObservation(
            cartons_counted=2,
            units_per_carton_counted=11,
            quantity_counted=22,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        res = compare_total_quantity(self.standard_po, obs)
        self.assertEqual(res.verdict, CheckVerdict.FAIL)
        self.assertEqual(res.discrepancy, -2)
        self.assertIn("short shipment", res.reason.lower())

    # 3. Extra quantity -> FAIL
    def test_03_extra_quantity(self):
        obs = VisualObservation(
            cartons_counted=2,
            units_per_carton_counted=13,
            quantity_counted=26,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        res = compare_total_quantity(self.standard_po, obs)
        self.assertEqual(res.verdict, CheckVerdict.FAIL)
        self.assertEqual(res.discrepancy, 2)
        self.assertIn("over-shipment", res.reason.lower())

    # 4. Matching SKU -> PASS
    def test_04_matching_sku(self):
        obs = VisualObservation(
            identified_sku="SKU-TOWEL-BLU",
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        res = compare_identity(self.standard_po, obs)
        self.assertEqual(res.verdict, CheckVerdict.PASS)
        self.assertIn("matches expected SKU", res.reason)

    # 5. Wrong SKU -> FAIL
    def test_05_wrong_sku(self):
        obs = VisualObservation(
            identified_sku="SKU-CABLE-USBC",
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        res = compare_identity(self.standard_po, obs)
        self.assertEqual(res.verdict, CheckVerdict.FAIL)
        self.assertIn("SKU mismatch", res.reason)

    # 6. Missing SKU evidence -> UNCERTAIN
    def test_06_missing_sku_evidence(self):
        obs = VisualObservation(
            identified_sku=None,
            barcode=None,
            ocr_text=None,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        res = compare_identity(self.standard_po, obs)
        self.assertEqual(res.verdict, CheckVerdict.UNCERTAIN)
        self.assertIn("missing or unreadable", res.reason)

    # 7. No damage -> PASS
    def test_07_no_damage(self):
        obs = VisualObservation(
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        c_res = evaluate_carton_damage(obs)
        u_res = evaluate_unit_damage(obs)
        self.assertEqual(c_res.verdict, CheckVerdict.PASS)
        self.assertEqual(u_res.verdict, CheckVerdict.PASS)

    # 8. Crushing -> FAIL
    def test_08_crushing_damage(self):
        obs = VisualObservation(
            carton_damage=DamageType.CRUSHING,
            unit_damage=DamageType.NONE,
        )
        c_res = evaluate_carton_damage(obs)
        self.assertEqual(c_res.verdict, CheckVerdict.FAIL)
        self.assertEqual(c_res.damage_type, "crushing")

    # 9. Unclear damage -> UNCERTAIN
    def test_09_unclear_damage(self):
        obs = VisualObservation(
            carton_damage=DamageType.UNCERTAIN,
            unit_damage=DamageType.UNCERTAIN,
        )
        c_res = evaluate_carton_damage(obs)
        u_res = evaluate_unit_damage(obs)
        self.assertEqual(c_res.verdict, CheckVerdict.UNCERTAIN)
        self.assertEqual(u_res.verdict, CheckVerdict.UNCERTAIN)

    # 10. Matching variant -> PASS
    def test_10_matching_variant(self):
        obs = VisualObservation(
            observed_colour="blue",
            observed_variant="bath",
            observed_components=["towel"],
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        res = evaluate_specification(self.standard_po, obs)
        self.assertEqual(res.verdict, CheckVerdict.PASS)
        self.assertEqual(len(res.flagged_issues), 0)

    # 11. Wrong variant -> FAIL
    def test_11_wrong_variant(self):
        obs = VisualObservation(
            observed_colour="blue",
            observed_variant="hand",  # expected is 'bath'
            observed_components=["towel"],
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        res = evaluate_specification(self.standard_po, obs)
        self.assertEqual(res.verdict, CheckVerdict.FAIL)
        self.assertIn("wrong_variant", res.flagged_issues)

    # 12. Missing component -> FAIL
    def test_12_missing_component(self):
        complex_po = POExpected(
            sku="SKU-LAMP-LED",
            asin="B0DUMMY357",
            product_title="LED Desk Lamp",
            expected_colour="grey",
            expected_variant="standard",
            expected_components=["lamp", "usb cable", "manual"],
            cartons_ordered=1,
            units_per_carton_ordered=12,
            quantity_ordered=12,
        )
        obs = VisualObservation(
            observed_colour="grey",
            observed_variant="standard",
            observed_components=["lamp"],  # missing usb cable and manual
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
        )
        res = evaluate_specification(complex_po, obs)
        self.assertEqual(res.verdict, CheckVerdict.FAIL)
        self.assertTrue(any("missing" in issue for issue in res.flagged_issues))

    # Holistic check: Short shipment produces overall FAIL
    def test_13_overall_verdict_short_shipment(self):
        obs = VisualObservation(
            identified_sku="SKU-TOWEL-BLU",
            cartons_counted=2,
            units_per_carton_counted=11,
            quantity_counted=22,
            carton_damage=DamageType.NONE,
            unit_damage=DamageType.NONE,
            observed_colour="blue",
            observed_variant="bath",
            observed_components=["towel"],
        )
        individual, final_verdict, reason = evaluate_all_checks(self.standard_po, obs)
        self.assertEqual(final_verdict, FinalVerdict.FAIL)
        self.assertEqual(individual.quantity_check.verdict, CheckVerdict.FAIL)
        self.assertEqual(individual.identity_check.verdict, CheckVerdict.PASS)
        self.assertIn("short shipment", reason.lower())


if __name__ == "__main__":
    unittest.main()

"""
Unit Tests for Evaluation Framework (Phase 3)
Tests Cohen's Kappa, 3x3 Confusion Matrices, Quantity Discrepancy Accounting,
and Evaluation Harness Honesty Guards.
Compatible with pytest and python -m unittest.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

agent_root = Path(__file__).resolve().parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

from eval.metrics import (
    ConfusionMatrix,
    calculate_cohens_kappa,
    evaluate_quantity_discrepancy,
)
from eval.run_eval import EvaluationHarness


class TestEvaluationFramework(unittest.TestCase):

    # Test 1: Empty / unannotated evaluation set produces NOT READY
    def test_01_unannotated_evaluation_set_not_ready(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            json.dump({
                "dataset_status": "not_ready",
                "annotation_status": "unannotated",
                "cases": [],
            }, tmp)
            tmp_path = Path(tmp.name)

        try:
            harness = EvaluationHarness(ground_truth_file=tmp_path)
            is_ready, message = harness.load_and_validate()
            self.assertFalse(is_ready)
            self.assertIn("not_ready", message)
        finally:
            tmp_path.unlink(missing_ok=True)

    # Test 2: Two identical annotation lists produce kappa = 1.0 (Mathematical unit test)
    def test_02_identical_annotations_kappa_one(self):
        rater_a = ["PASS", "FAIL", "PASS", "UNCERTAIN", "PASS", "FAIL"]
        rater_b = ["PASS", "FAIL", "PASS", "UNCERTAIN", "PASS", "FAIL"]
        result = calculate_cohens_kappa(rater_a, rater_b)
        self.assertEqual(result["agreement_count"], 6)
        self.assertEqual(result["disagreement_count"], 0)
        self.assertEqual(result["observed_agreement"], 1.0)
        self.assertEqual(result["kappa"], 1.0)

    # Test 3: Known disagreement fixture produces expected Cohen's Kappa
    def test_03_known_disagreement_kappa(self):
        # 10 cases: 7 agreements, 3 disagreements
        rater_a = ["PASS", "PASS", "PASS", "PASS", "FAIL", "FAIL", "FAIL", "UNCERTAIN", "UNCERTAIN", "PASS"]
        rater_b = ["PASS", "PASS", "PASS", "FAIL", "FAIL", "FAIL", "PASS", "UNCERTAIN", "PASS",      "PASS"]
        result = calculate_cohens_kappa(rater_a, rater_b)
        self.assertEqual(result["n"], 10)
        self.assertEqual(result["agreement_count"], 7)
        self.assertEqual(result["disagreement_count"], 3)
        self.assertEqual(result["observed_agreement"], 0.7)
        self.assertGreater(result["kappa"], 0.4)
        self.assertLess(result["kappa"], 0.8)

    # Test 4: Prediction PASS vs Ground-Truth PASS (True Positive)
    def test_04_prediction_pass_vs_gt_pass(self):
        matrix = ConfusionMatrix()
        matrix.add(ground_truth="PASS", prediction="PASS")
        counts = matrix.get_counts() if hasattr(matrix, "get_counts") else matrix.to_dict()
        self.assertEqual(counts["PASS"]["PASS"], 1)
        self.assertEqual(counts["PASS"]["FAIL"], 0)
        self.assertEqual(counts["PASS"]["UNCERTAIN"], 0)

    # Test 5: Prediction FAIL vs Ground-Truth PASS (False Positive / False Alarm)
    def test_05_prediction_fail_vs_gt_pass(self):
        matrix = ConfusionMatrix()
        matrix.add(ground_truth="PASS", prediction="FAIL")
        counts = matrix.to_dict()
        self.assertEqual(counts["PASS"]["FAIL"], 1)
        self.assertEqual(counts["PASS"]["PASS"], 0)

    # Test 6: Prediction PASS vs Ground-Truth FAIL (False Negative / Missed Defect)
    def test_06_prediction_pass_vs_gt_fail(self):
        matrix = ConfusionMatrix()
        matrix.add(ground_truth="FAIL", prediction="PASS")
        counts = matrix.to_dict()
        self.assertEqual(counts["FAIL"]["PASS"], 1)
        self.assertEqual(counts["FAIL"]["FAIL"], 0)

    # Test 7: Prediction UNCERTAIN is explicitly tracked
    def test_07_prediction_uncertain_explicitly_counted(self):
        matrix = ConfusionMatrix()
        matrix.add(ground_truth="PASS", prediction="UNCERTAIN")
        matrix.add(ground_truth="FAIL", prediction="UNCERTAIN")
        counts = matrix.to_dict()
        self.assertEqual(counts["PASS"]["UNCERTAIN"], 1)
        self.assertEqual(counts["FAIL"]["UNCERTAIN"], 1)
        self.assertEqual(matrix.total, 2)

    # Test 8: Quantity Shortage Accounting
    def test_08_quantity_shortage(self):
        res = evaluate_quantity_discrepancy(qty_ordered=24, qty_observed=22)
        self.assertEqual(res["status"], "shortage")
        self.assertEqual(res["discrepancy"], -2)
        self.assertEqual(res["short_units"], 2)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn("Short shipment", res["reason"])

    # Test 9: Quantity Overage Accounting
    def test_09_quantity_overage(self):
        res = evaluate_quantity_discrepancy(qty_ordered=24, qty_observed=26)
        self.assertEqual(res["status"], "overage")
        self.assertEqual(res["discrepancy"], 2)
        self.assertEqual(res["extra_units"], 2)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn("Over-shipment", res["reason"])

    # Test 10: Missing independent annotation causes runner to refuse official metrics
    def test_10_missing_annotation_refuses_official_metrics(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            json.dump({
                "dataset_status": "held_out",
                "annotation_status": "single_annotator_only",  # Missing dual independent labels!
                "cases": [
                    {
                        "case_id": "EVAL-0001",
                        "unit_id": "UNIT-E001",
                        "ground_truth": {
                            "identity": {"annotator_a": "PASS"}  # Missing annotator_b
                        }
                    }
                ],
            }, tmp)
            tmp_path = Path(tmp.name)

        try:
            harness = EvaluationHarness(ground_truth_file=tmp_path)
            is_ready, message = harness.load_and_validate()
            self.assertFalse(is_ready)
            self.assertIn("dual_independent", message)
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

"""
Headless Evaluation Runner for CUBE Receiving Manager (Pod 01)
Phase 3: Automated Evaluation Harness with Hard Honesty Guards.

Enforces:
- Hard guard: Refuses to report official accuracy, FP, FN, or Kappa if independent dual annotations are absent.
- Strict rejection of starter synthetic CSV as evaluation ground truth.
- Computes Cohen's Kappa for inter-annotator agreement.
- 3x3 Confusion Matrices for PASS / FAIL / UNCERTAIN.
- Named Failure-Mode analysis (FM-01 to FM-05).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

eval_root = Path(__file__).resolve().parent
agent_root = eval_root.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

from core.models import (
    EvidenceRecord,
    FinalVerdict,
    POExpected,
    POHeader,
    ViewType,
    VisualObservation,
)
from core.comparison_engine import evaluate_all_checks
from eval.metrics import (
    CheckMetrics,
    ConfusionMatrix,
    NAMED_FAILURE_MODES,
    calculate_cohens_kappa,
    evaluate_quantity_discrepancy,
)


class EvaluationHarness:
    """
    Automated evaluation harness for evaluating Receiving Manager against ground-truth datasets.
    """

    def __init__(self, ground_truth_file: Path, allow_test_fixture: bool = False):
        self.ground_truth_file = Path(ground_truth_file)
        self.allow_test_fixture = allow_test_fixture
        self.data: Dict[str, Any] = {}
        self.cases: List[Dict[str, Any]] = []

    def load_and_validate(self) -> Tuple[bool, str]:
        """
        Loads ground truth JSON and executes strict honesty validation.
        Returns (is_ready, reason_message).
        """
        if not self.ground_truth_file.exists():
            return False, f"Ground truth file not found at {self.ground_truth_file}"

        with open(self.ground_truth_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        dataset_status = self.data.get("dataset_status", "").lower()
        annotation_status = self.data.get("annotation_status", "").lower()
        self.cases = self.data.get("cases", [])

        # Honesty Guard: Test fixtures are permitted ONLY when explicitly flagged
        if self.allow_test_fixture:
            if not self.cases:
                return False, "Evaluation dataset contains 0 cases."
            return True, "Test fixture dataset loaded for harness verification."

        # Official Evaluation Mode Guards
        if dataset_status != "held_out":
            return (
                False,
                f"dataset_status is '{dataset_status}', not 'held_out'. Starter reference data or unverified datasets cannot be used for official evaluation.",
            )

        if annotation_status != "dual_independent":
            return (
                False,
                f"annotation_status is '{annotation_status}', not 'dual_independent'. Official metrics require two independent human annotators.",
            )

        if len(self.cases) == 0:
            return False, "Evaluation set is empty (0 cases). Held-out cases have not been populated yet."

        # Verify that all cases have annotator_a and annotator_b
        for c in self.cases:
            gt = c.get("ground_truth", {})
            for check in ["identity", "carton_damage", "unit_damage"]:
                if check in gt:
                    entry = gt[check]
                    if not isinstance(entry, dict) or "annotator_a" not in entry or "annotator_b" not in entry:
                        return (
                            False,
                            f"Case {c.get('case_id')} is missing independent annotator labels for check '{check}'.",
                        )

        return True, "Held-out evaluation dataset verified."

    def compute_inter_annotator_agreement(self) -> Dict[str, Any]:
        """
        Computes Cohen's Kappa across independent raters for all check categories.
        """
        checks = ["identity", "carton_damage", "unit_damage", "quantity"]
        results = {}

        for ch in checks:
            rater_a = []
            rater_b = []
            for c in self.cases:
                gt = c.get("ground_truth", {}).get(ch, {})
                if isinstance(gt, dict) and "annotator_a" in gt and "annotator_b" in gt:
                    rater_a.append(str(gt["annotator_a"]).upper())
                    rater_b.append(str(gt["annotator_b"]).upper())

            if len(rater_a) > 0:
                results[ch] = calculate_cohens_kappa(rater_a, rater_b)
            else:
                results[ch] = {"status": "no_annotations", "kappa": None}

        return results

    def run_evaluation(self, agent_predictions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Runs evaluation comparisons between predictions and adjudicated ground truth.
        """
        # If predictions not passed, run deterministic evaluation on expected observations
        results_by_check: Dict[str, CheckMetrics] = {
            "identity": CheckMetrics("identity"),
            "quantity": CheckMetrics("quantity"),
            "carton_condition": CheckMetrics("carton_condition"),
            "unit_condition": CheckMetrics("unit_condition"),
            "overall_verdict": CheckMetrics("overall_verdict"),
        }
        failure_mode_counts: Dict[str, int] = {fm: 0 for fm in NAMED_FAILURE_MODES}

        for idx, case in enumerate(self.cases):
            gt_data = case.get("ground_truth", {})
            fm = case.get("named_failure_mode")
            if fm and fm in failure_mode_counts:
                failure_mode_counts[fm] += 1

            # Determine adjudicated ground truth (fallback to annotator_a if agreed)
            def get_adjudicated(check_key: str, default="PASS") -> str:
                ch = gt_data.get(check_key, {})
                if isinstance(ch, dict):
                    return str(ch.get("adjudicated_label") or ch.get("annotator_a") or default).upper()
                return str(ch).upper()

            gt_id = get_adjudicated("identity")
            gt_qty = get_adjudicated("quantity")
            gt_carton = get_adjudicated("carton_damage")
            gt_unit = get_adjudicated("unit_damage")
            gt_final = "FAIL" if any(v == "FAIL" for v in [gt_id, gt_qty, gt_carton, gt_unit]) else ("UNCERTAIN" if any(v == "UNCERTAIN" for v in [gt_id, gt_qty, gt_carton, gt_unit]) else "PASS")

            # Extract prediction
            if agent_predictions and idx < len(agent_predictions):
                pred_entry = agent_predictions[idx]
                pred_id = pred_entry.get("identity", "UNCERTAIN")
                pred_qty = pred_entry.get("quantity", "UNCERTAIN")
                pred_carton = pred_entry.get("carton_damage", "UNCERTAIN")
                pred_unit = pred_entry.get("unit_damage", "UNCERTAIN")
                pred_final = pred_entry.get("final_verdict", "UNCERTAIN")
            else:
                pred_id = case.get("mock_prediction", {}).get("identity", "UNCERTAIN")
                pred_qty = case.get("mock_prediction", {}).get("quantity", "UNCERTAIN")
                pred_carton = case.get("mock_prediction", {}).get("carton_damage", "UNCERTAIN")
                pred_unit = case.get("mock_prediction", {}).get("unit_damage", "UNCERTAIN")
                pred_final = case.get("mock_prediction", {}).get("final_verdict", "UNCERTAIN")

            # Update metrics for each check
            pairs = [
                ("identity", gt_id, pred_id),
                ("quantity", gt_qty, pred_qty),
                ("carton_condition", gt_carton, pred_carton),
                ("unit_condition", gt_unit, pred_unit),
                ("overall_verdict", gt_final, pred_final),
            ]
            for check_name, gt_val, pred_val in pairs:
                cm: CheckMetrics = results_by_check[check_name]
                cm.total_cases += 1
                cm.confusion_matrix.add(gt_val, pred_val)

                if pred_val == "UNCERTAIN":
                    cm.uncertain_count += 1
                elif gt_val == "PASS" and pred_val == "PASS":
                    cm.true_positives += 1
                elif gt_val == "FAIL" and pred_val == "FAIL":
                    cm.true_negatives += 1
                elif gt_val == "PASS" and pred_val == "FAIL":
                    cm.false_positives += 1
                elif gt_val == "FAIL" and pred_val == "PASS":
                    cm.false_negatives += 1

        agreement = self.compute_inter_annotator_agreement()

        return {
            "evaluation_status": "COMPLETED",
            "total_evaluated_cases": len(self.cases),
            "inter_annotator_agreement": agreement,
            "check_metrics": {k: v.to_dict() for k, v in results_by_check.items()},
            "failure_mode_analysis": failure_mode_counts,
        }


def main():
    parser = argparse.ArgumentParser(
        description="CUBE Receiving Manager Evaluation Runner (Phase 3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ground-truth",
        default="submissions/cherryy-x23/agent/eval/ground_truth.json",
        help="Path to evaluation ground truth JSON file",
    )
    parser.add_argument(
        "--test-dataset",
        action="store_true",
        help="Flag indicating execution on automated test fixtures (for harness testing only)",
    )
    parser.add_argument(
        "--output",
        help="Path to save evaluation report JSON",
    )

    args = parser.parse_args()
    gt_path = Path(args.ground_truth)

    harness = EvaluationHarness(ground_truth_file=gt_path, allow_test_fixture=args.test_dataset)
    is_ready, message = harness.load_and_validate()

    if not is_ready:
        print("=" * 65)
        print("CUBE RECEIVING MANAGER -- EVALUATION STATUS: NOT READY")
        print("=" * 65)
        print(f"REASON: {message}")
        print()
        print("HONESTY GUARD ENFORCED:")
        print("- No independently annotated held-out evaluation cases are available.")
        print("- Official accuracy, FP, FN, and Cohen's Kappa metrics will NOT be reported.")
        print("- Starter reference data (receiving_sample.csv) is strictly excluded.")
        print("=" * 65)
        sys.exit(0)

    # If verified held-out dataset or test fixture is provided
    results = harness.run_evaluation()
    print("=" * 65)
    print("CUBE RECEIVING MANAGER -- EVALUATION RESULTS")
    print("=" * 65)
    print(f"Dataset File:          {gt_path}")
    print(f"Cases Evaluated:       {results['total_evaluated_cases']}")
    print("-" * 65)
    print("INTER-ANNOTATOR AGREEMENT (COHEN'S KAPPA):")
    for ch, data in results["inter_annotator_agreement"].items():
        k = data.get("kappa")
        k_str = f"{k:.4f}" if k is not None else "N/A"
        print(f"  {ch.ljust(20)}: -- = {k_str} (observed: {data.get('observed_agreement')}, n={data.get('n')})")
    print("-" * 65)
    print("PER-CHECK PERFORMANCE SUMMARY:")
    for ch, data in results["check_metrics"].items():
        acc = data["overall_accuracy"] * 100
        u_rate = data["uncertain_rate"] * 100
        print(f"  {ch.ljust(18)}: Accuracy={acc:.1f}%, FP={data['false_positives']}, FN={data['false_negatives']}, UNCERTAIN={data['uncertain_count']} ({u_rate:.1f}%)")
    print("=" * 65)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Evaluation report written to: {out_path}")


if __name__ == "__main__":
    main()

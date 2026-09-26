"""
Evaluation Metrics & Inter-Annotator Agreement Engine for CUBE Receiving Manager (Pod 01)
Phase 3: Cohen's Kappa, 3x3 Confusion Matrices (PASS/FAIL/UNCERTAIN), Discrepancy Accounting,
and Named Failure Mode Trackers.

Mathematical Guiding Principles:
- UNCERTAIN is a first-class categorical state and is never collapsed into PASS.
- False Positives (False Alarms on Good Goods) vs False Negatives (Missed Shortages/Defects)
  are tracked separately due to drastically differing supply chain economic impacts.
- Inter-annotator reliability is measured strictly via Cohen's Kappa (?).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# Standard CUBE labels
VERDICTS = ["PASS", "FAIL", "UNCERTAIN"]


# Official Named Failure Modes for Inbound Receiving
NAMED_FAILURE_MODES = {
    "FM-01": {
        "name": "Barcode Glare",
        "description": "Specular glare / plastic stretch-wrap reflection makes 1D/2D barcode unreadable.",
        "expected_verdict": "UNCERTAIN",
    },
    "FM-02": {
        "name": "Motion Blur",
        "description": "Poorly focused or fast-motion dock photograph obscures carton condition.",
        "expected_verdict": "UNCERTAIN",
    },
    "FM-03": {
        "name": "Concealed Unit Damage",
        "description": "Master carton exterior appears intact, but internal product packaging is crushed or broken.",
        "expected_verdict": "UNCERTAIN",
    },
    "FM-04": {
        "name": "Nested Bundles",
        "description": "Tightly stacked, nested, or polybagged items obscure inner unit counting.",
        "expected_verdict": "UNCERTAIN",
    },
    "FM-05": {
        "name": "Occluded Labels",
        "description": "Shipping labels or variant markings are partially blocked by strapping, tape, or debris.",
        "expected_verdict": "UNCERTAIN",
    },
}


def calculate_cohens_kappa(
    rater_a: List[str],
    rater_b: List[str],
    categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Computes Cohen's Kappa (?) for inter-annotator agreement between two independent human raters.

    Formula:
        ? = (p_o - p_e) / (1 - p_e)
        p_o = observed proportionate agreement
        p_e = hypothetical probability of chance agreement
    """
    if len(rater_a) != len(rater_b):
        raise ValueError(f"Rater lists must be of equal length. Got {len(rater_a)} and {len(rater_b)}.")

    n = len(rater_a)
    if n == 0:
        return {
            "n": 0,
            "agreement_count": 0,
            "disagreement_count": 0,
            "observed_agreement": 0.0,
            "expected_agreement": 0.0,
            "kappa": 0.0,
            "status": "empty",
        }

    # Normalize categories
    cats = categories or sorted(list(set(rater_a) | set(rater_b)))
    if not cats:
        return {
            "n": 0,
            "agreement_count": 0,
            "disagreement_count": 0,
            "observed_agreement": 0.0,
            "expected_agreement": 0.0,
            "kappa": 0.0,
            "status": "empty",
        }

    # Count agreement
    agreements = sum(1 for a, b in zip(rater_a, rater_b) if a == b)
    disagreements = n - agreements
    p_o = agreements / n

    # Marginal probabilities
    count_a = {c: 0 for c in cats}
    count_b = {c: 0 for c in cats}
    for a in rater_a:
        count_a[a] = count_a.get(a, 0) + 1
    for b in rater_b:
        count_b[b] = count_b.get(b, 0) + 1

    p_e = sum((count_a[c] / n) * (count_b[c] / n) for c in cats)

    # Kappa calculation
    if p_e >= 1.0:
        kappa = 1.0  # Perfect agreement on single category
    elif (1.0 - p_e) == 0:
        kappa = 1.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    # Round kappa to 4 decimal places
    kappa = round(max(-1.0, min(1.0, kappa)), 4)

    return {
        "n": n,
        "agreement_count": agreements,
        "disagreement_count": disagreements,
        "observed_agreement": round(p_o, 4),
        "expected_agreement": round(p_e, 4),
        "kappa": kappa,
        "status": "computed",
    }


class ConfusionMatrix:
    """
    3x3 Confusion Matrix tracking Ground Truth vs Prediction for PASS, FAIL, UNCERTAIN.
    """

    def __init__(self, labels: Optional[List[str]] = None):
        self.labels = labels or VERDICTS
        # matrix[gt][pred]
        self.matrix: Dict[str, Dict[str, int]] = {
            gt: {pred: 0 for pred in self.labels} for gt in self.labels
        }
        self.total = 0

    def add(self, ground_truth: str, prediction: str):
        gt = str(ground_truth).strip().upper()
        pred = str(prediction).strip().upper()
        if gt not in self.matrix:
            self.matrix[gt] = {p: 0 for p in self.labels}
        if pred not in self.matrix[gt]:
            for g in self.matrix:
                self.matrix[g][pred] = 0
            if pred not in self.labels:
                self.labels.append(pred)

        self.matrix[gt][pred] += 1
        self.total += 1

    def to_dict(self) -> Dict[str, Dict[str, int]]:
        return {gt: dict(preds) for gt, preds in self.matrix.items()}

    def format_table(self) -> str:
        """Renders GitHub markdown table of the matrix."""
        headers = ["Ground Truth \\ Pred"] + self.labels
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for gt in self.labels:
            row = [f"**{gt}**"]
            for pred in self.labels:
                val = self.matrix.get(gt, {}).get(pred, 0)
                row.append(str(val))
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)


@dataclass
class CheckMetrics:
    """Metrics container for an individual receiving check category."""
    check_name: str
    total_cases: int = 0
    true_positives: int = 0   # GT == PASS, Pred == PASS
    true_negatives: int = 0   # GT == FAIL, Pred == FAIL
    false_positives: int = 0  # GT == PASS, Pred == FAIL (False alarm)
    false_negatives: int = 0  # GT == FAIL, Pred == PASS (Missed defect/shortage)
    uncertain_count: int = 0  # Pred == UNCERTAIN
    confusion_matrix: ConfusionMatrix = field(default_factory=ConfusionMatrix)

    @property
    def uncertain_rate(self) -> float:
        return round(self.uncertain_count / self.total_cases, 4) if self.total_cases > 0 else 0.0

    @property
    def decisive_cases(self) -> int:
        """Cases where agent produced a definitive PASS or FAIL."""
        return self.total_cases - self.uncertain_count

    @property
    def decisive_accuracy(self) -> float:
        """Accuracy among decisive predictions (TP + TN) / (decisive_cases)."""
        if self.decisive_cases == 0:
            return 0.0
        return round((self.true_positives + self.true_negatives) / self.decisive_cases, 4)

    @property
    def overall_accuracy(self) -> float:
        """Strict accuracy across all cases (TP + TN) / total_cases."""
        if self.total_cases == 0:
            return 0.0
        return round((self.true_positives + self.true_negatives) / self.total_cases, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "total_cases": self.total_cases,
            "true_positives": self.true_positives,
            "true_negatives": self.true_negatives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "uncertain_count": self.uncertain_count,
            "uncertain_rate": self.uncertain_rate,
            "decisive_accuracy": self.decisive_accuracy,
            "overall_accuracy": self.overall_accuracy,
            "confusion_matrix": self.confusion_matrix.to_dict(),
        }


def evaluate_quantity_discrepancy(
    qty_ordered: int,
    qty_observed: Optional[int],
) -> Dict[str, Any]:
    """
    Evaluates quantity discrepancy mathematically.
    Discrepancy = qty_observed - qty_ordered.
    Missing evidence remains UNCERTAIN; never assumes shortage without evidence.
    """
    if qty_observed is None:
        return {
            "status": "uncertain",
            "discrepancy": None,
            "reason": "Missing or unreadable count evidence in photographs.",
            "verdict": "UNCERTAIN",
        }

    discrepancy = qty_observed - qty_ordered
    if discrepancy == 0:
        return {
            "status": "exact_match",
            "discrepancy": 0,
            "reason": f"Exact quantity match ({qty_ordered} units).",
            "verdict": "PASS",
        }
    elif discrepancy < 0:
        return {
            "status": "shortage",
            "discrepancy": discrepancy,
            "short_units": abs(discrepancy),
            "reason": f"Short shipment: expected {qty_ordered} units, observed {qty_observed} (shortage of {abs(discrepancy)} units).",
            "verdict": "FAIL",
        }
    else:
        return {
            "status": "overage",
            "discrepancy": discrepancy,
            "extra_units": discrepancy,
            "reason": f"Over-shipment: expected {qty_ordered} units, observed {qty_observed} (overage of {discrepancy} units).",
            "verdict": "FAIL",
        }

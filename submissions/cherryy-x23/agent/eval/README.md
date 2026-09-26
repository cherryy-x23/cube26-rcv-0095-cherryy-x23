# Evaluation Framework ? 01 Receiving Manager

## Overview & Architecture
The CUBE Receiving Manager Evaluation Framework provides an automated, mathematically rigorous benchmark for testing shipment verification performance against independent, dual-annotated ground truth.

```text
Held-Out Receiving Fixtures (50 Units) + Independent Dual Ground Truth
                               ?
                               ?
                        Receiving Agent
                               ?
                               ?
                          Predictions
                               ?
                               ?
                  Automated Evaluation Harness
                               ?
       ?????????????????????????????????????????????????
       ?                                               ?
Inter-Annotator Reliability                     Per-Check Performance
(Cohen's Kappa ?)                               (Accuracy, FP, FN, UNCERTAIN)
                                                       ?
                                                       ?
                                            3x3 Confusion Matrices
                                                       ?
                                                       ?
                                            Named Failure Modes (FM-01..05)
```

---

## Inviolable Data & Honesty Rules

1. **Starter CSV Exclusion:** `data/receiving_sample.csv` contains synthetic reference data only. It is **never** used for model evaluation, training, or accuracy claims.
2. **Honesty Guards Enforced:** The evaluation runner (`run_eval.py`) verifies:
   - `dataset_status == "held_out"`
   - `annotation_status == "dual_independent"`
   If either condition is unmet, the runner halts and refuses to report official accuracy or Cohen's Kappa.
3. **No Collapsing UNCERTAIN:** `UNCERTAIN` is treated as a distinct, first-class categorical prediction across all metrics and confusion matrices.
4. **Asymmetric Error Penalties:**
   - **False Negatives (Missed Defects/Shortages):** Severe financial penalty (unsubstantiated supplier disputes, customer returns).
   - **False Positives (False Alarms):** Operational delay / friction (unnecessary secondary manual inspections).

---

## Inter-Annotator Agreement: Cohen's Kappa ($\kappa$)

To ensure ground-truth labels are not the subjective bias of a single observer, two independent human raters annotate all cases. Inter-rater reliability is measured using Cohen's Kappa:

$$\kappa = rac{p_o - p_e}{1 - p_e}$$

- $p_o$: Observed proportionate agreement between Annotator A and Annotator B.
- $p_e$: Probability of random agreement based on marginal frequencies.
- If annotators disagree, an operational lead adjudicates the case, recording both the consensus label (`adjudicated_label`) and the rationale (`adjudication_reason`).

---

## 3x3 Confusion Matrix Specification

For each check (`identity`, `quantity`, `carton_condition`, `unit_condition`, `overall_verdict`), performance is evaluated via a $3 \times 3$ matrix:

| Ground Truth \ Pred | PASS | FAIL | UNCERTAIN |
|---|:---:|:---:|:---:|
| **PASS** | True Positive (Clean) | False Positive (False Alarm) | Deferred (Healthy Caution) |
| **FAIL** | False Negative (Missed Defect) | True Negative (Caught Defect) | Deferred (Triage Escalation) |
| **UNCERTAIN** | Speculative Pass | Speculative Fail | True Uncertain |

---

## Named Failure Modes Tracked

| Code | Failure Mode | Trigger / Physical Context | Expected System Outcome |
|---|---|---|---|
| **FM-01** | Barcode Glare | Specular reflections on shrink wrap obscure 1D/2D barcode | `UNCERTAIN` |
| **FM-02** | Motion Blur | Operator movement / low dock lighting blurs carton edge | `UNCERTAIN` |
| **FM-03** | Concealed Damage | Carton exterior intact, but inner retail goods broken | `UNCERTAIN` (Unit) |
| **FM-04** | Nested Bundles | Tightly stacked polybags prevent direct unit counting | `UNCERTAIN` (Count) |
| **FM-05** | Occluded Labels | Shipping labels partially covered by tape or banding | `UNCERTAIN` (Identity) |

---

## Running the Evaluation Harness

### 1. Official Evaluation (Enforces Honesty Guard)
```bash
python submissions/cherryy-x23/agent/eval/run_eval.py
```
*Current output:* Safely reports `EVALUATION STATUS: NOT READY` until real dual-annotated fixtures are supplied.

### 2. Running Automated Unit Tests
```bash
python -m unittest submissions/cherryy-x23/agent/tests/test_evaluation.py -v
```

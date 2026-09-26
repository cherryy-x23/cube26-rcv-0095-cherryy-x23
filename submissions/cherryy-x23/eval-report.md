# Evaluation Report ? 01 Receiving Manager

## A. Implemented Evaluation Infrastructure

In accordance with Phase 3 of the CUBE Buildathon, a production-grade, automated evaluation framework has been implemented in `submissions/cherryy-x23/agent/eval/`:

1. **Held-Out Dataset Contract & Schema:**
   - Formal JSON schema supporting multi-view photographic evidence (`pallet`, `carton`, `unit`, `barcode`).
   - Independent dual-annotator ground truth (`annotator_a` and `annotator_b`) covering `identity`, `quantity`, `carton_damage`, `unit_damage`, and `quality_flags`.
   - Adjudication metadata (`adjudicated_label` and `adjudication_reason`) for resolving inter-rater disagreements.
2. **Inter-Annotator Agreement Engine (`metrics.py`):**
   - Implements Cohen's Kappa ($\kappa$) calculation:
     $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
   - Quantifies human labeling reliability and flags ambiguous evaluation samples before model benchmarking.
3. **3x3 Confusion Matrix Engine (`metrics.py`):**
   - Tracks predictions against ground truth across all three first-class outcomes: `PASS`, `FAIL`, and `UNCERTAIN`.
   - Never collapses or drops `UNCERTAIN`.
4. **Asymmetric Error Accounting:**
   - Differentiates **False Negatives** (missed shortages/damage, highest operational cost) from **False Positives** (false alarms on good inventory).
   - Dedicated quantity discrepancy tracker ($Discrepancy = Qty_{observed} - Qty_{ordered}$).
5. **Named Failure-Mode Classification:**
   - Integrated taxonomy covering:
     - `FM-01`: Barcode Glare (reflective shrink wrap)
     - `FM-02`: Motion Blur (poor camera focus/motion)
     - `FM-03`: Concealed Unit Damage (intact carton, damaged contents)
     - `FM-04`: Nested Bundles (polybagged units obscuring counts)
     - `FM-05`: Occluded Labels (strapping/tape covering SKU text)
6. **Automated Runner with Hard Honesty Guards (`run_eval.py`):**
   - Refuses to report official metrics unless `dataset_status == "held_out"` and `annotation_status == "dual_independent"`.
   - Excludes starter reference data (`data/receiving_sample.csv`).

---

## B. Current Evaluation Status

> **HONESTY & INTEGRITY NOTICE:**  
> **Metrics: NOT YET AVAILABLE**  
> **Reason:** The independent 50-unit held-out dataset and physical dual-human annotations are not yet available.  
> 
> Per CUBE Buildathon engineering rules:
> - Zero evaluation accuracies, Cohen's Kappa scores, or confusion matrices have been fabricated.
> - The reference dataset (`data/receiving_sample.csv`) has **not** been used as ground truth.
> - The evaluation harness is fully built, tested, and waiting for the physical held-out dataset.

---

## C. Planned Evaluation Protocol (Target Benchmark)

When the 50 physical evaluation units are captured and annotated, the evaluation harness will execute the following benchmark:

### 1. Dataset Composition (50 Unseen Units)
- **15 Clean Units:** Flawless master cartons, matching quantities, and intact units (`PASS`).
- **7 Short Shipments:** Missing master cartons or carton count deficits (`FAIL`).
- **3 Overages:** Unmanifested extra cartons or overfilled boxes (`FAIL`).
- **5 SKU / ASIN Mismatches:** Incorrect product or substituted barcode (`FAIL`).
- **4 Variant Mismatches:** Wrong volume, pack size, or specification (`FAIL`).
- **3 Color Discrepancies:** Incorrect color variant delivered (`FAIL`).
- **5 Carton Damage:** Crushed corners, tears, or water damage (`FAIL`).
- **3 Unit Damage:** Dented retail cans, cracked plastic, broken seals (`FAIL`).
- **3 Missing Components:** Missing essential accessories (`FAIL`).
- **2 Extreme Ambiguity:** Heavy glare, partial occlusions, motion blur (`UNCERTAIN`).

### 2. Dual Annotator Protocol
- Annotators A and B independently review each unit's photos without consulting each other.
- Cases where Annotator A $\ne$ Annotator B are submitted to an operational warehouse lead for consensus adjudication.
- Cohen's Kappa is reported for all check categories. Target inter-annotator agreement: $\kappa \ge 0.85$.

### 3. Planned Performance Reporting Table (Template)

| Check Category | Cases | True Pos (PASS) | True Neg (FAIL) | False Pos (False Alarm) | False Neg (Missed Defect) | UNCERTAIN Rate | Accuracy |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Identity Verification** | 50 | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *TBD* |
| **Quantity Verification** | 50 | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *TBD* |
| **Carton Condition** | 50 | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *TBD* |
| **Unit Condition** | 50 | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *TBD* |
| **Specification Compliance**| 50 | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *TBD* |
| **OVERALL SHIPMENT VERDICT**| **50** | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *Pending Phase 3 Data* | *TBD* |

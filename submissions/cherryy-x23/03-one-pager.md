# Executive One-Pager ? 01 Receiving Manager

## Product Summary
**Receiving Manager** is the foundational gatekeeper of the physical supply chain. Stationed at inbound warehouse receiving docks, it verifies supplier deliveries against purchase orders in real-time, recording condition on arrival and producing an immutable, cross-pod **Evidence Record** (`RCV-XXXX`) keyed to `unit_id`.

---

## Target Metrics Framework (Measured on Held-Out Test Set)

| Metric | Target Standard | Evaluation Method | Current Status (Phase 6) |
|---|---|---|---|
| **Identity Verification Accuracy** | $\ge 98.0\%$ | Exact match against known SKU/ASIN ground truth | *Pending Real Held-Out Eval* |
| **Quantity Discrepancy Recall** | $\ge 95.0\%$ | Sensitivity in detecting short or over-shipments | *Pending Real Held-Out Eval* |
| **Damage Detection Precision** | $\ge 90.0\%$ | Carton crush, tear, moisture detection vs 2 annotators | *Pending Real Held-Out Eval* |
| **False-Pass Rate (Defect Miss)** | $\le 2.0\%$ | False negatives on damaged or short goods | *Pending Real Held-Out Eval* |
| **Uncertainty Rate** | $5.0\% - 10.0\%$ | Ambiguous/poor photos correctly routed to triage | *Pending Real Held-Out Eval* |
| **Deterministic Comparison Latency**| $< 50\text{ ms}$ | Computation time for 5 checks and verdict synthesis | **Passed (< 5 ms in unit tests)** |
| **Multi-Tenant Isolation** | $100\%$ zero-leak | Row-Level Security verification (Alpha vs Bravo) | **Passed (100% 404 isolation)** |

*Note: In accordance with CUBE Honesty Rules, all model accuracy metrics remain explicitly unpopulated until the 50-unit held-out test suite is executed with real physical photos and dual human annotators.*

---

## Architectural Principles
1. **AI Observes, Deterministic Code Decides:** Vision models extract raw observations (OCR, counts, classifications); deterministic Python logic conducts all comparisons and emits verdicts.
2. **First-Class Uncertainty:** Blurry or ambiguous evidence outputs `UNCERTAIN` and routes to `PENDING_REVIEW`.
3. **Fail-Open by Design:** Vision timeouts create `PENDING_REVIEW` placeholders without stalling the physical receiving dock line.
4. **Single-Batch Model Call:** A single multimodal API request processes all pallet, carton, and unit images simultaneously.

---

## Kill Condition
> **KILL CONDITION:**  
> If the vision model exhibits a **False-Pass rate greater than 5.0% on severe damage or shortage cases** (failing to catch crushed cartons, water damage, or under-shipments) OR if the **Uncertainty rate exceeds 30.0% under standard warehouse lighting**, the automated verdict pipeline will be suspended and all shipments will default to mandatory manual operator inspection.

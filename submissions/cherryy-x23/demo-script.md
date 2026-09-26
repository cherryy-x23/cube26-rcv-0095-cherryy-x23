# CUBE Buildathon RCV#1 — Live Jury Demo Script

**Project:** Receiving Manager — Verify what actually arrived  
**Team Fork:** `cube26-rcv-0095-cherryy-x23`  
**Duration:** 3–5 Minutes  
**Target Audience:** CUBE Buildathon Jury, Warehouse Operations Engineers, and Logistics Tech Evaluators  

---

## Pre-Demo Checklist (30 seconds before presenting)

1. **Terminal 1 (Backend):**
   ```cmd
   cd submissions\cherryy-x23
   python -m uvicorn app.main:app --app-dir backend --port 8000
   ```
2. **Terminal 2 (Frontend):**
   ```cmd
   cd submissions\cherryy-x23\frontend
   npm run dev
   ```
3. Open browser to: `http://localhost:5173`
4. Click **"Reset"** then **"⚡ [DEMO] Seed 4 Scenarios"** on the Dashboard (or run `python scripts/seed_demo_scenarios.py`).

---

## Timed Walkthrough

### 0:00–0:30 — The Problem

> *"Good morning/afternoon, judges. Every warehouse dock faces the same high-velocity vulnerability: **receiving verification**.*
>
> *When a shipment arrives at the inbound dock, warehouse teams must verify whether physical inventory actually matches what was purchased in the PO. Did 24 units arrive or only 22? Is the carton crushed? Did the supplier ship the wrong variant?*
>
> *Today, dock workers manually inspect cartons under severe time pressure, leading to undetected shortages, inventory record drift, and chargeback disputes. Traditional computer vision tries to prompt an LLM to decide 'Pass or Fail', leading to hallucinations, silent approvals of damaged cartons, and pipeline crashes when APIs time out.*
>
> *Our solution is **Receiving Manager**: deterministic verification powered by structured multimodal visual evidence."*

---

### 0:30–1:00 — Architecture & Core Design Principle

*(Point to the architecture diagram in the UI or slides)*

> *"Our core design principle is: **Vision AI is an evidence extractor, NOT a judge.**
>
> 1. Inbound PO expectations and dock photos are assembled.
> 2. We execute **exactly ONE batched Vision AI call per receiving unit** to prevent token explosion and latency.
> 3. The Vision extractor outputs a strict, validated `VisualObservation` schema (counts, detected barcodes, carton condition, unit defects).
> 4. A **deterministic comparison engine written in pure Python** compares observed values against PO specifications.
> 5. The engine produces a definitive verdict: `PASS`, `FAIL`, or `UNCERTAIN`—backed by an immutable, JSON-Schema-compliant `EvidenceRecord`.
> 6. If the AI model fails or times out, the system **fails open** into `PENDING_REVIEW`—the dock is never blocked."*

---

### 1:00–1:45 — Scenario 1: Clean Pass (`DEMO-PASS-001`)

*(Navigate to Dashboard → click on `DEMO-PASS-001` or create from preset "1. Clean Pass")*

> *"Let's look at Scenario 1: A clean, compliant shipment.
>
> * **PO Expected:** SKU `BLUE-BOTTLE-001`, Quantity `24`, Variant `Blue/Standard`, Clean cartons.
> * **Visual Evidence:** Clean pallet, intact master cartons, intact bottles.
> * **Result:** Notice the clean green `PASS` verdict hero.
> * **Expected vs Observed Panel:** 
>   * SKU: Expected `BLUE-BOTTLE-001` → Observed `BLUE-BOTTLE-001` (Match)
>   * Quantity: Expected `24` → Observed `24` (Match)
>   * Carton Condition: Expected `clean` → Observed `clean`
> * **Individual Checks:** Identity check PASS, Quantity check PASS, Carton condition check PASS.
>
> Everything is verified deterministically without LLM ambiguity."*

---

### 1:45–2:30 — Scenario 2: Short Shipment & Damage (`DEMO-FAIL-001`)

*(Navigate back to Dashboard → click on `DEMO-FAIL-001`)*

> *"Now let's examine Scenario 2: Defective inbound delivery.
>
> * **PO Expected:** Quantity `24`, Clean master cartons.
> * **Physical Dock Observation:** Only `22` units counted, and master carton shows structural crushing.
> * **Result:** Clear red `FAIL` badge.
> * Look at the **Discrepancy Breakdown**:
>   * Identity: `PASS` (SKU matches)
>   * Quantity Check: `FAIL` — Ordered 24, observed 22. Discrepancy: `-2 units`.
>   * Carton Condition Check: `FAIL` — Structural crushing detected.
> * The system immediately flags this for dock supervisor review and supplier chargeback before the freight carrier leaves the yard."*

---

### 2:30–3:00 — Scenario 3: Explicit Uncertainty (`DEMO-UNCERTAIN-001`)

*(Navigate to Dashboard → click on `DEMO-UNCERTAIN-001`)*

> *"A critical failure mode in warehouse AI is 'guessing'. What happens if barcode labels are obscured by glare, lighting is poor, or carton integrity cannot be confirmed?
>
> * In Scenario 3, the vision model returns low clarity and ambiguous OCR confidence.
> * **Result:** Yellow `UNCERTAIN` verdict.
> * **Crucial rule:** The system **never silently converts uncertainty into PASS or FAIL**.
> * The UI flags: `'Vision observations were ambiguous or photo evidence was insufficient.'`
> * It instructs the operator to perform a physical spot-check or capture clearer photos. This protects inventory accuracy from false confidences."*

---

### 3:00–3:30 — Scenario 4: Fail-Open Resilience (`DEMO-PENDING-001`)

*(Navigate to Dashboard → click on `DEMO-PENDING-001`)*

> *"What happens if Gemini or Claude times out, returns HTTP 503, or returns malformed JSON?
>
> * In traditional systems, receiving halts or unhandled 500 exceptions occur.
> * In Receiving Manager, we implement **Fail-Open Architecture**:
>   * Status transitions to `pending_review`.
>   * Verdict is `PENDING_REVIEW`.
>   * Dock photos and PO references are **safely persisted**.
>   * The operator is notified: `'AI vision analysis failed (provider error). Dock operation fails open to manual operator review.'`
> * The warehouse workflow never stops. Physical receiving continues uninterrupted."*

---

### 3:30–4:00 — Structured Evidence & Operator Override

*(On any inspection page, scroll down to Evidence & Override)*

> *"Notice two critical operational features:
>
> 1. **Structured Evidence Record:**
>    Every inspection produces a schema-validated `EvidenceRecord` tracking timestamp, SHA-256 photo references, exact discrepancies, and check-by-check evaluations for ERP audit trails.
>
> 2. **Operator Override Workflow:**
>    Human operators retain ultimate authority on the dock. If an operator recounts a shipment or accepts a damaged exterior because internal packaging was intact, they click **'Operator Override'**:
>    * They select a new verdict (e.g., `PASS`).
>    * They **must** enter an audit reason (e.g., `'Physical recount confirmed 24 units; exterior packaging damage did not affect goods'`).
>    * Both the original deterministic verdict and the override audit trail are permanently preserved."*

---

### 4:00–5:00 — Differentiators & Evaluation Rigor

> *"To summarize why Receiving Manager is built for real warehouse production:
>
> 1. **Single Batched Vision Call:** Exactly 1 API call per receiving unit instead of 5 separate prompts.
> 2. **Deterministic Comparison:** Pure Python rules engine. Zero LLM hallucinations in math or boolean logic.
> 3. **Fail-Open & Resilient:** Vision provider outages never block the physical receiving line.
> 4. **Multi-Tenant Scoping:** Inspections and overrides are strictly isolated by `X-Org-ID`.
> 5. **Truth in Evaluation:** We have built a complete evaluation harness measuring precision, recall, and Cohen's Kappa. However, in strict accordance with CUBE rules, because real-world receiving photos are not yet annotated, we declare: **Official evaluation metrics: NOT YET AVAILABLE**. We refuse to fabricate synthetic benchmarks or fake accuracy numbers.
>
> Thank you, and we welcome your questions!"*

---

## Quick Reference Q&A for Jury

| Question | Answer |
|---|---|
| *Why not let LLM decide PASS/FAIL directly?* | LLMs struggle with exact arithmetic (e.g., 22 vs 24 units), suffer from prompt drift, and can hallucinate compliance. The LLM is an extractor; deterministic code is the judge. |
| *How does multi-tenancy work?* | Every API request enforces `X-Org-ID` header. Cross-tenant inspections return HTTP 404/403. Tenant Alpha cannot see or override Tenant Beta's inspections. |
| *How does the system handle real photos?* | The `VisionExtractor` interface accepts file paths or URLs, computes SHA-256 hashes, and formats them into a single multimodal prompt for Gemini or mock providers. |

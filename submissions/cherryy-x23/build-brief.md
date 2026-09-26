# Build Brief ? 01 Receiving Manager

## 1. Problem
In physical e-commerce and retail supply chains, the inbound receiving dock is the single point where supplier liability is determined. Once pallets are received, de-palletized, and routed to prep or storage, suppliers routinely reject shortage or damage claims, arguing the fault occurred inside the merchant's warehouse or during 3PL transit.
Today, dock workers perform rushed spot-checks. Discrepancies (wrong variants, short carton counts, crushed units, moisture damage) surface weeks later when Amazon rejects inbound shipments or customers return units. By that time, the supplier dispute window is closed.

## 2. Target User
- **Inbound Warehouse Operators / Dock Receivers:** Need rapid, non-blocking visual verification tools that fit their scanning workflow.
- **Inventory & Operations Managers:** Need auditable proof of shortages and defects on arrival to initiate immediate supplier chargebacks before paying invoices.
- **Downstream CUBE Pods:**
  - *02 Prep Manager:* Checks compliance before applying labels.
  - *05 Recovery Manager:* Submits formal claims using the evidence record generated on arrival.

## 3. Architecture Overview
The Receiving Manager pipeline is structured as:
```text
Client / Future Frontend
            │
            ▼
   FastAPI REST Service (Phase 4 Implemented)
   [Row-Level Tenant Isolation via org_id]
            │
            ▼
   Inspection Service & Repository Abstraction
            │
            ▼
Purchase Order Line Item (Expected) + Physical Photos
            │
            ▼
ONE BATCHED MULTIMODAL VISION CALL (Phase 2 Implemented)
  [Extracts observations only: OCR, counts, damage, colors, clarity]
            │
            ▼
Structured VisualObservation
            │
            ▼
Deterministic Comparison Engine (Phase 1 Implemented)
  [Pure logic: arithmetic, string matches, thresholds]
            │
            ▼
Check Verdicts: PASS / FAIL / UNCERTAIN
            │
            ▼
Immutable Evidence Record (JSON Schema Draft 2020-12)
            │
            ├── Automated Evaluation Harness (Phase 3 Implemented)
            │     [Inter-annotator agreement (Cohen's Kappa κ), 3x3 matrices]
            │
            ▼
API Response + Operator Override Audit Trail
```

## 4. Single-Batch Invocation Architecture
At high-volume 3PL prep facilities processing thousands of units daily, making multiple sequential LLM calls per shipment unit (e.g. 1 call for SKU + 1 for quantity + 1 for damage + 1 for color) destroys gross margin and introduces unacceptable latency.
- The Receiving Manager enforces **exactly ONE model call per receiving unit**.
- The multimodal prompt packages all photos (pallet, carton, unit, barcode) and requests a single structured JSON response (`VisualObservation`).
- Unit test `test_11_single_batch_invocation_proof` confirms that `extractor.call_count == 1` across all 5 checks.

## 5. Why AI is Used Exclusively for Observation
Multimodal LLMs excel at perceiving unstructured visual scenes: reading blurry printed labels (OCR), detecting crush creases on cardboard, identifying moisture stains, and categorizing item color.
However, LLMs are fundamentally non-deterministic, prone to subtle arithmetic hallucinations, and poor at enforcing strict commercial contract rules consistently across millions of SKUs.
Therefore, AI is strictly bounded to the role of an **Evidence Extractor**: it reports what is visually present without deciding if the shipment is commercially acceptable.

## 6. Why Deterministic Code Performs Comparison
All contractual comparisons are computed by pure deterministic code:
- Calculating $CartonsCounted \times UnitsPerCartonCounted$ and checking against $QuantityOrdered$.
- Normalizing and matching SKU strings.
- Enforcing zero-tolerance thresholds for moisture or crushing on fragile items.
Deterministic code guarantees 100% reproducible decisions, clear discrepancy arithmetic (e.g., `-2 units`), and unambiguous audit trails.

## 7. Evaluation Architecture & Dual-Labeler Reliability (Phase 3)
A vision benchmark is only as credible as its ground-truth annotations:
1. **Independent Dual Annotators:** Ground-truth labels require independent review by two human raters (`Annotator A` and `Annotator B`).
2. **Inter-Annotator Agreement (Cohen's Kappa $\kappa$):** The framework quantifies labeling consensus before scoring the AI agent.
3. **Consensus Adjudication:** Disagreements are adjudicated by an operational lead with documented rationale.
4. **Hard Honesty Guards:** `run_eval.py` refuses to report official accuracy, false-positive rates, or Kappa if independent annotations are absent.
5. **Starter CSV Exclusion:** `data/receiving_sample.csv` is strictly isolated as synthetic starter reference data; it is never used for evaluation.

## 8. Why UNCERTAIN Exists
In an operational warehouse, lighting varies, labels can have specular glare, and pallets can be partially wrapped in plastic.
If an automated system is forced into a binary PASS/FAIL decision, it will either:
- **False-Fail** good shipments, generating costly operational false alarms and dock congestion.
- **False-Pass** defective shipments, letting expensive supplier errors slip into inventory.
`UNCERTAIN` represents honest epistemological limits. It alerts the operator to take a clearer photo or manually verify the discrepancy. It is never treated as a weak pass.

## 9. Fail-Open Operational Philosophy
Warehouse dock lines process hundreds of cartons per hour. A system that crashes or freezes when a vision API experiences a timeout will be bypassed by operators within 24 hours.
The Receiving Manager fails open: if a vision call times out, encounters network degradation, or is unconfigured, the raw photos and SHA-256 hashes are preserved, an unverified record is created with `final_verdict: PENDING_REVIEW`, and the line continues moving without interruption.

## 10. Tenancy Considerations
Enterprise 3PLs service dozens of distinct merchant clients on the same receiving docks.
Multi-tenancy isolation must be enforced:
- Every table and record is partitioned by `org_id` (e.g. `org_demo_alpha` vs `org_demo_bravo`).
- Database Row-Level Security (RLS) must guarantee zero visibility across tenant boundaries.
- Photo URLs and asset paths must not be sequentially guessable across tenants.
- Any request for an inspection belonging to another tenant returns `404 Not Found` (never 403) to prevent leaking the existence of competitor records.

## 11. Backend API & Inspection Service (Phase 4 Implemented)
In Phase 4, the Receiving Manager is encapsulated in a production-ready FastAPI service:
1. **Separation of Concerns:** The API handles HTTP validation, tenancy context, and serialization. It delegates domain verification to the existing `ReceivingAgent` and deterministic `ComparisonEngine`.
2. **Repository Abstraction:** Data access is abstracted behind an `InspectionRepository` interface. Phase 4 provides a thread-safe `InMemoryInspectionRepository`. Future phases can swap in PostgreSQL/MongoDB without touching business logic.
3. **Fail-Open Routing:** If the multimodal vision provider times out, returns malformed JSON, or is unconfigured, the service records `final_verdict: PENDING_REVIEW`, preserves all metadata and photo references, and returns safely without raising 500 errors.
4. **Auditable Operator Overrides:** Warehouse receivers can override automated verdicts (`POST /api/v1/inspections/{id}/override`). Overrides preserve the original verdict, require an `operator_id` and non-empty `reason`, and forbid `PENDING_REVIEW` as an override verdict.
5. **Development Persistence Note:**
   > *This Phase 4 backend uses an in-memory repository for development. Production persistence/authentication will be added in a later phase.*

## 12. Frontend Application & Exception UI (Phase 5 Implemented)
In Phase 5, an enterprise-grade warehouse operations interface is implemented in React 18, Vite 5, TypeScript, and React Router v6:
1. **Evidence-First Operational Design:** High-contrast status indicators for `PASS` (green), `FAIL` (red), `UNCERTAIN` (amber), and `PENDING_REVIEW` (orange). Large typography and structured tables designed for warehouse lighting and rapid scan-and-verify workflows.
2. **Centralized REST Integration:** `inspectionApi.ts` wraps all backend operations, injecting `X-Org-ID` headers to ensure tenant context is preserved across all HTTP requests.
3. **Deterministic Exception Visibility:** The Expected vs Observed comparison panel and Check-Level breakdown display exact numerical and textual deltas (e.g. quantity discrepancies of `-2 units` or damage notes), leaving zero ambiguity for supplier dispute claims.
4. **Auditable Human Overrides:** Operators can challenge automated decisions via a dedicated modal requiring an operator ID and non-empty rationale. Both original AI and human override verdicts remain permanently visible in UI history.
5. **Fail-Open Queue:** Failed-open inspections route directly to the `/pending` queue, allowing supervisors to review raw photos and manually override without blocking dock traffic.
6. **Phase 5 Limitations:**
   - Tenant selection is a development/demo mechanism, not production authentication.
   - In-memory persistence remains in use for rapid local development.
   - Photo references point to local files or mock staging identifiers.
   - Official held-out evaluation accuracy metrics remain strictly unpopulated.

## 13. Demo Hardening & Submission Preparation (Phase 6 Implemented)
In Phase 6, the system was hardened for live jury evaluations and end-to-end demonstrations:
1. **Isolated Demo Scenario Fixtures:** A dedicated demo runner and seed system provides 4 deterministic scenarios (`DEMO-PASS-001`, `DEMO-FAIL-001`, `DEMO-UNCERTAIN-001`, `DEMO-PENDING-001`). These are strictly tagged with `DEMO-*` prefixes and isolated from official evaluation datasets (`ground_truth.json`).
2. **One-Click Presets & Dev Seeding:**
   - Frontend provides quick preset buttons on the New Inspection form to prefill scenario attributes instantly.
   - Dashboard provides a `⚡ [DEMO] Seed 4 Scenarios` button and dev endpoints (`POST /api/v1/demo/seed`, `POST /api/v1/demo/reset`).
   - CLI tool `scripts/seed_demo_scenarios.py` enables non-interactive scenario population.
3. **Session Metrics Demarcation:** The Dashboard explicitly labels in-memory stats as `Session Metrics (In-Memory Development Demo)` to prevent presenting ephemeral counts as production throughput.
4. **Jury Walkthrough Script:** A structured 3–5 minute timed presentation guide (`demo-script.md`) walks judges through Problem, Architecture, PASS, Shortage/Damage FAIL, Explicit UNCERTAIN, Provider Failure Fail-Open, Structured Evidence, and Operator Overrides.
5. **Comprehensive Verification:** 70 automated tests (37 agent, 17 backend, 16 frontend) verified passing, and the frontend Vite production build compiles with zero errors.




# CUBE Buildathon ? Engineering Rules & Agent Guidelines

## Identity & Role
You are developing the **Receiving Manager** (Pod 01) for the CUBE Buildathon.
This is Step 1 of 5 in the Commerce Context stream:
`Receiving Manager` -> `Prep Manager` -> `Pack Manager` -> `Returns Manager` -> `Recovery Manager`.

## Core Inviolable Principles

### 1. Separation of Concerns: AI Observes, Deterministic Code Decides
- **Vision AI** extracts objective observations only: OCR of labels, carton count visible, units counted in master carton, detected damage categories with bounding boxes, visual color, observed components, and image clarity.
- **Deterministic Application Logic** conducts all mathematical checks (Cartons * Units/Carton), string matches, and contract verification.
- **Never** prompt an LLM to make the final holistic PASS/FAIL verdict.

### 2. UNCERTAIN is a First-Class Verdict
- `UNCERTAIN` is **never** a low-confidence PASS.
- When an image is blurry, occluded, or unreadable, the system returns `UNCERTAIN` and routes to `pending_review`.
- In warehouse operations, an agent that declines to guess bad data builds credibility; a hallucinating agent gets unplugged.

### 3. Absolute Honesty & Zero Fabrication
- **Never fabricate evaluation metrics:** Report only what was measured against real fixtures with recorded ground truth.
- **Never fabricate evidence:** No synthetic bounding boxes or fake image paths passed off as physical verification.
- **Say what was built:** A hash check is a hash check, not an "immutable distributed ledger" unless actually implemented.

### 4. Tenancy Isolation Before Any Feature
- All data queries and file access must be strictly scoped to `org_id` (e.g. `org_demo_alpha` vs `org_demo_bravo`).
- Multi-tenancy leaks (e.g. guessable image URLs across tenants) are critical security failures.

### 5. Batched Multimodal Calls (Phase 2 Requirement)
- In Phase 2, execute **exactly one** batched model call per unit covering all checks.
- Never fire multiple sequential or parallel LLM calls per individual check.

### 6. Fail-Open Operational Resilience
- If the vision model times out or errors, persist the capture with `final_verdict: PENDING_REVIEW`.
- Never block receiving dock operations with an unhandled exception.

### 7. Auditable Human-in-the-Loop Overrides
- When an operator overrides an agent verdict, capture:
  - `original_verdict`
  - `override_verdict`
  - `operator_id`
  - `reason`
  - `timestamp`
- Never discard or overwrite original verdicts silently.

### 8. Preserve Starter Files
- Do **not** modify or delete official CUBE root files:
  - `README.md`
  - `RULES.md`
  - `GITHUB-GUIDE.md`
  - `data/README.md`
  - `data/receiving_sample.csv`
  - `.github/*`

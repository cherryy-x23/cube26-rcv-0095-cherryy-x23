# CUBE Receiving Manager ? Frontend Application

**Pod 01: Receiving Manager — Dock Verification & Exception UI**

The Receiving Manager Frontend provides an enterprise warehouse operations interface for inbound dock receivers, supervisors, and inventory quality teams.

---

## Features

1. **Dashboard Overview:** Real-time visibility into today's inbound units, pass rates, exception counts (shortages, damages, SKU mismatches), and pending review queues.
2. **New Inbound Inspection:** Structured form capturing PO criteria (SKU, quantity, cartons, variants) and photographic evidence references.
3. **Deterministic Results Hero:** Clear, unambiguous visual banners for `PASS`, `FAIL`, `UNCERTAIN`, and `PENDING_REVIEW`.
4. **PO vs Observation Comparison:** Side-by-side comparison highlighting discrepancies (e.g. ordered 24 units vs observed 22 units).
5. **Check-Level Breakdown:** Table of individual contractual verification checks with deterministic rationale and mathematical delta.
6. **Receiving Evidence Viewer:** Displays raw photo references and SHA-256 digests computed when local files exist.
7. **Auditable Operator Overrides:** Full auditability for human overrides (`POST /api/v1/inspections/{id}/override`), preserving the original system verdict alongside the human rationale.
8. **Multi-Tenant Context:** Demonstrates tenant switching between `org_demo_alpha` and `org_demo_bravo` with strict row-level isolation.
9. **Fail-Open Safety:** Inspections routed to `PENDING_REVIEW` on AI provider timeouts are prominently queued without crashing dock workflows.

---

## Tech Stack

- **Framework:** React 18
- **Build Tool:** Vite 5
- **Language:** TypeScript 5
- **Routing:** React Router v6
- **Testing:** Vitest + React Testing Library + JSDOM
- **Styling:** Custom Warehouse Operations Design System (CSS)

---

## Local Development & Setup

### 1. Install Dependencies
```bash
cd submissions/cherryy-x23/frontend
npm install
```

### 2. Configure Environment
Create `.env` (or copy from `.env.example`):
```bash
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Start Development Server
```bash
npm run dev
```
The interface will be accessible at: `http://localhost:5173`

### 4. Build Production Bundle
```bash
npm run build
```
Build output is saved to `dist/`.

### 5. Run Frontend Tests
```bash
npm test
```

---

## Frontend Architecture

```text
src/
├── api/
│   └── inspectionApi.ts       # Centralized REST client with error wrapping
├── components/
│   ├── ChecksBreakdown.tsx    # Table of individual verification checks
│   ├── ComparisonPanel.tsx    # Expected PO vs Visual Evidence side-by-side
│   ├── EvidencePanel.tsx      # Photo references and SHA-256 digests
│   ├── Header.tsx             # Tenant and API connectivity status
│   ├── Layout.tsx             # Application sidebar + content shell
│   ├── OverrideModal.tsx      # Modal for submitting human operator overrides
│   ├── Sidebar.tsx            # Navigation and demo tenant switcher
│   └── StatusBadge.tsx        # High-contrast PASS/FAIL/UNCERTAIN/PENDING badges
├── context/
│   └── TenantContext.tsx      # Multi-tenant state and health polling
├── pages/
│   ├── Dashboard.tsx          # Real-time metrics and recent inspection table
│   ├── InspectionHistory.tsx  # Historical audit log with verdict filters
│   ├── InspectionResult.tsx   # Detailed inspection report and execution runner
│   ├── InspectionsList.tsx    # Tenant-scoped inspection directory
│   ├── NewInspection.tsx      # Inbound PO and evidence registration form
│   └── PendingReview.tsx      # Fail-open review queue for dock supervisors
├── styles/
│   └── index.css              # Operational warehouse design tokens
├── tests/
│   ├── frontend.test.tsx      # 14 unit and integration tests
│   └── setup.ts               # Test environment configuration
└── types/
    └── inspection.ts          # Strongly typed domain schemas
```

---

## Phase 5 Limitations

- **Tenant Selection:** The tenant switcher is a development/demo mechanism (`X-Org-ID`), not production authentication.
- **Backend Persistence:** Uses the Phase 4 in-memory repository for development. Persistent database storage (PostgreSQL/MongoDB) is scheduled for a future phase.
- **Evidence Storage:** Photo references point to local filepaths or staging identifiers, not cloud object storage.
- **Held-Out Evaluation:** Ground-truth accuracy metrics remain explicitly `NOT YET AVAILABLE` until physical held-out units are captured and annotated.

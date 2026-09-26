import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { TenantProvider } from '../context/TenantContext';
import { Dashboard } from '../pages/Dashboard';
import { NewInspection } from '../pages/NewInspection';
import { InspectionResult } from '../pages/InspectionResult';
import { InspectionHistory } from '../pages/InspectionHistory';
import { OverrideModal } from '../components/OverrideModal';
import { inspectionApi } from '../api/inspectionApi';
import { Inspection } from '../types/inspection';

const sampleInspectionPass: Inspection = {
  inspection_id: 'INSP-PASS-001',
  org_id: 'org_demo_alpha',
  unit_id: 'UNIT-DEMO-001',
  operator_id: 'operator-001',
  po_number: 'PO-1001',
  po_line: 1,
  supplier: 'Demo Supplier',
  expected: {
    sku: 'BLUE-BOTTLE-001',
    qty_ordered: 24,
    cartons_ordered: 2,
    units_per_carton_ordered: 12,
  },
  photo_references: [{ path: 'fixtures/unit-001/photo-01.jpg', sha256: 'abc123' }],
  status: 'completed',
  verdict: 'PASS',
  evidence_record: {
    rcv_number: 'RCV-001',
    unit_id: 'UNIT-DEMO-001',
    timestamp: '2026-09-26T08:00:00Z',
    final_verdict: 'PASS',
    checks: [
      {
        check_type: 'quantity_carton_and_unit',
        verdict: 'PASS',
        expected_value: '24 units',
        observed_value: '24 units',
        discrepancy: '0 units',
      },
    ],
  },
  created_at: '2026-09-26T08:00:00Z',
  updated_at: '2026-09-26T08:00:00Z',
};

const sampleInspectionFail: Inspection = {
  ...sampleInspectionPass,
  inspection_id: 'INSP-FAIL-002',
  verdict: 'FAIL',
  evidence_record: {
    ...sampleInspectionPass.evidence_record!,
    final_verdict: 'FAIL',
    checks: [
      {
        check_type: 'quantity_carton_and_unit',
        verdict: 'FAIL',
        expected_value: '24 units',
        observed_value: '22 units',
        discrepancy: '-2 units',
      },
    ],
  },
};

const sampleInspectionUncertain: Inspection = {
  ...sampleInspectionPass,
  inspection_id: 'INSP-UNCERTAIN-003',
  verdict: 'UNCERTAIN',
  evidence_record: {
    ...sampleInspectionPass.evidence_record!,
    final_verdict: 'UNCERTAIN',
    checks: [],
  },
};

const sampleInspectionPendingReview: Inspection = {
  ...sampleInspectionPass,
  inspection_id: 'INSP-PENDING-004',
  status: 'pending_review',
  verdict: 'PENDING_REVIEW',
  evidence_record: null,
};

describe('Receiving Manager Frontend Unit & Integration Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // Test 1: Dashboard renders
  it('1. Dashboard renders operational summary and cards', async () => {
    vi.spyOn(inspectionApi, 'listInspections').mockResolvedValue([sampleInspectionPass]);

    render(
      <TenantProvider>
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      </TenantProvider>
    );

    expect(screen.getByText(/Receiving Dock Overview/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Inbound/i)).toBeInTheDocument();
    expect(screen.getByText(/Passed Inbound/i)).toBeInTheDocument();
    expect(screen.getByText(/Exceptions/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('INSP-PASS-001')).toBeInTheDocument();
    });
  });

  // Test 2: New inspection form renders
  it('2. New inspection form renders all required inputs', () => {
    render(
      <TenantProvider>
        <MemoryRouter>
          <NewInspection />
        </MemoryRouter>
      </TenantProvider>
    );

    expect(screen.getByLabelText(/Receiving Unit ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Expected SKU/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Total Quantity Ordered/i)).toBeInTheDocument();
    expect(screen.getByTestId('submit-inspection-button')).toBeInTheDocument();
  });

  // Test 3: Required validation works
  it('3. Required validation rejects missing SKU', async () => {
    render(
      <TenantProvider>
        <MemoryRouter>
          <NewInspection />
        </MemoryRouter>
      </TenantProvider>
    );

    const skuInput = screen.getByLabelText(/Expected SKU/i);
    fireEvent.change(skuInput, { target: { value: '' } });

    const submitBtn = screen.getByTestId('submit-inspection-button');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId('create-error')).toHaveTextContent(/Product SKU is strictly required/i);
    });
  });

  // Test 4: Create inspection calls API
  it('4. Create inspection calls API with expected payload', async () => {
    const createSpy = vi.spyOn(inspectionApi, 'createInspection').mockResolvedValue(sampleInspectionPass);

    render(
      <TenantProvider>
        <MemoryRouter>
          <NewInspection />
        </MemoryRouter>
      </TenantProvider>
    );

    const submitBtn = screen.getByTestId('submit-inspection-button');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          org_id: 'org_demo_alpha',
          expected: expect.objectContaining({
            sku: 'BLUE-BOTTLE-001',
            qty_ordered: 24,
          }),
        })
      );
    });
  });

  // Test 5: Inspection result renders PASS
  it('5. Inspection result renders PASS hero and badge', async () => {
    vi.spyOn(inspectionApi, 'getInspection').mockResolvedValue(sampleInspectionPass);

    render(
      <TenantProvider>
        <MemoryRouter initialEntries={['/inspections/INSP-PASS-001']}>
          <Routes>
            <Route path="/inspections/:inspectionId" element={<InspectionResult />} />
          </Routes>
        </MemoryRouter>
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('result-hero-pass')).toBeInTheDocument();
      expect(screen.getByText(/Receiving matches the available photographic evidence/i)).toBeInTheDocument();
    });
  });

  // Test 6: FAIL result renders correctly
  it('6. FAIL result renders correctly with discrepancy notes', async () => {
    vi.spyOn(inspectionApi, 'getInspection').mockResolvedValue(sampleInspectionFail);

    render(
      <TenantProvider>
        <MemoryRouter initialEntries={['/inspections/INSP-FAIL-002']}>
          <Routes>
            <Route path="/inspections/:inspectionId" element={<InspectionResult />} />
          </Routes>
        </MemoryRouter>
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('result-hero-fail')).toBeInTheDocument();
      expect(screen.getByText('-2 units')).toBeInTheDocument();
    });
  });

  // Test 7: UNCERTAIN remains UNCERTAIN
  it('7. UNCERTAIN remains UNCERTAIN and does not convert to PASS or FAIL', async () => {
    vi.spyOn(inspectionApi, 'getInspection').mockResolvedValue(sampleInspectionUncertain);

    render(
      <TenantProvider>
        <MemoryRouter initialEntries={['/inspections/INSP-UNCERTAIN-003']}>
          <Routes>
            <Route path="/inspections/:inspectionId" element={<InspectionResult />} />
          </Routes>
        </MemoryRouter>
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('result-hero-uncertain')).toBeInTheDocument();
      expect(screen.getByText(/Available visual evidence is insufficient or ambiguous/i)).toBeInTheDocument();
    });
  });

  // Test 8: PENDING_REVIEW renders correctly
  it('8. PENDING_REVIEW renders correctly for fail-open routing', async () => {
    vi.spyOn(inspectionApi, 'getInspection').mockResolvedValue(sampleInspectionPendingReview);

    render(
      <TenantProvider>
        <MemoryRouter initialEntries={['/inspections/INSP-PENDING-004']}>
          <Routes>
            <Route path="/inspections/:inspectionId" element={<InspectionResult />} />
          </Routes>
        </MemoryRouter>
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('result-hero-pending_review')).toBeInTheDocument();
      expect(screen.getByText(/Automated inspection could not be completed/i)).toBeInTheDocument();
    });
  });

  // Test 9: Operator override modal works
  it('9. Operator override modal submits human override decision', async () => {
    const overrideSubmitMock = vi.fn().mockResolvedValue(undefined);

    render(
      <OverrideModal
        isOpen={true}
        onClose={vi.fn()}
        originalVerdict="FAIL"
        onSubmit={overrideSubmitMock}
        isLoading={false}
      />
    );

    expect(screen.getByTestId('override-modal')).toBeInTheDocument();
    const reasonInput = screen.getByLabelText(/Operator Rationale/i);
    fireEvent.change(reasonInput, { target: { value: 'Inspected physical carton; full 24 count verified.' } });

    const submitBtn = screen.getByTestId('submit-override-button');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(overrideSubmitMock).toHaveBeenCalledWith(
        'PASS',
        'Inspected physical carton; full 24 count verified.',
        'operator-lead-01'
      );
    });
  });

  // Test 10: Original verdict remains visible after override
  it('10. Original verdict remains visible alongside operator override', async () => {
    const overriddenInspection: Inspection = {
      ...sampleInspectionFail,
      operator_override: {
        original_verdict: 'FAIL',
        override_verdict: 'PASS',
        operator_id: 'operator-lead-01',
        reason: 'Physical box undamaged; inner count checked.',
        timestamp: '2026-09-26T08:15:00Z',
      },
    };

    vi.spyOn(inspectionApi, 'getInspection').mockResolvedValue(overriddenInspection);

    render(
      <TenantProvider>
        <MemoryRouter initialEntries={['/inspections/INSP-FAIL-002']}>
          <Routes>
            <Route path="/inspections/:inspectionId" element={<InspectionResult />} />
          </Routes>
        </MemoryRouter>
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('override-notice')).toBeInTheDocument();
      expect(screen.getByText(/Original AI Verdict:/i)).toBeInTheDocument();
      expect(screen.getByText(/Operator Final Verdict:/i)).toBeInTheDocument();
      expect(screen.getByText(/Physical box undamaged/i)).toBeInTheDocument();
    });
  });

  // Test 11: Inspection history renders
  it('11. Inspection history renders table and filter buttons', async () => {
    vi.spyOn(inspectionApi, 'listInspections').mockResolvedValue([sampleInspectionPass, sampleInspectionFail]);

    render(
      <TenantProvider>
        <MemoryRouter>
          <InspectionHistory />
        </MemoryRouter>
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Receiving Inspection History/i)).toBeInTheDocument();
      expect(screen.getByTestId('filter-all')).toBeInTheDocument();
      expect(screen.getByTestId('filter-pass')).toBeInTheDocument();
      expect(screen.getByTestId('filter-fail')).toBeInTheDocument();
      expect(screen.getByText('INSP-PASS-001')).toBeInTheDocument();
      expect(screen.getByText('INSP-FAIL-002')).toBeInTheDocument();
    });
  });

  // Test 12: Tenant header/context is sent
  it('12. Tenant header X-Org-ID is sent with API calls', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [sampleInspectionPass],
    });
    // @ts-ignore
    global.fetch = fetchMock;

    await inspectionApi.listInspections('org_demo_bravo');

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('org_id=org_demo_bravo'),
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    );

    const callHeaders = fetchMock.mock.calls[0][1].headers as Headers;
    expect(callHeaders.get('X-Org-ID')).toBe('org_demo_bravo');
  });

  // Test 13: Backend error state renders
  it('13. Backend error state renders clear error message', async () => {
    vi.spyOn(inspectionApi, 'listInspections').mockRejectedValue(
      new Error('Backend unavailable. Please make sure the FastAPI server is running.')
    );

    render(
      <TenantProvider>
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('dashboard-error')).toHaveTextContent(
        /Backend unavailable. Please make sure the FastAPI server is running/i
      );
    });
  });

  // Test 14: Loading state prevents duplicate submission
  it('14. Loading state disables duplicate run inspection clicks', async () => {
    const stagedInspection: Inspection = {
      ...sampleInspectionPass,
      status: 'pending',
      verdict: null,
      evidence_record: null,
    };

    vi.spyOn(inspectionApi, 'getInspection').mockResolvedValue(stagedInspection);
    // Make runInspection take a moment
    vi.spyOn(inspectionApi, 'runInspection').mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({}), 500))
    );

    render(
      <TenantProvider>
        <MemoryRouter initialEntries={['/inspections/INSP-PASS-001']}>
          <Routes>
            <Route path="/inspections/:inspectionId" element={<InspectionResult />} />
          </Routes>
        </MemoryRouter>
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('run-inspection-button')).toBeInTheDocument();
    });

    const runBtn = screen.getByTestId('run-inspection-button');
    fireEvent.click(runBtn);

    // During running, button is replaced with running banner
    expect(screen.getByTestId('running-inspection-card')).toBeInTheDocument();
    expect(screen.queryByTestId('run-inspection-button')).not.toBeInTheDocument();
  });

  // Test 15: Demo Scenario Presets auto-populate New Inspection Form
  it('15. Demo scenario presets auto-populate form fields', async () => {
    render(
      <TenantProvider>
        <MemoryRouter>
          <NewInspection />
        </MemoryRouter>
      </TenantProvider>
    );

    // Click on Shortage / Damage preset button
    const failPresetBtn = screen.getByTestId('preset-fail');
    expect(failPresetBtn).toBeInTheDocument();
    fireEvent.click(failPresetBtn);

    // Form inputs should reflect DEMO-FAIL values
    expect(screen.getByLabelText(/Receiving Unit ID/i)).toHaveValue('DEMO-FAIL-001');
    expect(screen.getByLabelText(/Purchase Order #/i)).toHaveValue('PO-DEMO-1002');
    expect(screen.getByLabelText(/Total Quantity Ordered/i)).toHaveValue(24);
  });

  // Test 16: Dashboard Demo Seed button invokes seed API
  it('16. Dashboard demo seed button invokes API and shows status message', async () => {
    vi.spyOn(inspectionApi, 'listInspections').mockResolvedValue([]);
    const seedSpy = vi.spyOn(inspectionApi, 'seedDemoScenarios').mockResolvedValue({
      status: 'seeded',
      count: 4,
      seeded_records: [],
    });

    render(
      <TenantProvider>
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      </TenantProvider>
    );

    const seedBtn = await screen.findByTestId('seed-demo-button');
    expect(seedBtn).not.toBeDisabled();
    fireEvent.click(seedBtn);

    await waitFor(() => {
      expect(seedSpy).toHaveBeenCalled();
      expect(screen.getByTestId('demo-feedback')).toHaveTextContent(/seeded successfully/i);
    });
  });
});


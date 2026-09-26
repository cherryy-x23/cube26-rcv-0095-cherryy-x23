import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { inspectionApi } from '../api/inspectionApi';
import { Inspection } from '../types/inspection';
import { StatusBadge } from '../components/StatusBadge';

export const Dashboard: React.FC = () => {
  const { currentOrg } = useTenant();
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInspections = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await inspectionApi.listInspections(currentOrg);
      setInspections(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch inspections.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInspections();
  }, [currentOrg]);

  // Derived real metrics from the active session
  const total = inspections.length;
  const passed = inspections.filter((i) => i.verdict === 'PASS').length;
  const exceptions = inspections.filter((i) => i.verdict === 'FAIL' || i.verdict === 'UNCERTAIN').length;
  const pendingReview = inspections.filter(
    (i) => i.status === 'pending_review' || i.verdict === 'PENDING_REVIEW'
  ).length;

  const [demoActionLoading, setDemoActionLoading] = useState<boolean>(false);
  const [demoFeedback, setDemoFeedback] = useState<string | null>(null);

  const handleSeedDemo = async () => {
    setDemoActionLoading(true);
    setDemoFeedback(null);
    try {
      await inspectionApi.seedDemoScenarios();
      setDemoFeedback('4 CUBE Demo Scenarios seeded successfully (PASS, FAIL, UNCERTAIN, PENDING_REVIEW).');
      await fetchInspections();
    } catch (err: any) {
      setError(err.message || 'Failed to seed demo scenarios.');
    } finally {
      setDemoActionLoading(false);
    }
  };

  const handleResetDemo = async () => {
    setDemoActionLoading(true);
    setDemoFeedback(null);
    try {
      await inspectionApi.resetDemoRepository();
      setDemoFeedback('In-memory repository cleared.');
      await fetchInspections();
    } catch (err: any) {
      setError(err.message || 'Failed to reset repository.');
    } finally {
      setDemoActionLoading(false);
    }
  };

  return (
    <div className="page-container" data-testid="dashboard-page">
      <div className="page-header">
        <div>
          <h2>Receiving Dock Overview</h2>
          <p>Real-time inbound shipment verification and defect exception tracking</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleSeedDemo}
            className="btn btn-outline btn-sm"
            disabled={demoActionLoading || loading}
            data-testid="seed-demo-button"
            title="Seeds all 4 official CUBE demo scenarios"
          >
            {demoActionLoading ? 'Loading...' : '⚡ [DEMO] Seed 4 Scenarios'}
          </button>
          <button
            onClick={handleResetDemo}
            className="btn btn-outline btn-sm"
            disabled={demoActionLoading || loading}
            data-testid="reset-demo-button"
            title="Resets in-memory records"
          >
            Reset
          </button>
          <Link to="/new-inspection" className="btn btn-primary btn-sm" data-testid="new-inspection-button">
            <span>➕</span>
            <span>New Inspection</span>
          </Link>
        </div>
      </div>

      {demoFeedback && (
        <div className="alert alert-info" style={{ marginBottom: '16px' }} data-testid="demo-feedback">
          <span>ℹ️</span>
          <div>{demoFeedback}</div>
        </div>
      )}

      {error && (
        <div className="alert alert-error" role="alert" data-testid="dashboard-error">
          <span>⚠️</span>
          <div>
            <strong>Backend Error:</strong> {error}
          </div>
        </div>
      )}

      <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
        Session Metrics (In-Memory Development Demo)
      </div>

      {/* Metrics Row */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Inbound</div>
          <div className="stat-value">{loading ? '—' : total}</div>
          <div className="stat-sub">Units inspected in session</div>
        </div>

        <div className="stat-card stat-pass">
          <div className="stat-label">Passed Inbound</div>
          <div className="stat-value" style={{ color: '#15803d' }}>
            {loading ? '—' : passed}
          </div>
          <div className="stat-sub">Matched PO & specifications</div>
        </div>

        <div className="stat-card stat-fail">
          <div className="stat-label">Exceptions (Fail/Uncertain)</div>
          <div className="stat-value" style={{ color: '#b91c1c' }}>
            {loading ? '—' : exceptions}
          </div>
          <div className="stat-sub">Shortages, wrong SKUs, damage</div>
        </div>

        <div className="stat-card stat-pending">
          <div className="stat-label">Pending Review</div>
          <div className="stat-value" style={{ color: '#c2410c' }}>
            {loading ? '—' : pendingReview}
          </div>
          <div className="stat-sub">Operator action required</div>
        </div>
      </div>

      {/* Recent Inspections Table */}
      <div className="card">
        <div className="card-title">
          <span>Recent Receiving Inspections ({currentOrg})</span>
          <button
            onClick={fetchInspections}
            className="btn btn-outline btn-sm"
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '32px' }}>
            <span className="spinner spinner-dark" />
            <div style={{ marginTop: '8px', color: '#64748b' }}>Loading receiving records...</div>
          </div>
        ) : inspections.length === 0 ? (
          <div className="empty-state" data-testid="empty-inspections">
            <div className="empty-state-icon">📦</div>
            <h3>No inspections yet</h3>
            <p>Create your first receiving inspection to verify an inbound shipment.</p>
            <Link to="/new-inspection" className="btn btn-primary btn-sm">
              Create Inspection
            </Link>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Inspection</th>
                  <th>PO Number</th>
                  <th>Unit ID</th>
                  <th>Expected SKU</th>
                  <th>Verdict</th>
                  <th>Status</th>
                  <th>Created At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {inspections.slice(0, 10).map((insp) => (
                  <tr key={insp.inspection_id} data-testid={`inspection-row-${insp.inspection_id}`}>
                    <td className="font-mono" style={{ fontWeight: 600 }}>
                      {insp.inspection_id}
                    </td>
                    <td className="font-mono">{insp.po_number}</td>
                    <td className="font-mono">{insp.unit_id}</td>
                    <td className="font-mono">{insp.expected.sku}</td>
                    <td>
                      <StatusBadge verdict={insp.verdict} size="sm" />
                    </td>
                    <td>
                      <span style={{ textTransform: 'capitalize', fontSize: '12px', color: '#64748b' }}>
                        {insp.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ fontSize: '12px', color: '#64748b' }}>
                      {new Date(insp.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td>
                      <Link
                        to={`/inspections/${insp.inspection_id}`}
                        className="btn btn-outline btn-sm"
                        data-testid={`view-inspection-${insp.inspection_id}`}
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

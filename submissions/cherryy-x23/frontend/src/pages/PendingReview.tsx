import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { inspectionApi } from '../api/inspectionApi';
import { Inspection } from '../types/inspection';
import { StatusBadge } from '../components/StatusBadge';

export const PendingReview: React.FC = () => {
  const { currentOrg } = useTenant();
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPending = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await inspectionApi.listInspections(currentOrg);
      const pendingItems = data.filter(
        (i) => i.status === 'pending_review' || i.verdict === 'PENDING_REVIEW'
      );
      setInspections(pendingItems);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch pending inspections.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, [currentOrg]);

  return (
    <div className="page-container" data-testid="pending-review-page">
      <div className="page-header">
        <div>
          <h2>Pending Review Queue</h2>
          <p>
            Inbound inspections that failed-open due to model timeout, unconfigured provider, or network degradation
          </p>
        </div>
        <button onClick={fetchPending} className="btn btn-outline btn-sm" disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh Queue'}
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          <span>⚠️</span>
          <div>{error}</div>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '36px' }}>
            <span className="spinner spinner-dark" />
            <p style={{ marginTop: '8px', color: '#64748b' }}>Checking pending review queue...</p>
          </div>
        ) : inspections.length === 0 ? (
          <div className="empty-state" data-testid="empty-pending-state">
            <div className="empty-state-icon">✓</div>
            <h3>No inspections require review</h3>
            <p>All inbound shipments have either completed deterministic inspection or are in initial staging.</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Inspection ID</th>
                  <th>PO Number</th>
                  <th>Unit ID</th>
                  <th>Reason / Status</th>
                  <th>Created At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {inspections.map((insp) => (
                  <tr key={insp.inspection_id} data-testid={`pending-row-${insp.inspection_id}`}>
                    <td className="font-mono" style={{ fontWeight: 600 }}>
                      {insp.inspection_id}
                    </td>
                    <td className="font-mono">{insp.po_number}</td>
                    <td className="font-mono">{insp.unit_id}</td>
                    <td>
                      <StatusBadge verdict="PENDING_REVIEW" size="sm" />
                    </td>
                    <td style={{ fontSize: '12.5px', color: '#64748b' }}>
                      {new Date(insp.created_at).toLocaleString()}
                    </td>
                    <td>
                      <Link to={`/inspections/${insp.inspection_id}`} className="btn btn-primary btn-sm">
                        Review & Override
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

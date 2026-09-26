import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { inspectionApi } from '../api/inspectionApi';
import { Inspection } from '../types/inspection';
import { StatusBadge } from '../components/StatusBadge';

export const InspectionsList: React.FC = () => {
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

  return (
    <div className="page-container" data-testid="inspections-list-page">
      <div className="page-header">
        <div>
          <h2>All Inbound Inspections</h2>
          <p>Complete directory of receiving units registered under tenant {currentOrg}</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={fetchInspections} className="btn btn-outline btn-sm" disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <Link to="/new-inspection" className="btn btn-primary btn-sm">
            + New Inspection
          </Link>
        </div>
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
            <p style={{ marginTop: '8px', color: '#64748b' }}>Loading tenant inspections...</p>
          </div>
        ) : inspections.length === 0 ? (
          <div className="empty-state" data-testid="empty-all-inspections">
            <div className="empty-state-icon">📦</div>
            <h3>No inspections registered</h3>
            <p>There are no active or completed inspections for organization {currentOrg}.</p>
            <Link to="/new-inspection" className="btn btn-primary btn-sm">
              Create First Inspection
            </Link>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Inspection ID</th>
                  <th>PO Number</th>
                  <th>Unit ID</th>
                  <th>SKU</th>
                  <th>Status</th>
                  <th>Verdict</th>
                  <th>Created At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {inspections.map((insp) => (
                  <tr key={insp.inspection_id} data-testid={`list-row-${insp.inspection_id}`}>
                    <td className="font-mono" style={{ fontWeight: 600 }}>
                      {insp.inspection_id}
                    </td>
                    <td className="font-mono">{insp.po_number}</td>
                    <td className="font-mono">{insp.unit_id}</td>
                    <td className="font-mono">{insp.expected.sku}</td>
                    <td>
                      <span
                        style={{
                          textTransform: 'capitalize',
                          fontSize: '12px',
                          color: '#475569',
                          fontWeight: 500,
                        }}
                      >
                        {insp.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td>
                      <StatusBadge verdict={insp.verdict} status={insp.status} size="sm" />
                    </td>
                    <td style={{ fontSize: '12.5px', color: '#64748b' }}>
                      {new Date(insp.created_at).toLocaleString()}
                    </td>
                    <td>
                      <Link
                        to={`/inspections/${insp.inspection_id}`}
                        className="btn btn-outline btn-sm"
                        data-testid={`inspect-btn-${insp.inspection_id}`}
                      >
                        {insp.status === 'pending' ? 'Run Inspection' : 'View Record'}
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

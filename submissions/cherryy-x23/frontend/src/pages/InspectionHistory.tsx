import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { inspectionApi } from '../api/inspectionApi';
import { Inspection } from '../types/inspection';
import { StatusBadge } from '../components/StatusBadge';

export const InspectionHistory: React.FC = () => {
  const { currentOrg } = useTenant();
  const [inspections, setInspections] = useState<Inspection[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filterVerdict, setFilterVerdict] = useState<string>('ALL');

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await inspectionApi.listInspections(currentOrg);
      // Completed or reviewed inspections
      const historyItems = data.filter((i) => i.status === 'completed' || i.status === 'pending_review');
      setInspections(historyItems);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch inspection history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [currentOrg]);

  const filtered = inspections.filter((insp) => {
    if (filterVerdict === 'ALL') return true;
    return insp.verdict === filterVerdict;
  });

  return (
    <div className="page-container" data-testid="inspection-history-page">
      <div className="page-header">
        <div>
          <h2>Receiving Inspection History</h2>
          <p>Historical audit records of inbound shipments verified across this dock</p>
        </div>
        <button onClick={fetchHistory} className="btn btn-outline btn-sm" disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          <span>⚠️</span>
          <div>{error}</div>
        </div>
      )}

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {['ALL', 'PASS', 'FAIL', 'UNCERTAIN', 'PENDING_REVIEW'].map((tab) => (
          <button
            key={tab}
            className={`btn btn-sm ${filterVerdict === tab ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilterVerdict(tab)}
            data-testid={`filter-${tab.toLowerCase()}`}
          >
            {tab.replace('_', ' ')}
          </button>
        ))}
      </div>

      <div className="card">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '36px' }}>
            <span className="spinner spinner-dark" />
            <p style={{ marginTop: '8px', color: '#64748b' }}>Loading historical records...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state" data-testid="empty-history-state">
            <div className="empty-state-icon">📋</div>
            <h3>No historical records found</h3>
            <p>
              {filterVerdict === 'ALL'
                ? 'No completed inspections are stored in memory for this tenant session.'
                : `No inspections found with verdict ${filterVerdict}.`}
            </p>
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
                  <th>System Verdict</th>
                  <th>Operator Override</th>
                  <th>Updated At</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((insp) => (
                  <tr key={insp.inspection_id} data-testid={`history-row-${insp.inspection_id}`}>
                    <td className="font-mono" style={{ fontWeight: 600 }}>
                      {insp.inspection_id}
                    </td>
                    <td className="font-mono">{insp.po_number}</td>
                    <td className="font-mono">{insp.unit_id}</td>
                    <td className="font-mono">{insp.expected.sku}</td>
                    <td>
                      <StatusBadge
                        verdict={insp.operator_override ? insp.operator_override.original_verdict : insp.verdict}
                        size="sm"
                      />
                    </td>
                    <td>
                      {insp.operator_override ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <StatusBadge verdict={insp.operator_override.override_verdict} size="sm" />
                          <span style={{ fontSize: '11px', color: '#64748b' }}>
                            ({insp.operator_override.operator_id})
                          </span>
                        </div>
                      ) : (
                        <span style={{ color: '#94a3b8', fontSize: '12px' }}>None</span>
                      )}
                    </td>
                    <td style={{ fontSize: '12.5px', color: '#64748b' }}>
                      {new Date(insp.updated_at).toLocaleString()}
                    </td>
                    <td>
                      <Link to={`/inspections/${insp.inspection_id}`} className="btn btn-outline btn-sm">
                        View Evidence
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

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';
import { inspectionApi } from '../api/inspectionApi';
import { Inspection, OverrideVerdict } from '../types/inspection';
import { StatusBadge } from '../components/StatusBadge';
import { ComparisonPanel } from '../components/ComparisonPanel';
import { ChecksBreakdown } from '../components/ChecksBreakdown';
import { EvidencePanel } from '../components/EvidencePanel';
import { OverrideModal } from '../components/OverrideModal';

export const InspectionResult: React.FC = () => {
  const { inspectionId } = useParams<{ inspectionId: string }>();
  const { currentOrg } = useTenant();

  const [inspection, setInspection] = useState<Inspection | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isOverrideOpen, setIsOverrideOpen] = useState<boolean>(false);
  const [overrideLoading, setOverrideLoading] = useState<boolean>(false);

  const fetchInspection = async () => {
    if (!inspectionId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await inspectionApi.getInspection(inspectionId, currentOrg);
      setInspection(data);
    } catch (err: any) {
      setError(err.message || 'Inspection not found or inaccessible.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInspection();
  }, [inspectionId, currentOrg]);

  const handleRunInspection = async () => {
    if (!inspectionId) return;
    setRunning(true);
    setError(null);
    try {
      await inspectionApi.runInspection(inspectionId, currentOrg);
      await fetchInspection();
    } catch (err: any) {
      setError(err.message || 'Error running inspection.');
    } finally {
      setRunning(false);
    }
  };

  const handleOverrideSubmit = async (
    overrideVerdict: OverrideVerdict,
    reason: string,
    operatorId: string
  ) => {
    if (!inspectionId) return;
    setOverrideLoading(true);
    try {
      await inspectionApi.overrideInspection(inspectionId, currentOrg, {
        operator_id: operatorId,
        override_verdict: overrideVerdict,
        reason,
      });
      await fetchInspection();
    } finally {
      setOverrideLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '60px 0' }}>
        <span className="spinner spinner-dark" />
        <p style={{ marginTop: '12px', color: '#64748b' }}>Loading inspection #{inspectionId}...</p>
      </div>
    );
  }

  if (error || !inspection) {
    return (
      <div className="page-container" data-testid="inspection-error-state">
        <div className="alert alert-error">
          <span>⚠️</span>
          <div>
            <strong>Error:</strong> {error || 'Inspection not found or inaccessible.'}
          </div>
        </div>
        <Link to="/inspections" className="btn btn-outline">
          ← Back to Inspections
        </Link>
      </div>
    );
  }

  const effectiveVerdict = inspection.verdict;
  const hasOverride = !!inspection.operator_override;

  return (
    <div className="page-container" data-testid="inspection-detail-page">
      {/* Breadcrumb / Top Bar */}
      <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Link to="/inspections" style={{ color: '#0284c7', textDecoration: 'none', fontWeight: 600 }}>
            ← Inspections
          </Link>
          <span style={{ color: '#94a3b8' }}>/</span>
          <span className="font-mono" style={{ color: '#64748b' }}>
            {inspection.inspection_id}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {effectiveVerdict && (
            <button
              onClick={() => setIsOverrideOpen(true)}
              className="btn btn-outline btn-sm"
              data-testid="open-override-button"
            >
              ⚙ Operator Override
            </button>
          )}
          <button onClick={fetchInspection} className="btn btn-outline btn-sm">
            Refresh
          </button>
        </div>
      </div>

      {/* Header Summary Card */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <h2 className="font-mono" style={{ fontSize: '22px', fontWeight: 700 }}>
                {inspection.inspection_id}
              </h2>
              <StatusBadge verdict={inspection.verdict} status={inspection.status} size="lg" />
            </div>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', color: '#475569', fontSize: '13px' }}>
              <div>
                <strong>PO:</strong> <span className="font-mono">{inspection.po_number} (Line {inspection.po_line})</span>
              </div>
              <div>
                <strong>Unit:</strong> <span className="font-mono">{inspection.unit_id}</span>
              </div>
              <div>
                <strong>SKU:</strong> <span className="font-mono">{inspection.expected.sku}</span>
              </div>
              <div>
                <strong>Supplier:</strong> {inspection.supplier || '—'}
              </div>
              <div>
                <strong>Operator:</strong> {inspection.operator_id}
              </div>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase' }}>Created At</div>
            <div className="font-mono" style={{ fontSize: '12.5px' }}>
              {new Date(inspection.created_at).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Action / Ready Banner (If pending) */}
      {inspection.status === 'pending' && !running && (
        <div
          className="card"
          style={{
            background: 'linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%)',
            borderColor: '#bae6fd',
            textAlign: 'center',
            padding: '36px 20px',
          }}
          data-testid="ready-for-inspection-card"
        >
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>⚡</div>
          <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>READY FOR INSPECTION</h3>
          <p style={{ color: '#475569', fontSize: '13.5px', maxWidth: '520px', margin: '0 auto 20px auto' }}>
            Inbound PO criteria and photo references are staged. Run the Receiving Agent to perform
            single-batch multimodal visual extraction and contractual comparison.
          </p>
          <button
            onClick={handleRunInspection}
            className="btn btn-primary btn-lg"
            disabled={running}
            data-testid="run-inspection-button"
          >
            <span>▶</span>
            <span>Run Inspection</span>
          </button>
        </div>
      )}

      {/* Running State Banner */}
      {running && (
        <div
          className="card"
          style={{
            background: '#f8fafc',
            border: '2px dashed #0284c7',
            padding: '32px 20px',
            textAlign: 'center',
          }}
          data-testid="running-inspection-card"
        >
          <span className="spinner spinner-dark" style={{ width: '28px', height: '28px', borderWidth: '3px' }} />
          <h3 style={{ fontSize: '17px', fontWeight: 700, marginTop: '12px', marginBottom: '8px' }}>
            Analyzing receiving evidence...
          </h3>
          <div
            style={{
              display: 'inline-flex',
              flexDirection: 'column',
              gap: '4px',
              color: '#0284c7',
              fontFamily: 'monospace',
              fontSize: '12.5px',
              textAlign: 'left',
              marginTop: '8px',
            }}
          >
            <div>1. Vision evidence extraction (one batched call)</div>
            <div>&nbsp;&nbsp;↓</div>
            <div>2. Specification & SKU matching</div>
            <div>&nbsp;&nbsp;↓</div>
            <div>3. Deterministic quantity arithmetic</div>
            <div>&nbsp;&nbsp;↓</div>
            <div>4. Final immutable evidence record generation</div>
          </div>
        </div>
      )}

      {/* Operator Override Notice Banner */}
      {hasOverride && inspection.operator_override && (
        <div
          className="alert alert-warning"
          style={{ display: 'block', padding: '16px' }}
          data-testid="override-notice"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <strong>OPERATOR OVERRIDE ACTIVE</strong>
            <span style={{ fontSize: '12px', color: '#64748b' }}>
              Recorded at {new Date(inspection.operator_override.timestamp).toLocaleString()}
            </span>
          </div>
          <div style={{ display: 'flex', gap: '24px', fontSize: '13px', flexWrap: 'wrap' }}>
            <div>
              Original AI Verdict:{' '}
              <strong style={{ color: '#b91c1c' }}>{inspection.operator_override.original_verdict}</strong>
            </div>
            <div>
              Operator Final Verdict:{' '}
              <strong style={{ color: '#15803d' }}>{inspection.operator_override.override_verdict}</strong>
            </div>
            <div>
              Operator ID: <span className="font-mono">{inspection.operator_override.operator_id}</span>
            </div>
          </div>
          <div style={{ marginTop: '8px', fontSize: '12.5px', background: '#fff', padding: '8px', borderRadius: '4px' }}>
            <strong>Operator Rationale:</strong> {inspection.operator_override.reason}
          </div>
        </div>
      )}

      {/* Primary Result Hero Card */}
      {effectiveVerdict && (
        <div
          className={`result-hero result-${effectiveVerdict.toLowerCase()}`}
          data-testid={`result-hero-${effectiveVerdict.toLowerCase()}`}
        >
          <div className="result-hero-content">
            <h3>
              {effectiveVerdict === 'PASS' && <span>✓ PASS</span>}
              {effectiveVerdict === 'FAIL' && <span>⚠ FAIL</span>}
              {effectiveVerdict === 'UNCERTAIN' && <span>? UNCERTAIN</span>}
              {effectiveVerdict === 'PENDING_REVIEW' && <span>⏳ PENDING REVIEW</span>}
            </h3>
            <p>
              {effectiveVerdict === 'PASS' &&
                'Receiving matches the available photographic evidence and PO expectations deterministically.'}
              {effectiveVerdict === 'FAIL' &&
                'One or more receiving checks did not match PO expectations (e.g. shortage, damage, wrong variant).'}
              {effectiveVerdict === 'UNCERTAIN' &&
                'Available visual evidence is insufficient or ambiguous for a reliable automated decision.'}
              {effectiveVerdict === 'PENDING_REVIEW' &&
                'Automated inspection could not be completed (e.g. vision provider timeout). Operator review required.'}
            </p>
          </div>
          <div>
            <StatusBadge verdict={effectiveVerdict} size="lg" />
          </div>
        </div>
      )}

      {/* Expected vs Observed Comparison Panel */}
      <ComparisonPanel expected={inspection.expected} evidenceRecord={inspection.evidence_record} />

      {/* Individual Checks Breakdown */}
      {(inspection.evidence_record?.individual_checks || inspection.evidence_record?.checks) && (
        <ChecksBreakdown
          checks={inspection.evidence_record?.checks}
          individualChecks={inspection.evidence_record?.individual_checks}
          expected={inspection.expected}
          observed={inspection.evidence_record?.observed_values}
        />
      )}

      {/* Receiving Evidence & Hashes */}
      <EvidencePanel photoReferences={inspection.photo_references} />

      {/* Operator Override Modal */}
      {effectiveVerdict && (
        <OverrideModal
          isOpen={isOverrideOpen}
          onClose={() => setIsOverrideOpen(false)}
          originalVerdict={inspection.operator_override ? inspection.operator_override.original_verdict : effectiveVerdict}
          onSubmit={handleOverrideSubmit}
          isLoading={overrideLoading}
        />
      )}
    </div>
  );
};

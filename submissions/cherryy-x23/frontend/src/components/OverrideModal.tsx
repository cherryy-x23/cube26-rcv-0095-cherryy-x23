import React, { useState } from 'react';
import { OverrideVerdict, Verdict } from '../types/inspection';
import { StatusBadge } from './StatusBadge';

interface OverrideModalProps {
  isOpen: boolean;
  onClose: () => void;
  originalVerdict: Verdict;
  onSubmit: (overrideVerdict: OverrideVerdict, reason: string, operatorId: string) => Promise<void>;
  isLoading: boolean;
}

export const OverrideModal: React.FC<OverrideModalProps> = ({
  isOpen,
  onClose,
  originalVerdict,
  onSubmit,
  isLoading,
}) => {
  const [selectedVerdict, setSelectedVerdict] = useState<OverrideVerdict>('PASS');
  const [reason, setReason] = useState<string>('');
  const [operatorId, setOperatorId] = useState<string>('operator-lead-01');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) {
      setError('A comprehensive operator rationale is strictly required.');
      return;
    }
    setError(null);
    try {
      await onSubmit(selectedVerdict, reason.trim(), operatorId.trim());
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to submit operator override.');
    }
  };

  return (
    <div className="modal-overlay" data-testid="override-modal">
      <div className="modal-card">
        <div className="modal-header">
          <h3 className="modal-title">Operator Inspection Override</h3>
          <button
            onClick={onClose}
            disabled={isLoading}
            style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px', padding: '12px', background: '#f8fafc', borderRadius: '6px' }}>
            <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Original System Verdict:</div>
            <StatusBadge verdict={originalVerdict} />
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label className="form-label">
              New Operator Verdict <span className="req">*</span>
            </label>
            <div style={{ display: 'flex', gap: '16px', marginTop: '4px' }}>
              {(['PASS', 'FAIL', 'UNCERTAIN'] as OverrideVerdict[]).map((v) => (
                <label
                  key={v}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: 600,
                  }}
                >
                  <input
                    type="radio"
                    name="override_verdict"
                    value={v}
                    checked={selectedVerdict === v}
                    onChange={() => setSelectedVerdict(v)}
                    disabled={isLoading}
                  />
                  <span>{v}</span>
                </label>
              ))}
            </div>
            <div className="form-hint">PENDING_REVIEW is not permitted as a final human override.</div>
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label className="form-label" htmlFor="override-operator-id">
              Operator ID <span className="req">*</span>
            </label>
            <input
              id="override-operator-id"
              className="form-input"
              value={operatorId}
              onChange={(e) => setOperatorId(e.target.value)}
              placeholder="e.g. operator-lead-01"
              required
              disabled={isLoading}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label className="form-label" htmlFor="override-reason">
              Operator Rationale & Physical Verification Notes <span className="req">*</span>
            </label>
            <textarea
              id="override-reason"
              className="form-textarea"
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Hand-counted inner polybags; confirmed full 24 units arrived undamaged despite label tear."
              required
              disabled={isLoading}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              type="button"
              className="btn btn-outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isLoading || !reason.trim()}
              data-testid="submit-override-button"
            >
              {isLoading ? (
                <>
                  <span className="spinner" />
                  <span>Submitting Override...</span>
                </>
              ) : (
                'Submit Override'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

import React from 'react';
import { PhotoReference } from '../types/inspection';

interface EvidencePanelProps {
  photoReferences: PhotoReference[];
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ photoReferences }) => {
  if (!photoReferences || photoReferences.length === 0) {
    return (
      <div className="card">
        <div className="card-title">Receiving Evidence References</div>
        <p style={{ color: '#64748b', fontSize: '13px' }}>No photo references provided for this inspection.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">
        <span>Receiving Evidence References ({photoReferences.length})</span>
        <span style={{ fontSize: '12px', color: '#64748b' }}>Cryptographically verified when files exist locally</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
        {photoReferences.map((ref, idx) => (
          <div
            key={idx}
            style={{
              border: '1px solid #e2e8f0',
              borderRadius: '6px',
              padding: '14px',
              background: '#f8fafc',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 600, fontSize: '13px' }}>
                Photo Reference #{idx + 1}
              </span>
              {ref.photo_id && (
                <span className="font-mono" style={{ fontSize: '11px', color: '#64748b' }}>
                  {ref.photo_id}
                </span>
              )}
            </div>

            <div style={{ marginBottom: '8px' }}>
              <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
                File Path / Reference
              </div>
              <div className="font-mono" style={{ fontSize: '12.5px', wordBreak: 'break-all', color: '#0f172a' }}>
                {ref.path}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
                SHA-256 Digest
              </div>
              <div
                className="font-mono"
                style={{
                  fontSize: '11.5px',
                  wordBreak: 'break-all',
                  color: ref.sha256 ? '#0284c7' : '#94a3b8',
                }}
              >
                {ref.sha256 ? ref.sha256 : 'SHA-256: Not available (remote reference)'}
              </div>
            </div>

            {ref.notes && (
              <div style={{ marginTop: '8px', fontSize: '12px', color: '#475569' }}>
                <strong>Notes:</strong> {ref.notes}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

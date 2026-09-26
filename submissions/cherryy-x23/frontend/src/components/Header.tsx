import React from 'react';
import { useTenant } from '../context/TenantContext';

interface HeaderProps {
  title?: string;
}

export const Header: React.FC<HeaderProps> = ({ title = 'Inbound Receiving Inspection' }) => {
  const { currentOrg, apiConnected } = useTenant();

  return (
    <header className="top-header">
      <div className="header-title-area">
        <h1>{title}</h1>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div className="api-status">
          <span className={`status-dot ${apiConnected ? 'online' : 'offline'}`} />
          <span style={{ color: apiConnected ? '#15803d' : '#b91c1c', fontWeight: 600 }}>
            {apiConnected === null ? 'Connecting...' : apiConnected ? 'Backend Connected' : 'Backend Disconnected'}
          </span>
        </div>
        <div className="header-org-tag" title="Active Tenant Context">
          <span style={{ color: '#64748b' }}>Org:</span>
          <strong>{currentOrg}</strong>
        </div>
      </div>
    </header>
  );
};

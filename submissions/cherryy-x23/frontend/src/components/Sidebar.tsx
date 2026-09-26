import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTenant } from '../context/TenantContext';

export const Sidebar: React.FC = () => {
  const { currentOrg, setCurrentOrg, apiConnected, checkApiHealth } = useTenant();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-icon">01</div>
        <div>
          <div className="brand-title">Receiving Manager</div>
          <div className="brand-subtitle">CUBE Commerce Suite</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink
          to="/"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          end
        >
          <span>📊</span>
          <span>Dashboard</span>
        </NavLink>

        <NavLink
          to="/new-inspection"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <span>➕</span>
          <span>New Inspection</span>
        </NavLink>

        <NavLink
          to="/inspections"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <span>📦</span>
          <span>Inspections</span>
        </NavLink>

        <NavLink
          to="/pending"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <span>⏳</span>
          <span>Pending Review</span>
        </NavLink>

        <NavLink
          to="/history"
          className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
        >
          <span>📋</span>
          <span>History</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <div className="tenant-selector">
          <label htmlFor="tenant-select">
            Tenant Context <span style={{ color: '#94a3b8', fontSize: '10px' }}>(Demo)</span>
          </label>
          <select
            id="tenant-select"
            className="tenant-select"
            value={currentOrg}
            onChange={(e) => setCurrentOrg(e.target.value)}
          >
            <option value="org_demo_alpha">org_demo_alpha</option>
            <option value="org_demo_bravo">org_demo_bravo</option>
          </select>
          <div style={{ fontSize: '10px', color: '#64748b', marginTop: '4px' }}>
            Row-Level isolation enforced
          </div>
        </div>

        <div className="api-status" style={{ justifyContent: 'space-between', marginTop: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className={`status-dot ${apiConnected ? 'online' : 'offline'}`} />
            <span>{apiConnected ? 'API Online' : 'API Offline'}</span>
          </div>
          <button
            onClick={() => checkApiHealth()}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: '11px',
              textDecoration: 'underline',
            }}
            title="Refresh API Status"
          >
            Retry
          </button>
        </div>
      </div>
    </aside>
  );
};

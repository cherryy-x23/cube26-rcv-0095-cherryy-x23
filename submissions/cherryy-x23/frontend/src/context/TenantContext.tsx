import React, { createContext, useContext, useState, useEffect } from 'react';
import { inspectionApi } from '../api/inspectionApi';

interface TenantContextType {
  currentOrg: string;
  setCurrentOrg: (org: string) => void;
  apiConnected: boolean | null;
  checkApiHealth: () => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const TenantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentOrg, setCurrentOrg] = useState<string>('org_demo_alpha');
  const [apiConnected, setApiConnected] = useState<boolean | null>(null);

  const checkApiHealth = async () => {
    try {
      const health = await inspectionApi.getHealth();
      setApiConnected(health.status === 'ok');
    } catch {
      setApiConnected(false);
    }
  };

  useEffect(() => {
    checkApiHealth();
    const interval = setInterval(checkApiHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <TenantContext.Provider
      value={{
        currentOrg,
        setCurrentOrg,
        apiConnected,
        checkApiHealth,
      }}
    >
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = (): TenantContextType => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
};

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { TenantProvider } from './context/TenantContext';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { NewInspection } from './pages/NewInspection';
import { InspectionsList } from './pages/InspectionsList';
import { InspectionResult } from './pages/InspectionResult';
import { PendingReview } from './pages/PendingReview';
import { InspectionHistory } from './pages/InspectionHistory';

export const App: React.FC = () => {
  return (
    <TenantProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="dashboard" element={<Navigate to="/" replace />} />
            <Route path="new-inspection" element={<NewInspection />} />
            <Route path="inspections" element={<InspectionsList />} />
            <Route path="inspections/:inspectionId" element={<InspectionResult />} />
            <Route path="pending" element={<PendingReview />} />
            <Route path="history" element={<InspectionHistory />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </TenantProvider>
  );
};

export default App;

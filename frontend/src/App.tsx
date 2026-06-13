import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { useWebSocket } from './hooks/useWebSocket';
import './index.css';

// Lazy load pages
const LandingPage = lazy(() => import('./landing/LandingPage'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Assess = lazy(() => import('./pages/Assess'));
const Registry = lazy(() => import('./pages/Registry'));
const Deploy = lazy(() => import('./pages/Deploy'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Impact = lazy(() => import('./pages/Impact'));
const AI = lazy(() => import('./pages/AI'));
const Marketplace = lazy(() => import('./pages/Marketplace'));

const PageLoader = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
    <div className="assess__spinner-ring" style={{ width: 48, height: 48 }} />
  </div>
);

const AppLayout: React.FC = () => {
  const location = useLocation();
  const isLanding = location.pathname === '/';
  const { connected, lastEvent } = useWebSocket();

  if (isLanding) {
    return (
      <Suspense fallback={<PageLoader />}>
        <LandingPage />
      </Suspense>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar wsConnected={connected} />
      <main className="app-main">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/dashboard" element={<Dashboard lastEvent={lastEvent} />} />
            <Route path="/assess" element={<Assess lastEvent={lastEvent} />} />
            <Route path="/registry" element={<Registry />} />
            <Route path="/deploy" element={<Deploy />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/impact" element={<Impact />} />
            <Route path="/ai" element={<AI />} />
            <Route path="/marketplace" element={<Marketplace />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/*" element={<AppLayout />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;

import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, useLocation, Navigate } from 'react-router-dom';
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
const LoginPage = lazy(() => import('./pages/LoginPage'));
const SellerDashboard = lazy(() => import('./pages/SellerDashboard'));

const PageLoader = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
    <div className="assess__spinner-ring" style={{ width: 48, height: 48 }} />
  </div>
);

/** Role guard — blocks suppliers from buyer-only pages */
const BuyerOnly: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const hasSupplierToken = !!localStorage.getItem('supplier_token');
  if (hasSupplierToken) return <Navigate to="/seller-dashboard" replace />;
  return children;
};

/** Role guard — blocks buyers/anon from seller-only pages */
const SellerOnly: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const hasSupplierToken = !!localStorage.getItem('supplier_token');
  if (!hasSupplierToken) return <Navigate to="/login" replace />;
  return children;
};

const AppLayout: React.FC = () => {
  const location = useLocation();
  const isLanding = location.pathname === '/';
  const isLogin = location.pathname === '/login';
  const { connected, lastEvent } = useWebSocket();

  if (isLanding) {
    return (
      <Suspense fallback={<PageLoader />}>
        <LandingPage />
      </Suspense>
    );
  }

  // Login page renders without sidebar chrome
  if (isLogin) {
    return (
      <Suspense fallback={<PageLoader />}>
        <LoginPage />
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
            <Route path="/marketplace" element={
              <BuyerOnly><Marketplace lastEvent={lastEvent} /></BuyerOnly>
            } />
            <Route path="/seller-dashboard" element={
              <SellerOnly><SellerDashboard /></SellerOnly>
            } />
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

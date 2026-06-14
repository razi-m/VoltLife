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
const Marketplace = lazy(() => import('./pages/MarketplaceComingSoon'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
// const SellerDashboard = lazy(() => import('./pages/SellerDashboard'));

const PageLoader = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
    <div className="assess__spinner-ring" style={{ width: 48, height: 48 }} />
  </div>
);

/** Requires any session token — redirects to landing if not */
const RequireRole: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const hasRole = !!localStorage.getItem('supplier_token') ||
    !!localStorage.getItem('buyer_token');
  if (!hasRole) return <Navigate to="/" replace />;
  return children;
};

/** Seller-only guard — buyers get sent to marketplace */
const SellerOnly: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const isSupplier = !!localStorage.getItem('supplier_token');
  if (!isSupplier) return <Navigate to="/marketplace" replace />;
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

  if (isLogin) {
    return (
      <Suspense fallback={<PageLoader />}>
        <LoginPage />
      </Suspense>
    );
  }

  return (
    <RequireRole>
      <div className="app-layout">
        <Sidebar wsConnected={connected} />
        <main className="app-main">
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/dashboard" element={<SellerOnly><Dashboard lastEvent={lastEvent} /></SellerOnly>} />
              <Route path="/assess" element={<SellerOnly><Assess lastEvent={lastEvent} /></SellerOnly>} />
              <Route path="/registry" element={<SellerOnly><Registry /></SellerOnly>} />
              <Route path="/deploy" element={<SellerOnly><Deploy /></SellerOnly>} />
              <Route path="/analytics" element={<SellerOnly><Analytics /></SellerOnly>} />
              <Route path="/impact" element={<SellerOnly><Impact /></SellerOnly>} />
              <Route path="/ai" element={<AI />} />
              <Route path="/marketplace" element={<Marketplace lastEvent={lastEvent} />} />
              {/* <Route path="/seller-dashboard" element={<SellerOnly><SellerDashboard /></SellerOnly>} /> */}
            </Routes>
          </Suspense>
        </main>
      </div>
    </RequireRole>
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

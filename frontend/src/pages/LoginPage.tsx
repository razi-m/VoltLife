import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [role, setRole] = useState<'buyer' | 'supplier'>('buyer');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Clear any existing session token when entering login screen to prevent session pollution
  useEffect(() => {
    localStorage.removeItem('buyer_token');
    localStorage.removeItem('buyer_username');
    localStorage.removeItem('supplier_token');
    localStorage.removeItem('supplier_username');
    localStorage.removeItem('supplier_company');
  }, []);

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Username and password are required.');
      return;
    }

    setLoading(true);
    setError(null);

    const loginPayload = { username, password };
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const endpoint = role === 'buyer' ? '/api/v1/buyers/login' : '/api/v1/suppliers/login';

    try {
      const response = await fetch(`${apiBase}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginPayload)
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData?.error?.message || 'Login failed. Check credentials.');
      }

      const data = await response.json();

      if (role === 'buyer') {
        if (data.access_token) {
          localStorage.setItem('buyer_token', data.access_token);
          localStorage.setItem('buyer_username', data.buyer?.company_name || username);
          navigate('/marketplace');
        }
      } else {
        if (data.access_token) {
          localStorage.setItem('supplier_token', data.access_token);
          localStorage.setItem('supplier_username', username);
          localStorage.setItem('supplier_company', data.supplier?.company_name || 'Supplier Corp');
          navigate('/seller-dashboard');
        }
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during authentication.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (selectedRole: 'buyer' | 'supplier') => {
    const defaultUser = selectedRole === 'buyer' ? 'demo_buyer' : 'demo_supplier';
    const defaultPassword = 'password123';
    
    setRole(selectedRole);
    setUsername(defaultUser);
    setPassword(defaultPassword);
    
    // We run the login process after setting credentials.
    // React state updates are asynchronous, so we pass credentials directly to a helper to avoid state race conditions.
    setLoading(true);
    setError(null);

    const loginPayload = { username: defaultUser, password: defaultPassword };
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const endpoint = selectedRole === 'buyer' ? '/api/v1/buyers/login' : '/api/v1/suppliers/login';

    try {
      const response = await fetch(`${apiBase}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginPayload)
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData?.error?.message || 'Login failed. Run resets to re-seed.');
      }

      const data = await response.json();

      if (selectedRole === 'buyer') {
        if (data.access_token) {
          localStorage.setItem('buyer_token', data.access_token);
          localStorage.setItem('buyer_username', data.buyer?.company_name || defaultUser);
          navigate('/marketplace');
        }
      } else {
        if (data.access_token) {
          localStorage.setItem('supplier_token', data.access_token);
          localStorage.setItem('supplier_username', defaultUser);
          localStorage.setItem('supplier_company', data.supplier?.company_name || 'Supplier Corp');
          navigate('/seller-dashboard');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Quick login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-page__container card glassmorphism animate-fadeIn">
        <div className="login-page__header">
          <div className="login-page__logo">
            <span className="login-page__bolt">⚡</span>
            <span className="login-page__logo-text">VoltLife Gateway</span>
          </div>
          <p className="login-page__subtitle text-label-caps text-on-surface-variant">
            Identity &amp; Role-Based Access Control
          </p>
        </div>

        {/* Role Toggle Tabs */}
        <div className="login-page__role-tabs">
          <button
            type="button"
            className={`login-page__role-btn ${role === 'buyer' ? 'active' : ''}`}
            onClick={() => {
              setRole('buyer');
              setError(null);
            }}
          >
            🔋 Buyer Portal
          </button>
          <button
            type="button"
            className={`login-page__role-btn ${role === 'supplier' ? 'active' : ''}`}
            onClick={() => {
              setRole('supplier');
              setError(null);
            }}
          >
            🏭 Supplier Portal
          </button>
        </div>

        <form onSubmit={handleLogin} className="login-page__form">
          <div className="login-page__field">
            <label className="text-label-caps block mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="login-page__input"
              placeholder={role === 'buyer' ? 'e.g. demo_buyer' : 'e.g. demo_supplier'}
              required
            />
          </div>

          <div className="login-page__field">
            <label className="text-label-caps block mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="login-page__input"
              placeholder="••••••••"
              required
            />
          </div>

          {error && <p className="login-page__error text-body-sm text-red-400">{error}</p>}

          <button
            type="submit"
            className="login-page__submit-btn"
            disabled={loading}
          >
            {loading ? 'AUTHENTICATING...' : `Access ${role === 'buyer' ? 'Marketplace' : 'Seller Panel'} →`}
          </button>
        </form>

        <div className="login-page__divider">
          <span>OR USE DEMO ACCOUNT</span>
        </div>

        <div className="login-page__quick-login-grid">
          <button
            type="button"
            onClick={() => handleQuickLogin('buyer')}
            className="login-page__quick-btn login-page__quick-btn--buyer"
            disabled={loading}
          >
            ⚡ Quick Buyer Login
            <span className="text-xs text-on-surface-variant block mt-1 font-mono">demo_buyer / password123</span>
          </button>
          <button
            type="button"
            onClick={() => handleQuickLogin('supplier')}
            className="login-page__quick-btn login-page__quick-btn--supplier"
            disabled={loading}
          >
            ⚡ Quick Supplier Login
            <span className="text-xs text-on-surface-variant block mt-1 font-mono">demo_supplier / password123</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

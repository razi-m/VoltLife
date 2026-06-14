import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { Card, MetricCard } from '../components/ui/Card';
import { GradeBadge } from '../components/ui/Badge';
import './SellerDashboard.css';

interface DashboardStats {
  active_lots_count: number;
  completed_orders_count: number;
  pending_orders_count: number;
  total_revenue_rupees: number;
  available_batteries: number;
}

interface InventoryLotItem {
  id: number;
  grade: string;
  chemistry: string;
  available_quantity: number;
  capacity_per_battery_kwh: number;
  total_capacity_kwh: number;
  avg_soh: number;
  avg_rul_years: number;
  status: string;
  created_at: string;
  listing: {
    id: number | null;
    title: string;
    description: string;
    moq: number;
    is_published: boolean;
  } | null;
  pricing_tiers: { min_quantity: number; price_per_kwh: number }[];
}

interface OrderItem {
  id: number;
  quantity: number;
  total_price: number;
  payment_status: string;
  tracking_status: string;
  created_at: string;
  buyer: {
    company_name: string;
    email: string;
  };
  lot: {
    id: number;
    grade: string;
    chemistry: string;
  };
}

interface RequirementItem {
  id: number;
  use_case_text: string;
  parsed_grade: string | null;
  parsed_capacity_kwh: number | null;
  parsed_quantity: number | null;
  created_at: string;
  buyer: {
    company_name: string;
  };
}

const SellerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(localStorage.getItem('supplier_token'));
  const [companyName, setCompanyName] = useState<string | null>(localStorage.getItem('supplier_company'));
  const [activeTab, setActiveTab] = useState<'inventory' | 'orders' | 'requirements'>('inventory');

  // Dashboard Data
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [inventory, setInventory] = useState<InventoryLotItem[]>([]);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [requirements, setRequirements] = useState<RequirementItem[]>([]);

  // Subscription States
  const [subStatus, setSubStatus] = useState<{ status: string; plan_name: string | null; expires_at: string | null } | null>(null);
  const [plans, setPlans] = useState<any[]>([]);
  const [activeSubscribingPlan, setActiveSubscribingPlan] = useState<string | null>(null);
  const [paymentSession, setPaymentSession] = useState<{ session_id: string; amount_paise: number; key_id: string; is_mock: boolean } | null>(null);
  const [paymentSubmitting, setPaymentSubmitting] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);

  // Loading / Error states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Publish Modal State
  const [publishingLot, setPublishingLot] = useState<InventoryLotItem | null>(null);
  const [moqInput, setMoqInput] = useState<number>(1);
  const [descriptionInput, setDescriptionInput] = useState('');
  const [priceInput, setPriceInput] = useState<number>(100);
  const [modalSubmitting, setModalSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Auth Guard redirect
  useEffect(() => {
    if (!token) {
      navigate('/login');
    }
  }, [token, navigate]);

  // Fetch all dashboard data
  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch Subscription Status First
      const subRes = await api.subscriptions.status(token);
      setSubStatus(subRes);
      
      if (subRes.status === 'active') {
        const [statsRes, invRes, ordRes, reqsRes] = await Promise.all([
          api.suppliers.dashboardStats(token),
          api.suppliers.dashboardInventory(token),
          api.suppliers.dashboardOrders(token),
          api.suppliers.dashboardRequirements(token),
        ]);
        setStats(statsRes);
        setInventory(invRes);
        setOrders(ordRes);
        setRequirements(reqsRes);
      } else {
        // Fetch plans to display
        const plansRes = await api.subscriptions.plans();
        setPlans(plansRes);
      }
    } catch (err: any) {
      console.error('Failed to load supplier dashboard data:', err);
      if (err.status === 403 && err.code === 'subscription_required') {
        setSubStatus({ status: 'inactive', plan_name: null, expires_at: null });
        try {
          const plansRes = await api.subscriptions.plans();
          setPlans(plansRes);
        } catch (planErr) {
          console.error('Failed to load plans:', planErr);
        }
      } else {
        setError(err.message || 'Error loading dashboard. Verify authorization.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  // Razorpay Dynamic SDK Trigger
  const triggerRealRazorpay = (planName: string, session: { session_id: string; amount_paise: number; key_id: string }) => {
    return new Promise<void>((resolve, reject) => {
      const scriptId = 'razorpay-checkout-script';
      let script = document.getElementById(scriptId) as HTMLScriptElement;
      
      const openCheckout = () => {
        const options = {
          key: session.key_id,
          amount: session.amount_paise,
          currency: 'INR',
          name: 'VoltLife Battery SaaS',
          description: `${planName} Subscription Plan`,
          order_id: session.session_id,
          handler: async (response: any) => {
            try {
              setLoading(true);
              await api.subscriptions.verify({
                plan_name: planName,
                session_id: session.session_id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
              }, token!);
              setPaymentSession(null);
              setActiveSubscribingPlan(null);
              fetchData();
              resolve();
            } catch (verifyErr: any) {
              setPaymentError(verifyErr.message || 'Signature verification failed.');
              reject(verifyErr);
            } finally {
              setLoading(false);
            }
          },
          prefill: {
            name: companyName || 'VoltLife Seller',
            email: 'supplier@demovolt.com'
          },
          theme: {
            color: '#2563eb'
          },
          modal: {
            ondismiss: () => {
              setPaymentSession(null);
              setActiveSubscribingPlan(null);
              reject(new Error('Checkout cancelled by user.'));
            }
          }
        };
        const rzp = new (window as any).Razorpay(options);
        rzp.open();
      };

      if (!script) {
        script = document.createElement('script');
        script.id = scriptId;
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.onload = () => {
          openCheckout();
        };
        script.onerror = () => {
          reject(new Error('Failed to load Razorpay SDK.'));
        };
        document.body.appendChild(script);
      } else {
        openCheckout();
      }
    });
  };

  const handleSubscribeInit = async (planName: string) => {
    if (!token) return;
    setActiveSubscribingPlan(planName);
    setPaymentSubmitting(true);
    setPaymentError(null);
    try {
      const session = await api.subscriptions.createSession(planName, token);
      setPaymentSession(session);
      
      // If it's a real Razorpay session, trigger it (already starts in background)
      if (!session.is_mock) {
        await triggerRealRazorpay(planName, session);
      }
    } catch (err: any) {
      console.error('Failed to initiate subscription:', err);
      setPaymentError(err.message || 'Failed to initiate payment session. Please try again.');
      setActiveSubscribingPlan(null);
    } finally {
      setPaymentSubmitting(false);
    }
  };

  const handleConfirmMockSubscription = async () => {
    if (!token || !paymentSession || !activeSubscribingPlan) return;
    setLoading(true);
    setPaymentError(null);
    try {
      await api.subscriptions.verify({
        plan_name: activeSubscribingPlan,
        session_id: paymentSession.session_id
      }, token);
      setPaymentSession(null);
      setActiveSubscribingPlan(null);
      fetchData();
    } catch (err: any) {
      console.error('Failed to confirm mock subscription:', err);
      setPaymentError(err.message || 'Failed to verify subscription. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!token) return;
    if (!window.confirm("WARNING: Are you sure you want to force-expire the SaaS subscription for testing? This will lock the dashboard.")) return;
    setLoading(true);
    try {
      await api.subscriptions.cancel(token);
      fetchData();
    } catch (err: any) {
      console.error('Failed to cancel subscription:', err);
      alert(err.message || 'Failed to cancel subscription.');
      setLoading(false);
    }
  };


  const handleLogout = () => {
    localStorage.removeItem('supplier_token');
    localStorage.removeItem('supplier_username');
    localStorage.removeItem('supplier_company');
    setToken(null);
    setCompanyName(null);
    navigate('/login');
  };

  // Open Publish Modal with defaults
  const openPublishModal = (lot: InventoryLotItem) => {
    setPublishingLot(lot);
    setMoqInput(lot.listing?.moq || 1);
    setDescriptionInput(lot.listing?.description || '');
    setPriceInput(lot.pricing_tiers?.[0]?.price_per_kwh || 100);
    setModalError(null);
  };

  // Submit configuration and publish
  const handlePublishSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!publishingLot || !token) return;

    setModalSubmitting(true);
    setModalError(null);
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    try {
      // 1. Configure listing details
      const listingResp = await fetch(`${apiBase}/api/v1/suppliers/inventory/lots/${publishingLot.id}/listing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ moq: moqInput, description: descriptionInput })
      });
      if (!listingResp.ok) throw new Error('Failed to configure listing metadata.');

      // 2. Configure pricing tiers (using a single basic tier)
      const pricingResp = await fetch(`${apiBase}/api/v1/suppliers/inventory/lots/${publishingLot.id}/pricing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          tiers: [{ min_quantity: 1, price_per_kwh: priceInput }]
        })
      });
      if (!pricingResp.ok) throw new Error('Failed to configure pricing tiers.');

      // 3. Publish the listing
      const publishResp = await fetch(`${apiBase}/api/v1/suppliers/inventory/lots/${publishingLot.id}/publish?publish=true`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!publishResp.ok) throw new Error('Failed to publish listing.');

      // Success: refresh dashboard data and close modal
      setPublishingLot(null);
      fetchData();
    } catch (err: any) {
      setModalError(err.message || 'Error occurred during listing publishing.');
    } finally {
      setModalSubmitting(false);
    }
  };

  if (!token) return null;

  return (
    <div className="seller-dashboard page-content">
      {/* Header Panel */}
      <div className="page-header seller-dashboard__header">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="page-title">{companyName || 'Supplier Portal'}</h1>
            <span className="seller-dashboard__verified-badge">VoltLife Verified Seller</span>
            {subStatus?.status === 'active' && (
              <span className="seller-dashboard__sub-badge">
                Active: {subStatus.plan_name} Plan (Expires: {subStatus.expires_at ? new Date(subStatus.expires_at).toLocaleDateString() : 'N/A'})
              </span>
            )}
          </div>
          <p className="text-body-sm text-on-surface-variant style-caps" style={{ marginTop: 4 }}>
            SUPPLIER CONSOLE • REAL-TIME ASSET &amp; INVENTORY DISTRIBUTION
          </p>
        </div>
        <div className="flex items-center gap-4">
          {subStatus?.status === 'active' && (
            <button 
              onClick={handleCancelSubscription} 
              className="seller-dashboard__cancel-sub-btn text-label-caps"
            >
              ⚠️ Force Expire Sub
            </button>
          )}
          <button onClick={handleLogout} className="seller-dashboard__logout-btn text-label-caps">
            🚪 Logout
          </button>
        </div>
      </div>

      {loading && !stats && !subStatus ? (
        <div className="seller-dashboard__loading">
          <div className="assess__spinner-ring" style={{ width: 48, height: 48 }} />
          <p className="text-body-sm text-on-surface-variant mt-4">Retrieving ledger details...</p>
        </div>
      ) : error ? (
        <div className="seller-dashboard__error card p-6 border border-red-500">
          <h3 className="text-headline-sm text-red-400 mb-2">Sync Connection Error</h3>
          <p className="text-body-sm text-on-surface-variant mb-4">{error}</p>
          <button onClick={fetchData} className="seller-dashboard__btn-primary">Retry Sync</button>
        </div>
      ) : subStatus?.status !== 'active' ? (
        <div className="seller-dashboard__sub-required animate-fadeIn">
          <div className="seller-dashboard__sub-locked-banner card p-6 mb-8 text-center">
            <h2 className="text-headline-sm text-primary mb-2">⚡ Workspace Locked: SaaS Subscription Required</h2>
            <p className="text-body-sm text-on-surface-variant max-w-2xl mx-auto">
              SaaS subscription gates access to the seller workspace (dashboard metrics, battery uploads, listings publishing, and market demand feed). VoltLife takes <strong>zero commissions</strong> or transaction cuts on battery sales.
            </p>
            {subStatus?.status === 'expired' && (
              <div className="seller-dashboard__expired-banner mt-3">
                ⚠️ Your previous subscription has expired. Please renew to restore access.
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {plans.map((plan) => (
              <div key={plan.name} className={`pricing-card card p-6 flex flex-col justify-between ${plan.name.toLowerCase() === 'annual' ? 'pricing-card--featured' : ''}`}>
                <div>
                  <div className="pricing-card__header mb-4">
                    <h3 className="text-headline-sm text-primary">{plan.name} Plan</h3>
                    <div className="pricing-card__price mt-2">
                      <span className="text-headline-lg font-bold text-secondary">₹{plan.price_rupees.toLocaleString()}</span>
                      <span className="text-xs text-on-surface-variant"> / {plan.name === 'Annual' ? 'year' : plan.name === 'Enterprise' ? 'year' : 'month'}</span>
                    </div>
                  </div>
                  <p className="text-body-xs text-on-surface-variant mb-6">{plan.description}</p>
                  <ul className="pricing-card__features space-y-2 mb-6">
                    <li className="text-body-sm text-on-surface flex items-center gap-2">✓ Telemetry uploads &amp; AI auto-grading</li>
                    <li className="text-body-sm text-on-surface flex items-center gap-2">✓ Dynamic quantity pricing tiers</li>
                    <li className="text-body-sm text-on-surface flex items-center gap-2">✓ Match with active buyer requirements</li>
                    <li className="text-body-sm text-on-surface flex items-center gap-2">✓ Zero marketplace transaction commissions</li>
                    {plan.name === 'Enterprise' && (
                      <li className="text-body-sm text-secondary font-bold flex items-center gap-2">✓ Dedicated offline account manager</li>
                    )}
                  </ul>
                </div>
                
                <button
                  onClick={() => handleSubscribeInit(plan.name)}
                  disabled={activeSubscribingPlan !== null}
                  className="seller-dashboard__subscribe-btn text-label-caps"
                >
                  {activeSubscribingPlan === plan.name ? 'Processing...' : `Subscribe ${plan.name}`}
                </button>
              </div>
            ))}
          </div>

          {/* Developer Mock Control for checkout */}
          {paymentSession?.is_mock && (
            <div className="seller-dashboard__mock-overlay animate-fadeIn">
              <div className="seller-dashboard__mock-modal card p-6 text-center max-w-md mx-auto">
                <h3 className="text-headline-sm text-primary mb-2">💳 Simulated Payment</h3>
                <p className="text-body-sm text-on-surface-variant mb-4">
                  Demo Mode is active. Complete subscription purchase using simulation.
                </p>
                <div className="seller-dashboard__mock-details p-3 text-left font-mono text-xs mb-4">
                  <div>PLAN: {activeSubscribingPlan}</div>
                  <div>AMOUNT: ₹{(paymentSession.amount_paise / 100).toLocaleString()}</div>
                  <div className="seller-dashboard__mock-session">SESSION: {paymentSession.session_id}</div>
                </div>
                {paymentError && (
                  <p className="text-red-400 text-xs mb-3">{paymentError}</p>
                )}
                <div className="flex gap-3 justify-center">
                  <button
                    onClick={() => { setPaymentSession(null); setActiveSubscribingPlan(null); }}
                    className="seller-dashboard__mock-btn-sec text-label-caps"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmMockSubscription}
                    className="seller-dashboard__mock-btn-pri text-label-caps"
                  >
                    Confirm Demo Purchase
                  </button>
                </div>
              </div>
            </div>
          )}

          {paymentError && !paymentSession && (
            <p className="text-red-400 text-center mt-4">{paymentError}</p>
          )}
        </div>
      ) : (
        <div className="animate-fadeIn">
          {/* Metric KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            <MetricCard 
              label="Active Listed Lots" 
              value={stats?.active_lots_count ?? 0} 
              icon="🏭" 
              color="var(--primary)" 
            />
            <MetricCard 
              label="Available Batteries" 
              value={stats?.available_batteries ?? 0} 
              icon="🔋" 
              color="var(--color-info, var(--primary))" 
            />
            <MetricCard 
              label="Active Shipments" 
              value={stats?.pending_orders_count ?? 0} 
              icon="🚚" 
              color="var(--color-warning)" 
            />
            <MetricCard 
              label="Fulfilled Orders" 
              value={stats?.completed_orders_count ?? 0} 
              icon="✓" 
              color="var(--color-success)" 
            />
            <div className="metric-card metric-card--glow" style={{ borderLeft: '2px solid var(--secondary)' }}>
              <div className="metric-card__header">
                <span className="metric-card__icon">💰</span>
                <span className="text-label-caps">Cumulative Revenue</span>
              </div>
              <div className="metric-card__value">
                <span className="text-data-lg text-secondary">
                  ₹{(stats?.total_revenue_rupees ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="text-label-caps" style={{ color: 'var(--secondary)', fontSize: 10, marginTop: 4 }}>
                SETTLED IN INR VALUATIONS
              </div>
            </div>
          </div>

          {/* Sub Navigation Tabs */}
          <div className="seller-dashboard__tabs mb-6">
            <button
              onClick={() => setActiveTab('inventory')}
              className={`seller-dashboard__tab-btn ${activeTab === 'inventory' ? 'active' : ''}`}
            >
              📦 My Inventory Stock
            </button>
            <button
              onClick={() => setActiveTab('orders')}
              className={`seller-dashboard__tab-btn ${activeTab === 'orders' ? 'active' : ''}`}
            >
              📥 Received Order Log
            </button>
            <button
              onClick={() => setActiveTab('requirements')}
              className={`seller-dashboard__tab-btn ${activeTab === 'requirements' ? 'active' : ''}`}
            >
              💡 Active Buyer Requirements
            </button>
          </div>

          {/* Workspace Content */}
          <div className="seller-dashboard__workspace">
            {activeTab === 'inventory' && (
              /* --- MY INVENTORY STOCK --- */
              <Card className="seller-dashboard__panel">
                <div className="seller-dashboard__panel-header">
                  <h3 className="text-headline-sm">Inventory Monitor</h3>
                  <span className="text-label-caps text-on-surface-variant">All assessed pack lots</span>
                </div>
                {inventory.length === 0 ? (
                  <div className="seller-dashboard__empty">
                    <p className="text-body-sm text-on-surface-variant">No battery lots uploaded yet.</p>
                    <p className="text-xs text-on-surface-variant/70 mt-1">Upload files under Battery Intake to auto-grade inventory lots.</p>
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="seller-dashboard__table">
                      <thead>
                        <tr>
                          <th className="text-label-caps">Lot ID</th>
                          <th className="text-label-caps">Grade</th>
                          <th className="text-label-caps">Chemistry</th>
                          <th className="text-label-caps text-right">Available Qty</th>
                          <th className="text-label-caps text-right">Per Battery</th>
                          <th className="text-label-caps text-right">Total Capacity</th>
                          <th className="text-label-caps text-right">Avg SoH</th>
                          <th className="text-label-caps text-right">Avg RUL</th>
                          <th className="text-label-caps">Status</th>
                          <th className="text-label-caps">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {inventory.map((lot) => (
                          <tr key={lot.id}>
                            <td className="text-data-md font-bold">#{lot.id}</td>
                            <td><GradeBadge grade={lot.grade} /></td>
                            <td className="text-data-md">{lot.chemistry}</td>
                            <td className="text-data-md text-right">{lot.available_quantity} packs</td>
                            <td className="text-data-md text-right">{lot.capacity_per_battery_kwh.toFixed(2)} kWh</td>
                            <td className="text-data-md text-right">{lot.total_capacity_kwh.toFixed(1)} kWh</td>
                            <td className="text-data-md text-right text-secondary">{lot.avg_soh.toFixed(1)}%</td>
                            <td className="text-data-md text-right">{lot.avg_rul_years.toFixed(1)} yrs</td>
                            <td>
                              <span className={`seller-dashboard__status-tag status-${lot.status}`}>
                                {lot.status.replace('_', ' ').toUpperCase()}
                              </span>
                            </td>
                            <td>
                              {lot.available_quantity === 0 ? (
                                <span className="text-xs text-on-surface-variant italic">Sold Out</span>
                              ) : lot.status === 'draft' ? (
                                <button
                                  onClick={() => openPublishModal(lot)}
                                  className="seller-dashboard__action-btn"
                                >
                                  Publish Listing
                                </button>
                              ) : (
                                <button
                                  onClick={() => openPublishModal(lot)}
                                  className="seller-dashboard__action-btn btn-outline"
                                >
                                  Configure Pricing
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            )}

            {activeTab === 'orders' && (
              /* --- RECEIVED ORDERS LOG --- */
              <Card className="seller-dashboard__panel">
                <div className="seller-dashboard__panel-header">
                  <h3 className="text-headline-sm">Received Orders</h3>
                  <span className="text-label-caps text-on-surface-variant">Incoming procurement requests</span>
                </div>
                {orders.length === 0 ? (
                  <div className="seller-dashboard__empty">
                    <p className="text-body-sm text-on-surface-variant">No orders received yet.</p>
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="seller-dashboard__table">
                      <thead>
                        <tr>
                          <th className="text-label-caps">Order ID</th>
                          <th className="text-label-caps">Customer Company</th>
                          <th className="text-label-caps">Battery Specifications</th>
                          <th className="text-label-caps text-right">Quantity</th>
                          <th className="text-label-caps text-right">Total Price</th>
                          <th className="text-label-caps">Payment Status</th>
                          <th className="text-label-caps">Tracking Status</th>
                          <th className="text-label-caps">Order Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {orders.map((o) => (
                          <tr key={o.id}>
                            <td className="text-data-md font-bold">#{o.id}</td>
                            <td>
                              <div className="font-bold">{o.buyer.company_name}</div>
                              <div className="text-xs text-on-surface-variant">{o.buyer.email}</div>
                            </td>
                            <td>
                              <span className="font-bold text-primary">Lot #{o.lot.id}</span>
                              <span className="text-xs text-on-surface-variant block">Grade {o.lot.grade} • {o.lot.chemistry}</span>
                            </td>
                            <td className="text-data-md text-right">{o.quantity} units</td>
                            <td className="text-data-md text-right font-bold text-secondary">
                              ₹{o.total_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </td>
                            <td>
                              <span className={`seller-dashboard__payment-badge payment-${o.payment_status}`}>
                                {o.payment_status.toUpperCase()}
                              </span>
                            </td>
                            <td>
                              <span className={`seller-dashboard__tracking-badge tracking-${o.tracking_status}`}>
                                {o.tracking_status.replace('_', ' ').toUpperCase()}
                              </span>
                            </td>
                            <td className="text-data-md">
                              {new Date(o.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            )}

            {activeTab === 'requirements' && (
              /* --- MARKET DEMAND FEED --- */
              <Card className="seller-dashboard__panel">
                <div className="seller-dashboard__panel-header">
                  <h3 className="text-headline-sm">Market Demand</h3>
                  <span className="text-label-caps text-on-surface-variant">Active buyer queries in the system</span>
                </div>
                {requirements.length === 0 ? (
                  <div className="seller-dashboard__empty">
                    <p className="text-body-sm text-on-surface-variant">No active buyer requirements found.</p>
                  </div>
                ) : (
                  <div className="seller-dashboard__requirements-feed">
                    {requirements.map((req) => (
                      <div key={req.id} className="seller-dashboard__req-card">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="text-label-caps block text-outline-variant">Requirement ID: #{req.id}</span>
                            <span className="font-bold text-body-lg text-primary">{req.buyer.company_name}</span>
                          </div>
                          <span className="text-xs text-on-surface-variant font-mono">
                            {new Date(req.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-body-sm text-on-surface mb-3 italic">
                          "{req.use_case_text}"
                        </p>
                        <div className="grid grid-cols-3 gap-2 bg-surface-container-lowest p-2 rounded text-body-sm">
                          <div>
                            <span className="text-label-caps text-on-surface-variant block mb-1">Target Grade</span>
                            <span className="font-bold text-secondary">{req.parsed_grade || 'Any'}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block mb-1">Capacity Goal</span>
                            <span className="font-bold">{req.parsed_capacity_kwh ? `${req.parsed_capacity_kwh} kWh` : 'Any'}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block mb-1">Quantity Requested</span>
                            <span className="font-bold">{req.parsed_quantity ? `${req.parsed_quantity} packs` : 'Any'}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Configure Listing & Publish Modal */}
      {publishingLot && (
        <div className="seller-dashboard__modal-overlay animate-fadeIn">
          <div className="seller-dashboard__modal card glassmorphism animate-scaleUp">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-outline-variant">
              <h3 className="text-headline-sm text-primary">
                Configure Lot #{publishingLot.id}
              </h3>
              <button 
                onClick={() => setPublishingLot(null)} 
                className="seller-dashboard__modal-close"
              >
                ×
              </button>
            </div>
            
            <form onSubmit={handlePublishSubmit} className="seller-dashboard__modal-form">
              <div className="seller-dashboard__form-group">
                <label className="text-label-caps block mb-1">Minimum Order Quantity (MOQ)</label>
                <input
                  type="number"
                  min="1"
                  max={publishingLot.available_quantity}
                  value={moqInput}
                  onChange={(e) => setMoqInput(Math.max(1, Number(e.target.value)))}
                  className="seller-dashboard__form-input"
                  required
                />
                <span className="text-xs text-on-surface-variant mt-1 block">
                  Available packs: {publishingLot.available_quantity}
                </span>
              </div>

              <div className="seller-dashboard__form-group">
                <label className="text-label-caps block mb-1">Price per kWh (in ₹)</label>
                <input
                  type="number"
                  min="1"
                  value={priceInput}
                  onChange={(e) => setPriceInput(Math.max(1, Number(e.target.value)))}
                  className="seller-dashboard__form-input"
                  required
                />
              </div>

              <div className="seller-dashboard__form-group">
                <label className="text-label-caps block mb-1">Listing Description</label>
                <textarea
                  placeholder="Describe your inventory lot (e.g. chemical composition, optimal deployments, SOH warranty)..."
                  value={descriptionInput}
                  onChange={(e) => setDescriptionInput(e.target.value)}
                  rows={3}
                  className="seller-dashboard__form-textarea"
                  required
                />
              </div>

              {modalError && (
                <p className="text-body-sm text-red-400 text-center">{modalError}</p>
              )}

              <div className="flex gap-3 justify-end mt-4">
                <button
                  type="button"
                  onClick={() => setPublishingLot(null)}
                  className="seller-dashboard__modal-btn-sec text-label-caps"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalSubmitting}
                  className="seller-dashboard__modal-btn-pri text-label-caps"
                >
                  {modalSubmitting ? 'PUBLISHING...' : 'CONFIRM & PUBLISH'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SellerDashboard;

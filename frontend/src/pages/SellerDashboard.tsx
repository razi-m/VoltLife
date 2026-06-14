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
    } catch (err: any) {
      console.error('Failed to load supplier dashboard data:', err);
      setError(err.message || 'Error loading dashboard. Verify authorization.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

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
          </div>
          <p className="text-body-sm text-on-surface-variant style-caps" style={{ marginTop: 4 }}>
            SUPPLIER CONSOLE • REAL-TIME ASSET &amp; INVENTORY DISTRIBUTION
          </p>
        </div>
        <button onClick={handleLogout} className="seller-dashboard__logout-btn text-label-caps">
          🚪 Logout
        </button>
      </div>

      {loading && !stats ? (
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

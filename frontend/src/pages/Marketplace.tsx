import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Card, MetricCard } from '../components/ui/Card';
import type { WSEvent } from '../lib/types';
import './Marketplace.css';

interface LotItem {
  id: string;
  title: string;
  price: string;
  units: string;
  origin: string;
  avg_soh: string;
  avg_rul_years: number;
  moq: number;
  grade: string;
  chemistry: string;
  total_capacity_kwh: number;
  available_quantity: number;
  description: string;
  certification: string;
  img_alt: string;
  img_url: string;
  supplier_id: number;
  pricing_tiers: { min_quantity: number; price_per_kwh: number }[];
}

interface SummaryStats {
  total_asset_value: string;
  auctions_count: number;
  recently_sold: number;
  second_life_index: number;
}

interface SupplierItem {
  id: number;
  company_name: string;
  email: string;
  phone: string;
  address: string;
}

// Indian states with supplier presence (for buyer map view)
const INDIA_STATES: { name: string; x: number; y: number; suppliers: number; state: string }[] = [
  { name: 'Delhi NCR', x: 148, y: 108, suppliers: 3, state: 'Delhi' },
  { name: 'Mumbai', x: 88, y: 205, suppliers: 5, state: 'Maharashtra' },
  { name: 'Pune', x: 100, y: 220, suppliers: 4, state: 'Maharashtra' },
  { name: 'Bangalore', x: 115, y: 285, suppliers: 6, state: 'Karnataka' },
  { name: 'Chennai', x: 145, y: 280, suppliers: 3, state: 'Tamil Nadu' },
  { name: 'Hyderabad', x: 130, y: 240, suppliers: 4, state: 'Telangana' },
  { name: 'Kolkata', x: 195, y: 170, suppliers: 2, state: 'West Bengal' },
  { name: 'Ahmedabad', x: 78, y: 170, suppliers: 3, state: 'Gujarat' },
  { name: 'Jaipur', x: 118, y: 140, suppliers: 2, state: 'Rajasthan' },
  { name: 'Lucknow', x: 160, y: 130, suppliers: 1, state: 'Uttar Pradesh' },
];

interface MarketplaceProps {
  lastEvent: WSEvent | null;
}

const Marketplace: React.FC<MarketplaceProps> = ({ lastEvent }) => {
  const isSupplier = !!localStorage.getItem('supplier_token');
  const isBuyer = !isSupplier;

  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [lots, setLots] = useState<LotItem[]>([]);
  const [suppliers, setSuppliers] = useState<SupplierItem[]>([]);
  const [selectedSupplierId, setSelectedSupplierId] = useState<number | null>(null);
  const [selectedSupplier, setSelectedSupplier] = useState<SupplierItem | null>(null);
  const [selectedCity, setSelectedCity] = useState<string | null>(null);

  // Filters
  const [gradeFilter, setGradeFilter] = useState<string>('');
  const [chemFilter, setChemFilter] = useState<string>('');
  const [minCapacity, setMinCapacity] = useState<number | ''>('');
  const [reqQuantity, setReqQuantity] = useState<number | ''>('');

  // Quote
  const [showQuoteLotId, setShowQuoteLotId] = useState<string | null>(null);
  const [quoteQtyInput, setQuoteQtyInput] = useState<number>(1);

  // Buyer session
  const [buyerToken] = useState<string | null>(localStorage.getItem('buyer_token'));

  // Quotes & Orders
  const [activeTab, setActiveTab] = useState<'store' | 'quotes_orders'>('store');
  const [quotes, setQuotes] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);
  const [trackingData, setTrackingData] = useState<any | null>(null);
  const [trackingLoading, setTrackingLoading] = useState(false);

  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' } | null>(null);

  const fetchData = async () => {
    try {
      const sumRes = await api.marketplace.summary();
      setSummary(sumRes);
    } catch (err) {
      console.error('Failed to load marketplace summary:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStoreData = async () => {
    try {
      const params: any = {};
      if (gradeFilter) params.grade_filter = gradeFilter;
      if (chemFilter) params.chemistry_filter = chemFilter;
      if (selectedSupplierId) params.supplier_id = selectedSupplierId;

      const [lotsRes, suppsRes] = await Promise.all([
        api.marketplace.lots(params),
        api.marketplace.suppliers(),
      ]);

      let filteredLots = lotsRes;
      if (selectedCity) {
        filteredLots = filteredLots.filter((lot: any) =>
          lot.origin.toLowerCase().includes(selectedCity.toLowerCase())
        );
      }
      if (minCapacity) {
        filteredLots = filteredLots.filter((lot: any) =>
          lot.total_capacity_kwh >= Number(minCapacity)
        );
      }
      if (reqQuantity) {
        filteredLots = filteredLots.filter((lot: any) =>
          lot.available_quantity >= Number(reqQuantity)
        );
      }

      setLots(filteredLots);
      setSuppliers(suppsRes);
    } catch (err) {
      console.error('Failed to load store data:', err);
    }
  };

  const fetchQuotesAndOrders = async () => {
    if (!buyerToken) return;
    try {
      const [quotesRes, ordersRes] = await Promise.all([
        api.quotes.list(buyerToken),
        api.payments.orders(buyerToken)
      ]);
      setQuotes(quotesRes);
      setOrders(ordersRes);
    } catch (err) {
      console.error('Failed to load quotes/orders:', err);
    }
  };

  const fetchTracking = async (orderId: number) => {
    if (!buyerToken) return;
    setTrackingLoading(true);
    try {
      const data = await api.logistics.tracking(orderId, buyerToken);
      setTrackingData(data);
    } catch (err) {
      console.error('Failed to load tracking:', err);
    } finally {
      setTrackingLoading(false);
    }
  };

  const handleConfirmQuote = async (lotId: string) => {
    if (!buyerToken) return;
    try {
      const cleanLotId = lotId.startsWith('lot-') ? Number(lotId.replace('lot-', '')) : Number(lotId);
      await api.quotes.create(cleanLotId, quoteQtyInput, buyerToken);
      showToast('Quote requested successfully!', 'success');
      setShowQuoteLotId(null);
      setActiveTab('quotes_orders');
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Failed to create quote.', 'info');
    }
  };

  const handleCheckout = async (quoteId: number) => {
    if (!buyerToken) return;
    showToast('Initiating checkout...', 'info');
    try {
      const session = await api.payments.checkoutSession(quoteId, buyerToken);
      const order = await api.payments.mockConfirm(session.session_id, buyerToken);
      showToast(`Payment confirmed! Order #${order.id} created.`, 'success');
      fetchQuotesAndOrders();
    } catch (err: any) {
      showToast(err.message || 'Checkout failed.', 'info');
    }
  };

  useEffect(() => { fetchData(); }, []);
  useEffect(() => { fetchStoreData(); }, [gradeFilter, chemFilter, selectedSupplierId, selectedCity, minCapacity, reqQuantity]);
  useEffect(() => {
    if (activeTab === 'quotes_orders' && buyerToken) fetchQuotesAndOrders();
  }, [activeTab, buyerToken]);

  useEffect(() => {
    if (lastEvent && lastEvent.type === 'order_tracking_update') {
      const order_id = Number(lastEvent.payload.order_id);
      const tracking_status = String(lastEvent.payload.tracking_status);
      setOrders((prev) => prev.map((o) => o.id === order_id ? { ...o, tracking_status } : o));
      if (selectedOrder && selectedOrder.id === order_id) fetchTracking(order_id);
      showToast(`Order #${order_id} → ${tracking_status}`, 'success');
    }
  }, [lastEvent, selectedOrder]);

  const showToast = (message: string, type: 'success' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const deduceUseCases = (chemistry: string, grade: string): string[] => {
    const g = grade.replace('GRADE ', '').toUpperCase();
    if (g === 'S') return ['EV Fast Charge Buffer', 'Heavy Duty Transport'];
    if (g === 'A') return chemistry === 'LFP' ? ['Telecom Tower Backup', 'Rural Microgrid'] : ['Solar Storage', 'UPS Backup'];
    if (g === 'B') return ['Commercial Solar Storage', 'UPS Backup'];
    return ['Certified Recycling', 'Basic Solar Light'];
  };

  const handleCityClick = (cityName: string) => {
    if (selectedCity === cityName) {
      setSelectedCity(null);
      setSelectedSupplierId(null);
      setSelectedSupplier(null);
    } else {
      setSelectedCity(cityName);
      setSelectedSupplierId(null);
      setSelectedSupplier(null);
    }
  };

  const selectSupplier = (supplier: SupplierItem) => {
    setSelectedSupplierId(supplier.id);
    setSelectedSupplier(supplier);
    setSelectedCity(null);
  };

  if (loading || !summary) {
    return (
      <div className="page-content">
        <div className="page-header"><h2 className="page-title">Battery Marketplace</h2></div>
        <div className="grid grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton" style={{ height: 120 }} />)}
        </div>
      </div>
    );
  }

  // ======== BUYER VIEW: India Map → Seller Profiles → Inventory ========
  if (isBuyer) {
    return (
      <div className="page-content marketplace">
        {toast && (
          <div className={`marketplace-toast marketplace-toast--${toast.type}`}>
            <span className="marketplace-toast__icon">⚡</span>
            <span className="text-body-sm">{toast.message}</span>
          </div>
        )}

        <div className="page-header marketplace__header">
          <div>
            <h1 className="page-title">Battery Marketplace</h1>
            <p className="text-body-sm text-on-surface-variant" style={{ marginTop: 2 }}>
              Find second-life batteries from verified suppliers across India
            </p>
          </div>
          <div className="marketplace__tabs-toggle">
            <button
              className={`marketplace__tab-btn ${activeTab === 'store' ? 'marketplace__tab-btn--active' : ''}`}
              onClick={() => setActiveTab('store')}
            >
              🗺 Explore Suppliers
            </button>
            {buyerToken && (
              <button
                className={`marketplace__tab-btn ${activeTab === 'quotes_orders' ? 'marketplace__tab-btn--active' : ''}`}
                onClick={() => setActiveTab('quotes_orders')}
              >
                📋 My Orders
              </button>
            )}
          </div>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="metric-card metric-card--glow">
            <div className="metric-card__header">
              <span className="metric-card__icon">💰</span>
              <span className="text-label-caps">Total Market Value</span>
            </div>
            <div className="metric-card__value">
              <span className="text-data-lg text-primary">{summary.total_asset_value}</span>
            </div>
          </div>
          <MetricCard label="Listed Batteries" value={summary.auctions_count} icon="🔋" />
          <MetricCard label="Recently Sold" value={`${summary.recently_sold} Units`} icon="📦" />
          <MetricCard label="Verified Suppliers" value={suppliers.length || '—'} icon="🏭" />
        </div>

        {activeTab === 'store' ? (
          <div className="marketplace__store-layout">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

              {/* LEFT: India Map */}
              <div className="lg:col-span-5 flex flex-col gap-6">
                <div className="card marketplace__map-card">
                  <div className="marketplace__panel-header bg-transparent p-0 pb-3">
                    <h3 className="text-headline-sm flex items-center gap-2">
                      🗺 Suppliers Across India
                    </h3>
                    <span className="text-label-caps text-on-surface-variant">Click a city</span>
                  </div>
                  <div className="marketplace__map-container relative flex justify-center py-4 bg-surface-container-low rounded" style={{ minHeight: 420 }}>
                    <svg
                      className="marketplace__india-svg"
                      viewBox="0 0 280 370"
                      width="260"
                      height="350"
                      fill="none"
                      stroke="var(--outline)"
                      strokeWidth="1.5"
                    >
                      {/* India outline */}
                      <path
                        d="M 135 10 L 155 18 L 170 30 L 180 50 L 190 65 L 205 80 L 215 90 L 230 90 L 225 105 L 235 125 L 228 138 L 218 148 L 200 155 L 208 175 L 198 185 L 185 192 L 172 200 L 165 212 L 170 228 L 175 255 L 162 275 L 155 290 L 148 308 L 138 325 L 132 335 L 128 325 L 122 308 L 118 290 L 108 265 L 95 248 L 90 230 L 82 212 L 68 200 L 55 195 L 42 188 L 50 172 L 60 160 L 72 148 L 82 138 L 88 118 L 92 98 L 108 85 L 115 65 L 125 42 Z"
                        fill="var(--surface-container)"
                        stroke="var(--outline-variant)"
                        strokeWidth="1.5"
                      />

                      {/* State boundaries (simplified) */}
                      <path d="M 88 118 L 140 118 L 155 140 L 145 160 L 100 155 L 88 138" stroke="var(--outline-variant)" strokeWidth="0.5" fill="none" opacity="0.3" />
                      <path d="M 140 118 L 195 120 L 210 145 L 200 155 L 155 140" stroke="var(--outline-variant)" strokeWidth="0.5" fill="none" opacity="0.3" />
                      <path d="M 100 155 L 145 160 L 165 212 L 90 230 L 82 212 L 68 200" stroke="var(--outline-variant)" strokeWidth="0.5" fill="none" opacity="0.3" />
                      <path d="M 145 160 L 200 155 L 208 175 L 185 192 L 165 212" stroke="var(--outline-variant)" strokeWidth="0.5" fill="none" opacity="0.3" />

                      {/* City markers */}
                      {INDIA_STATES.map((city) => {
                        const isActive = selectedCity === city.name;
                        const dotSize = Math.min(city.suppliers * 1.5 + 3, 12);
                        return (
                          <g
                            key={city.name}
                            className="marketplace__city-group"
                            style={{ cursor: 'pointer' }}
                            onClick={() => handleCityClick(city.name)}
                          >
                            {/* Pulse ring on active */}
                            {isActive && (
                              <circle cx={city.x} cy={city.y} r={dotSize + 6} fill="none" stroke="var(--secondary)" strokeWidth="1.5" opacity="0.4">
                                <animate attributeName="r" from={dotSize + 4} to={dotSize + 12} dur="1.5s" repeatCount="indefinite" />
                                <animate attributeName="opacity" from="0.5" to="0" dur="1.5s" repeatCount="indefinite" />
                              </circle>
                            )}
                            {/* Glow */}
                            <circle cx={city.x} cy={city.y} r={dotSize + 3} fill={isActive ? 'var(--secondary)' : 'var(--primary)'} opacity="0.15" />
                            {/* Dot */}
                            <circle cx={city.x} cy={city.y} r={dotSize} fill={isActive ? 'var(--secondary)' : 'var(--primary)'} opacity={isActive ? 1 : 0.7} />
                            {/* Count */}
                            <text x={city.x} y={city.y + 3} textAnchor="middle" fill="#fff" fontSize="7px" fontWeight="bold">
                              {city.suppliers}
                            </text>
                            {/* Label */}
                            <text
                              x={city.x}
                              y={city.y + dotSize + 12}
                              textAnchor="middle"
                              fill={isActive ? 'var(--secondary)' : 'var(--on-surface)'}
                              fontSize="8px"
                              fontWeight={isActive ? 'bold' : 'normal'}
                            >
                              {city.name}
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  </div>

                  {/* Legend */}
                  <div style={{ padding: '12px 16px', display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
                    <span className="text-label-caps text-on-surface-variant" style={{ fontSize: 10 }}>
                      Circle size = number of suppliers
                    </span>
                    {selectedCity && (
                      <button
                        onClick={() => { setSelectedCity(null); setSelectedSupplierId(null); setSelectedSupplier(null); }}
                        className="text-label-caps"
                        style={{ color: 'var(--primary)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 10 }}
                      >
                        ✕ Clear filter
                      </button>
                    )}
                  </div>
                </div>

                {/* Supplier List from selected city */}
                {selectedCity && (
                  <div className="card p-5 animate-fadeIn">
                    <h3 className="text-headline-sm mb-4">Suppliers in {selectedCity}</h3>
                    {suppliers.length === 0 ? (
                      <p className="text-body-sm text-on-surface-variant">Loading suppliers...</p>
                    ) : (
                      <div className="flex flex-col gap-3">
                        {suppliers
                          .filter(s => s.address.toLowerCase().includes(selectedCity.toLowerCase()))
                          .map(s => (
                            <button
                              key={s.id}
                              onClick={() => selectSupplier(s)}
                              className={`marketplace__supplier-card ${selectedSupplierId === s.id ? 'marketplace__supplier-card--active' : ''}`}
                            >
                              <div className="flex justify-between items-center">
                                <div>
                                  <span className="text-body-sm font-bold block">{s.company_name}</span>
                                  <span className="text-label-caps text-on-surface-variant">📍 {s.address}</span>
                                </div>
                                <span className="marketplace__badge-verified text-label-caps">Verified</span>
                              </div>
                            </button>
                          ))
                        }
                        {suppliers.filter(s => s.address.toLowerCase().includes(selectedCity.toLowerCase())).length === 0 && (
                          <div className="flex flex-col gap-3">
                            {suppliers.map(s => (
                              <button
                                key={s.id}
                                onClick={() => selectSupplier(s)}
                                className={`marketplace__supplier-card ${selectedSupplierId === s.id ? 'marketplace__supplier-card--active' : ''}`}
                              >
                                <div className="flex justify-between items-center">
                                  <div>
                                    <span className="text-body-sm font-bold block">{s.company_name}</span>
                                    <span className="text-label-caps text-on-surface-variant">📍 {s.address}</span>
                                  </div>
                                  <span className="marketplace__badge-verified text-label-caps">Verified</span>
                                </div>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Filters */}
                <div className="card marketplace__filter-panel">
                  <div className="marketplace__panel-header bg-transparent p-0 pb-3 mb-4">
                    <h3 className="text-headline-sm">Filters</h3>
                    <button
                      onClick={() => { setGradeFilter(''); setChemFilter(''); setMinCapacity(''); setReqQuantity(''); setSelectedCity(null); setSelectedSupplierId(null); setSelectedSupplier(null); }}
                      className="text-label-caps text-on-surface-variant hover:text-primary"
                      style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                    >
                      Clear All
                    </button>
                  </div>
                  <div className="flex flex-col gap-4">
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <label className="text-label-caps text-on-surface-variant block mb-1">Grade</label>
                        <select value={gradeFilter} onChange={(e) => setGradeFilter(e.target.value)} className="marketplace__filter-select">
                          <option value="">All</option>
                          <option value="S">Grade S</option>
                          <option value="A">Grade A</option>
                          <option value="B">Grade B</option>
                          <option value="C">Grade C</option>
                        </select>
                      </div>
                      <div className="flex-1">
                        <label className="text-label-caps text-on-surface-variant block mb-1">Chemistry</label>
                        <select value={chemFilter} onChange={(e) => setChemFilter(e.target.value)} className="marketplace__filter-select">
                          <option value="">All</option>
                          <option value="NMC">NMC</option>
                          <option value="LFP">LFP</option>
                        </select>
                      </div>
                    </div>
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <label className="text-label-caps text-on-surface-variant block mb-1">Min Capacity (kWh)</label>
                        <input type="number" placeholder="e.g. 100" value={minCapacity} onChange={(e) => setMinCapacity(e.target.value ? Number(e.target.value) : '')} className="marketplace__filter-input" />
                      </div>
                      <div className="flex-1">
                        <label className="text-label-caps text-on-surface-variant block mb-1">Quantity</label>
                        <input type="number" placeholder="e.g. 10" value={reqQuantity} onChange={(e) => setReqQuantity(e.target.value ? Number(e.target.value) : '')} className="marketplace__filter-input" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* RIGHT: Inventory Listings */}
              <div className="lg:col-span-7 flex flex-col gap-6">
                <div className="flex justify-between items-center bg-surface-container-low p-4 rounded card mb-2">
                  <div>
                    <h3 className="text-headline-sm">
                      {selectedSupplier ? `${selectedSupplier.company_name} — Inventory` : selectedCity ? `Batteries near ${selectedCity}` : 'All Available Batteries'}
                    </h3>
                    <p className="text-body-sm text-on-surface-variant">
                      {lots.length} battery lots available for purchase
                    </p>
                  </div>
                  {(selectedCity || selectedSupplierId) && (
                    <button
                      onClick={() => { setSelectedCity(null); setSelectedSupplierId(null); setSelectedSupplier(null); }}
                      className="marketplace__btn-secondary"
                    >
                      Show All
                    </button>
                  )}
                </div>

                <div className="marketplace__listings-grid flex flex-col gap-6">
                  {lots.length > 0 ? lots.map((lot) => (
                    <div key={lot.id} className="marketplace__lot-card card glassmorphism animate-fadeIn">
                      <div className="p-6">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="text-headline-sm font-bold text-on-surface">{lot.title}</h4>
                            <span className="text-label-caps text-on-surface-variant">📍 {lot.origin}</span>
                          </div>
                          <span className="text-headline-sm text-secondary font-bold">{lot.price}</span>
                        </div>

                        <p className="text-body-sm text-on-surface-variant mb-4">
                          {lot.description || 'Verified second-life battery packs under strict VoltLife evaluation standards.'}
                        </p>

                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 bg-surface-container-low p-4 rounded mb-4">
                          <div>
                            <span className="text-label-caps text-on-surface-variant block mb-1">Grade</span>
                            <span className={`marketplace__grade-tag marketplace__grade-tag--${lot.grade.toLowerCase()}`}>GRADE {lot.grade}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Chemistry</span>
                            <span className="text-data-md font-bold">{lot.chemistry}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Avg SoH</span>
                            <span className="text-data-md font-bold text-primary">{lot.avg_soh}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Avg RUL</span>
                            <span className="text-data-md font-bold">{lot.avg_rul_years} yrs</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Available</span>
                            <span className="text-data-md font-bold">{lot.available_quantity} units</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Total Capacity</span>
                            <span className="text-body-sm font-bold">{lot.total_capacity_kwh} kWh</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Per Unit</span>
                            <span className="text-body-sm font-bold">{(lot.total_capacity_kwh / lot.available_quantity).toFixed(1)} kWh</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">MOQ</span>
                            <span className="text-body-sm font-bold">{lot.moq} units</span>
                          </div>
                        </div>

                        {lot.pricing_tiers && lot.pricing_tiers.length > 0 && (
                          <div className="mb-4">
                            <span className="text-label-caps text-on-surface-variant block mb-2">Pricing Tiers</span>
                            <div className="flex gap-4 bg-surface-container p-3 rounded">
                              {lot.pricing_tiers.map((t, idx) => (
                                <div key={idx} className="text-body-sm">
                                  <span className="text-on-surface-variant">{t.min_quantity}+: </span>
                                  <span className="font-bold text-secondary">${t.price_per_kwh}/kWh</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="mb-4">
                          <span className="text-label-caps text-on-surface-variant block mb-2">Recommended Use Cases</span>
                          <div className="flex gap-2">
                            {deduceUseCases(lot.chemistry, lot.grade).map((u, i) => (
                              <span key={i} className="marketplace__badge-usecase text-body-sm">{u}</span>
                            ))}
                          </div>
                        </div>

                        {showQuoteLotId === String(lot.id) ? (
                          <div className="mt-4 p-4 bg-surface-container rounded border border-primary animate-fadeIn">
                            <label className="text-label-caps block mb-2" style={{ color: 'var(--primary)' }}>Quantity:</label>
                            <div className="flex gap-2 mb-3">
                              <input
                                type="number"
                                min={lot.moq || 1}
                                max={lot.available_quantity}
                                value={quoteQtyInput}
                                onChange={(e) => setQuoteQtyInput(Math.max(1, Number(e.target.value)))}
                                className="marketplace__filter-input w-24 text-data-md"
                              />
                              <span className="text-body-sm self-center text-on-surface-variant">Min: {lot.moq} • Max: {lot.available_quantity}</span>
                            </div>
                            <div className="flex gap-2">
                              <button onClick={() => handleConfirmQuote(String(lot.id))} className="marketplace__btn-primary flex-1 text-label-caps">BUY NOW</button>
                              <button onClick={() => setShowQuoteLotId(null)} className="marketplace__btn-secondary text-label-caps">CANCEL</button>
                            </div>
                          </div>
                        ) : (
                          <button
                            onClick={() => { setShowQuoteLotId(String(lot.id)); setQuoteQtyInput(lot.moq || 1); }}
                            className="marketplace__btn-primary w-full mt-4"
                          >
                            SELECT & BUY
                          </button>
                        )}
                      </div>
                    </div>
                  )) : (
                    <div className="card p-8 text-center text-body-sm text-on-surface-variant">
                      {selectedCity ? `No listings found near ${selectedCity}. Try a different location.` : 'No published listings found. Try adjusting filters.'}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Quotes & Orders Tab */
          <div className="marketplace__store-layout animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              <div className="lg:col-span-7 flex flex-col gap-6">
                <div className="card p-6">
                  <h3 className="text-headline-sm mb-4">📋 My Quotes</h3>
                  {quotes.length === 0 ? (
                    <p className="text-body-sm text-on-surface-variant">No quotes yet. Browse the marketplace to request one.</p>
                  ) : quotes.map((q) => (
                    <div key={q.id} className="marketplace__quote-card p-4 mb-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <span className="text-label-caps block text-on-surface-variant">Quote #{q.id}</span>
                          <span className="text-body-sm font-bold">Qty: {q.quantity} • Lot #{q.inventory_lot_id}</span>
                        </div>
                        <span className={`marketplace__grade-tag marketplace__grade-tag--${q.status === 'accepted' ? 's' : 'c'}`}>{q.status.toUpperCase()}</span>
                      </div>
                      <div className="grid grid-cols-3 gap-4 bg-surface-container-low p-3 rounded mb-3 text-body-sm">
                        <div><span className="text-label-caps text-on-surface-variant block">Battery</span><span className="font-bold">${q.battery_cost?.toLocaleString()}</span></div>
                        <div><span className="text-label-caps text-on-surface-variant block">Transport</span><span className="font-bold">${q.transport_cost?.toLocaleString()}</span></div>
                        <div><span className="text-label-caps text-on-surface-variant block">Total</span><span className="font-bold text-secondary">${q.total_cost?.toLocaleString()}</span></div>
                      </div>
                      {q.status === 'pending' && (
                        <button onClick={() => handleCheckout(q.id)} className="marketplace__btn-primary w-full text-label-caps">💳 Pay & Confirm</button>
                      )}
                    </div>
                  ))}
                </div>
                <div className="card p-6">
                  <h3 className="text-headline-sm mb-4">📦 My Orders</h3>
                  {orders.length === 0 ? (
                    <p className="text-body-sm text-on-surface-variant">No orders yet.</p>
                  ) : orders.map((o) => (
                    <div key={o.id} className="marketplace__order-card p-4 mb-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <span className="text-label-caps block text-on-surface-variant">Order #{o.id}</span>
                          <span className="text-body-sm font-bold">Qty: {o.quantity} • ${o.total_price?.toLocaleString()}</span>
                        </div>
                        <span className="text-label-caps text-primary font-bold">{o.tracking_status?.replace('_', ' ').toUpperCase()}</span>
                        <button onClick={() => { setSelectedOrder(o); fetchTracking(o.id); }} className="marketplace__btn-primary text-label-caps">Track</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="lg:col-span-5">
                <div className="card p-6 sticky" style={{ top: 20 }}>
                  <h3 className="text-headline-sm mb-4">🚚 Live Tracker</h3>
                  {!selectedOrder ? (
                    <div className="text-center p-8 border border-dashed border-outline-variant rounded text-on-surface-variant text-body-sm">Select an order to track.</div>
                  ) : trackingData ? (
                    <div className="animate-fadeIn">
                      <h4 className="text-headline-xs text-primary mb-2">Order #{trackingData.order_id}</h4>
                      <p className="text-body-sm text-on-surface-variant mb-4">
                        Via: {trackingData.porter_vehicle_type} • Est: {trackingData.delivery_days} days
                      </p>
                      <div className="marketplace__stepper">
                        {["confirmed","porter_booked","seller_notified","shipment_started","in_transit","delivered"].map((status, i) => {
                          const statusIdx = trackingData.tracking_status === "completed" ? 6 : ["confirmed","porter_booked","seller_notified","shipment_started","in_transit","delivered"].indexOf(trackingData.tracking_status);
                          return (
                            <div key={status} className={`marketplace__step ${i < statusIdx ? 'completed' : ''} ${i === statusIdx ? 'active' : ''}`}>
                              <div className="marketplace__step-circle">{i < statusIdx ? '✓' : i + 1}</div>
                              <span className="marketplace__step-label">{status.replace('_', ' ')}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center p-8"><div className="assess__spinner-ring mx-auto" style={{ width: 32, height: 32 }} /></div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ======== SELLER VIEW: Simple Inventory Store (No Auctions/Bidding) ========
  return (
    <div className="page-content marketplace">
      {toast && (
        <div className={`marketplace-toast marketplace-toast--${toast.type}`}>
          <span className="marketplace-toast__icon">⚡</span>
          <span className="text-body-sm">{toast.message}</span>
        </div>
      )}

      <div className="page-header marketplace__header">
        <div>
          <h1 className="page-title">Battery Marketplace</h1>
          <p className="text-body-sm text-on-surface-variant" style={{ marginTop: 2 }}>
            Inventory Listings & Market Overview
          </p>
        </div>
        <div className="marketplace__live-status">
          <span className="marketplace__status-dot animate-pulse"></span>
          <span className="text-label-caps" style={{ color: 'var(--secondary)' }}>MARKET OPEN</span>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="metric-card metric-card--glow">
          <div className="metric-card__header">
            <span className="metric-card__icon">💰</span>
            <span className="text-label-caps">Total Asset Value</span>
          </div>
          <div className="metric-card__value">
            <span className="text-data-lg text-primary">{summary.total_asset_value}</span>
          </div>
          <div className="metric-card__trend metric-card__trend--up" style={{ color: 'var(--secondary)', fontSize: 11 }}>↑ +12.4% vs last Q</div>
        </div>
        <MetricCard label="Listed Batteries" value={summary.auctions_count} icon="🔋" />
        <MetricCard label="Recently Sold" value={`${summary.recently_sold} Units`} icon="📦" />
        <div className="metric-card" style={{ borderLeft: '2px solid var(--secondary)' }}>
          <div className="metric-card__header">
            <span className="metric-card__icon">📈</span>
            <span className="text-label-caps">Second Life Index</span>
          </div>
          <div className="metric-card__value"><span className="text-data-lg">{summary.second_life_index}</span></div>
          <div className="text-label-caps" style={{ color: 'var(--secondary)', fontSize: 10, marginTop: 4 }}>Demand: CRITICAL HIGH</div>
        </div>
      </div>

      {/* Seller Store: Inventory Listings */}
      <div className="marketplace__store-layout">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Filters */}
          <div className="lg:col-span-3 flex flex-col gap-6">
            <div className="card marketplace__filter-panel">
              <div className="marketplace__panel-header bg-transparent p-0 pb-3 mb-4">
                <h3 className="text-headline-sm">Filters</h3>
              </div>
              <div className="flex flex-col gap-4">
                <div>
                  <label className="text-label-caps text-on-surface-variant block mb-1">Grade</label>
                  <select value={gradeFilter} onChange={(e) => setGradeFilter(e.target.value)} className="marketplace__filter-select">
                    <option value="">All</option>
                    <option value="S">Grade S</option>
                    <option value="A">Grade A</option>
                    <option value="B">Grade B</option>
                    <option value="C">Grade C</option>
                  </select>
                </div>
                <div>
                  <label className="text-label-caps text-on-surface-variant block mb-1">Chemistry</label>
                  <select value={chemFilter} onChange={(e) => setChemFilter(e.target.value)} className="marketplace__filter-select">
                    <option value="">All</option>
                    <option value="NMC">NMC</option>
                    <option value="LFP">LFP</option>
                  </select>
                </div>
                <div>
                  <label className="text-label-caps text-on-surface-variant block mb-1">Min Capacity (kWh)</label>
                  <input type="number" placeholder="100" value={minCapacity} onChange={(e) => setMinCapacity(e.target.value ? Number(e.target.value) : '')} className="marketplace__filter-input" />
                </div>
                <button
                  onClick={() => { setGradeFilter(''); setChemFilter(''); setMinCapacity(''); setReqQuantity(''); }}
                  className="marketplace__btn-secondary text-label-caps w-full"
                >
                  Clear Filters
                </button>
              </div>
            </div>

            {/* Market Chart */}
            <div className="card p-5">
              <h3 className="text-headline-sm mb-3">Market Insights</h3>
              <p className="text-label-caps text-on-surface-variant mb-3">Grade B Price Index</p>
              <svg viewBox="0 0 400 200" style={{ width: '100%' }}>
                <defs>
                  <linearGradient id="chart-glow" x1="0%" x2="0%" y1="0%" y2="100%">
                    <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <line x1="0" y1="50" x2="400" y2="50" stroke="var(--outline-variant)" strokeDasharray="2,2" />
                <line x1="0" y1="100" x2="400" y2="100" stroke="var(--outline-variant)" strokeDasharray="2,2" />
                <line x1="0" y1="150" x2="400" y2="150" stroke="var(--outline-variant)" strokeDasharray="2,2" />
                <path d="M 0 180 Q 50 150 100 160 T 200 120 T 300 130 T 400 60 V 200 H 0 Z" fill="url(#chart-glow)" />
                <path d="M 0 180 Q 50 150 100 160 T 200 120 T 300 130 T 400 60" fill="none" stroke="var(--primary)" strokeWidth="2" />
              </svg>
              <div className="mt-2 text-body-sm" style={{ color: 'var(--secondary)' }}>↑ 8.2% last 30 days</div>
            </div>
          </div>

          {/* Listings */}
          <div className="lg:col-span-9 flex flex-col gap-6">
            <div className="flex justify-between items-center bg-surface-container-low p-4 rounded card mb-2">
              <div>
                <h3 className="text-headline-sm">Active Inventory Listings</h3>
                <p className="text-body-sm text-on-surface-variant">{lots.length} published battery lots</p>
              </div>
            </div>

            <div className="marketplace__listings-grid flex flex-col gap-6">
              {lots.length > 0 ? lots.map((lot) => (
                <div key={lot.id} className="marketplace__lot-card card glassmorphism animate-fadeIn">
                  <div className="p-6">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="text-headline-sm font-bold text-on-surface">{lot.title}</h4>
                        <span className="text-label-caps text-on-surface-variant">📍 {lot.origin}</span>
                      </div>
                      <span className="text-headline-sm text-secondary font-bold">{lot.price}</span>
                    </div>
                    <p className="text-body-sm text-on-surface-variant mb-4">
                      {lot.description || 'Verified second-life battery packs under strict VoltLife evaluation standards.'}
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 bg-surface-container-low p-4 rounded mb-4">
                      <div>
                        <span className="text-label-caps text-on-surface-variant block mb-1">Grade</span>
                        <span className={`marketplace__grade-tag marketplace__grade-tag--${lot.grade.toLowerCase()}`}>GRADE {lot.grade}</span>
                      </div>
                      <div>
                        <span className="text-label-caps text-on-surface-variant block">Chemistry</span>
                        <span className="text-data-md font-bold">{lot.chemistry}</span>
                      </div>
                      <div>
                        <span className="text-label-caps text-on-surface-variant block">Avg SoH</span>
                        <span className="text-data-md font-bold text-primary">{lot.avg_soh}</span>
                      </div>
                      <div>
                        <span className="text-label-caps text-on-surface-variant block">Avg RUL</span>
                        <span className="text-data-md font-bold">{lot.avg_rul_years} yrs</span>
                      </div>
                      <div>
                        <span className="text-label-caps text-on-surface-variant block">Available</span>
                        <span className="text-data-md font-bold">{lot.available_quantity} units</span>
                      </div>
                    </div>
                    {lot.pricing_tiers && lot.pricing_tiers.length > 0 && (
                      <div className="mb-4">
                        <span className="text-label-caps text-on-surface-variant block mb-2">Pricing Tiers</span>
                        <div className="flex gap-4 bg-surface-container p-3 rounded">
                          {lot.pricing_tiers.map((t, idx) => (
                            <div key={idx} className="text-body-sm">
                              <span className="text-on-surface-variant">{t.min_quantity}+: </span>
                              <span className="font-bold text-secondary">${t.price_per_kwh}/kWh</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="mb-4">
                      <span className="text-label-caps text-on-surface-variant block mb-2">Recommended Use Cases</span>
                      <div className="flex gap-2">
                        {deduceUseCases(lot.chemistry, lot.grade).map((u, i) => (
                          <span key={i} className="marketplace__badge-usecase text-body-sm">{u}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )) : (
                <div className="card p-8 text-center text-body-sm text-on-surface-variant">
                  No published listings found. Publish inventory from your Seller Panel.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Marketplace;

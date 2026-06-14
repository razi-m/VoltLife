import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Card, MetricCard } from '../components/ui/Card';
import type { WSEvent } from '../lib/types';
import './Marketplace.css';

interface AuctionItem {
  id: number;
  bpan: string;
  grade: string;
  chemistry: string;
  current_bid: number;
  time_remaining: string;
  rated_capacity_kwh: number;
}

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

// Stylized city coordinate mapping on the SVG map (canvas size: 300x380)
const supplierCities = [
  { name: 'Pune', x: 85, y: 200, supplierId: 1 },
  { name: 'Mumbai', x: 75, y: 185, supplierId: 2 },
  { name: 'Bangalore', x: 105, y: 275, supplierId: 3 },
  { name: 'Hyderabad', x: 125, y: 225, supplierId: 4 },
];

interface MarketplaceProps {
  lastEvent: WSEvent | null;
}

const Marketplace: React.FC<MarketplaceProps> = ({ lastEvent }) => {
  const [activeTab, setActiveTab] = useState<'auctions' | 'store' | 'quotes_orders'>('auctions');
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  
  // Auctions Tab State
  const [auctions, setAuctions] = useState<AuctionItem[]>([]);
  const [filter, setFilter] = useState<string>(''); // '', 'A', 'B', 'C'
  const [biddingId, setBiddingId] = useState<number | null>(null);

  // Store Tab State
  const [lots, setLots] = useState<LotItem[]>([]);
  const [suppliers, setSuppliers] = useState<SupplierItem[]>([]);
  const [selectedSupplierId, setSelectedSupplierId] = useState<number | null>(null);
  const [selectedSupplier, setSelectedSupplier] = useState<SupplierItem | null>(null);
  
  // Store Search & Filters
  const [gradeFilter, setGradeFilter] = useState<string>('');
  const [chemFilter, setChemFilter] = useState<string>('');
  const [minCapacity, setMinCapacity] = useState<number | ''>('');
  const [reqQuantity, setReqQuantity] = useState<number | ''>('');
  const [cityFilter, setCityFilter] = useState<string>('');

  // AI Requirement Matcher State
  const [useCaseText, setUseCaseText] = useState<string>('');
  const [matchingResults, setMatchingResults] = useState<any[]>([]);
  const [matchingLoading, setMatchingLoading] = useState(false);
  const [activeRequirementId, setActiveRequirementId] = useState<number | null>(null);

  // Buyer Auth Session Simulation
  const [buyerToken, setBuyerToken] = useState<string | null>(localStorage.getItem('buyer_token'));
  const [buyerUsername, setBuyerUsername] = useState<string | null>(localStorage.getItem('buyer_username'));
  const [authError, setAuthError] = useState<string | null>(null);

  // Quotes & Orders State
  const [quotes, setQuotes] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<any | null>(null);
  const [trackingData, setTrackingData] = useState<any | null>(null);
  const [trackingLoading, setTrackingLoading] = useState(false);

  // Interactive Quote input
  const [showQuoteLotId, setShowQuoteLotId] = useState<string | null>(null);
  const [quoteQtyInput, setQuoteQtyInput] = useState<number>(1);

  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' } | null>(null);

  // Support Ticket State (Phase 12)
  const [showTicketModal, setShowTicketModal] = useState(false);
  const [ticketIssueText, setTicketIssueText] = useState('');
  const [submittingTicket, setSubmittingTicket] = useState(false);

  const fetchData = async (selectedGrade = filter) => {
    try {
      const [sumRes, aucRes] = await Promise.all([
        api.marketplace.summary(),
        api.marketplace.auctions(selectedGrade),
      ]);
      setSummary(sumRes);
      setAuctions(aucRes);
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

      // Apply client-side filters for city, capacity, and quantity
      let filteredLots = lotsRes;
      if (cityFilter) {
        filteredLots = filteredLots.filter((lot: any) => 
          lot.origin.toLowerCase().includes(cityFilter.toLowerCase())
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
      showToast('Failed to load tracking data.', 'info');
    } finally {
      setTrackingLoading(false);
    }
  };

  const handleConfirmQuote = async (lotId: string) => {
    if (!buyerToken) return;
    try {
      const cleanLotId = lotId.startsWith('lot-') ? Number(lotId.replace('lot-', '')) : Number(lotId);
      await api.quotes.create(cleanLotId, quoteQtyInput, buyerToken);
      showToast('Formal quote requested successfully!', 'success');
      setShowQuoteLotId(null);
      // Switch tab to quotes so they can see it
      setActiveTab('quotes_orders');
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Failed to create quote.', 'info');
    }
  };

  const handleCheckout = async (quoteId: number) => {
    if (!buyerToken) return;
    showToast('Initiating checkout session...', 'info');
    try {
      const session = await api.payments.checkoutSession(quoteId, buyerToken);
      showToast('Redirecting to payment processor...', 'success');
      
      // Simulating Stripe / Mock checkout confirm directly in sandbox
      showToast('Verifying payment and locking inventory...', 'info');
      const order = await api.payments.mockConfirm(session.session_id, buyerToken);
      showToast(`Payment confirmed! Order #${order.id} created.`, 'success');
      
      // Refresh quotes and orders
      fetchQuotesAndOrders();
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Checkout failed.', 'info');
    }
  };

  const handleTriggerStatus = async (statusStr: string) => {
    if (!selectedOrder) return;
    try {
      await api.logistics.triggerCallback(selectedOrder.id, statusStr);
      showToast(`Simulated status callback '${statusStr}' sent!`, 'success');
      // Refresh tracking details
      fetchTracking(selectedOrder.id);
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Callback rejected.', 'info');
    }
  };

  const handleTriggerAutoSimulation = async () => {
    if (!selectedOrder) return;
    try {
      await api.logistics.triggerCallback(selectedOrder.id, "porter_booked");
      showToast('Logistics simulation triggered!', 'success');
      fetchTracking(selectedOrder.id);
    } catch (err: any) {
      console.error(err);
      showToast('Simulation already completed or running.', 'info');
    }
  };

  const handleSelectOrder = (order: any) => {
    setSelectedOrder(order);
    fetchTracking(order.id);
  };

  const handleConfirmReceipt = async () => {
    if (!selectedOrder || !buyerToken) return;
    try {
      await api.logistics.confirmReceipt(selectedOrder.id, buyerToken);
      showToast('Delivery receipt confirmed successfully!', 'success');
      fetchTracking(selectedOrder.id);
      fetchQuotesAndOrders(); // Refresh order status in listing
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Failed to confirm receipt.', 'info');
    }
  };

  const handleRaiseIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder || !buyerToken || !ticketIssueText.trim()) return;
    setSubmittingTicket(true);
    try {
      await api.logistics.raiseIssue(selectedOrder.id, ticketIssueText, buyerToken);
      showToast('Support ticket raised successfully!', 'success');
      setTicketIssueText('');
      setShowTicketModal(false);
      fetchTracking(selectedOrder.id); // Refresh tracking data to pull new support tickets
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Failed to raise support ticket.', 'info');
    } finally {
      setSubmittingTicket(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (activeTab === 'store') {
      fetchStoreData();
    }
  }, [activeTab, gradeFilter, chemFilter, selectedSupplierId, cityFilter, minCapacity, reqQuantity]);

  useEffect(() => {
    if (activeTab === 'quotes_orders' && buyerToken) {
      fetchQuotesAndOrders();
    }
  }, [activeTab, buyerToken]);

  useEffect(() => {
    if (lastEvent && lastEvent.type === 'order_tracking_update') {
      const order_id = Number(lastEvent.payload.order_id);
      const tracking_status = String(lastEvent.payload.tracking_status);
      
      // Update the status in the orders list
      setOrders((prev) => 
        prev.map((o) => o.id === order_id ? { ...o, tracking_status } : o)
      );

      // If this order is currently selected, refresh its tracking data
      if (selectedOrder && selectedOrder.id === order_id) {
        fetchTracking(order_id);
      }
      
      showToast(`Order #${order_id} advanced to ${tracking_status}!`, 'success');
    }
  }, [lastEvent, selectedOrder]);

  const handleFilterChange = (grade: string) => {
    setFilter(grade);
    fetchData(grade);
  };

  const handlePlaceBid = async (id: number, bpan: string) => {
    setBiddingId(id);
    try {
      const res = await api.marketplace.bid(id);
      showToast(`Bid placed on ${bpan}! New bid: $${res.new_bid.toLocaleString()}`, 'success');
      fetchData();
    } catch (err) {
      console.error('Failed to place bid:', err);
      showToast('Error placing bid. Please try again.', 'info');
    } finally {
      setBiddingId(null);
    }
  };

  const handleDemoAuth = async () => {
    setAuthError(null);
    try {
      // Attempt login
      let loginResp;
      try {
        loginResp = await api.marketplace.bid(1); // just checking api, let's call actual buyer login
        const loginPayload = { username: 'grid_operator', password: 'buyerpassword123' };
        
        // Let's call the buyer login directly using fetch because we want a quick check
        const response = await fetch('http://localhost:8000/api/v1/buyers/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(loginPayload)
        });
        
        if (response.status === 401) {
          // If operator does not exist, register them
          const regPayload = {
            company_name: "Grid operator Inc",
            email: "buyer_demo@grid.com",
            phone: "+917777777777",
            address: "Pune",
            username: "grid_operator",
            password: "buyerpassword123"
          };
          await fetch('http://localhost:8000/api/v1/buyers/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(regPayload)
          });
          
          // Try login again
          const retryResp = await fetch('http://localhost:8000/api/v1/buyers/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(loginPayload)
          });
          loginResp = await retryResp.json();
        } else {
          loginResp = await response.json();
        }
      } catch (e) {
        console.error('Registration/login API error:', e);
      }

      if (loginResp && loginResp.access_token) {
        localStorage.setItem('buyer_token', loginResp.access_token);
        localStorage.setItem('buyer_username', 'grid_operator');
        setBuyerToken(loginResp.access_token);
        setBuyerUsername('grid_operator');
        showToast('Successfully logged in as Demo Buyer!', 'success');
      } else {
        setAuthError('Authentication failed. Ensure backend is running.');
      }
    } catch (err: any) {
      setAuthError(err.message || 'Auth simulation failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('buyer_token');
    localStorage.removeItem('buyer_username');
    setBuyerToken(null);
    setBuyerUsername(null);
    setMatchingResults([]);
    setActiveRequirementId(null);
    showToast('Logged out of buyer session.', 'info');
  };

  const handleAIQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!buyerToken) {
      showToast('Please log in as a buyer first.', 'info');
      return;
    }
    if (!useCaseText.trim()) return;

    setMatchingLoading(true);
    try {
      // 1. Create requirement (parses via Gemini/Fallback)
      const reqRes = await api.requirements.create(useCaseText, buyerToken);
      setActiveRequirementId(reqRes.id);
      
      // Update filter UI with parsed parameters to make match clear
      if (reqRes.parsed_grade) setGradeFilter(reqRes.parsed_grade);
      if (reqRes.parsed_capacity_kwh) setMinCapacity(reqRes.parsed_capacity_kwh);
      if (reqRes.parsed_quantity) setReqQuantity(reqRes.parsed_quantity);
      
      // 2. Fetch compatibility matches
      const matches = await api.requirements.matches(reqRes.id, buyerToken);
      setMatchingResults(matches);
      showToast('AI requirement matches compiled!', 'success');
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Error processing AI query', 'info');
    } finally {
      setMatchingLoading(false);
    }
  };

  const selectCitySupplier = (supplierId: number) => {
    if (selectedSupplierId === supplierId) {
      // Toggle off
      setSelectedSupplierId(null);
      setSelectedSupplier(null);
    } else {
      setSelectedSupplierId(supplierId);
      const found = suppliers.find(s => s.id === supplierId);
      setSelectedSupplier(found || null);
    }
  };

  const showToast = (message: string, type: 'success' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const deduceUseCases = (chemistry: string, grade: string): string[] => {
    const normGrade = grade.replace('GRADE ', '').toUpperCase();
    if (normGrade === 'S') return ['EV Fast Charge Buffer', 'Heavy Duty Transport'];
    if (normGrade === 'A') {
      return chemistry === 'LFP' ? ['Telecom Tower Backup', 'Rural Microgrid'] : ['Solar Storage System', 'UPS Backup'];
    }
    if (normGrade === 'B') return ['Commercial Solar Storage', 'UPS Backup'];
    return ['Certified Recycling Routing', 'Basic Solar Light'];
  };

  if (loading || !summary) {
    return (
      <div className="page-content">
        <div className="page-header">
          <h2 className="page-title">Battery Marketplace</h2>
        </div>
        <div className="grid grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 120 }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="page-content marketplace">
      {/* Toast Notification */}
      {toast && (
        <div className={`marketplace-toast marketplace-toast--${toast.type}`}>
          <span className="marketplace-toast__icon">⚡</span>
          <span className="text-body-sm">{toast.message}</span>
        </div>
      )}

      {/* Hero Header */}
      <div className="page-header marketplace__header">
        <div>
          <h1 className="page-title">Battery Marketplace</h1>
          <p className="text-body-sm text-on-surface-variant" style={{ marginTop: 2 }}>
            Asset Monetization &amp; Procurement Hub • v4.3.0-ENTERPRISE
          </p>
        </div>
        
        {/* Tab Toggle */}
        <div className="marketplace__tabs-toggle">
          <button 
            className={`marketplace__tab-btn ${activeTab === 'auctions' ? 'marketplace__tab-btn--active' : ''}`}
            onClick={() => setActiveTab('auctions')}
          >
            🔨 Live Auctions
          </button>
          <button 
            className={`marketplace__tab-btn ${activeTab === 'store' ? 'marketplace__tab-btn--active' : ''}`}
            onClick={() => setActiveTab('store')}
          >
            🔌 Bulk Store
          </button>
          {buyerToken && (
            <button 
              className={`marketplace__tab-btn ${activeTab === 'quotes_orders' ? 'marketplace__tab-btn--active' : ''}`}
              onClick={() => setActiveTab('quotes_orders')}
            >
              📋 My Quotes & Orders
            </button>
          )}
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
          <div className="metric-card__trend metric-card__trend--up" style={{ color: 'var(--secondary)', fontSize: 11 }}>
            ↑ +12.4% vs last Q
          </div>
        </div>

        <MetricCard label="Batteries for Auction" value={summary.auctions_count} icon="⚖" />
        <MetricCard label="Recently Sold" value={`${summary.recently_sold} Units`} icon="🔌" />
        
        <div className="metric-card" style={{ borderLeft: '2px solid var(--secondary)' }}>
          <div className="metric-card__header">
            <span className="metric-card__icon">📈</span>
            <span className="text-label-caps">Second Life Index</span>
          </div>
          <div className="metric-card__value">
            <span className="text-data-lg">{summary.second_life_index}</span>
          </div>
          <div className="text-label-caps" style={{ color: 'var(--secondary)', fontSize: 10, marginTop: 4 }}>
            Demand: CRITICAL HIGH
          </div>
        </div>
      </div>

      {activeTab === 'auctions' ? (
        /* --- LIVE AUCTIONS TAB VIEW --- */
        <div className="marketplace__grid">
          {/* Live Auctions Table */}
          <div className="marketplace__auctions-panel card">
            <div className="marketplace__panel-header">
              <h3 className="text-headline-sm flex items-center gap-2">
                <span className="text-primary">🔨</span> Live Auctions
              </h3>
              <div className="marketplace__filter-group">
                <button 
                  className={`marketplace__filter-btn ${filter === '' ? 'marketplace__filter-btn--active' : ''}`}
                  onClick={() => handleFilterChange('')}
                >
                  ALL
                </button>
                <button 
                  className={`marketplace__filter-btn ${filter === 'A' ? 'marketplace__filter-btn--active' : ''}`}
                  onClick={() => handleFilterChange('A')}
                >
                  GRADE A
                </button>
                <button 
                  className={`marketplace__filter-btn ${filter === 'B' ? 'marketplace__filter-btn--active' : ''}`}
                  onClick={() => handleFilterChange('B')}
                >
                  GRADE B
                </button>
                <button 
                  className={`marketplace__filter-btn ${filter === 'C' ? 'marketplace__filter-btn--active' : ''}`}
                  onClick={() => handleFilterChange('C')}
                >
                  GRADE C
                </button>
              </div>
            </div>
            <div className="marketplace__table-container">
              <table className="marketplace__table">
                <thead>
                  <tr>
                    <th className="text-label-caps">Asset ID (BPAN)</th>
                    <th className="text-label-caps">Grade</th>
                    <th className="text-label-caps">Chemistry</th>
                    <th className="text-label-caps">Capacity</th>
                    <th className="text-label-caps text-right">Current Bid</th>
                    <th className="text-label-caps">Time Remaining</th>
                    <th className="text-label-caps text-center">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {auctions.map((auc) => (
                    <tr key={auc.id} className="marketplace__row">
                      <td className="text-data-md text-primary font-bold">{auc.bpan}</td>
                      <td>
                        <span className={`marketplace__grade-tag marketplace__grade-tag--${auc.grade.replace('GRADE ', '').toLowerCase()}`}>
                          {auc.grade}
                        </span>
                      </td>
                      <td className="text-on-surface-variant">{auc.chemistry}</td>
                      <td className="text-data-md">{auc.rated_capacity_kwh} kWh</td>
                      <td className="text-right text-data-md font-bold">${auc.current_bid.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                      <td className="text-on-surface-variant">
                        <span className="marketplace__clock-icon">⏱</span> {auc.time_remaining}
                      </td>
                      <td className="text-center">
                        <button 
                          className="marketplace__bid-btn"
                          disabled={biddingId === auc.id}
                          onClick={() => handlePlaceBid(auc.id, auc.bpan)}
                        >
                          {biddingId === auc.id ? 'PLACING...' : 'PLACE BID'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Market Insights Panel */}
          <div className="marketplace__insights-panel card">
            <div className="marketplace__panel-header">
              <div>
                <h3 className="text-headline-sm">Market Insights</h3>
                <p className="text-label-caps text-on-surface-variant" style={{ marginTop: 2 }}>
                  Grade B Price Index (Global)
                </p>
              </div>
            </div>
            <div className="marketplace__chart-container">
              <div className="marketplace__chart-svg-wrapper">
                <svg className="marketplace__chart-svg" viewBox="0 0 400 200">
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
                <div className="marketplace__chart-stat">
                  <span className="text-data-md" style={{ color: 'var(--secondary)' }}>↑ 8.2%</span>
                  <span className="text-label-caps text-on-surface-variant">Last 30 Days</span>
                </div>
              </div>
            </div>
            <div className="marketplace__recommendation">
              <div className="marketplace__recommendation-header">
                <span className="text-primary">💡</span>
                <span className="text-label-caps">Analyst Recommendation</span>
              </div>
              <p className="text-body-sm text-on-surface-variant" style={{ fontSize: 13, lineHeight: 1.4 }}>
                Heavy demand from micro-grid developers in SE Asia. Strategic hold recommended for Tier 1 NMC packs until Q4.
              </p>
            </div>
          </div>
        </div>
      ) : activeTab === 'store' ? (
        /* --- BULK STORE DISCOVERY TAB VIEW (PHASE 7) --- */
        <div className="marketplace__store-layout">
          
          {/* Main Grid: Left Column (Map & Filters), Right Column (Listings) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            {/* LEFT COLUMN: Map, AI Matcher, Filters (Spans 5 Columns) */}
            <div className="lg:col-span-5 flex flex-col gap-6">
              
              {/* Buyer Session Widget */}
              <div className="card marketplace__auth-widget">
                <h4 className="text-headline-xs mb-2 flex items-center gap-2">
                  👤 {buyerUsername ? 'Buyer Session Active' : 'Buyer Session Required'}
                </h4>
                {buyerUsername ? (
                  <div className="flex justify-between items-center bg-surface-container-low p-3 rounded">
                    <div>
                      <span className="text-body-sm font-bold text-primary">{buyerUsername}</span>
                      <span className="text-label-caps text-on-surface-variant block">Mock Buyer account logged in</span>
                    </div>
                    <button onClick={handleLogout} className="marketplace__btn-secondary">Logout</button>
                  </div>
                ) : (
                  <div>
                    <p className="text-body-sm text-on-surface-variant mb-4">
                      Create buyer requirements and request quotes in simulated sandbox mode.
                    </p>
                    <button onClick={handleDemoAuth} className="marketplace__btn-primary w-full">
                      ⚡ Quick Login as Demo Buyer
                    </button>
                    {authError && <p className="text-body-sm text-red-500 mt-2">{authError}</p>}
                  </div>
                )}
              </div>

              {/* Vector SVG India Map */}
              <div className="card marketplace__map-card">
                <div className="marketplace__panel-header bg-transparent p-0 pb-3">
                  <h3 className="text-headline-sm flex items-center gap-2">
                    📍 Supplier Logistics Hubs
                  </h3>
                  <span className="text-label-caps text-on-surface-variant">Click City to Filter</span>
                </div>
                <div className="marketplace__map-container relative flex justify-center py-4 bg-surface-container-low rounded">
                  <svg 
                    className="marketplace__india-svg" 
                    viewBox="0 0 250 320" 
                    width="230" 
                    height="290"
                    fill="none" 
                    stroke="var(--outline)" 
                    strokeWidth="1.5"
                  >
                    {/* Simplified geometric polygon representation of India outline */}
                    <path 
                      d="M 120 15 L 140 25 L 150 45 L 160 55 L 175 75 L 180 85 L 205 85 L 200 100 L 210 120 L 205 130 L 195 140 L 180 145 L 185 160 L 175 170 L 165 175 L 155 185 L 150 195 L 155 210 L 158 235 L 148 250 L 142 265 L 135 285 L 125 305 L 122 312 L 118 305 L 114 285 L 110 265 L 102 240 L 92 225 L 88 210 L 80 195 L 68 185 L 58 180 L 45 172 L 52 160 L 60 150 L 70 140 L 78 132 L 82 110 L 85 90 L 98 80 L 105 60 L 112 40 Z" 
                      fill="var(--surface-container)" 
                      stroke="var(--outline-variant)" 
                      strokeWidth="1.5"
                    />
                    
                    {/* Connecting Logistical Routes */}
                    <polyline points="75,185 85,200" stroke="var(--primary)" strokeWidth="0.8" strokeDasharray="3,3" opacity="0.5" />
                    <polyline points="85,200 105,275" stroke="var(--primary)" strokeWidth="0.8" strokeDasharray="3,3" opacity="0.5" />
                    <polyline points="85,200 125,225" stroke="var(--primary)" strokeWidth="0.8" strokeDasharray="3,3" opacity="0.5" />
                    <polyline points="125,225 105,275" stroke="var(--primary)" strokeWidth="0.8" strokeDasharray="3,3" opacity="0.5" />

                    {/* Plot city dots */}
                    {supplierCities.map((city) => {
                      const active = selectedSupplierId === city.supplierId;
                      return (
                        <g 
                          key={city.name} 
                          className="marketplace__city-group cursor-pointer"
                          onClick={() => selectCitySupplier(city.supplierId)}
                        >
                          <circle 
                            cx={city.x} 
                            cy={city.y} 
                            r={active ? 8 : 5} 
                            fill={active ? 'var(--secondary)' : 'var(--primary)'}
                            className={active ? 'animate-ping' : ''}
                            opacity={active ? 0.3 : 0.8}
                          />
                          <circle 
                            cx={city.x} 
                            cy={city.y} 
                            r={active ? 4 : 3} 
                            fill={active ? 'var(--secondary)' : 'var(--primary)'}
                          />
                          <text 
                            x={city.x + 8} 
                            y={city.y + 4} 
                            className="marketplace__map-label font-bold text-headline-xxs"
                            fill={active ? 'var(--secondary)' : 'var(--on-surface)'}
                            fontSize="9px"
                          >
                            {city.name}
                          </text>
                        </g>
                      );
                    })}
                  </svg>

                  {/* Supplier Profile Detail overlay card */}
                  {selectedSupplier && (
                    <div className="marketplace__map-overlay card glassmorphism animate-fadeIn">
                      <div className="flex justify-between items-start">
                        <h4 className="text-headline-xs text-primary">{selectedSupplier.company_name}</h4>
                        <button 
                          onClick={() => { setSelectedSupplierId(null); setSelectedSupplier(null); }}
                          className="marketplace__close-btn"
                        >
                          ×
                        </button>
                      </div>
                      <p className="text-body-sm text-on-surface-variant font-bold mt-1">📍 {selectedSupplier.address}</p>
                      <div className="mt-2 text-body-sm text-on-surface-variant">
                        <div>Email: {selectedSupplier.email}</div>
                        <div>Phone: {selectedSupplier.phone}</div>
                        <span className="marketplace__badge-verified mt-2 block w-fit text-label-caps">VoltLife Verified</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Gemini AI Requirement Builder */}
              <div className="card marketplace__ai-card">
                <div className="marketplace__panel-header bg-transparent p-0 pb-3">
                  <h3 className="text-headline-sm flex items-center gap-2">
                    💡 VoltAI Requirement Builder
                  </h3>
                  <span className="text-label-caps text-primary">Powered by Gemini</span>
                </div>
                <form onSubmit={handleAIQuerySubmit} className="flex flex-col gap-3">
                  <textarea
                    placeholder="Describe your battery use case in plain English... (e.g. 'Need LFP batteries for 100 kWh solar backup, qty 10')"
                    value={useCaseText}
                    onChange={(e) => setUseCaseText(e.target.value)}
                    rows={3}
                    className="marketplace__ai-input"
                    disabled={!buyerToken}
                  />
                  {!buyerToken && (
                    <p className="text-body-sm text-on-surface-variant italic">
                      * Please login using the Demo Session widget above to activate AI Matching.
                    </p>
                  )}
                  <button 
                    type="submit" 
                    className="marketplace__ai-submit-btn"
                    disabled={matchingLoading || !buyerToken}
                  >
                    {matchingLoading ? 'ANALYZING & MATCHING...' : 'Find Matches'}
                  </button>
                </form>
              </div>

              {/* Search & Filters Panel */}
              <div className="card marketplace__filter-panel">
                <div className="marketplace__panel-header bg-transparent p-0 pb-3 mb-4">
                  <h3 className="text-headline-sm">Advanced Search</h3>
                  <button 
                    onClick={() => {
                      setGradeFilter('');
                      setChemFilter('');
                      setMinCapacity('');
                      setReqQuantity('');
                      setCityFilter('');
                      setSelectedSupplierId(null);
                      setSelectedSupplier(null);
                      setMatchingResults([]);
                    }}
                    className="text-label-caps text-on-surface-variant hover:text-primary"
                  >
                    Clear Filters
                  </button>
                </div>
                <div className="flex flex-col gap-4">
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <label className="text-label-caps text-on-surface-variant block mb-1">Grade</label>
                      <select 
                        value={gradeFilter} 
                        onChange={(e) => setGradeFilter(e.target.value)} 
                        className="marketplace__filter-select"
                      >
                        <option value="">All Grades</option>
                        <option value="S">Grade S</option>
                        <option value="A">Grade A</option>
                        <option value="B">Grade B</option>
                        <option value="C">Grade C</option>
                      </select>
                    </div>
                    <div className="flex-1">
                      <label className="text-label-caps text-on-surface-variant block mb-1">Chemistry</label>
                      <select 
                        value={chemFilter} 
                        onChange={(e) => setChemFilter(e.target.value)} 
                        className="marketplace__filter-select"
                      >
                        <option value="">All Chemistries</option>
                        <option value="NMC">NMC</option>
                        <option value="LFP">LFP</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="text-label-caps text-on-surface-variant block mb-1">City Location</label>
                    <select 
                      value={cityFilter} 
                      onChange={(e) => setCityFilter(e.target.value)} 
                      className="marketplace__filter-select"
                    >
                      <option value="">All Cities</option>
                      <option value="Pune">Pune</option>
                      <option value="Mumbai">Mumbai</option>
                      <option value="Bangalore">Bangalore</option>
                      <option value="Hyderabad">Hyderabad</option>
                    </select>
                  </div>
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <label className="text-label-caps text-on-surface-variant block mb-1">Min Capacity (kWh)</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 100" 
                        value={minCapacity} 
                        onChange={(e) => setMinCapacity(e.target.value ? Number(e.target.value) : '')} 
                        className="marketplace__filter-input"
                      />
                    </div>
                    <div className="flex-1">
                      <label className="text-label-caps text-on-surface-variant block mb-1">Req Quantity (units)</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 10" 
                        value={reqQuantity} 
                        onChange={(e) => setReqQuantity(e.target.value ? Number(e.target.value) : '')} 
                        className="marketplace__filter-input"
                      />
                    </div>
                  </div>
                </div>
              </div>

            </div>

            {/* RIGHT COLUMN: Active Inventory Listings (Spans 7 Columns) */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              
              {/* Listings Header */}
              <div className="flex justify-between items-center bg-surface-container-low p-4 rounded card mb-2">
                <div>
                  <h3 className="text-headline-sm">
                    {matchingResults.length > 0 ? 'AI Recommended Matches' : 'Active Enterprise Lots'}
                  </h3>
                  <p className="text-body-sm text-on-surface-variant">
                    {matchingResults.length > 0 
                      ? `Found ${matchingResults.length} matching published lots sorted by compatibility score.`
                      : `Displaying ${lots.length} published bulk battery lots available for purchase.`
                    }
                  </p>
                </div>
                {matchingResults.length > 0 && (
                  <button 
                    onClick={() => { setMatchingResults([]); setUseCaseText(''); }}
                    className="marketplace__btn-secondary"
                  >
                    Show All Listings
                  </button>
                )}
              </div>

              {/* Lots Grid */}
              <div className="marketplace__listings-grid flex flex-col gap-6">
                
                {/* AI Matching results view */}
                {matchingResults.length > 0 ? (
                  matchingResults.map((match) => (
                    <div key={match.listing_id} className="marketplace__lot-card card glassmorphism marketplace__lot-card--matched animate-fadeIn">
                      {/* Match Score Strip */}
                      <div className="marketplace__match-score-bar">
                        <span className="text-label-caps text-on-primary">
                          🎯 Compatibility Match: {match.match_score}%
                        </span>
                      </div>
                      <div className="p-6">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="text-headline-sm font-bold text-on-surface">{match.title}</h4>
                            <span className="text-label-caps text-on-surface-variant">📍 {match.supplier_name} • {match.supplier_address}</span>
                          </div>
                          <span className="text-headline-sm text-secondary font-bold">{match.price_range}</span>
                        </div>

                        <p className="text-body-sm text-on-surface-variant mb-4">{match.description}</p>

                        {/* Specs Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-surface-container-low p-4 rounded mb-4">
                          <div>
                            <span className="text-label-caps text-on-surface-variant block mb-1">Grade</span>
                            <span className={`marketplace__grade-tag marketplace__grade-tag--${match.grade.toLowerCase()}`}>
                              GRADE {match.grade}
                            </span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Chemistry</span>
                            <span className="text-data-md font-bold">{match.chemistry}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Avg SoH</span>
                            <span className="text-data-md font-bold text-primary">{match.avg_soh}%</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Avg RUL</span>
                            <span className="text-data-md font-bold">{match.avg_rul_years} yrs</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Capacity (Pack)</span>
                            <span className="text-body-sm font-bold">{(match.total_capacity_kwh / match.available_quantity).toFixed(1)} kWh</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Total Capacity</span>
                            <span className="text-body-sm font-bold">{match.total_capacity_kwh} kWh</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Available Qty</span>
                            <span className="text-body-sm font-bold">{match.available_quantity} units</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Min Order (MOQ)</span>
                            <span className="text-body-sm font-bold">{match.moq} units</span>
                          </div>
                        </div>

                        {/* AI Use cases */}
                        <div className="mb-4">
                          <span className="text-label-caps text-on-surface-variant block mb-2">Recommended Use Cases</span>
                          <div className="flex gap-2">
                            {deduceUseCases(match.chemistry, match.grade).map((u, i) => (
                              <span key={i} className="marketplace__badge-usecase text-body-sm">{u}</span>
                            ))}
                          </div>
                        </div>

                        {showQuoteLotId === String(match.listing_id) ? (
                          <div className="mt-4 p-4 bg-surface-container rounded border border-primary animate-fadeIn">
                            <label className="text-label-caps block mb-2" style={{ color: 'var(--primary)' }}>Quote Quantity (units):</label>
                            <div className="flex gap-2 mb-3">
                              <input 
                                type="number" 
                                min={match.moq || 1} 
                                max={match.available_quantity}
                                value={quoteQtyInput}
                                onChange={(e) => setQuoteQtyInput(Math.max(1, Number(e.target.value)))}
                                className="marketplace__filter-input w-24 text-data-md"
                              />
                              <span className="text-body-sm self-center text-on-surface-variant">
                                Min: {match.moq} • Max: {match.available_quantity}
                              </span>
                            </div>
                            <div className="flex gap-2">
                              <button 
                                onClick={() => handleConfirmQuote(String(match.listing_id))}
                                className="marketplace__btn-primary flex-1 text-label-caps"
                              >
                                CONFIRM REQUEST
                              </button>
                              <button 
                                onClick={() => setShowQuoteLotId(null)}
                                className="marketplace__btn-secondary text-label-caps"
                              >
                                CANCEL
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button 
                            onClick={() => {
                              if (!buyerToken) {
                                showToast('Please log in as a buyer first.', 'info');
                                return;
                              }
                              setShowQuoteLotId(String(match.listing_id));
                              setQuoteQtyInput(match.moq || 1);
                            }}
                            className="marketplace__btn-primary w-full mt-4"
                          >
                            REQUEST QUOTE
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                ) : lots.length > 0 ? (
                  // Default published lots view
                  lots.map((lot) => (
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
                          {lot.description || 'Verified second-life battery packs prepared under strict VoltLife evaluation standards.'}
                        </p>

                        {/* Specs Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 bg-surface-container-low p-4 rounded mb-4">
                          <div>
                            <span className="text-label-caps text-on-surface-variant block mb-1">Grade</span>
                            <span className={`marketplace__grade-tag marketplace__grade-tag--${lot.grade.toLowerCase()}`}>
                              GRADE {lot.grade}
                            </span>
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
                            <span className="text-label-caps text-on-surface-variant block">SoC (Sim)</span>
                            <span className="text-data-md font-bold text-yellow-500">100%</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Capacity (Pack)</span>
                            <span className="text-body-sm font-bold">{(lot.total_capacity_kwh / lot.available_quantity).toFixed(1)} kWh</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Total Capacity</span>
                            <span className="text-body-sm font-bold">{lot.total_capacity_kwh} kWh</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Available Qty</span>
                            <span className="text-body-sm font-bold">{lot.available_quantity} units</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Min Order (MOQ)</span>
                            <span className="text-body-sm font-bold">{lot.moq} units</span>
                          </div>
                        </div>

                        {/* Pricing Tiers Table */}
                        {lot.pricing_tiers && lot.pricing_tiers.length > 0 && (
                          <div className="mb-4">
                            <span className="text-label-caps text-on-surface-variant block mb-2">Quantity Pricing Tiers</span>
                            <div className="flex gap-4 bg-surface-container p-3 rounded">
                              {lot.pricing_tiers.map((t, idx) => (
                                <div key={idx} className="text-body-sm">
                                  <span className="text-on-surface-variant">{t.min_quantity}+ units: </span>
                                  <span className="font-bold text-secondary">${t.price_per_kwh}/kWh</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Recommended use cases */}
                        <div className="mb-4">
                          <span className="text-label-caps text-on-surface-variant block mb-2">VoltAI Recommended Use Cases</span>
                          <div className="flex gap-2">
                            {deduceUseCases(lot.chemistry, lot.grade).map((u, i) => (
                              <span key={i} className="marketplace__badge-usecase text-body-sm">{u}</span>
                            ))}
                          </div>
                        </div>

                        {showQuoteLotId === String(lot.id) ? (
                          <div className="mt-4 p-4 bg-surface-container rounded border border-primary animate-fadeIn">
                            <label className="text-label-caps block mb-2" style={{ color: 'var(--primary)' }}>Quote Quantity (units):</label>
                            <div className="flex gap-2 mb-3">
                              <input 
                                type="number" 
                                min={lot.moq || 1} 
                                max={lot.available_quantity}
                                value={quoteQtyInput}
                                onChange={(e) => setQuoteQtyInput(Math.max(1, Number(e.target.value)))}
                                className="marketplace__filter-input w-24 text-data-md"
                              />
                              <span className="text-body-sm self-center text-on-surface-variant">
                                Min: {lot.moq} • Max: {lot.available_quantity}
                              </span>
                            </div>
                            <div className="flex gap-2">
                              <button 
                                onClick={() => handleConfirmQuote(String(lot.id))}
                                className="marketplace__btn-primary flex-1 text-label-caps"
                              >
                                CONFIRM REQUEST
                              </button>
                              <button 
                                onClick={() => setShowQuoteLotId(null)}
                                className="marketplace__btn-secondary text-label-caps"
                              >
                                CANCEL
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button 
                            onClick={() => {
                              if (!buyerToken) {
                                showToast('Please log in as a buyer first.', 'info');
                                return;
                              }
                              setShowQuoteLotId(String(lot.id));
                              setQuoteQtyInput(lot.moq || 1);
                            }}
                            className="marketplace__btn-primary w-full mt-4"
                          >
                            REQUEST QUOTE
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="card p-8 text-center text-body-sm text-on-surface-variant">
                    No published listings found matching the active filters.
                  </div>
                )}
              </div>

            </div>

          </div>

        </div>
      ) : (
        /* --- MY QUOTES & ORDERS TAB VIEW (PHASE 11) --- */
        <div className="marketplace__store-layout animate-fadeIn">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            {/* LEFT COLUMN: Quotes & Orders Lists (Spans 7 Columns) */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              
              {/* Quotes Section */}
              <div className="card p-6">
                <h3 className="text-headline-sm mb-4 flex items-center gap-2">
                  <span style={{ color: 'var(--primary)' }}>📋</span> My Requested Quotes
                </h3>
                {quotes.length === 0 ? (
                  <p className="text-body-sm text-on-surface-variant">No requested quotes found. Request one in the Bulk Store tab.</p>
                ) : (
                  <div className="flex flex-col gap-4">
                    {quotes.map((q) => (
                      <div key={q.id} className="marketplace__quote-card p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="text-label-caps block text-on-surface-variant">Quote #{q.id}</span>
                            <span className="text-body-sm font-bold">Qty: {q.quantity} packs • Lot #{q.inventory_lot_id}</span>
                          </div>
                          <span className={`marketplace__grade-tag marketplace__grade-tag--${q.status === 'accepted' ? 's' : q.status === 'expired' ? 'd' : 'c'}`}>
                            {q.status.toUpperCase()}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-surface-container-low p-3 rounded mb-3 text-body-sm">
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Battery Cost</span>
                            <span className="font-bold">${q.battery_cost.toLocaleString()}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Porter Transport</span>
                            <span className="font-bold">${q.transport_cost.toLocaleString()}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Porter Vehicle</span>
                            <span className="font-bold text-primary">{q.porter_vehicle_type}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Total Price</span>
                            <span className="font-bold text-secondary">${q.total_cost.toLocaleString()}</span>
                          </div>
                        </div>

                        {q.status === 'pending' && (
                          <button 
                            onClick={() => handleCheckout(q.id)}
                            className="marketplace__btn-primary w-full text-label-caps"
                          >
                            💳 Checkout &amp; Pay
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Orders Section */}
              <div className="card p-6">
                <h3 className="text-headline-sm mb-4 flex items-center gap-2">
                  <span style={{ color: 'var(--secondary)' }}>📦</span> My Orders
                </h3>
                {orders.length === 0 ? (
                  <p className="text-body-sm text-on-surface-variant">No completed orders found.</p>
                ) : (
                  <div className="flex flex-col gap-4">
                    {orders.map((o) => (
                      <div key={o.id} className="marketplace__order-card p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="text-label-caps block text-on-surface-variant">Order #{o.id}</span>
                            <span className="text-body-sm font-bold">Qty: {o.quantity} packs • Lot #{o.inventory_lot_id}</span>
                          </div>
                          <span className={`marketplace__grade-tag marketplace__grade-tag--${o.payment_status === 'paid' ? 's' : 'd'}`}>
                            {o.payment_status.toUpperCase()}
                          </span>
                        </div>

                        <div className="flex justify-between items-center bg-surface-container-low p-3 rounded text-body-sm">
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Paid Amount</span>
                            <span className="font-bold text-secondary">${o.total_price.toLocaleString()}</span>
                          </div>
                          <div>
                            <span className="text-label-caps text-on-surface-variant block">Tracking Status</span>
                            <span className="font-bold text-primary">{o.tracking_status.replace('_', ' ').toUpperCase()}</span>
                          </div>
                          <button 
                            onClick={() => handleSelectOrder(o)}
                            className="marketplace__btn-primary text-label-caps"
                          >
                            🚚 Track Order
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>

            {/* RIGHT COLUMN: Order Tracking & Stepper details (Spans 5 Columns) */}
            <div className="lg:col-span-5">
              <div className="card p-6 sticky" style={{ top: 20 }}>
                <h3 className="text-headline-sm mb-4 flex items-center gap-2">
                  <span style={{ color: 'var(--primary)' }}>🚚</span> Live Tracker
                </h3>

                {!selectedOrder ? (
                  <div className="text-center p-8 border border-dashed border-outline-variant rounded text-on-surface-variant text-body-sm">
                    Select an order from the list to track its real-time logistics progress.
                  </div>
                ) : trackingLoading && !trackingData ? (
                  <div className="text-center p-8">
                    <div className="assess__spinner-ring mx-auto mb-4" style={{ width: 32, height: 32 }} />
                    <p className="text-body-sm text-on-surface-variant">Fetching tracking database...</p>
                  </div>
                ) : trackingData ? (
                  <div className="animate-fadeIn">
                    <div className="mb-4 pb-4 border-b border-outline-variant flex justify-between items-start">
                      <div>
                        <h4 className="text-headline-xs text-primary mb-1">Order #{trackingData.order_id}</h4>
                        <p className="text-body-sm text-on-surface-variant">
                          Delivery via: <span className="font-bold text-on-surface">{trackingData.porter_vehicle_type}</span>
                          <br />
                          Est. Delivery: <span className="font-bold text-on-surface">{trackingData.delivery_days} days</span>
                          <br />
                          Shipping Cost: <span className="font-bold text-on-surface">${trackingData.transport_cost.toLocaleString()}</span>
                        </p>
                      </div>
                      <button
                        onClick={() => setShowTicketModal(true)}
                        className="marketplace__btn-tertiary text-label-caps"
                        style={{ fontSize: 11, padding: '4px 8px', color: 'var(--tertiary)', borderColor: 'var(--tertiary)' }}
                      >
                        ⚠️ Raise Issue
                      </button>
                    </div>

                    {/* Sequential Progress Stepper */}
                    <div className="marketplace__stepper">
                      {/* Stepper Progress bar */}
                      <div 
                        className="marketplace__stepper-progress"
                        style={{ 
                          width: `${
                            trackingData.tracking_status === "completed"
                              ? 100
                              : (
                                  [
                                    "confirmed",
                                    "porter_booked",
                                    "seller_notified",
                                    "buyer_notified",
                                    "shipment_started",
                                    "in_transit",
                                    "delivered"
                                  ].indexOf(trackingData.tracking_status) / 6
                                ) * 100
                          }%` 
                        }}
                      />

                      {[
                        { status: "confirmed", num: 1, label: "Paid" },
                        { status: "porter_booked", num: 2, label: "Booked" },
                        { status: "seller_notified", num: 3, label: "Seller" },
                        { status: "buyer_notified", num: 4, label: "Buyer" },
                        { status: "shipment_started", num: 5, label: "Shipped" },
                        { status: "in_transit", num: 6, label: "Transit" },
                        { status: "delivered", num: 7, label: "Arrived" }
                      ].map((step) => {
                        const statusIdx = trackingData.tracking_status === "completed"
                          ? 7
                          : [
                              "confirmed",
                              "porter_booked",
                              "seller_notified",
                              "buyer_notified",
                              "shipment_started",
                              "in_transit",
                              "delivered"
                            ].indexOf(trackingData.tracking_status);
                        const stepIdx = [
                          "confirmed",
                          "porter_booked",
                          "seller_notified",
                          "buyer_notified",
                          "shipment_started",
                          "in_transit",
                          "delivered"
                        ].indexOf(step.status);

                        const isCompleted = stepIdx < statusIdx;
                        const isActive = stepIdx === statusIdx;

                        return (
                          <div 
                            key={step.status} 
                            className={`marketplace__step ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}
                          >
                            <div className="marketplace__step-circle">
                              {isCompleted ? '✓' : step.num}
                            </div>
                            <span className="marketplace__step-label">{step.label}</span>
                          </div>
                        );
                      })}
                    </div>

                    {/* Phase 12: Confirm Receipt Panel */}
                    {trackingData.tracking_status === "delivered" && (
                      <div className="marketplace__completion-panel card glassmorphism p-4 border border-secondary mb-4 animate-fadeIn">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-secondary" style={{ fontSize: 24 }}>🎁</span>
                          <div>
                            <h4 className="text-headline-xs font-bold text-on-surface">Shipment Delivered</h4>
                            <p className="text-body-sm text-on-surface-variant">
                              The battery lot has arrived at your destination. Please verify the physical QR passport and confirm receipt.
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={handleConfirmReceipt}
                          className="marketplace__btn-secondary w-full text-label-caps font-bold"
                          style={{ borderColor: 'var(--secondary)', color: 'var(--secondary)', padding: '10px' }}
                        >
                          ✓ Confirm Delivery Receipt
                        </button>
                      </div>
                    )}
                    {trackingData.tracking_status === "completed" && (
                      <div className="marketplace__completion-panel card glassmorphism p-4 border border-primary mb-4 animate-fadeIn" style={{ borderLeft: '4px solid var(--primary)' }}>
                        <div className="flex items-center gap-3">
                          <span className="text-primary" style={{ fontSize: 24 }}>🎉</span>
                          <div>
                            <h4 className="text-headline-xs font-bold text-primary">Order Completed</h4>
                            <p className="text-body-sm text-on-surface-variant">
                              Delivery receipt confirmed. Battery lifecycle record updated to second-life active.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Timeline Log */}
                    <div className="mt-6">
                      <h5 className="text-label-caps text-on-surface-variant mb-3">Event Timeline Log</h5>
                      <div className="flex flex-col gap-3 bg-surface-container p-4 rounded text-body-sm" style={{ maxHeight: 180, overflowY: 'auto' }}>
                        {trackingData.events.length === 0 ? (
                          <p className="text-on-surface-variant italic">No tracking events recorded yet.</p>
                        ) : (
                          trackingData.events.map((ev: any) => (
                            <div key={ev.id} className="flex justify-between border-b border-outline-variant/30 pb-2">
                              <div>
                                <span className="font-bold text-primary block">{ev.event_type.replace('_', ' ').toUpperCase()}</span>
                                <span className="text-on-surface-variant text-xs">{ev.notes}</span>
                              </div>
                              <span className="text-xs text-on-surface-variant font-mono self-center">
                                {new Date(ev.occurred_at).toLocaleTimeString()}
                              </span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Phase 12 Support Tickets Log */}
                    {trackingData.support_tickets && trackingData.support_tickets.length > 0 && (
                      <div className="mt-6 pt-4 border-t border-outline-variant/30">
                        <h5 className="text-label-caps text-on-surface-variant mb-3">Support Tickets Log</h5>
                        <div className="flex flex-col gap-3">
                          {trackingData.support_tickets.map((ticket: any) => (
                            <div key={ticket.id} className="marketplace__ticket-item p-3 rounded bg-surface-container-low">
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-xs text-on-surface-variant font-mono">Ticket #{ticket.id}</span>
                                <span className={`marketplace__ticket-status marketplace__ticket-status--${ticket.status}`}>
                                  {ticket.status.toUpperCase()}
                                </span>
                              </div>
                              <p className="text-body-sm text-on-surface">{ticket.issue_text}</p>
                              <span className="text-xs text-on-surface-variant font-mono block mt-1">
                                Raised: {new Date(ticket.created_at).toLocaleString()}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Simulation Controller Panel */}
                    <div className="sim-controls">
                      <h5>🛠️ Logistics Simulation Console</h5>
                      <p className="text-body-sm text-on-surface-variant mb-3" style={{ fontSize: 12 }}>
                        Trigger backend status callbacks manually to test transition guards or launch automatic background execution.
                      </p>
                      
                      <div className="flex flex-wrap gap-2 mb-3">
                        <button 
                          onClick={handleTriggerAutoSimulation}
                          disabled={trackingData.tracking_status !== 'confirmed'}
                          className="marketplace__btn-primary text-label-caps"
                          style={{ flex: '1 1 100%' }}
                        >
                          ⚡ Run Auto-Simulation Loop
                        </button>
                      </div>

                      <div className="flex gap-2">
                        <select 
                          id="manual-status-select"
                          className="marketplace__filter-select flex-1"
                          defaultValue=""
                        >
                          <option value="" disabled>Select target state...</option>
                          <option value="porter_booked">Porter Booked</option>
                          <option value="seller_notified">Seller Notified</option>
                          <option value="buyer_notified">Buyer Notified</option>
                          <option value="shipment_started">Shipment Started</option>
                          <option value="in_transit">In Transit</option>
                          <option value="delivered">Delivered</option>
                        </select>
                        <button 
                          onClick={() => {
                            const val = (document.getElementById('manual-status-select') as HTMLSelectElement).value;
                            if (val) handleTriggerStatus(val);
                          }}
                          className="marketplace__btn-tertiary text-label-caps"
                        >
                          Advance State
                        </button>
                      </div>
                    </div>

                  </div>
                ) : (
                  <div className="text-center p-8 text-on-surface-variant text-body-sm">
                    Error loading tracking data.
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      )}

      {/* Technical Footer Overlay */}
      <footer className="marketplace__footer mt-8 text-label-caps text-on-surface-variant" style={{ opacity: 0.4 }}>
        <div className="flex gap-6">
          <span>ENC: AES-256-GCM</span>
          <span>LATENCY: 14MS</span>
          <span>MARKET_STATUS: OPEN</span>
        </div>
        <div className="flex gap-6">
          <span>SECURE PROTOCOL ACTIVE</span>
          <span className="text-primary">VOLTLIFE_CORE_V.4.3</span>
        </div>
      </footer>

      {/* Support Ticket Modal (Phase 12) */}
      {showTicketModal && (
        <div className="marketplace__modal-overlay animate-fadeIn">
          <div className="marketplace__modal-content card glassmorphism animate-scaleUp">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-outline-variant">
              <h3 className="text-headline-sm text-primary flex items-center gap-2">
                ⚠️ Raise Support Ticket
              </h3>
              <button 
                onClick={() => { setShowTicketModal(false); setTicketIssueText(''); }}
                className="marketplace__close-btn"
                style={{ fontSize: 24 }}
              >
                ×
              </button>
            </div>
            <p className="text-body-sm text-on-surface-variant mb-4">
              Describe any issues with Order #{selectedOrder?.id}. A VoltLife representative will address this immediately.
            </p>
            <form onSubmit={handleRaiseIssue}>
              <textarea
                placeholder="Describe your issue in detail (e.g. damaged packaging, delivery delay, etc.)..."
                value={ticketIssueText}
                onChange={(e) => setTicketIssueText(e.target.value)}
                rows={4}
                className="marketplace__ai-input w-full p-3 mb-4"
                required
              />
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => { setShowTicketModal(false); setTicketIssueText(''); }}
                  className="marketplace__btn-secondary text-label-caps"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingTicket || !ticketIssueText.trim()}
                  className="marketplace__btn-primary text-label-caps"
                >
                  {submittingTicket ? 'SUBMITTING...' : 'SUBMIT TICKET'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Marketplace;

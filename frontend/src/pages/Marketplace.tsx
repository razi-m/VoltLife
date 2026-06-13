import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Card, MetricCard } from '../components/ui/Card';
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
  certification: string;
  img_alt: string;
  img_url: string;
}

interface SummaryStats {
  total_asset_value: string;
  auctions_count: number;
  recently_sold: number;
  second_life_index: number;
}

const Marketplace: React.FC = () => {
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [auctions, setAuctions] = useState<AuctionItem[]>([]);
  const [lots, setLots] = useState<LotItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>(''); // '', 'A', 'B', 'C'
  const [biddingId, setBiddingId] = useState<number | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' } | null>(null);

  const fetchData = async (selectedGrade = filter) => {
    try {
      const [sumRes, aucRes, lotsRes] = await Promise.all([
        api.marketplace.summary(),
        api.marketplace.auctions(selectedGrade),
        api.marketplace.lots(),
      ]);
      setSummary(sumRes);
      setAuctions(aucRes);
      setLots(lotsRes);
    } catch (err) {
      console.error('Failed to load marketplace data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleFilterChange = (grade: string) => {
    setFilter(grade);
    fetchData(grade);
  };

  const handlePlaceBid = async (id: number, bpan: string) => {
    setBiddingId(id);
    try {
      const res = await api.marketplace.bid(id);
      showToast(`Bid placed on ${bpan}! New bid: $${res.new_bid.toLocaleString()}`, 'success');
      // Refresh auction list to reflect the new bid
      fetchData();
    } catch (err) {
      console.error('Failed to place bid:', err);
      showToast('Error placing bid. Please try again.', 'info');
    } finally {
      setBiddingId(null);
    }
  };

  const showToast = (message: string, type: 'success' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
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
            Asset Monetization &amp; Procurement Hub • v4.2.0-STABLE
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

      {/* Main Layout Grid */}
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
                {/* Grid Lines */}
                <line x1="0" y1="50" x2="400" y2="50" stroke="var(--outline-variant)" strokeDasharray="2,2" />
                <line x1="0" y1="100" x2="400" y2="100" stroke="var(--outline-variant)" strokeDasharray="2,2" />
                <line x1="0" y1="150" x2="400" y2="150" stroke="var(--outline-variant)" strokeDasharray="2,2" />
                
                {/* Area under curve */}
                <path d="M 0 180 Q 50 150 100 160 T 200 120 T 300 130 T 400 60 V 200 H 0 Z" fill="url(#chart-glow)" />
                
                {/* Curve */}
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

      {/* Featured Bulk Lots */}
      <div className="marketplace__lots-section">
        <div className="marketplace__section-header flex justify-between items-center mb-4">
          <h3 className="text-headline-sm">Featured Bulk Lots</h3>
          <span className="text-label-caps text-primary cursor-pointer hover:underline">
            View all enterprise lots →
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {lots.map((lot) => (
            <div key={lot.id} className="marketplace__lot-card card group">
              <div className="marketplace__lot-image-container">
                <img 
                  src={lot.img_url} 
                  alt={lot.img_alt} 
                  className="marketplace__lot-image" 
                />
                <div className="marketplace__lot-badge text-label-caps">
                  {lot.units}
                </div>
              </div>
              <div className="marketplace__lot-content">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-headline-sm font-bold text-on-surface">{lot.title}</h4>
                  <span className="text-data-md text-secondary font-bold">{lot.price}</span>
                </div>
                <div className="marketplace__lot-details">
                  <div className="marketplace__lot-detail-row">
                    <span className="text-on-surface-variant">Origin:</span>
                    <span className="text-on-surface font-bold">{lot.origin}</span>
                  </div>
                  <div className="marketplace__lot-detail-row">
                    <span className="text-on-surface-variant">Avg SoH:</span>
                    <span className="text-on-surface font-bold">{lot.avg_soh}</span>
                  </div>
                  <div className="marketplace__lot-detail-row">
                    <span className="text-on-surface-variant">Certification:</span>
                    <span className="text-on-surface font-bold">{lot.certification}</span>
                  </div>
                </div>
                <button className="marketplace__inspect-btn">
                  INSPECT DOCUMENTATION
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Technical Footer Overlay */}
      <footer className="marketplace__footer mt-8 text-label-caps text-on-surface-variant" style={{ opacity: 0.4 }}>
        <div className="flex gap-6">
          <span>ENC: AES-256-GCM</span>
          <span>LATENCY: 14MS</span>
          <span>MARKET_STATUS: OPEN</span>
        </div>
        <div className="flex gap-6">
          <span>SECURE PROTOCOL ACTIVE</span>
          <span className="text-primary">VOLTLIFE_CORE_V.4.2</span>
        </div>
      </footer>
    </div>
  );
};

export default Marketplace;

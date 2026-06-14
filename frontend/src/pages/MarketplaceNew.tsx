import React, { useState, useMemo } from 'react';
import './MarketplaceNew.css';

// ── n8n Webhook URL ────────────────────────────────
// Paste your n8n webhook URL below. This webhook receives contact requests
// and triggers a WhatsApp message via n8n automation.
const N8N_WEBHOOK_URL = '';

// ── Types ──────────────────────────────────────────
interface Listing {
  id: string;
  companyName: string;
  grade: string;
  rating: number;
  chemistry: string;
  capacityKwh: number;
  quantity: number;
  pricePerUnit: number;
  state: string;
  city: string;
  phone: string;
  email: string;
  createdAt: string;
}

// ── Demo Listings ──────────────────────────────────
const DEMO_LISTINGS: Listing[] = [
  { id: '1', companyName: 'Tata Green Energy', grade: 'A', rating: 4.5, chemistry: 'NMC', capacityKwh: 21.5, quantity: 120, pricePerUnit: 18500, state: 'MH', city: 'Pune', phone: '+919876543210', email: 'sales@tatagreenev.in', createdAt: '2026-06-10' },
  { id: '2', companyName: 'Exide Second Life', grade: 'B', rating: 4.2, chemistry: 'LFP', capacityKwh: 15.0, quantity: 85, pricePerUnit: 12000, state: 'KA', city: 'Bangalore', phone: '+919876543211', email: 'info@exidesl.in', createdAt: '2026-06-08' },
  { id: '3', companyName: 'Amara Raja Relife', grade: 'S', rating: 4.8, chemistry: 'NMC', capacityKwh: 30.0, quantity: 40, pricePerUnit: 28000, state: 'TG', city: 'Hyderabad', phone: '+919876543212', email: 'relife@amararaja.com', createdAt: '2026-06-12' },
  { id: '4', companyName: 'Ola Cell Reuse', grade: 'A', rating: 4.3, chemistry: 'NCA', capacityKwh: 25.0, quantity: 200, pricePerUnit: 22000, state: 'TN', city: 'Chennai', phone: '+919876543213', email: 'cells@olaelectric.com', createdAt: '2026-06-11' },
  { id: '5', companyName: 'Ather Recycle Hub', grade: 'C', rating: 3.9, chemistry: 'LFP', capacityKwh: 10.0, quantity: 300, pricePerUnit: 6500, state: 'KA', city: 'Bangalore', phone: '+919876543214', email: 'recycle@atherenergy.com', createdAt: '2026-06-09' },
  { id: '6', companyName: 'Delhi EV Parts', grade: 'B', rating: 4.0, chemistry: 'NMC', capacityKwh: 18.0, quantity: 65, pricePerUnit: 14000, state: 'DL', city: 'New Delhi', phone: '+919876543215', email: 'contact@delhievparts.in', createdAt: '2026-06-07' },
  { id: '7', companyName: 'GreenVolt Gujarat', grade: 'A', rating: 4.6, chemistry: 'LFP', capacityKwh: 22.0, quantity: 150, pricePerUnit: 20000, state: 'GJ', city: 'Ahmedabad', phone: '+919876543216', email: 'sales@greenvolt.in', createdAt: '2026-06-13' },
  { id: '8', companyName: 'Kolkata Battery Co', grade: 'D', rating: 3.5, chemistry: 'NMC', capacityKwh: 8.0, quantity: 500, pricePerUnit: 3500, state: 'WB', city: 'Kolkata', phone: '+919876543217', email: 'info@kolbattery.in', createdAt: '2026-06-06' },
  { id: '9', companyName: 'Rajasthan Solar Store', grade: 'B', rating: 4.1, chemistry: 'LFP', capacityKwh: 20.0, quantity: 90, pricePerUnit: 13500, state: 'RJ', city: 'Jaipur', phone: '+919876543218', email: 'solar@rajstore.in', createdAt: '2026-06-10' },
  { id: '10', companyName: 'MP Energy Works', grade: 'C', rating: 3.8, chemistry: 'NMC', capacityKwh: 12.0, quantity: 110, pricePerUnit: 7000, state: 'MP', city: 'Bhopal', phone: '+919876543219', email: 'works@mpenergy.in', createdAt: '2026-06-09' },
];

const GRADE_COLORS: Record<string, string> = { S: '#4edea3', A: '#3b82f6', B: '#06b6d4', C: '#f59e0b', D: '#ff5451' };

// ── Grading Parameters used to assign a battery grade ──
const GRADE_PARAMS: Record<string, { soh: string; cycles: string; internalResistance: string; voltage: string; tempStability: string }> = {
  S: { soh: '≥ 95%', cycles: '≥ 2500 cycles', internalResistance: '< 25 mΩ', voltage: 'Within 1% of nominal', tempStability: 'Excellent (no thermal drift)' },
  A: { soh: '90 – 94%', cycles: '2000 – 2500 cycles', internalResistance: '25 – 35 mΩ', voltage: 'Within 2% of nominal', tempStability: 'Very Good' },
  B: { soh: '80 – 89%', cycles: '1500 – 2000 cycles', internalResistance: '35 – 50 mΩ', voltage: 'Within 4% of nominal', tempStability: 'Good' },
  C: { soh: '70 – 79%', cycles: '1000 – 1500 cycles', internalResistance: '50 – 70 mΩ', voltage: 'Within 6% of nominal', tempStability: 'Moderate' },
  D: { soh: '< 70%', cycles: '< 1000 cycles', internalResistance: '> 70 mΩ', voltage: 'Beyond 6% of nominal', tempStability: 'Poor' },
};

// ── Indian States for the map ──────────────────────
const INDIA_STATES: Record<string, { name: string; x: number; y: number }> = {
  JK: { name: 'Jammu & Kashmir', x: 175, y: 45 },
  HP: { name: 'Himachal Pradesh', x: 195, y: 80 },
  PB: { name: 'Punjab', x: 170, y: 95 },
  HR: { name: 'Haryana', x: 185, y: 115 },
  DL: { name: 'Delhi', x: 198, y: 120 },
  UK: { name: 'Uttarakhand', x: 220, y: 90 },
  UP: { name: 'Uttar Pradesh', x: 245, y: 135 },
  RJ: { name: 'Rajasthan', x: 150, y: 155 },
  GJ: { name: 'Gujarat', x: 110, y: 210 },
  MP: { name: 'Madhya Pradesh', x: 210, y: 200 },
  BR: { name: 'Bihar', x: 305, y: 150 },
  JH: { name: 'Jharkhand', x: 300, y: 175 },
  WB: { name: 'West Bengal', x: 325, y: 185 },
  OR: { name: 'Odisha', x: 295, y: 225 },
  CG: { name: 'Chhattisgarh', x: 265, y: 220 },
  MH: { name: 'Maharashtra', x: 175, y: 260 },
  TG: { name: 'Telangana', x: 225, y: 285 },
  AP: { name: 'Andhra Pradesh', x: 240, y: 320 },
  KA: { name: 'Karnataka', x: 190, y: 330 },
  GA: { name: 'Goa', x: 155, y: 310 },
  KL: { name: 'Kerala', x: 195, y: 390 },
  TN: { name: 'Tamil Nadu', x: 230, y: 375 },
  AS: { name: 'Assam', x: 380, y: 130 },
  NE: { name: 'Northeast', x: 395, y: 150 },
};

const Marketplace: React.FC = () => {
  const isSupplier = !!localStorage.getItem('supplier_token');
  const [listings, setListings] = useState<Listing[]>(DEMO_LISTINGS);
  const [hoveredState, setHoveredState] = useState<string | null>(null);
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [selectedSeller, setSelectedSeller] = useState<Listing | null>(null);
  const [requestSent, setRequestSent] = useState<Set<string>>(new Set());
  const [showListForm, setShowListForm] = useState(false);
  const [formData, setFormData] = useState({
    companyName: '', grade: 'A', chemistry: 'NMC', capacityKwh: '',
    quantity: '', pricePerUnit: '', state: 'MH', city: '', phone: '', email: '', rating: '',
  });

  const stateListings = useMemo(() => {
    const map: Record<string, Listing[]> = {};
    listings.forEach(l => {
      if (!map[l.state]) map[l.state] = [];
      map[l.state].push(l);
    });
    return map;
  }, [listings]);

  const filteredListings = selectedState
    ? listings.filter(l => l.state === selectedState)
    : listings;

  const handleListSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newListing: Listing = {
      id: Date.now().toString(),
      companyName: formData.companyName,
      grade: formData.grade,
      rating: Number(formData.rating) || 4.0,
      chemistry: formData.chemistry,
      capacityKwh: Number(formData.capacityKwh),
      quantity: Number(formData.quantity),
      pricePerUnit: Number(formData.pricePerUnit),
      state: formData.state,
      city: formData.city,
      phone: formData.phone,
      email: formData.email,
      createdAt: new Date().toISOString().slice(0, 10),
    };
    setListings(prev => [newListing, ...prev]);
    setShowListForm(false);
    setFormData({ companyName: '', grade: 'A', chemistry: 'NMC', capacityKwh: '', quantity: '', pricePerUnit: '', state: 'MH', city: '', phone: '', email: '', rating: '' });
  };

  const handleRequest = async (listing: Listing) => {
    setRequestSent(prev => new Set(prev).add(listing.id));

    if (N8N_WEBHOOK_URL) {
      try {
        await fetch(N8N_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'battery_inquiry',
            seller: {
              company: listing.companyName,
              phone: listing.phone,
              email: listing.email,
              city: listing.city,
              state: listing.state,
            },
            battery: {
              grade: listing.grade,
              chemistry: listing.chemistry,
              capacity_kwh: listing.capacityKwh,
              quantity_available: listing.quantity,
              price_per_unit: listing.pricePerUnit,
            },
            buyer: {
              name: localStorage.getItem('supplier_username') || localStorage.getItem('buyer_username') || 'VoltLife User',
              company: localStorage.getItem('supplier_company') || 'N/A',
              timestamp: new Date().toISOString(),
            },
            message: `Hi ${listing.companyName}, I'm interested in your ${listing.grade}-grade ${listing.chemistry} batteries (${listing.capacityKwh} kWh, ₹${listing.pricePerUnit.toLocaleString('en-IN')}/unit). ${listing.quantity} units available. Please share more details. — via VoltLife Marketplace`,
          }),
        });
      } catch { /* webhook failed silently */ }
    }
  };

  const gradeInventory = (seller: Listing) => {
    const related = listings.filter(l => l.companyName === seller.companyName);
    const grades: Record<string, number> = {};
    related.forEach(l => { grades[l.grade] = (grades[l.grade] || 0) + l.quantity; });
    return grades;
  };

  // ── Seller View: List Form + My Listings ─────────
  if (isSupplier) {
    const myListings = listings.filter(l => l.createdAt >= '2026-06-01');
    return (
      <div className="page-content">
        <div className="page-header">
          <h1 className="page-title">Marketplace — Seller Portal</h1>
          <button className="mp__add-btn" onClick={() => setShowListForm(!showListForm)}>
            {showListForm ? '✕ Cancel' : '+ List Batteries'}
          </button>
        </div>

        {selectedSeller && (
          <div className="mp__modal-overlay" onClick={() => setSelectedSeller(null)}>
            <div className="mp__modal" onClick={e => e.stopPropagation()}>
              <button className="mp__modal-close" onClick={() => setSelectedSeller(null)}>✕</button>
              <div className="mp__modal-header">
                <h2>{selectedSeller.companyName}</h2>
                <div className="mp__modal-meta">
                  <span className="mp__grade-badge" style={{ background: GRADE_COLORS[selectedSeller.grade] }}>Grade {selectedSeller.grade}</span>
                  <span className="mp__stars">{'★'.repeat(Math.round(selectedSeller.rating))}{'☆'.repeat(5 - Math.round(selectedSeller.rating))} {selectedSeller.rating}</span>
                </div>
              </div>
              <div className="mp__modal-body">
                <div className="mp__modal-section">
                  <h4>Contact</h4>
                  <div className="mp__modal-info">
                    <div>📍 {selectedSeller.city}, {INDIA_STATES[selectedSeller.state]?.name || selectedSeller.state}</div>
                    <div>📞 {selectedSeller.phone}</div>
                    <div>✉ {selectedSeller.email}</div>
                  </div>
                  <div className="mp__contact-actions">
                    <a className="mp__contact-btn mp__contact-btn--whatsapp" href={`https://wa.me/${selectedSeller.phone.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer">
                      💬 Message on WhatsApp
                    </a>
                    <a className="mp__contact-btn mp__contact-btn--call" href={`tel:${selectedSeller.phone}`}>
                      📞 Call Now ({selectedSeller.phone})
                    </a>
                  </div>
                </div>
                <div className="mp__modal-section">
                  <h4>Grading Parameters (Grade {selectedSeller.grade})</h4>
                  <div className="mp__grading-params">
                    {Object.entries(GRADE_PARAMS[selectedSeller.grade] || {}).map(([key, value]) => (
                      <div key={key} className="mp__grading-row">
                        <span className="mp__spec-label">{key.replace(/([A-Z])/g, ' $1').replace(/^./, c => c.toUpperCase())}</span>
                        <span className="mp__spec-value">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mp__modal-section">
                  <h4>Listed Batteries</h4>
                  <div className="mp__modal-listings">
                    {listings.filter(l => l.companyName === selectedSeller.companyName).map(l => (
                      <div key={l.id} className="mp__modal-listing-row">
                        <span className="mp__grade-badge mp__grade-badge--sm" style={{ background: GRADE_COLORS[l.grade] }}>{l.grade}</span>
                        <span>{l.chemistry} · {l.capacityKwh} kWh</span>
                        <span>{l.quantity} units</span>
                        <span className="mp__price">₹{l.pricePerUnit.toLocaleString('en-IN')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {showListForm && (
          <div className="mp__list-form-card">
            <h3 className="mp__form-title">List Your Batteries</h3>
            <form onSubmit={handleListSubmit} className="mp__list-form">
              <div className="mp__form-grid">
                <div className="mp__form-field">
                  <label>Company Name *</label>
                  <input required value={formData.companyName} onChange={e => setFormData(p => ({ ...p, companyName: e.target.value }))} placeholder="Your company name" />
                </div>
                <div className="mp__form-field">
                  <label>Battery Grade *</label>
                  <select value={formData.grade} onChange={e => setFormData(p => ({ ...p, grade: e.target.value }))}>
                    {['S', 'A', 'B', 'C', 'D'].map(g => <option key={g} value={g}>Grade {g}</option>)}
                  </select>
                </div>
                <div className="mp__form-field">
                  <label>Rating (1-5)</label>
                  <input type="number" min="1" max="5" step="0.1" value={formData.rating} onChange={e => setFormData(p => ({ ...p, rating: e.target.value }))} placeholder="4.5" />
                </div>
                <div className="mp__form-field">
                  <label>Chemistry *</label>
                  <select value={formData.chemistry} onChange={e => setFormData(p => ({ ...p, chemistry: e.target.value }))}>
                    {['NMC', 'LFP', 'NCA', 'LTO'].map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div className="mp__form-field">
                  <label>Capacity (kWh) *</label>
                  <input required type="number" step="0.1" value={formData.capacityKwh} onChange={e => setFormData(p => ({ ...p, capacityKwh: e.target.value }))} placeholder="21.5" />
                </div>
                <div className="mp__form-field">
                  <label>Quantity *</label>
                  <input required type="number" value={formData.quantity} onChange={e => setFormData(p => ({ ...p, quantity: e.target.value }))} placeholder="100" />
                </div>
                <div className="mp__form-field">
                  <label>Price per Unit (₹) *</label>
                  <input required type="number" value={formData.pricePerUnit} onChange={e => setFormData(p => ({ ...p, pricePerUnit: e.target.value }))} placeholder="18500" />
                </div>
                <div className="mp__form-field">
                  <label>State *</label>
                  <select value={formData.state} onChange={e => setFormData(p => ({ ...p, state: e.target.value }))}>
                    {Object.entries(INDIA_STATES).map(([code, s]) => <option key={code} value={code}>{s.name}</option>)}
                  </select>
                </div>
                <div className="mp__form-field">
                  <label>City *</label>
                  <input required value={formData.city} onChange={e => setFormData(p => ({ ...p, city: e.target.value }))} placeholder="Mumbai" />
                </div>
                <div className="mp__form-field">
                  <label>Phone *</label>
                  <input required type="tel" value={formData.phone} onChange={e => setFormData(p => ({ ...p, phone: e.target.value }))} placeholder="+919876543210" />
                </div>
                <div className="mp__form-field mp__form-field--wide">
                  <label>Email *</label>
                  <input required type="email" value={formData.email} onChange={e => setFormData(p => ({ ...p, email: e.target.value }))} placeholder="sales@company.in" />
                </div>
              </div>
              <button type="submit" className="mp__form-submit">Publish Listing →</button>
            </form>
          </div>
        )}

        <div className="mp__my-listings">
          <h3 className="mp__section-title">All Listings ({myListings.length})</h3>
          <div className="mp__listing-grid">
            {myListings.map(l => (
              <div key={l.id} className="mp__listing-card" onClick={() => setSelectedSeller(l)} style={{ cursor: 'pointer' }}>
                <div className="mp__listing-header">
                  <span className="mp__grade-badge" style={{ background: GRADE_COLORS[l.grade] }}>Grade {l.grade}</span>
                  <span className="mp__chem-tag">{l.chemistry}</span>
                </div>
                <h4 className="mp__listing-company">{l.companyName}</h4>
                <div className="mp__listing-specs">
                  <div><span className="mp__spec-label">Capacity</span><span className="mp__spec-value">{l.capacityKwh} kWh</span></div>
                  <div><span className="mp__spec-label">Quantity</span><span className="mp__spec-value">{l.quantity} units</span></div>
                  <div><span className="mp__spec-label">Price</span><span className="mp__spec-value">₹{l.pricePerUnit.toLocaleString('en-IN')}</span></div>
                  <div><span className="mp__spec-label">Location</span><span className="mp__spec-value">{l.city}, {l.state}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ── Buyer / Default View: Map + Listings ─────────
  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Battery Marketplace</h1>
        <span className="mp__listing-count">{listings.length} sellers across India</span>
      </div>

      {/* Seller profile modal */}
      {selectedSeller && (
        <div className="mp__modal-overlay" onClick={() => setSelectedSeller(null)}>
          <div className="mp__modal" onClick={e => e.stopPropagation()}>
            <button className="mp__modal-close" onClick={() => setSelectedSeller(null)}>✕</button>
            <div className="mp__modal-header">
              <h2>{selectedSeller.companyName}</h2>
              <div className="mp__modal-meta">
                <span className="mp__grade-badge" style={{ background: GRADE_COLORS[selectedSeller.grade] }}>Grade {selectedSeller.grade}</span>
                <span className="mp__stars">{'★'.repeat(Math.round(selectedSeller.rating))}{'☆'.repeat(5 - Math.round(selectedSeller.rating))} {selectedSeller.rating}</span>
              </div>
            </div>
            <div className="mp__modal-body">
              <div className="mp__modal-section">
                <h4>Contact</h4>
                <div className="mp__modal-info">
                  <div>📍 {selectedSeller.city}, {INDIA_STATES[selectedSeller.state]?.name || selectedSeller.state}</div>
                  <div>📞 {selectedSeller.phone}</div>
                  <div>✉ {selectedSeller.email}</div>
                </div>
                <div className="mp__contact-actions">
                  <a className="mp__contact-btn mp__contact-btn--whatsapp" href={`https://wa.me/${selectedSeller.phone.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer">
                    💬 Message on WhatsApp
                  </a>
                  <a className="mp__contact-btn mp__contact-btn--call" href={`tel:${selectedSeller.phone}`}>
                    📞 Call Now ({selectedSeller.phone})
                  </a>
                </div>
              </div>
              <div className="mp__modal-section">
                <h4>Grading Parameters (Grade {selectedSeller.grade})</h4>
                <div className="mp__grading-params">
                  {Object.entries(GRADE_PARAMS[selectedSeller.grade] || {}).map(([key, value]) => (
                    <div key={key} className="mp__grading-row">
                      <span className="mp__spec-label">{key.replace(/([A-Z])/g, ' $1').replace(/^./, c => c.toUpperCase())}</span>
                      <span className="mp__spec-value">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mp__modal-section">
                <h4>Inventory by Grade</h4>
                <div className="mp__grade-inventory">
                  {Object.entries(gradeInventory(selectedSeller)).map(([grade, qty]) => (
                    <div key={grade} className="mp__grade-bar">
                      <span className="mp__grade-badge mp__grade-badge--sm" style={{ background: GRADE_COLORS[grade] }}>Grade {grade}</span>
                      <div className="mp__grade-qty">{qty} units</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mp__modal-section">
                <h4>Listed Batteries</h4>
                <div className="mp__modal-listings">
                  {listings.filter(l => l.companyName === selectedSeller.companyName).map(l => (
                    <div key={l.id} className="mp__modal-listing-row">
                      <span className="mp__grade-badge mp__grade-badge--sm" style={{ background: GRADE_COLORS[l.grade] }}>{l.grade}</span>
                      <span>{l.chemistry} · {l.capacityKwh} kWh</span>
                      <span>{l.quantity} units</span>
                      <span className="mp__price">₹{l.pricePerUnit.toLocaleString('en-IN')}</span>
                      <button
                        className={`mp__request-btn ${requestSent.has(l.id) ? 'mp__request-btn--sent' : ''}`}
                        disabled={requestSent.has(l.id)}
                        onClick={() => handleRequest(l)}
                      >
                        {requestSent.has(l.id) ? '✓ Sent' : 'Request'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mp__layout">
        {/* India Map */}
        <div className="mp__map-container">
          <h3 className="mp__section-title">Sellers Across India</h3>
          <div className="mp__map-wrapper">
            <svg viewBox="0 0 450 440" className="mp__india-map">
              {/* India outline - simplified */}
              <path className="mp__india-outline" d="
                M175,30 L200,25 L230,40 L250,35 L260,50 L240,65 L250,75 L265,80
                L280,75 L300,85 L320,80 L350,90 L380,100 L400,120 L410,140
                L400,155 L390,170 L380,160 L370,170 L360,165 L350,175
                L340,170 L335,185 L340,200 L335,210 L325,220 L320,235
                L310,240 L305,255 L295,260 L290,275 L280,285 L275,300
                L265,310 L260,325 L250,340 L240,355 L235,370 L225,385
                L215,395 L205,400 L195,395 L190,380 L185,365 L180,350
                L170,335 L160,315 L155,300 L148,290 L140,280 L135,265
                L130,250 L120,240 L110,225 L100,210 L95,195 L100,180
                L110,170 L120,160 L130,150 L140,140 L145,125 L150,115
                L155,105 L160,90 L165,70 L170,50 Z
              " />

              {/* State markers */}
              {Object.entries(INDIA_STATES).map(([code, state]) => {
                const sellers = stateListings[code];
                const count = sellers?.length || 0;
                const isHovered = hoveredState === code;
                const isSelected = selectedState === code;
                const hasListings = count > 0;

                return (
                  <g key={code}
                    onMouseEnter={() => hasListings && setHoveredState(code)}
                    onMouseLeave={() => setHoveredState(null)}
                    onClick={() => hasListings && setSelectedState(isSelected ? null : code)}
                    style={{ cursor: hasListings ? 'pointer' : 'default' }}
                  >
                    {/* Pulse ring for active states */}
                    {hasListings && (
                      <circle
                        cx={state.x} cy={state.y}
                        r={isHovered || isSelected ? 18 : 14}
                        className={`mp__state-ring ${isSelected ? 'mp__state-ring--selected' : ''}`}
                      />
                    )}
                    {/* Dot */}
                    <circle
                      cx={state.x} cy={state.y}
                      r={hasListings ? (isHovered || isSelected ? 8 : 6) : 3}
                      className={`mp__state-dot ${hasListings ? 'mp__state-dot--active' : ''} ${isSelected ? 'mp__state-dot--selected' : ''}`}
                    />
                    {/* Count badge */}
                    {hasListings && (
                      <text x={state.x} y={state.y + 1} className="mp__state-count" textAnchor="middle" dominantBaseline="middle">
                        {count}
                      </text>
                    )}
                    {/* Label */}
                    <text x={state.x} y={state.y + (hasListings ? 22 : 12)} className="mp__state-label" textAnchor="middle">
                      {code}
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* Hover tooltip */}
            {hoveredState && stateListings[hoveredState] && (
              <div className="mp__map-tooltip">
                <div className="mp__tooltip-title">{INDIA_STATES[hoveredState]?.name}</div>
                <div className="mp__tooltip-count">{stateListings[hoveredState].length} seller{stateListings[hoveredState].length > 1 ? 's' : ''}</div>
                {stateListings[hoveredState].slice(0, 3).map(s => (
                  <div key={s.id} className="mp__tooltip-seller">
                    <span className="mp__grade-badge mp__grade-badge--xs" style={{ background: GRADE_COLORS[s.grade] }}>{s.grade}</span>
                    <span>{s.companyName}</span>
                  </div>
                ))}
                {stateListings[hoveredState].length > 3 && (
                  <div className="mp__tooltip-more">+{stateListings[hoveredState].length - 3} more</div>
                )}
                <div className="mp__tooltip-hint">Click to filter</div>
              </div>
            )}
          </div>

          {selectedState && (
            <button className="mp__clear-filter" onClick={() => setSelectedState(null)}>
              ✕ Clear filter: {INDIA_STATES[selectedState]?.name}
            </button>
          )}
        </div>

        {/* Listings */}
        <div className="mp__listings-panel">
          <h3 className="mp__section-title">
            {selectedState ? `Sellers in ${INDIA_STATES[selectedState]?.name}` : 'All Listings'}
            <span className="mp__count-badge">{filteredListings.length}</span>
          </h3>
          <div className="mp__listings-scroll">
            {filteredListings.map(listing => (
              <div key={listing.id} className="mp__listing-card mp__listing-card--compact">
                <div className="mp__listing-header">
                  <span className="mp__grade-badge" style={{ background: GRADE_COLORS[listing.grade] }}>Grade {listing.grade}</span>
                  <span className="mp__chem-tag">{listing.chemistry}</span>
                  <span className="mp__stars mp__stars--sm">{'★'.repeat(Math.round(listing.rating))} {listing.rating}</span>
                </div>
                <h4 className="mp__listing-company" onClick={() => setSelectedSeller(listing)} style={{ cursor: 'pointer' }}>
                  {listing.companyName}
                </h4>
                <div className="mp__listing-specs">
                  <div><span className="mp__spec-label">Capacity</span><span className="mp__spec-value">{listing.capacityKwh} kWh</span></div>
                  <div><span className="mp__spec-label">Qty</span><span className="mp__spec-value">{listing.quantity}</span></div>
                  <div><span className="mp__spec-label">Price</span><span className="mp__spec-value">₹{listing.pricePerUnit.toLocaleString('en-IN')}/unit</span></div>
                  <div><span className="mp__spec-label">Location</span><span className="mp__spec-value">{listing.city}, {listing.state}</span></div>
                </div>
                <div className="mp__listing-actions">
                  <button className="mp__profile-btn" onClick={() => setSelectedSeller(listing)}>
                    View Profile
                  </button>
                  <button
                    className={`mp__request-btn ${requestSent.has(listing.id) ? 'mp__request-btn--sent' : ''}`}
                    disabled={requestSent.has(listing.id)}
                    onClick={() => handleRequest(listing)}
                  >
                    {requestSent.has(listing.id) ? '✓ Request Sent' : '📩 Request Info'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Marketplace;

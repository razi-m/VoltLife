import React from 'react';
import type { WSEvent } from '../lib/types';

interface MarketplaceProps {
  lastEvent: WSEvent | null;
}

const Marketplace: React.FC<MarketplaceProps> = () => {
  return (
    <div className="page-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
      <div style={{ textAlign: 'center', maxWidth: 520, animation: 'fadeIn 0.5s ease' }}>
        <div style={{ fontSize: 64, marginBottom: 16 }}>🔋</div>
        <h1 style={{ fontSize: 'clamp(28px, 4vw, 40px)', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 12 }}>
          Marketplace
        </h1>
        <div style={{
          display: 'inline-block',
          padding: '6px 20px',
          borderRadius: 'var(--radius-full)',
          background: 'linear-gradient(135deg, rgba(77,142,255,0.15), rgba(78,222,163,0.15))',
          border: '1px solid rgba(77,142,255,0.25)',
          color: 'var(--primary)',
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: 1.5,
          textTransform: 'uppercase',
          marginBottom: 24,
        }}>
          Coming Soon
        </div>
        <p style={{
          color: 'var(--on-surface-variant)',
          fontSize: 15,
          lineHeight: 1.7,
          marginBottom: 32,
        }}>
          India's first AI-powered second-life battery marketplace is under construction.
          Browse verified inventory, get instant quotes, and track deliveries — all in one place.
        </p>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: 16,
          padding: 20,
          borderRadius: 'var(--radius-lg)',
          background: 'var(--surface-container-low)',
          border: '1px solid var(--outline-variant)',
        }}>
          {[
            { icon: '🗺', label: 'Supplier Map', desc: 'Find sellers across India' },
            { icon: '⚡', label: 'Instant Quotes', desc: 'Real-time pricing' },
            { icon: '🚚', label: 'Live Tracking', desc: 'End-to-end logistics' },
          ].map(f => (
            <div key={f.label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 28, marginBottom: 6 }}>{f.icon}</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--on-surface)', marginBottom: 2 }}>{f.label}</div>
              <div style={{ fontSize: 11, color: 'var(--on-surface-variant)' }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Marketplace;

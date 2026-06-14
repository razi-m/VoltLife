import React, { useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import './Sidebar.css';

/** Shared nav items visible to all authenticated roles */
const sharedNavItems = [
  { path: '/dashboard', label: 'Mission Control', icon: '◎' },
  { path: '/assess', label: 'Battery Intake', icon: '⚡' },
  { path: '/registry', label: 'BPAN Registry', icon: '▣' },
  { path: '/deploy', label: 'Deployment', icon: '◈' },
  { path: '/analytics', label: 'Analytics', icon: '◉' },
  { path: '/impact', label: 'Impact', icon: '◐' },
  { path: '/ai', label: 'Volt AI', icon: '◆' },
];

/** Buyer-only nav items */
const buyerNavItems = [
  { path: '/marketplace', label: 'Marketplace', icon: '❖' },
];

/** Seller-only nav items */
const sellerNavItems = [
  { path: '/seller-dashboard', label: 'Seller Panel', icon: '▦' },
];

interface SidebarProps {
  wsConnected: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ wsConnected }) => {
  const location = useLocation(); // subscribing to location changes forces re-render
  const isSupplier = !!localStorage.getItem('supplier_token');
  const isBuyer = !!localStorage.getItem('buyer_token');

  const roleItems = isSupplier ? sellerNavItems : buyerNavItems;
  const roleLabel = isSupplier ? 'Seller Mode' : isBuyer ? 'Buyer Mode' : null;
  const roleDotClass = isSupplier ? 'sidebar__role-dot--seller' : 'sidebar__role-dot--buyer';

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar__logo">
        <NavLink to="/" className="sidebar__logo-link">
          <div className="sidebar__logo-mark">
            <span className="sidebar__logo-bolt">⚡</span>
          </div>
          <div className="sidebar__logo-text">
            <span className="sidebar__brand">VoltLife</span>
            <span className="sidebar__subtitle">Battery OS</span>
          </div>
        </NavLink>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">
        <div className="sidebar__section-label text-label-caps">Operations</div>
        {sharedNavItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar__item ${isActive ? 'sidebar__item--active' : ''}`
            }
          >
            <span className="sidebar__item-icon">{item.icon}</span>
            <span className="sidebar__item-label">{item.label}</span>
          </NavLink>
        ))}
        {roleItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar__item ${isActive ? 'sidebar__item--active' : ''}`
            }
          >
            <span className="sidebar__item-icon">{item.icon}</span>
            <span className="sidebar__item-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Status footer */}
      <div className="sidebar__footer">
        <div className="sidebar__status">
          <span className={`sidebar__status-dot ${wsConnected ? 'sidebar__status-dot--online' : ''}`} />
          <span className="text-body-sm">
            {wsConnected ? 'Live Feed Active' : 'Connecting...'}
          </span>
        </div>
        {roleLabel && (
          <div className="sidebar__role-indicator">
            <span className={`sidebar__role-dot ${roleDotClass}`} />
            <span>{roleLabel}</span>
          </div>
        )}
        <div className="sidebar__version text-label-caps">v1.2.0</div>
      </div>
    </aside>
  );
};


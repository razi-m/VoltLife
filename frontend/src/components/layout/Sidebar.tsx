import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import './Sidebar.css';

const navItems = [
  { path: '/dashboard', label: 'Mission Control', icon: '◎' },
  { path: '/assess', label: 'Battery Intake', icon: '⚡' },
  { path: '/registry', label: 'BPAN Registry', icon: '▣' },
  { path: '/deploy', label: 'Deployment', icon: '◈' },
  { path: '/analytics', label: 'Analytics', icon: '◉' },
  { path: '/impact', label: 'Impact', icon: '◐' },
  { path: '/ai', label: 'Volt AI', icon: '◆' },
  { path: '/marketplace', label: 'Marketplace', icon: '❖' },
];

interface SidebarProps {
  wsConnected: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ wsConnected }) => {
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
        {navItems.map((item) => (
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
        <div className="sidebar__version text-label-caps">v1.2.0</div>
      </div>
    </aside>
  );
};

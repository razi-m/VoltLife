import React from 'react';
import './Card.css';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({ children, className = '', glow = false, onClick, style }) => (
  <div className={`card ${glow ? 'card--glow' : ''} ${onClick ? 'card--clickable' : ''} ${className}`} onClick={onClick} style={style}>
    {children}
  </div>
);

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  color?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value, unit, icon, trend, color }) => (
  <div className="metric-card" style={color ? { '--metric-accent': color } as React.CSSProperties : undefined}>
    <div className="metric-card__header">
      {icon && <span className="metric-card__icon">{icon}</span>}
      <span className="text-label-caps">{label}</span>
    </div>
    <div className="metric-card__value">
      <span className="text-data-lg">{value}</span>
      {unit && <span className="metric-card__unit">{unit}</span>}
    </div>
    {trend && (
      <span className={`metric-card__trend metric-card__trend--${trend}`}>
        {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '—'}
      </span>
    )}
  </div>
);

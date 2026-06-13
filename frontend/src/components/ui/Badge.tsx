import React from 'react';
import './Badge.css';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'grade-s' | 'grade-a' | 'grade-b' | 'grade-c' | 'grade-d';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', size = 'md' }) => (
  <span className={`badge badge--${variant} badge--${size}`}>{children}</span>
);

// Grade badge with auto color
interface GradeBadgeProps {
  grade: string | null;
}

const gradeVariants: Record<string, BadgeProps['variant']> = {
  S: 'grade-s',
  A: 'grade-a',
  B: 'grade-b',
  C: 'grade-c',
  D: 'grade-d',
};

export const GradeBadge: React.FC<GradeBadgeProps> = ({ grade }) => {
  if (!grade) return <Badge variant="default">—</Badge>;
  return <Badge variant={gradeVariants[grade] || 'default'}>{grade}</Badge>;
};

// Status badge
interface StatusBadgeProps {
  status: string;
}

const statusVariants: Record<string, BadgeProps['variant']> = {
  ingested: 'info',
  assessed: 'warning',
  assigned: 'success',
  deployed: 'success',
  recycled: 'danger',
  recommended: 'info',
  approved: 'success',
  dispatched: 'success',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => (
  <Badge variant={statusVariants[status] || 'default'}>
    {status.toUpperCase()}
  </Badge>
);

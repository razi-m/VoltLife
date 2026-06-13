import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '../lib/api';
import { useApi } from '../hooks/useApi';
import { MetricCard } from '../components/ui/Card';
import { Card } from '../components/ui/Card';
import { GradeBadge, StatusBadge } from '../components/ui/Badge';
import type { WSEvent } from '../lib/types';
import './Dashboard.css';

const GRADE_COLORS: Record<string, string> = { S: '#4edea3', A: '#3b82f6', B: '#06b6d4', C: '#f59e0b', D: '#ff5451' };

interface DashboardProps {
  lastEvent: WSEvent | null;
}

const Dashboard: React.FC<DashboardProps> = ({ lastEvent }) => {
  const { data: stats, loading, refetch } = useApi(() => api.dashboard.stats(), []);
  const navigate = useNavigate();

  // Refetch on WebSocket events
  useEffect(() => {
    if (lastEvent) refetch();
  }, [lastEvent]);

  if (loading || !stats) {
    return (
      <div className="page-content">
        <div className="page-header"><h2 className="page-title">Mission Control</h2></div>
        <div className="grid grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 120 }} />
          ))}
        </div>
      </div>
    );
  }

  const gradeData = Object.entries(stats.by_grade).map(([grade, count]) => ({
    name: `Grade ${grade}`, value: count, color: GRADE_COLORS[grade],
  }));

  const statusData = Object.entries(stats.by_status).map(([status, count]) => ({
    name: status, count,
  }));

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Mission Control</h1>
        <div className="dashboard__live-indicator">
          <span className="dashboard__live-dot" /> LIVE
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 dashboard__kpis">
        <MetricCard label="Total Batteries" value={stats.total_batteries} icon="⚡" color="#4d8eff" />
        <MetricCard label="Avg State of Health" value={`${stats.avg_soh_pct}%`} icon="◎" color="#4edea3" />
        <MetricCard label="Active Deployments" value={stats.active_deployments} icon="◈" color="#06b6d4" />
        <MetricCard label="Energy Unlocked" value={stats.mwh_unlocked} unit="MWh" icon="⚡" color="#f59e0b" />
      </div>

      <div className="grid grid-cols-4 dashboard__kpis" style={{ marginTop: 'var(--space-4)' }}>
        <MetricCard label="CO₂ Saved" value={stats.carbon_saved_tonnes} unit="tonnes" icon="◐" color="#4edea3" />
        <MetricCard label="Processed" value={stats.processed} icon="◉" color="#4d8eff" />
        <MetricCard label="Recycled" value={stats.recycled} icon="♻" color="#ff5451" />
        <MetricCard
          label="Pipeline Rate"
          value={stats.total_batteries > 0 ? `${Math.round((stats.processed / stats.total_batteries) * 100)}%` : '0%'}
          icon="▣" color="#06b6d4"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2" style={{ marginTop: 'var(--space-6)' }}>
        {/* Grade distribution */}
        <Card>
          <h3 className="text-headline-sm" style={{ marginBottom: 'var(--space-4)' }}>Grade Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={gradeData} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={3} dataKey="value">
                {gradeData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#201f22', border: '1px solid #424754', borderRadius: 4, color: '#e5e1e4' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="dashboard__legend">
            {gradeData.map((d) => (
              <div key={d.name} className="dashboard__legend-item">
                <span className="dashboard__legend-dot" style={{ background: d.color }} />
                <span className="text-body-sm">{d.name}</span>
                <span className="text-data-md">{d.value}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Status distribution */}
        <Card>
          <h3 className="text-headline-sm" style={{ marginBottom: 'var(--space-4)' }}>Pipeline Status</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={statusData} layout="vertical" margin={{ left: 10 }}>
              <XAxis type="number" stroke="#8c909f" fontSize={11} />
              <YAxis dataKey="name" type="category" stroke="#8c909f" fontSize={11} width={90} tick={{ fontFamily: 'JetBrains Mono' }} />
              <Tooltip contentStyle={{ background: '#201f22', border: '1px solid #424754', borderRadius: 4, color: '#e5e1e4' }} />
              <Bar dataKey="count" fill="#4d8eff" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Recent batteries */}
      <Card className="dashboard__recent" style={{ marginTop: 'var(--space-6)' }}>
        <div className="dashboard__recent-header">
          <h3 className="text-headline-sm">Recent Batteries</h3>
          <button className="dashboard__view-all" onClick={() => navigate('/registry')}>View All →</button>
        </div>
        <table className="dashboard__recent-table">
          <thead>
            <tr>
              <th className="text-label-caps">ID</th>
              <th className="text-label-caps">Aadhaar ID</th>
              <th className="text-label-caps">OEM</th>
              <th className="text-label-caps">Grade</th>
              <th className="text-label-caps">SoH</th>
              <th className="text-label-caps">Status</th>
            </tr>
          </thead>
          <tbody>
            {stats.recent_batteries.map((b) => (
              <tr key={b.id} onClick={() => navigate(`/registry`)} style={{ cursor: 'pointer' }}>
                <td className="text-data-md">{b.id}</td>
                <td className="text-data-md">{b.aadhaar_id || '—'}</td>
                <td>{b.oem}</td>
                <td><GradeBadge grade={b.grade} /></td>
                <td className="text-data-md">{b.soh_pct ? `${b.soh_pct}%` : '—'}</td>
                <td><StatusBadge status={b.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

export default Dashboard;

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { api } from '../lib/api';
import { useApi } from '../hooks/useApi';
import { MetricCard, Card } from '../components/ui/Card';
import './Impact.css';

const SITE_COLORS: Record<string, string> = {
  solar_storage: '#f59e0b', rural_microgrid: '#4edea3', school_backup: '#3b82f6',
  health_center_backup: '#06b6d4', industrial_backup: '#06b6d4', telecom_tower: '#0891b2',
  ev_charging_buffer: '#10b981', street_lighting: '#ec4899', recycler: '#ff5451',
};

const Impact: React.FC = () => {
  const { data, loading } = useApi(() => api.impact.summary(), []);

  if (loading || !data) {
    return (
      <div className="page-content">
        <div className="page-header"><h2 className="page-title">Sustainability Impact & India 2030 Vision</h2></div>
        <div className="grid grid-cols-4">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton" style={{ height: 110 }} />)}</div>
      </div>
    );
  }

  const gradeData = Object.entries(data.by_grade).map(([grade, count]) => ({ grade: `Grade ${grade}`, count }));
  const GRADE_COLORS = ['#4edea3', '#3b82f6', '#06b6d4', '#f59e0b', '#ff5451'];

  const siteData = Object.entries(data.by_site_type)
    .filter(([_, count]) => count > 0)
    .map(([type, count]) => ({ name: type.replace(/_/g, ' '), count, color: SITE_COLORS[type] || '#8c909f' }));

  // India 2030 Vision projections
  const projectedBatteries = 40_000_000;
  const currentRate = data.total > 0 ? data.processed / data.total : 0;
  const projectedMwh = data.total > 0 ? (data.mwh_unlocked / data.total) * projectedBatteries * currentRate : 0;
  const projectedCO2 = data.total > 0 ? (data.carbon_saved_tonnes / data.total) * projectedBatteries * currentRate : 0;

  return (
    <div className="page-content">
      <div className="page-header"><h1 className="page-title">Sustainability Impact & India 2030 Vision</h1></div>

      {/* Impact KPIs */}
      <div className="grid grid-cols-4">
        <MetricCard label="Energy Unlocked" value={data.mwh_unlocked} unit="MWh" icon="⚡" color="#f59e0b" />
        <MetricCard label="CO₂ Saved" value={data.carbon_saved_tonnes} unit="tonnes" icon="◐" color="#4edea3" />
        <MetricCard label="Diverted from Recycling" value={data.diverted_from_recycling} icon="♻" color="#3b82f6" />
        <MetricCard label="Recycled Responsibly" value={data.recycled_responsibly} icon="◈" color="#ff5451" />
      </div>

      <div className="grid grid-cols-2" style={{ marginTop: 'var(--space-4)' }}>
        <MetricCard label="Processed" value={data.processed} icon="◉" color="#4d8eff" />
        <MetricCard label="Total Fleet" value={data.total} icon="▣" color="#06b6d4" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2" style={{ marginTop: 'var(--space-6)' }}>
        <Card>
          <h3 className="text-headline-sm" style={{ marginBottom: 'var(--space-4)' }}>By Grade</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={gradeData}>
              <XAxis dataKey="grade" stroke="#8c909f" fontSize={11} tick={{ fontFamily: 'JetBrains Mono' }} />
              <YAxis stroke="#8c909f" fontSize={11} />
              <Tooltip contentStyle={{ background: '#201f22', border: '1px solid #424754', borderRadius: 4, color: '#e5e1e4' }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {gradeData.map((_, i) => <Cell key={i} fill={GRADE_COLORS[i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-headline-sm" style={{ marginBottom: 'var(--space-4)' }}>By Destination Type</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={siteData} cx="50%" cy="50%" innerRadius={50} outerRadius={90} paddingAngle={2} dataKey="count" nameKey="name">
                {siteData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#201f22', border: '1px solid #424754', borderRadius: 4, color: '#e5e1e4' }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="impact__legend">
            {siteData.map((d) => (
              <div key={d.name} className="dashboard__legend-item">
                <span className="dashboard__legend-dot" style={{ background: d.color }} />
                <span className="text-body-sm">{d.name}</span>
                <span className="text-data-md">{d.count}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* India 2030 Vision */}
      <Card style={{ marginTop: 'var(--space-6)' }} glow>
        <h3 className="text-headline-sm" style={{ marginBottom: 'var(--space-4)' }}>
          🇮🇳 India 2030 Vision — 40M Batteries
        </h3>
        <p className="text-body-sm" style={{ color: 'var(--on-surface-variant)', marginBottom: 'var(--space-5)' }}>
          By 2030, India will retire over 40 million EV and industrial batteries. VoltLife's national-scale 
          platform can unlock massive second-life value and prevent catastrophic environmental damage.
        </p>
        <div className="grid grid-cols-3">
          <div className="impact__vision-stat">
            <div className="text-label-caps">Projected Energy</div>
            <div className="text-data-lg" style={{ color: 'var(--color-warning)', marginTop: 'var(--space-2)' }}>
              {(projectedMwh / 1000).toFixed(0)} GWh
            </div>
          </div>
          <div className="impact__vision-stat">
            <div className="text-label-caps">CO₂ Prevented</div>
            <div className="text-data-lg" style={{ color: 'var(--secondary)', marginTop: 'var(--space-2)' }}>
              {(projectedCO2 / 1000).toFixed(0)}K tonnes
            </div>
          </div>
          <div className="impact__vision-stat">
            <div className="text-label-caps">Batteries Targeted</div>
            <div className="text-data-lg" style={{ color: 'var(--primary)', marginTop: 'var(--space-2)' }}>40M</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Impact;

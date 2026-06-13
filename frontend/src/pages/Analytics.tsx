import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { api } from '../lib/api';
import { useApi } from '../hooks/useApi';
import { MetricCard, Card } from '../components/ui/Card';
import './Analytics.css';

const CHART_STYLE = { background: '#201f22', border: '1px solid #424754', borderRadius: 4, color: '#e5e1e4' };

const Analytics: React.FC = () => {
  const { data, loading } = useApi(() => api.analytics.fleet(), []);

  if (loading || !data) {
    return (
      <div className="page-content">
        <div className="page-header"><h2 className="page-title">Deep Health Analytics & Telemetry</h2></div>
        <div className="grid grid-cols-4">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="skeleton" style={{ height: 110 }} />)}</div>
      </div>
    );
  }

  const sohData = Object.entries(data.soh_distribution).map(([range, count]) => ({ range, count }));
  const cycleData = Object.entries(data.cycle_distribution).map(([range, count]) => ({ range, count }));
  const chemData = Object.entries(data.by_chemistry).map(([name, count]) => ({ name, count }));
  const oemData = Object.entries(data.by_oem).map(([name, count]) => ({ name, count }));

  const CHEM_COLORS = ['#4d8eff', '#4edea3', '#06b6d4', '#f59e0b', '#ff5451', '#06b6d4'];

  return (
    <div className="page-content">
      <div className="page-header"><h1 className="page-title">Deep Health Analytics & Telemetry</h1></div>

      {/* Fleet Averages */}
      <div className="grid grid-cols-4">
        <MetricCard label="Fleet Size" value={data.total_batteries} icon="⚡" color="#4d8eff" />
        <MetricCard label="Avg Cycle Count" value={data.averages.cycle_count} icon="◎" color="#06b6d4" />
        <MetricCard label="Avg Capacity Fade" value={`${data.averages.capacity_fade_pct}%`} icon="◉" color="#f59e0b" />
        <MetricCard label="Avg Temperature" value={`${data.averages.avg_temp_c}°C`} icon="◐" color="#ff5451" />
      </div>
      <div className="grid grid-cols-4" style={{ marginTop: 'var(--space-4)' }}>
        <MetricCard label="Avg IR" value={data.averages.internal_resistance_mohm} unit="mΩ" icon="▣" color="#4d8eff" />
        <MetricCard label="IR Growth" value={`${data.averages.ir_growth_pct}%`} icon="◈" color="#f59e0b" />
        <MetricCard label="Coulombic Eff." value={data.averages.coulombic_efficiency} icon="◆" color="#4edea3" />
        <MetricCard label="Voltage Stability" value={data.averages.voltage_stability} icon="◎" color="#06b6d4" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2" style={{ marginTop: 'var(--space-6)' }}>
        <Card>
          <h3 className="text-headline-sm" style={{ marginBottom: 'var(--space-4)' }}>SoH Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={sohData}>
              <XAxis dataKey="range" stroke="#8c909f" fontSize={11} tick={{ fontFamily: 'JetBrains Mono' }} />
              <YAxis stroke="#8c909f" fontSize={11} />
              <Tooltip contentStyle={CHART_STYLE} />
              <Bar dataKey="count" fill="#4edea3" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <h3 className="text-headline-sm" style={{ marginBottom: 'var(--space-4)' }}>Cycle Count Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={cycleData}>
              <XAxis dataKey="range" stroke="#8c909f" fontSize={11} tick={{ fontFamily: 'JetBrains Mono' }} />
              <YAxis stroke="#8c909f" fontSize={11} />
              <Tooltip contentStyle={CHART_STYLE} />
              <Bar dataKey="count" fill="#4d8eff" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid grid-cols-2" style={{ marginTop: 'var(--space-4)' }}>
        <Card>
          <h3 className="text-headline-sm" style={{ marginBottom: 'var(--space-4)' }}>By Chemistry</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={chemData} cx="50%" cy="50%" innerRadius={50} outerRadius={85} paddingAngle={3} dataKey="count" nameKey="name">
                {chemData.map((_, i) => <Cell key={i} fill={CHEM_COLORS[i % CHEM_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={CHART_STYLE} />
            </PieChart>
          </ResponsiveContainer>
          <div className="analytics__legend">
            {chemData.map((d, i) => (
              <div key={d.name} className="dashboard__legend-item"><span className="dashboard__legend-dot" style={{ background: CHEM_COLORS[i % CHEM_COLORS.length] }} /><span className="text-body-sm">{d.name}</span><span className="text-data-md">{d.count}</span></div>
            ))}
          </div>
        </Card>

        <Card>
          <h3 className="text-headline-sm" style={{ marginBottom: 'var(--space-4)' }}>By OEM</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={oemData} layout="vertical">
              <XAxis type="number" stroke="#8c909f" fontSize={11} />
              <YAxis dataKey="name" type="category" stroke="#8c909f" fontSize={10} width={120} tick={{ fontFamily: 'Inter' }} />
              <Tooltip contentStyle={CHART_STYLE} />
              <Bar dataKey="count" fill="#06b6d4" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
};

export default Analytics;

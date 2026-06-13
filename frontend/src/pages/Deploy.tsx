import React, { useState } from 'react';
import { api } from '../lib/api';
import { useApi } from '../hooks/useApi';
import { DataTable } from '../components/ui/DataTable';
import { GradeBadge, Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { MetricCard } from '../components/ui/Card';
import type { DeploymentItem } from '../lib/types';
import './Deploy.css';

const Deploy: React.FC = () => {
  const [page, setPage] = useState(1);
  const [siteTypeFilter, setSiteTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const params: Record<string, string | number> = { page, page_size: 25 };
  if (siteTypeFilter) params.site_type = siteTypeFilter;
  if (statusFilter) params.deployment_status = statusFilter;

  const { data, loading, error, refetch } = useApi(
    () => api.deployments.list(params),
    [page, siteTypeFilter, statusFilter]
  );

  const handleApprove = async (id: number) => {
    try {
      await api.deployments.approve(id);
      refetch();
    } catch (err) {
      // Already approved or not in recommended state
    }
  };

  const totalDeployments = data?.total || 0;
  const totalEnergy = data?.items?.reduce((sum, d) => sum + d.energy_unlocked_mwh, 0) || 0;
  const totalCarbon = data?.items?.reduce((sum, d) => sum + d.carbon_saved_kg, 0) || 0;

  const columns = [
    { key: 'battery_id', header: 'Battery', width: '70px', render: (r: DeploymentItem) => <span className="text-data-md">{r.battery_id}</span> },
    { key: 'aadhaar_id', header: 'Aadhaar', render: (r: DeploymentItem) => <span className="text-data-md" style={{ fontSize: 10 }}>{r.aadhaar_id?.slice(0, 15) || '—'}...</span> },
    { key: 'grade', header: 'Grade', width: '65px', render: (r: DeploymentItem) => <GradeBadge grade={r.grade} /> },
    { key: 'site_name', header: 'Destination Site' },
    { key: 'site_type', header: 'Type', render: (r: DeploymentItem) => r.site_type.replace(/_/g, ' ') },
    { key: 'score', header: 'Score', width: '70px', render: (r: DeploymentItem) => <span className="text-data-md">{(r.score * 100).toFixed(0)}%</span> },
    { key: 'distance_km', header: 'Dist.', width: '70px', render: (r: DeploymentItem) => <span className="text-data-md">{r.distance_km?.toFixed(0) || '—'} km</span> },
    { key: 'energy_unlocked_mwh', header: 'MWh', width: '70px', render: (r: DeploymentItem) => <span className="text-data-md">{r.energy_unlocked_mwh.toFixed(2)}</span> },
    { key: 'deployment_status', header: 'Status', width: '120px', render: (r: DeploymentItem) => (
      <div className="deploy__status-cell">
        <Badge variant={r.deployment_status === 'approved' ? 'success' : r.deployment_status === 'dispatched' ? 'success' : 'info'}>
          {r.deployment_status.toUpperCase()}
        </Badge>
        {r.deployment_status === 'recommended' && (
          <Button size="sm" variant="success" onClick={(e) => { e.stopPropagation(); handleApprove(r.id); }}>
            Approve
          </Button>
        )}
      </div>
    )},
  ];

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Deployment Command Center</h1>
      </div>

      <div className="grid grid-cols-3" style={{ marginBottom: 'var(--space-6)' }}>
        <MetricCard label="Total Deployments" value={totalDeployments} icon="◈" color="#4d8eff" />
        <MetricCard label="Energy (this page)" value={totalEnergy.toFixed(2)} unit="MWh" icon="⚡" color="#4edea3" />
        <MetricCard label="CO₂ Saved (this page)" value={(totalCarbon / 1000).toFixed(2)} unit="t" icon="◐" color="#f59e0b" />
      </div>

      <div className="deploy__filters">
        <div className="deploy__filter-item">
          <label className="text-label-caps" htmlFor="site-type-filter">Destination:</label>
          <select id="site-type-filter" className="registry__filter-select" value={siteTypeFilter} onChange={(e) => { setSiteTypeFilter(e.target.value); setPage(1); }}>
            <option value="">All Site Types</option>
            {['solar_storage','rural_microgrid','school_backup','health_center_backup','industrial_backup','telecom_tower','ev_charging_buffer','street_lighting','recycler'].map(t => (
              <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
        <div className="deploy__filter-item">
          <label className="text-label-caps" htmlFor="status-filter">Status:</label>
          <select id="status-filter" className="registry__filter-select" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">All Statuses</option>
            {['recommended','approved','dispatched'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <DataTable
        columns={columns as any}
        data={data?.items || []}
        loading={loading}
        error={error}
        page={page}
        pageSize={25}
        total={data?.total || 0}
        onPageChange={setPage}
      />
    </div>
  );
};

export default Deploy;

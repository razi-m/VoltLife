import React, { useState, useCallback } from 'react';
import { api } from '../lib/api';
import { useApi } from '../hooks/useApi';
import { DataTable } from '../components/ui/DataTable';
import { GradeBadge, StatusBadge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import type { BatterySummary, AadhaarPassport } from '../lib/types';
import './Registry.css';

const Registry: React.FC = () => {
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [gradeFilter, setGradeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedBattery, setSelectedBattery] = useState<number | null>(null);
  const [passport, setPassport] = useState<AadhaarPassport | null>(null);
  const [loadingPassport, setLoadingPassport] = useState(false);

  const fetchParams = useCallback(() => {
    const params: Record<string, string | number> = { page, page_size: 25, sort_by: sortBy, sort_order: sortOrder };
    if (search) params.search = search;
    if (gradeFilter) params.grade = gradeFilter;
    if (statusFilter) params.status = statusFilter;
    return params;
  }, [page, search, sortBy, sortOrder, gradeFilter, statusFilter]);

  const { data, loading, error } = useApi(
    () => api.batteries.list(fetchParams()),
    [page, search, sortBy, sortOrder, gradeFilter, statusFilter]
  );

  const handleRowClick = async (row: BatterySummary) => {
    setSelectedBattery(row.id);
    setPassport(null);
    if (row.aadhaar_id) {
      setLoadingPassport(true);
      try {
        const p = await api.batteries.getAadhaar(row.id);
        setPassport(p);
      } catch {
        // Battery not assessed yet
      } finally {
        setLoadingPassport(false);
      }
    }
  };

  const columns = [
    { key: 'id', header: 'ID', sortable: true, width: '60px', render: (r: BatterySummary) => <span className="text-data-md">{r.id}</span> },
    { key: 'aadhaar_id', header: 'Aadhaar ID', sortable: false, render: (r: BatterySummary) => <span className="text-data-md" style={{ fontSize: 11 }}>{r.aadhaar_id || '—'}</span> },
    { key: 'external_ref', header: 'Ext. Ref', sortable: true },
    { key: 'oem', header: 'OEM', sortable: true },
    { key: 'chemistry', header: 'Chem', sortable: true, width: '70px' },
    { key: 'rated_capacity_kwh', header: 'Cap (kWh)', sortable: true, width: '90px', render: (r: BatterySummary) => <span className="text-data-md">{r.rated_capacity_kwh}</span> },
    { key: 'grade', header: 'Grade', width: '70px', render: (r: BatterySummary) => <GradeBadge grade={r.grade} /> },
    { key: 'soh_pct', header: 'SoH %', width: '80px', render: (r: BatterySummary) => <span className="text-data-md">{r.soh_pct ? `${r.soh_pct}%` : '—'}</span> },
    { key: 'status', header: 'Status', width: '100px', render: (r: BatterySummary) => <StatusBadge status={r.status} /> },
  ];

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Battery Aadhaar (BPAN) Registry</h1>
      </div>

      <div className="registry__layout">
        <div className="registry__table-section">
          {/* Filters */}
          <div className="registry__filters">
            <select
              className="registry__filter-select"
              value={gradeFilter}
              onChange={(e) => { setGradeFilter(e.target.value); setPage(1); }}
            >
              <option value="">All Grades</option>
              {['S', 'A', 'B', 'C', 'D'].map((g) => <option key={g} value={g}>Grade {g}</option>)}
            </select>
            <select
              className="registry__filter-select"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            >
              <option value="">All Statuses</option>
              {['ingested', 'assessed', 'assigned', 'deployed', 'recycled'].map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <DataTable
            columns={columns as any}
            data={data?.items || []}
            loading={loading}
            error={error}
            searchPlaceholder="Search by Aadhaar ID, reference, OEM..."
            onSearch={(q) => { setSearch(q); setPage(1); }}
            searchValue={search}
            onSort={(key, order) => { setSortBy(key); setSortOrder(order); }}
            sortKey={sortBy}
            sortOrder={sortOrder}
            page={page}
            pageSize={25}
            total={data?.total || 0}
            onPageChange={setPage}
            onRowClick={handleRowClick as any}
          />
        </div>

        {/* Aadhaar Passport Panel */}
        {selectedBattery && (
          <div className="registry__passport-panel">
            <Card glow>
              <div className="registry__passport-header">
                <h3 className="text-headline-sm">Battery Aadhaar Passport</h3>
                <button className="registry__close-btn" onClick={() => setSelectedBattery(null)}>✕</button>
              </div>

              {loadingPassport ? (
                <div style={{ padding: 'var(--space-8)', textAlign: 'center' }}>
                  <div className="assess__spinner-ring" style={{ width: 40, height: 40, margin: '0 auto' }} />
                </div>
              ) : passport ? (
                <div className="registry__passport-body">
                  <div className="registry__aadhaar-id text-data-lg">{passport.aadhaar_id}</div>

                  <div className="registry__passport-section">
                    <div className="text-label-caps">Decoded Identity</div>
                    <div className="registry__passport-grid">
                      {Object.entries(passport.decoded).map(([k, v]) => (
                        <div key={k} className="registry__passport-field">
                          <span className="text-label-caps" style={{ fontSize: 9 }}>{k.replace(/_/g, ' ')}</span>
                          <span className="text-data-md">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="registry__passport-section">
                    <div className="text-label-caps">Life Story</div>
                    <p className="text-body-sm" style={{ marginTop: 'var(--space-2)' }}>{passport.life_story}</p>
                  </div>

                  <div className="registry__passport-section">
                    <div className="text-label-caps">Timeline</div>
                    <div className="registry__timeline">
                      {passport.timeline.map((e, i) => (
                        <div key={i} className="registry__timeline-event">
                          <span className="registry__timeline-dot" />
                          <div>
                            <span className="text-body-sm">{e.event}</span>
                            <span className="text-label-caps" style={{ display: 'block', marginTop: 2 }}>{new Date(e.timestamp).toLocaleDateString()}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-body-sm" style={{ color: 'var(--on-surface-variant)', padding: 'var(--space-4)' }}>
                  Select an assessed battery to view its Aadhaar passport.
                </p>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default Registry;

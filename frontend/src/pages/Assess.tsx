import React, { useState, useRef } from 'react';
import { api } from '../lib/api';
import { Button } from '../components/ui/Button';
import { Card, MetricCard } from '../components/ui/Card';
import type { WSEvent, BatteryDetail } from '../lib/types';
import './Assess.css';

interface AssessProps { lastEvent: WSEvent | null; }

const FIELD_SECTIONS = [
  {
    title: 'Identity',
    icon: '🏷',
    fields: [
      { key: 'external_ref', label: 'External Ref', type: 'text' },
      { key: 'oem', label: 'OEM', type: 'text' },
      { key: 'model', label: 'Model', type: 'text' },
      { key: 'chemistry', label: 'Chemistry', type: 'select', options: ['NMC', 'LFP', 'NCA', 'LTO'] },
    ],
  },
  {
    title: 'Specifications',
    icon: '⚡',
    fields: [
      { key: 'rated_capacity_kwh', label: 'Rated Capacity (kWh)', type: 'number' },
      { key: 'nominal_voltage', label: 'Nominal Voltage (V)', type: 'number' },
      { key: 'manufacture_date', label: 'Manufacture Date', type: 'date' },
      { key: 'cycle_count', label: 'Cycle Count', type: 'number' },
    ],
  },
  {
    title: 'Origin',
    icon: '📍',
    fields: [
      { key: 'source_city', label: 'City', type: 'text' },
      { key: 'source_state', label: 'State', type: 'text' },
      { key: 'lat', label: 'Latitude', type: 'number' },
      { key: 'lng', label: 'Longitude', type: 'number' },
    ],
  },
  {
    title: 'Health Telemetry',
    icon: '📊',
    fields: [
      { key: 'capacity_now_kwh', label: 'Current Capacity (kWh)', type: 'number' },
      { key: 'avg_temp_c', label: 'Avg Temp (°C)', type: 'number' },
      { key: 'max_temp_c', label: 'Max Temp (°C)', type: 'number' },
      { key: 'thermal_stress_hours', label: 'Thermal Stress (hrs)', type: 'number' },
      { key: 'internal_resistance_mohm', label: 'Internal Resistance (mΩ)', type: 'number' },
      { key: 'ir_growth_pct', label: 'IR Growth (%)', type: 'number' },
    ],
  },
  {
    title: 'Advanced Metrics',
    icon: '🔬',
    fields: [
      { key: 'coulombic_efficiency', label: 'Coulombic Efficiency', type: 'number' },
      { key: 'fade_rate', label: 'Fade Rate', type: 'number' },
      { key: 'fade_acceleration', label: 'Fade Acceleration', type: 'number' },
      { key: 'cv_phase_fraction', label: 'CV Phase Fraction', type: 'number' },
      { key: 'voltage_slope', label: 'Voltage Slope', type: 'number' },
      { key: 'voltage_variance', label: 'Voltage Variance', type: 'number' },
      { key: 'discharge_efficiency', label: 'Discharge Efficiency', type: 'number' },
    ],
  },
];

const DEFAULT_VALUES: Record<string, any> = {
  external_ref: '', oem: '', model: '', chemistry: 'NMC',
  rated_capacity_kwh: '', nominal_voltage: '', manufacture_date: '',
  source_city: '', source_state: '', lat: '', lng: '',
  cycle_count: '', capacity_now_kwh: '', avg_temp_c: '', max_temp_c: '',
  thermal_stress_hours: '', internal_resistance_mohm: '', ir_growth_pct: '',
  coulombic_efficiency: '', fade_rate: '', fade_acceleration: '',
  cv_phase_fraction: '', voltage_slope: '', voltage_variance: '', discharge_efficiency: '',
};

const DEMO_BATTERY: Record<string, any> = {
  external_ref: 'TATA-EV-2024-C8H6', oem: 'Tata AutoComp', model: 'ZipTron 3S1P', chemistry: 'NMC',
  rated_capacity_kwh: 21.5, nominal_voltage: 48.0, manufacture_date: '2022-06-15',
  source_city: 'Pune', source_state: 'MH', lat: 18.52, lng: 73.85,
  cycle_count: 850, capacity_now_kwh: 18.2, avg_temp_c: 34.5, max_temp_c: 52.1,
  thermal_stress_hours: 120, internal_resistance_mohm: 85, ir_growth_pct: 18.5,
  coulombic_efficiency: 0.985, fade_rate: 0.05, fade_acceleration: 0.005,
  cv_phase_fraction: 0.15, voltage_slope: 0.06, voltage_variance: 0.004, discharge_efficiency: 0.96,
};

const GRADE_COLORS: Record<string, string> = { S: '#4edea3', A: '#3b82f6', B: '#06b6d4', C: '#f59e0b', D: '#ff5451' };

const Assess: React.FC<AssessProps> = ({ lastEvent }) => {
  const [formData, setFormData] = useState<Record<string, any>>({ ...DEFAULT_VALUES });
  const [submitting, setSubmitting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [result, setResult] = useState<BatteryDetail | null>(null);
  const [step, setStep] = useState<'form' | 'processing' | 'result'>('form');
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<number>(0);
  const [csvStatus, setCsvStatus] = useState<{ count: number; message: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const setField = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const loadDemo = () => {
    setFormData({ ...DEMO_BATTERY });
    setCsvStatus(null);
  };

  const clearForm = () => {
    setFormData({ ...DEFAULT_VALUES });
    setCsvStatus(null);
  };

  const handleCsvImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      const lines = text.trim().split('\n');
      if (lines.length < 2) {
        setCsvStatus({ count: 0, message: 'CSV must have a header row and at least one data row.' });
        return;
      }

      const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/\s+/g, '_'));
      const rows = lines.slice(1).map(line => {
        const values = line.split(',').map(v => v.trim());
        const row: Record<string, any> = {};
        headers.forEach((h, i) => {
          const val = values[i] || '';
          row[h] = isNaN(Number(val)) || val === '' ? val : Number(val);
        });
        return row;
      });

      if (rows.length === 1) {
        const mapped: Record<string, any> = { ...DEFAULT_VALUES };
        Object.keys(mapped).forEach(key => {
          if (rows[0][key] !== undefined) mapped[key] = rows[0][key];
        });
        setFormData(mapped);
        setCsvStatus({ count: 1, message: `Loaded 1 battery from ${file.name}` });
      } else {
        // For multiple rows, submit all as batch
        handleBatchSubmit(rows, file.name);
      }
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleBatchSubmit = async (rows: Record<string, any>[], filename: string) => {
    setSubmitting(true);
    setError(null);
    setCsvStatus({ count: rows.length, message: `Submitting ${rows.length} batteries from ${filename}...` });
    try {
      const res = await api.batteries.ingest(rows);
      setJobId(res.job_id);
      setCsvStatus({ count: rows.length, message: `${rows.length} batteries submitted. Processing...` });
      setStep('processing');
      pollJob(res.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Batch ingestion failed');
      setSubmitting(false);
      setCsvStatus(null);
    }
  };

  const isFormValid = () => {
    return formData.external_ref && formData.oem && formData.chemistry && formData.rated_capacity_kwh;
  };

  const handleSubmit = async () => {
    if (!isFormValid()) {
      setError('Please fill in at least: External Ref, OEM, Chemistry, and Rated Capacity.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const payload: Record<string, any> = {};
      Object.entries(formData).forEach(([k, v]) => {
        if (v !== '' && v !== null && v !== undefined) payload[k] = v;
      });
      const res = await api.batteries.ingest([payload]);
      setJobId(res.job_id);
      setStep('processing');
      pollJob(res.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ingestion failed');
      setSubmitting(false);
    }
  };

  const pollJob = async (jid: string) => {
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const job = await api.jobs.get(jid);
        if (job.status === 'done' || job.status === 'failed') {
          clearInterval(interval);
          setSubmitting(false);
          if (job.status === 'done' && job.processed > 0) {
            const batteries = await api.batteries.list({ page: 1, page_size: 1, sort_by: 'id', sort_order: 'desc' });
            if (batteries.items.length > 0) {
              const bid = batteries.items[0].id;
              const detail = await api.batteries.get(bid);
              setResult(detail);
              setStep('result');
            }
          }
        }
      } catch { /* keep polling */ }
      if (attempts > 60) {
        clearInterval(interval);
        setSubmitting(false);
        setError('Assessment timed out.');
      }
    }, 2000);
  };

  const handleReset = () => {
    setStep('form');
    setResult(null);
    setJobId(null);
    setError(null);
    setCsvStatus(null);
  };

  const filledCount = Object.values(formData).filter(v => v !== '' && v !== null && v !== undefined).length;
  const totalFields = Object.keys(formData).length;

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Battery Intake & AI Assessment</h1>
      </div>

      {step === 'form' && (
        <div className="assess__layout">
          {/* Top action bar */}
          <div className="assess__action-bar">
            <div className="assess__action-bar-left">
              <button className="assess__action-chip" onClick={loadDemo}>
                <span>🧪</span> Load Demo Data
              </button>
              <button className="assess__action-chip" onClick={() => fileInputRef.current?.click()}>
                <span>📄</span> Import CSV
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                style={{ display: 'none' }}
                onChange={handleCsvImport}
              />
              <button className="assess__action-chip assess__action-chip--ghost" onClick={clearForm}>
                Clear
              </button>
            </div>
            <div className="assess__progress-pill">
              <div className="assess__progress-fill" style={{ width: `${(filledCount / totalFields) * 100}%` }} />
              <span className="assess__progress-text">{filledCount}/{totalFields} fields</span>
            </div>
          </div>

          {csvStatus && (
            <div className="assess__csv-status">
              <span>📄</span> {csvStatus.message}
            </div>
          )}

          {/* Form sections */}
          <div className="assess__sections">
            {FIELD_SECTIONS.map((section, sIdx) => {
              const isOpen = expandedSection === sIdx;
              const sectionFilled = section.fields.filter(f => formData[f.key] !== '' && formData[f.key] !== null && formData[f.key] !== undefined).length;
              return (
                <div key={section.title} className={`assess__section ${isOpen ? 'assess__section--open' : ''}`}>
                  <button
                    className="assess__section-header"
                    onClick={() => setExpandedSection(isOpen ? -1 : sIdx)}
                  >
                    <div className="assess__section-title">
                      <span className="assess__section-icon">{section.icon}</span>
                      <span>{section.title}</span>
                      <span className="assess__section-count">{sectionFilled}/{section.fields.length}</span>
                    </div>
                    <span className={`assess__section-chevron ${isOpen ? 'assess__section-chevron--open' : ''}`}>▾</span>
                  </button>
                  {isOpen && (
                    <div className="assess__section-body">
                      <div className="assess__field-grid">
                        {section.fields.map(field => (
                          <div key={field.key} className="assess__field">
                            <label className="assess__field-label">{field.label}</label>
                            {field.type === 'select' ? (
                              <select
                                className="assess__input"
                                value={formData[field.key] || ''}
                                onChange={e => setField(field.key, e.target.value)}
                              >
                                <option value="">Select...</option>
                                {field.options?.map(o => <option key={o} value={o}>{o}</option>)}
                              </select>
                            ) : (
                              <input
                                className="assess__input"
                                type={field.type}
                                placeholder={String(DEMO_BATTERY[field.key] ?? '')}
                                value={formData[field.key] ?? ''}
                                onChange={e => setField(field.key, field.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)}
                              />
                            )}
                          </div>
                        ))}
                      </div>
                      {sIdx < FIELD_SECTIONS.length - 1 && (
                        <button className="assess__next-section" onClick={() => setExpandedSection(sIdx + 1)}>
                          Next: {FIELD_SECTIONS[sIdx + 1].title} →
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {error && <div className="assess__error">{error}</div>}

          <button
            className="assess__submit-btn"
            disabled={submitting || !isFormValid()}
            onClick={handleSubmit}
          >
            {submitting ? (
              <><div className="assess__spinner-ring assess__spinner-ring--sm" /> Processing...</>
            ) : (
              <>⚡ Run AI Assessment</>
            )}
          </button>
        </div>
      )}

      {step === 'processing' && (
        <Card className="assess__processing">
          <div className="assess__processing-animation">
            <div className="assess__spinner-ring" />
            <span className="text-headline-sm">AI Assessment in Progress</span>
            <span className="text-body-sm" style={{ color: 'var(--on-surface-variant)' }}>
              Job ID: <span className="text-data-md">{jobId}</span>
            </span>
            {csvStatus && <span className="text-body-sm" style={{ color: 'var(--secondary)' }}>{csvStatus.message}</span>}
            <div className="assess__pipeline-stages">
              {['Telemetry Analysis', 'Feature Extraction', 'ML Prediction', 'Deployment Matching'].map((s, i) => (
                <div key={s} className="assess__pipeline-stage" style={{ animationDelay: `${i * 0.5}s` }}>
                  <span className="assess__stage-dot" />
                  <span className="text-body-sm">{s}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {step === 'result' && result && (
        <div className="assess__result">
          <div className="grid grid-cols-4">
            <MetricCard label="State of Health" value={result.assessment ? `${result.assessment.soh_pct}%` : '—'} icon="◎" color="#4edea3" />
            <MetricCard label="Remaining Life" value={result.assessment ? `${result.assessment.rul_years} yr` : '—'} icon="◉" color="#4d8eff" />
            <MetricCard label="Grade" value={result.assessment?.grade || '—'} icon="▣" color={GRADE_COLORS[result.assessment?.grade || ''] || '#8c909f'} />
            <MetricCard label="Confidence" value={result.assessment?.confidence?.toUpperCase() || '—'} icon="◆" color="#06b6d4" />
          </div>

          <div className="grid grid-cols-2" style={{ marginTop: 'var(--space-4)' }}>
            <Card>
              <h3 className="text-headline-sm">Assessment Details</h3>
              <div className="assess__detail-grid">
                <div className="assess__detail-row">
                  <span className="text-label-caps">Aadhaar ID</span>
                  <span className="text-data-md">{result.aadhaar_id || '—'}</span>
                </div>
                <div className="assess__detail-row">
                  <span className="text-label-caps">Battery ID</span>
                  <span className="text-data-md">{result.id}</span>
                </div>
                <div className="assess__detail-row">
                  <span className="text-label-caps">OEM / Model</span>
                  <span className="text-body-sm">{result.oem} {result.model}</span>
                </div>
                <div className="assess__detail-row">
                  <span className="text-label-caps">Chemistry</span>
                  <span className="text-body-sm">{result.chemistry}</span>
                </div>
                {result.assessment?.reasons.map((r, i) => (
                  <div key={i} className="assess__detail-row">
                    <span className="text-label-caps">Reason {i + 1}</span>
                    <span className="text-body-sm">{r}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h3 className="text-headline-sm">Deployment Recommendation</h3>
              {result.deployment ? (
                <div className="assess__detail-grid">
                  <div className="assess__detail-row">
                    <span className="text-label-caps">Site</span>
                    <span className="text-body-sm">{result.deployment.site_name}</span>
                  </div>
                  <div className="assess__detail-row">
                    <span className="text-label-caps">Type</span>
                    <span className="text-body-sm">{result.deployment.site_type.replace(/_/g, ' ')}</span>
                  </div>
                  <div className="assess__detail-row">
                    <span className="text-label-caps">Match Score</span>
                    <span className="text-data-md">{(result.deployment.score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="assess__detail-row">
                    <span className="text-label-caps">Distance</span>
                    <span className="text-data-md">{result.deployment.distance_km} km</span>
                  </div>
                  <div className="assess__detail-row">
                    <span className="text-label-caps">Energy Unlocked</span>
                    <span className="text-data-md">{result.deployment.energy_unlocked_mwh} MWh</span>
                  </div>
                  <div className="assess__detail-row">
                    <span className="text-label-caps">CO₂ Saved</span>
                    <span className="text-data-md">{result.deployment.carbon_saved_kg} kg</span>
                  </div>
                </div>
              ) : (
                <p className="text-body-sm" style={{ color: 'var(--on-surface-variant)', marginTop: 'var(--space-3)' }}>
                  No deployment recommendation yet.
                </p>
              )}
            </Card>
          </div>

          <Button variant="ghost" size="md" onClick={handleReset} style={{ marginTop: 'var(--space-4)' }}>
            ← Assess Another Battery
          </Button>
        </div>
      )}
    </div>
  );
};

export default Assess;

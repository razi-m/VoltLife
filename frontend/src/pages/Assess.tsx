import React, { useState, useCallback } from 'react';
import { api } from '../lib/api';
import { useApi } from '../hooks/useApi';
import { Button } from '../components/ui/Button';
import { Card, MetricCard } from '../components/ui/Card';
import { GradeBadge, StatusBadge } from '../components/ui/Badge';
import type { WSEvent, BatteryDetail } from '../lib/types';
import './Assess.css';

interface AssessProps { lastEvent: WSEvent | null; }

const DEMO_BATTERY = {
  external_ref: 'TATA-EV-2024-' + Math.random().toString(36).slice(2, 6).toUpperCase(),
  oem: 'Tata AutoComp', model: 'ZipTron 3S1P', chemistry: 'NMC',
  rated_capacity_kwh: 21.5, nominal_voltage: 48.0,
  manufacture_date: '2022-06-15', source_city: 'Pune', source_state: 'MH',
  lat: 18.52, lng: 73.85, cycle_count: 850, capacity_now_kwh: 18.2,
  avg_temp_c: 34.5, max_temp_c: 52.1, thermal_stress_hours: 120,
  internal_resistance_mohm: 85, ir_growth_pct: 18.5, coulombic_efficiency: 0.985,
};

const Assess: React.FC<AssessProps> = ({ lastEvent }) => {
  const [submitting, setSubmitting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [result, setResult] = useState<BatteryDetail | null>(null);
  const [batteryId, setBatteryId] = useState<number | null>(null);
  const [step, setStep] = useState<'form' | 'processing' | 'result'>('form');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.batteries.ingest([DEMO_BATTERY]);
      setJobId(res.job_id);
      setStep('processing');
      // Poll for completion
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
            // Fetch latest battery list to find the new one
            const batteries = await api.batteries.list({ page: 1, page_size: 1, sort_by: 'id', sort_order: 'desc' });
            if (batteries.items.length > 0) {
              const bid = batteries.items[0].id;
              setBatteryId(bid);
              const detail = await api.batteries.get(bid);
              setResult(detail);
              setStep('result');
            }
          }
        }
      } catch {
        // Keep polling
      }
      if (attempts > 60) {
        clearInterval(interval);
        setSubmitting(false);
        setError('Assessment timed out. Check the pipeline.');
      }
    }, 2000);
  };

  const handleReset = () => {
    setStep('form');
    setResult(null);
    setBatteryId(null);
    setJobId(null);
    setError(null);
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <h1 className="page-title">Battery Intake & AI Assessment</h1>
      </div>

      {step === 'form' && (
        <div className="assess__grid">
          <Card className="assess__form-card">
            <h3 className="text-headline-sm">New Battery Intake</h3>
            <p className="text-body-sm" style={{ color: 'var(--on-surface-variant)', marginTop: 'var(--space-2)' }}>
              Submit a battery for AI-powered health assessment and deployment recommendation.
            </p>

            <div className="assess__form-fields">
              {Object.entries(DEMO_BATTERY).map(([key, val]) => (
                <div key={key} className="assess__field">
                  <label className="text-label-caps">{key.replace(/_/g, ' ')}</label>
                  <div className="assess__field-value text-data-md">{String(val)}</div>
                </div>
              ))}
            </div>

            {error && <div className="assess__error">{error}</div>}

            <Button
              variant="solid"
              size="lg"
              loading={submitting}
              onClick={handleSubmit}
              style={{ marginTop: 'var(--space-5)', width: '100%' }}
            >
              ⚡ Run AI Assessment
            </Button>
          </Card>

          <Card className="assess__info-card">
            <h3 className="text-headline-sm">How It Works</h3>
            <div className="assess__steps">
              {[
                { num: '01', label: 'INTAKE', desc: 'Battery data and telemetry uploaded' },
                { num: '02', label: 'AADHAAR', desc: 'Unique identity (BPAN) assigned' },
                { num: '03', label: 'ASSESS', desc: 'ML model predicts SoH, RUL, and grade' },
                { num: '04', label: 'DEPLOY', desc: 'Optimal second-life site recommended' },
              ].map((s) => (
                <div key={s.num} className="assess__step">
                  <span className="assess__step-num text-data-lg">{s.num}</span>
                  <div>
                    <div className="text-label-caps" style={{ color: 'var(--primary)' }}>{s.label}</div>
                    <div className="text-body-sm">{s.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
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

const GRADE_COLORS: Record<string, string> = { S: '#4edea3', A: '#3b82f6', B: '#06b6d4', C: '#f59e0b', D: '#ff5451' };
export default Assess;

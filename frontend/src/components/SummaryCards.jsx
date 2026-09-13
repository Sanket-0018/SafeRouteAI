import React from 'react';
import { Layers, AlertTriangle, TrendingUp, Building2 } from 'lucide-react';

export default function SummaryCards({ stats, selectedCity, onSelectCity }) {
  const total = stats?.total_hotspot_records || 100;
  const highCount = stats?.risk_tier_breakdown?.HIGH || 100;
  const maxProb = stats?.probability_stats?.max
    ? (stats.probability_stats.max * 100).toFixed(1)
    : '87.2';
  const avgProb = stats?.probability_stats?.mean
    ? (stats.probability_stats.mean * 100).toFixed(1)
    : '76.0';
  const cities = stats?.cities_covered || [
    'Bangalore', 'Chandigarh', 'Chennai', 'Hyderabad', 'Kolkata', 'Mumbai', 'Pune',
  ];

  return (
    <section className="summary-cards-row">
      <div className="summary-card">
        <div className="summary-card-label">Ranked hotspots</div>
        <div className="summary-card-value">{total}</div>
        <div className="summary-card-sub">evaluated windows</div>
      </div>

      <div className="summary-card">
        <div className="summary-card-label">High-risk predictions</div>
        <div className="summary-card-value" style={{ color: 'var(--hazard-ml)' }}>{highCount}</div>
        <div className="summary-card-sub">HIGH tier</div>
      </div>

      <div className="summary-card">
        <div className="summary-card-label">Peak risk probability</div>
        <div className="summary-card-value">{maxProb}%</div>
        <div className="summary-card-sub">mean: {avgProb}%</div>
      </div>

      <div className="summary-card">
        <div className="summary-card-label">Cities covered</div>
        <div className="summary-card-value">{cities.length}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem', marginTop: '0.35rem' }}>
          {cities.map((c) => (
            <button
              key={c}
              onClick={() => onSelectCity(selectedCity === c ? '' : c)}
              style={{
                fontSize: '0.68rem',
                padding: '1px 7px',
                borderRadius: 'var(--radius-full)',
                border: '1px solid',
                borderColor: selectedCity === c ? 'var(--accent-cta)' : 'var(--border-color)',
                background: selectedCity === c ? 'var(--hazard-official-bg)' : 'var(--bg-card)',
                color: selectedCity === c ? 'var(--accent-cta)' : 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              {c}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

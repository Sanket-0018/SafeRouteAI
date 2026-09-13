import React from 'react';
import { AlertTriangle, MapPin, Clock, Gauge, ArrowDownCircle, ShieldAlert, TrendingUp } from 'lucide-react';

export default function RiskResultBanner({ hotspotDetail, onScrollToFactors, onScrollToGuidance }) {
  if (!hotspotDetail) return null;

  const { rank, location, temporal, prediction } = hotspotDetail;
  const probPct = (prediction.high_probability * 100).toFixed(1);
  const multiplier = (prediction.high_probability / 0.065).toFixed(1);

  return (
    <div className="risk-result-dominant-banner">
      <div className="banner-top-badge">
        <AlertTriangle size={18} className="text-red pulse-fast" />
        <span className="banner-badge-title">ELEVATED ROAD-SAFETY RISK DETECTED</span>
        <span className="banner-rank-tag">Priority Rank #{rank}</span>
      </div>

      <div className="banner-core-grid">
        {/* WHERE */}
        <div className="banner-metric-block">
          <div className="metric-step-label">1. WHERE (Location)</div>
          <div className="metric-main-val">
            {location.city} • <span className="text-zone">Zone {location.zone_id}</span>
          </div>
          <div className="metric-sub-val">
            {location.latitude.toFixed(4)}°N, {location.longitude.toFixed(4)}°E ({location.cluster_radius_km.toFixed(2)} km radius)
          </div>
        </div>

        {/* WHEN */}
        <div className="banner-metric-block">
          <div className="metric-step-label">2. WHEN (Time Shift)</div>
          <div className="metric-main-val text-amber">{temporal.time_window}</div>
          <div className="metric-sub-val">
            Target Month: {temporal.target_month} {temporal.is_peak_window ? '• Peak Traffic Shift' : ''}
          </div>
        </div>

        {/* HOW RISKY */}
        <div className="banner-metric-block highlight-risk-block">
          <div className="metric-step-label">3. HOW RISKY? (Model Probability)</div>
          <div className="metric-main-val text-red">
            {prediction.risk_tier} RISK ({probPct}%)
          </div>
          <div className="metric-sub-val">
            <strong>{multiplier}x elevated</strong> vs metro base rate (~6.5%)
          </div>
        </div>
      </div>

      {/* Quick Action Navigation Buttons */}
      <div className="banner-actions-row">
        <span className="action-hint">Inspect Risk Breakdown:</span>
        <button className="btn-jump-section" onClick={onScrollToFactors}>
          <span>4. Why This Area is Flagged (SHAP Factors) ↓</span>
        </button>
        <button className="btn-jump-section btn-guidance-jump" onClick={onScrollToGuidance}>
          <span>5. What Prevention Measures Apply (RAG Guidance) ↓</span>
        </button>
      </div>
    </div>
  );
}

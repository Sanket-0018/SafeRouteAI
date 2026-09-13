import React, { useRef } from 'react';
import {
  MapPin,
  Clock,
  Gauge,
  Calendar,
  Layers,
  AlertTriangle,
  Sparkles,
  ShieldCheck,
  TrendingUp,
  HelpCircle,
  BookOpen,
} from 'lucide-react';
import ShapFactorsView from './ShapFactorsView';
import RagGuidanceView from './RagGuidanceView';

export default function HotspotDetail({ hotspotDetail, isLoading = false, factorsRef, guidanceRef }) {
  if (isLoading) {
    return (
      <div className="detail-loading-panel">
        <div className="spinner-large" />
        <p>Loading deep hotspot intelligence from FastAPI...</p>
      </div>
    );
  }

  if (!hotspotDetail) {
    return (
      <div className="detail-empty-panel">
        <AlertTriangle size={36} className="text-amber" />
        <h3>Select a Hotspot Window to Inspect Intelligence</h3>
        <p>Click on any marker on the map, use the Risk Checker above, or choose a row in the table to load the full prediction rationale and preventive safety guidelines.</p>
      </div>
    );
  }

  const { rank, location, temporal, prediction, contributing_factors, safety_guidance, retrieval_query } =
    hotspotDetail;
  const probPct = (prediction.high_probability * 100).toFixed(1);
  const baselineMultiplier = (prediction.high_probability / 0.065).toFixed(1);

  return (
    <div className="hotspot-detail-container">
      {/* Detailed Risk Intelligence Header */}
      <div className="detail-hero-card">
        <div className="hero-top-row">
          <div className="hero-rank-group">
            <span className="hero-rank-badge">Priority #{rank}</span>
            <div className="hero-title-group">
              <h2 className="hero-city-title">
                {location.city} • <span className="text-muted">Zone {location.zone_id}</span>
              </h2>
              <span className="hero-coords">
                {location.latitude.toFixed(4)}°N, {location.longitude.toFixed(4)}°E
              </span>
            </div>
          </div>

          <div className="hero-tier-box">
            <span className="hero-tier-pill high">{prediction.risk_tier} RISK TIER</span>
            <div className="hero-prob-text">
              <strong>{probPct}%</strong> High Probability
            </div>
          </div>
        </div>

        {/* Spatial & Temporal Metadata Pills */}
        <div className="hero-meta-grid">
          <div className="meta-card">
            <Clock size={16} className="meta-icon text-blue" />
            <div>
              <div className="meta-label">Time Shift Window</div>
              <div className="meta-value">{temporal.time_window}</div>
            </div>
          </div>

          <div className="meta-card">
            <Calendar size={16} className="meta-icon text-purple" />
            <div>
              <div className="meta-label">Evaluation Period</div>
              <div className="meta-value">{temporal.target_month} (Test Set)</div>
            </div>
          </div>

          <div className="meta-card">
            <Layers size={16} className="meta-icon text-amber" />
            <div>
              <div className="meta-label">Hotspot Area Radius</div>
              <div className="meta-value">{location.cluster_radius_km.toFixed(2)} km radius</div>
            </div>
          </div>

          <div className="meta-card">
            <TrendingUp size={16} className="meta-icon text-red" />
            <div>
              <div className="meta-label">Risk Elevation</div>
              <div className="meta-value">{baselineMultiplier}x over base rate</div>
            </div>
          </div>
        </div>

        {temporal.is_peak_window && (
          <div className="peak-alert-banner">
            <AlertTriangle size={15} />
            <span>This shift coincides with known metropolitan peak-traffic congestion hours.</span>
          </div>
        )}
      </div>

      {/* 4. WHY THIS AREA IS FLAGGED (SHAP Factor Attribution Section) */}
      <div ref={factorsRef} id="section-factors">
        <ShapFactorsView factors={contributing_factors} />
      </div>

      {/* 5. WHAT SHOULD AUTHORITIES & COMMUTERS KNOW? (RAG Prevention Guidance) */}
      <div ref={guidanceRef} id="section-guidance">
        <RagGuidanceView guidance={safety_guidance} retrievalQuery={retrieval_query} />
      </div>
    </div>
  );
}

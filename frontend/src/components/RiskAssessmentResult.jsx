import React from 'react';
import {
  AlertTriangle,
  MapPin,
  Clock,
  Gauge,
  HelpCircle,
  BookOpen,
  Info,
  ExternalLink,
  ShieldCheck,
  TrendingUp,
  Award,
  CheckCircle2,
} from 'lucide-react';
import ShapFactorsView from './ShapFactorsView';
import RagGuidanceView from './RagGuidanceView';

export default function RiskAssessmentResult({
  assessmentResult,
  isLoading = false,
  onExploreHotspots,
}) {
  if (isLoading) {
    return (
      <div className="assessment-loading-card">
        <div className="spinner-large" />
        <p>Evaluating road-safety accident risk and retrieving prevention standards...</p>
      </div>
    );
  }

  if (!assessmentResult) {
    return (
      <div className="assessment-empty-card">
        <MapPin size={36} className="text-red" />
        <h3>Where are you heading?</h3>
        <p>
          Enter your planned destination and travel time above, or click on any hotspot on the map to evaluate road-safety risk conditions.
        </p>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // CASE B: Location is OUTSIDE model coverage (e.g. Nagpur, Jaipur, Lucknow)
  // ──────────────────────────────────────────────────────────────────────────
  if (!assessmentResult.covered) {
    return (
      <div className="unsupported-coverage-card">
        <div className="unsupported-header">
          <div className="unsupported-title-row">
            <Info size={24} className="text-amber" />
            <div>
              <h3 className="unsupported-title">Location Found: {assessmentResult.location_name}</h3>
              <span className="unsupported-tag">Outside Active Model Coverage</span>
            </div>
          </div>
        </div>

        <div className="unsupported-body">
          <p className="unsupported-message">
            <strong>Model Coverage Limitation:</strong> {assessmentResult.message}
          </p>
          <div className="unsupported-details-box">
            <div className="detail-item">
              <span className="detail-label">Queried Coordinates:</span>
              <span className="detail-val">
                {assessmentResult.latitude.toFixed(4)}°N, {assessmentResult.longitude.toFixed(4)}°E
              </span>
            </div>
            {assessmentResult.nearest_supported_city && (
              <div className="detail-item">
                <span className="detail-label">Nearest Evaluated Corridor:</span>
                <span className="detail-val">
                  {assessmentResult.nearest_supported_city}{' '}
                  {assessmentResult.distance_km ? `(~${assessmentResult.distance_km} km away)` : ''}
                </span>
              </div>
            )}
            <div className="detail-item">
              <span className="detail-label">Responsible AI Policy:</span>
              <span className="detail-val text-green">
                Zero synthetic or unverified predictions generated for unsupported regions.
              </span>
            </div>
          </div>

          <div className="unsupported-actions">
            <button className="btn-explore-supported" onClick={onExploreHotspots}>
              <span>Explore Active Hotspots & Metros →</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // CASE A: Location is COVERED & EVALUATED (e.g. Pune, Bangalore, Hyderabad)
  // ──────────────────────────────────────────────────────────────────────────
  const intelligence = assessmentResult.intelligence;
  if (!intelligence) return null;

  const { location, temporal, prediction, contributing_factors, safety_guidance, retrieval_query } =
    intelligence;
  const probPct = (prediction.high_probability * 100).toFixed(1);
  const multiplier = (prediction.high_probability / 0.065).toFixed(1);
  const areaDisplay = location.area_name || `${location.city} Corridor`;

  return (
    <div className="assessment-result-container">
      {/* Visual Dominant Result Card */}
      <div className="dominant-risk-card">
        <div className="risk-card-top-bar">
          <div className="risk-badge-group">
            <AlertTriangle size={18} className="text-red pulse-dot" />
            <span className="risk-badge-text">ROAD-SAFETY RISK ASSESSMENT</span>
          </div>
          <span className="risk-tier-pill high">{prediction.risk_tier} RISK</span>
        </div>

        {/* 3 Core Immediate Answers */}
        <div className="three-answers-grid">
          {/* 1. WHERE? */}
          <div className="answer-block">
            <div className="answer-step-tag">1. WHERE?</div>
            <div className="answer-primary-text">
              <MapPin size={16} className="text-red" />
              <span>{areaDisplay}</span>
            </div>
            <div className="answer-sub-text">
              {location.city}, Maharashtra • {location.latitude.toFixed(4)}°N, {location.longitude.toFixed(4)}°E
            </div>
          </div>

          {/* 2. WHEN? */}
          <div className="answer-block">
            <div className="answer-step-tag">2. WHEN?</div>
            <div className="answer-primary-text">
              <Clock size={16} className="text-amber" />
              <span>{temporal.time_window}</span>
            </div>
            <div className="answer-sub-text">
              {temporal.is_peak_window ? '⚠️ Coincides with metropolitan rush hours' : 'Regular travel window'}
            </div>
          </div>

          {/* 3. HOW RISKY? */}
          <div className="answer-block highlight-risk">
            <div className="answer-step-tag">3. HOW RISKY?</div>
            <div className="answer-primary-text text-red">
              <Gauge size={16} className="text-red" />
              <span>{probPct}% High Probability</span>
            </div>
            <div className="answer-sub-text">
              <strong>{multiplier}x elevated risk</strong> compared to regional baseline (~6.5%)
            </div>
          </div>
        </div>

        <div className="prob-bar-container">
          <div className="prob-bar-track">
            <div
              className="prob-bar-fill"
              style={{ width: `${Math.min(100, Math.max(15, prediction.high_probability * 100))}%` }}
            />
          </div>
          <div className="prob-bar-labels">
            <span>Low Risk (0%)</span>
            <span>City Base Rate (~6.5%)</span>
            <span className="text-red font-bold">Predicted Risk ({probPct}%)</span>
          </div>
        </div>
      </div>

      {/* 4. WHY IS THIS LOCATION/TIME FLAGGED? */}
      <ShapFactorsView factors={contributing_factors} />

      {/* 5. WHAT SHOULD YOU DO? (Prevention Guidance) */}
      <RagGuidanceView guidance={safety_guidance} retrievalQuery={retrieval_query} />
    </div>
  );
}

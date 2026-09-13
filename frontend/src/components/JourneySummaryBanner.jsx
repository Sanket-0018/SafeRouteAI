import React from 'react';
import {
  ArrowRight,
  ArrowLeft,
  Clock,
  Layers,
  Calendar,
} from 'lucide-react';

export default function JourneySummaryBanner({ assessment, onBackToPlanner }) {
  if (!assessment) return null;

  const {
    origin,
    destination,
    departure_datetime,
    total_distance_km,
    estimated_duration_formatted,
    total_hazards_count,
    ml_hotspots_count,
    official_blackspots_count,
    highest_risk_time_window,
    road_context_summary,
  } = assessment;

  // Format departure datetime if available
  let formattedDeparture = departure_datetime;
  try {
    const dt = new Date(departure_datetime);
    if (!isNaN(dt.getTime())) {
      formattedDeparture = dt.toLocaleString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      });
    }
  } catch {
    formattedDeparture = departure_datetime;
  }

  // Simplified city names for title
  const originCity = origin.split(',')[0].trim().toUpperCase();
  const destCity = destination.split(',')[0].trim().toUpperCase();

  return (
    <section className="journey-summary-bar">
      {/* Optional Top Navigation Row */}
      {onBackToPlanner && (
        <div className="summary-nav-row">
          <button
            type="button"
            className="btn-banner-back"
            onClick={onBackToPlanner}
            aria-label="Back to Journey Planner"
          >
            <ArrowLeft size={13} />
            <span>Back to Journey Planner</span>
          </button>
        </div>
      )}

      <div className="summary-main-row">
        <div className="summary-title-col">
          <div className="summary-route-heading">
            <span className="city-title">{originCity}</span>
            <ArrowRight size={16} className="route-arrow" />
            <span className="city-title">{destCity}</span>
          </div>
          <div className="summary-meta-line">
            <span className="meta-metric"><strong>{total_distance_km} km</strong></span>
            <span className="meta-sep">·</span>
            <span className="meta-metric"><strong>{estimated_duration_formatted}</strong> driving time</span>
            {formattedDeparture && (
              <>
                <span className="meta-sep">·</span>
                <span className="meta-dep">
                  <Calendar size={11} />
                  <span>Departure: {formattedDeparture}</span>
                </span>
              </>
            )}
          </div>
        </div>

        <div className="summary-hazards-col">
          <div className="hazard-count-badge">
            <span className="hazard-count-number">{total_hazards_count}</span>
            <span className="hazard-count-label">Identified Hazards Along Route</span>
          </div>
          <div className="hazard-sources-row">
            <span className="source-chip ml-chip">
              <span className="chip-dot ml-dot">●</span> {ml_hotspots_count} ML Hotspots
            </span>
            <span className="source-chip official-chip">
              <span className="chip-dot official-dot">◆</span> {official_blackspots_count} Official Blackspots
            </span>
          </div>
        </div>
      </div>

      {/* Secondary Context Strips */}
      <div className="summary-context-row">
        {highest_risk_time_window && (
          <div className="context-time-window">
            <Clock size={12} className="text-amber" />
            <span className="context-label">ELEVATED RISK WINDOW:</span>
            <span className="context-val">{highest_risk_time_window}</span>
            <span className="context-note">(historical night transit density)</span>
          </div>
        )}

        {road_context_summary && (
          <div className="context-road-strip">
            <Layers size={12} className="text-muted" />
            <span className="context-label">OBSERVED INFRASTRUCTURE:</span>
            {road_context_summary.major_highways?.length > 0 && (
              <span className="road-chip">{road_context_summary.major_highways.join(', ')}</span>
            )}
            {road_context_summary.divided_carriageway_pct !== null && (
              <span className="road-chip">{road_context_summary.divided_carriageway_pct}% divided</span>
            )}
            {road_context_summary.lit_coverage_pct !== null && (
              <span className="road-chip">~{road_context_summary.lit_coverage_pct}% lit</span>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

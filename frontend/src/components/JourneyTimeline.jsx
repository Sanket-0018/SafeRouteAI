import React, { useState, useEffect } from 'react';
import {
  Clock,
  MapPin,
  ShieldCheck,
  ExternalLink,
  BookOpen,
  Activity,
  Award,
  Layers,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
} from 'lucide-react';

export default function JourneyTimeline({
  hazards = [],
  selectedHazardSeq = null,
  onSelectHazard,
}) {
  const [expandedHazards, setExpandedHazards] = useState({});

  // Auto-expand and scroll when a hazard is selected from the map
  useEffect(() => {
    if (selectedHazardSeq !== null) {
      setExpandedHazards((prev) => ({ ...prev, [selectedHazardSeq]: true }));
      const cardNode = document.getElementById(`hazard-card-${selectedHazardSeq}`);
      if (cardNode) {
        cardNode.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }, [selectedHazardSeq]);

  const toggleExpand = (seq, e) => {
    if (e) e.stopPropagation();
    setExpandedHazards((prev) => ({ ...prev, [seq]: !prev[seq] }));
  };

  const handleExpandAll = () => {
    const allExpanded = hazards.reduce((acc, h) => {
      acc[h.sequence] = true;
      return acc;
    }, {});
    setExpandedHazards(allExpanded);
  };

  const handleCollapseAll = () => {
    setExpandedHazards({});
  };

  if (!hazards || hazards.length === 0) {
    return (
      <div className="workspace-timeline-panel">
        <div className="empty-hazards-panel">
          <ShieldCheck size={36} className="text-status-ok" />
          <h3 className="empty-title">No identified hazards in the available evidence.</h3>
          <p className="empty-desc">
            This assessment reflects the available historical crash patterns and official government registry evidence. The absence of flagged hazards does not guarantee a risk-free journey. Always observe live traffic, weather, and road conditions.
          </p>
        </div>
      </div>
    );
  }

  const allAreExpanded = hazards.length > 0 && hazards.every((h) => expandedHazards[h.sequence]);

  return (
    <div className="workspace-timeline-panel">
      {/* Aligned Timeline Header */}
      <div className="workspace-panel-header">
        <div className="panel-header-left">
          <Activity size={14} className="text-muted" />
          <span className="panel-title">CORRIDOR HAZARDS</span>
          <span className="timeline-count-badge">{hazards.length} Flagged</span>
        </div>
        <div className="panel-header-right">
          <button
            type="button"
            className="btn-timeline-toggle-all"
            onClick={allAreExpanded ? handleCollapseAll : handleExpandAll}
          >
            {allAreExpanded ? 'Collapse all' : 'Expand all'}
          </button>
        </div>
      </div>

      <div className="timeline-scroll-container">
        {hazards.map((h, idx) => {
          const isSelected = h.sequence === selectedHazardSeq;
          const isML = h.hazard_type === 'ML_PREDICTED_HOTSPOT';
          const isExpanded = !!expandedHazards[h.sequence];
          const probPct = h.risk_probability ? (h.risk_probability * 100).toFixed(1) : null;
          const roadCtx = h.road_context;

          return (
            <div
              key={h.sequence}
              id={`hazard-card-${h.sequence}`}
              style={{ '--index': idx }}
              className={`timeline-milestone-row ${isML ? 'row-ml' : 'row-official'} ${
                isSelected ? 'row-selected' : ''
              } ${isExpanded ? 'milestone-expanded' : 'milestone-collapsed'}`}
              onClick={() => {
                if (onSelectHazard) onSelectHazard(h.sequence);
              }}
            >
              {/* Vertical connector & Node badge */}
              <div className="timeline-node-gutter">
                {isML ? (
                  <div className="node-badge-ml-circle" title="ML-Predicted Risk Hotspot">
                    <span className="node-num">{h.sequence}</span>
                  </div>
                ) : (
                  <div className="node-badge-official-diamond" title="Official Government Blackspot">
                    <div className="diamond-shape" />
                    <span className="node-num">{h.sequence}</span>
                  </div>
                )}
                <div className="timeline-track-line" />
              </div>

              {/* Milestone Card Body */}
              <div className="timeline-briefing-card">
                {/* 1. Milestone Header (Always Visible — Compact & High-Signal) */}
                <div
                  className="card-compact-header"
                  onClick={(e) => toggleExpand(h.sequence, e)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      toggleExpand(h.sequence, e);
                    }
                  }}
                  aria-expanded={isExpanded}
                >
                  <div className="milestone-main-info">
                    <div className="milestone-title-line">
                      <h4 className="location-name">{h.location_name}</h4>
                      {h.highway && <span className="highway-pill">{h.highway}</span>}
                    </div>

                    <div className="milestone-meta-pills">
                      <span className="dist-pill">
                        <MapPin size={11} className="text-muted" />
                        <span>{h.distance_from_origin_km} km</span>
                      </span>
                      <span className="meta-sep">·</span>
                      <span className="eta-pill">
                        <Clock size={11} className="text-amber" />
                        <span>ETA {h.expected_arrival_time}</span>
                        {h.expected_arrival_window && (
                          <span className="shift-sub">({h.expected_arrival_window})</span>
                        )}
                      </span>
                    </div>
                  </div>

                  <div className="milestone-header-right">
                    <span className={`type-badge-pill ${isML ? 'badge-ml' : 'badge-official'}`}>
                      <span className="badge-icon">{isML ? '●' : '◆'}</span>
                      <span className="badge-text">{isML ? 'ML Hotspot' : 'Official Blackspot'}</span>
                    </span>

                    <button
                      type="button"
                      className="btn-milestone-expand"
                      aria-label={isExpanded ? 'Collapse hazard details' : 'Expand hazard details'}
                      onClick={(e) => toggleExpand(h.sequence, e)}
                    >
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                  </div>
                </div>

                {/* 2. EXPANDED BODY (Progressive Disclosure) */}
                {isExpanded && (
                  <div className="hazard-expanded-body">
                    {/* Primary Evidence & Risk Metrics Banner */}
                    <div className={`card-type-banner ${isML ? 'type-banner-ml' : 'type-banner-official'}`}>
                      <div className="type-title-group">
                        <span className="type-symbol">{isML ? '🔴' : '🟠'}</span>
                        <span className="type-text">
                          {isML ? 'STATISTICAL RISK PREDICTION' : 'GOVERNMENT REGISTRY RECORD'}
                        </span>
                      </div>

                      <div className="type-metric-group">
                        {isML && probPct && (
                          <span className="metric-tag tag-ml">
                            <strong>{probPct}%</strong> Historical Risk Probability
                          </span>
                        )}
                        {isML && !h.covered && (
                          <span className="metric-tag tag-coverage">
                            ML risk coverage is unavailable for this location
                          </span>
                        )}
                        {!isML && h.official_provenance?.total_fatalities_3yr !== undefined && (
                          <span className="metric-tag tag-official">
                            <strong>{h.official_provenance.total_fatalities_3yr} Fatalities</strong> ({h.official_provenance.fatal_crashes_3yr || 0} crashes)
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Rationale Callout */}
                    <div className="card-reason-summary">
                      <div className="reason-label">ASSESSMENT RATIONALE</div>
                      <p>{h.reason}</p>
                    </div>

                    {/* Observed Road Context */}
                    {roadCtx && (
                      <div className="card-sub-section road-context-sub">
                        <div className="sub-section-title">
                          <Layers size={12} className="text-muted" />
                          <span>OBSERVED ROAD CONTEXT</span>
                        </div>
                        <div className="road-chips-row">
                          {roadCtx.highway_class && (
                            <span className="road-data-chip">{roadCtx.highway_class.toUpperCase()}</span>
                          )}
                          {roadCtx.lanes && (
                            <span className="road-data-chip">{roadCtx.lanes} Lanes</span>
                          )}
                          {roadCtx.maxspeed_kmh && (
                            <span className="road-data-chip">{roadCtx.maxspeed_kmh} km/h</span>
                          )}
                          {roadCtx.is_lit !== null && roadCtx.is_lit !== undefined && (
                            <span className={`road-data-chip ${roadCtx.is_lit ? 'chip-lit' : 'chip-unlit'}`}>
                              {roadCtx.is_lit ? '💡 Illuminated' : '🌑 Unlit'}
                            </span>
                          )}
                          {roadCtx.is_bridge && <span className="road-data-chip chip-alert">Bridge</span>}
                          {roadCtx.is_tunnel && <span className="road-data-chip chip-alert">Tunnel</span>}
                          {roadCtx.is_junction && <span className="road-data-chip chip-alert">Junction</span>}
                        </div>
                      </div>
                    )}

                    {/* Safety Guidance */}
                    {h.safety_guidance && h.safety_guidance.length > 0 && (
                      <div className="card-sub-section guidance-sub">
                        <div className="sub-section-title">
                          <BookOpen size={12} className="text-muted" />
                          <span>DOMAIN SAFETY GUIDANCE</span>
                        </div>
                        <div className="guidance-list">
                          {h.safety_guidance.map((g, idx) => (
                            <div key={idx} className="guidance-mini-card">
                              <div className="guidance-mini-head">
                                <span className="guidance-heading">{g.title}</span>
                                <span className="guidance-authority">{g.organization}</span>
                              </div>
                              <p className="guidance-mini-body">{g.content_excerpt}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Statistical Model Attribution (SHAP) for ML */}
                    {isML && h.contributing_factors?.length > 0 && (
                      <div className="card-sub-section tech-sub">
                        <div className="sub-section-title">
                          <Activity size={12} className="text-muted" />
                          <span>STATISTICAL MODEL ATTRIBUTION (SHAP)</span>
                        </div>
                        <p className="tech-notice-text">
                          Describes model feature sensitivity in historical patterns, not mechanical accident causation.
                        </p>
                        <div className="shap-chips-row">
                          {h.contributing_factors.map((f, idx) => (
                            <div key={idx} className="shap-chip">
                              <span className="shap-name">{f.feature}</span>
                              <span className="shap-val">+{f.contribution.toFixed(3)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Official Evidence & Registry Audit for Government Blackspots */}
                    {!isML && h.official_provenance && (
                      <div className="card-sub-section tech-sub">
                        <div className="sub-section-title">
                          <Award size={12} className="text-hazard-official" />
                          <span>OFFICIAL EVIDENCE & REGISTRY AUDIT</span>
                        </div>
                        <div className="official-meta-rows">
                          <div>
                            <span className="meta-lbl">Authority:</span>{' '}
                            <strong>{h.official_provenance.source_organization}</strong> ({h.official_provenance.report_year})
                          </div>
                          <div>
                            <span className="meta-lbl">Blackspot ID:</span>{' '}
                            <code className="code-tag">{h.official_provenance.blackspot_id}</code>
                          </div>
                          {h.official_provenance.total_fatalities_3yr !== undefined && (
                            <div>
                              <span className="meta-lbl">3-Year Record:</span>{' '}
                              <strong>{h.official_provenance.total_fatalities_3yr} Fatalities</strong> across {h.official_provenance.fatal_crashes_3yr || 0} Fatal Crashes
                            </div>
                          )}
                          {h.official_provenance.source_url && (
                            <div>
                              <a
                                href={h.official_provenance.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="official-source-link"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <span>Official Registry Source</span>
                                <ExternalLink size={10} />
                              </a>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

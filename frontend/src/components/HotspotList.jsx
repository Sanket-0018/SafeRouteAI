import React, { useState } from 'react';
import { ChevronRight, Clock, MapPin, Gauge, Search, Sparkles, AlertCircle } from 'lucide-react';

export default function HotspotList({
  hotspots = [],
  selectedRank = null,
  onSelectHotspot,
  isLoading = false,
}) {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = hotspots.filter((h) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      h.city.toLowerCase().includes(term) ||
      h.zone_id.toString().includes(term) ||
      h.time_window.toLowerCase().includes(term) ||
      h.rank.toString() === term
    );
  });

  return (
    <div className="hotspot-list-wrapper">
      <div className="list-header-bar">
        <div className="list-title-row">
          <Gauge size={16} className="text-red" />
          <div>
            <span className="list-title">Priority Risk Windows</span>
            <span className="list-subtitle-tag">Ranked by Model Probability</span>
          </div>
          <span className="list-count-badge">{filtered.length}</span>
        </div>
        <div className="list-search-box">
          <Search size={14} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search city, zone, or shift..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="table-responsive-container">
        <table className="hotspot-table">
          <thead>
            <tr>
              <th style={{ width: '60px' }}>Rank</th>
              <th>WHERE (Location)</th>
              <th>WHEN (Time Shift)</th>
              <th style={{ width: '140px' }}>HOW RISKY? (Probability)</th>
              <th style={{ width: '40px' }}></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <tr key={i} className="skeleton-row">
                  <td colSpan={5}>
                    <div className="skeleton-line" />
                  </td>
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty-table-cell">
                  No matching risk windows found for the current search filter.
                </td>
              </tr>
            ) : (
              filtered.map((h) => {
                const isSelected = h.rank === selectedRank;
                const probPct = (h.high_probability * 100).toFixed(1);
                const isPeak = h.is_peak_window;

                return (
                  <tr
                    key={h.rank}
                    className={`hotspot-row ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSelectHotspot(h.rank)}
                  >
                    <td>
                      <span className={`rank-pill ${h.rank <= 3 ? 'top-rank' : ''}`}>
                        #{h.rank}
                      </span>
                    </td>
                    <td>
                      <div className="table-location">
                        <span className="city-name">{h.city}</span>
                        <span className="zone-tag">Zone {h.zone_id}</span>
                      </div>
                      <div className="coords-text">
                        {h.latitude.toFixed(3)}°N, {h.longitude.toFixed(3)}°E
                      </div>
                    </td>
                    <td>
                      <div className="window-cell">
                        <span className="window-text">{h.time_window}</span>
                        {isPeak && <span className="peak-badge">Peak Rush</span>}
                      </div>
                      <div className="target-month-sub">{h.target_month}</div>
                    </td>
                    <td>
                      <div className="prob-container">
                        <div className="prob-header">
                          <span className="tier-pill high">{h.risk_tier}</span>
                          <span className="prob-val">{probPct}%</span>
                        </div>
                        <div className="prob-track">
                          <div
                            className="prob-fill"
                            style={{ width: `${Math.min(100, Math.max(10, h.high_probability * 100))}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>
                      <ChevronRight
                        size={16}
                        className={`row-arrow ${isSelected ? 'arrow-selected' : ''}`}
                      />
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

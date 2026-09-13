import React, { useState, useEffect } from 'react';
import { Search, MapPin, Clock, ShieldAlert, Sparkles, Navigation2Off, ArrowRight } from 'lucide-react';

const TIME_WINDOW_OPTIONS = [
  { value: '', label: 'Any Time Shift Window' },
  { value: '00:00 - 03:59 (Late Night)', label: '00:00 - 03:59 (Late Night Shift)' },
  { value: '04:00 - 07:59 (Early Morning)', label: '04:00 - 07:59 (Early Morning Shift)' },
  { value: '08:00 - 11:59 (Morning Rush)', label: '08:00 - 11:59 (Morning Rush Hours)' },
  { value: '12:00 - 15:59 (Afternoon)', label: '12:00 - 15:59 (Afternoon Window)' },
  { value: '16:00 - 19:59 (Evening Rush)', label: '16:00 - 19:59 (Evening Rush Hours)' },
  { value: '20:00 - 23:59 (Night)', label: '20:00 - 23:59 (Night Window)' },
];

export default function RiskCheckerWidget({
  cities = [],
  hotspots = [],
  onSearchMatch,
  selectedCity,
  onChangeCity,
}) {
  const [selectedZone, setSelectedZone] = useState('');
  const [selectedWindow, setSelectedWindow] = useState('');
  const [availableZones, setAvailableZones] = useState([]);
  const [searchFeedback, setSearchFeedback] = useState(null);

  // Extract distinct zones for the currently selected city
  useEffect(() => {
    const zonesSet = new Set();
    hotspots.forEach((h) => {
      if (!selectedCity || h.city.toLowerCase() === selectedCity.toLowerCase()) {
        zonesSet.add(h.zone_id);
      }
    });
    setAvailableZones(Array.from(zonesSet).sort((a, b) => a - b));
    setSelectedZone('');
  }, [selectedCity, hotspots]);

  const handleCheckRisk = () => {
    // Find matching hotspot in current dataset
    const matched = hotspots.find((h) => {
      const matchCity = !selectedCity || h.city.toLowerCase() === selectedCity.toLowerCase();
      const matchZone = !selectedZone || h.zone_id.toString() === selectedZone.toString();
      const matchWindow = !selectedWindow || h.time_window.includes(selectedWindow) || selectedWindow.includes(h.time_window);
      return matchCity && matchZone && matchWindow;
    });

    if (matched) {
      setSearchFeedback({
        type: 'found',
        message: `High-risk prediction found for ${matched.city} (Zone ${matched.zone_id}) during ${matched.time_window}. Displaying full intelligence report.`,
      });
      onSearchMatch(matched.rank);
    } else {
      // Fallback: match by city or select highest risk in city
      const cityMatch = hotspots.find((h) => !selectedCity || h.city.toLowerCase() === selectedCity.toLowerCase());
      if (cityMatch) {
        setSearchFeedback({
          type: 'info',
          message: `Showing highest risk window available for ${selectedCity || 'selected filters'} (Zone ${cityMatch.zone_id} • ${cityMatch.time_window}).`,
        });
        onSearchMatch(cityMatch.rank);
      } else {
        setSearchFeedback({
          type: 'empty',
          message: 'No elevated risk hotspot record matches this exact combination in the test register.',
        });
      }
    }
  };

  const handleQuickPreset = (city, zone, windowStr) => {
    onChangeCity(city);
    setSelectedZone(zone.toString());
    setSelectedWindow(windowStr);

    const match = hotspots.find(
      (h) =>
        h.city.toLowerCase() === city.toLowerCase() &&
        h.zone_id.toString() === zone.toString() &&
        h.time_window.includes(windowStr)
    );

    if (match) {
      setSearchFeedback({
        type: 'found',
        message: `Preset activated: ${city} Zone ${zone} (${windowStr}).`,
      });
      onSearchMatch(match.rank);
    }
  };

  return (
    <section className="risk-checker-card">
      <div className="checker-header">
        <div className="checker-title-row">
          <ShieldAlert size={20} className="text-red" />
          <div>
            <h2 className="checker-title">Check Area & Travel-Time Risk</h2>
            <p className="checker-subtitle">
              Look up accident risk predictions for a city, hotspot zone, and planned time window.
            </p>
          </div>
        </div>
      </div>

      <div className="checker-controls-grid">
        {/* City Selector */}
        <div className="checker-field">
          <label className="checker-label">
            <MapPin size={14} className="text-blue" />
            <span>Target City</span>
          </label>
          <select
            className="checker-select"
            value={selectedCity}
            onChange={(e) => onChangeCity(e.target.value)}
          >
            <option value="">All Metros (7 Indian Cities)</option>
            {cities.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* Hotspot Zone Selector */}
        <div className="checker-field">
          <label className="checker-label">
            <MapPin size={14} className="text-amber" />
            <span>Hotspot Area / Zone</span>
          </label>
          <select
            className="checker-select"
            value={selectedZone}
            onChange={(e) => setSelectedZone(e.target.value)}
          >
            <option value="">All Monitored Hotspot Zones</option>
            {availableZones.map((z) => (
              <option key={z} value={z}>
                Zone {z} {selectedCity ? `(${selectedCity})` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Time Window Selector */}
        <div className="checker-field">
          <label className="checker-label">
            <Clock size={14} className="text-purple" />
            <span>Travel Shift / Time Window</span>
          </label>
          <select
            className="checker-select"
            value={selectedWindow}
            onChange={(e) => setSelectedWindow(e.target.value)}
          >
            {TIME_WINDOW_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Action Button */}
        <div className="checker-action-col">
          <button className="btn-check-risk" onClick={handleCheckRisk}>
            <Search size={16} />
            <span>Check Area Risk</span>
          </button>
        </div>
      </div>

      {/* Quick Presets */}
      <div className="checker-presets-row">
        <span className="presets-label">Popular High-Risk Windows:</span>
        <button
          className="preset-btn"
          onClick={() => handleQuickPreset('Pune', 363, '00:00 - 03:59')}
        >
          Pune • Zone 363 (Late Night)
        </button>
        <button
          className="preset-btn"
          onClick={() => handleQuickPreset('Pune', 363, '20:00 - 23:59')}
        >
          Pune • Zone 363 (Night)
        </button>
        <button
          className="preset-btn"
          onClick={() => handleQuickPreset('Chandigarh', 97, '04:00 - 07:59')}
        >
          Chandigarh • Zone 97 (Early Morning)
        </button>
        <button
          className="preset-btn"
          onClick={() => handleQuickPreset('Hyderabad', 233, '16:00 - 19:59')}
        >
          Hyderabad • Zone 233 (Evening Rush)
        </button>
      </div>

      {searchFeedback && (
        <div className={`search-feedback-banner ${searchFeedback.type}`}>
          <span>{searchFeedback.message}</span>
        </div>
      )}

      <div className="checker-footer-notice">
        <Navigation2Off size={13} />
        <span>
          <strong>Scope Notice:</strong> This is a spatiotemporal road-safety hazard lookup. SafeRoute AI does <em>not</em> provide turn-by-turn navigation or alternate route calculations.
        </span>
      </div>
    </section>
  );
}

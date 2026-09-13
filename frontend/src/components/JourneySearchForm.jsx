import React, { useState } from 'react';
import {
  MapPin,
  Navigation,
  Calendar,
  Clock,
  ArrowUpDown,
  Search,
} from 'lucide-react';
import PlaceSearchInput from './PlaceSearchInput';

export default function JourneySearchForm({
  onAnalyzeJourney,
  initialOrigin = 'Pune, Maharashtra',
  initialDestination = 'Nagpur, Maharashtra',
  initialDeparture = '2026-08-30T20:00:00',
  isLoading = false,
}) {
  const [originPlace, setOriginPlace] = useState({
    display_name: initialOrigin,
    latitude: 18.5204,
    longitude: 73.8567,
  });

  const [destPlace, setDestPlace] = useState({
    display_name: initialDestination,
    latitude: 21.1458,
    longitude: 79.0882,
  });

  const [depDate, setDepDate] = useState('2026-08-30');
  const [depTime, setDepTime] = useState('20:00');

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    onAnalyzeJourney({
      origin: originPlace?.display_name || initialOrigin,
      destination: destPlace?.display_name || initialDestination,
      departure_datetime: `${depDate}T${depTime}:00`,
      origin_lat: originPlace?.latitude,
      origin_lon: originPlace?.longitude,
      dest_lat: destPlace?.latitude,
      dest_lon: destPlace?.longitude,
    });
  };

  const handleSwap = () => {
    const prevOrigin = originPlace;
    const prevDest = destPlace;
    setOriginPlace(prevDest);
    setDestPlace(prevOrigin);
  };

  const handlePreset = (orig, origLat, origLon, dest, destLat, destLon, date, time) => {
    const origObj = { display_name: orig, latitude: origLat, longitude: origLon };
    const destObj = { display_name: dest, latitude: destLat, longitude: destLon };
    setOriginPlace(origObj);
    setDestPlace(destObj);
    setDepDate(date);
    setDepTime(time);
    onAnalyzeJourney({
      origin: orig,
      destination: dest,
      departure_datetime: `${date}T${time}:00`,
      origin_lat: origLat,
      origin_lon: origLon,
      dest_lat: destLat,
      dest_lon: destLon,
    });
  };

  return (
    <section className="search-console-card">
      <form onSubmit={handleSubmit} className="console-form-container">
        {/* Upper Block: Connected Vertical Route Indicator with Origin & Destination */}
        <div className="route-endpoints-block">
          {/* Vertical Visual Transit Track */}
          <div className="route-track-gutter" aria-hidden="true">
            <div className="route-node-pin origin-node-pin" title="Starting Point">
              <span className="route-node-dot origin-dot" />
            </div>
            <div className="route-track-vertical-line" />
            <div className="route-node-pin dest-node-pin" title="Destination">
              <span className="route-node-dot dest-dot" />
            </div>
          </div>

          {/* Search Inputs Stack */}
          <div className="route-inputs-stack">
            {/* Origin Row */}
            <div className="route-input-row origin-row">
              <PlaceSearchInput
                label="STARTING POINT"
                icon={MapPin}
                iconClass="text-status-ok"
                placeholder="Search starting city, airport, station..."
                initialText={originPlace?.display_name || initialOrigin}
                onSelectPlace={(place) => setOriginPlace(place)}
                required
              />
            </div>

            {/* Destination Row */}
            <div className="route-input-row dest-row">
              <PlaceSearchInput
                label="DESTINATION"
                icon={Navigation}
                iconClass="text-dest"
                placeholder="Search destination city, town, landmark..."
                initialText={destPlace?.display_name || initialDestination}
                onSelectPlace={(place) => setDestPlace(place)}
                required
              />
            </div>
          </div>

          {/* Floating Midpoint Swap Button */}
          <div className="route-swap-wrap">
            <button
              type="button"
              className="btn-swap-endpoints"
              onClick={handleSwap}
              title="Swap Origin & Destination"
              aria-label="Swap starting point and destination"
            >
              <ArrowUpDown size={15} />
            </button>
          </div>
        </div>

        {/* Lower Block: Timing Controls & Tactile Primary CTA Bar */}
        <div className="route-action-bar">
          <div className="timing-inputs-group">
            {/* Departure Date */}
            <div className="timing-field-col date-field">
              <label className="timing-field-label">
                <Calendar size={12} className="text-muted" />
                <span>DEPARTURE DATE</span>
              </label>
              <div className="timing-input-wrap">
                <input
                  type="date"
                  className="timing-text-input"
                  value={depDate}
                  onChange={(e) => setDepDate(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Departure Time */}
            <div className="timing-field-col time-field">
              <label className="timing-field-label">
                <Clock size={12} className="text-muted" />
                <span>DEPARTURE TIME</span>
              </label>
              <div className="timing-input-wrap">
                <input
                  type="time"
                  className="timing-text-input"
                  value={depTime}
                  onChange={(e) => setDepTime(e.target.value)}
                  required
                />
              </div>
            </div>
          </div>

          {/* Substantial, Tactile Primary Action CTA */}
          <div className="cta-button-col">
            <button
              type="submit"
              className="btn-primary-cta"
              disabled={isLoading}
            >
              <Search size={15} className="cta-icon" />
              <span>{isLoading ? 'ANALYZING ROAD RISKS...' : 'ANALYZE JOURNEY'}</span>
            </button>
          </div>
        </div>
      </form>

      {/* Quick Corridor Presets Strip */}
      <div className="console-presets-strip">
        <div className="presets-left">
          <span className="preset-strip-title">QUICK CORRIDORS:</span>
          <div className="preset-buttons-wrap">
            <button
              type="button"
              className="btn-preset-pill"
              onClick={() => handlePreset('Pune, Maharashtra', 18.5204, 73.8567, 'Nagpur, Maharashtra', 21.1458, 79.0882, '2026-08-30', '20:00')}
            >
              Pune → Nagpur
            </button>
            <button
              type="button"
              className="btn-preset-pill"
              onClick={() => handlePreset('Mumbai, Maharashtra', 19.0760, 72.8777, 'Pune, Maharashtra', 18.5204, 73.8567, '2026-08-30', '18:30')}
            >
              Mumbai → Pune
            </button>
            <button
              type="button"
              className="btn-preset-pill"
              onClick={() => handlePreset('Pune, Maharashtra', 18.5204, 73.8567, 'Kolhapur, Maharashtra', 16.7050, 74.2433, '2026-08-31', '07:00')}
            >
              Pune → Kolhapur
            </button>
            <button
              type="button"
              className="btn-preset-pill"
              onClick={() => handlePreset('Nashik, Maharashtra', 19.9975, 73.7898, 'Pune, Maharashtra', 18.5204, 73.8567, '2026-08-31', '16:00')}
            >
              Nashik → Pune
            </button>
          </div>
        </div>
      </div>

      {/* Subtle Supporting Evidence Indicators (NOT cards) */}
      <div className="planner-evidence-strip">
        <span className="evidence-pill ml-pill" title="Statistical Risk Model Hotspots">
          <span className="indicator-dot ml-dot" />
          <span>ML-PREDICTED HOTSPOTS</span>
        </span>
        <span className="evidence-sep">·</span>
        <span className="evidence-pill official-pill" title="State Highway Police Blackspot Registry">
          <span className="indicator-dot official-dot" />
          <span>OFFICIAL BLACKSPOTS</span>
        </span>
        <span className="evidence-sep">·</span>
        <span className="evidence-pill guidance-pill" title="MoRTH / IRC Domain Safety Guidelines">
          <span className="indicator-dot guidance-dot" />
          <span>SAFETY GUIDANCE</span>
        </span>
      </div>
    </section>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import { Search, MapPin, Clock, Calendar, ShieldAlert, Sparkles, Navigation2Off, ChevronDown, Check } from 'lucide-react';

// Comprehensive dictionary of major Indian cities, areas & corridors with coordinates
const INDIAN_LOCATIONS = [
  // Evaluated Monitored Corridors
  { name: 'Pune, Maharashtra', lat: 18.5204, lon: 73.8567, isEvaluated: true, region: 'Western India' },
  { name: 'Hadapsar / Magarpatta, Pune', lat: 18.4966, lon: 73.8833, isEvaluated: true, region: 'Pune Corridor' },
  { name: 'Hinjewadi / Wakad, Pune', lat: 18.6005, lon: 73.7709, isEvaluated: true, region: 'Pune Corridor' },
  { name: 'Gachibowli / Financial District, Hyderabad', lat: 17.4020, lon: 78.2914, isEvaluated: true, region: 'Hyderabad Corridor' },
  { name: 'Shamshabad / Airport Highway, Hyderabad', lat: 17.2777, lon: 78.2784, isEvaluated: true, region: 'Hyderabad Corridor' },
  { name: 'Secunderabad / Begumpet, Hyderabad', lat: 17.4661, lon: 78.4816, isEvaluated: true, region: 'Hyderabad Corridor' },
  { name: 'Yelahanka / Hebbal, Bangalore', lat: 13.1269, lon: 77.5816, isEvaluated: true, region: 'Bangalore Corridor' },
  { name: 'Ambattur / Avadi, Chennai', lat: 13.1496, lon: 80.1314, isEvaluated: true, region: 'Chennai Corridor' },
  { name: 'Zirakpur / Mohali, Chandigarh', lat: 30.6177, lon: 76.7799, isEvaluated: true, region: 'Chandigarh Corridor' },
  { name: 'Salt Lake / New Town, Kolkata', lat: 22.5631, lon: 88.4638, isEvaluated: true, region: 'Kolkata Corridor' },
  { name: 'Navi Mumbai / JNPT, Mumbai', lat: 18.8555, lon: 72.9237, isEvaluated: true, region: 'Mumbai Corridor' },
  
  // Unsupported / Broader Indian Cities (Tested for coverage boundary handling)
  { name: 'Nagpur, Maharashtra', lat: 21.1458, lon: 79.0882, isEvaluated: false, region: 'Central India' },
  { name: 'Jaipur, Rajasthan', lat: 26.9124, lon: 75.7873, isEvaluated: false, region: 'Northern India' },
  { name: 'Lucknow, Uttar Pradesh', lat: 26.8467, lon: 80.9462, isEvaluated: false, region: 'Northern India' },
  { name: 'Indore, Madhya Pradesh', lat: 22.7196, lon: 75.8577, isEvaluated: false, region: 'Central India' },
  { name: 'Ahmedabad, Gujarat', lat: 23.0225, lon: 72.5714, isEvaluated: false, region: 'Western India' },
  { name: 'Bhopal, Madhya Pradesh', lat: 23.2599, lon: 77.4126, isEvaluated: false, region: 'Central India' },
  { name: 'Coimbatore, Tamil Nadu', lat: 11.0168, lon: 76.9558, isEvaluated: false, region: 'Southern India' },
  { name: 'Visakhapatnam, Andhra Pradesh', lat: 17.6868, lon: 83.2185, isEvaluated: false, region: 'Eastern India' },
];

export default function LocationSearchPicker({
  onCheckRisk,
  currentLocationName,
  currentTravelTime,
  currentTravelDate,
  isLoading = false,
}) {
  const [query, setQuery] = useState(currentLocationName || 'Pune, Maharashtra');
  const [selectedCoords, setSelectedCoords] = useState({ lat: 18.5204, lon: 73.8567 });
  const [travelTime, setTravelTime] = useState(currentTravelTime || '20:00');
  const [travelDate, setTravelDate] = useState(
    currentTravelDate || new Date().toISOString().split('T')[0]
  );
  
  const [suggestions, setSuggestions] = useState([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Filter suggestions as user types
  useEffect(() => {
    if (!query || query.trim().length === 0) {
      setSuggestions(INDIAN_LOCATIONS.slice(0, 6));
      return;
    }
    const clean = query.toLowerCase().trim();
    const matches = INDIAN_LOCATIONS.filter(
      (loc) => loc.name.toLowerCase().includes(clean) || loc.region.toLowerCase().includes(clean)
    );
    setSuggestions(matches.length > 0 ? matches : []);
  }, [query]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectLocation = (loc) => {
    setQuery(loc.name);
    setSelectedCoords({ lat: loc.lat, lon: loc.lon });
    setIsDropdownOpen(false);
  };

  const handleTriggerSearch = () => {
    // Check if query matches a known location or use current coords
    const match = INDIAN_LOCATIONS.find((l) => l.name.toLowerCase() === query.toLowerCase().trim());
    const finalLat = match ? match.lat : selectedCoords.lat;
    const finalLon = match ? match.lon : selectedCoords.lon;
    const finalName = match ? match.name : query;

    onCheckRisk({
      latitude: finalLat,
      longitude: finalLon,
      location_name: finalName,
      travel_time: travelTime,
      travel_date: travelDate,
    });
  };

  const handleQuickLocation = (locName, timeStr) => {
    const loc = INDIAN_LOCATIONS.find((l) => l.name.toLowerCase().includes(locName.toLowerCase()));
    if (loc) {
      setQuery(loc.name);
      setSelectedCoords({ lat: loc.lat, lon: loc.lon });
      setTravelTime(timeStr);
      onCheckRisk({
        latitude: loc.lat,
        longitude: loc.lon,
        location_name: loc.name,
        travel_time: timeStr,
        travel_date: travelDate,
      });
    }
  };

  return (
    <section className="location-risk-search-card">
      <div className="search-card-header">
        <div className="search-title-row">
          <ShieldAlert size={22} className="text-red" />
          <div>
            <h2 className="search-card-title">Check Road-Safety Risk for Your Trip</h2>
            <p className="search-card-subtitle">
              Enter where you are going and your planned travel time to evaluate accident risk before you leave.
            </p>
          </div>
        </div>
      </div>

      <div className="search-inputs-grid">
        {/* Location Search Input with Autocomplete */}
        <div className="search-field-col location-search-col" ref={dropdownRef}>
          <label className="input-field-label">
            <MapPin size={15} className="text-red" />
            <span>Where are you going?</span>
          </label>
          <div className="input-box-wrap">
            <input
              type="text"
              className="natural-text-input"
              placeholder="Search city, area or landmark (e.g. Pune, Nagpur, Hinjewadi)..."
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setIsDropdownOpen(true);
              }}
              onFocus={() => setIsDropdownOpen(true)}
            />
            <ChevronDown size={16} className="dropdown-arrow-icon" />
          </div>

          {/* Autocomplete Dropdown */}
          {isDropdownOpen && suggestions.length > 0 && (
            <ul className="location-suggestions-dropdown">
              {suggestions.map((loc, idx) => (
                <li
                  key={idx}
                  className="suggestion-item"
                  onClick={() => handleSelectLocation(loc)}
                >
                  <div className="suggestion-left">
                    <MapPin size={14} className={loc.isEvaluated ? 'text-red' : 'text-muted'} />
                    <span className="suggestion-name">{loc.name}</span>
                  </div>
                  <span className={`coverage-tag ${loc.isEvaluated ? 'evaluated' : 'outside'}`}>
                    {loc.isEvaluated ? 'Active Risk Model' : 'Coverage Expansion'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Travel Date */}
        <div className="search-field-col date-col">
          <label className="input-field-label">
            <Calendar size={15} className="text-purple" />
            <span>Travel Date</span>
          </label>
          <input
            type="date"
            className="natural-date-input"
            value={travelDate}
            onChange={(e) => setTravelDate(e.target.value)}
          />
        </div>

        {/* Travel Time */}
        <div className="search-field-col time-col">
          <label className="input-field-label">
            <Clock size={15} className="text-amber" />
            <span>When are you travelling?</span>
          </label>
          <input
            type="time"
            className="natural-time-input"
            value={travelTime}
            onChange={(e) => setTravelTime(e.target.value)}
          />
        </div>

        {/* Primary Action Button */}
        <div className="search-field-col action-col">
          <button
            className="btn-primary-check-risk"
            onClick={handleTriggerSearch}
            disabled={isLoading}
          >
            <Search size={17} />
            <span>{isLoading ? 'Evaluating Risk...' : 'CHECK ROAD-SAFETY RISK'}</span>
          </button>
        </div>
      </div>

      {/* Quick Example Presets */}
      <div className="quick-examples-bar">
        <span className="examples-label">Try searching:</span>
        <button
          className="example-pill-btn"
          onClick={() => handleQuickLocation('Hadapsar / Magarpatta, Pune', '02:00')}
        >
          📍 Pune (Hadapsar • Late Night 02:00)
        </button>
        <button
          className="example-pill-btn"
          onClick={() => handleQuickLocation('Hinjewadi / Wakad, Pune', '19:30')}
        >
          📍 Pune (Hinjewadi • Evening 19:30)
        </button>
        <button
          className="example-pill-btn"
          onClick={() => handleQuickLocation('Zirakpur / Mohali, Chandigarh', '06:00')}
        >
          📍 Chandigarh (Early Morning 06:00)
        </button>
        <button
          className="example-pill-btn example-unsupported"
          onClick={() => handleQuickLocation('Nagpur, Maharashtra', '20:00')}
          title="Demonstrates graceful handling of locations outside current training coverage"
        >
          ⚠️ Test Unsupported: Nagpur, Maharashtra
        </button>
      </div>

      <div className="search-scope-disclaimer">
        <Navigation2Off size={13} />
        <span>
          <strong>Scope Notice:</strong> SafeRoute AI evaluates road safety risk for your destination and travel time. It does <em>not</em> calculate turn-by-turn routes or recommend driving navigation.
        </span>
      </div>
    </section>
  );
}

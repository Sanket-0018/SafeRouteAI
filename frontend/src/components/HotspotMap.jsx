import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Navigation2Off, Info, Crosshair } from 'lucide-react';

const CITY_CENTERS = {
  Pune: [18.5204, 73.8567],
  Mumbai: [19.076, 72.8777],
  Delhi: [28.6139, 77.209],
  Bangalore: [12.9716, 77.5946],
  Chennai: [13.0827, 80.2707],
  Hyderabad: [17.385, 78.4867],
  Kolkata: [22.5726, 88.3639],
  Chandigarh: [30.7333, 76.7794],
};

export default function HotspotMap({
  hotspots = [],
  selectedRank = null,
  onSelectHotspot,
  onMapClickLocation,
  selectedCity = '',
  selectedCoords = null,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);
  const userPinLayerRef = useRef(null);

  // Initialize map instance once
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [20.5937, 78.9629],
      zoom: 5,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | SafeRoute AI',
    }).addTo(map);

    markersLayerRef.current = L.layerGroup().addTo(map);
    userPinLayerRef.current = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;

    // Allow user to click anywhere on map to check risk for that location
    map.on('click', (e) => {
      const { lat, lng } = e.latlng;
      if (onMapClickLocation) {
        onMapClickLocation(lat, lng);
      }
    });

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update markers when hotspots or selectedRank changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();
    if (hotspots.length === 0) return;

    const latLngs = [];

    hotspots.forEach((h) => {
      const isSelected = h.rank === selectedRank;
      const probPct = (h.high_probability * 100).toFixed(1);
      const lat = h.latitude;
      const lon = h.longitude;

      if (!lat || !lon) return;
      latLngs.push([lat, lon]);

      const markerHtml = `
        <div class="custom-map-pin ${isSelected ? 'selected-pin' : ''}">
          <div class="pin-badge">${h.rank}</div>
          ${isSelected ? '<div class="pulse-ring"></div>' : ''}
        </div>
      `;

      const icon = L.divIcon({
        html: markerHtml,
        className: 'custom-leaflet-icon',
        iconSize: isSelected ? [36, 36] : [28, 28],
        iconAnchor: isSelected ? [18, 18] : [14, 14],
      });

      const marker = L.marker([lat, lon], { icon }).addTo(markersLayer);

      const areaTitle = h.area_name || `${h.city} Corridor`;

      const popupContent = `
        <div class="map-popup-card">
          <div class="popup-header">
            <span class="popup-rank">Priority #${h.rank}</span>
            <span class="popup-tier ${h.risk_tier.toLowerCase()}">${h.risk_tier} RISK</span>
          </div>
          <div class="popup-body">
            <div class="popup-location"><strong>${areaTitle}</strong></div>
            <div class="popup-window">${h.time_window}</div>
            <div class="popup-prob">
              Risk Probability: <strong>${probPct}%</strong>
            </div>
            <div class="popup-coords">${lat.toFixed(4)}°N, ${lon.toFixed(4)}°E</div>
          </div>
          <button class="popup-select-btn" id="btn-select-${h.rank}">
            Inspect Risk & Guidance →
          </button>
        </div>
      `;

      marker.bindPopup(popupContent, { minWidth: 220 });

      marker.on('click', () => {
        onSelectHotspot(h.rank);
      });
    });

    map.on('popupopen', (e) => {
      const popupNode = e.popup.getElement();
      if (!popupNode) return;
      const btn = popupNode.querySelector('.popup-select-btn');
      if (btn) {
        btn.onclick = () => {
          const rankId = Number(btn.id.replace('btn-select-', ''));
          onSelectHotspot(rankId);
        };
      }
    });

    if (selectedCity && CITY_CENTERS[selectedCity]) {
      map.flyTo(CITY_CENTERS[selectedCity], 11, { duration: 1.2 });
    } else if (latLngs.length > 0 && !selectedCoords) {
      const bounds = L.latLngBounds(latLngs);
      map.fitBounds(bounds.pad(0.15), { maxZoom: 12 });
    }
  }, [hotspots, selectedCity]);

  // Update searched location marker
  useEffect(() => {
    const map = mapInstanceRef.current;
    const userLayer = userPinLayerRef.current;
    if (!map || !userLayer) return;

    userLayer.clearLayers();

    if (selectedCoords && selectedCoords.lat && selectedCoords.lon) {
      const userIcon = L.divIcon({
        html: `
          <div class="user-search-pin">
            <div class="user-pin-inner"></div>
            <div class="user-pin-pulse"></div>
          </div>
        `,
        className: 'custom-leaflet-icon',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      L.marker([selectedCoords.lat, selectedCoords.lon], { icon: userIcon }).addTo(userLayer);
      map.flyTo([selectedCoords.lat, selectedCoords.lon], 12, { duration: 1.0 });
    }
  }, [selectedCoords]);

  return (
    <div className="map-wrapper">
      <div className="map-header-bar">
        <div className="map-title-row">
          <MapPin size={16} className="text-red" />
          <span className="map-title">Road-Safety Risk Hotspots (WHERE)</span>
          <span className="map-count-pill">{hotspots.length} Hotspots Visible</span>
        </div>
        <div className="map-notice-badge">
          <Navigation2Off size={13} />
          <span>Spatiotemporal Risk Analysis • Non-Routing System</span>
        </div>
      </div>

      <div ref={mapContainerRef} className="leaflet-map-container" />

      <div className="map-legend">
        <div className="legend-item">
          <span className="legend-dot dot-high"></span>
          <span>Evaluated High Risk Location</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot dot-selected"></span>
          <span>Selected Hotspot</span>
        </div>
        <div className="legend-item text-muted">
          <Crosshair size={12} />
          <span>Click anywhere on the map or select a pin to evaluate that area</span>
        </div>
      </div>
    </div>
  );
}

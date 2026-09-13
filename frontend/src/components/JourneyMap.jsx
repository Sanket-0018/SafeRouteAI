import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Map, Navigation } from 'lucide-react';

export default function JourneyMap({
  routeGeometry,
  hazards = [],
  selectedHazardSeq = null,
  onSelectHazard,
  originName = 'Origin',
  destinationName = 'Destination',
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const routeLayerRef = useRef(null);
  const markersLayerRef = useRef(null);

  // 1. Initialize map instance
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [19.8, 76.5],
      zoom: 7,
      zoomControl: true,
      attributionControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | SafeRoute AI',
    }).addTo(map);

    routeLayerRef.current = L.layerGroup().addTo(map);
    markersLayerRef.current = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Render route polyline & markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    const routeLayer = routeLayerRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !routeLayer || !markersLayer) return;

    routeLayer.clearLayers();
    markersLayer.clearLayers();

    if (!routeGeometry?.coordinates || routeGeometry.coordinates.length < 2) return;

    // Convert GeoJSON [lon, lat] -> Leaflet [lat, lon]
    const latLngs = routeGeometry.coordinates.map((c) => [c[1], c[0]]);

    // Route casing
    L.polyline(latLngs, {
      color: '#1e3a8a',
      weight: 6,
      opacity: 0.35,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(routeLayer);

    // Primary route line (Blue reserved exclusively for route)
    L.polyline(latLngs, {
      color: '#2563eb',
      weight: 4,
      opacity: 0.95,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(routeLayer);

    // Origin Marker (Green "A")
    const originIcon = L.divIcon({
      html: `
        <div class="map-endpoint-pin origin-pin" title="Origin: ${originName}">
          <span>A</span>
        </div>
      `,
      className: 'custom-leaflet-marker',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
    L.marker(latLngs[0], { icon: originIcon })
      .bindPopup(`<strong>Origin:</strong> ${originName}`)
      .addTo(markersLayer);

    // Destination Marker (Dark "B")
    const destIcon = L.divIcon({
      html: `
        <div class="map-endpoint-pin dest-pin" title="Destination: ${destinationName}">
          <span>B</span>
        </div>
      `,
      className: 'custom-leaflet-marker',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
    L.marker(latLngs[latLngs.length - 1], { icon: destIcon })
      .bindPopup(`<strong>Destination:</strong> ${destinationName}`)
      .addTo(markersLayer);

    // Hazard Markers (🔴 ML Circle vs 🟠 Official Diamond)
    hazards.forEach((h) => {
      const isSelected = h.sequence === selectedHazardSeq;
      const isML = h.hazard_type === 'ML_PREDICTED_HOTSPOT';

      let markerHtml = '';
      if (isML) {
        // Red Circle Marker
        markerHtml = `
          <div class="map-pin-ml-circle ${isSelected ? 'pin-active' : ''}">
            <span class="pin-text">${h.sequence}</span>
          </div>
        `;
      } else {
        // Orange Diamond Marker (Upright number over rotated diamond background)
        markerHtml = `
          <div class="map-pin-official-diamond ${isSelected ? 'pin-active' : ''}">
            <div class="diamond-shape"></div>
            <span class="pin-text">${h.sequence}</span>
          </div>
        `;
      }

      const icon = L.divIcon({
        html: markerHtml,
        className: 'custom-leaflet-marker',
        iconSize: isSelected ? [34, 34] : [26, 26],
        iconAnchor: isSelected ? [17, 17] : [13, 13],
      });

      const typeBadge = isML
        ? `<span class="popup-tag ml-tag">🔴 ML PREDICTED HOTSPOT</span>`
        : `<span class="popup-tag official-tag">🟠 OFFICIAL GOVERNMENT BLACKSPOT</span>`;

      const metricLine = isML && h.risk_probability
        ? `<div class="popup-metric">Model Risk Probability: <strong>${(h.risk_probability * 100).toFixed(1)}%</strong></div>`
        : h.official_provenance?.total_fatalities_3yr
        ? `<div class="popup-metric">3-Yr Record: <strong>${h.official_provenance.total_fatalities_3yr} Fatalities</strong> (${h.official_provenance.fatal_crashes_3yr || 0} fatal crashes)</div>`
        : '';

      const popupHtml = `
        <div class="journey-map-popup-card">
          <div class="popup-seq-row">
            <span class="popup-seq-label">Milestone #${h.sequence}</span>
            <span class="popup-dist">${h.distance_from_origin_km} km along route</span>
          </div>
          <div class="popup-type-wrap">${typeBadge}</div>
          <div class="popup-title">${h.location_name}</div>
          <div class="popup-eta">Expected Arrival: <strong>${h.expected_arrival_time}</strong> (${h.expected_arrival_window})</div>
          ${metricLine}
          <div class="popup-reason">${h.reason}</div>
          <button class="btn-popup-focus" id="btn-focus-hazard-${h.sequence}">
            View Details in Timeline ↓
          </button>
        </div>
      `;

      const marker = L.marker([h.latitude, h.longitude], { icon }).addTo(markersLayer);
      marker.bindPopup(popupHtml, { minWidth: 250 });
      marker.on('click', () => {
        if (onSelectHazard) onSelectHazard(h.sequence);
      });
    });

    // Wire popup button clicks
    map.on('popupopen', (e) => {
      const btn = e.popup.getElement()?.querySelector('.btn-popup-focus');
      if (btn) {
        btn.onclick = () => {
          const seq = Number(btn.id.replace('btn-focus-hazard-', ''));
          if (onSelectHazard) onSelectHazard(seq);
        };
      }
    });

    // Fit route bounds
    map.fitBounds(L.latLngBounds(latLngs).pad(0.1));
  }, [routeGeometry, hazards, selectedHazardSeq]);

  // 3. Pan to selected hazard when selected in timeline
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !selectedHazardSeq || !hazards?.length) return;
    const h = hazards.find((x) => x.sequence === selectedHazardSeq);
    if (h) {
      map.panTo([h.latitude, h.longitude], { animate: true, duration: 0.7 });
    }
  }, [selectedHazardSeq, hazards]);

  return (
    <div className="workspace-map-panel">
      {/* Floating Modern Map Overlay Bar */}
      <div className="map-floating-overlay">
        <div className="map-overlay-badge">
          <Map size={13} className="text-muted" />
          <span className="overlay-title">CORRIDOR HAZARDS</span>
          {routeGeometry?.distance_km && (
            <span className="corridor-dist-pill">{routeGeometry.distance_km} km</span>
          )}
        </div>

        {/* Clear Explicit Floating Map Legend */}
        <div className="map-floating-legend">
          <div className="legend-entry">
            <span className="legend-circle-ml">●</span>
            <span className="legend-text">ML Hotspot</span>
          </div>
          <div className="legend-entry">
            <span className="legend-diamond-official">◆</span>
            <span className="legend-text">Official Blackspot</span>
          </div>
          <div className="legend-entry">
            <span className="legend-line-route">―</span>
            <span className="legend-text">Planned Route</span>
          </div>
        </div>
      </div>

      <div ref={mapContainerRef} className="leaflet-journey-map-canvas" />
    </div>
  );
}

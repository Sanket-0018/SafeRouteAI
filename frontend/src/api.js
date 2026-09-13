/**
 * SafeRoute AI — API Client Service
 * Communicates strictly with the FastAPI backend over HTTP.
 * Base URL defaults to http://localhost:8000, configurable via VITE_API_BASE_URL.
 */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL !== undefined
    ? import.meta.env.VITE_API_BASE_URL
    : (import.meta.env.DEV ? 'http://localhost:8000' : '');

class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Accept': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || JSON.stringify(errorJson);
      } catch {
        // use statusText fallback
      }
      throw new ApiError(`API Error (${response.status}): ${errorDetail}`, response.status, errorDetail);
    }

    return await response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Network error connecting to ${url}: ${err.message}`, 0, err.message);
  }
}

export async function fetchHealth() {
  return request('/health');
}

export async function fetchStats() {
  return request('/stats');
}

export async function fetchCities() {
  return request('/cities');
}

export async function fetchHotspots({ city = null, risk_tier = null, limit = 50 } = {}) {
  const params = new URLSearchParams();
  if (city) params.append('city', city);
  if (risk_tier) params.append('risk_tier', risk_tier);
  if (limit) params.append('limit', limit.toString());

  const queryString = params.toString();
  return request(`/hotspots${queryString ? `?${queryString}` : ''}`);
}

export async function fetchHotspotDetail(rank) {
  if (typeof rank !== 'number' || rank < 1) {
    throw new Error(`Invalid rank: ${rank}`);
  }
  return request(`/hotspots/${rank}`);
}

export async function checkLocationRisk({
  latitude,
  longitude,
  location_name = null,
  travel_time = null,
  travel_date = null,
}) {
  return request('/check-risk', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      latitude,
      longitude,
      location_name,
      travel_time,
      travel_date,
    }),
  });
}

export async function analyzeJourney({
  origin,
  destination,
  departure_datetime = null,
  origin_lat = null,
  origin_lon = null,
  dest_lat = null,
  dest_lon = null,
}) {
  return request('/journey/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      origin,
      destination,
      departure_datetime,
      origin_lat,
      origin_lon,
      dest_lat,
      dest_lon,
    }),
  });
}

export async function fetchPlaceSuggestions(query, limit = 8) {
  if (!query || query.trim().length < 2) {
    return { query: query || '', count: 0, results: [] };
  }
  const params = new URLSearchParams({
    q: query.trim(),
    limit: limit.toString(),
  });
  return request(`/places/autocomplete?${params.toString()}`);
}

export async function fetchJourneyAiBrief(evidence) {
  return request('/api/journey/ai-brief', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(evidence),
  });
}

export { API_BASE_URL };

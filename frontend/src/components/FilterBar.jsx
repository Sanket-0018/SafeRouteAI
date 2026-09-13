import React from 'react';
import { RotateCcw } from 'lucide-react';

export default function FilterBar({
  cities,
  selectedCity,
  onChangeCity,
  selectedRiskTier,
  onChangeRiskTier,
  selectedLimit,
  onChangeLimit,
  onResetFilters,
  totalResults,
  filteredCount,
  isLoading,
}) {
  const hasActiveFilters =
    selectedCity !== '' || selectedRiskTier !== '' || selectedLimit !== 50;

  return (
    <section className="filter-bar">
      <select
        value={selectedCity}
        onChange={(e) => onChangeCity(e.target.value)}
        disabled={isLoading}
      >
        <option value="">All cities</option>
        {cities.map((city) => (
          <option key={city} value={city}>{city}</option>
        ))}
      </select>

      <select
        value={selectedRiskTier}
        onChange={(e) => onChangeRiskTier(e.target.value)}
        disabled={isLoading}
      >
        <option value="">All risk tiers</option>
        <option value="HIGH">HIGH</option>
        <option value="MEDIUM">MEDIUM</option>
        <option value="LOW">LOW</option>
      </select>

      <select
        value={selectedLimit}
        onChange={(e) => onChangeLimit(Number(e.target.value))}
        disabled={isLoading}
      >
        <option value={10}>Top 10</option>
        <option value={20}>Top 20</option>
        <option value={50}>Top 50</option>
        <option value={100}>All 100</option>
      </select>

      {hasActiveFilters && (
        <button className="btn-reset-filters" onClick={onResetFilters}>
          <RotateCcw size={12} />
          <span>Reset</span>
        </button>
      )}

      <div className="filter-results-count">
        {filteredCount} of {totalResults} results
      </div>
    </section>
  );
}

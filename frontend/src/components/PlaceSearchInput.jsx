import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MapPin,
  Navigation,
  Search,
  X,
  Loader2,
  Plane,
  Train,
  Building2,
  Compass,
  CheckCircle2,
} from 'lucide-react';
import { fetchPlaceSuggestions } from '../api';

export default function PlaceSearchInput({
  label,
  icon: Icon = MapPin,
  iconClass = 'text-blue',
  placeholder = 'Search city, airport, station, or town...',
  initialText = '',
  onSelectPlace,
  required = false,
}) {
  const [inputText, setInputText] = useState(initialText);
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const containerRef = useRef(null);
  const inputRef = useRef(null);
  const debounceTimerRef = useRef(null);

  // Sync initialText if parent updates it
  useEffect(() => {
    if (initialText && initialText !== inputText) {
      setInputText(initialText);
    }
  }, [initialText]);

  // Click outside listener to close dropdown
  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced API search
  const performSearch = useCallback((query) => {
    if (!query || query.trim().length < 2) {
      setSuggestions([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    fetchPlaceSuggestions(query, 8)
      .then((data) => {
        setSuggestions(data.results || []);
        setIsOpen(true);
        setHighlightedIndex(-1);
      })
      .catch((err) => {
        console.error('Geocoding search error:', err);
        setSuggestions([]);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const handleInputChange = (e) => {
    const text = e.target.value;
    setInputText(text);
    setSelectedPlace(null);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (text.trim().length >= 2) {
      debounceTimerRef.current = setTimeout(() => {
        performSearch(text);
      }, 200);
    } else {
      setSuggestions([]);
      setIsOpen(false);
    }
  };

  const handleSelectSuggestion = (place) => {
    setInputText(place.display_name);
    setSelectedPlace(place);
    setIsOpen(false);
    setSuggestions([]);
    if (onSelectPlace) {
      onSelectPlace(place);
    }
  };

  const handleClear = () => {
    setInputText('');
    setSelectedPlace(null);
    setSuggestions([]);
    setIsOpen(false);
    if (inputRef.current) {
      inputRef.current.focus();
    }
    if (onSelectPlace) {
      onSelectPlace(null);
    }
  };

  const handleKeyDown = (e) => {
    if (!isOpen || suggestions.length === 0) {
      if (e.key === 'ArrowDown' && suggestions.length > 0) {
        setIsOpen(true);
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
        handleSelectSuggestion(suggestions[highlightedIndex]);
      } else if (suggestions.length > 0) {
        handleSelectSuggestion(suggestions[0]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const getPlaceIcon = (type) => {
    switch (type) {
      case 'airport':
        return <Plane size={14} className="text-purple" />;
      case 'railway_station':
        return <Train size={14} className="text-amber" />;
      case 'city':
        return <Building2 size={14} className="text-blue" />;
      default:
        return <MapPin size={14} className="text-emerald" />;
    }
  };

  return (
    <div
      className={`place-search-container ${isOpen ? 'dropdown-open' : ''}`}
      ref={containerRef}
    >
      {label && (
        <label className="place-search-label">
          <Icon size={14} className={iconClass} />
          <span>{label}</span>
        </label>
      )}

      <div className="place-input-wrapper">
        <input
          ref={inputRef}
          type="text"
          className="place-text-input"
          placeholder={placeholder}
          value={inputText}
          onChange={handleInputChange}
          onFocus={() => {
            if (suggestions.length > 0) setIsOpen(true);
            else if (inputText.trim().length >= 2) performSearch(inputText);
          }}
          onKeyDown={handleKeyDown}
          required={required}
          autoComplete="off"
        />

        <div className="place-input-actions">
          {isLoading && <Loader2 size={14} className="spin text-muted" />}
          {!isLoading && inputText && (
            <button
              type="button"
              className="btn-clear-place"
              onClick={handleClear}
              title="Clear place"
            >
              <X size={13} />
            </button>
          )}
        </div>

        {/* Autocomplete Dropdown - Positioned relative to place-input-wrapper */}
        {isOpen && suggestions.length > 0 && (
          <ul className="place-suggestions-dropdown" role="listbox">
            {suggestions.map((place, idx) => {
              const isHighlighted = idx === highlightedIndex;
              return (
                <li
                  key={idx}
                  className={`place-suggestion-item ${isHighlighted ? 'highlighted' : ''}`}
                  onClick={() => handleSelectSuggestion(place)}
                  onMouseEnter={() => setHighlightedIndex(idx)}
                  role="option"
                  aria-selected={isHighlighted}
                >
                  <div className="place-item-icon">
                    {getPlaceIcon(place.place_type)}
                  </div>
                  <div className="place-item-content">
                    <div className="place-name-primary">{place.display_name}</div>
                    <div className="place-name-sub">
                      {place.city && <span>{place.city}</span>}
                      {place.state && <span> · {place.state}</span>}
                      <span className="place-type-tag">{place.place_type.replace('_', ' ')}</span>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}

        {/* No Results Floating Dropdown */}
        {isOpen && !isLoading && suggestions.length === 0 && inputText.trim().length >= 2 && (
          <div className="place-no-results-dropdown">
            <span>No matching locations found for "{inputText}".</span>
          </div>
        )}
      </div>
    </div>
  );
}

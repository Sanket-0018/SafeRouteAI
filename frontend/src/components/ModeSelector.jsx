import React from 'react';
import { Milestone, Database } from 'lucide-react';

export default function ModeSelector({ currentMode, onSelectMode }) {
  return (
    <div className="mode-selector-wrapper">
      <div className="mode-tabs-container">
        <button
          className={`mode-tab-btn ${currentMode === 'journey' ? 'active' : ''}`}
          onClick={() => onSelectMode('journey')}
        >
          <Milestone size={15} />
          <span className="mode-tab-title">Journey Safety Assessment</span>
          <span className="mode-pill-primary">Primary</span>
        </button>

        <button
          className={`mode-tab-btn ${currentMode === 'hotspot' ? 'active' : ''}`}
          onClick={() => onSelectMode('hotspot')}
        >
          <Database size={15} />
          <span className="mode-tab-title">Explore Historical Risk & Hotspots</span>
        </button>
      </div>
    </div>
  );
}

import React from 'react';
import { ShieldAlert, Sun, Moon, ArrowLeft, Info } from 'lucide-react';

export default function Header({
  view = 'planner',
  onBackToPlanner,
  onOpenResponsibleAI,
  apiStatus = 'ok',
  theme = 'light',
  onToggleTheme,
}) {
  const isOnline = apiStatus === 'ok';
  const isOffline = apiStatus === 'offline';
  const isChecking = apiStatus === 'checking';

  return (
    <header className="app-header">
      <div className="header-container">
        {/* Brand Lockup */}
        <div
          className="header-brand-group"
          onClick={onBackToPlanner}
          role="button"
          tabIndex={0}
          style={{ cursor: view === 'results' ? 'pointer' : 'default' }}
          title={view === 'results' ? 'Back to Journey Planner' : 'SafeRoute AI'}
        >
          <div className="brand-badge-icon">
            <ShieldAlert size={15} className="text-hazard-ml" />
          </div>
          <div className="brand-text-stack">
            <span className="brand-title">SAFE ROUTE AI</span>
            <span className="brand-subtitle">JOURNEY RISK INTELLIGENCE</span>
          </div>
        </div>

        {/* Center / Context Action */}
        {view === 'results' && onBackToPlanner && (
          <button
            type="button"
            className="btn-back-planner"
            onClick={onBackToPlanner}
            aria-label="Plan another journey"
          >
            <ArrowLeft size={13} />
            <span>Plan another journey</span>
          </button>
        )}

        {/* Controls */}
        <div className="header-controls">
          <div
            className={`status-pill ${
              isOnline ? 'status-online' : isOffline ? 'status-offline' : 'status-checking'
            }`}
            title={
              isOnline
                ? 'FastAPI & ML backend connected'
                : isChecking
                ? 'Checking backend connection...'
                : 'Backend connection offline'
            }
          >
            <span className="status-dot" />
            <span className="status-text">
              {isOnline ? 'Online' : isChecking ? 'Checking...' : 'Offline'}
            </span>
          </div>

          <button
            type="button"
            className="btn-header-rai"
            onClick={onOpenResponsibleAI}
            title="Responsible AI & Risk Methodology Disclosures"
            aria-label="How SafeRoute works and about risk"
          >
            <Info size={13} />
            <span className="rai-header-label">How SafeRoute works · About risk</span>
          </button>

          <button
            type="button"
            className="btn-header-control"
            onClick={onToggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
          </button>
        </div>
      </div>
    </header>
  );
}

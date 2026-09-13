import React, { useState, useEffect, useCallback, useRef } from 'react';
import Header from './components/Header';
import HeroSection from './components/HeroSection';
import JourneySearchForm from './components/JourneySearchForm';
import JourneySummaryBanner from './components/JourneySummaryBanner';
import AiJourneyBrief from './components/AiJourneyBrief';
import JourneyMap from './components/JourneyMap';
import JourneyTimeline from './components/JourneyTimeline';
import ResponsibleAINotice from './components/ResponsibleAINotice';
import {
  fetchHealth,
  analyzeJourney,
  API_BASE_URL,
} from './api';
import { AlertTriangle, ArrowLeft } from 'lucide-react';
import './App.css';

export default function App() {
  // ── THEME (Light mode strictly default) ──────────────────────────────────
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('saferoute-theme-v3');
    return saved === 'dark' ? 'dark' : 'light';
  });

  // Ambient cursor-following atmospheric light ref
  const ambientLightRef = useRef(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('saferoute-theme-v3', theme);
  }, [theme]);

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  // ── VIEW STATE: 'planner' | 'results' ──────────────────────────────────────
  const [view, setView] = useState('planner');
  const [isResponsibleAIOpen, setIsResponsibleAIOpen] = useState(false);

  // ── GLOBAL API STATE ───────────────────────────────────────────────────────
  const [apiStatus, setApiStatus] = useState('checking');
  const [globalError, setGlobalError] = useState(null);

  // ── JOURNEY STATE ──────────────────────────────────────────────────────────
  const [journeyOrigin, setJourneyOrigin] = useState('Pune, Maharashtra');
  const [journeyDest, setJourneyDest] = useState('Nagpur, Maharashtra');
  const [journeyDepDateTime, setJourneyDepDateTime] = useState('2026-08-30T20:00:00');
  const [journeyAssessment, setJourneyAssessment] = useState(null);
  const [isAnalyzingJourney, setIsAnalyzingJourney] = useState(false);
  const [journeyError, setJourneyError] = useState(null);
  const [selectedHazardSeq, setSelectedHazardSeq] = useState(null);
  const [mobileView, setMobileView] = useState('map');

  // Check health on mount
  const checkHealth = useCallback(async () => {
    try {
      const health = await fetchHealth();
      setApiStatus(health.status === 'ok' ? 'ok' : 'degraded');
      setGlobalError(null);
    } catch (err) {
      setApiStatus('offline');
      setGlobalError(
        `Unable to connect to SafeRoute AI backend at ${API_BASE_URL}. Ensure uvicorn is running.`
      );
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  // ── JOURNEY ANALYSIS ───────────────────────────────────────────────────────
  const handleAnalyzeJourney = useCallback(
    async ({
      origin,
      destination,
      departure_datetime,
      origin_lat = null,
      origin_lon = null,
      dest_lat = null,
      dest_lon = null,
    }) => {
      setIsAnalyzingJourney(true);
      setJourneyError(null);
      setJourneyOrigin(origin);
      setJourneyDest(destination);
      setJourneyDepDateTime(departure_datetime);
      setSelectedHazardSeq(null);
      setView('results'); // Transition to results view

      try {
        const assessment = await analyzeJourney({
          origin,
          destination,
          departure_datetime,
          origin_lat,
          origin_lon,
          dest_lat,
          dest_lon,
        });
        setJourneyAssessment(assessment);
      } catch (err) {
        console.error('Journey analysis error:', err);
        setJourneyError(err.message || 'Unable to complete journey safety assessment.');
      } finally {
        setIsAnalyzingJourney(false);
      }
    },
    []
  );

  const handleBackToPlanner = () => {
    setView('planner');
  };

  const handleSelectHazardFromMap = (seq) => {
    setSelectedHazardSeq(seq);
    const cardNode = document.getElementById(`hazard-card-${seq}`);
    if (cardNode) {
      cardNode.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Ambient cursor-following atmospheric light (Desktop only, respects reduced motion)
  useEffect(() => {
    if (view !== 'planner') return;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isFinePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    if (prefersReducedMotion || !isFinePointer) return;

    let targetX = window.innerWidth / 2;
    let targetY = 300;
    let currentX = targetX;
    let currentY = targetY;
    let animId = null;
    let isVisible = false;

    const handleMouseMove = (e) => {
      targetX = e.clientX;
      targetY = e.clientY;
      if (!isVisible && ambientLightRef.current) {
        ambientLightRef.current.style.opacity = '1';
        isVisible = true;
      }
    };

    const handleMouseLeave = () => {
      if (ambientLightRef.current) {
        ambientLightRef.current.style.opacity = '0';
        isVisible = false;
      }
    };

    const animate = () => {
      currentX += (targetX - currentX) * 0.055;
      currentY += (targetY - currentY) * 0.055;

      if (ambientLightRef.current) {
        ambientLightRef.current.style.transform = `translate3d(${(currentX - 275).toFixed(1)}px, ${(currentY - 275).toFixed(1)}px, 0)`;
      }
      animId = requestAnimationFrame(animate);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);
    animId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      if (animId) cancelAnimationFrame(animId);
    };
  }, [view]);

  // ── RENDER ─────────────────────────────────────────────────────────────────
  return (
    <div className="app-layout">
      {view === 'planner' && (
        <div ref={ambientLightRef} className="ambient-cursor-glow" aria-hidden="true" />
      )}

      <Header
        view={view}
        onBackToPlanner={handleBackToPlanner}
        onOpenResponsibleAI={() => setIsResponsibleAIOpen(true)}
        apiStatus={apiStatus}
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />

      {globalError && (
        <div className="global-error-banner" role="alert">
          <AlertTriangle size={15} style={{ flexShrink: 0 }} />
          <div className="error-text-content">
            <strong>Connection notice:</strong> {globalError}
          </div>
          <button className="btn-retry" onClick={checkHealth}>
            Retry
          </button>
        </div>
      )}

      {view === 'planner' ? (
        <main className="landing-view-main">
          <HeroSection />

          <JourneySearchForm
            onAnalyzeJourney={handleAnalyzeJourney}
            initialOrigin={journeyOrigin}
            initialDestination={journeyDest}
            initialDeparture={journeyDepDateTime}
            isLoading={isAnalyzingJourney}
          />

          <footer className="planner-footer">
            <div className="planner-footer-inner">
              <span className="footer-brand">
                SafeRoute AI &middot; Indian Transportation Safety Intelligence
              </span>
              <div className="planner-footer-links">
                <button
                  type="button"
                  className="btn-text-link"
                  onClick={() => setIsResponsibleAIOpen(true)}
                >
                  How SafeRoute works · About risk
                </button>
                <span className="footer-sep">&middot;</span>
                <span className="footer-sdg">UN SDG 11 &amp; SDG 3</span>
              </div>
            </div>
          </footer>
        </main>
      ) : (
        <main className="results-view-main">
          {journeyError && (
            <div className="journey-error-banner" role="alert">
              <AlertTriangle size={18} className="journey-error-icon" />
              <div className="journey-error-content">
                <strong>Safety Assessment Error</strong>
                <p>{journeyError}</p>
              </div>
              <button
                type="button"
                className="btn-back-link"
                onClick={handleBackToPlanner}
              >
                <ArrowLeft size={13} />
                <span>Return to planner</span>
              </button>
            </div>
          )}

          {isAnalyzingJourney && (
            <div className="journey-loading-state">
              <div className="spinner-ring" />
              <h3 className="loading-title">Assessing Journey Safety</h3>
              <p className="loading-desc">
                Querying OSRM road geometry, scanning trained LightGBM spatial risk models,
                and cross-referencing verified Maharashtra Highway Police blackspots&hellip;
              </p>
            </div>
          )}

          {!isAnalyzingJourney && journeyAssessment && (
            <div className="journey-assessment-container">
              <JourneySummaryBanner
                assessment={journeyAssessment}
                onBackToPlanner={handleBackToPlanner}
              />

              <AiJourneyBrief assessment={journeyAssessment} />

              {/* Mobile View Toggle */}
              <div className="mobile-view-tabs" role="tablist" aria-label="Mobile View Toggle">
                <button
                  type="button"
                  className={`btn-mobile-tab ${mobileView === 'map' ? 'active' : ''}`}
                  onClick={() => setMobileView('map')}
                >
                  Corridor Map
                </button>
                <button
                  type="button"
                  className={`btn-mobile-tab ${mobileView === 'timeline' ? 'active' : ''}`}
                  onClick={() => setMobileView('timeline')}
                >
                  Hazards ({journeyAssessment.hazards?.length || 0})
                </button>
              </div>

              <div className={`journey-visual-grid mobile-view-${mobileView}`}>
                <div className="journey-map-column">
                  <JourneyMap
                    routeGeometry={journeyAssessment.route_geometry}
                    hazards={journeyAssessment.hazards}
                    selectedHazardSeq={selectedHazardSeq}
                    onSelectHazard={handleSelectHazardFromMap}
                    originName={journeyAssessment.origin}
                    destinationName={journeyAssessment.destination}
                  />
                </div>
                <div className="journey-timeline-column">
                  <JourneyTimeline
                    hazards={journeyAssessment.hazards}
                    selectedHazardSeq={selectedHazardSeq}
                    onSelectHazard={setSelectedHazardSeq}
                  />
                </div>
              </div>
            </div>
          )}
        </main>
      )}

      {/* Accessible Responsible AI modal */}
      <ResponsibleAINotice
        isOpen={isResponsibleAIOpen}
        onClose={() => setIsResponsibleAIOpen(false)}
      />
    </div>
  );
}

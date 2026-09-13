import React, { useEffect } from 'react';
import { X, ShieldAlert, BookOpen } from 'lucide-react';

export default function ResponsibleAINotice({ isOpen, onClose }) {
  // Handle ESC key to close modal
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="rai-modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="rai-modal-title"
    >
      <div
        className="rai-modal-container"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="rai-modal-header">
          <div className="rai-modal-title-group">
            <div className="rai-modal-icon-badge">
              <ShieldAlert size={16} />
            </div>
            <div>
              <h2 id="rai-modal-title" className="rai-modal-title">
                Responsible AI & Methodology Principles
              </h2>
              <p className="rai-modal-subtitle">
                Safety intelligence disclosures, analytical scope, and evidence standards
              </p>
            </div>
          </div>
          <button
            type="button"
            className="btn-modal-close"
            onClick={onClose}
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>

        <div className="rai-modal-body">
          <div className="rai-principles-grid">
            <div className="rai-card">
              <div className="rai-card-header">
                <span className="rai-badge">01</span>
                <h4>Probabilistic, Not Predictive</h4>
              </div>
              <p>
                HIGH risk indicates elevated historical accident density at this location and time
                window — not a deterministic prediction that a crash will occur. Never interpret risk
                scores as certainties.
              </p>
            </div>

            <div className="rai-card">
              <div className="rai-card-header">
                <span className="rai-badge">02</span>
                <h4>Correlation vs. Mechanical Causation</h4>
              </div>
              <p>
                SHAP feature contributions describe how the LightGBM machine learning model weighted
                inputs to reach a probability. They represent statistical correlation within the training
                corpus, not direct physical causality.
              </p>
            </div>

            <div className="rai-card">
              <div className="rai-card-header">
                <span className="rai-badge">03</span>
                <h4>Strict Separation of Evidence</h4>
              </div>
              <p>
                Machine learning hotspots and Official Government Blackspots originate from different
                empirical pipelines. Official blackspots represent historical police-verified high-fatality
                stretches and are never modified with synthetic model metrics.
              </p>
            </div>

            <div className="rai-card">
              <div className="rai-card-header">
                <span className="rai-badge">04</span>
                <h4>Road Context ≠ Direct Causation</h4>
              </div>
              <p>
                OpenStreetMap attributes (speed limits, lane counts, lighting, surface type) characterize
                the physical road environment along the corridor. Physical traits do not imply that road
                geometry itself caused prior collisions.
              </p>
            </div>

            <div className="rai-card">
              <div className="rai-card-header">
                <span className="rai-badge">05</span>
                <h4>Advisory Guidance Scope</h4>
              </div>
              <p>
                Safety countermeasures are retrieved from verified Ministry of Road Transport and Highways
                (MoRTH), Indian Road Congress (IRC), and WHO publications. They provide advisory guidance and do
                not replace traffic authority mandates or civil engineering surveys.
              </p>
            </div>

            <div className="rai-card">
              <div className="rai-card-header">
                <span className="rai-badge">06</span>
                <h4>Zero-Hazard Disclosure & Non-Navigation</h4>
              </div>
              <p>
                The absence of flagged hazards does not imply a road is risk-free. SafeRoute AI is an advisory
                safety assessment tool — it is strictly not a turn-by-turn routing engine or navigation system.
              </p>
            </div>
          </div>

          <div className="rai-provenance-box">
            <div className="rai-provenance-header">
              <BookOpen size={14} />
              <span>Data Provenance & SDG Alignment</span>
            </div>
            <p>
              SafeRoute AI is built for <strong>SDG 11 (Sustainable Cities & Communities)</strong> and{' '}
              <strong>SDG 3 (Good Health & Well-being)</strong>. Production data uses verified accident registries
              with zero synthetic accident generation. Map data &copy; OpenStreetMap contributors under ODbL;
              official blackspot registry via MoRTH / Maharashtra Highway Police.
            </p>
          </div>
        </div>

        <div className="rai-modal-footer">
          <span className="rai-footer-note">
            SafeRoute AI &middot; Indian Road Safety Intelligence System
          </span>
          <button type="button" className="btn-modal-dismiss" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

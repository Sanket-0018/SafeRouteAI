import React from 'react';
import { BarChart3, HelpCircle, AlertCircle } from 'lucide-react';

export default function ShapFactorsView({ factors = [] }) {
  if (!factors || factors.length === 0) {
    return (
      <div className="factors-empty">
        <p>No SHAP contributing factor data available for this prediction.</p>
      </div>
    );
  }

  // Calculate max contribution for relative bar scaling
  const maxContrib = Math.max(...factors.map((f) => Math.abs(f.contribution)), 0.1);

  return (
    <div className="shap-factors-section">
      <div className="section-title-row">
        <div className="title-left">
          <BarChart3 size={18} className="text-blue" />
          <h3 className="section-title">Model Contributing Factors (SHAP Attribution)</h3>
        </div>
        <span className="factor-count-pill">{factors.length} Key Signals</span>
      </div>

      <p className="factor-subtext">
        These historical features contributed most strongly to the model's <strong>HIGH</strong> risk prediction for this location and time shift.
      </p>

      <div className="factors-list">
        {factors.map((f, i) => {
          const isPositive = f.contribution >= 0;
          const barWidth = Math.min(100, Math.max(8, (Math.abs(f.contribution) / maxContrib) * 100));

          return (
            <div key={i} className="factor-item">
              <div className="factor-header">
                <div className="factor-name-row">
                  <span className="factor-rank">#{i + 1}</span>
                  <span className="factor-name">{f.feature}</span>
                </div>
                <div className="factor-value-pill">
                  <span className="observed-label">Observed: </span>
                  <strong>{typeof f.value === 'number' ? f.value.toFixed(2) : f.value}</strong>
                </div>
              </div>

              <div className="factor-bar-wrapper">
                <div className="factor-bar-track">
                  <div
                    className={`factor-bar-fill ${isPositive ? 'positive' : 'negative'}`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
                <span className={`factor-impact-badge ${isPositive ? 'text-red' : 'text-green'}`}>
                  {isPositive ? `+${f.contribution.toFixed(3)}` : f.contribution.toFixed(3)} SHAP
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="shap-disclaimer-box">
        <AlertCircle size={14} className="text-amber" />
        <span>
          <strong>Methodological Notice:</strong> SHAP values indicate statistical predictive contribution to the model's output score. They reflect feature sensitivity in historical patterns, <em>not verified physical causation</em>.
        </span>
      </div>
    </div>
  );
}

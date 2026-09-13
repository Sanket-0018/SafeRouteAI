import React, { useState, useEffect } from 'react';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { fetchJourneyAiBrief } from '../api';
import ibmBobIcon from '../assets/ibm-bob-icon.png';

/**
 * Safely parses and normalizes IBM Bob brief output into structured heading and bullet items.
 * Strictly avoids dangerouslySetInnerHTML so no HTML or scripts can ever execute.
 * Strips raw markdown syntax: ##, **, --, standalone dashes, blank lines.
 */
function parseBobBrief(rawText) {
  if (!rawText || typeof rawText !== 'string') {
    return { heading: null, bullets: [] };
  }

  const lines = rawText.split('\n');
  let heading = null;
  const bullets = [];

  for (let rawLine of lines) {
    const line = rawLine.trim();
    if (!line) continue;

    // 1. Ignore markdown divider lines / horizontal rules: ---, --, ___, ***
    if (/^[-*_]{2,}\s*$/.test(line)) {
      continue;
    }

    // 2. Detect & clean heading lines e.g. ## 🛡️ SafeRoute AI Journey Safety Brief
    const isMarkdownHeading = /^#{1,6}\s+/.test(line);
    const cleanLine = line.replace(/^#{1,6}\s+/, '').trim();

    // Check if line is the document title
    if (
      isMarkdownHeading ||
      cleanLine.startsWith('🛡️') ||
      cleanLine.includes('SafeRoute AI Journey Safety Brief') ||
      cleanLine.includes('Journey Safety Brief')
    ) {
      if (!heading) {
        // Strip markdown formatting symbols from heading
        heading = cleanLine.replace(/[*_`#\\]/g, '').trim();
        continue;
      }
    }

    // 3. Normalize bullet points: strip leading bullet characters (•, -, *, 1., etc.)
    const bulletMatch = cleanLine.match(/^([•\-\*]|\d+\.)\s*(.*)$/);
    const itemText = (bulletMatch ? bulletMatch[2] : cleanLine).trim();

    // Skip empty lines or stray divider artifacts
    if (!itemText || /^[-*_]{2,}\s*$/.test(itemText)) {
      continue;
    }

    bullets.push(itemText);
  }

  return { heading, bullets };
}

/**
 * Safely parses inline markdown (such as **bold** and *italic*) into React elements.
 * Prevents raw Markdown asterisks from displaying in the UI while retaining clean emphasis.
 */
function renderInlineFormatted(text) {
  if (!text) return null;

  const parts = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let lastIndex = 0;
  let match;
  let hasMarkdownEmphasis = false;

  while ((match = regex.exec(text)) !== null) {
    hasMarkdownEmphasis = true;
    if (match.index > lastIndex) {
      const plain = text.substring(lastIndex, match.index).replace(/[*_`#\\]/g, '');
      if (plain) parts.push({ type: 'text', value: plain });
    }

    const chunk = match[0];
    if (chunk.startsWith('**') && chunk.endsWith('**')) {
      const content = chunk.slice(2, -2).replace(/[*_`#\\]/g, '').trim();
      if (content) parts.push({ type: 'strong', value: content });
    } else if (chunk.startsWith('*') && chunk.endsWith('*')) {
      const content = chunk.slice(1, -1).replace(/[*_`#\\]/g, '').trim();
      if (content) parts.push({ type: 'em', value: content });
    }

    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    const trailing = text.substring(lastIndex).replace(/[*_`#\\]/g, '');
    if (trailing) parts.push({ type: 'text', value: trailing });
  }

  // If there was no markdown bolding, but line has a key-value prefix like "Route: ..." or "Departure: ..."
  if (!hasMarkdownEmphasis) {
    const kvMatch = text.match(/^([A-Za-z0-9\s—–\-_/]+:)\s*(.*)$/);
    if (kvMatch && kvMatch[1].length <= 35) {
      return (
        <>
          <strong className="ai-brief-strong">{kvMatch[1]}</strong>{' '}
          {kvMatch[2].replace(/[*_`#\\]/g, '')}
        </>
      );
    }
    return text.replace(/[*_`#\\]/g, '');
  }

  return parts.map((part, i) => {
    if (part.type === 'strong') {
      return (
        <strong key={i} className="ai-brief-strong">
          {part.value}
        </strong>
      );
    }
    if (part.type === 'em') {
      return (
        <em key={i} className="ai-brief-em">
          {part.value}
        </em>
      );
    }
    return <React.Fragment key={i}>{part.value}</React.Fragment>;
  });
}

export default function AiJourneyBrief({ assessment }) {
  const [status, setStatus] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const [brief, setBrief] = useState(null);
  const [model, setModel] = useState('IBM Bob');
  const [errorMsg, setErrorMsg] = useState(null);

  // Reset state whenever the user evaluates a new journey
  useEffect(() => {
    setStatus('idle');
    setBrief(null);
    setErrorMsg(null);
  }, [assessment?.origin, assessment?.destination, assessment?.departure_datetime]);

  if (!assessment) return null;

  const handleGenerate = async () => {
    if (status === 'loading') return;
    setStatus('loading');
    setErrorMsg(null);

    try {
      const evidence = {
        route: `${assessment.origin} → ${assessment.destination}`,
        distance_km: assessment.total_distance_km,
        duration: assessment.estimated_duration_formatted,
        departure: assessment.departure_datetime,
        risk_window: assessment.highest_risk_time_window,
        hazards: (assessment.hazards || []).slice(0, 6).map((h) => ({
          type: h.hazard_type === 'ML_PREDICTED_HOTSPOT' ? 'ML hotspot' : 'Official blackspot',
          name: h.location_name,
          distance_km: h.distance_from_origin_km,
          eta: h.expected_arrival_time,
          risk_tier: h.risk_tier,
          road_context: h.road_classification || h.highway_designation || undefined,
        })),
      };

      const result = await fetchJourneyAiBrief(evidence);
      setBrief(result.brief);
      if (result.model) setModel(result.model);
      setStatus('success');
    } catch (err) {
      console.warn('IBM Bob AI briefing request failed:', err);
      setErrorMsg('AI briefing is temporarily unavailable. Your journey analysis is still available.');
      setStatus('error');
    }
  };

  return (
    <div className="ai-brief-card" aria-live="polite">
      <div className="ai-brief-header">
        <div className="ai-brief-title-group">
          <div className="ai-brief-icon-wrap" aria-hidden="true">
            <img
              src={ibmBobIcon}
              alt="IBM Bob"
              className="ai-bob-icon-img"
              width="24"
              height="24"
            />
          </div>
          <div>
            <div className="ai-brief-badge-row">
              <span className="ai-brief-title">AI JOURNEY BRIEF</span>
              <span className="ai-bob-tag">Powered by IBM Bob</span>
            </div>
            <p className="ai-brief-subtitle">
              Get a quick AI-generated safety summary from the analyzed journey.
            </p>
          </div>
        </div>

        {status === 'idle' && (
          <button
            type="button"
            className="btn-generate-ai-brief"
            onClick={handleGenerate}
          >
            <span>Generate AI Brief</span>
          </button>
        )}

        {status === 'loading' && (
          <button
            type="button"
            className="btn-generate-ai-brief is-loading"
            disabled
          >
            <Loader2 size={13} className="spin-icon" />
            <span>Generating AI brief...</span>
          </button>
        )}

        {(status === 'success' || status === 'error') && (
          <button
            type="button"
            className="btn-generate-ai-brief btn-refresh-brief"
            onClick={handleGenerate}
            title="Regenerate brief with IBM Bob"
          >
            <RefreshCw size={12} />
            <span>Regenerate</span>
          </button>
        )}
      </div>

      {status === 'loading' && (
        <div className="ai-brief-loading-body">
          <div className="ai-brief-skeleton-line short" />
          <div className="ai-brief-skeleton-line" />
          <div className="ai-brief-skeleton-line medium" />
        </div>
      )}

      {status === 'error' && (
        <div className="ai-brief-error-body" role="alert">
          <AlertCircle size={15} className="ai-error-icon" />
          <div className="ai-error-text">
            <span>{errorMsg}</span>
          </div>
        </div>
      )}

      {status === 'success' && brief && (() => {
        const { heading, bullets } = parseBobBrief(brief);
        return (
          <div className="ai-brief-content-body">
            {heading && (
              <div className="ai-brief-heading-banner">
                {heading}
              </div>
            )}

            <div className="ai-brief-bullets-list">
              {bullets.map((bullet, idx) => (
                <div key={idx} className="ai-bullet-item">
                  <span className="ai-bullet-point" aria-hidden="true">•</span>
                  <span className="ai-line-text">{renderInlineFormatted(bullet)}</span>
                </div>
              ))}
            </div>

            <div className="ai-brief-footer">
              <span className="ai-disclaimer-text">
                AI-generated decision support based on available historical and official evidence. It does not guarantee safety.
              </span>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

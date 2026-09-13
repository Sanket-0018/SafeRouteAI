import React from 'react';
import { BookOpen, ExternalLink, Award, CheckCircle2, ShieldCheck } from 'lucide-react';

export default function RagGuidanceView({ guidance = [], retrievalQuery = '' }) {
  if (!guidance || guidance.length === 0) {
    return (
      <div className="guidance-empty">
        <p>No safety guidance chunks retrieved for this scenario.</p>
      </div>
    );
  }

  const getOrgBadgeClass = (org = '') => {
    if (org.includes('WHO') || org.includes('World Health')) return 'badge-who';
    if (org.includes('MoRTH') || org.includes('Transport')) return 'badge-morth';
    if (org.includes('IRC') || org.includes('Indian Roads')) return 'badge-irc';
    return 'badge-gov';
  };

  return (
    <div className="rag-guidance-section">
      <div className="section-title-row">
        <div className="title-left">
          <BookOpen size={18} className="text-emerald" />
          <h3 className="section-title">Prevention & Road-Safety Guidance (RAG Domain Knowledge)</h3>
        </div>
        <span className="rag-count-pill">{guidance.length} Countermeasures Retrieved</span>
      </div>

      <p className="guidance-subtext">
        The RAG system semantically matched the hotspot's top predictive factors against official road safety standards (MoRTH, IRC, WHO) to retrieve evidence-grounded engineering countermeasures and enforcement interventions.
      </p>

      {retrievalQuery && (
        <details className="retrieval-query-details">
          <summary className="query-summary-tag">
            <span>View Synthesized Retrieval Query</span>
          </summary>
          <div className="query-code-box">"{retrievalQuery}"</div>
        </details>
      )}

      <div className="guidance-cards-list">
        {guidance.map((g, i) => {
          const matchPct = (g.relevance_score * 100).toFixed(1);

          return (
            <div key={g.chunk_id || i} className="guidance-card">
              <div className="guidance-card-header">
                <div className="guidance-org-row">
                  <span className={`org-badge ${getOrgBadgeClass(g.organization)}`}>
                    <ShieldCheck size={12} />
                    <span>{g.organization}</span>
                  </span>
                  {g.document_type && (
                    <span className="doc-type-pill">{g.document_type.replace(/_/g, ' ')}</span>
                  )}
                </div>
                <div className="relevance-badge" title="Semantic cosine similarity score">
                  <Award size={13} />
                  <span>{matchPct}% Match</span>
                </div>
              </div>

              <h4 className="guidance-title">{g.title}</h4>

              {g.topic && <div className="guidance-topic-tag">Topic: {g.topic}</div>}

              <div className="guidance-excerpt-box">
                <p className="guidance-excerpt">{g.content_excerpt}</p>
              </div>

              <div className="guidance-footer">
                <div className="chunk-id-tag">Chunk: {g.chunk_id}</div>
                {g.source_url && (
                  <a
                    href={g.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-link-btn"
                  >
                    <span>View Official Source</span>
                    <ExternalLink size={13} />
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="rag-notice-box">
        <CheckCircle2 size={14} className="text-emerald" />
        <span>
          <strong>Domain Separation Notice:</strong> RAG retrieves authoritative domain guidelines to support engineering remediation; it does <em>not</em> calculate or alter the accident probability.
        </span>
      </div>
    </div>
  );
}

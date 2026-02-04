/**
 * Optimized RAG Component
 * Real-time streaming RAG with intermediate results
 *
 * Features:
 * - Progressive document retrieval display
 * - Reranking visualization
 * - Token-by-token answer generation
 * - Performance metrics
 */

import React, { useState } from 'react';
import { useRAGStreaming } from '../hooks/useStreaming';

interface OptimizedRAGProps {
  onQueryComplete?: (result: any) => void;
}

export const OptimizedRAG: React.FC<OptimizedRAGProps> = ({ onQueryComplete }) => {
  const [query, setQuery] = useState<string>('');
  const [k, setK] = useState<number>(5);
  const [expandQueries, setExpandQueries] = useState<boolean>(true);
  const [useReranking, setUseReranking] = useState<boolean>(true);

  const {
    state,
    isStreaming,
    error,
    startStream,
    stopStream,
    reset
  } = useRAGStreaming();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim() || isStreaming) return;

    startStream({
      query,
      k,
      expand_queries: expandQueries,
      use_reranking: useReranking
    });
  };

  const handleStop = () => {
    stopStream();
  };

  const handleReset = () => {
    reset();
    setQuery('');
  };

  const getStageIcon = () => {
    switch (state.stage) {
      case 'searching': return '🔍';
      case 'reranking': return '📊';
      case 'generating': return '✍️';
      case 'done': return '✅';
      default: return '⏳';
    }
  };

  const getStageLabel = () => {
    switch (state.stage) {
      case 'searching': return 'Dökümanlar aranıyor...';
      case 'reranking': return 'Sonuçlar sıralanıyor...';
      case 'generating': return 'Cevap oluşturuluyor...';
      case 'done': return 'Tamamlandı';
      default: return 'Hazır';
    }
  };

  return (
    <div className="optimized-rag-container" style={styles.container}>
      {/* Query form */}
      <form onSubmit={handleSubmit} style={styles.form}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Sorunuzu yazın..."
          disabled={isStreaming}
          style={{
            ...styles.input,
            ...(isStreaming && styles.inputDisabled)
          }}
        />

        <div style={styles.options}>
          <label style={styles.label}>
            <input
              type="checkbox"
              checked={expandQueries}
              onChange={(e) => setExpandQueries(e.target.checked)}
              disabled={isStreaming}
            />
            Query Expansion
          </label>

          <label style={styles.label}>
            <input
              type="checkbox"
              checked={useReranking}
              onChange={(e) => setUseReranking(e.target.checked)}
              disabled={isStreaming}
            />
            Cross-Encoder Reranking
          </label>

          <label style={styles.label}>
            Top K:
            <input
              type="number"
              value={k}
              onChange={(e) => setK(parseInt(e.target.value))}
              min={1}
              max={20}
              disabled={isStreaming}
              style={styles.numberInput}
            />
          </label>
        </div>

        <div style={styles.buttonGroup}>
          {isStreaming ? (
            <button
              type="button"
              onClick={handleStop}
              style={{ ...styles.button, ...styles.stopButton }}
            >
              ⏹ Durdur
            </button>
          ) : (
            <button
              type="submit"
              disabled={!query.trim()}
              style={{
                ...styles.button,
                ...styles.searchButton,
                ...(!query.trim() && styles.buttonDisabled)
              }}
            >
              🔍 Ara
            </button>
          )}

          {state.content && (
            <button
              type="button"
              onClick={handleReset}
              style={{ ...styles.button, ...styles.resetButton }}
            >
              🔄 Temizle
            </button>
          )}
        </div>
      </form>

      {/* Error */}
      {error && (
        <div className="error" style={styles.error}>
          ❌ {error.message}
        </div>
      )}

      {/* Stage indicator */}
      {isStreaming && (
        <div className="stage" style={styles.stage}>
          <span style={styles.stageIcon}>{getStageIcon()}</span>
          <span style={styles.stageLabel}>{getStageLabel()}</span>
        </div>
      )}

      {/* Documents */}
      {state.documents.length > 0 && (
        <div className="documents" style={styles.documents}>
          <h3 style={styles.heading}>
            📚 Bulunan Dökümanlar ({state.documents.length})
          </h3>

          <div style={styles.documentList}>
            {state.documents.map((doc, index) => (
              <div key={index} className="document" style={styles.document}>
                <div style={styles.documentHeader}>
                  <span style={styles.documentRank}>#{index + 1}</span>
                  <span style={styles.documentScore}>
                    Score: {doc.score?.toFixed(3) || 'N/A'}
                  </span>
                </div>

                <div style={styles.documentContent}>
                  {doc.content?.substring(0, 200)}
                  {doc.content?.length > 200 && '...'}
                </div>

                {doc.metadata && (
                  <div style={styles.documentMetadata}>
                    {Object.entries(doc.metadata).map(([key, value]) => (
                      <span key={key} style={styles.metadataTag}>
                        {key}: {String(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Answer */}
      {state.content && (
        <div className="answer" style={styles.answer}>
          <h3 style={styles.heading}>💡 Cevap</h3>

          <div style={styles.answerContent}>
            {state.content}
            {isStreaming && state.stage === 'generating' && (
              <span className="cursor" style={styles.cursor}>▋</span>
            )}
          </div>
        </div>
      )}

      {/* Metadata */}
      {state.metadata && (
        <div className="metadata" style={styles.metadata}>
          ⚡ {state.metadata.total_time_ms}ms total
          {state.metadata.search_time_ms && ` · ${state.metadata.search_time_ms}ms search`}
          {state.metadata.generation_time_ms && ` · ${state.metadata.generation_time_ms}ms generation`}
          {state.metadata.documents_retrieved && ` · ${state.metadata.documents_retrieved} docs`}
        </div>
      )}
    </div>
  );
};

// ==================== STYLES ====================

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    maxWidth: '1000px',
    margin: '0 auto',
    padding: '20px'
  },

  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    padding: '20px',
    backgroundColor: '#fff',
    border: '1px solid #ddd',
    borderRadius: '8px'
  },

  input: {
    padding: '12px 16px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '14px',
    outline: 'none'
  },

  inputDisabled: {
    backgroundColor: '#f5f5f5',
    cursor: 'not-allowed'
  },

  options: {
    display: 'flex',
    gap: '20px',
    flexWrap: 'wrap'
  },

  label: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    color: '#555'
  },

  numberInput: {
    width: '60px',
    marginLeft: '8px',
    padding: '4px 8px',
    border: '1px solid #ddd',
    borderRadius: '4px'
  },

  buttonGroup: {
    display: 'flex',
    gap: '8px'
  },

  button: {
    padding: '12px 24px',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s'
  },

  searchButton: {
    backgroundColor: '#1976d2',
    color: '#fff'
  },

  stopButton: {
    backgroundColor: '#d32f2f',
    color: '#fff'
  },

  resetButton: {
    backgroundColor: '#757575',
    color: '#fff'
  },

  buttonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed'
  },

  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '12px',
    borderRadius: '8px',
    textAlign: 'center'
  },

  stage: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 20px',
    backgroundColor: '#e3f2fd',
    border: '1px solid #90caf9',
    borderRadius: '8px'
  },

  stageIcon: {
    fontSize: '24px'
  },

  stageLabel: {
    fontSize: '14px',
    fontWeight: 500,
    color: '#1976d2'
  },

  documents: {
    padding: '20px',
    backgroundColor: '#fff',
    border: '1px solid #ddd',
    borderRadius: '8px'
  },

  heading: {
    margin: '0 0 16px 0',
    fontSize: '16px',
    fontWeight: 600,
    color: '#333'
  },

  documentList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },

  document: {
    padding: '12px',
    backgroundColor: '#f8f9fa',
    border: '1px solid #e0e0e0',
    borderRadius: '6px'
  },

  documentHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px'
  },

  documentRank: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#1976d2'
  },

  documentScore: {
    fontSize: '12px',
    color: '#666'
  },

  documentContent: {
    fontSize: '13px',
    lineHeight: '1.5',
    color: '#333',
    marginBottom: '8px'
  },

  documentMetadata: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap'
  },

  metadataTag: {
    fontSize: '11px',
    padding: '2px 8px',
    backgroundColor: '#e0e0e0',
    borderRadius: '4px',
    color: '#555'
  },

  answer: {
    padding: '20px',
    backgroundColor: '#fff',
    border: '1px solid #ddd',
    borderRadius: '8px'
  },

  answerContent: {
    fontSize: '14px',
    lineHeight: '1.7',
    color: '#333',
    whiteSpace: 'pre-wrap'
  },

  cursor: {
    animation: 'blink 1s infinite',
    marginLeft: '2px'
  },

  metadata: {
    padding: '12px 20px',
    fontSize: '12px',
    color: '#666',
    backgroundColor: '#f8f9fa',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    textAlign: 'center'
  }
};

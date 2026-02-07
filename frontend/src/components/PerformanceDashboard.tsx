/**
 * Performance Dashboard Component
 * Real-time monitoring of system performance metrics
 *
 * Features:
 * - LLM connection pool stats
 * - Vector store performance
 * - Cache hit rates
 * - RAG pipeline metrics
 * - Auto-refresh capability
 */

import * as React from 'react';
import {  useState  } from 'react';

import {
  usePerformanceMonitor,
  useLLMPoolStats,
  useVectorStoreStats,
  useCacheStats,
  useRAGPipelineStats,
} from '../hooks/usePerformanceMonitor';

interface PerformanceDashboardProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  autoRefresh = true,
  refreshInterval = 10000,
}) => {
  const [showDetails, setShowDetails] = useState<string | null>(null);

  const { metrics: _metrics, isLoading: metricsLoading, refresh: refreshMetrics } = usePerformanceMonitor(
    autoRefresh,
    refreshInterval,
  );

  const { stats: llmStats, refresh: refreshLLM } = useLLMPoolStats(autoRefresh, 5000);
  const { stats: vectorStats, refresh: refreshVector } = useVectorStoreStats(autoRefresh, 5000);
  const { stats: cacheStats, clearByTag, refresh: refreshCache } = useCacheStats(autoRefresh, 5000);
  const { stats: ragStats, refresh: refreshRAG } = useRAGPipelineStats(autoRefresh, 5000);

  const handleRefreshAll = async () => {
    await Promise.all([
      refreshMetrics(),
      refreshLLM(),
      refreshVector(),
      refreshCache(),
      refreshRAG(),
    ]);
  };

  const handleClearCache = async (tag: string) => {
    if (window.confirm(`"${tag}" etiketli cache temizlensin mi?`)) {
      await clearByTag(tag);
    }
  };

  const toggleDetails = (section: string) => {
    setShowDetails(prev => prev === section ? null : section);
  };

  const getPerformanceColor = (value: number, thresholds: { good: number; warning: number }) => {
    if (value >= thresholds.good) {return '#4caf50';}
    if (value >= thresholds.warning) {return '#ff9800';}
    return '#f44336';
  };

  return (
    <div className="performance-dashboard" style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h2 style={styles.title}>⚡ Performance Dashboard</h2>

        <button onClick={handleRefreshAll} style={styles.refreshButton} disabled={metricsLoading}>
          🔄 {metricsLoading ? 'Yenileniyor...' : 'Yenile'}
        </button>
      </div>

      {/* Overview Cards */}
      <div style={styles.cardGrid}>
        {/* LLM Pool Card */}
        <div
          className="metric-card"
          style={styles.card}
          onClick={() => toggleDetails('llm')}
        >
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>🔌</span>
            <span style={styles.cardTitle}>LLM Connection Pool</span>
          </div>

          {llmStats && (
            <>
              <div style={styles.cardMetric}>
                <span style={styles.metricValue}>{llmStats.avg_response_time_ms.toFixed(0)}ms</span>
                <span style={styles.metricLabel}>Avg Response Time</span>
              </div>

              <div style={styles.cardStats}>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>Requests</span>
                  <span style={styles.statValue}>{llmStats.total_requests.toLocaleString()}</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>Active Conn.</span>
                  <span style={styles.statValue}>{llmStats.active_connections}</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>Cache Hit</span>
                  <span style={{ ...styles.statValue, color: getPerformanceColor(llmStats.cache_hit_rate * 100, { good: 80, warning: 50 }) }}>
                    {(llmStats.cache_hit_rate * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </>
          )}

          {showDetails === 'llm' && llmStats && (
            <div style={styles.details}>
              <div style={styles.detailRow}>
                <span>Total Requests:</span>
                <span>{llmStats.total_requests.toLocaleString()}</span>
              </div>
              <div style={styles.detailRow}>
                <span>Errors:</span>
                <span style={{ color: llmStats.errors > 0 ? '#f44336' : '#4caf50' }}>
                  {llmStats.errors}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Vector Store Card */}
        <div
          className="metric-card"
          style={styles.card}
          onClick={() => toggleDetails('vector')}
        >
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>🔍</span>
            <span style={styles.cardTitle}>Vector Store</span>
          </div>

          {vectorStats && (
            <>
              <div style={styles.cardMetric}>
                <span style={styles.metricValue}>{vectorStats.avg_search_time_ms.toFixed(0)}ms</span>
                <span style={styles.metricLabel}>Avg Search Time</span>
              </div>

              <div style={styles.cardStats}>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>Searches</span>
                  <span style={styles.statValue}>{vectorStats.total_searches.toLocaleString()}</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>Cache Hit</span>
                  <span style={{ ...styles.statValue, color: getPerformanceColor(vectorStats.cache_hit_rate * 100, { good: 85, warning: 60 }) }}>
                    {(vectorStats.cache_hit_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>HNSW</span>
                  <span style={{ ...styles.statValue, color: vectorStats.hnsw_enabled ? '#4caf50' : '#ff9800' }}>
                    {vectorStats.hnsw_enabled ? '✓' : '✗'}
                  </span>
                </div>
              </div>
            </>
          )}

          {showDetails === 'vector' && vectorStats && (
            <div style={styles.details}>
              <div style={styles.detailRow}>
                <span>Index Size:</span>
                <span>{vectorStats.index_size.toLocaleString()}</span>
              </div>
              <div style={styles.detailRow}>
                <span>Cache Hits:</span>
                <span>{vectorStats.cache_hits.toLocaleString()}</span>
              </div>
              <div style={styles.detailRow}>
                <span>Cache Misses:</span>
                <span>{vectorStats.cache_misses.toLocaleString()}</span>
              </div>
            </div>
          )}
        </div>

        {/* Cache Card */}
        <div
          className="metric-card"
          style={styles.card}
          onClick={() => toggleDetails('cache')}
        >
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>💾</span>
            <span style={styles.cardTitle}>Multi-layer Cache</span>
          </div>

          {cacheStats && (
            <>
              <div style={styles.cardMetric}>
                <span style={styles.metricValue}>
                  {(cacheStats.hit_ratio * 100).toFixed(1)}%
                </span>
                <span style={styles.metricLabel}>Hit Ratio</span>
              </div>

              <div style={styles.cardStats}>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>L1 Hits</span>
                  <span style={styles.statValue}>{cacheStats.l1_hits.toLocaleString()}</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>L2 Hits</span>
                  <span style={styles.statValue}>{cacheStats.l2_hits.toLocaleString()}</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>Misses</span>
                  <span style={styles.statValue}>{cacheStats.misses.toLocaleString()}</span>
                </div>
              </div>
            </>
          )}

          {showDetails === 'cache' && cacheStats && (
            <div style={styles.details}>
              <div style={styles.detailRow}>
                <span>Total Keys:</span>
                <span>{cacheStats.total_keys.toLocaleString()}</span>
              </div>
              <div style={styles.detailRow}>
                <span>L1 Size:</span>
                <span>{cacheStats.l1_size.toLocaleString()}</span>
              </div>
              <div style={styles.detailRow}>
                <span>L2 Size:</span>
                <span>{cacheStats.l2_size.toLocaleString()}</span>
              </div>
              <div style={styles.detailRow}>
                <span>Evictions:</span>
                <span>{cacheStats.evictions.toLocaleString()}</span>
              </div>

              <div style={styles.cacheActions}>
                <button onClick={() => handleClearCache('user')} style={styles.actionButton}>
                  Clear User Cache
                </button>
                <button onClick={() => handleClearCache('session')} style={styles.actionButton}>
                  Clear Session Cache
                </button>
              </div>
            </div>
          )}
        </div>

        {/* RAG Pipeline Card */}
        <div
          className="metric-card"
          style={styles.card}
          onClick={() => toggleDetails('rag')}
        >
          <div style={styles.cardHeader}>
            <span style={styles.cardIcon}>📚</span>
            <span style={styles.cardTitle}>RAG Pipeline</span>
          </div>

          {ragStats && (
            <>
              <div style={styles.cardMetric}>
                <span style={styles.metricValue}>{ragStats.avg_query_time_ms.toFixed(0)}ms</span>
                <span style={styles.metricLabel}>Avg Query Time</span>
              </div>

              <div style={styles.cardStats}>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>Queries</span>
                  <span style={styles.statValue}>{ragStats.total_queries.toLocaleString()}</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>Speedup</span>
                  <span style={{ ...styles.statValue, color: getPerformanceColor(ragStats.parallel_speedup, { good: 2, warning: 1.5 }) }}>
                    {ragStats.parallel_speedup.toFixed(1)}x
                  </span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statLabel}>Avg Docs</span>
                  <span style={styles.statValue}>{ragStats.avg_documents_retrieved.toFixed(1)}</span>
                </div>
              </div>
            </>
          )}

          {showDetails === 'rag' && ragStats && (
            <div style={styles.details}>
              <div style={styles.detailRow}>
                <span>Query Expansion:</span>
                <span style={{ color: ragStats.query_expansion_enabled ? '#4caf50' : '#ff9800' }}>
                  {ragStats.query_expansion_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <div style={styles.detailRow}>
                <span>Reranking:</span>
                <span style={{ color: ragStats.reranking_enabled ? '#4caf50' : '#ff9800' }}>
                  {ragStats.reranking_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Performance Targets */}
      <div style={styles.targets}>
        <h3 style={styles.targetsTitle}>🎯 Performance Targets</h3>

        <div style={styles.targetGrid}>
          <div style={styles.targetItem}>
            <span style={styles.targetLabel}>Chat Response:</span>
            <span style={styles.targetValue}>&lt;200ms</span>
          </div>
          <div style={styles.targetItem}>
            <span style={styles.targetLabel}>LLM Generation:</span>
            <span style={styles.targetValue}>&lt;2s</span>
          </div>
          <div style={styles.targetItem}>
            <span style={styles.targetLabel}>Vector Search:</span>
            <span style={styles.targetValue}>&lt;100ms</span>
          </div>
          <div style={styles.targetItem}>
            <span style={styles.targetLabel}>RAG Queries:</span>
            <span style={styles.targetValue}>&lt;2s</span>
          </div>
          <div style={styles.targetItem}>
            <span style={styles.targetLabel}>Cache Hit Rate:</span>
            <span style={styles.targetValue}>&gt;85%</span>
          </div>
          <div style={styles.targetItem}>
            <span style={styles.targetLabel}>Parallel Speedup:</span>
            <span style={styles.targetValue}>&gt;2x</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// ==================== STYLES ====================

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '20px',
    maxWidth: '1400px',
    margin: '0 auto',
  },

  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },

  title: {
    margin: 0,
    fontSize: '24px',
    fontWeight: 600,
    color: '#333',
  },

  refreshButton: {
    padding: '10px 20px',
    backgroundColor: '#1976d2',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },

  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '20px',
    marginBottom: '24px',
  },

  card: {
    padding: '20px',
    backgroundColor: '#fff',
    border: '1px solid #ddd',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
  },

  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '16px',
  },

  cardIcon: {
    fontSize: '24px',
  },

  cardTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#555',
  },

  cardMetric: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    marginBottom: '16px',
    padding: '16px',
    backgroundColor: '#f8f9fa',
    borderRadius: '6px',
  },

  metricValue: {
    fontSize: '32px',
    fontWeight: 700,
    color: '#1976d2',
    marginBottom: '4px',
  },

  metricLabel: {
    fontSize: '12px',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },

  cardStats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
  },

  stat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '8px',
    backgroundColor: '#fafafa',
    borderRadius: '4px',
  },

  statLabel: {
    fontSize: '11px',
    color: '#666',
    marginBottom: '4px',
  },

  statValue: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#333',
  },

  details: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#f8f9fa',
    borderRadius: '6px',
    borderTop: '2px solid #e0e0e0',
  },

  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '8px 0',
    fontSize: '13px',
    borderBottom: '1px solid #e0e0e0',
  },

  cacheActions: {
    display: 'flex',
    gap: '8px',
    marginTop: '12px',
  },

  actionButton: {
    flex: 1,
    padding: '8px 12px',
    backgroundColor: '#757575',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
  },

  targets: {
    padding: '20px',
    backgroundColor: '#fff',
    border: '1px solid #ddd',
    borderRadius: '8px',
  },

  targetsTitle: {
    margin: '0 0 16px 0',
    fontSize: '16px',
    fontWeight: 600,
    color: '#333',
  },

  targetGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '12px',
  },

  targetItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px',
    backgroundColor: '#f8f9fa',
    borderRadius: '6px',
  },

  targetLabel: {
    fontSize: '13px',
    color: '#555',
  },

  targetValue: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#1976d2',
  },
};

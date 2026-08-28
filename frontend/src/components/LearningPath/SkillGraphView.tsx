/**
 * SkillGraphView — F4 Granüler Bilgi Haritası
 *
 * Ön koşul DAG'ını ve öğrencinin hakimiyet durumunu görselleştirir.
 * API verisi alınamazsa statik fallback verileri kullanılır.
 *
 * Endpoints:
 *   GET /api/v1/knowledge-map/{subject}       — DAG yapısı {nodes, edges}
 *   GET /api/v1/knowledge-map/{subject}/state — Öğrenci hakimiyet katmanı
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Chip,
  Tooltip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  AccountTree,
  CheckCircle,
  Lock,
  RadioButtonUnchecked,
  Refresh,
} from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';
import { apiRequest } from '../../utils/apiHelpers';

// ---------------------------------------------------------------------------
// Types matching backend Pydantic schemas
// ---------------------------------------------------------------------------

interface KnowledgeNode {
  id: string;
  name: string;
  prerequisites: string[];
  difficulty_range: [number, number];
}

interface KnowledgeEdge {
  from: string;
  to: string;
}

interface DagResponse {
  subject: string;
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}

interface KnowledgeStateItem {
  knowledge_point_id: string;
  name: string;
  mastery_level: number;
  confidence: number;
  last_assessed: string | null;
  /** locked | available | mastered */
  status: 'locked' | 'available' | 'mastered';
}

// Merged node — DAG structure + mastery overlay
interface EnrichedNode extends KnowledgeNode {
  mastery_level: number;
  confidence: number;
  status: 'locked' | 'available' | 'mastered';
  last_assessed: string | null;
}

// ---------------------------------------------------------------------------
// Static fallback data (used when API is unavailable)
// ---------------------------------------------------------------------------

const STATIC_FALLBACK: Record<string, DagResponse> = {
  matematik: {
    subject: 'matematik',
    nodes: [
      { id: 'temel-islemler', name: 'Temel İşlemler', prerequisites: [], difficulty_range: [0.0, 1.0] },
      { id: 'kesirler', name: 'Kesirler ve Ondalıklar', prerequisites: ['temel-islemler'], difficulty_range: [0.5, 1.5] },
      { id: 'oran-oranti', name: 'Oran-Orantı', prerequisites: ['kesirler'], difficulty_range: [1.0, 2.0] },
      { id: 'denklemler', name: 'Denklemler', prerequisites: ['temel-islemler'], difficulty_range: [1.0, 2.5] },
      { id: 'fonksiyonlar', name: 'Fonksiyonlar', prerequisites: ['denklemler'], difficulty_range: [1.5, 3.0] },
      { id: 'turev', name: 'Türev', prerequisites: ['fonksiyonlar'], difficulty_range: [2.0, 4.0] },
      { id: 'integral', name: 'İntegral', prerequisites: ['turev'], difficulty_range: [2.5, 4.0] },
    ],
    edges: [
      { from: 'temel-islemler', to: 'kesirler' },
      { from: 'temel-islemler', to: 'denklemler' },
      { from: 'kesirler', to: 'oran-oranti' },
      { from: 'denklemler', to: 'fonksiyonlar' },
      { from: 'fonksiyonlar', to: 'turev' },
      { from: 'turev', to: 'integral' },
    ],
  },
  fizik: {
    subject: 'fizik',
    nodes: [
      { id: 'kinematik', name: 'Kinematik', prerequisites: [], difficulty_range: [0.5, 2.0] },
      { id: 'dinamik', name: 'Dinamik (Newton)', prerequisites: ['kinematik'], difficulty_range: [1.0, 2.5] },
      { id: 'enerji', name: 'Enerji ve İş', prerequisites: ['dinamik'], difficulty_range: [1.0, 2.5] },
      { id: 'elektrik', name: 'Elektrik', prerequisites: ['enerji'], difficulty_range: [1.5, 3.5] },
      { id: 'manyetizma', name: 'Manyetizma', prerequisites: ['elektrik'], difficulty_range: [2.0, 4.0] },
    ],
    edges: [
      { from: 'kinematik', to: 'dinamik' },
      { from: 'dinamik', to: 'enerji' },
      { from: 'enerji', to: 'elektrik' },
      { from: 'elektrik', to: 'manyetizma' },
    ],
  },
};

function getFallbackDag(subject: string): DagResponse {
  const key = subject.toLowerCase();
  if (STATIC_FALLBACK[key]) {return STATIC_FALLBACK[key];}
  // Generic single-node fallback for unknown subjects
  return {
    subject: key,
    nodes: [{ id: key, name: subject, prerequisites: [], difficulty_range: [0.0, 4.0] }],
    edges: [],
  };
}

// ---------------------------------------------------------------------------
// Helper: merge mastery state onto DAG nodes
// ---------------------------------------------------------------------------

function mergeState(
  dag: DagResponse,
  states: KnowledgeStateItem[],
): EnrichedNode[] {
  const stateMap = new Map(states.map(s => [s.knowledge_point_id, s]));
  return dag.nodes.map(node => {
    const s = stateMap.get(node.id);
    return {
      ...node,
      mastery_level: s?.mastery_level ?? 0,
      confidence: s?.confidence ?? 0,
      status: s?.status ?? 'locked',
      last_assessed: s?.last_assessed ?? null,
    };
  });
}

// ---------------------------------------------------------------------------
// Status icon + color helpers
// ---------------------------------------------------------------------------

function statusColor(status: EnrichedNode['status']): string {
  switch (status) {
    case 'mastered': return '#22c55e';
    case 'available': return '#6366f1';
    case 'locked': return '#94a3b8';
  }
}

function StatusIcon({ status, size = 18 }: { status: EnrichedNode['status']; size?: number }) {
  const sx = { fontSize: size, color: statusColor(status) };
  switch (status) {
    case 'mastered': return <CheckCircle sx={sx} />;
    case 'available': return <RadioButtonUnchecked sx={sx} />;
    case 'locked': return <Lock sx={sx} />;
  }
}

// ---------------------------------------------------------------------------
// NodeCard sub-component
// ---------------------------------------------------------------------------

interface NodeCardProps {
  node: EnrichedNode;
  isSelected: boolean;
  onClick: () => void;
}

function NodeCard({ node, isSelected, onClick }: NodeCardProps) {
  const masteryPct = Math.round(node.mastery_level * 100);
  const color = statusColor(node.status);

  return (
    <Box
      onClick={onClick}
      sx={{
        p: 1.5,
        borderRadius: 2,
        border: `1.5px solid ${isSelected ? color : 'rgba(0,0,0,0.08)'}`,
        backgroundColor: isSelected ? `${color}10` : 'rgba(255,255,255,0.6)',
        cursor: 'pointer',
        transition: 'all 0.18s ease',
        '&:hover': {
          borderColor: color,
          backgroundColor: `${color}08`,
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.75 }}>
        <StatusIcon status={node.status} />
        <Typography
          variant="body2"
          fontWeight={isSelected ? 700 : 500}
          sx={{
            flex: 1,
            color: node.status === 'locked' ? 'text.disabled' : 'text.primary',
          }}
        >
          {node.name}
        </Typography>
        <Typography variant="caption" fontWeight={700} sx={{ color }}>
          %{masteryPct}
        </Typography>
      </Box>

      {node.status !== 'locked' && (
        <LinearProgress
          variant="determinate"
          value={masteryPct}
          sx={{
            height: 4,
            borderRadius: 2,
            bgcolor: 'rgba(0,0,0,0.06)',
            '& .MuiLinearProgress-bar': {
              borderRadius: 2,
              backgroundColor: color,
            },
          }}
        />
      )}

      {node.prerequisites.length > 0 && (
        <Typography variant="caption" color="text.disabled" sx={{ mt: 0.5, display: 'block' }}>
          Ön koşul: {node.prerequisites.length} konu
        </Typography>
      )}
    </Box>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface SkillGraphViewProps {
  /** Subject code, e.g. "matematik" or "fizik" */
  subject: string;
}

export function SkillGraphView({ subject }: SkillGraphViewProps) {
  const [dag, setDag] = useState<DagResponse | null>(null);
  const [enrichedNodes, setEnrichedNodes] = useState<EnrichedNode[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [loadingDag, setLoadingDag] = useState(true);
  const [loadingState, setLoadingState] = useState(false);
  const [usingFallback, setUsingFallback] = useState(false);

  // ------------------------------------------------------------------
  // Fetch DAG structure
  // ------------------------------------------------------------------
  const fetchDag = useCallback(async () => {
    setLoadingDag(true);
    setUsingFallback(false);

    try {
      const data = await apiRequest<DagResponse>(
        `/api/v1/knowledge-map/${encodeURIComponent(subject.toLowerCase())}`,
      );
      setDag(data);
      // Populate with zero-mastery until state loads
      setEnrichedNodes(mergeState(data, []));
    } catch {
      // API unavailable — use static fallback
      const fallback = getFallbackDag(subject);
      setDag(fallback);
      setEnrichedNodes(mergeState(fallback, []));
      setUsingFallback(true);
    } finally {
      setLoadingDag(false);
    }
  }, [subject]);

  // ------------------------------------------------------------------
  // Fetch student knowledge state (mastery overlay)
  // ------------------------------------------------------------------
  const fetchKnowledgeState = useCallback(async (currentDag: DagResponse) => {
    setLoadingState(true);
    try {
      const states = await apiRequest<KnowledgeStateItem[]>(
        `/api/v1/knowledge-map/${encodeURIComponent(subject.toLowerCase())}/state`,
      );
      setEnrichedNodes(mergeState(currentDag, states));
    } catch {
      // State endpoint failed — keep zero-mastery nodes, don't error out
    } finally {
      setLoadingState(false);
    }
  }, [subject]);

  // ------------------------------------------------------------------
  // On mount / subject change: fetch DAG then state
  // ------------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoadingDag(true);
      setUsingFallback(false);

      let resolvedDag: DagResponse;

      try {
        const data = await apiRequest<DagResponse>(
          `/api/v1/knowledge-map/${encodeURIComponent(subject.toLowerCase())}`,
        );
        if (cancelled) {return;}
        resolvedDag = data;
        setDag(data);
        setEnrichedNodes(mergeState(data, []));
      } catch {
        if (cancelled) {return;}
        resolvedDag = getFallbackDag(subject);
        setDag(resolvedDag);
        setEnrichedNodes(mergeState(resolvedDag, []));
        setUsingFallback(true);
      } finally {
        if (!cancelled) {setLoadingDag(false);}
      }

      // Fetch mastery overlay (best-effort, only if DAG loaded from API)
      if (!usingFallback) {
        setLoadingState(true);
        try {
          const states = await apiRequest<KnowledgeStateItem[]>(
            `/api/v1/knowledge-map/${encodeURIComponent(subject.toLowerCase())}/state`,
          );
          if (!cancelled) {
            setEnrichedNodes(mergeState(resolvedDag, states));
          }
        } catch {
          // Silently ignore — zero-mastery is acceptable fallback
        } finally {
          if (!cancelled) {setLoadingState(false);}
        }
      }
    }

    load();
    return () => { cancelled = true; };
  }, [subject]); // eslint-disable-line react-hooks/exhaustive-deps

  // ------------------------------------------------------------------
  // Derived stats
  // ------------------------------------------------------------------
  const stats = (() => {
    const total = enrichedNodes.length;
    const mastered = enrichedNodes.filter(n => n.status === 'mastered').length;
    const available = enrichedNodes.filter(n => n.status === 'available').length;
    const locked = enrichedNodes.filter(n => n.status === 'locked').length;
    const avgMastery = total > 0
      ? Math.round((enrichedNodes.reduce((acc, n) => acc + n.mastery_level, 0) / total) * 100)
      : 0;
    return { total, mastered, available, locked, avgMastery };
  })();

  const selectedNode = enrichedNodes.find(n => n.id === selectedNodeId) ?? null;

  // ------------------------------------------------------------------
  // Render: loading
  // ------------------------------------------------------------------
  if (loadingDag) {
    return (
      <GlassCard glassIntensity="light">
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 5, gap: 2 }}>
          <CircularProgress size={36} />
          <Typography variant="body2" color="text.secondary">
            Bilgi haritası yükleniyor...
          </Typography>
        </Box>
      </GlassCard>
    );
  }

  // ------------------------------------------------------------------
  // Render: main
  // ------------------------------------------------------------------
  return (
    <GlassCard glassIntensity="light">
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccountTree sx={{ fontSize: 20, color: '#6366f1' }} />
          <Typography variant="subtitle1" fontWeight={700}>
            Bilgi Haritası
          </Typography>
          <Chip
            label={subject.charAt(0).toUpperCase() + subject.slice(1)}
            size="small"
            sx={{
              fontSize: 10,
              height: 20,
              fontWeight: 600,
              backgroundColor: 'rgba(99,102,241,0.1)',
              color: '#6366f1',
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {loadingState && <CircularProgress size={16} />}
          <Tooltip title="Yenile">
            <Box
              component="button"
              onClick={() => {
                if (dag) {
                  fetchDag();
                  if (!usingFallback) {fetchKnowledgeState(dag);}
                }
              }}
              sx={{
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                color: 'text.secondary',
                p: 0.5,
                borderRadius: 1,
                '&:hover': { backgroundColor: 'rgba(0,0,0,0.04)' },
              }}
            >
              <Refresh sx={{ fontSize: 18 }} />
            </Box>
          </Tooltip>
        </Box>
      </Box>

      {/* Fallback notice */}
      {usingFallback && (
        <Alert severity="info" sx={{ mb: 2, py: 0.5, fontSize: 12 }}>
          API bağlantısı yok — örnek veriler gösteriliyor.
        </Alert>
      )}

      {/* Summary stats */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1, mb: 2.5 }}>
        {[
          { label: 'Toplam', value: stats.total, color: '#6366f1' },
          { label: 'Ustalaşılan', value: stats.mastered, color: '#22c55e' },
          { label: 'Müsait', value: stats.available, color: '#6366f1' },
          { label: 'Kilitli', value: stats.locked, color: '#94a3b8' },
        ].map(s => (
          <Box
            key={s.label}
            sx={{
              p: 1,
              borderRadius: 1.5,
              backgroundColor: `${s.color}08`,
              textAlign: 'center',
            }}
          >
            <Typography variant="h6" fontWeight={800} sx={{ color: s.color, lineHeight: 1.2 }}>
              {s.value}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: 10 }}>
              {s.label}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Overall mastery progress */}
      <Box sx={{ mb: 2.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            Ortalama Hakimiyet
          </Typography>
          <Typography variant="caption" fontWeight={700} color="#6366f1">
            %{stats.avgMastery}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={stats.avgMastery}
          sx={{
            height: 6,
            borderRadius: 3,
            bgcolor: 'rgba(0,0,0,0.06)',
            '& .MuiLinearProgress-bar': {
              borderRadius: 3,
              background: 'linear-gradient(90deg, #6366f1, #22c55e)',
            },
          }}
        />
      </Box>

      {/* Node list */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {enrichedNodes.map(node => (
          <NodeCard
            key={node.id}
            node={node}
            isSelected={selectedNodeId === node.id}
            onClick={() => setSelectedNodeId(prev => (prev === node.id ? null : node.id))}
          />
        ))}
      </Box>

      {/* Selected node detail panel */}
      {selectedNode && (
        <Box
          sx={{
            mt: 2,
            p: 2,
            borderRadius: 2,
            border: `1.5px solid ${statusColor(selectedNode.status)}40`,
            backgroundColor: `${statusColor(selectedNode.status)}06`,
          }}
        >
          <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
            {selectedNode.name}
          </Typography>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            <Chip
              label={`Hakimiyet: %${Math.round(selectedNode.mastery_level * 100)}`}
              size="small"
              sx={{ fontSize: 11, fontWeight: 600, backgroundColor: `${statusColor(selectedNode.status)}15`, color: statusColor(selectedNode.status) }}
            />
            <Chip
              label={`Güven: %${Math.round(selectedNode.confidence * 100)}`}
              size="small"
              sx={{ fontSize: 11, fontWeight: 600 }}
            />
            <Chip
              label={`Zorluk: ${selectedNode.difficulty_range[0].toFixed(1)}–${selectedNode.difficulty_range[1].toFixed(1)}`}
              size="small"
              sx={{ fontSize: 11, fontWeight: 600 }}
            />
          </Box>

          {selectedNode.last_assessed && (
            <Typography variant="caption" color="text.disabled" sx={{ mt: 1, display: 'block' }}>
              Son değerlendirme: {new Date(selectedNode.last_assessed).toLocaleDateString('tr-TR')}
            </Typography>
          )}

          {selectedNode.prerequisites.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary" fontWeight={600}>
                Ön koşullar:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.25 }}>
                {selectedNode.prerequisites.map(prereqId => {
                  const prereq = enrichedNodes.find(n => n.id === prereqId);
                  return (
                    <Chip
                      key={prereqId}
                      label={prereq?.name ?? prereqId}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: 10, height: 20 }}
                    />
                  );
                })}
              </Box>
            </Box>
          )}
        </Box>
      )}
    </GlassCard>
  );
}

export default SkillGraphView;

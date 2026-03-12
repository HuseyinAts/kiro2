/**
 * SkillGraphView — Prerequisite DAG skill haritası (ALEKS KST modeli)
 *
 * SVG tabanlı lightweight DAG görselleştirme.
 * - Mastery renk kodlaması: kırmızı (<40%) → sarı (40-79%) → yeşil (≥80%)
 * - Locked node'lar: prerequisite tamamlanmamış → gri + kilit
 * - Edge'ler: prerequisite okları (yönlü)
 * - Tıklanabilir node → detay gösterir
 *
 * No react-flow dependency — pure SVG for minimal bundle impact.
 */

import { useState, useMemo } from 'react';
import { Box, Typography, Chip, Popover } from '@mui/material';
import { Lock, CheckCircle, RadioButtonUnchecked } from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';
import {
  PREREQUISITE_GRAPH,
  CATEGORY_COLORS,
  CATEGORY_LABELS,
  type PrerequisiteNode,
} from './prerequisite-data';
import type { PathNodeData } from './PathNode';

interface SkillGraphViewProps {
  pathNodes: PathNodeData[];
}

/** Map pathNode titles to prerequisite IDs (fuzzy match) */
function buildMasteryMap(pathNodes: PathNodeData[]): Record<string, number> {
  const map: Record<string, number> = {};
  for (const prereq of PREREQUISITE_GRAPH) {
    // Try to find a matching pathNode by title similarity
    const match = pathNodes.find(n => {
      const titleLower = n.title.toLowerCase().replace(/\s+/g, '');
      const prereqLower = prereq.label.toLowerCase().replace(/\s+/g, '');
      return titleLower.includes(prereqLower) || prereqLower.includes(titleLower);
    });
    if (match) {
      map[prereq.id] = match.progress;
    }
    // Default to 0 if no match
    if (!(prereq.id in map)) {
      map[prereq.id] = 0;
    }
  }
  return map;
}

function getMasteryColor(mastery: number): string {
  if (mastery >= 80) return '#22c55e';
  if (mastery >= 40) return '#f59e0b';
  return '#ef4444';
}

function isNodeLocked(nodeId: string, masteryMap: Record<string, number>): boolean {
  const node = PREREQUISITE_GRAPH.find(n => n.id === nodeId);
  if (!node) return false;
  return node.prerequisites.some(prereqId => (masteryMap[prereqId] || 0) < 80);
}

// Layout: assign x/y positions using topological layers
interface LayoutNode extends PrerequisiteNode {
  x: number;
  y: number;
  layer: number;
}

function layoutDAG(): LayoutNode[] {
  const nodeMap = new Map(PREREQUISITE_GRAPH.map(n => [n.id, n]));
  const layers: Map<string, number> = new Map();

  // Topological sort to assign layers
  function getLayer(id: string): number {
    if (layers.has(id)) return layers.get(id)!;
    const node = nodeMap.get(id);
    if (!node || node.prerequisites.length === 0) {
      layers.set(id, 0);
      return 0;
    }
    const maxPrereqLayer = Math.max(...node.prerequisites.map(p => getLayer(p)));
    const layer = maxPrereqLayer + 1;
    layers.set(id, layer);
    return layer;
  }

  PREREQUISITE_GRAPH.forEach(n => getLayer(n.id));

  // Group by layer
  const layerGroups: Map<number, string[]> = new Map();
  layers.forEach((layer, id) => {
    if (!layerGroups.has(layer)) layerGroups.set(layer, []);
    layerGroups.get(layer)!.push(id);
  });

  const NODE_W = 140;
  const NODE_H = 80;
  const PADDING_X = 30;
  const PADDING_Y = 20;

  const layoutNodes: LayoutNode[] = [];

  layerGroups.forEach((ids, layer) => {
    ids.forEach((id, idx) => {
      const node = nodeMap.get(id)!;
      layoutNodes.push({
        ...node,
        layer,
        x: PADDING_X + idx * (NODE_W + 20),
        y: PADDING_Y + layer * (NODE_H + 40),
      });
    });
  });

  return layoutNodes;
}

export function SkillGraphView({ pathNodes }: SkillGraphViewProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [popoverAnchor, setPopoverAnchor] = useState<{ el: SVGElement; node: LayoutNode } | null>(null);

  const masteryMap = useMemo(() => buildMasteryMap(pathNodes), [pathNodes]);
  const layoutNodes = useMemo(() => layoutDAG(), []);

  const nodeMap = useMemo(
    () => new Map(layoutNodes.map(n => [n.id, n])),
    [layoutNodes],
  );

  // SVG dimensions
  const maxX = Math.max(...layoutNodes.map(n => n.x)) + 170;
  const maxY = Math.max(...layoutNodes.map(n => n.y)) + 100;

  const handleNodeClick = (e: React.MouseEvent<SVGGElement>, node: LayoutNode) => {
    setSelectedNode(node.id);
    setPopoverAnchor({ el: e.currentTarget as unknown as SVGElement, node });
  };

  const popoverNode = popoverAnchor?.node;

  return (
    <Box>
      {/* Category legend */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
        {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
          <Chip
            key={key}
            label={label}
            size="small"
            sx={{
              fontWeight: 600,
              fontSize: 11,
              backgroundColor: `${CATEGORY_COLORS[key]}15`,
              color: CATEGORY_COLORS[key],
              borderColor: CATEGORY_COLORS[key],
              borderWidth: 1,
              borderStyle: 'solid',
            }}
          />
        ))}
        <Chip label="≥80% Tamamlandı" size="small" sx={{ fontSize: 11, bgcolor: '#22c55e20', color: '#22c55e' }} />
        <Chip label="40-79%" size="small" sx={{ fontSize: 11, bgcolor: '#f59e0b20', color: '#f59e0b' }} />
        <Chip label="<40%" size="small" sx={{ fontSize: 11, bgcolor: '#ef444420', color: '#ef4444' }} />
      </Box>

      {/* SVG Graph */}
      <GlassCard glassIntensity="light" sx={{ overflow: 'auto', maxHeight: 600 }}>
        <svg
          width={Math.max(maxX, 600)}
          height={Math.max(maxY, 400)}
          style={{ display: 'block' }}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="8"
              markerHeight="6"
              refX="8"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 8 3, 0 6" fill="#94a3b8" />
            </marker>
          </defs>

          {/* Edges */}
          {layoutNodes.map(node =>
            node.prerequisites.map(prereqId => {
              const from = nodeMap.get(prereqId);
              if (!from) return null;
              return (
                <line
                  key={`${prereqId}-${node.id}`}
                  x1={from.x + 65}
                  y1={from.y + 45}
                  x2={node.x + 65}
                  y2={node.y}
                  stroke="#cbd5e1"
                  strokeWidth={1.5}
                  markerEnd="url(#arrowhead)"
                />
              );
            }),
          )}

          {/* Nodes */}
          {layoutNodes.map(node => {
            const mastery = masteryMap[node.id] || 0;
            const locked = isNodeLocked(node.id, masteryMap);
            const color = locked ? '#94a3b8' : getMasteryColor(mastery);
            const catColor = CATEGORY_COLORS[node.category];
            const isSelected = selectedNode === node.id;

            return (
              <g
                key={node.id}
                onClick={(e) => handleNodeClick(e, node)}
                style={{ cursor: 'pointer' }}
              >
                <rect
                  x={node.x}
                  y={node.y}
                  width={130}
                  height={45}
                  rx={8}
                  fill={locked ? '#f1f5f9' : `${color}15`}
                  stroke={isSelected ? catColor : color}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                />
                {/* Category indicator */}
                <rect
                  x={node.x}
                  y={node.y}
                  width={4}
                  height={45}
                  rx={2}
                  fill={catColor}
                />
                {/* Label */}
                <text
                  x={node.x + 65}
                  y={node.y + 19}
                  textAnchor="middle"
                  fontSize={11}
                  fontWeight={600}
                  fill={locked ? '#94a3b8' : '#334155'}
                >
                  {node.label.length > 16 ? node.label.slice(0, 14) + '…' : node.label}
                </text>
                {/* Mastery % or lock */}
                <text
                  x={node.x + 65}
                  y={node.y + 35}
                  textAnchor="middle"
                  fontSize={10}
                  fill={locked ? '#94a3b8' : color}
                  fontWeight={700}
                >
                  {locked ? '🔒 Kilitli' : `%${mastery}`}
                </text>
              </g>
            );
          })}
        </svg>
      </GlassCard>

      {/* Node detail popover */}
      <Popover
        open={Boolean(popoverAnchor)}
        anchorReference="anchorPosition"
        anchorPosition={
          popoverAnchor
            ? { top: (popoverAnchor.el.getBoundingClientRect?.()?.bottom ?? 200) + 8, left: popoverAnchor.el.getBoundingClientRect?.()?.left ?? 200 }
            : undefined
        }
        onClose={() => { setPopoverAnchor(null); setSelectedNode(null); }}
        slotProps={{ paper: { sx: { p: 2, maxWidth: 280, borderRadius: 2 } } }}
      >
        {popoverNode && (() => {
          const mastery = masteryMap[popoverNode.id] || 0;
          const locked = isNodeLocked(popoverNode.id, masteryMap);
          const prereqNodes = popoverNode.prerequisites
            .map(pid => PREREQUISITE_GRAPH.find(n => n.id === pid))
            .filter(Boolean) as PrerequisiteNode[];

          return (
            <Box>
              <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 0.5 }}>
                {popoverNode.label}
              </Typography>
              <Chip
                label={CATEGORY_LABELS[popoverNode.category]}
                size="small"
                sx={{ mb: 1, fontSize: 10, bgcolor: `${CATEGORY_COLORS[popoverNode.category]}15`, color: CATEGORY_COLORS[popoverNode.category] }}
              />

              {/* Mastery */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                {mastery >= 80 ? (
                  <CheckCircle sx={{ fontSize: 16, color: '#22c55e' }} />
                ) : (
                  <RadioButtonUnchecked sx={{ fontSize: 16, color: getMasteryColor(mastery) }} />
                )}
                <Typography variant="body2" fontWeight={600}>
                  Hakimiyet: %{mastery}
                </Typography>
              </Box>

              {/* Prerequisites */}
              {prereqNodes.length > 0 && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="caption" fontWeight={700} color="text.secondary">
                    Neden bu sırada?
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.25, mt: 0.5 }}>
                    {prereqNodes.map(pn => {
                      const pm = masteryMap[pn.id] || 0;
                      return (
                        <Box key={pn.id} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          {pm >= 80 ? (
                            <CheckCircle sx={{ fontSize: 14, color: '#22c55e' }} />
                          ) : (
                            <Lock sx={{ fontSize: 14, color: '#ef4444' }} />
                          )}
                          <Typography variant="caption">
                            {pn.label} — %{pm}
                          </Typography>
                        </Box>
                      );
                    })}
                  </Box>
                </Box>
              )}

              {locked && (
                <Typography variant="caption" color="error" fontWeight={600}>
                  Önkoşulları tamamlayarak kilidi açın
                </Typography>
              )}
            </Box>
          );
        })()}
      </Popover>
    </Box>
  );
}

export default SkillGraphView;

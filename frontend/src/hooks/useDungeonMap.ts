/**
 * useDungeonMap Hook
 *
 * Fetches dungeon map data for a subject and computes dagre layout.
 * Returns rooms with x/y positions, edges, loading state, and refetch.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import dagre from 'dagre';
import { apiRequest } from '@/utils/apiHelpers';
import type {
  DungeonMapResponse,
  DungeonRoom,
  DungeonEdge,
} from '@/types/dungeon';

export interface LayoutNode extends DungeonRoom {
  x: number;
  y: number;
}

export interface LayoutEdge extends DungeonEdge {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
}

interface UseDungeonMapReturn {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  theta: number;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

const NODE_WIDTH = 120;
const NODE_HEIGHT = 90;
const RANK_SEP = 140;
const NODE_SEP = 100;

function computeLayout(
  rooms: DungeonRoom[],
  edges: DungeonEdge[],
): { nodes: LayoutNode[]; edges: LayoutEdge[] } {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'TB', ranksep: RANK_SEP, nodesep: NODE_SEP });
  g.setDefaultEdgeLabel(() => ({}));

  rooms.forEach((r) => {
    g.setNode(r.topic_id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });
  edges.forEach((e) => {
    g.setEdge(e.from_topic, e.to_topic);
  });

  dagre.layout(g);

  const nodeMap = new Map<string, { x: number; y: number }>();
  g.nodes().forEach((id) => {
    const node = g.node(id);
    if (node) {nodeMap.set(id, { x: node.x, y: node.y });}
  });

  const layoutNodes: LayoutNode[] = rooms.map((r) => ({
    ...r,
    x: nodeMap.get(r.topic_id)?.x ?? 0,
    y: nodeMap.get(r.topic_id)?.y ?? 0,
  }));

  const layoutEdges: LayoutEdge[] = edges
    .map((e) => ({
      ...e,
      fromX: nodeMap.get(e.from_topic)?.x ?? 0,
      fromY: nodeMap.get(e.from_topic)?.y ?? 0,
      toX: nodeMap.get(e.to_topic)?.x ?? 0,
      toY: nodeMap.get(e.to_topic)?.y ?? 0,
    }))
    .filter((e) => nodeMap.has(e.from_topic) && nodeMap.has(e.to_topic));

  return { nodes: layoutNodes, edges: layoutEdges };
}

export function useDungeonMap(subject: string): UseDungeonMapReturn {
  const [data, setData] = useState<DungeonMapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMap = useCallback(async () => {
    if (!subject) {return;}
    setLoading(true);
    setError(null);
    try {
      const resp = await apiRequest<DungeonMapResponse>(
        `/api/v1/dungeon/${encodeURIComponent(subject)}`,
      );
      setData(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Harita yuklenemedi');
    } finally {
      setLoading(false);
    }
  }, [subject]);

  useEffect(() => {
    fetchMap();
  }, [fetchMap]);

  const layout = useMemo(() => {
    if (!data) {return { nodes: [], edges: [] };}
    return computeLayout(data.rooms, data.edges);
  }, [data]);

  return {
    nodes: layout.nodes,
    edges: layout.edges,
    theta: data?.theta ?? 0,
    loading,
    error,
    refetch: fetchMap,
  };
}

/**
 * Knowledge Graph Visualization
 * Interactive graph showing topic relationships and learning paths
 */
import axios from 'axios';
import * as React from 'react';
import {  useEffect, useRef, useState  } from 'react';

interface GraphNode {
  id: string;
  label: string;
  type: 'topic' | 'question' | 'kazanim';
  difficulty?: number;
  status?: 'strong' | 'weak' | 'neutral';
  x?: number;
  y?: number;
}

interface GraphEdge {
  source: string;
  target: string;
  relation: 'prerequisite' | 'related' | 'tests';
}

export const KnowledgeGraphViz: React.FC<{ studentId: string }> = ({ studentId }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, _setNodes] = useState<GraphNode[]>([]);
  const [edges, _setEdges] = useState<GraphEdge[]>([]);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    loadGraphData();
  }, [studentId]);

  const loadGraphData = async () => {
    try {
      const [statsRes, _gapsRes] = await Promise.all([
        axios.get('/api/v2/knowledge-graph/stats'),
        axios.get(`/api/v2/knowledge-graph/student/${studentId}/gaps`),
      ]);

      setStats(statsRes.data);
      // Process graph data for visualization
      renderGraph();
    } catch (error) {
      console.error('Graph load failed:', error);
    }
  };

  const renderGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}

    const ctx = canvas.getContext('2d');
    if (!ctx) {return;}

    // Simple force-directed graph rendering
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw nodes
    nodes.forEach(node => {
      ctx.beginPath();
      ctx.arc(node.x || 0, node.y || 0, 20, 0, 2 * Math.PI);
      ctx.fillStyle = node.status === 'weak' ? '#ef4444' : '#10b981';
      ctx.fill();
      ctx.fillStyle = '#000';
      ctx.fillText(node.label, (node.x || 0) + 25, (node.y || 0) + 5);
    });

    // Draw edges
    edges.forEach(edge => {
      const source = nodes.find(n => n.id === edge.source);
      const target = nodes.find(n => n.id === edge.target);
      if (source && target) {
        ctx.beginPath();
        ctx.moveTo(source.x || 0, source.y || 0);
        ctx.lineTo(target.x || 0, target.y || 0);
        ctx.strokeStyle = edge.relation === 'prerequisite' ? '#3b82f6' : '#9ca3af';
        ctx.stroke();
      }
    });
  };

  return (
    <div className="knowledge-graph-viz">
      <h2>Bilgi Haritası</h2>
      {stats && (
        <div className="graph-stats">
          <p>Toplam Node: {stats.total_nodes}</p>
          <p>İlişkiler: {stats.total_edges}</p>
        </div>
      )}
      <canvas ref={canvasRef} width={800} height={600} />
    </div>
  );
};

export default KnowledgeGraphViz;

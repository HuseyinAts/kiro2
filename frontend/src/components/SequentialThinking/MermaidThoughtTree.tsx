/**
 * MermaidThoughtTree Component
 * Mermaid.js based thought tree visualization (REQ-6.2)
 *
 * Renders reasoning steps as an interactive flowchart diagram.
 */

import * as React from 'react';
import {  useEffect, useRef, useState, useCallback  } from 'react';

// Type definitions
interface MermaidThoughtTreeProps {
  mermaidCode: string
  criticalPath?: string[]
  onNodeClick?: (nodeId: string) => void
  className?: string
  theme?: 'default' | 'dark' | 'forest' | 'neutral'
  showControls?: boolean
}

// Store click handlers for cleanup
interface NodeClickHandler {
  node: Element
  handler: () => void
}

// Mermaid configuration
const MERMAID_CONFIG = {
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose' as const,
  flowchart: {
    useMaxWidth: true,
    htmlLabels: true,
    curve: 'basis' as const,
    padding: 20,
    nodeSpacing: 50,
    rankSpacing: 50,
  },
  themeVariables: {
    primaryColor: '#e3f2fd',
    primaryTextColor: '#1a1a1a',
    primaryBorderColor: '#90caf9',
    lineColor: '#64b5f6',
    secondaryColor: '#fff3e0',
    tertiaryColor: '#e8f5e9',
    edgeLabelBackground: '#ffffff',
    fontFamily: 'Inter, system-ui, sans-serif',
  },
};

/**
 * MermaidThoughtTree - Düşünce ağacı görselleştirmesi
 *
 * Mermaid flowchart kullanarak reasoning steps'i interaktif diagram olarak gösterir.
 */
export const MermaidThoughtTree: React.FC<MermaidThoughtTreeProps> = ({
  mermaidCode,
  criticalPath = [],
  onNodeClick,
  className = '',
  theme = 'default',
  showControls = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mermaidLoaded, setMermaidLoaded] = useState(false);
  const [zoom, setZoom] = useState(1);
  // Track click handlers for cleanup (memory leak fix)
  const clickHandlersRef = useRef<NodeClickHandler[]>([]);

  // Load Mermaid library dynamically
  useEffect(() => {
    let isMounted = true;

    const loadMermaid = async () => {
      try {
        // Check if mermaid is already loaded
        if ((window as unknown as { mermaid?: unknown }).mermaid) {
          if (isMounted) {
            setMermaidLoaded(true);
          }
          return;
        }

        // Dynamic import
        const mermaidModule = await import('mermaid');
        const mermaid = mermaidModule.default;

        // Initialize with config
        mermaid.initialize({
          ...MERMAID_CONFIG,
          theme: theme,
        })

        // Store in window for reuse
        ;(window as unknown as { mermaid: typeof mermaid }).mermaid = mermaid;
        if (isMounted) {
          setMermaidLoaded(true);
        }
      } catch (err) {
        console.error('Failed to load Mermaid:', err);
        if (isMounted) {
          setError('Mermaid kutuphanesi yuklenemedi');
          setIsLoading(false);
        }
      }
    };

    loadMermaid();

    // Cleanup function
    return () => {
      isMounted = false;
    };
  }, [theme]);

  // Helper function to cleanup click handlers
  const cleanupClickHandlers = useCallback(() => {
    clickHandlersRef.current.forEach(({ node, handler }) => {
      node.removeEventListener('click', handler);
    });
    clickHandlersRef.current = [];
  }, []);

  // Render diagram when mermaid code changes
  const renderDiagram = useCallback(async () => {
    if (!containerRef.current || !mermaidLoaded || !mermaidCode) {
      return;
    }

    setIsLoading(true);
    setError(null);

    // Cleanup previous click handlers before re-rendering (memory leak fix)
    cleanupClickHandlers();

    try {
      const mermaid = (window as unknown as { mermaid: { render: (id: string, code: string) => Promise<{ svg: string }> } }).mermaid;

      // Generate unique ID for this render
      const id = `mermaid-${Date.now()}`;

      // Render the diagram
      const { svg } = await mermaid.render(id, mermaidCode);

      // Insert SVG into container
      if (containerRef.current) {
        containerRef.current.innerHTML = svg;

        // Add click handlers to nodes if callback provided
        if (onNodeClick) {
          const nodes = containerRef.current.querySelectorAll('.node');
          nodes.forEach((node) => {
            const handler = () => {
              const nodeId = node.id || node.getAttribute('data-id');
              if (nodeId) {
                onNodeClick(nodeId);
              }
            };
            node.addEventListener('click', handler);
            // Track handler for cleanup (memory leak fix)
            clickHandlersRef.current.push({ node, handler })
            ;(node as HTMLElement).style.cursor = 'pointer';
          });
        }

        // Highlight critical path nodes
        if (criticalPath.length > 0) {
          criticalPath.forEach((nodeId) => {
            const node = containerRef.current?.querySelector(`#${nodeId}`);
            if (node) {
              node.classList.add('critical-path');
            }
          });
        }
      }

      setIsLoading(false);
    } catch (err) {
      console.error('Mermaid render error:', err);
      setError('Diagram olusturulamadi');
      setIsLoading(false);
    }
  }, [mermaidCode, mermaidLoaded, onNodeClick, criticalPath, cleanupClickHandlers]);

  useEffect(() => {
    if (mermaidLoaded) {
      renderDiagram();
    }
  }, [mermaidLoaded, renderDiagram]);

  // Cleanup on unmount (memory leak fix)
  useEffect(() => {
    return () => {
      // Remove all click handlers
      clickHandlersRef.current.forEach(({ node, handler }) => {
        node.removeEventListener('click', handler);
      });
      clickHandlersRef.current = [];

      // Clear container content
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, []);

  // Zoom controls
  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.1, 2));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.1, 0.5));
  const handleZoomReset = () => setZoom(1);

  // Render fallback if mermaid not loaded
  if (!mermaidLoaded && !error) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="animate-pulse flex flex-col items-center gap-2">
          <div className="w-12 h-12 bg-blue-100 rounded-full" />
          <span className="text-sm text-gray-500">Mermaid yukleniyor...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`mermaid-thought-tree ${className}`}>
      {/* Controls */}
      {showControls && (
        <div className="flex items-center justify-between p-2 border-b bg-gray-50 rounded-t-lg">
          <span className="text-sm text-gray-600">Dusunce Agaci</span>
          <div className="flex items-center gap-2">
            <button
              onClick={handleZoomOut}
              className="p-1 hover:bg-gray-200 rounded"
              title="Kucult"
              aria-label="Küçült"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
            <span className="text-xs text-gray-500 w-12 text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1 hover:bg-gray-200 rounded"
              title="Buyut"
              aria-label="Büyüt"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button
              onClick={handleZoomReset}
              className="p-1 hover:bg-gray-200 rounded text-xs"
              title="Sifirla"
            >
              Reset
            </button>
          </div>
        </div>
      )}

      {/* Diagram container */}
      <div
        className="mermaid-container overflow-auto bg-white border rounded-b-lg"
        style={{
          minHeight: '200px',
          maxHeight: '600px',
        }}
      >
        {isLoading && (
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center p-8 text-red-500">
            <span>{error}</span>
          </div>
        )}

        <div
          ref={containerRef}
          className="mermaid-svg-container p-4"
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: 'top left',
            transition: 'transform 0.2s ease',
          }}
        />
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 p-2 text-xs text-gray-500 border-t">
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 bg-blue-100 rounded" />
          <span>Baslangic</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 bg-green-100 rounded" />
          <span>Dogrulandi</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 bg-orange-100 rounded" />
          <span>Kritik Yol</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 bg-green-300 rounded" />
          <span>Sonuc</span>
        </div>
      </div>

      {/* Styles */}
      <style>{`
        .mermaid-thought-tree .node {
          transition: all 0.2s ease;
        }
        .mermaid-thought-tree .node:hover {
          filter: brightness(0.95);
        }
        .mermaid-thought-tree .critical-path rect,
        .mermaid-thought-tree .critical-path polygon {
          stroke: #f57c00 !important;
          stroke-width: 2px !important;
        }
        .mermaid-thought-tree .edgePath path {
          stroke-width: 2px;
        }
      `}</style>
    </div>
  );
};

/**
 * MermaidCodePreview - Mermaid kod onizlemesi
 * Debugging ve development icin kullanilir.
 */
export const MermaidCodePreview: React.FC<{ code: string }> = ({ code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Copy failed:', err);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800">
        <span className="text-xs text-gray-400">Mermaid Kodu</span>
        <button
          onClick={handleCopy}
          className="text-xs text-gray-400 hover:text-white"
        >
          {copied ? 'Kopyalandi!' : 'Kopyala'}
        </button>
      </div>
      <pre className="p-4 text-sm text-gray-300 overflow-auto max-h-64">
        <code>{code}</code>
      </pre>
    </div>
  );
};

export default MermaidThoughtTree;

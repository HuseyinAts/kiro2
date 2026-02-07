/**
 * QuestionGraph Component
 *
 * Renders SVG graphs from visual_content for ÖSYM-style questions.
 * Phase 2: Graphs implementation.
 *
 * Features:
 * - Renders SVG graphs (line, bar, pie, scatter, histogram)
 * - Responsive design (mobile + desktop)
 * - WCAG 2.1 AA accessibility compliant
 * - Print-friendly styles
 * - Proper Turkish language support
 */

import * as React from 'react';

import { sanitizeSVG } from '../utils/sanitize';
import './QuestionGraph.css';

interface GraphMetadata {
  graph_type: string;
  title: string;
  x_label: string;
  y_label: string;
  description: string;
}

interface VisualContent {
  type: string;
  format: string;
  content: string;  // SVG markup
  data?: any;
  metadata: GraphMetadata;
}

interface QuestionGraphProps {
  visualContent: VisualContent;
  className?: string;
}

/**
 * QuestionGraph Component
 */
export const QuestionGraph: React.FC<QuestionGraphProps> = ({
  visualContent,
  className = '',
}) => {
  if (!visualContent || visualContent.type !== 'graph') {
    return null;
  }

  // SECURITY FIX #4: Use DOMPurify for secure SVG sanitization
  const sanitizedSVG = sanitizeSVG(visualContent.content);

  return (
    <figure className={`question-graph-wrapper ${className}`}>
      {/* Caption */}
      {visualContent.metadata.title && (
        <figcaption className="question-graph-caption">
          {visualContent.metadata.title}
        </figcaption>
      )}

      {/* Graph SVG */}
      <div
        className="question-graph-container"
        role="img"
        aria-label={visualContent.metadata.description || visualContent.metadata.title}
      >
        <div
          className="question-graph-svg"
          dangerouslySetInnerHTML={{ __html: sanitizedSVG }}
        />
      </div>

      {/* Metadata for screen readers */}
      <div className="sr-only" aria-live="polite">
        Grafik türü: {visualContent.metadata.graph_type}
        {visualContent.metadata.x_label && `, X ekseni: ${visualContent.metadata.x_label}`}
        {visualContent.metadata.y_label && `, Y ekseni: ${visualContent.metadata.y_label}`}
      </div>
    </figure>
  );
};

export default QuestionGraph;

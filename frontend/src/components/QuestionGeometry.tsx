/**
 * QuestionGeometry Component
 *
 * Renders SVG geometric figures from visual_content for ÖSYM-style questions.
 * Phase 3: Geometry implementation.
 *
 * Features:
 * - Renders SVG geometry (triangles, circles, quadrilaterals, polygons, 3D shapes)
 * - Responsive design (mobile + desktop)
 * - WCAG 2.1 AA accessibility compliant
 * - Print-friendly styles
 * - Proper Turkish language support
 */

import * as React from 'react';

import { sanitizeSVG } from '../utils/sanitize';
import './QuestionGeometry.css';

interface GeometryMetadata {
  geometry_type: string;
  shape_subtype: string;
  dimensions: Record<string, number>;
  description: string;
}

interface VisualContent {
  type: string;
  format: string;
  content: string;  // SVG markup
  data?: any;
  metadata: GeometryMetadata;
}

interface QuestionGeometryProps {
  visualContent: VisualContent;
  className?: string;
}

/**
 * QuestionGeometry Component
 */
export const QuestionGeometry: React.FC<QuestionGeometryProps> = ({
  visualContent,
  className = '',
}) => {
  if (!visualContent || visualContent.type !== 'geometry') {
    return null;
  }

  // SECURITY FIX #4: Use DOMPurify for secure SVG sanitization
  const sanitizedSVG = sanitizeSVG(visualContent.content);

  // Format dimension text for display
  const formatDimensions = (dimensions: Record<string, number>): string => {
    return Object.entries(dimensions)
      .map(([key, value]) => {
        // Translate keys to Turkish
        const translations: Record<string, string> = {
          'base': 'Taban',
          'height': 'Yükseklik',
          'side': 'Kenar',
          'radius': 'Yarıçap',
          'width': 'Genişlik',
          'depth': 'Derinlik',
          'angle': 'Açı',
          'equal_side': 'Eşit Kenar',
        };
        const label = translations[key] || key;
        return `${label}: ${value}${key === 'angle' ? '°' : ' cm'}`;
      })
      .join(', ');
  };

  return (
    <figure className={`question-geometry-wrapper ${className}`}>
      {/* Caption with shape information */}
      <figcaption className="question-geometry-caption">
        Şekil: {visualContent.metadata.shape_subtype.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
      </figcaption>

      {/* Geometry SVG */}
      <div
        className="question-geometry-container"
        role="img"
        aria-label={visualContent.metadata.description}
      >
        <div
          className="question-geometry-svg"
          dangerouslySetInnerHTML={{ __html: sanitizedSVG }}
        />
      </div>

      {/* Dimension information */}
      <div className="question-geometry-info">
        {formatDimensions(visualContent.metadata.dimensions)}
      </div>

      {/* Metadata for screen readers */}
      <div className="sr-only" aria-live="polite">
        Geometrik şekil türü: {visualContent.metadata.geometry_type}
        {', '}
        Alt tip: {visualContent.metadata.shape_subtype}
        {', '}
        Boyutlar: {formatDimensions(visualContent.metadata.dimensions)}
      </div>
    </figure>
  );
};

export default QuestionGeometry;

/**
 * QuestionMapDiagram Component
 *
 * Renders SVG maps and diagrams from visual_content for ÖSYM-style questions.
 * Phase 4: Maps & Diagrams implementation.
 *
 * Features:
 * - Renders SVG maps/diagrams (geographic maps, flowcharts, Venn diagrams, timelines)
 * - Responsive design (mobile + desktop)
 * - WCAG 2.1 AA accessibility compliant
 * - Print-friendly styles
 * - Proper Turkish language support
 */

import * as React from 'react';

import { sanitizeSVG } from '../utils/sanitize';
import './QuestionMapDiagram.css';

interface DiagramMetadata {
  diagram_type: string;
  diagram_subtype: string;
  description: string;
  [key: string]: any;
}

interface VisualContent {
  type: string;
  format: string;
  content: string;  // SVG markup
  metadata: DiagramMetadata;
}

interface QuestionMapDiagramProps {
  visualContent: VisualContent;
  className?: string;
}

/**
 * QuestionMapDiagram Component
 */
export const QuestionMapDiagram: React.FC<QuestionMapDiagramProps> = ({
  visualContent,
  className = '',
}) => {
  if (!visualContent || visualContent.type !== 'map_diagram') {
    return null;
  }

  // SECURITY FIX #4: Use DOMPurify for secure SVG sanitization
  const sanitizedSVG = sanitizeSVG(visualContent.content);

  // Format diagram title
  const getDiagramTitle = (): string => {
    const subtype = visualContent.metadata.diagram_subtype || '';
    const typeMap: Record<string, string> = {
      'turkey_regions': 'Türkiye Coğrafi Bölgeleri',
      'turkey_cities': 'Türkiye Büyük Şehirleri',
      'continents': 'Dünya Kıtaları',
      'flowchart': 'Akış Diyagramı',
      'cycle_diagram': 'Döngü Diyagramı',
      'system_diagram': 'Sistem Diyagramı',
      'tree_diagram': 'Sınıflandırma Ağacı',
      'venn_diagram': 'Venn Diyagramı',
      'matrix_diagram': 'Karşılaştırma Matrisi',
      'organizational_chart': 'Organizasyon Şeması',
      'horizontal_timeline': 'Zaman Çizelgesi',
      'vertical_timeline': 'Zaman Çizelgesi',
    };
    return typeMap[subtype] || 'Diyagram';
  };

  return (
    <figure className={`question-map-diagram-wrapper ${className}`}>
      {/* Caption with diagram information */}
      <figcaption className="question-map-diagram-caption">
        {getDiagramTitle()}
      </figcaption>

      {/* Map/Diagram SVG */}
      <div
        className="question-map-diagram-container"
        role="img"
        aria-label={visualContent.metadata.description}
      >
        <div
          className="question-map-diagram-svg"
          dangerouslySetInnerHTML={{ __html: sanitizedSVG }}
        />
      </div>

      {/* Metadata for screen readers */}
      <div className="sr-only" aria-live="polite">
        Diyagram türü: {visualContent.metadata.diagram_type}
        {', '}
        Alt tip: {visualContent.metadata.diagram_subtype}
        {', '}
        Açıklama: {visualContent.metadata.description}
      </div>
    </figure>
  );
};

export default QuestionMapDiagram;

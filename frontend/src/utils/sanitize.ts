/**
 * HTML/SVG Sanitization Utilities
 *
 * SECURITY FIX #4: XSS Prevention with DOMPurify
 *
 * Uses DOMPurify library for secure HTML/SVG sanitization.
 * This replaces the insecure regex-based sanitization.
 *
 * @see https://github.com/cure53/DOMPurify
 */

import DOMPurify from 'dompurify';

/**
 * Default DOMPurify configuration for general HTML
 */
const DEFAULT_HTML_CONFIG: DOMPurify.Config = {
  ALLOWED_TAGS: [
    'b', 'i', 'em', 'strong', 'u', 'span', 'div', 'p', 'br', 'hr',
    'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'thead', 'tbody',
    'sup', 'sub', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'code', 'pre', 'blockquote', 'a',
  ],
  ALLOWED_ATTR: ['class', 'id', 'style', 'href', 'target', 'rel'],
  ALLOW_DATA_ATTR: false,
  USE_PROFILES: { html: true },
};

/**
 * DOMPurify configuration for SVG content
 */
const SVG_CONFIG: DOMPurify.Config = {
  USE_PROFILES: { svg: true, svgFilters: true },
  ALLOWED_TAGS: [
    'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline',
    'polygon', 'text', 'tspan', 'defs', 'clipPath', 'mask', 'use',
    'linearGradient', 'radialGradient', 'stop', 'pattern', 'image',
    'title', 'desc', 'marker', 'symbol', 'filter', 'feGaussianBlur',
    'feOffset', 'feMerge', 'feMergeNode', 'foreignObject',
  ],
  ALLOWED_ATTR: [
    'class', 'id', 'style', 'fill', 'stroke', 'stroke-width', 'stroke-dasharray',
    'stroke-linecap', 'stroke-linejoin', 'opacity', 'fill-opacity', 'stroke-opacity',
    'd', 'points', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
    'width', 'height', 'viewBox', 'preserveAspectRatio', 'transform',
    'font-family', 'font-size', 'font-weight', 'text-anchor', 'dominant-baseline',
    'dx', 'dy', 'offset', 'stop-color', 'stop-opacity', 'gradientUnits',
    'spreadMethod', 'patternUnits', 'patternContentUnits', 'clipPathUnits',
    'href', 'xlink:href', 'markerWidth', 'markerHeight', 'refX', 'refY',
    'orient', 'markerUnits', 'stdDeviation', 'result', 'in', 'in2',
    'role', 'aria-label', 'aria-labelledby', 'aria-describedby',
  ],
  ALLOW_DATA_ATTR: false,
};

/**
 * DOMPurify configuration for MathML content
 */
const MATHML_CONFIG: DOMPurify.Config = {
  USE_PROFILES: { mathMl: true },
  ALLOWED_TAGS: [
    'math', 'mi', 'mn', 'mo', 'ms', 'mtext', 'mspace', 'mrow', 'mfrac',
    'msqrt', 'mroot', 'mtable', 'mtr', 'mtd', 'msup', 'msub', 'msubsup',
    'munder', 'mover', 'munderover', 'mmultiscripts', 'mprescripts',
    'mstyle', 'menclose', 'mfenced', 'mpadded', 'mphantom', 'merror',
    'semantics', 'annotation', 'annotation-xml',
  ],
  ALLOWED_ATTR: [
    'class', 'id', 'style', 'mathvariant', 'mathsize', 'mathcolor',
    'mathbackground', 'displaystyle', 'scriptlevel', 'lspace', 'rspace',
    'stretchy', 'form', 'fence', 'separator', 'accent', 'accentunder',
    'linethickness', 'notation', 'open', 'close', 'separators',
    'rowalign', 'columnalign', 'rowspacing', 'columnspacing', 'rowlines',
    'columnlines', 'frame', 'framespacing', 'equalrows', 'equalcolumns',
    'encoding', 'href', 'alttext', 'xmlns',
  ],
  ALLOW_DATA_ATTR: false,
};

/**
 * Sanitize general HTML content
 *
 * @param dirty - Potentially unsafe HTML string
 * @param extraConfig - Additional DOMPurify configuration
 * @returns Sanitized HTML string safe for dangerouslySetInnerHTML
 */
export function sanitizeHTML(dirty: string, extraConfig?: Record<string, unknown>): string {
  if (!dirty || typeof dirty !== 'string') {
    return '';
  }

  const config = extraConfig
    ? { ...DEFAULT_HTML_CONFIG, ...extraConfig }
    : DEFAULT_HTML_CONFIG;

  return DOMPurify.sanitize(dirty, config as Parameters<typeof DOMPurify.sanitize>[1]);
}

/**
 * Sanitize SVG content
 *
 * @param dirty - Potentially unsafe SVG string
 * @param extraConfig - Additional DOMPurify configuration
 * @returns Sanitized SVG string safe for dangerouslySetInnerHTML
 */
export function sanitizeSVG(dirty: string, extraConfig?: Record<string, unknown>): string {
  if (!dirty || typeof dirty !== 'string') {
    return '';
  }

  const config = extraConfig
    ? { ...SVG_CONFIG, ...extraConfig }
    : SVG_CONFIG;

  return DOMPurify.sanitize(dirty, config as Parameters<typeof DOMPurify.sanitize>[1]);
}

/**
 * Sanitize MathML content
 *
 * @param dirty - Potentially unsafe MathML string
 * @param extraConfig - Additional DOMPurify configuration
 * @returns Sanitized MathML string safe for dangerouslySetInnerHTML
 */
export function sanitizeMathML(dirty: string, extraConfig?: Record<string, unknown>): string {
  if (!dirty || typeof dirty !== 'string') {
    return '';
  }

  const config = extraConfig
    ? { ...MATHML_CONFIG, ...extraConfig }
    : MATHML_CONFIG;

  return DOMPurify.sanitize(dirty, config as Parameters<typeof DOMPurify.sanitize>[1]);
}

/**
 * Sanitize bionic reading text (bold first letters)
 *
 * @param dirty - Potentially unsafe HTML string
 * @returns Sanitized HTML string safe for dangerouslySetInnerHTML
 */
export function sanitizeBionicText(dirty: string): string {
  if (!dirty || typeof dirty !== 'string') {
    return '';
  }

  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'strong', 'span', 'br', 'p', 'div'],
    ALLOWED_ATTR: ['class', 'style'],
    ALLOW_DATA_ATTR: false,
  });
}

/**
 * Strip all HTML tags, returning plain text
 *
 * @param dirty - HTML string to strip
 * @returns Plain text without HTML
 */
export function stripHTML(dirty: string): string {
  if (!dirty || typeof dirty !== 'string') {
    return '';
  }

  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: [],
  });
}

/**
 * Check if a string contains potentially dangerous content
 *
 * @param content - String to check
 * @returns true if content appears safe, false otherwise
 */
export function isContentSafe(content: string): boolean {
  if (!content || typeof content !== 'string') {
    return true;
  }

  const sanitized = DOMPurify.sanitize(content);
  return sanitized === content;
}

// Export DOMPurify for advanced usage
export { DOMPurify };

// Default export for convenience
export default {
  sanitizeHTML,
  sanitizeSVG,
  sanitizeMathML,
  sanitizeBionicText,
  stripHTML,
  isContentSafe,
  DOMPurify,
};

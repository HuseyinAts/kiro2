/**
 * Whiteboard Module Exports
 *
 * Central export file for all whiteboard components and utilities.
 */

// Main component
export { default as CollaborativeWhiteboard } from './CollaborativeWhiteboard';
export { default } from './CollaborativeWhiteboard';

// Sub-components
export { default as WhiteboardToolbar } from './WhiteboardToolbar';
export { default as WhiteboardCanvas } from './WhiteboardCanvas';
export { default as WhiteboardSync, useWhiteboardSync, createEmptyState, serializeState, deserializeState } from './WhiteboardSync';
export { default as TextEditor, createTextElement, createEquationElement, renderText, renderEquation, measureText, LATEX_TEMPLATES } from './TextEditor';

// Shape tools (utility functions)
export {
  default as ShapeTools,
  createShape,
  calculateCircleRadius,
  calculateArrowAngle,
  getArrowheadPoints,
  getShapeBoundingBox,
  isPointInShape,
  drawRectangle,
  drawCircle,
  drawLine,
  drawArrow,
  moveShape,
  scaleShape,
} from './ShapeTools';

// Types
export type {
  Point,
  DrawingTool,
  ShapeType,
  WhiteboardTool,
  Stroke,
  Shape,
  TextElement,
  EquationElement,
  WhiteboardState,
  CollaborativeWhiteboardProps,
  WhiteboardToolbarProps,
  WhiteboardCanvasProps,
  TextEditorProps,
  ShapeToolsProps,
  WhiteboardMessageType,
  WhiteboardMessage,
  WhiteboardSyncProps,
} from './types';

// Constants
export {
  DEFAULT_COLORS,
  DEFAULT_STROKE_WIDTH,
  DEFAULT_FONT_SIZE,
  MIN_STROKE_WIDTH,
  MAX_STROKE_WIDTH,
  MIN_ZOOM,
  MAX_ZOOM,
  ZOOM_STEP,
} from './types';

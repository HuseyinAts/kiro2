/**
 * CollaborativeWhiteboard Re-export Wrapper
 *
 * DEPRECATED: This file is maintained for backwards compatibility.
 * Please import from './Whiteboard' instead.
 *
 * Refactored structure:
 * - Whiteboard/CollaborativeWhiteboard.tsx - Main orchestrator (~200 lines)
 * - Whiteboard/WhiteboardToolbar.tsx - Toolbar component (~200 lines)
 * - Whiteboard/WhiteboardCanvas.tsx - Canvas rendering (~200 lines)
 * - Whiteboard/ShapeTools.tsx - Shape utilities (~180 lines)
 * - Whiteboard/TextEditor.tsx - Text/LaTeX editor (~150 lines)
 * - Whiteboard/WhiteboardSync.tsx - WebSocket sync (~180 lines)
 * - Whiteboard/types.ts - Type definitions (~140 lines)
 * - Whiteboard/index.tsx - Exports
 *
 * Migration: Replace imports with:
 * import { CollaborativeWhiteboard } from './Whiteboard';
 */

export { default } from './Whiteboard';
export { CollaborativeWhiteboard } from './Whiteboard';

// Re-export all types and utilities for backwards compatibility
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
} from './Whiteboard';

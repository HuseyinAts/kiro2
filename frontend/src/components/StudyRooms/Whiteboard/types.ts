/**
 * Whiteboard Types
 *
 * Type definitions for the collaborative whiteboard system.
 * Extracted from CollaborativeWhiteboard.tsx for better maintainability.
 */

// ============================================================
// Basic Types
// ============================================================

export interface Point {
  x: number;
  y: number;
}

// ============================================================
// Drawing Types
// ============================================================

export type DrawingTool = 'pen' | 'highlighter' | 'eraser';
export type ShapeType = 'rectangle' | 'circle' | 'line' | 'arrow';
export type WhiteboardTool = DrawingTool | 'shape' | 'text' | 'equation' | 'pan';

export interface Stroke {
  id: string;
  tool: DrawingTool;
  points: Point[];
  color: string;
  width: number;
  opacity: number;
}

export interface Shape {
  id: string;
  type: ShapeType;
  start: Point;
  end: Point;
  color: string;
  width: number;
  fill?: boolean;
}

// ============================================================
// Text and Equation Types
// ============================================================

export interface TextElement {
  id: string;
  position: Point;
  content: string;
  fontSize: number;
  color: string;
  fontFamily: string;
}

export interface EquationElement {
  id: string;
  position: Point;
  latex: string;
  fontSize: number;
  color: string;
}

// ============================================================
// Whiteboard State
// ============================================================

export interface WhiteboardState {
  strokes: Stroke[];
  shapes: Shape[];
  texts: TextElement[];
  equations: EquationElement[];
}

// ============================================================
// Component Props
// ============================================================

export interface CollaborativeWhiteboardProps {
  roomId: string;
  currentUserId: string;
}

export interface WhiteboardToolbarProps {
  tool: WhiteboardTool;
  shapeType: ShapeType;
  color: string;
  strokeWidth: number;
  zoom: number;
  canUndo: boolean;
  onToolChange: (tool: WhiteboardTool) => void;
  onShapeTypeChange: (shapeType: ShapeType) => void;
  onColorChange: (color: string) => void;
  onStrokeWidthChange: (width: number) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onUndo: () => void;
  onClear: () => void;
  onSave: () => void;
}

export interface WhiteboardCanvasProps {
  tool: WhiteboardTool;
  shapeType: ShapeType;
  color: string;
  strokeWidth: number;
  zoom: number;
  pan: Point;
  whiteboardState: WhiteboardState;
  currentStroke: Point[];
  currentShape: { start: Point; end: Point } | null;
  isDrawing: boolean;
  onMouseDown: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  onMouseMove: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  onMouseUp: () => void;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  containerRef: React.RefObject<HTMLDivElement>;
}

export interface TextEditorProps {
  position: Point;
  zoom: number;
  pan: Point;
  textInput: string;
  latexInput: string;
  tool: 'text' | 'equation';
  onTextChange: (text: string) => void;
  onLatexChange: (latex: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

export interface ShapeToolsProps {
  shapeType: ShapeType;
  onShapeTypeChange: (shapeType: ShapeType) => void;
}

// ============================================================
// WebSocket Types
// ============================================================

export type WhiteboardMessageType =
  | 'stroke-added'
  | 'shape-added'
  | 'text-added'
  | 'equation-added'
  | 'clear';

export interface WhiteboardMessage {
  type: WhiteboardMessageType;
  stroke?: Stroke;
  shape?: Shape;
  text?: TextElement;
  equation?: EquationElement;
}

export interface WhiteboardSyncProps {
  roomId: string;
  onStrokeAdded: (stroke: Stroke) => void;
  onShapeAdded: (shape: Shape) => void;
  onTextAdded: (text: TextElement) => void;
  onEquationAdded: (equation: EquationElement) => void;
  onClear: () => void;
}

// ============================================================
// Constants
// ============================================================

export const DEFAULT_COLORS = [
  '#000000', // Black
  '#FF0000', // Red
  '#00FF00', // Green
  '#0000FF', // Blue
  '#FFFF00', // Yellow
  '#FF00FF', // Magenta
  '#00FFFF', // Cyan
  '#FFA500', // Orange
  '#800080', // Purple
  '#FFFFFF', // White
] as const;

export const DEFAULT_STROKE_WIDTH = 2;
export const DEFAULT_FONT_SIZE = 16;
export const MIN_STROKE_WIDTH = 1;
export const MAX_STROKE_WIDTH = 20;
export const MIN_ZOOM = 0.5;
export const MAX_ZOOM = 3;
export const ZOOM_STEP = 0.1;

/**
 * ShapeTools Component
 *
 * Shape drawing utilities and helpers for the whiteboard.
 * Provides shape creation, manipulation, and rendering functions.
 */

import { Point, Shape, ShapeType } from './types';

// ============================================================
// Shape Creation Functions
// ============================================================

/**
 * Create a new shape with the given parameters
 */
export const createShape = (
  type: ShapeType,
  start: Point,
  end: Point,
  color: string,
  width: number,
  fill: boolean = false,
): Shape => ({
  id: `shape-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
  type,
  start,
  end,
  color,
  width,
  fill,
});

// ============================================================
// Shape Calculation Helpers
// ============================================================

/**
 * Calculate the radius for a circle shape
 */
export const calculateCircleRadius = (start: Point, end: Point): number => {
  return Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2));
};

/**
 * Calculate the angle for arrow direction
 */
export const calculateArrowAngle = (start: Point, end: Point): number => {
  return Math.atan2(end.y - start.y, end.x - start.x);
};

/**
 * Get arrowhead points for drawing
 */
export const getArrowheadPoints = (
  end: Point,
  angle: number,
  size: number = 15,
): { left: Point; right: Point } => {
  return {
    left: {
      x: end.x - size * Math.cos(angle - Math.PI / 6),
      y: end.y - size * Math.sin(angle - Math.PI / 6),
    },
    right: {
      x: end.x - size * Math.cos(angle + Math.PI / 6),
      y: end.y - size * Math.sin(angle + Math.PI / 6),
    },
  };
};

// ============================================================
// Bounding Box Helpers
// ============================================================

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Get bounding box for a shape
 */
export const getShapeBoundingBox = (shape: Shape): BoundingBox => {
  switch (shape.type) {
    case 'rectangle':
      return {
        x: Math.min(shape.start.x, shape.end.x),
        y: Math.min(shape.start.y, shape.end.y),
        width: Math.abs(shape.end.x - shape.start.x),
        height: Math.abs(shape.end.y - shape.start.y),
      };

    case 'circle': {
      const radius = calculateCircleRadius(shape.start, shape.end);
      return {
        x: shape.start.x - radius,
        y: shape.start.y - radius,
        width: radius * 2,
        height: radius * 2,
      };
    }

    case 'line':
    case 'arrow':
      return {
        x: Math.min(shape.start.x, shape.end.x),
        y: Math.min(shape.start.y, shape.end.y),
        width: Math.abs(shape.end.x - shape.start.x),
        height: Math.abs(shape.end.y - shape.start.y),
      };

    default:
      return { x: 0, y: 0, width: 0, height: 0 };
  }
};

/**
 * Check if a point is inside a shape's bounding box
 */
export const isPointInShape = (point: Point, shape: Shape, tolerance: number = 5): boolean => {
  const bbox = getShapeBoundingBox(shape);

  return (
    point.x >= bbox.x - tolerance &&
    point.x <= bbox.x + bbox.width + tolerance &&
    point.y >= bbox.y - tolerance &&
    point.y <= bbox.y + bbox.height + tolerance
  );
};

// ============================================================
// Shape Drawing Functions
// ============================================================

/**
 * Draw a rectangle on canvas context
 */
export const drawRectangle = (
  ctx: CanvasRenderingContext2D,
  start: Point,
  end: Point,
  color: string,
  width: number,
  fill: boolean = false,
): void => {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.strokeRect(start.x, start.y, end.x - start.x, end.y - start.y);

  if (fill) {
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.3;
    ctx.fillRect(start.x, start.y, end.x - start.x, end.y - start.y);
    ctx.globalAlpha = 1;
  }
};

/**
 * Draw a circle on canvas context
 */
export const drawCircle = (
  ctx: CanvasRenderingContext2D,
  center: Point,
  end: Point,
  color: string,
  width: number,
  fill: boolean = false,
): void => {
  const radius = calculateCircleRadius(center, end);
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.arc(center.x, center.y, radius, 0, 2 * Math.PI);
  ctx.stroke();

  if (fill) {
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.3;
    ctx.fill();
    ctx.globalAlpha = 1;
  }
};

/**
 * Draw a line on canvas context
 */
export const drawLine = (
  ctx: CanvasRenderingContext2D,
  start: Point,
  end: Point,
  color: string,
  width: number,
): void => {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();
};

/**
 * Draw an arrow on canvas context
 */
export const drawArrow = (
  ctx: CanvasRenderingContext2D,
  start: Point,
  end: Point,
  color: string,
  width: number,
  arrowSize: number = 15,
): void => {
  // Draw the line
  drawLine(ctx, start, end, color, width);

  // Draw the arrowhead
  const angle = calculateArrowAngle(start, end);
  const arrowPoints = getArrowheadPoints(end, angle, arrowSize);

  ctx.beginPath();
  ctx.moveTo(end.x, end.y);
  ctx.lineTo(arrowPoints.left.x, arrowPoints.left.y);
  ctx.moveTo(end.x, end.y);
  ctx.lineTo(arrowPoints.right.x, arrowPoints.right.y);
  ctx.stroke();
};

// ============================================================
// Shape Transformation Functions
// ============================================================

/**
 * Move a shape by delta
 */
export const moveShape = (shape: Shape, delta: Point): Shape => ({
  ...shape,
  start: { x: shape.start.x + delta.x, y: shape.start.y + delta.y },
  end: { x: shape.end.x + delta.x, y: shape.end.y + delta.y },
});

/**
 * Scale a shape from center
 */
export const scaleShape = (shape: Shape, scale: number): Shape => {
  const centerX = (shape.start.x + shape.end.x) / 2;
  const centerY = (shape.start.y + shape.end.y) / 2;

  const newStart = {
    x: centerX + (shape.start.x - centerX) * scale,
    y: centerY + (shape.start.y - centerY) * scale,
  };

  const newEnd = {
    x: centerX + (shape.end.x - centerX) * scale,
    y: centerY + (shape.end.y - centerY) * scale,
  };

  return { ...shape, start: newStart, end: newEnd };
};

export default {
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
};

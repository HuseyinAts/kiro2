/**
 * WhiteboardCanvas Component
 *
 * Canvas rendering component for the collaborative whiteboard.
 * Handles drawing strokes, shapes, text, and equations.
 */

import { Box } from '@mui/material';
import * as React from 'react';
import {  useEffect, useCallback  } from 'react';

import { WhiteboardCanvasProps, Point, Stroke, Shape } from './types';

const WhiteboardCanvas: React.FC<WhiteboardCanvasProps> = ({
  tool,
  shapeType,
  color,
  strokeWidth,
  zoom,
  pan,
  whiteboardState,
  currentStroke,
  currentShape,
  isDrawing,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  canvasRef,
  containerRef,
}) => {
  // Initialize canvas dimensions
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (canvas && container) {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    }
  }, [canvasRef, containerRef]);

  // Draw a single stroke on context
  const drawStroke = useCallback(
    (ctx: CanvasRenderingContext2D, stroke: Stroke) => {
      ctx.beginPath();
      ctx.strokeStyle = stroke.color;
      ctx.lineWidth = stroke.width;
      ctx.globalAlpha = stroke.opacity;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      stroke.points.forEach((point, index) => {
        if (index === 0) {
          ctx.moveTo(point.x, point.y);
        } else {
          ctx.lineTo(point.x, point.y);
        }
      });

      ctx.stroke();
      ctx.globalAlpha = 1;
    },
    [],
  );

  // Draw a single shape on context
  const drawShape = useCallback((ctx: CanvasRenderingContext2D, shape: Shape) => {
    ctx.strokeStyle = shape.color;
    ctx.lineWidth = shape.width;

    switch (shape.type) {
      case 'rectangle':
        ctx.strokeRect(
          shape.start.x,
          shape.start.y,
          shape.end.x - shape.start.x,
          shape.end.y - shape.start.y,
        );
        if (shape.fill) {
          ctx.fillStyle = shape.color;
          ctx.globalAlpha = 0.3;
          ctx.fillRect(
            shape.start.x,
            shape.start.y,
            shape.end.x - shape.start.x,
            shape.end.y - shape.start.y,
          );
          ctx.globalAlpha = 1;
        }
        break;

      case 'circle': {
        const radius = Math.sqrt(
          Math.pow(shape.end.x - shape.start.x, 2) + Math.pow(shape.end.y - shape.start.y, 2),
        );
        ctx.beginPath();
        ctx.arc(shape.start.x, shape.start.y, radius, 0, 2 * Math.PI);
        ctx.stroke();
        if (shape.fill) {
          ctx.fillStyle = shape.color;
          ctx.globalAlpha = 0.3;
          ctx.fill();
          ctx.globalAlpha = 1;
        }
        break;
      }

      case 'line':
      case 'arrow':
        ctx.beginPath();
        ctx.moveTo(shape.start.x, shape.start.y);
        ctx.lineTo(shape.end.x, shape.end.y);
        ctx.stroke();

        if (shape.type === 'arrow') {
          drawArrowhead(ctx, shape.start, shape.end);
        }
        break;
    }
  }, []);

  // Draw arrowhead helper
  const drawArrowhead = (ctx: CanvasRenderingContext2D, start: Point, end: Point) => {
    const angle = Math.atan2(end.y - start.y, end.x - start.x);
    const arrowSize = 15;
    ctx.beginPath();
    ctx.moveTo(end.x, end.y);
    ctx.lineTo(
      end.x - arrowSize * Math.cos(angle - Math.PI / 6),
      end.y - arrowSize * Math.sin(angle - Math.PI / 6),
    );
    ctx.moveTo(end.x, end.y);
    ctx.lineTo(
      end.x - arrowSize * Math.cos(angle + Math.PI / 6),
      end.y - arrowSize * Math.sin(angle + Math.PI / 6),
    );
    ctx.stroke();
  };

  // Draw current stroke preview
  const drawCurrentStroke = useCallback(
    (ctx: CanvasRenderingContext2D, points: Point[]) => {
      if (points.length === 0) {return;}

      ctx.save();
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);
      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = strokeWidth;
      ctx.globalAlpha = tool === 'highlighter' ? 0.5 : 1;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      points.forEach((point, index) => {
        if (index === 0) {
          ctx.moveTo(point.x, point.y);
        } else {
          ctx.lineTo(point.x, point.y);
        }
      });

      ctx.stroke();
      ctx.restore();
    },
    [color, pan.x, pan.y, strokeWidth, tool, zoom],
  );

  // Draw current shape preview
  const drawCurrentShape = useCallback(
    (ctx: CanvasRenderingContext2D, shape: { start: Point; end: Point }) => {
      ctx.save();
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);
      ctx.strokeStyle = color;
      ctx.lineWidth = strokeWidth;

      switch (shapeType) {
        case 'rectangle':
          ctx.strokeRect(
            shape.start.x,
            shape.start.y,
            shape.end.x - shape.start.x,
            shape.end.y - shape.start.y,
          );
          break;

        case 'circle': {
          const radius = Math.sqrt(
            Math.pow(shape.end.x - shape.start.x, 2) + Math.pow(shape.end.y - shape.start.y, 2),
          );
          ctx.beginPath();
          ctx.arc(shape.start.x, shape.start.y, radius, 0, 2 * Math.PI);
          ctx.stroke();
          break;
        }

        case 'line':
        case 'arrow':
          ctx.beginPath();
          ctx.moveTo(shape.start.x, shape.start.y);
          ctx.lineTo(shape.end.x, shape.end.y);
          ctx.stroke();
          break;
      }

      ctx.restore();
    },
    [color, pan.x, pan.y, shapeType, strokeWidth, zoom],
  );

  // Main redraw effect
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) {return;}

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Apply zoom and pan transformation
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, zoom);

    // Draw all strokes
    whiteboardState.strokes.forEach((stroke) => {
      drawStroke(ctx, stroke);
    });

    // Draw all shapes
    whiteboardState.shapes.forEach((shape) => {
      drawShape(ctx, shape);
    });

    // Draw all texts
    whiteboardState.texts.forEach((text) => {
      ctx.font = `${text.fontSize}px ${text.fontFamily}`;
      ctx.fillStyle = text.color;
      ctx.fillText(text.content, text.position.x, text.position.y);
    });

    // Draw all equations (simplified rendering)
    whiteboardState.equations.forEach((eq) => {
      ctx.font = `${eq.fontSize}px Arial`;
      ctx.fillStyle = eq.color;
      ctx.fillText(`LaTeX: ${eq.latex}`, eq.position.x, eq.position.y);
    });

    ctx.restore();

    // Draw current stroke preview
    if (isDrawing && currentStroke.length > 0) {
      drawCurrentStroke(ctx, currentStroke);
    }

    // Draw current shape preview
    if (isDrawing && currentShape && tool === 'shape') {
      drawCurrentShape(ctx, currentShape);
    }
  }, [
    canvasRef,
    whiteboardState,
    zoom,
    pan,
    isDrawing,
    currentStroke,
    currentShape,
    tool,
    drawStroke,
    drawShape,
    drawCurrentStroke,
    drawCurrentShape,
  ]);

  // Determine cursor style based on tool
  const getCursorStyle = (): string => {
    switch (tool) {
      case 'pan':
        return 'grab';
      case 'text':
      case 'equation':
        return 'text';
      default:
        return 'crosshair';
    }
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        flex: 1,
        position: 'relative',
        overflow: 'hidden',
        bgcolor: 'background.default',
      }}
    >
      <canvas
        ref={canvasRef}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        role="img"
        aria-label="Interaktif beyaz tahta"
        style={{
          cursor: getCursorStyle(),
          display: 'block',
        }}
      />
    </Box>
  );
};

export default WhiteboardCanvas;

/**
 * CollaborativeWhiteboard Component (Orchestrator)
 *
 * Main orchestration component for the collaborative whiteboard.
 * Coordinates toolbar, canvas, text editor, and WebSocket sync.
 *
 * Refactored from 904-line monolithic component into modular architecture.
 */

import { Box } from '@mui/material';
import * as React from 'react';
import {  useState, useEffect, useRef, useCallback  } from 'react';

import TextEditor, { createTextElement, createEquationElement } from './TextEditor';
import {
  CollaborativeWhiteboardProps,
  WhiteboardState,
  WhiteboardTool,
  ShapeType,
  Point,
  Stroke,
  Shape,
  TextElement,
  EquationElement,
  DEFAULT_STROKE_WIDTH,
  DEFAULT_FONT_SIZE,
  MIN_ZOOM,
  MAX_ZOOM,
  ZOOM_STEP,
} from './types';
import WhiteboardCanvas from './WhiteboardCanvas';
import { useWhiteboardSync, createEmptyState } from './WhiteboardSync';
import WhiteboardToolbar from './WhiteboardToolbar';

const CollaborativeWhiteboard: React.FC<CollaborativeWhiteboardProps> = ({
  roomId,
  currentUserId: _currentUserId,
}) => {
  // Tool state
  const [tool, setTool] = useState<WhiteboardTool>('pen');
  const [shapeType, setShapeType] = useState<ShapeType>('rectangle');
  const [color, setColor] = useState('#000000');
  const [strokeWidth, setStrokeWidth] = useState(DEFAULT_STROKE_WIDTH);
  const [fontSize] = useState(DEFAULT_FONT_SIZE);

  // Whiteboard state
  const [whiteboardState, setWhiteboardState] = useState<WhiteboardState>(createEmptyState());
  const [_undoStack, setUndoStack] = useState<WhiteboardState[]>([]);

  // Drawing state
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentStroke, setCurrentStroke] = useState<Point[]>([]);
  const [currentShape, setCurrentShape] = useState<{ start: Point; end: Point } | null>(null);

  // View state
  const [zoom, setZoom] = useState(1);
  const [pan] = useState<Point>({ x: 0, y: 0 });

  // Text editor state
  const [textInput, setTextInput] = useState('');
  const [latexInput, setLatexInput] = useState('');
  const [textPosition, setTextPosition] = useState<Point | null>(null);

  // Refs
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // WebSocket sync
  const {
    sendStroke,
    sendShape,
    sendText,
    sendEquation,
    sendClear,
    fetchState,
  } = useWhiteboardSync({
    roomId,
    onStateChange: setWhiteboardState,
    onStrokeAdded: (stroke) => {
      setWhiteboardState((prev) => ({
        ...prev,
        strokes: [...prev.strokes, stroke],
      }));
    },
    onShapeAdded: (shape) => {
      setWhiteboardState((prev) => ({
        ...prev,
        shapes: [...prev.shapes, shape],
      }));
    },
    onTextAdded: (text) => {
      setWhiteboardState((prev) => ({
        ...prev,
        texts: [...prev.texts, text],
      }));
    },
    onEquationAdded: (equation) => {
      setWhiteboardState((prev) => ({
        ...prev,
        equations: [...prev.equations, equation],
      }));
    },
    onClear: () => {
      setWhiteboardState(createEmptyState());
    },
  });

  // Fetch initial state
  useEffect(() => {
    fetchState();
  }, [fetchState]);

  // Get canvas point from mouse event
  const getCanvasPoint = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>): Point => {
      const canvas = canvasRef.current;
      if (!canvas) {return { x: 0, y: 0 };}

      const rect = canvas.getBoundingClientRect();
      return {
        x: (e.clientX - rect.left - pan.x) / zoom,
        y: (e.clientY - rect.top - pan.y) / zoom,
      };
    },
    [pan.x, pan.y, zoom],
  );

  // Mouse event handlers
  const handleMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const point = getCanvasPoint(e);
      setIsDrawing(true);

      if (tool === 'pen' || tool === 'highlighter' || tool === 'eraser') {
        setCurrentStroke([point]);
      } else if (tool === 'shape') {
        setCurrentShape({ start: point, end: point });
      } else if (tool === 'text' || tool === 'equation') {
        setTextPosition(point);
      }
    },
    [tool, getCanvasPoint],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isDrawing) {return;}

      const point = getCanvasPoint(e);

      if (tool === 'pen' || tool === 'highlighter' || tool === 'eraser') {
        setCurrentStroke((prev) => [...prev, point]);
      } else if (tool === 'shape' && currentShape) {
        setCurrentShape({ ...currentShape, end: point });
      }
    },
    [isDrawing, tool, currentShape, getCanvasPoint],
  );

  const handleMouseUp = useCallback(async () => {
    if (!isDrawing) {return;}
    setIsDrawing(false);

    // Handle stroke completion
    if ((tool === 'pen' || tool === 'highlighter' || tool === 'eraser') && currentStroke.length > 0) {
      const newStroke: Stroke = {
        id: `stroke-${Date.now()}`,
        tool: tool as 'pen' | 'highlighter' | 'eraser',
        points: currentStroke,
        color,
        width: strokeWidth,
        opacity: tool === 'highlighter' ? 0.5 : 1,
      };

      setWhiteboardState((prev) => ({
        ...prev,
        strokes: [...prev.strokes, newStroke],
      }));

      await sendStroke(newStroke);
      setCurrentStroke([]);
    }

    // Handle shape completion
    if (tool === 'shape' && currentShape) {
      const newShape: Shape = {
        id: `shape-${Date.now()}`,
        type: shapeType,
        start: currentShape.start,
        end: currentShape.end,
        color,
        width: strokeWidth,
      };

      setWhiteboardState((prev) => ({
        ...prev,
        shapes: [...prev.shapes, newShape],
      }));

      await sendShape(newShape);
      setCurrentShape(null);
    }
  }, [isDrawing, tool, currentStroke, currentShape, color, strokeWidth, shapeType, sendStroke, sendShape]);

  // Text/equation submission
  const handleAddText = useCallback(async () => {
    if (!textInput || !textPosition) {return;}

    const newText: TextElement = createTextElement(
      textPosition,
      textInput,
      fontSize,
      color,
    );

    setWhiteboardState((prev) => ({
      ...prev,
      texts: [...prev.texts, newText],
    }));

    await sendText(newText);
    setTextInput('');
    setTextPosition(null);
  }, [textInput, textPosition, fontSize, color, sendText]);

  const handleAddEquation = useCallback(async () => {
    if (!latexInput || !textPosition) {return;}

    const newEquation: EquationElement = createEquationElement(
      textPosition,
      latexInput,
      fontSize,
      color,
    );

    setWhiteboardState((prev) => ({
      ...prev,
      equations: [...prev.equations, newEquation],
    }));

    await sendEquation(newEquation);
    setLatexInput('');
    setTextPosition(null);
  }, [latexInput, textPosition, fontSize, color, sendEquation]);

  // Toolbar actions
  const handleUndo = useCallback(() => {
    setUndoStack((prev) => [...prev, whiteboardState]);
    setWhiteboardState((prev) => {
      if (prev.strokes.length > 0) {
        return { ...prev, strokes: prev.strokes.slice(0, -1) };
      } else if (prev.shapes.length > 0) {
        return { ...prev, shapes: prev.shapes.slice(0, -1) };
      }
      return prev;
    });
  }, [whiteboardState]);

  const handleClear = useCallback(async () => {
    if (!window.confirm('Tahtayi temizlemek istediginizden emin misiniz?')) {return;}

    setWhiteboardState(createEmptyState());
    await sendClear();
  }, [sendClear]);

  const handleSave = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) {return;}

    try {
      const dataUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `whiteboard-${Date.now()}.png`;
      link.href = dataUrl;
      link.click();
    } catch (error) {
      console.error('Error saving whiteboard:', error);
    }
  }, []);

  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(prev + ZOOM_STEP, MAX_ZOOM));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(prev - ZOOM_STEP, MIN_ZOOM));
  }, []);

  const handleTextCancel = useCallback(() => {
    setTextPosition(null);
    setTextInput('');
    setLatexInput('');
  }, []);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <WhiteboardToolbar
        tool={tool}
        shapeType={shapeType}
        color={color}
        strokeWidth={strokeWidth}
        zoom={zoom}
        canUndo={whiteboardState.strokes.length > 0 || whiteboardState.shapes.length > 0}
        onToolChange={setTool}
        onShapeTypeChange={setShapeType}
        onColorChange={setColor}
        onStrokeWidthChange={setStrokeWidth}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onUndo={handleUndo}
        onClear={handleClear}
        onSave={handleSave}
      />

      <WhiteboardCanvas
        tool={tool}
        shapeType={shapeType}
        color={color}
        strokeWidth={strokeWidth}
        zoom={zoom}
        pan={pan}
        whiteboardState={whiteboardState}
        currentStroke={currentStroke}
        currentShape={currentShape}
        isDrawing={isDrawing}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        canvasRef={canvasRef}
        containerRef={containerRef}
      />

      {(tool === 'text' || tool === 'equation') && textPosition && (
        <TextEditor
          position={textPosition}
          zoom={zoom}
          pan={pan}
          textInput={textInput}
          latexInput={latexInput}
          tool={tool}
          onTextChange={setTextInput}
          onLatexChange={setLatexInput}
          onSubmit={tool === 'text' ? handleAddText : handleAddEquation}
          onCancel={handleTextCancel}
        />
      )}
    </Box>
  );
};

export default CollaborativeWhiteboard;

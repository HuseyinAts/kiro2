/**
 * Task 109.6: Collaborative Whiteboard Canvas
 *
 * Real-time collaborative whiteboard with drawing tools.
 * Supports pen, shapes, text, LaTeX equations, and image embedding.
 */

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Box,
  Paper,
  IconButton,
  Typography,
  Tooltip,
  Slider,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  Popover,
  TextField,
  Button,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Create as PenIcon,
  Highlight as HighlightIcon,
  Square as RectangleIcon,
  Circle as CircleIcon,
  Timeline as LineIcon,
  TextFields as TextIcon,
  Functions as EquationIcon,
  Image as ImageIcon,
  Undo as UndoIcon,
  Redo as RedoIcon,
  Delete as DeleteIcon,
  Clear as ClearIcon,
  SaveAlt as SaveIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  PanTool as PanIcon,
  ColorLens as ColorIcon,
} from '@mui/icons-material';

// ============================================================
// Types
// ============================================================

interface Point {
  x: number;
  y: number;
}

interface Stroke {
  id: string;
  tool: 'pen' | 'highlighter' | 'eraser';
  points: Point[];
  color: string;
  width: number;
  opacity: number;
}

interface Shape {
  id: string;
  type: 'rectangle' | 'circle' | 'line' | 'arrow';
  start: Point;
  end: Point;
  color: string;
  width: number;
  fill?: boolean;
}

interface TextElement {
  id: string;
  position: Point;
  content: string;
  fontSize: number;
  color: string;
  fontFamily: string;
}

interface EquationElement {
  id: string;
  position: Point;
  latex: string;
  fontSize: number;
  color: string;
}

interface WhiteboardState {
  strokes: Stroke[];
  shapes: Shape[];
  texts: TextElement[];
  equations: EquationElement[];
}

interface CollaborativeWhiteboardProps {
  roomId: string;
  currentUserId: string;
}

// ============================================================
// Component
// ============================================================

const CollaborativeWhiteboard: React.FC<CollaborativeWhiteboardProps> = ({
  roomId,
  currentUserId,
}) => {
  const [tool, setTool] = useState<'pen' | 'highlighter' | 'eraser' | 'shape' | 'text' | 'equation' | 'pan'>('pen');
  const [shapeType, setShapeType] = useState<'rectangle' | 'circle' | 'line' | 'arrow'>('rectangle');
  const [color, setColor] = useState('#000000');
  const [strokeWidth, setStrokeWidth] = useState(2);
  const [fontSize, setFontSize] = useState(16);
  const [whiteboardState, setWhiteboardState] = useState<WhiteboardState>({
    strokes: [],
    shapes: [],
    texts: [],
    equations: [],
  });
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentStroke, setCurrentStroke] = useState<Point[]>([]);
  const [currentShape, setCurrentShape] = useState<{ start: Point; end: Point } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [undoStack, setUndoStack] = useState<WhiteboardState[]>([]);
  const [redoStack, setRedoStack] = useState<WhiteboardState[]>([]);
  const [colorAnchorEl, setColorAnchorEl] = useState<null | HTMLElement>(null);
  const [textInput, setTextInput] = useState('');
  const [latexInput, setLatexInput] = useState('');
  const [textPosition, setTextPosition] = useState<Point | null>(null);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const colors = [
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
  ];

  useEffect(() => {
    initializeCanvas();
    connectWebSocket();
    fetchWhiteboardState();

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, []);

  useEffect(() => {
    redrawCanvas();
  }, [whiteboardState, zoom, pan]);

  const initializeCanvas = () => {
    const canvas = canvasRef.current;
    if (canvas && containerRef.current) {
      canvas.width = containerRef.current.clientWidth;
      canvas.height = containerRef.current.clientHeight;
    }
  };

  const connectWebSocket = () => {
    const wsUrl = `ws://localhost:8000/ws/study-rooms/${roomId}/whiteboard`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected for whiteboard');
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'stroke-added':
          setWhiteboardState((prev) => ({
            ...prev,
            strokes: [...prev.strokes, message.stroke],
          }));
          break;
        case 'shape-added':
          setWhiteboardState((prev) => ({
            ...prev,
            shapes: [...prev.shapes, message.shape],
          }));
          break;
        case 'text-added':
          setWhiteboardState((prev) => ({
            ...prev,
            texts: [...prev.texts, message.text],
          }));
          break;
        case 'equation-added':
          setWhiteboardState((prev) => ({
            ...prev,
            equations: [...prev.equations, message.equation],
          }));
          break;
        case 'clear':
          setWhiteboardState({
            strokes: [],
            shapes: [],
            texts: [],
            equations: [],
          });
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const fetchWhiteboardState = async () => {
    try {
      const response = await axios.get(`/api/study-rooms/${roomId}/whiteboard/state`);
      setWhiteboardState(response.data);
    } catch (error) {
      console.error('Error fetching whiteboard state:', error);
    }
  };

  const redrawCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Apply zoom and pan
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, zoom);

    // Draw strokes
    whiteboardState.strokes.forEach((stroke) => {
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
    });

    // Draw shapes
    whiteboardState.shapes.forEach((shape) => {
      ctx.strokeStyle = shape.color;
      ctx.lineWidth = shape.width;

      switch (shape.type) {
        case 'rectangle':
          ctx.strokeRect(
            shape.start.x,
            shape.start.y,
            shape.end.x - shape.start.x,
            shape.end.y - shape.start.y
          );
          if (shape.fill) {
            ctx.fillStyle = shape.color;
            ctx.globalAlpha = 0.3;
            ctx.fillRect(
              shape.start.x,
              shape.start.y,
              shape.end.x - shape.start.x,
              shape.end.y - shape.start.y
            );
            ctx.globalAlpha = 1;
          }
          break;
        case 'circle':
          const radius = Math.sqrt(
            Math.pow(shape.end.x - shape.start.x, 2) + Math.pow(shape.end.y - shape.start.y, 2)
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
        case 'line':
        case 'arrow':
          ctx.beginPath();
          ctx.moveTo(shape.start.x, shape.start.y);
          ctx.lineTo(shape.end.x, shape.end.y);
          ctx.stroke();

          if (shape.type === 'arrow') {
            // Draw arrowhead
            const angle = Math.atan2(shape.end.y - shape.start.y, shape.end.x - shape.start.x);
            const arrowSize = 15;
            ctx.beginPath();
            ctx.moveTo(shape.end.x, shape.end.y);
            ctx.lineTo(
              shape.end.x - arrowSize * Math.cos(angle - Math.PI / 6),
              shape.end.y - arrowSize * Math.sin(angle - Math.PI / 6)
            );
            ctx.moveTo(shape.end.x, shape.end.y);
            ctx.lineTo(
              shape.end.x - arrowSize * Math.cos(angle + Math.PI / 6),
              shape.end.y - arrowSize * Math.sin(angle + Math.PI / 6)
            );
            ctx.stroke();
          }
          break;
      }
    });

    // Draw texts
    whiteboardState.texts.forEach((text) => {
      ctx.font = `${text.fontSize}px ${text.fontFamily}`;
      ctx.fillStyle = text.color;
      ctx.fillText(text.content, text.position.x, text.position.y);
    });

    // Draw equations (simplified - in production use MathJax or KaTeX)
    whiteboardState.equations.forEach((eq) => {
      ctx.font = `${eq.fontSize}px Arial`;
      ctx.fillStyle = eq.color;
      ctx.fillText(`LaTeX: ${eq.latex}`, eq.position.x, eq.position.y);
    });

    ctx.restore();

    // Draw current stroke
    if (isDrawing && currentStroke.length > 0) {
      ctx.save();
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);
      ctx.beginPath();
      ctx.strokeStyle = color;
      ctx.lineWidth = strokeWidth;
      ctx.globalAlpha = tool === 'highlighter' ? 0.5 : 1;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      currentStroke.forEach((point, index) => {
        if (index === 0) {
          ctx.moveTo(point.x, point.y);
        } else {
          ctx.lineTo(point.x, point.y);
        }
      });

      ctx.stroke();
      ctx.restore();
    }

    // Draw current shape
    if (isDrawing && currentShape && tool === 'shape') {
      ctx.save();
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);
      ctx.strokeStyle = color;
      ctx.lineWidth = strokeWidth;

      switch (shapeType) {
        case 'rectangle':
          ctx.strokeRect(
            currentShape.start.x,
            currentShape.start.y,
            currentShape.end.x - currentShape.start.x,
            currentShape.end.y - currentShape.start.y
          );
          break;
        case 'circle':
          const radius = Math.sqrt(
            Math.pow(currentShape.end.x - currentShape.start.x, 2) +
              Math.pow(currentShape.end.y - currentShape.start.y, 2)
          );
          ctx.beginPath();
          ctx.arc(currentShape.start.x, currentShape.start.y, radius, 0, 2 * Math.PI);
          ctx.stroke();
          break;
        case 'line':
        case 'arrow':
          ctx.beginPath();
          ctx.moveTo(currentShape.start.x, currentShape.start.y);
          ctx.lineTo(currentShape.end.x, currentShape.end.y);
          ctx.stroke();
          break;
      }

      ctx.restore();
    }
  };

  const getCanvasPoint = (e: React.MouseEvent<HTMLCanvasElement>): Point => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left - pan.x) / zoom,
      y: (e.clientY - rect.top - pan.y) / zoom,
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const point = getCanvasPoint(e);
    setIsDrawing(true);

    if (tool === 'pen' || tool === 'highlighter' || tool === 'eraser') {
      setCurrentStroke([point]);
    } else if (tool === 'shape') {
      setCurrentShape({ start: point, end: point });
    } else if (tool === 'text' || tool === 'equation') {
      setTextPosition(point);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const point = getCanvasPoint(e);

    if (tool === 'pen' || tool === 'highlighter' || tool === 'eraser') {
      setCurrentStroke((prev) => [...prev, point]);
    } else if (tool === 'shape' && currentShape) {
      setCurrentShape({ ...currentShape, end: point });
    }
  };

  const handleMouseUp = async () => {
    if (!isDrawing) return;
    setIsDrawing(false);

    if ((tool === 'pen' || tool === 'highlighter' || tool === 'eraser') && currentStroke.length > 0) {
      const newStroke: Stroke = {
        id: `stroke-${Date.now()}`,
        tool: tool as 'pen' | 'highlighter' | 'eraser',
        points: currentStroke,
        color: color,
        width: strokeWidth,
        opacity: tool === 'highlighter' ? 0.5 : 1,
      };

      // Add to local state
      setWhiteboardState((prev) => ({
        ...prev,
        strokes: [...prev.strokes, newStroke],
      }));

      // Send to server
      try {
        await axios.post(`/api/study-rooms/${roomId}/whiteboard/stroke`, newStroke);

        // Broadcast via WebSocket
        if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
          wsConnection.send(
            JSON.stringify({
              type: 'stroke-added',
              stroke: newStroke,
            })
          );
        }
      } catch (error) {
        console.error('Error adding stroke:', error);
      }

      setCurrentStroke([]);
    } else if (tool === 'shape' && currentShape) {
      const newShape: Shape = {
        id: `shape-${Date.now()}`,
        type: shapeType,
        start: currentShape.start,
        end: currentShape.end,
        color: color,
        width: strokeWidth,
      };

      // Add to local state
      setWhiteboardState((prev) => ({
        ...prev,
        shapes: [...prev.shapes, newShape],
      }));

      // Send to server
      try {
        await axios.post(`/api/study-rooms/${roomId}/whiteboard/shape`, newShape);

        // Broadcast via WebSocket
        if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
          wsConnection.send(
            JSON.stringify({
              type: 'shape-added',
              shape: newShape,
            })
          );
        }
      } catch (error) {
        console.error('Error adding shape:', error);
      }

      setCurrentShape(null);
    }
  };

  const handleAddText = async () => {
    if (!textInput || !textPosition) return;

    const newText: TextElement = {
      id: `text-${Date.now()}`,
      position: textPosition,
      content: textInput,
      fontSize: fontSize,
      color: color,
      fontFamily: 'Arial',
    };

    setWhiteboardState((prev) => ({
      ...prev,
      texts: [...prev.texts, newText],
    }));

    try {
      await axios.post(`/api/study-rooms/${roomId}/whiteboard/text`, newText);

      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(
          JSON.stringify({
            type: 'text-added',
            text: newText,
          })
        );
      }
    } catch (error) {
      console.error('Error adding text:', error);
    }

    setTextInput('');
    setTextPosition(null);
  };

  const handleAddEquation = async () => {
    if (!latexInput || !textPosition) return;

    const newEquation: EquationElement = {
      id: `equation-${Date.now()}`,
      position: textPosition,
      latex: latexInput,
      fontSize: fontSize,
      color: color,
    };

    setWhiteboardState((prev) => ({
      ...prev,
      equations: [...prev.equations, newEquation],
    }));

    try {
      await axios.post(`/api/study-rooms/${roomId}/whiteboard/equation`, newEquation);

      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(
          JSON.stringify({
            type: 'equation-added',
            equation: newEquation,
          })
        );
      }
    } catch (error) {
      console.error('Error adding equation:', error);
    }

    setLatexInput('');
    setTextPosition(null);
  };

  const handleClear = async () => {
    if (!window.confirm('Tahtayı temizlemek istediğinizden emin misiniz?')) return;

    setWhiteboardState({
      strokes: [],
      shapes: [],
      texts: [],
      equations: [],
    });

    try {
      await axios.post(`/api/study-rooms/${roomId}/whiteboard/clear`);

      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(
          JSON.stringify({
            type: 'clear',
          })
        );
      }
    } catch (error) {
      console.error('Error clearing whiteboard:', error);
    }
  };

  const handleUndo = () => {
    // Simple undo implementation
    setUndoStack((prev) => [...prev, whiteboardState]);
    // Remove last element
    setWhiteboardState((prev) => {
      if (prev.strokes.length > 0) {
        return { ...prev, strokes: prev.strokes.slice(0, -1) };
      } else if (prev.shapes.length > 0) {
        return { ...prev, shapes: prev.shapes.slice(0, -1) };
      }
      return prev;
    });
  };

  const handleSave = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    try {
      const dataUrl = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `whiteboard-${Date.now()}.png`;
      link.href = dataUrl;
      link.click();
    } catch (error) {
      console.error('Error saving whiteboard:', error);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toolbar */}
      <Paper sx={{ p: 1, display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
        {/* Drawing Tools */}
        <ToggleButtonGroup
          value={tool}
          exclusive
          onChange={(e, value) => value && setTool(value)}
          size="small"
        >
          <ToggleButton value="pen">
            <Tooltip title="Kalem">
              <PenIcon />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="highlighter">
            <Tooltip title="Fosforlu Kalem">
              <HighlightIcon />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="eraser">
            <Tooltip title="Silgi">
              <DeleteIcon />
            </Tooltip>
          </ToggleButton>
        </ToggleButtonGroup>

        <Divider orientation="vertical" flexItem />

        {/* Shape Tools */}
        <ToggleButtonGroup
          value={tool === 'shape' ? shapeType : tool}
          exclusive
          onChange={(e, value) => {
            if (['rectangle', 'circle', 'line', 'arrow'].includes(value)) {
              setTool('shape');
              setShapeType(value as any);
            }
          }}
          size="small"
        >
          <ToggleButton value="rectangle">
            <Tooltip title="Dikdörtgen">
              <RectangleIcon />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="circle">
            <Tooltip title="Daire">
              <CircleIcon />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="line">
            <Tooltip title="Çizgi">
              <LineIcon />
            </Tooltip>
          </ToggleButton>
        </ToggleButtonGroup>

        <Divider orientation="vertical" flexItem />

        {/* Text & Equation */}
        <ToggleButtonGroup value={tool} exclusive onChange={(e, value) => value && setTool(value)} size="small">
          <ToggleButton value="text">
            <Tooltip title="Metin">
              <TextIcon />
            </Tooltip>
          </ToggleButton>
          <ToggleButton value="equation">
            <Tooltip title="Denklem (LaTeX)">
              <EquationIcon />
            </Tooltip>
          </ToggleButton>
        </ToggleButtonGroup>

        <Divider orientation="vertical" flexItem />

        {/* Color Picker */}
        <IconButton onClick={(e) => setColorAnchorEl(e.currentTarget)} size="small">
          <ColorIcon sx={{ color: color }} />
        </IconButton>

        <Popover
          open={Boolean(colorAnchorEl)}
          anchorEl={colorAnchorEl}
          onClose={() => setColorAnchorEl(null)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        >
          <Box sx={{ p: 2, display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 1 }}>
            {colors.map((c) => (
              <Box
                key={c}
                onClick={() => {
                  setColor(c);
                  setColorAnchorEl(null);
                }}
                sx={{
                  width: 32,
                  height: 32,
                  bgcolor: c,
                  border: color === c ? 3 : 1,
                  borderColor: color === c ? 'primary.main' : 'divider',
                  cursor: 'pointer',
                  borderRadius: 1,
                }}
              />
            ))}
          </Box>
        </Popover>

        {/* Stroke Width */}
        <Box sx={{ width: 120, mx: 1 }}>
          <Typography variant="caption">Kalınlık: {strokeWidth}px</Typography>
          <Slider
            value={strokeWidth}
            onChange={(e, value) => setStrokeWidth(value as number)}
            min={1}
            max={20}
            size="small"
          />
        </Box>

        <Divider orientation="vertical" flexItem />

        {/* Actions */}
        <Tooltip title="Geri Al">
          <IconButton onClick={handleUndo} size="small" disabled={whiteboardState.strokes.length === 0}>
            <UndoIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Temizle">
          <IconButton onClick={handleClear} size="small">
            <ClearIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Kaydet">
          <IconButton onClick={handleSave} size="small">
            <SaveIcon />
          </IconButton>
        </Tooltip>

        <Divider orientation="vertical" flexItem />

        {/* Zoom */}
        <Tooltip title="Yakınlaştır">
          <IconButton onClick={() => setZoom((prev) => Math.min(prev + 0.1, 3))} size="small">
            <ZoomInIcon />
          </IconButton>
        </Tooltip>
        <Typography variant="caption">{Math.round(zoom * 100)}%</Typography>
        <Tooltip title="Uzaklaştır">
          <IconButton onClick={() => setZoom((prev) => Math.max(prev - 0.1, 0.5))} size="small">
            <ZoomOutIcon />
          </IconButton>
        </Tooltip>
      </Paper>

      {/* Canvas */}
      <Box ref={containerRef} sx={{ flex: 1, position: 'relative', overflow: 'hidden', bgcolor: 'background.default' }}>
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{
            cursor: tool === 'pan' ? 'grab' : 'crosshair',
            display: 'block',
          }}
        />
      </Box>

      {/* Text Input Dialog */}
      {tool === 'text' && textPosition && (
        <Box
          sx={{
            position: 'absolute',
            top: textPosition.y * zoom + pan.y,
            left: textPosition.x * zoom + pan.x,
            bgcolor: 'background.paper',
            p: 2,
            borderRadius: 1,
            boxShadow: 3,
            zIndex: 1000,
          }}
        >
          <TextField
            autoFocus
            placeholder="Metin girin..."
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            size="small"
            fullWidth
          />
          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
            <Button size="small" variant="contained" onClick={handleAddText}>
              Ekle
            </Button>
            <Button size="small" onClick={() => setTextPosition(null)}>
              İptal
            </Button>
          </Box>
        </Box>
      )}

      {/* Equation Input Dialog */}
      {tool === 'equation' && textPosition && (
        <Box
          sx={{
            position: 'absolute',
            top: textPosition.y * zoom + pan.y,
            left: textPosition.x * zoom + pan.x,
            bgcolor: 'background.paper',
            p: 2,
            borderRadius: 1,
            boxShadow: 3,
            zIndex: 1000,
          }}
        >
          <TextField
            autoFocus
            placeholder="LaTeX kodu girin... (örn: x^2 + y^2 = r^2)"
            value={latexInput}
            onChange={(e) => setLatexInput(e.target.value)}
            size="small"
            fullWidth
          />
          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
            <Button size="small" variant="contained" onClick={handleAddEquation}>
              Ekle
            </Button>
            <Button size="small" onClick={() => setTextPosition(null)}>
              İptal
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default CollaborativeWhiteboard;

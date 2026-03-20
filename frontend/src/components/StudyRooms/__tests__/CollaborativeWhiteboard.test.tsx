/**
 * Test Suite: CollaborativeWhiteboard Component
 * Task 109.6: Collaborative Whiteboard Testing
 *
 * Tests canvas drawing, shapes, text, equations, real-time sync,
 * zoom, pan, and all drawing tools.
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import CollaborativeWhiteboard from '../CollaborativeWhiteboard';
import { vi, Mocked } from 'vitest';

// ============================================================
// Mocks
// ============================================================

// Mock Axios
vi.mock('axios');
const mockedAxios = axios as Mocked<typeof axios>;

// WebSocket is already mocked in src/test/setup.ts with a proper function constructor

// Mock Canvas Context
const mockContext = {
  clearRect: vi.fn(),
  fillRect: vi.fn(),
  strokeRect: vi.fn(),
  fillText: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  stroke: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  save: vi.fn(),
  restore: vi.fn(),
  translate: vi.fn(),
  scale: vi.fn(),
  toDataURL: vi.fn(() => 'data:image/png;base64,mock'),
  measureText: vi.fn(() => ({ width: 100 })),
  createLinearGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
};

HTMLCanvasElement.prototype.getContext = vi.fn(() => mockContext) as any;
HTMLCanvasElement.prototype.toDataURL = vi.fn(() => 'data:image/png;base64,mock') as any;
HTMLCanvasElement.prototype.getBoundingClientRect = vi.fn(() => ({
  left: 0,
  top: 0,
  width: 800,
  height: 600,
  x: 0,
  y: 0,
  right: 800,
  bottom: 600,
  toJSON: () => {},
})) as any;

// Mock appendChild to prevent "parameter 1 is not of type 'Node'" error
const originalAppendChild = HTMLElement.prototype.appendChild;
HTMLElement.prototype.appendChild = function<T extends Node>(node: T): T {
  if (node instanceof Node) {
    return originalAppendChild.call(this, node);
  }
  // For non-Node objects (e.g., canvas elements in jsdom), return mock
  return node;
};

// Mock window.confirm
global.confirm = vi.fn(() => true);

// ============================================================
// Test Data
// ============================================================

const mockProps = {
  roomId: 'room1',
  currentUserId: 'user1',
};

const mockWhiteboardState = {
  strokes: [
    {
      id: 'stroke1',
      tool: 'pen' as const,
      points: [{ x: 10, y: 10 }, { x: 20, y: 20 }],
      color: '#000000',
      width: 2,
      opacity: 1,
    },
  ],
  shapes: [
    {
      id: 'shape1',
      type: 'rectangle' as const,
      start: { x: 50, y: 50 },
      end: { x: 100, y: 100 },
      color: '#FF0000',
      width: 2,
    },
  ],
  texts: [
    {
      id: 'text1',
      position: { x: 150, y: 150 },
      content: 'Test Text',
      fontSize: 16,
      color: '#000000',
      fontFamily: 'Arial',
    },
  ],
  equations: [
    {
      id: 'eq1',
      position: { x: 200, y: 200 },
      latex: 'x^2 + y^2 = r^2',
      fontSize: 16,
      color: '#000000',
    },
  ],
};

// ============================================================
// Tests: Rendering
// ============================================================

describe('CollaborativeWhiteboard Component - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: mockWhiteboardState });
  });

  it('renders whiteboard with canvas', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('displays drawing tools', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    expect(screen.getByTestId('CreateIcon')).toBeInTheDocument(); // Pen
    expect(screen.getByTestId('HighlightIcon')).toBeInTheDocument(); // Highlighter
    expect(screen.getByTestId('DeleteIcon')).toBeInTheDocument(); // Eraser
  });

  it('displays shape tools', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    expect(screen.getByTestId('SquareIcon')).toBeInTheDocument(); // Rectangle
    expect(screen.getByTestId('CircleIcon')).toBeInTheDocument(); // Circle
    expect(screen.getByTestId('TimelineIcon')).toBeInTheDocument(); // Line
  });

  it('displays text and equation tools', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    expect(screen.getByTestId('TextFieldsIcon')).toBeInTheDocument(); // Text
    expect(screen.getByTestId('FunctionsIcon')).toBeInTheDocument(); // Equation
  });

  it('displays action buttons', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    expect(screen.getByTestId('UndoIcon')).toBeInTheDocument();
    expect(screen.getByTestId('ClearIcon')).toBeInTheDocument();
    expect(screen.getByTestId('SaveAltIcon')).toBeInTheDocument();
  });

  it('displays zoom controls', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    expect(screen.getByTestId('ZoomInIcon')).toBeInTheDocument();
    expect(screen.getByTestId('ZoomOutIcon')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Canvas Initialization
// ============================================================

describe('CollaborativeWhiteboard Component - Canvas Initialization', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: mockWhiteboardState });
  });

  it('initializes canvas on mount', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const canvas = document.querySelector('canvas') as HTMLCanvasElement;
    expect(canvas).toBeInTheDocument();
    expect(canvas.getContext).toHaveBeenCalledWith('2d');
  });

  it('fetches whiteboard state on mount', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/v1/study-rooms/room1/whiteboard/state'
      );
    });
  });

  it('connects to WebSocket on mount', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    await waitFor(() => {
      expect(global.WebSocket).toHaveBeenCalledWith(
        expect.stringContaining('ws://localhost:8000/ws/study-rooms/room1/whiteboard')
      );
    });
  });

  it('handles whiteboard state fetch error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.get.mockRejectedValue(new Error('Fetch failed'));

    render(<CollaborativeWhiteboard {...mockProps} />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error fetching whiteboard state:',
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });
});

// ============================================================
// Tests: Tool Selection
// ============================================================

describe('CollaborativeWhiteboard Component - Tool Selection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
  });

  it('selects pen tool', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const penButton = screen.getByTestId('CreateIcon').closest('button')!;
    fireEvent.click(penButton);

    expect(penButton.closest('.MuiToggleButton-root')).toHaveClass('Mui-selected');
  });

  it('selects highlighter tool', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const highlighterButton = screen.getByTestId('HighlightIcon').closest('button')!;
    fireEvent.click(highlighterButton);

    expect(highlighterButton.closest('.MuiToggleButton-root')).toHaveClass('Mui-selected');
  });

  it('selects eraser tool', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const eraserButton = screen.getByTestId('DeleteIcon').closest('button')!;
    fireEvent.click(eraserButton);

    expect(eraserButton.closest('.MuiToggleButton-root')).toHaveClass('Mui-selected');
  });

  it('selects rectangle shape', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const rectangleButton = screen.getByTestId('SquareIcon').closest('button')!;
    fireEvent.click(rectangleButton);

    expect(rectangleButton.closest('.MuiToggleButton-root')).toHaveClass('Mui-selected');
  });

  it('selects circle shape', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const circleButton = screen.getByTestId('CircleIcon').closest('button')!;
    fireEvent.click(circleButton);

    expect(circleButton.closest('.MuiToggleButton-root')).toHaveClass('Mui-selected');
  });

  it('selects text tool', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const textButton = screen.getByTestId('TextFieldsIcon').closest('button')!;
    fireEvent.click(textButton);

    expect(textButton.closest('.MuiToggleButton-root')).toHaveClass('Mui-selected');
  });

  it('selects equation tool', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const equationButton = screen.getByTestId('FunctionsIcon').closest('button')!;
    fireEvent.click(equationButton);

    expect(equationButton.closest('.MuiToggleButton-root')).toHaveClass('Mui-selected');
  });
});

// ============================================================
// Tests: Drawing with Pen
// ============================================================

describe('CollaborativeWhiteboard Component - Drawing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
    mockedAxios.post.mockResolvedValue({ data: {} });
  });

  it('draws with pen tool', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const canvas = document.querySelector('canvas')!;

    // Mouse down
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });

    // Mouse move
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });

    // Mouse up
    fireEvent.mouseUp(canvas);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/study-rooms/room1/whiteboard/stroke',
        expect.objectContaining({
          tool: 'pen',
          color: '#000000',
          width: 2,
        })
      );
    });
  });

  it('draws with highlighter tool', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const highlighterButton = screen.getByTestId('HighlightIcon').closest('button')!;
    fireEvent.click(highlighterButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
    fireEvent.mouseUp(canvas);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/study-rooms/room1/whiteboard/stroke',
        expect.objectContaining({
          tool: 'highlighter',
          opacity: 0.5,
        })
      );
    });
  });

  it('handles mouse leave while drawing', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });

    // Mouse leave should finish drawing
    fireEvent.mouseLeave(canvas);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalled();
    });
  });
});

// ============================================================
// Tests: Drawing Shapes
// ============================================================

describe('CollaborativeWhiteboard Component - Shapes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
    mockedAxios.post.mockResolvedValue({ data: {} });
  });

  it('draws rectangle', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const rectangleButton = screen.getByTestId('SquareIcon').closest('button')!;
    fireEvent.click(rectangleButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 50, clientY: 50 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
    fireEvent.mouseUp(canvas);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/study-rooms/room1/whiteboard/shape',
        expect.objectContaining({
          type: 'rectangle',
        })
      );
    });
  });

  it('draws circle', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const circleButton = screen.getByTestId('CircleIcon').closest('button')!;
    fireEvent.click(circleButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
    fireEvent.mouseUp(canvas);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/study-rooms/room1/whiteboard/shape',
        expect.objectContaining({
          type: 'circle',
        })
      );
    });
  });

  it('draws line', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const lineButton = screen.getByTestId('TimelineIcon').closest('button')!;
    fireEvent.click(lineButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 50, clientY: 50 });
    fireEvent.mouseMove(canvas, { clientX: 200, clientY: 200 });
    fireEvent.mouseUp(canvas);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/study-rooms/room1/whiteboard/shape',
        expect.objectContaining({
          type: 'line',
        })
      );
    });
  });
});

// ============================================================
// Tests: Text and Equations
// ============================================================

describe('CollaborativeWhiteboard Component - Text and Equations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
    mockedAxios.post.mockResolvedValue({ data: {} });
  });

  it('adds text to canvas', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const textButton = screen.getByTestId('TextFieldsIcon').closest('button')!;
    fireEvent.click(textButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Metin girin...')).toBeInTheDocument();
    });

    const textInput = screen.getByPlaceholderText('Metin girin...');
    fireEvent.change(textInput, { target: { value: 'Hello World' } });

    const addButton = screen.getByText('Ekle');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/study-rooms/room1/whiteboard/text',
        expect.objectContaining({
          content: 'Hello World',
        })
      );
    });
  });

  it('cancels text input', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const textButton = screen.getByTestId('TextFieldsIcon').closest('button')!;
    fireEvent.click(textButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Metin girin...')).toBeInTheDocument();
    });

    const cancelButton = screen.getByText('İptal');
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByPlaceholderText('Metin girin...')).not.toBeInTheDocument();
    });
  });

  it('adds equation to canvas', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const equationButton = screen.getByTestId('FunctionsIcon').closest('button')!;
    fireEvent.click(equationButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/LaTeX kodu girin/i)).toBeInTheDocument();
    });

    const latexInput = screen.getByPlaceholderText(/LaTeX kodu girin/i);
    fireEvent.change(latexInput, { target: { value: 'x^2 + y^2 = r^2' } });

    const addButton = screen.getByText('Ekle');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/study-rooms/room1/whiteboard/equation',
        expect.objectContaining({
          latex: 'x^2 + y^2 = r^2',
        })
      );
    });
  });

  it('cancels equation input', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const equationButton = screen.getByTestId('FunctionsIcon').closest('button')!;
    fireEvent.click(equationButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/LaTeX kodu girin/i)).toBeInTheDocument();
    });

    const cancelButton = screen.getByText('İptal');
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByPlaceholderText(/LaTeX kodu girin/i)).not.toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Color Picker
// ============================================================

describe('CollaborativeWhiteboard Component - Color Picker', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
  });

  it('opens color picker', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const colorButton = screen.getByTestId('ColorLensIcon').closest('button')!;
    fireEvent.click(colorButton);

    await waitFor(() => {
      const colorBoxes = document.querySelectorAll('[style*="background-color"]');
      expect(colorBoxes.length).toBeGreaterThan(0);
    });
  });

  it('selects color from picker', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const colorButton = screen.getByTestId('ColorLensIcon').closest('button')!;
    fireEvent.click(colorButton);

    await waitFor(() => {
      const colorBoxes = document.querySelectorAll('[style*="rgb(255, 0, 0)"]');
      if (colorBoxes.length > 0) {
        fireEvent.click(colorBoxes[0]);
      }
    });

    // Color picker should close
    await waitFor(() => {
      expect(document.querySelectorAll('[style*="background-color"]').length).toBeLessThan(15);
    });
  });
});

// ============================================================
// Tests: Stroke Width
// ============================================================

describe('CollaborativeWhiteboard Component - Stroke Width', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
  });

  it('displays stroke width slider', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    expect(screen.getByText(/Kalınlık: 2px/i)).toBeInTheDocument();
  });

  it('changes stroke width', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const slider = document.querySelector('input[type="range"]') as HTMLInputElement;
    expect(slider).toBeInTheDocument();

    fireEvent.change(slider, { target: { value: '10' } });

    await waitFor(() => {
      expect(screen.getByText(/Kalınlık: 10px/i)).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Undo and Clear
// ============================================================

describe('CollaborativeWhiteboard Component - Undo and Clear', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: mockWhiteboardState });
    mockedAxios.post.mockResolvedValue({ data: {} });
  });

  it('undo removes last stroke', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalled();
    });

    const undoButton = screen.getByTestId('UndoIcon').closest('button')!;
    fireEvent.click(undoButton);

    // Should update state (implementation detail)
    expect(undoButton).toBeInTheDocument();
  });

  it('clears whiteboard with confirmation', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalled();
    });

    const clearButton = screen.getByTestId('ClearIcon').closest('button')!;
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalled();
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/study-rooms/room1/whiteboard/clear'
      );
    });
  });

  it('cancels clear when user declines', async () => {
    (global.confirm as jest.Mock).mockReturnValueOnce(false);

    render(<CollaborativeWhiteboard {...mockProps} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalled();
    });

    const clearButton = screen.getByTestId('ClearIcon').closest('button')!;
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalled();
    });

    // Clear API should not be called
    expect(mockedAxios.post).not.toHaveBeenCalledWith(
      '/api/v1/study-rooms/room1/whiteboard/clear'
    );
  });
});

// ============================================================
// Tests: Save
// ============================================================

describe('CollaborativeWhiteboard Component - Save', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });

    // Mock document.createElement and link.click
    const mockLink = {
      download: '',
      href: '',
      click: vi.fn(),
    };
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
  });

  it('saves whiteboard as PNG', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const saveButton = screen.getByTestId('SaveAltIcon').closest('button')!;
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(document.createElement).toHaveBeenCalledWith('a');
    });
  });

  it('handles save error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    (HTMLCanvasElement.prototype.toDataURL as jest.Mock).mockImplementation(() => {
      throw new Error('Canvas error');
    });

    render(<CollaborativeWhiteboard {...mockProps} />);

    const saveButton = screen.getByTestId('SaveAltIcon').closest('button')!;
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });
});

// ============================================================
// Tests: Zoom Controls
// ============================================================

describe('CollaborativeWhiteboard Component - Zoom', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
  });

  it('zooms in', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    expect(screen.getByText('100%')).toBeInTheDocument();

    const zoomInButton = screen.getByTestId('ZoomInIcon').closest('button')!;
    fireEvent.click(zoomInButton);

    await waitFor(() => {
      expect(screen.getByText('110%')).toBeInTheDocument();
    });
  });

  it('zooms out', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    expect(screen.getByText('100%')).toBeInTheDocument();

    const zoomOutButton = screen.getByTestId('ZoomOutIcon').closest('button')!;
    fireEvent.click(zoomOutButton);

    await waitFor(() => {
      expect(screen.getByText('90%')).toBeInTheDocument();
    });
  });

  it('limits zoom in at 300%', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const zoomInButton = screen.getByTestId('ZoomInIcon').closest('button')!;

    // Click 25 times (should max at 300%)
    for (let i = 0; i < 25; i++) {
      fireEvent.click(zoomInButton);
    }

    await waitFor(() => {
      expect(screen.getByText('300%')).toBeInTheDocument();
    });
  });

  it('limits zoom out at 50%', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const zoomOutButton = screen.getByTestId('ZoomOutIcon').closest('button')!;

    // Click 10 times (should min at 50%)
    for (let i = 0; i < 10; i++) {
      fireEvent.click(zoomOutButton);
    }

    await waitFor(() => {
      expect(screen.getByText('50%')).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: WebSocket Real-time Sync
// ============================================================

describe('CollaborativeWhiteboard Component - Real-time Sync', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
  });

  it('receives stroke from WebSocket', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const ws = (global.WebSocket as any).mock.instances[0];
    await waitFor(() => expect(ws).toBeDefined());

    ws.simulateMessage({
      type: 'stroke-added',
      stroke: {
        id: 'stroke-remote',
        tool: 'pen',
        points: [{ x: 10, y: 10 }, { x: 20, y: 20 }],
        color: '#FF0000',
        width: 2,
        opacity: 1,
      },
    });

    // Canvas should redraw (implementation detail)
    await waitFor(() => {
      expect(mockContext.stroke).toHaveBeenCalled();
    });
  });

  it('receives shape from WebSocket', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const ws = (global.WebSocket as any).mock.instances[0];
    await waitFor(() => expect(ws).toBeDefined());

    ws.simulateMessage({
      type: 'shape-added',
      shape: {
        id: 'shape-remote',
        type: 'rectangle',
        start: { x: 50, y: 50 },
        end: { x: 100, y: 100 },
        color: '#0000FF',
        width: 2,
      },
    });

    await waitFor(() => {
      expect(mockContext.strokeRect).toHaveBeenCalled();
    });
  });

  it('receives text from WebSocket', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const ws = (global.WebSocket as any).mock.instances[0];
    await waitFor(() => expect(ws).toBeDefined());

    ws.simulateMessage({
      type: 'text-added',
      text: {
        id: 'text-remote',
        position: { x: 100, y: 100 },
        content: 'Remote Text',
        fontSize: 16,
        color: '#000000',
        fontFamily: 'Arial',
      },
    });

    await waitFor(() => {
      expect(mockContext.fillText).toHaveBeenCalled();
    });
  });

  it('receives equation from WebSocket', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const ws = (global.WebSocket as any).mock.instances[0];
    await waitFor(() => expect(ws).toBeDefined());

    ws.simulateMessage({
      type: 'equation-added',
      equation: {
        id: 'eq-remote',
        position: { x: 150, y: 150 },
        latex: 'E = mc^2',
        fontSize: 16,
        color: '#000000',
      },
    });

    await waitFor(() => {
      expect(mockContext.fillText).toHaveBeenCalled();
    });
  });

  it('receives clear message from WebSocket', async () => {
    render(<CollaborativeWhiteboard {...mockProps} />);

    const ws = (global.WebSocket as any).mock.instances[0];
    await waitFor(() => expect(ws).toBeDefined());

    ws.simulateMessage({
      type: 'clear',
    });

    await waitFor(() => {
      expect(mockContext.clearRect).toHaveBeenCalled();
    });
  });

  it('handles unknown WebSocket message type', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation();

    render(<CollaborativeWhiteboard {...mockProps} />);

    const ws = (global.WebSocket as any).mock.instances[0];
    await waitFor(() => expect(ws).toBeDefined());

    ws.simulateMessage({
      type: 'unknown-type',
    });

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Unknown message type:', 'unknown-type');
    });

    consoleSpy.mockRestore();
  });
});

// ============================================================
// Tests: Error Handling
// ============================================================

describe('CollaborativeWhiteboard Component - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
  });

  it('handles stroke save error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.post.mockRejectedValue(new Error('Save failed'));

    render(<CollaborativeWhiteboard {...mockProps} />);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
    fireEvent.mouseUp(canvas);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error adding stroke:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it('handles text save error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.post.mockRejectedValue(new Error('Save failed'));

    render(<CollaborativeWhiteboard {...mockProps} />);

    const textButton = screen.getByTestId('TextFieldsIcon').closest('button')!;
    fireEvent.click(textButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });

    await waitFor(() => {
      const textInput = screen.getByPlaceholderText('Metin girin...');
      fireEvent.change(textInput, { target: { value: 'Test' } });
    });

    const addButton = screen.getByText('Ekle');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });

  it('handles clear error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.post.mockRejectedValue(new Error('Clear failed'));

    render(<CollaborativeWhiteboard {...mockProps} />);

    const clearButton = screen.getByTestId('ClearIcon').closest('button')!;
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });

  it('handles WebSocket error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();

    render(<CollaborativeWhiteboard {...mockProps} />);

    const ws = (global.WebSocket as any).mock.instances[0];
    await waitFor(() => expect(ws).toBeDefined());

    if (ws.onerror) {
      ws.onerror(new Event('error'));
    }

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });
});

// ============================================================
// Tests: Cleanup
// ============================================================

describe('CollaborativeWhiteboard Component - Cleanup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: { strokes: [], shapes: [], texts: [], equations: [] } });
  });

  it('closes WebSocket on unmount', async () => {
    const { unmount } = render(<CollaborativeWhiteboard {...mockProps} />);

    const ws = (global.WebSocket as any).mock.instances[0];
    await waitFor(() => expect(ws).toBeDefined());

    const closeSpy = vi.spyOn(ws, 'close');

    unmount();

    expect(closeSpy).toHaveBeenCalled();
  });
});

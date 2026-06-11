/**
 * Test Suite: InteractiveGeometry Component
 * Task 87.3: Interactive Geometry Testing
 *
 * Tests canvas-based geometry tools, shape drawing, measurements,
 * transformations, and tool usage tracking.
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import InteractiveGeometry from '../InteractiveGeometry';
import { vi, Mocked, Mock } from 'vitest';

// ============================================================
// Mocks
// ============================================================

// Mock Axios
vi.mock('axios');
const mockedAxios = axios as Mocked<typeof axios>;

// Mock window.alert
global.alert = vi.fn();

// Mock Canvas Context
const mockContext = {
  clearRect: vi.fn(),
  strokeRect: vi.fn(),
  fillRect: vi.fn(),
  rect: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  stroke: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  closePath: vi.fn(),
  fillText: vi.fn(),
  setLineDash: vi.fn(),
};

HTMLCanvasElement.prototype.getContext = vi.fn(() => mockContext) as any;
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

// ============================================================
// Tests: Rendering
// ============================================================

describe('InteractiveGeometry Component - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders component', () => {
    render(<InteractiveGeometry />);

    expect(screen.getByText('İnteraktif Geometri')).toBeInTheDocument();
  });

  it('renders canvas', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
    expect(canvas).toHaveAttribute('width', '800');
    expect(canvas).toHaveAttribute('height', '600');
  });

  it('renders drawing tools', () => {
    render(<InteractiveGeometry />);

    expect(screen.getByTitle('Doğru')).toBeInTheDocument();
    expect(screen.getByTitle('Daire')).toBeInTheDocument();
    expect(screen.getByTitle('Dikdörtgen')).toBeInTheDocument();
  });

  it('renders measurement tools', () => {
    render(<InteractiveGeometry />);

    expect(screen.getByText(/Uzunluk/)).toBeInTheDocument();
  });

  it('renders transformation tools', () => {
    render(<InteractiveGeometry />);

    expect(screen.getByText(/Döndür/)).toBeInTheDocument();
    expect(screen.getByText(/Yansıt/)).toBeInTheDocument();
    expect(screen.getByText(/Ötle/)).toBeInTheDocument();
  });

  it('renders control buttons', () => {
    render(<InteractiveGeometry />);

    expect(screen.getByText('Temizle')).toBeInTheDocument();
    expect(screen.getByText('Kaydet')).toBeInTheDocument();
  });

  it('displays statistics', () => {
    render(<InteractiveGeometry />);

    expect(screen.getByText(/Şekiller: 0/)).toBeInTheDocument();
    expect(screen.getByText(/Ölçümler: 0/)).toBeInTheDocument();
  });

  it('displays help text', () => {
    render(<InteractiveGeometry />);

    expect(screen.getByText(/Nasıl Kullanılır:/)).toBeInTheDocument();
    expect(screen.getByText(/Canvas üzerinde tıklayıp sürükleyin/)).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Canvas Initialization
// ============================================================

describe('InteractiveGeometry Component - Canvas', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes canvas context', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas');
    expect(canvas?.getContext).toHaveBeenCalledWith('2d');
  });

  it('draws grid on mount', () => {
    render(<InteractiveGeometry />);

    expect(mockContext.beginPath).toHaveBeenCalled();
    expect(mockContext.moveTo).toHaveBeenCalled();
    expect(mockContext.lineTo).toHaveBeenCalled();
    expect(mockContext.stroke).toHaveBeenCalled();
  });

  it('clears canvas on render', () => {
    render(<InteractiveGeometry />);

    expect(mockContext.clearRect).toHaveBeenCalledWith(0, 0, 800, 600);
  });
});

// ============================================================
// Tests: Tool Selection
// ============================================================

describe('InteractiveGeometry Component - Tool Selection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('selects line tool', () => {
    render(<InteractiveGeometry />);

    const lineButton = screen.getByTitle('Doğru');
    fireEvent.click(lineButton);

    expect(lineButton).toHaveClass('bg-blue-500', 'text-white');
  });

  it('selects circle tool', () => {
    render(<InteractiveGeometry />);

    const circleButton = screen.getByTitle('Daire');
    fireEvent.click(circleButton);

    expect(circleButton).toHaveClass('bg-blue-500', 'text-white');
  });

  it('selects rectangle tool', () => {
    render(<InteractiveGeometry />);

    const rectButton = screen.getByTitle('Dikdörtgen');
    fireEvent.click(rectButton);

    expect(rectButton).toHaveClass('bg-blue-500', 'text-white');
  });

  it('selects rotate tool', () => {
    render(<InteractiveGeometry />);

    const rotateButton = screen.getByTitle('Döndür');
    fireEvent.click(rotateButton);

    expect(rotateButton).toHaveClass('bg-blue-500', 'text-white');
  });

  it('selects reflect tool', () => {
    render(<InteractiveGeometry />);

    const reflectButton = screen.getByTitle('Yansıt');
    fireEvent.click(reflectButton);

    expect(reflectButton).toHaveClass('bg-blue-500', 'text-white');
  });

  it('selects translate tool', () => {
    render(<InteractiveGeometry />);

    const translateButton = screen.getByTitle('Ötle');
    fireEvent.click(translateButton);

    expect(translateButton).toHaveClass('bg-blue-500', 'text-white');
  });

  it('only one tool selected at a time', () => {
    render(<InteractiveGeometry />);

    const lineButton = screen.getByTitle('Doğru');
    const circleButton = screen.getByTitle('Daire');

    fireEvent.click(lineButton);
    expect(lineButton).toHaveClass('bg-blue-500');

    fireEvent.click(circleButton);
    expect(circleButton).toHaveClass('bg-blue-500');
    expect(lineButton).not.toHaveClass('bg-blue-500');
  });
});

// ============================================================
// Tests: Drawing Shapes - Line
// ============================================================

describe('InteractiveGeometry Component - Draw Line', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('draws line on mouse drag', () => {
    render(<InteractiveGeometry />);

    const lineButton = screen.getByTitle('Doğru');
    fireEvent.click(lineButton);

    const canvas = document.querySelector('canvas')!;

    // Start drawing
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 200, clientY: 200 });
    fireEvent.mouseUp(canvas);

    // Should draw line
    expect(mockContext.moveTo).toHaveBeenCalled();
    expect(mockContext.lineTo).toHaveBeenCalled();
  });

  it('updates shapes count after drawing line', () => {
    render(<InteractiveGeometry />);

    const lineButton = screen.getByTitle('Doğru');
    fireEvent.click(lineButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 200, clientY: 200 });
    fireEvent.mouseUp(canvas);

    expect(screen.getByText(/Şekiller: 1/)).toBeInTheDocument();
  });

  it('shows temporary line while dragging', () => {
    render(<InteractiveGeometry />);

    const lineButton = screen.getByTitle('Doğru');
    fireEvent.click(lineButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });

    // Should draw dashed line
    expect(mockContext.setLineDash).toHaveBeenCalledWith([5, 5]);
  });

  it('calls onToolUsage callback when line drawn', () => {
    const onToolUsage = vi.fn();
    render(<InteractiveGeometry onToolUsage={onToolUsage} />);

    const lineButton = screen.getByTitle('Doğru');
    fireEvent.click(lineButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 200, clientY: 200 });
    fireEvent.mouseUp(canvas);

    expect(onToolUsage).toHaveBeenCalledWith('line');
  });
});

// ============================================================
// Tests: Drawing Shapes - Circle
// ============================================================

describe('InteractiveGeometry Component - Draw Circle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('draws circle on mouse drag', () => {
    render(<InteractiveGeometry />);

    const circleButton = screen.getByTitle('Daire');
    fireEvent.click(circleButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
    fireEvent.mouseUp(canvas);

    // Should draw circle
    expect(mockContext.arc).toHaveBeenCalled();
  });

  it('updates shapes count after drawing circle', () => {
    render(<InteractiveGeometry />);

    const circleButton = screen.getByTitle('Daire');
    fireEvent.click(circleButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
    fireEvent.mouseUp(canvas);

    expect(screen.getByText(/Şekiller: 1/)).toBeInTheDocument();
  });

  it('shows temporary circle while dragging', () => {
    render(<InteractiveGeometry />);

    const circleButton = screen.getByTitle('Daire');
    fireEvent.click(circleButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });

    // Should draw dashed circle
    expect(mockContext.setLineDash).toHaveBeenCalledWith([5, 5]);
    expect(mockContext.arc).toHaveBeenCalled();
  });

  it('calls onToolUsage callback when circle drawn', () => {
    const onToolUsage = vi.fn();
    render(<InteractiveGeometry onToolUsage={onToolUsage} />);

    const circleButton = screen.getByTitle('Daire');
    fireEvent.click(circleButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
    fireEvent.mouseUp(canvas);

    expect(onToolUsage).toHaveBeenCalledWith('circle');
  });
});

// ============================================================
// Tests: Drawing Shapes - Rectangle
// ============================================================

describe('InteractiveGeometry Component - Draw Rectangle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('draws rectangle on mouse drag', () => {
    render(<InteractiveGeometry />);

    const rectButton = screen.getByTitle('Dikdörtgen');
    fireEvent.click(rectButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 50, clientY: 50 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 100 });
    fireEvent.mouseUp(canvas);

    // Should draw rectangle
    expect(mockContext.rect).toHaveBeenCalled();
  });

  it('updates shapes count after drawing rectangle', () => {
    render(<InteractiveGeometry />);

    const rectButton = screen.getByTitle('Dikdörtgen');
    fireEvent.click(rectButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 50, clientY: 50 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 100 });
    fireEvent.mouseUp(canvas);

    expect(screen.getByText(/Şekiller: 1/)).toBeInTheDocument();
  });

  it('shows temporary rectangle while dragging', () => {
    render(<InteractiveGeometry />);

    const rectButton = screen.getByTitle('Dikdörtgen');
    fireEvent.click(rectButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 50, clientY: 50 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 100 });

    // Should draw dashed rectangle
    expect(mockContext.setLineDash).toHaveBeenCalledWith([5, 5]);
    expect(mockContext.rect).toHaveBeenCalled();
  });

  it('calls onToolUsage callback when rectangle drawn', () => {
    const onToolUsage = vi.fn();
    render(<InteractiveGeometry onToolUsage={onToolUsage} />);

    const rectButton = screen.getByTitle('Dikdörtgen');
    fireEvent.click(rectButton);

    const canvas = document.querySelector('canvas')!;
    fireEvent.mouseDown(canvas, { clientX: 50, clientY: 50 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 100 });
    fireEvent.mouseUp(canvas);

    expect(onToolUsage).toHaveBeenCalledWith('rectangle');
  });
});

// ============================================================
// Tests: Multiple Shapes
// ============================================================

describe('InteractiveGeometry Component - Multiple Shapes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('draws multiple shapes', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;

    // Draw line
    const lineButton = screen.getByTitle('Doğru');
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 200, clientY: 200 });
    fireEvent.mouseUp(canvas);

    expect(screen.getByText(/Şekiller: 1/)).toBeInTheDocument();

    // Draw circle
    const circleButton = screen.getByTitle('Daire');
    fireEvent.click(circleButton);
    fireEvent.mouseDown(canvas, { clientX: 300, clientY: 300 });
    fireEvent.mouseMove(canvas, { clientX: 350, clientY: 350 });
    fireEvent.mouseUp(canvas);

    expect(screen.getByText(/Şekiller: 2/)).toBeInTheDocument();
  });

  it('preserves previous shapes when drawing new ones', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    // Draw first line
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseUp(canvas);

    // Draw second line
    fireEvent.mouseDown(canvas, { clientX: 200, clientY: 200 });
    fireEvent.mouseUp(canvas);

    expect(screen.getByText(/Şekiller: 2/)).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Measurements
// ============================================================

describe('InteractiveGeometry Component - Measurements', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('measures length of drawn shape', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    // Draw a line
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 0, clientY: 0 });
    fireEvent.mouseMove(canvas, { clientX: 300, clientY: 400 });
    fireEvent.mouseUp(canvas);

    // Measure it
    const measureButton = screen.getByTitle('Uzunluk Ölç');
    fireEvent.click(measureButton);

    expect(screen.getByText(/Ölçümler: 1/)).toBeInTheDocument();
  });

  it('shows alert when measuring without shapes', () => {
    render(<InteractiveGeometry />);

    const measureButton = screen.getByTitle('Uzunluk Ölç');
    fireEvent.click(measureButton);

    expect(global.alert).toHaveBeenCalledWith('Önce bir şekil çizin!');
  });

  it('displays measurement on canvas', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    // Draw and measure
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 0, clientY: 0 });
    fireEvent.mouseMove(canvas, { clientX: 100, clientY: 0 });
    fireEvent.mouseUp(canvas);

    const measureButton = screen.getByTitle('Uzunluk Ölç');
    fireEvent.click(measureButton);

    // Should draw measurement text
    expect(mockContext.fillText).toHaveBeenCalled();
  });

  it('measures multiple shapes', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');
    const measureButton = screen.getByTitle('Uzunluk Ölç');

    // Draw and measure first shape
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 0, clientY: 0 });
    fireEvent.mouseMove(canvas, { clientX: 100, clientY: 0 });
    fireEvent.mouseUp(canvas);
    fireEvent.click(measureButton);

    expect(screen.getByText(/Ölçümler: 1/)).toBeInTheDocument();

    // Draw and measure second shape
    fireEvent.mouseDown(canvas, { clientX: 200, clientY: 200 });
    fireEvent.mouseMove(canvas, { clientX: 300, clientY: 300 });
    fireEvent.mouseUp(canvas);
    fireEvent.click(measureButton);

    expect(screen.getByText(/Ölçümler: 2/)).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Clear Functionality
// ============================================================

describe('InteractiveGeometry Component - Clear', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('clears all shapes and measurements', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');
    const measureButton = screen.getByTitle('Uzunluk Ölç');

    // Draw shape and measure
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 200, clientY: 200 });
    fireEvent.mouseUp(canvas);
    fireEvent.click(measureButton);

    expect(screen.getByText(/Şekiller: 1/)).toBeInTheDocument();
    expect(screen.getByText(/Ölçümler: 1/)).toBeInTheDocument();

    // Clear
    const clearButton = screen.getByText('Temizle');
    fireEvent.click(clearButton);

    expect(screen.getByText(/Şekiller: 0/)).toBeInTheDocument();
    expect(screen.getByText(/Ölçümler: 0/)).toBeInTheDocument();
  });

  it('clears canvas visually', () => {
    render(<InteractiveGeometry />);

    const clearButton = screen.getByText('Temizle');
    fireEvent.click(clearButton);

    // clearRect should be called for clearing
    expect(mockContext.clearRect).toHaveBeenCalled();
  });
});

// ============================================================
// Tests: Save Usage
// ============================================================

describe('InteractiveGeometry Component - Save Usage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.post.mockResolvedValue({ data: { success: true } });
    vi.spyOn(Date, 'now')
      .mockReturnValueOnce(1000000) // Start time
      .mockReturnValueOnce(1060000); // Save time (60 seconds later)
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('saves usage data', async () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    // Draw a shape
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 200, clientY: 200 });
    fireEvent.mouseUp(canvas);

    // Save
    const saveButton = screen.getByText('Kaydet');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/manipulatives/geometry/tool-usage',
        expect.objectContaining({
          tool_type: 'line',
          shapes_created: expect.arrayContaining([
            expect.objectContaining({ type: 'line', points: 2 })
          ]),
          duration_seconds: expect.any(Number),
        })
      );
    });
  });

  it('shows success alert on save', async () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    // Draw and save
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseUp(canvas);

    const saveButton = screen.getByText('Kaydet');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith('Kullanım kaydedildi!');
    });
  });

  it('resets shapes and measurements after save', async () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    // Draw and save
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseUp(canvas);

    const saveButton = screen.getByText('Kaydet');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Şekiller: 0/)).toBeInTheDocument();
      expect(screen.getByText(/Ölçümler: 0/)).toBeInTheDocument();
    });
  });

  it('handles save error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.post.mockRejectedValue(new Error('Save failed'));

    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    // Draw and save
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseUp(canvas);

    const saveButton = screen.getByText('Kaydet');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Kullanım kaydedilemedi:',
        expect.any(Error)
      );
      expect(global.alert).toHaveBeenCalledWith(
        'Kullanım kaydedilemedi. Lütfen tekrar deneyin.'
      );
    });

    consoleSpy.mockRestore();
  });

  it('disables save button when no shapes', () => {
    render(<InteractiveGeometry />);

    const saveButton = screen.getByText('Kaydet');
    expect(saveButton).toBeDisabled();
  });

  it('enables save button after drawing', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    // Draw a shape
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseUp(canvas);

    const saveButton = screen.getByText('Kaydet');
    expect(saveButton).not.toBeDisabled();
  });

  it('includes measurements in save data', async () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');
    const measureButton = screen.getByTitle('Uzunluk Ölç');

    // Draw and measure
    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 0, clientY: 0 });
    fireEvent.mouseMove(canvas, { clientX: 100, clientY: 0 });
    fireEvent.mouseUp(canvas);
    fireEvent.click(measureButton);

    // Save
    const saveButton = screen.getByText('Kaydet');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/manipulatives/geometry/tool-usage',
        expect.objectContaining({
          measurements: expect.arrayContaining([
            expect.objectContaining({ type: 'length' })
          ])
        })
      );
    });
  });
});

// ============================================================
// Tests: Mouse Events
// ============================================================

describe('InteractiveGeometry Component - Mouse Events', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles mouse leave during drawing', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
    fireEvent.mouseLeave(canvas);

    // Should complete the shape
    expect(screen.getByText(/Şekiller: 1/)).toBeInTheDocument();
  });

  it('does not draw when mouse moves without mouseDown', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    fireEvent.click(lineButton);
    fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });

    // No shape should be created
    expect(screen.getByText(/Şekiller: 0/)).toBeInTheDocument();
  });

  it('does not draw with transformation tools', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const rotateButton = screen.getByTitle('Döndür');

    fireEvent.click(rotateButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseUp(canvas);

    // No shape should be created with transformation tool
    expect(screen.getByText(/Şekiller: 0/)).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Edge Cases
// ============================================================

describe('InteractiveGeometry Component - Edge Cases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles missing canvas context', () => {
    (HTMLCanvasElement.prototype.getContext as Mock).mockReturnValueOnce(null);

    // Should not crash
    render(<InteractiveGeometry />);

    expect(screen.getByText('İnteraktif Geometri')).toBeInTheDocument();
  });

  it('handles click without drag', () => {
    render(<InteractiveGeometry />);

    const canvas = document.querySelector('canvas')!;
    const lineButton = screen.getByTitle('Doğru');

    fireEvent.click(lineButton);
    fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
    fireEvent.mouseUp(canvas);

    // Should create shape even without drag
    expect(screen.getByText(/Şekiller: 1/)).toBeInTheDocument();
  });
});

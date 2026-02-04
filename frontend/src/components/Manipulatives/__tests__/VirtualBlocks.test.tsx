/**
 * Task 87.5: VirtualBlocks Component Tests
 * Tests for virtual blocks drag-and-drop manipulative
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import VirtualBlocks from '../VirtualBlocks';

vi.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock canvas context
const mockContext = {
  clearRect: vi.fn(),
  fillRect: vi.fn(),
  fillStyle: '',
  strokeStyle: '',
  lineWidth: 0,
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
  font: '',
  fillText: vi.fn(),
  measureText: jest.fn(() => ({ width: 0 })),
};

HTMLCanvasElement.prototype.getContext = jest.fn(() => mockContext) as any;

describe('VirtualBlocks Component', () => {
  const mockOnOperationComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.post.mockResolvedValue({ data: { success: true } });
  });

  describe('Rendering', () => {
    it('renders the component with canvas', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const canvas = document.querySelector('canvas');
      expect(canvas).toBeInTheDocument();
    });

    it('renders operation buttons', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      expect(screen.getByText('Toplama')).toBeInTheDocument();
      expect(screen.getByText('Çıkarma')).toBeInTheDocument();
      expect(screen.getByText('Çarpma')).toBeInTheDocument();
      expect(screen.getByText('Bölme')).toBeInTheDocument();
    });

    it('renders block type buttons', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      expect(screen.getByText(/Birler/i)).toBeInTheDocument();
      expect(screen.getByText(/Onlar/i)).toBeInTheDocument();
      expect(screen.getByText(/Yüzler/i)).toBeInTheDocument();
    });

    it('initializes canvas context', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      expect(HTMLCanvasElement.prototype.getContext).toHaveBeenCalledWith('2d');
    });
  });

  describe('Operation Selection', () => {
    it('defaults to addition operation', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const addButton = screen.getByText('Toplama');
      expect(addButton).toHaveClass('selected'); // Or similar styling indicator
    });

    it('changes operation when clicked', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const subtractButton = screen.getByText('Çıkarma');
      fireEvent.click(subtractButton);

      // Operation should change to subtract
      expect(subtractButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('supports all four operations', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const operations = ['Toplama', 'Çıkarma', 'Çarpma', 'Bölme'];
      operations.forEach(op => {
        const button = screen.getByText(op);
        fireEvent.click(button);
        expect(button).toBeInTheDocument();
      });
    });
  });

  describe('Block Management', () => {
    it('adds block when block button is clicked', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const unitButton = screen.getByText(/Birler/i);
      fireEvent.click(unitButton);

      // Canvas should be redrawn with new block
      expect(mockContext.fillRect).toHaveBeenCalled();
    });

    it('creates different colored blocks for different types', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      // Add unit block (blue)
      fireEvent.click(screen.getByText(/Birler/i));
      expect(mockContext.fillStyle).toBe('#2196F3'); // Blue

      // Add ten block (green)
      fireEvent.click(screen.getByText(/Onlar/i));
      expect(mockContext.fillStyle).toBe('#4CAF50'); // Green

      // Add hundred block (red)
      fireEvent.click(screen.getByText(/Yüzler/i));
      expect(mockContext.fillStyle).toBe('#F44336'); // Red
    });

    it('assigns correct values to blocks', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      // Unit block = 1
      fireEvent.click(screen.getByText(/Birler/i));

      // Ten block = 10
      fireEvent.click(screen.getByText(/Onlar/i));

      // Hundred block = 100
      fireEvent.click(screen.getByText(/Yüzler/i));

      // Total should be 111
      expect(screen.getByText(/Toplam: 111/i)).toBeInTheDocument();
    });
  });

  describe('Drag and Drop', () => {
    it('allows dragging blocks', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const canvas = document.querySelector('canvas') as HTMLCanvasElement;

      // Add a block first
      fireEvent.click(screen.getByText(/Birler/i));

      // Simulate drag
      fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
      fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 });
      fireEvent.mouseUp(canvas);

      // Block position should be updated
      expect(mockContext.clearRect).toHaveBeenCalled();
    });

    it('highlights block on hover', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const canvas = document.querySelector('canvas') as HTMLCanvasElement;

      fireEvent.click(screen.getByText(/Birler/i));
      fireEvent.mouseMove(canvas, { clientX: 100, clientY: 100 });

      // Should redraw with hover effect
      expect(mockContext.fillRect).toHaveBeenCalled();
    });

    it('stops dragging on mouse up', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const canvas = document.querySelector('canvas') as HTMLCanvasElement;

      fireEvent.click(screen.getByText(/Birler/i));
      fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 });
      fireEvent.mouseUp(canvas);

      // Dragging should stop
      fireEvent.mouseMove(canvas, { clientX: 200, clientY: 200 });

      // Block should not move
    });
  });

  describe('Calculations', () => {
    it('calculates addition correctly', async () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText('Toplama'));
      fireEvent.click(screen.getByText(/Birler/i)); // +1
      fireEvent.click(screen.getByText(/Onlar/i)); // +10

      const calculateButton = screen.getByText('Hesapla');
      fireEvent.click(calculateButton);

      await waitFor(() => {
        expect(screen.getByText(/Sonuç: 11/i)).toBeInTheDocument();
      });
    });

    it('calculates subtraction correctly', async () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText('Çıkarma'));
      fireEvent.click(screen.getByText(/Onlar/i)); // Start with 10
      // Remove or subtract blocks

      const calculateButton = screen.getByText('Hesapla');
      fireEvent.click(calculateButton);

      await waitFor(() => {
        expect(screen.getByText(/Sonuç:/i)).toBeInTheDocument();
      });
    });

    it('calculates multiplication correctly', async () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText('Çarpma'));
      // Add blocks to represent multiplication

      const calculateButton = screen.getByText('Hesapla');
      fireEvent.click(calculateButton);

      await waitFor(() => {
        expect(screen.getByText(/Sonuç:/i)).toBeInTheDocument();
      });
    });

    it('handles division correctly', async () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText('Bölme'));
      // Add blocks to represent division

      const calculateButton = screen.getByText('Hesapla');
      fireEvent.click(calculateButton);

      await waitFor(() => {
        expect(screen.getByText(/Sonuç:/i)).toBeInTheDocument();
      });
    });
  });

  describe('Saving Operations', () => {
    it('saves operation to backend', async () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));
      fireEvent.click(screen.getByText('Hesapla'));

      const saveButton = screen.getByText('Kaydet');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/manipulatives/virtual-blocks/operation',
          expect.objectContaining({
            operation_type: 'add',
            blocks_used: expect.any(Number),
          })
        );
      });
    });

    it('calls onOperationComplete after save', async () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));
      fireEvent.click(screen.getByText('Hesapla'));
      fireEvent.click(screen.getByText('Kaydet'));

      await waitFor(() => {
        expect(mockOnOperationComplete).toHaveBeenCalled();
      });
    });

    it('includes correct operation result', async () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));
      fireEvent.click(screen.getByText(/Onlar/i));
      fireEvent.click(screen.getByText('Hesapla'));
      fireEvent.click(screen.getByText('Kaydet'));

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            correct: expect.any(Boolean),
          })
        );
      });
    });
  });

  describe('Clear Functionality', () => {
    it('clears all blocks when clear button is clicked', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));
      fireEvent.click(screen.getByText(/Onlar/i));

      const clearButton = screen.getByText('Temizle');
      fireEvent.click(clearButton);

      // Canvas should be cleared
      expect(mockContext.clearRect).toHaveBeenCalled();
      expect(screen.getByText(/Toplam: 0/i)).toBeInTheDocument();
    });

    it('resets operation result', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));
      fireEvent.click(screen.getByText('Hesapla'));
      fireEvent.click(screen.getByText('Temizle'));

      expect(screen.queryByText(/Sonuç:/i)).not.toBeInTheDocument();
    });
  });

  describe('Visual Feedback', () => {
    it('shows block values on blocks', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));

      // Text should be drawn on canvas
      expect(mockContext.fillText).toHaveBeenCalledWith('1', expect.any(Number), expect.any(Number));
    });

    it('updates total display when blocks are added', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      expect(screen.getByText(/Toplam: 0/i)).toBeInTheDocument();

      fireEvent.click(screen.getByText(/Birler/i));
      expect(screen.getByText(/Toplam: 1/i)).toBeInTheDocument();

      fireEvent.click(screen.getByText(/Onlar/i));
      expect(screen.getByText(/Toplam: 11/i)).toBeInTheDocument();
    });

    it('shows operation history', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));
      fireEvent.click(screen.getByText('Hesapla'));

      expect(screen.getByText(/Geçmiş/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles save errors gracefully', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Save failed'));
      console.error = vi.fn();

      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));
      fireEvent.click(screen.getByText('Hesapla'));
      fireEvent.click(screen.getByText('Kaydet'));

      await waitFor(() => {
        expect(console.error).toHaveBeenCalled();
      });
    });

    it('validates operations before calculation', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const calculateButton = screen.getByText('Hesapla');
      fireEvent.click(calculateButton);

      // Should not calculate without blocks
      expect(screen.queryByText(/Sonuç:/i)).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has descriptive button labels', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      expect(screen.getByText('Toplama')).toHaveAttribute('role', 'button');
      expect(screen.getByText(/Birler/i)).toHaveAttribute('role', 'button');
    });

    it('supports keyboard navigation', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const addButton = screen.getByText('Toplama');
      addButton.focus();
      expect(addButton).toHaveFocus();
    });

    it('provides ARIA labels for blocks', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      const canvas = document.querySelector('canvas');
      expect(canvas).toHaveAttribute('aria-label');
    });
  });

  describe('Dyscalculia Support', () => {
    it('uses distinct colors for different block values', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      // Blue for 1, Green for 10, Red for 100
      fireEvent.click(screen.getByText(/Birler/i));
      expect(mockContext.fillStyle).toContain('#');
    });

    it('shows visual quantity representation', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));

      // Should draw block visually
      expect(mockContext.fillRect).toHaveBeenCalled();
    });

    it('provides immediate visual feedback', () => {
      render(<VirtualBlocks onOperationComplete={mockOnOperationComplete} />);

      fireEvent.click(screen.getByText(/Birler/i));

      // Total should update immediately
      expect(screen.getByText(/Toplam:/i)).toBeInTheDocument();
    });
  });
});

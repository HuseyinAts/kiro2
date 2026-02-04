/**
 * Task Progress Visualization Component Tests
 * 
 * Requirements: REQ-52.46 - REQ-52.50
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import TaskProgressVisualization from '../TaskProgressVisualization';

// Mock fetch
global.fetch = vi.fn();

const mockProgressData = {
  task_id: 'task-123',
  title: 'Matematik Sınavına Hazırlan',
  progress_percentage: 60,
  completed_subtasks: 3,
  total_subtasks: 5,
  estimated_minutes: 120,
  actual_minutes: 75,
  time_remaining_minutes: 45,
  milestones: [
    {
      percentage: 25,
      label: 'Başlangıç',
      reached: true,
      icon: '🚀',
      color: '#4CAF50'
    },
    {
      percentage: 50,
      label: 'Yarı Yol',
      reached: true,
      icon: '⚡',
      color: '#2196F3'
    },
    {
      percentage: 75,
      label: 'Son Çeyrek',
      reached: false,
      icon: '🎯',
      color: '#FF9800'
    },
    {
      percentage: 100,
      label: 'Tamamlandı',
      reached: false,
      icon: '🎉',
      color: '#4CAF50'
    }
  ],
  color: '#FF9800',
  status: 'in_progress'
};

describe('TaskProgressVisualization', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
    localStorage.setItem('token', 'test-token');
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('REQ-52.46: Progress Bar Gösterimi', () => {
    it('should display progress bar with correct percentage', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('60%')).toBeInTheDocument();
      });

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '60');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('should display progress bar with correct color', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toHaveStyle({ backgroundColor: '#FF9800' });
      });
    });

    it('should have ARIA label for accessibility', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toHaveAttribute('aria-label', 'Görev ilerleme yüzdesi: 60%');
      });
    });
  });

  describe('REQ-52.47: Tamamlanma Yüzdesi', () => {
    it('should display completion percentage', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('60%')).toBeInTheDocument();
      });
    });

    it('should display completed subtasks count', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText(/3/)).toBeInTheDocument();
        expect(screen.getByText(/5 alt görev tamamlandı/)).toBeInTheDocument();
      });
    });

    it('should calculate percentage correctly', async () => {
      const customData = {
        ...mockProgressData,
        completed_subtasks: 4,
        total_subtasks: 5,
        progress_percentage: 80
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => customData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('80%')).toBeInTheDocument();
      });
    });
  });

  describe('REQ-52.48: Görsel Milestone Göstergeleri', () => {
    it('should display all milestones', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('Başlangıç')).toBeInTheDocument();
        expect(screen.getByText('Yarı Yol')).toBeInTheDocument();
        expect(screen.getByText('Son Çeyrek')).toBeInTheDocument();
        expect(screen.getByText('Tamamlandı')).toBeInTheDocument();
      });
    });

    it('should show checkmark for reached milestones', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        const checkmarks = screen.getAllByText('✓');
        // 2 reached milestones + 1 in subtasks section
        expect(checkmarks.length).toBeGreaterThanOrEqual(2);
      });
    });

    it('should display milestone icons', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('🚀')).toBeInTheDocument();
        expect(screen.getByText('⚡')).toBeInTheDocument();
        expect(screen.getByText('🎯')).toBeInTheDocument();
        expect(screen.getByText('🎉')).toBeInTheDocument();
      });
    });

    it('should display milestone percentages', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('25%')).toBeInTheDocument();
        expect(screen.getByText('50%')).toBeInTheDocument();
        expect(screen.getByText('75%')).toBeInTheDocument();
        expect(screen.getByText('100%')).toBeInTheDocument();
      });
    });
  });

  describe('Loading and Error States', () => {
    it('should show loading state initially', () => {
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

      render(<TaskProgressVisualization taskId="task-123" />);

      expect(screen.getByText('İlerleme yükleniyor...')).toBeInTheDocument();
    });

    it('should show error state on fetch failure', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('Tekrar Dene')).toBeInTheDocument();
      });
    });

    it('should retry fetch on retry button click', async () => {
      (global.fetch as jest.Mock)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProgressData
        });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('Tekrar Dene')).toBeInTheDocument();
      });

      const retryButton = screen.getByText('Tekrar Dene');
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Matematik Sınavına Hazırlan')).toBeInTheDocument();
      });
    });
  });

  describe('Time Tracking', () => {
    it('should display estimated time', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('2 saat 0 dakika')).toBeInTheDocument();
      });
    });

    it('should display actual time', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('1 saat 15 dakika')).toBeInTheDocument();
      });
    });

    it('should display remaining time', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('45 dakika')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('should call onRefresh callback when custom action button is clicked', async () => {
      const mockOnRefresh = vi.fn();

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" onRefresh={mockOnRefresh} />);

      await waitFor(() => {
        expect(screen.getByText('Görevi Görüntüle')).toBeInTheDocument();
      });

      const customButton = screen.getByText('Görevi Görüntüle');
      fireEvent.click(customButton);

      expect(mockOnRefresh).toHaveBeenCalledTimes(1);
    });

    it('should refresh data when refresh button is clicked', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('🔄 Yenile')).toBeInTheDocument();
      });

      const refreshButton = screen.getByText('🔄 Yenile');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Status Display', () => {
    it('should display correct status badge for in_progress', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('Devam Ediyor')).toBeInTheDocument();
      });
    });

    it('should display correct status badge for completed', async () => {
      const completedData = {
        ...mockProgressData,
        status: 'completed',
        progress_percentage: 100
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => completedData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        expect(screen.getByText('Tamamlandı')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        const refreshButton = screen.getByLabelText('İlerlemeyi yenile');
        expect(refreshButton).toBeInTheDocument();
      });
    });

    it('should be keyboard navigable', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProgressData
      });

      render(<TaskProgressVisualization taskId="task-123" />);

      await waitFor(() => {
        const refreshButton = screen.getByText('🔄 Yenile');
        refreshButton.focus();
        expect(document.activeElement).toBe(refreshButton);
      });
    });
  });
});

/**
 * Focus Mode Component Tests
 * 
 * Requirements: REQ-52.21 - REQ-52.40
 * Task: 89 Focus Mode
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FocusMode from '../FocusMode';
import { vi, Mock } from 'vitest';

// Mock fetch with vitest Mock type
const fetchMock = vi.fn() as Mock;
global.fetch = fetchMock;

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => 'mock-token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock as any;

// Mock fullscreen API
document.documentElement.requestFullscreen = vi.fn();
document.exitFullscreen = vi.fn();

describe('FocusMode Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockClear();
  });

  describe('Setup View', () => {
    it('should render setup view when not active', () => {
      render(<FocusMode taskId="task1" />);
      
      expect(screen.getByText('🎯 Odak Modu')).toBeInTheDocument();
      expect(screen.getByText(/Dikkat dağıtıcı unsurları kaldırarak/)).toBeInTheDocument();
    });

    it('should fetch task data on mount - REQ-52.21', async () => {
      const mockTask = {
        id: 'task1',
        title: 'Matematik Çalışması',
        description: 'Türev konusunu çalış',
        estimated_duration_minutes: 45,
        priority: 'high',
        subject: 'Matematik'
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTask
      });

      render(<FocusMode taskId="task1" />);

      await waitFor(() => {
        expect(screen.getByText('Matematik Çalışması')).toBeInTheDocument();
      });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/adhd-support/focus-mode/task/task1',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token'
          })
        })
      );
    });

    it('should display loading state while fetching', () => {
      fetchMock.mockImplementation(() => new Promise(() => {}));

      render(<FocusMode taskId="task1" />);

      expect(screen.getByText('Görev yükleniyor...')).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('should display error state on fetch failure', async () => {
      fetchMock.mockRejectedValueOnce(new Error('Network error'));

      render(<FocusMode taskId="task1" />);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    it('should render all settings checkboxes - REQ-52.26, REQ-52.31, REQ-52.36', () => {
      render(<FocusMode taskId="task1" />);

      expect(screen.getByLabelText(/Kenar çubuğunu gizle/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Navigasyonu gizle/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Bildirimleri kapat/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Tam ekran modu/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Minimal arayüz/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Zamanlayıcıyı göster/)).toBeInTheDocument();
    });

    it('should toggle settings when checkboxes are clicked', () => {
      render(<FocusMode taskId="task1" />);

      const sidebarCheckbox = screen.getByLabelText(/Kenar çubuğunu gizle/) as HTMLInputElement;
      
      expect(sidebarCheckbox.checked).toBe(true);
      
      fireEvent.click(sidebarCheckbox);
      
      expect(sidebarCheckbox.checked).toBe(false);
    });

    it('should display keyboard shortcuts - REQ-52.40', () => {
      render(<FocusMode taskId="task1" />);

      expect(screen.getByText(/ESC/)).toBeInTheDocument();
      expect(screen.getByText(/F11/)).toBeInTheDocument();
    });
  });

  describe('Focus Mode Activation', () => {
    it('should activate focus mode when button clicked - REQ-52.23', async () => {
      const mockTask = {
        id: 'task1',
        title: 'Test Task',
        estimated_duration_minutes: 30,
        priority: 'medium'
      };

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTask
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, session_id: 'session1' })
        });

      render(<FocusMode taskId="task1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      const activateButton = screen.getByText(/Odak Modunu Başlat/);
      fireEvent.click(activateButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/adhd-support/focus-mode/activate',
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
              'Authorization': 'Bearer mock-token'
            })
          })
        );
      });
    });

    it('should apply body classes when activated - REQ-52.27, REQ-52.36, REQ-52.37', async () => {
      const mockTask = {
        id: 'task1',
        title: 'Test Task',
        estimated_duration_minutes: 30
      };

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTask
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(<FocusMode taskId="task1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      const activateButton = screen.getByText(/Odak Modunu Başlat/);
      fireEvent.click(activateButton);

      await waitFor(() => {
        expect(document.body.classList.contains('focus-mode-active')).toBe(true);
        expect(document.body.classList.contains('focus-mode-hide-sidebar')).toBe(true);
        expect(document.body.classList.contains('focus-mode-hide-navigation')).toBe(true);
        expect(document.body.classList.contains('focus-mode-hide-notifications')).toBe(true);
      });
    });

    it('should request fullscreen when enabled - REQ-52.38', async () => {
      const mockTask = {
        id: 'task1',
        title: 'Test Task',
        estimated_duration_minutes: 30
      };

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTask
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(<FocusMode taskId="task1" initialSettings={{ fullscreen_mode: true }} />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      const activateButton = screen.getByText(/Odak Modunu Başlat/);
      fireEvent.click(activateButton);

      await waitFor(() => {
        expect(document.documentElement.requestFullscreen).toHaveBeenCalled();
      });
    });
  });

  describe('Active Focus Mode View', () => {
    const setupActiveFocusMode = async () => {
      const mockTask = {
        id: 'task1',
        title: 'Matematik Çalışması',
        description: 'Türev konusunu çalış',
        estimated_duration_minutes: 45,
        priority: 'high',
        subject: 'Matematik'
      };

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTask
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      const { rerender } = render(<FocusMode taskId="task1" />);

      await waitFor(() => {
        expect(screen.getByText('Matematik Çalışması')).toBeInTheDocument();
      });

      const activateButton = screen.getByText(/Odak Modunu Başlat/);
      fireEvent.click(activateButton);

      await waitFor(() => {
        expect(document.body.classList.contains('focus-mode-active')).toBe(true);
      });

      return { rerender };
    };

    it('should display task title in active view - REQ-52.21', async () => {
      await setupActiveFocusMode();

      await waitFor(() => {
        const titles = screen.getAllByText('Matematik Çalışması');
        expect(titles.length).toBeGreaterThan(0);
      });
    });

    it('should display timer when enabled - REQ-52.29', async () => {
      await setupActiveFocusMode();

      await waitFor(() => {
        expect(screen.getByLabelText(/Kalan süre/)).toBeInTheDocument();
      });
    });

    it('should display progress bar - REQ-52.29', async () => {
      await setupActiveFocusMode();

      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toBeInTheDocument();
      });
    });

    it('should show exit button - REQ-52.24', async () => {
      await setupActiveFocusMode();

      await waitFor(() => {
        const exitButton = screen.getByLabelText(/Odak modundan çık/);
        expect(exitButton).toBeInTheDocument();
      });
    });
  });

  describe('Focus Mode Deactivation', () => {
    it('should deactivate focus mode on exit button click - REQ-52.24', async () => {
      const mockTask = {
        id: 'task1',
        title: 'Test Task',
        estimated_duration_minutes: 30
      };

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTask
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, focus_time_minutes: 5 })
        });

      const onExit = vi.fn();
      render(<FocusMode taskId="task1" onExit={onExit} />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      // Activate
      const activateButton = screen.getByText(/Odak Modunu Başlat/);
      fireEvent.click(activateButton);

      await waitFor(() => {
        expect(document.body.classList.contains('focus-mode-active')).toBe(true);
      });

      // Deactivate
      const exitButton = screen.getByLabelText(/Odak modundan çık/);
      fireEvent.click(exitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/adhd-support/focus-mode/deactivate',
          expect.objectContaining({
            method: 'POST'
          })
        );
      });

      expect(onExit).toHaveBeenCalled();
    });

    it('should remove body classes on deactivation - REQ-52.25', async () => {
      const mockTask = {
        id: 'task1',
        title: 'Test Task',
        estimated_duration_minutes: 30
      };

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTask
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(<FocusMode taskId="task1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      // Activate
      const activateButton = screen.getByText(/Odak Modunu Başlat/);
      fireEvent.click(activateButton);

      await waitFor(() => {
        expect(document.body.classList.contains('focus-mode-active')).toBe(true);
      });

      // Deactivate
      const exitButton = screen.getByLabelText(/Odak modundan çık/);
      fireEvent.click(exitButton);

      await waitFor(() => {
        expect(document.body.classList.contains('focus-mode-active')).toBe(false);
        expect(document.body.classList.contains('focus-mode-hide-sidebar')).toBe(false);
      });
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('should exit focus mode on ESC key - REQ-52.40', async () => {
      const mockTask = {
        id: 'task1',
        title: 'Test Task',
        estimated_duration_minutes: 30
      };

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTask
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(<FocusMode taskId="task1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      // Activate
      const activateButton = screen.getByText(/Odak Modunu Başlat/);
      fireEvent.click(activateButton);

      await waitFor(() => {
        expect(document.body.classList.contains('focus-mode-active')).toBe(true);
      });

      // Press ESC
      fireEvent.keyDown(window, { key: 'Escape' });

      await waitFor(() => {
        expect(document.body.classList.contains('focus-mode-active')).toBe(false);
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels - REQ-52.30', () => {
      render(<FocusMode taskId="task1" />);

      expect(screen.getByRole('main') || screen.getByText(/Odak Modu/)).toBeInTheDocument();
    });

    it('should provide screen reader status updates - REQ-52.30', async () => {
      const mockTask = {
        id: 'task1',
        title: 'Test Task',
        estimated_duration_minutes: 30
      };

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockTask
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true })
        });

      render(<FocusMode taskId="task1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      const activateButton = screen.getByText(/Odak Modunu Başlat/);
      fireEvent.click(activateButton);

      await waitFor(() => {
        const srOnly = document.querySelector('.sr-only');
        expect(srOnly).toBeInTheDocument();
      });
    });
  });

  describe('Requirements Coverage', () => {
    it('REQ-52.21: Single-task view (sadece aktif görev görünür)', async () => {
      const mockTask = {
        id: 'task1',
        title: 'Single Task',
        estimated_duration_minutes: 30
      };

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockTask
      });

      render(<FocusMode taskId="task1" />);

      await waitFor(() => {
        expect(screen.getByText('Single Task')).toBeInTheDocument();
      });
    });

    it('REQ-52.26: Minimal interface (minimal arayüz)', () => {
      render(<FocusMode taskId="task1" initialSettings={{ minimal_ui: true }} />);

      const minimalCheckbox = screen.getByLabelText(/Minimal arayüz/) as HTMLInputElement;
      expect(minimalCheckbox.checked).toBe(true);
    });

    it('REQ-52.31: Notification suppression (bildirimler kapalı)', () => {
      render(<FocusMode taskId="task1" initialSettings={{ hide_notifications: true }} />);

      const notifCheckbox = screen.getByLabelText(/Bildirimleri kapat/) as HTMLInputElement;
      expect(notifCheckbox.checked).toBe(true);
    });

    it('REQ-52.36: Hide sidebar (kenar çubuğunu gizle)', () => {
      render(<FocusMode taskId="task1" initialSettings={{ hide_sidebar: true }} />);

      const sidebarCheckbox = screen.getByLabelText(/Kenar çubuğunu gizle/) as HTMLInputElement;
      expect(sidebarCheckbox.checked).toBe(true);
    });

    it('REQ-52.37: Hide navigation (navigasyonu gizle)', () => {
      render(<FocusMode taskId="task1" initialSettings={{ hide_navigation: true }} />);

      const navCheckbox = screen.getByLabelText(/Navigasyonu gizle/) as HTMLInputElement;
      expect(navCheckbox.checked).toBe(true);
    });

    it('REQ-52.38: Fullscreen mode (tam ekran modu)', () => {
      render(<FocusMode taskId="task1" initialSettings={{ fullscreen_mode: true }} />);

      const fullscreenCheckbox = screen.getByLabelText(/Tam ekran modu/) as HTMLInputElement;
      expect(fullscreenCheckbox.checked).toBe(true);
    });
  });
});

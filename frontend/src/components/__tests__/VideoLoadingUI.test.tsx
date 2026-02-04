/**
 * VideoLoadingUI Component Tests
 * 
 * Test coverage for VideoLoadingUI component
 * 
 * @module VideoLoadingUI.test
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { VideoLoadingUI } from '../VideoLoadingUI';
import { VideoLoadingState } from '../../services/VideoLoadingManager';
import { vi } from 'vitest';

describe('VideoLoadingUI Component', () => {
  // Helper function to create mock state
  const createMockState = (overrides: Partial<VideoLoadingState> = {}): VideoLoadingState => ({
    status: 'idle',
    videos: [],
    error: null,
    loadingProgress: 0,
    retryCount: 0,
    requestId: '',
    loadingTime: 0,
    ...overrides,
  });

  describe('Idle State', () => {
    it('should render nothing when status is idle', () => {
      const state = createMockState({ status: 'idle' });
      const { container } = render(<VideoLoadingUI state={state} />);
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Loading State', () => {
    it('should render loading spinner and progress bar', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 50,
      });

      render(<VideoLoadingUI state={state} />);

      // Check for loading message
      expect(screen.getByText(/AI size özel videoları buluyor/i)).toBeInTheDocument();

      // Check for progress indicator
      expect(screen.getByText(/Videolar aranıyor/i)).toBeInTheDocument();
    });

    it('should display correct progress message based on progress value', () => {
      const { rerender } = render(
        <VideoLoadingUI state={createMockState({ status: 'loading', loadingProgress: 20 })} />
      );
      expect(screen.getByText(/Bağlantı kuruluyor/i)).toBeInTheDocument();

      rerender(
        <VideoLoadingUI state={createMockState({ status: 'loading', loadingProgress: 50 })} />
      );
      expect(screen.getByText(/Videolar aranıyor/i)).toBeInTheDocument();

      rerender(
        <VideoLoadingUI state={createMockState({ status: 'loading', loadingProgress: 80 })} />
      );
      expect(screen.getByText(/Sonuçlar hazırlanıyor/i)).toBeInTheDocument();
    });

    it('should display retry count when retrying', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 30,
        retryCount: 1,
      });

      render(<VideoLoadingUI state={state} />);
      expect(screen.getByText(/Yeniden deneme: 1\. deneme/i)).toBeInTheDocument();
    });
  });

  describe('Success State', () => {
    it('should render success message with video count', () => {
      const state = createMockState({
        status: 'success',
        videos: [
          {
            subject_exam: 'TYT Matematik',
            videos: [
              {
                video_id: '1',
                title: 'Test Video 1',
                channel: 'Test Channel',
                duration: '10:00',
                quality_score: 8.5,
                subject: 'matematik',
                url: 'https://youtube.com/watch?v=1',
              },
              {
                video_id: '2',
                title: 'Test Video 2',
                channel: 'Test Channel',
                duration: '15:00',
                quality_score: 9.0,
                subject: 'matematik',
                url: 'https://youtube.com/watch?v=2',
              },
            ],
            total_count: 2,
          },
        ],
        loadingTime: 2500,
      });

      render(<VideoLoadingUI state={state} />);

      expect(screen.getByText(/Videolar Başarıyla Yüklendi/i)).toBeInTheDocument();
      expect(screen.getByText(/2 video bulundu/i)).toBeInTheDocument();
      expect(screen.getByText(/Yükleme süresi: 2\.5s/i)).toBeInTheDocument();
    });

    it('should display cache hit indicator when cache is hit', () => {
      const state = createMockState({
        status: 'success',
        videos: [
          {
            subject_exam: 'TYT Matematik',
            videos: [],
            total_count: 0,
          },
        ],
        loadingTime: 100,
        cacheHit: true,
      });

      render(<VideoLoadingUI state={state} />);
      expect(screen.getByText(/Hızlı yükleme \(önbellekten\)/i)).toBeInTheDocument();
    });

    it('should display subject count when multiple subjects', () => {
      const state = createMockState({
        status: 'success',
        videos: [
          {
            subject_exam: 'TYT Matematik',
            videos: [
              {
                video_id: '1',
                title: 'Test Video',
                channel: 'Test Channel',
                duration: '10:00',
                quality_score: 8.5,
                subject: 'matematik',
                url: 'https://youtube.com/watch?v=1',
              },
            ],
            total_count: 1,
          },
          {
            subject_exam: 'TYT Fizik',
            videos: [
              {
                video_id: '2',
                title: 'Test Video',
                channel: 'Test Channel',
                duration: '10:00',
                quality_score: 8.5,
                subject: 'fizik',
                url: 'https://youtube.com/watch?v=2',
              },
            ],
            total_count: 1,
          },
        ],
        loadingTime: 3000,
      });

      render(<VideoLoadingUI state={state} />);
      expect(screen.getByText(/2 video bulundu \(2 farklı konu\)/i)).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should render error message and retry button', () => {
      const onRetry = vi.fn();
      const state = createMockState({
        status: 'error',
        error: new Error('Network error'),
        errorMessage: 'İnternet bağlantınızı kontrol edin.',
        retryCount: 1,
      });

      render(<VideoLoadingUI state={state} onRetry={onRetry} />);

      expect(screen.getByText(/Video Yükleme Hatası/i)).toBeInTheDocument();
      expect(screen.getByText(/İnternet bağlantınızı kontrol edin/i)).toBeInTheDocument();

      const retryButton = screen.getByText(/Tekrar Dene/i);
      expect(retryButton).toBeInTheDocument();

      fireEvent.click(retryButton);
      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('should render fallback button', () => {
      const onShowFallback = vi.fn();
      const state = createMockState({
        status: 'error',
        error: new Error('Timeout'),
        errorMessage: 'İstek zaman aşımına uğradı.',
        retryCount: 0,
      });

      render(<VideoLoadingUI state={state} onShowFallback={onShowFallback} />);

      const fallbackButton = screen.getByText(/Örnek Videoları Göster/i);
      expect(fallbackButton).toBeInTheDocument();

      fireEvent.click(fallbackButton);
      expect(onShowFallback).toHaveBeenCalledTimes(1);
    });

    it('should not render retry button when max retries reached', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Max retries'),
        errorMessage: 'Maksimum deneme sayısına ulaşıldı.',
        retryCount: 2, // Max retries
      });

      render(<VideoLoadingUI state={state} />);

      expect(screen.queryByText(/Tekrar Dene/i)).not.toBeInTheDocument();
      expect(screen.getByText(/Örnek Videoları Göster/i)).toBeInTheDocument();
    });

    it('should display retry count', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
        retryCount: 1,
      });

      render(<VideoLoadingUI state={state} />);
      expect(screen.getByText(/1 kez denendi/i)).toBeInTheDocument();
    });

    it('should display troubleshooting tips', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
      });

      render(<VideoLoadingUI state={state} />);
      expect(screen.getByText(/Sorun giderme önerileri/i)).toBeInTheDocument();
      expect(screen.getByText(/İnternet bağlantınızı kontrol edin/i)).toBeInTheDocument();
    });
  });

  describe('Fallback State', () => {
    it('should render fallback message and button', () => {
      const onShowFallback = vi.fn();
      const state = createMockState({
        status: 'fallback',
        error: new Error('Timeout'),
        errorMessage: 'Videoları 20 saniye içinde yükleyemedik.',
      });

      render(<VideoLoadingUI state={state} onShowFallback={onShowFallback} />);

      expect(screen.getByText(/Kişiselleştirilmiş Videolar Yüklenemedi/i)).toBeInTheDocument();
      expect(screen.getByText(/Videoları 20 saniye içinde yükleyemedik/i)).toBeInTheDocument();

      const fallbackButton = screen.getByText(/Örnek Videoları Göster/i);
      expect(fallbackButton).toBeInTheDocument();

      fireEvent.click(fallbackButton);
      expect(onShowFallback).toHaveBeenCalledTimes(1);
    });

    it('should display informational note', () => {
      const state = createMockState({
        status: 'fallback',
        error: new Error('Timeout'),
      });

      render(<VideoLoadingUI state={state} />);
      expect(
        screen.getByText(/Örnek videolar genel eğitim içerikleridir/i)
      ).toBeInTheDocument();
    });
  });

  describe('Button Interactions', () => {
    it('should handle retry button hover effects', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
        retryCount: 0,
      });

      render(<VideoLoadingUI state={state} onRetry={() => {}} />);

      const retryButton = screen.getByText(/Tekrar Dene/i);

      // Simulate hover
      fireEvent.mouseOver(retryButton);
      expect(retryButton).toHaveStyle({ backgroundColor: '#0056b3' });

      // Simulate mouse out
      fireEvent.mouseOut(retryButton);
      expect(retryButton).toHaveStyle({ backgroundColor: '#007bff' });
    });

    it('should handle fallback button hover effects', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
      });

      render(<VideoLoadingUI state={state} onShowFallback={() => {}} />);

      const fallbackButton = screen.getByText(/Örnek Videoları Göster/i);

      // Simulate hover
      fireEvent.mouseOver(fallbackButton);
      expect(fallbackButton).toHaveStyle({ backgroundColor: '#5a6268' });

      // Simulate mouse out
      fireEvent.mouseOut(fallbackButton);
      expect(fallbackButton).toHaveStyle({ backgroundColor: '#6c757d' });
    });
  });

  describe('Animations', () => {
    it('should apply fadeIn animation to loading state', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 50,
      });

      const { container } = render(<VideoLoadingUI state={state} />);
      const loadingContainer = container.firstChild as HTMLElement;

      expect(loadingContainer).toHaveStyle({ animation: 'fadeIn 0.3s ease-in' });
    });

    it('should apply fadeIn animation to success state', () => {
      const state = createMockState({
        status: 'success',
        videos: [],
        loadingTime: 1000,
      });

      const { container } = render(<VideoLoadingUI state={state} />);
      const successContainer = container.firstChild as HTMLElement;

      expect(successContainer).toHaveStyle({ animation: 'fadeIn 0.5s ease-in' });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty videos array in success state', () => {
      const state = createMockState({
        status: 'success',
        videos: [],
        loadingTime: 1000,
      });

      render(<VideoLoadingUI state={state} />);
      expect(screen.getByText(/0 video bulundu/i)).toBeInTheDocument();
    });

    it('should handle missing error message', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Unknown error'),
        errorMessage: undefined,
      });

      render(<VideoLoadingUI state={state} />);
      expect(screen.getByText(/Unknown error/i)).toBeInTheDocument();
    });

    it('should handle missing callbacks gracefully', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
      });

      // Should not throw error when callbacks are missing
      expect(() => {
        render(<VideoLoadingUI state={state} />);
      }).not.toThrow();
    });
  });
});

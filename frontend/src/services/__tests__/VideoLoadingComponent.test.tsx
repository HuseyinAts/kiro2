/**
 * Video Loading Component Tests
 * 
 * Component tests for video loading states and error handling
 * Tests the integration of VideoLoadingManager and VideoErrorHandler in React components
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import React, { useState, useEffect } from 'react';
import {
  VideoLoadingManager,
  StudentProfile,
  VideoLoadingState,
  SubjectVideos,
} from '../VideoLoadingManager';
import { VideoErrorHandler } from '../VideoErrorHandler';

/**
 * Test Component: VideoLoadingComponent
 * 
 * Simulates a real component that uses VideoLoadingManager and VideoErrorHandler
 */
interface VideoLoadingComponentProps {
  profile: StudentProfile;
  manager: VideoLoadingManager;
  errorHandler: VideoErrorHandler;
}

const VideoLoadingComponent: React.FC<VideoLoadingComponentProps> = ({
  profile,
  manager,
  errorHandler,
}) => {
  const [state, setState] = useState<VideoLoadingState>(manager.getState());
  const [userErrorMessage, setUserErrorMessage] = useState<string>('');

  useEffect(() => {
    // Subscribe to state changes
    const unsubscribe = manager.subscribe((newState) => {
      setState(newState);

      // Handle errors
      if (newState.error) {
        const videoError = errorHandler.handleError(newState.error, {
          requestId: newState.requestId,
        });
        setUserErrorMessage(videoError.userMessage);
      }
    });

    return () => unsubscribe();
  }, [manager, errorHandler]);

  const handleLoadVideos = async () => {
    try {
      await manager.loadVideos(profile);
    } catch (error) {
      // Error is already handled by the manager
      console.error('Failed to load videos:', error);
    }
  };

  const handleRetry = () => {
    manager.reset();
    handleLoadVideos();
  };

  const handleCancel = () => {
    manager.cancelLoad();
  };

  // Render based on state
  return (
    <div data-testid="video-loading-component">
      {/* Idle State */}
      {state.status === 'idle' && (
        <div data-testid="idle-state">
          <h2>Video Önerileri</h2>
          <button onClick={handleLoadVideos} data-testid="load-button">
            Videoları Yükle
          </button>
        </div>
      )}

      {/* Loading State */}
      {state.status === 'loading' && (
        <div data-testid="loading-state">
          <h2>🤖 AI size özel videoları buluyor...</h2>
          <div data-testid="progress-bar">
            <div style={{ width: `${state.loadingProgress}%` }}>
              {state.loadingProgress}%
            </div>
          </div>
          <p data-testid="loading-message">
            Videolar hazırlanıyor, lütfen bekleyin...
          </p>
          <button onClick={handleCancel} data-testid="cancel-button">
            İptal Et
          </button>
        </div>
      )}

      {/* Success State */}
      {state.status === 'success' && (
        <div data-testid="success-state">
          <h2>✅ Videolar Hazır!</h2>
          <p data-testid="video-count">
            {state.videos.length} konu için video bulundu
          </p>
          <p data-testid="loading-time">
            Yükleme süresi: {state.loadingTime}ms
          </p>
          {state.cacheHit && (
            <p data-testid="cache-hit">⚡ Cache'den yüklendi</p>
          )}
          <div data-testid="video-list">
            {state.videos.map((subject, index) => (
              <div key={index} data-testid={`subject-${index}`}>
                <h3>{subject.subject_exam}</h3>
                <p>{subject.videos.length} video</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error State */}
      {state.status === 'error' && (
        <div data-testid="error-state">
          <h2>❌ Hata Oluştu</h2>
          <p data-testid="error-message">{userErrorMessage}</p>
          <p data-testid="retry-count">Deneme sayısı: {state.retryCount}</p>
          <button onClick={handleRetry} data-testid="retry-button">
            🔄 Tekrar Dene
          </button>
          <button onClick={() => manager.reset()} data-testid="reset-button">
            Sıfırla
          </button>
        </div>
      )}

      {/* Fallback State */}
      {state.status === 'fallback' && (
        <div data-testid="fallback-state">
          <h2>⚠️ Örnek Videolar</h2>
          <p data-testid="fallback-message">
            Kişiselleştirilmiş videolar şu anda hazırlanamadı. Örnek videolar
            gösteriliyor.
          </p>
          <button onClick={handleRetry} data-testid="retry-button">
            Tekrar Dene
          </button>
        </div>
      )}
    </div>
  );
};

describe('VideoLoadingComponent', () => {
  let manager: VideoLoadingManager;
  let errorHandler: VideoErrorHandler;
  let mockFetch: ReturnType<typeof vi.fn>;

  const mockProfile: StudentProfile = {
    goals: ['TYT Matematik', 'TYT Fizik'],
    currentLevel: { matematik: 50, fizik: 60 },
    learningStyle: 'visual',
  };

  beforeEach(() => {
    // Create instances
    manager = new VideoLoadingManager('http://localhost:8001', 5000, 2);
    errorHandler = new VideoErrorHandler(false, false);

    // Mock fetch
    mockFetch = vi.fn();
    global.fetch = mockFetch;

    // Mock timers
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Idle State', () => {
    it('should render idle state initially', () => {
      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={manager}
          errorHandler={errorHandler}
        />
      );

      expect(screen.getByTestId('idle-state')).toBeInTheDocument();
      expect(screen.getByTestId('load-button')).toBeInTheDocument();
      expect(screen.getByText('Video Önerileri')).toBeInTheDocument();
    });

    it('should start loading when load button is clicked', async () => {
      const mockVideos: SubjectVideos[] = [
        {
          subject_exam: 'TYT_matematik',
          videos: [
            {
              video_id: 'test123',
              title: 'Test Video',
              channel: 'Test Channel',
              duration: '10:00',
              quality_score: 8.5,
              subject: 'matematik',
              url: 'https://youtube.com/test',
            },
          ],
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockVideos }),
      });

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={manager}
          errorHandler={errorHandler}
        />
      );

      // Click load button
      fireEvent.click(screen.getByTestId('load-button'));

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should display loading state with progress', async () => {
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({ recommendations: [] }),
                }),
              1000
            )
          )
      );

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={manager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Wait for loading state
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toBeInTheDocument();
      });

      // Check loading elements
      expect(
        screen.getByText(/AI size özel videoları buluyor/)
      ).toBeInTheDocument();
      expect(screen.getByTestId('progress-bar')).toBeInTheDocument();
      expect(screen.getByTestId('loading-message')).toBeInTheDocument();
      expect(screen.getByTestId('cancel-button')).toBeInTheDocument();
    });

    it('should show progress updates', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: [] }),
      });

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={manager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Wait for loading state
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toBeInTheDocument();
      });

      // Progress bar should exist
      const progressBar = screen.getByTestId('progress-bar');
      expect(progressBar).toBeInTheDocument();
    });

    it('should allow cancellation during loading', async () => {
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({ recommendations: [] }),
                }),
              10000
            )
          )
      );

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={manager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Wait for loading state
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toBeInTheDocument();
      });

      // Click cancel
      fireEvent.click(screen.getByTestId('cancel-button'));

      // Should return to idle state
      await waitFor(() => {
        expect(screen.getByTestId('idle-state')).toBeInTheDocument();
      });
    });
  });

  describe('Success State', () => {
    it('should display success state with videos', async () => {
      const mockVideos: SubjectVideos[] = [
        {
          subject_exam: 'TYT_matematik',
          videos: [
            {
              video_id: 'test123',
              title: 'Matematik Video',
              channel: 'Test Channel',
              duration: '10:00',
              quality_score: 8.5,
              subject: 'matematik',
              url: 'https://youtube.com/test',
            },
          ],
        },
        {
          subject_exam: 'TYT_fizik',
          videos: [
            {
              video_id: 'test456',
              title: 'Fizik Video',
              channel: 'Test Channel',
              duration: '15:00',
              quality_score: 9.0,
              subject: 'fizik',
              url: 'https://youtube.com/test2',
            },
          ],
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockVideos }),
      });

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={manager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Wait for success state
      await waitFor(() => {
        expect(screen.getByTestId('success-state')).toBeInTheDocument();
      });

      // Check success elements
      expect(screen.getByText('✅ Videolar Hazır!')).toBeInTheDocument();
      expect(screen.getByTestId('video-count')).toHaveTextContent(
        '2 konu için video bulundu'
      );
      expect(screen.getByTestId('loading-time')).toBeInTheDocument();
      expect(screen.getByTestId('video-list')).toBeInTheDocument();
    });

    it('should show cache hit indicator', async () => {
      const mockVideos: SubjectVideos[] = [
        {
          subject_exam: 'TYT_matematik',
          videos: [],
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockVideos, cache_hit: true }),
      });

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={manager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Wait for success state
      await waitFor(() => {
        expect(screen.getByTestId('success-state')).toBeInTheDocument();
      });

      // Check cache hit indicator
      expect(screen.getByTestId('cache-hit')).toBeInTheDocument();
      expect(screen.getByText('⚡ Cache\'den yüklendi')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error state with user-friendly message', async () => {
      // Create manager with no retries for this test
      const noRetryManager = new VideoLoadingManager(
        'http://localhost:8001',
        5000,
        0
      );

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={noRetryManager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByTestId('error-state')).toBeInTheDocument();
      });

      // Check error elements
      expect(screen.getByText('❌ Hata Oluştu')).toBeInTheDocument();
      expect(screen.getByTestId('error-message')).toBeInTheDocument();
      expect(screen.getByTestId('retry-button')).toBeInTheDocument();
      expect(screen.getByTestId('reset-button')).toBeInTheDocument();
    });

    it('should show Turkish error message for network error', async () => {
      const noRetryManager = new VideoLoadingManager(
        'http://localhost:8001',
        5000,
        0
      );

      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={noRetryManager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByTestId('error-state')).toBeInTheDocument();
      });

      // Check Turkish error message
      const errorMessage = screen.getByTestId('error-message');
      expect(errorMessage).toHaveTextContent(/İnternet/);
    });

    it('should allow retry after error', async () => {
      const noRetryManager = new VideoLoadingManager(
        'http://localhost:8001',
        5000,
        0
      );

      // First call fails
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={noRetryManager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByTestId('error-state')).toBeInTheDocument();
      });

      // Second call succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: [] }),
      });

      // Click retry
      fireEvent.click(screen.getByTestId('retry-button'));

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toBeInTheDocument();
      });
    });

    it('should show retry count', async () => {
      const noRetryManager = new VideoLoadingManager(
        'http://localhost:8001',
        5000,
        0
      );

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={noRetryManager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByTestId('error-state')).toBeInTheDocument();
      });

      // Check retry count
      expect(screen.getByTestId('retry-count')).toBeInTheDocument();
    });
  });

  describe('Fallback State', () => {
    it('should display fallback state after timeout', async () => {
      // Mock timeout
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({ recommendations: [] }),
                }),
              10000
            )
          )
      );

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={manager}
          errorHandler={errorHandler}
        />
      );

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Fast-forward time to trigger timeout
      vi.advanceTimersByTime(6000);

      // Wait for fallback state
      await waitFor(() => {
        expect(screen.queryByTestId('fallback-state')).toBeInTheDocument();
      });
    });
  });

  describe('State Transitions', () => {
    it('should transition from idle -> loading -> success', async () => {
      const mockVideos: SubjectVideos[] = [
        {
          subject_exam: 'TYT_matematik',
          videos: [],
        },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: mockVideos }),
      });

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={manager}
          errorHandler={errorHandler}
        />
      );

      // Initial state: idle
      expect(screen.getByTestId('idle-state')).toBeInTheDocument();

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Loading state
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toBeInTheDocument();
      });

      // Success state
      await waitFor(() => {
        expect(screen.getByTestId('success-state')).toBeInTheDocument();
      });
    });

    it('should transition from idle -> loading -> error', async () => {
      const noRetryManager = new VideoLoadingManager(
        'http://localhost:8001',
        5000,
        0
      );

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      render(
        <VideoLoadingComponent
          profile={mockProfile}
          manager={noRetryManager}
          errorHandler={errorHandler}
        />
      );

      // Initial state: idle
      expect(screen.getByTestId('idle-state')).toBeInTheDocument();

      // Start loading
      fireEvent.click(screen.getByTestId('load-button'));

      // Loading state
      await waitFor(() => {
        expect(screen.getByTestId('loading-state')).toBeInTheDocument();
      });

      // Error state
      await waitFor(() => {
        expect(screen.getByTestId('error-state')).toBeInTheDocument();
      });
    });
  });
});

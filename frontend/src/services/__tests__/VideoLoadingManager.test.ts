/**
 * VideoLoadingManager Tests
 * 
 * Unit tests for VideoLoadingManager service
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { VideoLoadingManager, StudentProfile, VideoLoadingState } from '../VideoLoadingManager';

describe('VideoLoadingManager', () => {
  let manager: VideoLoadingManager;
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Create manager instance
    manager = new VideoLoadingManager('http://localhost:8001', 5000, 2);

    // Mock fetch
    mockFetch = vi.fn();
    global.fetch = mockFetch;

    // Mock setTimeout and clearTimeout
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Constructor', () => {
    it('should initialize with default values', () => {
      const state = manager.getState();
      
      expect(state.status).toBe('idle');
      expect(state.videos).toEqual([]);
      expect(state.error).toBeNull();
      expect(state.loadingProgress).toBe(0);
      expect(state.retryCount).toBe(0);
    });

    it('should accept custom configuration', () => {
      const customManager = new VideoLoadingManager('http://custom-api.com', 10000, 3);
      expect(customManager).toBeDefined();
    });
  });

  describe('loadVideos', () => {
    const mockProfile: StudentProfile = {
      goals: ['TYT Matematik'],
      currentLevel: { matematik: 50 },
      learningStyle: 'visual',
    };

    it('should successfully load videos', async () => {
      // Mock successful response
      const mockVideos = [
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

      // Load videos
      const result = await manager.loadVideos(mockProfile);

      // Verify
      expect(result).toEqual(mockVideos);
      expect(manager.getState().status).toBe('success');
      expect(manager.getState().videos).toEqual(mockVideos);
      expect(manager.getState().error).toBeNull();
    });

    it('should update loading progress during load', async () => {
      const progressUpdates: number[] = [];

      // Subscribe to state changes
      manager.subscribe((state) => {
        progressUpdates.push(state.loadingProgress);
      });

      // Mock successful response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ recommendations: [] }),
      });

      // Load videos
      await manager.loadVideos(mockProfile);

      // Verify progress updates
      expect(progressUpdates.length).toBeGreaterThan(0);
      expect(progressUpdates[progressUpdates.length - 1]).toBe(100);
    });

    it('should handle backend errors', async () => {
      // Create manager with no retries for this test
      const noRetryManager = new VideoLoadingManager('http://localhost:8001', 5000, 0);
      
      // Mock error response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      // Load videos and expect error
      await expect(noRetryManager.loadVideos(mockProfile)).rejects.toThrow();

      // Verify state
      const state = noRetryManager.getState();
      expect(state.status).toBe('error');
      expect(state.error).toBeDefined();
    });

    it('should generate unique request IDs', async () => {
      const requestIds: string[] = [];

      manager.subscribe((state) => {
        if (state.requestId && state.requestId !== '') {
          requestIds.push(state.requestId);
        }
      });

      // Mock successful response
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ recommendations: [] }),
      });

      // Load videos multiple times
      await manager.loadVideos(mockProfile);
      manager.reset();
      await manager.loadVideos(mockProfile);

      // Verify unique IDs - should have at least 2 unique IDs
      expect(requestIds.length).toBeGreaterThanOrEqual(2);
      const uniqueIds = new Set(requestIds.filter(id => id !== ''));
      expect(uniqueIds.size).toBeGreaterThanOrEqual(2);
    });
  });

  describe('State Management', () => {
    it('should notify subscribers on state change', () => {
      const callback = vi.fn();
      
      manager.subscribe(callback);
      manager.reset();

      expect(callback).toHaveBeenCalled();
    });

    it('should allow unsubscribing', () => {
      const callback = vi.fn();
      
      const unsubscribe = manager.subscribe(callback);
      unsubscribe();
      
      manager.reset();

      expect(callback).not.toHaveBeenCalled();
    });

    it('should return current state', () => {
      const state = manager.getState();
      
      expect(state).toHaveProperty('status');
      expect(state).toHaveProperty('videos');
      expect(state).toHaveProperty('error');
      expect(state).toHaveProperty('loadingProgress');
    });
  });

  describe('cancelLoad', () => {
    it('should cancel ongoing request', async () => {
      const mockProfile: StudentProfile = {
        goals: ['TYT Matematik'],
        currentLevel: { matematik: 50 },
        learningStyle: 'visual',
      };

      // Mock slow response
      mockFetch.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: async () => ({ recommendations: [] }),
        }), 10000))
      );

      // Start loading
      const loadPromise = manager.loadVideos(mockProfile);

      // Cancel immediately
      manager.cancelLoad();

      // Verify state
      expect(manager.getState().status).toBe('idle');
      expect(manager.getState().error?.message).toContain('cancelled');
    });
  });

  describe('reset', () => {
    it('should reset state to idle', () => {
      manager.reset();

      const state = manager.getState();
      expect(state.status).toBe('idle');
      expect(state.videos).toEqual([]);
      expect(state.error).toBeNull();
      expect(state.loadingProgress).toBe(0);
      expect(state.retryCount).toBe(0);
    });
  });
});

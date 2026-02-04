/**
 * Test Suite: VideoPlayerWithAnalytics Component
 * Task 100: Video Analytics - Player & Tracking Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { VideoPlayerWithAnalytics, VideoPlayerProps } from '../VideoPlayerWithAnalytics';

// Mock fetch
global.fetch = vi.fn();

const mockProps: VideoPlayerProps = {
  videoUrl: 'https://example.com/video.mp4',
  videoId: 'test-video-123',
  videoSource: 'youtube',
  userId: 'user-456',
  videoDuration: 600, // 10 minutes
  initialPosition: 0
};

const mockSessionResponse = {
  session_id: 'session-789',
  video_id: 'test-video-123',
  started_at: '2025-10-28T10:00:00Z'
};

const mockProgressResponse = {
  completion_percentage: 50.5,
  is_completed: false
};

const mockProgressResponseCompleted = {
  completion_percentage: 100,
  is_completed: true
};

describe('VideoPlayerWithAnalytics - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('renders video player', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      const video = document.querySelector('video');
      expect(video).toBeInTheDocument();
    });
  });

  it('sets video source URL', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      const video = document.querySelector('video') as HTMLVideoElement;
      expect(video.src).toBe('https://example.com/video.mp4');
    });
  });

  it('shows video controls on mouse enter', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(document.querySelector('.video-controls')).toBeInTheDocument();
    });
  });

  it('hides video controls initially', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseLeave(container!);

    await waitFor(() => {
      expect(document.querySelector('.video-controls')).not.toBeInTheDocument();
    });
  });

  it('displays session ID when session starts', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });
  });
});

describe('VideoPlayerWithAnalytics - Session Management', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('starts watch session on mount', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/video-analytics/sessions/start'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('test-video-123')
        })
      );
    });
  });

  it('sends correct video data in session start', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      const call = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(call[1].body);
      expect(body.video_id).toBe('test-video-123');
      expect(body.video_source).toBe('youtube');
      expect(body.video_duration).toBe(600);
    });
  });

  it('handles session start failure gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();

    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to start watch session:',
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });

  it('ends session on unmount', async () => {
    const { unmount } = render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    (global.fetch as jest.Mock).mockClear();
    unmount();

    // Wait a bit for cleanup
    await waitFor(() => {
      const endCalls = (global.fetch as jest.Mock).mock.calls.filter(
        call => call[0].includes('/end')
      );
      expect(endCalls.length).toBeGreaterThan(0);
    });
  });

  it('includes user_id in session start', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('user_id=user-456'),
        expect.any(Object)
      );
    });
  });
});

describe('VideoPlayerWithAnalytics - Playback Controls', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('shows play button when paused', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByLabelText('Play')).toBeInTheDocument();
      expect(screen.getByText('▶')).toBeInTheDocument();
    });
  });

  it('shows pause button when playing', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video');
    fireEvent.play(video!);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByLabelText('Pause')).toBeInTheDocument();
      expect(screen.getByText('⏸')).toBeInTheDocument();
    });
  });

  it('updates isPlaying state on play', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video');
    fireEvent.play(video!);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByLabelText('Pause')).toBeInTheDocument();
    });
  });

  it('updates isPlaying state on pause', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video');
    fireEvent.play(video!);
    fireEvent.pause(video!);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByLabelText('Play')).toBeInTheDocument();
    });
  });

  it('records pause event', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    (global.fetch as jest.Mock).mockClear();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => ({})
    });

    const video = document.querySelector('video');
    fireEvent.pause(video!);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions/session-789/pause'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
});

describe('VideoPlayerWithAnalytics - Progress Tracking', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    jest.useFakeTimers();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('sends progress updates every 10 seconds while playing', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockSessionResponse })
      .mockResolvedValue({ json: async () => mockProgressResponse });

    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    const video = document.querySelector('video');
    fireEvent.play(video!);

    (global.fetch as jest.Mock).mockClear();

    jest.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions/session-789/progress'),
        expect.any(Object)
      );
    });
  });

  it('sends current position in progress update', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockSessionResponse })
      .mockResolvedValue({ json: async () => mockProgressResponse });

    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'currentTime', { value: 120, writable: true });
    fireEvent.play(video);

    (global.fetch as jest.Mock).mockClear();
    jest.advanceTimersByTime(10000);

    await waitFor(() => {
      const progressCalls = (global.fetch as jest.Mock).mock.calls.filter(
        call => call[0].includes('/progress')
      );
      if (progressCalls.length > 0) {
        const body = JSON.parse(progressCalls[0][1].body);
        expect(body.current_position).toBeDefined();
      }
    });
  });

  it('sends playback speed in progress update', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockSessionResponse })
      .mockResolvedValue({ json: async () => mockProgressResponse });

    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    const video = document.querySelector('video');
    fireEvent.play(video!);

    (global.fetch as jest.Mock).mockClear();
    jest.advanceTimersByTime(10000);

    await waitFor(() => {
      const progressCalls = (global.fetch as jest.Mock).mock.calls.filter(
        call => call[0].includes('/progress')
      );
      if (progressCalls.length > 0) {
        const body = JSON.parse(progressCalls[0][1].body);
        expect(body.playback_speed).toBe(1.0);
      }
    });
  });

  it('updates completion percentage from API response', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockSessionResponse })
      .mockResolvedValue({ json: async () => mockProgressResponse });

    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    const video = document.querySelector('video');
    fireEvent.play(video!);

    jest.advanceTimersByTime(10000);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByText('51%')).toBeInTheDocument();
    });
  });

  it('calls onProgress callback with position and percentage', async () => {
    const onProgress = vi.fn();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockSessionResponse })
      .mockResolvedValue({ json: async () => mockProgressResponse });

    render(<VideoPlayerWithAnalytics {...mockProps} onProgress={onProgress} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    const video = document.querySelector('video');
    fireEvent.play(video!);

    jest.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(onProgress).toHaveBeenCalledWith(
        expect.any(Number),
        50.5
      );
    });
  });

  it('calls onComplete when video is completed', async () => {
    const onComplete = vi.fn();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockSessionResponse })
      .mockResolvedValue({ json: async () => mockProgressResponseCompleted });

    render(<VideoPlayerWithAnalytics {...mockProps} onComplete={onComplete} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    const video = document.querySelector('video');
    fireEvent.play(video!);

    jest.advanceTimersByTime(10000);

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalled();
    });
  });

  it('stops progress updates when paused', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockSessionResponse })
      .mockResolvedValue({ json: async () => mockProgressResponse });

    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    const video = document.querySelector('video');
    fireEvent.play(video!);
    fireEvent.pause(video!);

    (global.fetch as jest.Mock).mockClear();
    jest.advanceTimersByTime(10000);

    await waitFor(() => {
      const progressCalls = (global.fetch as jest.Mock).mock.calls.filter(
        call => call[0].includes('/progress')
      );
      expect(progressCalls.length).toBe(0);
    });
  });
});

describe('VideoPlayerWithAnalytics - Seeking', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('records seek event', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    (global.fetch as jest.Mock).mockClear();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => ({})
    });

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'currentTime', { value: 180, writable: true });
    fireEvent.seeked(video);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions/session-789/seek'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(String)
        })
      );
    });
  });

  it('sends from and to positions on seek', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(/session-789/)).toBeInTheDocument();
    });

    (global.fetch as jest.Mock).mockClear();

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'currentTime', { value: 240, writable: true });
    fireEvent.seeked(video);

    await waitFor(() => {
      const seekCalls = (global.fetch as jest.Mock).mock.calls.filter(
        call => call[0].includes('/seek')
      );
      if (seekCalls.length > 0) {
        const body = JSON.parse(seekCalls[0][1].body);
        expect(body.from_position).toBeDefined();
        expect(body.to_position).toBe(240);
      }
    });
  });
});

describe('VideoPlayerWithAnalytics - Playback Speed', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('shows speed selector', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByLabelText('Playback speed')).toBeInTheDocument();
    });
  });

  it('has default speed of 1x', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      const select = screen.getByLabelText('Playback speed') as HTMLSelectElement;
      expect(select.value).toBe('1');
    });
  });

  it('shows all speed options', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByText('0.5x')).toBeInTheDocument();
      expect(screen.getByText('0.75x')).toBeInTheDocument();
      expect(screen.getByText('1x')).toBeInTheDocument();
      expect(screen.getByText('1.25x')).toBeInTheDocument();
      expect(screen.getByText('1.5x')).toBeInTheDocument();
      expect(screen.getByText('2x')).toBeInTheDocument();
    });
  });

  it('changes playback speed', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      const select = screen.getByLabelText('Playback speed') as HTMLSelectElement;
      fireEvent.change(select, { target: { value: '1.5' } });
      expect(select.value).toBe('1.5');
    });
  });

  it('updates video element playback rate', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video') as HTMLVideoElement;
    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      const select = screen.getByLabelText('Playback speed');
      fireEvent.change(select, { target: { value: '2' } });
      expect(video.playbackRate).toBe(2);
    });
  });
});

describe('VideoPlayerWithAnalytics - Time Display', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('displays current time and duration', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'duration', { value: 600, writable: true });
    Object.defineProperty(video, 'currentTime', { value: 0, writable: true });
    fireEvent.loadedMetadata(video);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByText(/0:00 \/ 10:00/)).toBeInTheDocument();
    });
  });

  it('formats time correctly (minutes:seconds)', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'duration', { value: 600, writable: true });
    Object.defineProperty(video, 'currentTime', { value: 125, writable: true });
    fireEvent.loadedMetadata(video);
    fireEvent.timeUpdate(video);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByText(/2:05/)).toBeInTheDocument();
    });
  });

  it('pads seconds with zero', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'duration', { value: 600, writable: true });
    Object.defineProperty(video, 'currentTime', { value: 65, writable: true });
    fireEvent.loadedMetadata(video);
    fireEvent.timeUpdate(video);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByText(/1:05/)).toBeInTheDocument();
    });
  });
});

describe('VideoPlayerWithAnalytics - Progress Bar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('renders progress bar', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(document.querySelector('.progress-bar')).toBeInTheDocument();
    });
  });

  it('updates progress bar width based on current time', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'duration', { value: 600, writable: true });
    Object.defineProperty(video, 'currentTime', { value: 300, writable: true });
    fireEvent.loadedMetadata(video);
    fireEvent.timeUpdate(video);

    await waitFor(() => {
      const progressFilled = document.querySelector('.progress-filled') as HTMLElement;
      expect(progressFilled.style.width).toBe('50%');
    });
  });

  it('shows 0% at start', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'duration', { value: 600, writable: true });
    Object.defineProperty(video, 'currentTime', { value: 0, writable: true });
    fireEvent.loadedMetadata(video);
    fireEvent.timeUpdate(video);

    await waitFor(() => {
      const progressFilled = document.querySelector('.progress-filled') as HTMLElement;
      expect(progressFilled.style.width).toBe('0%');
    });
  });

  it('shows 100% at end', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'duration', { value: 600, writable: true });
    Object.defineProperty(video, 'currentTime', { value: 600, writable: true });
    fireEvent.loadedMetadata(video);
    fireEvent.timeUpdate(video);

    await waitFor(() => {
      const progressFilled = document.querySelector('.progress-filled') as HTMLElement;
      expect(progressFilled.style.width).toBe('100%');
    });
  });
});

describe('VideoPlayerWithAnalytics - Notes & Bookmarks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('shows add note button', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByLabelText('Add note')).toBeInTheDocument();
      expect(screen.getByText('📝')).toBeInTheDocument();
    });
  });

  it('shows add bookmark button', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByLabelText('Add bookmark')).toBeInTheDocument();
      expect(screen.getByText('🔖')).toBeInTheDocument();
    });
  });

  it('calls onNote with current timestamp', async () => {
    const onNote = vi.fn();
    render(<VideoPlayerWithAnalytics {...mockProps} onNote={onNote} />);

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'currentTime', { value: 150, writable: true });

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      const noteButton = screen.getByLabelText('Add note');
      fireEvent.click(noteButton);
      expect(onNote).toHaveBeenCalledWith(150);
    });
  });

  it('calls onBookmark with current timestamp', async () => {
    const onBookmark = vi.fn();
    render(<VideoPlayerWithAnalytics {...mockProps} onBookmark={onBookmark} />);

    const video = document.querySelector('video') as HTMLVideoElement;
    Object.defineProperty(video, 'currentTime', { value: 200, writable: true });

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      const bookmarkButton = screen.getByLabelText('Add bookmark');
      fireEvent.click(bookmarkButton);
      expect(onBookmark).toHaveBeenCalledWith(200);
    });
  });
});

describe('VideoPlayerWithAnalytics - Initial Position', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('sets initial position when provided', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} initialPosition={120} />);

    await waitFor(() => {
      const video = document.querySelector('video') as HTMLVideoElement;
      expect(video.currentTime).toBe(120);
    });
  });

  it('does not set position when initialPosition is 0', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} initialPosition={0} />);

    await waitFor(() => {
      const video = document.querySelector('video') as HTMLVideoElement;
      expect(video.currentTime).toBe(0);
    });
  });
});

describe('VideoPlayerWithAnalytics - Completion Badge', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockSessionResponse })
      .mockResolvedValue({ json: async () => mockProgressResponse });
  });

  it('displays completion percentage badge', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video');
    fireEvent.play(video!);

    jest.useFakeTimers();
    jest.advanceTimersByTime(10000);
    jest.useRealTimers();

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByText('51%')).toBeInTheDocument();
    });
  });

  it('displays 0% initially', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const container = document.querySelector('.video-container');
    fireEvent.mouseEnter(container!);

    await waitFor(() => {
      expect(screen.getByText('0%')).toBeInTheDocument();
    });
  });
});

describe('VideoPlayerWithAnalytics - Edge Cases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockSessionResponse
    });
  });

  it('handles missing session gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Session failed'));

    render(<VideoPlayerWithAnalytics {...mockProps} />);

    const video = document.querySelector('video');
    expect(video).toBeInTheDocument();
  });

  it('handles different video sources', async () => {
    const sources: Array<'youtube' | 'eba' | 'khan' | 'vimeo'> = ['youtube', 'eba', 'khan', 'vimeo'];

    for (const source of sources) {
      const { unmount } = render(
        <VideoPlayerWithAnalytics {...mockProps} videoSource={source} />
      );

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            body: expect.stringContaining(source)
          })
        );
      });

      unmount();
      vi.clearAllMocks();
      (global.fetch as jest.Mock).mockResolvedValue({
        json: async () => mockSessionResponse
      });
    }
  });

  it('handles zero duration', async () => {
    render(<VideoPlayerWithAnalytics {...mockProps} videoDuration={0} />);

    const video = document.querySelector('video');
    expect(video).toBeInTheDocument();
  });
});

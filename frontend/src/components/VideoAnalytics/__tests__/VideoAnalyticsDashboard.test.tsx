/**
 * Test Suite: VideoAnalyticsDashboard Component
 * Task 100: Video Analytics - Dashboard & Insights Tests
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { VideoAnalyticsDashboard, AnalyticsSummary } from '../VideoAnalyticsDashboard';
import { vi, Mock } from 'vitest';

// Create fetch mock with proper vitest typing
const fetchMock = vi.fn() as Mock;
global.fetch = fetchMock;

const mockSummaryData: AnalyticsSummary = {
  userId: 'user-123',
  periodType: 'daily',
  periodStart: '2025-10-28T00:00:00Z',
  periodEnd: '2025-10-28T23:59:59Z',
  totalVideosWatched: 10,
  totalWatchTime: 7200, // 2 hours
  totalVideosCompleted: 8,
  averageCompletionRate: 85.5,
  totalNotes: 15,
  totalBookmarks: 5,
  averagePlaybackSpeed: 1.25,
  sourceBreakdown: {
    youtube: 5,
    eba: 3,
    khan: 2
  },
  subjectBreakdown: {
    'Matematik': 4,
    'Fizik': 3,
    'Kimya': 3
  }
};

const mockEmptySummary: AnalyticsSummary = {
  userId: 'user-123',
  periodType: 'daily',
  periodStart: '2025-10-28T00:00:00Z',
  periodEnd: '2025-10-28T23:59:59Z',
  totalVideosWatched: 0,
  totalWatchTime: 0,
  totalVideosCompleted: 0,
  averageCompletionRate: 0,
  totalNotes: 0,
  totalBookmarks: 0,
  averagePlaybackSpeed: 1.0,
  sourceBreakdown: {},
  subjectBreakdown: {}
};

describe('VideoAnalyticsDashboard - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      json: async () => ({
        user_id: mockSummaryData.userId,
        period_type: mockSummaryData.periodType,
        period_start: mockSummaryData.periodStart,
        period_end: mockSummaryData.periodEnd,
        total_videos_watched: mockSummaryData.totalVideosWatched,
        total_watch_time: mockSummaryData.totalWatchTime,
        total_videos_completed: mockSummaryData.totalVideosCompleted,
        average_completion_rate: mockSummaryData.averageCompletionRate,
        total_notes: mockSummaryData.totalNotes,
        total_bookmarks: mockSummaryData.totalBookmarks,
        average_playback_speed: mockSummaryData.averagePlaybackSpeed,
        source_breakdown: mockSummaryData.sourceBreakdown,
        subject_breakdown: mockSummaryData.subjectBreakdown
      })
    });
  });

  it('renders dashboard header', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);
    expect(screen.getByText('Video İzleme Analitikleri')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);
    expect(screen.getByText('Analitikler yükleniyor...')).toBeInTheDocument();
  });

  it('renders date selector', () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);
    expect(screen.getByLabelText('Tarih:')).toBeInTheDocument();
  });

  it('renders date input with current date', () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);
    const dateInput = screen.getByLabelText('Select date for analytics') as HTMLInputElement;
    const today = new Date().toISOString().split('T')[0];
    expect(dateInput.value).toBe(today);
  });

  it('sets max date to today', () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);
    const dateInput = screen.getByLabelText('Select date for analytics') as HTMLInputElement;
    const today = new Date().toISOString().split('T')[0];
    expect(dateInput.max).toBe(today);
  });
});

describe('VideoAnalyticsDashboard - Data Loading', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      json: async () => ({
        user_id: mockSummaryData.userId,
        period_type: mockSummaryData.periodType,
        period_start: mockSummaryData.periodStart,
        period_end: mockSummaryData.periodEnd,
        total_videos_watched: mockSummaryData.totalVideosWatched,
        total_watch_time: mockSummaryData.totalWatchTime,
        total_videos_completed: mockSummaryData.totalVideosCompleted,
        average_completion_rate: mockSummaryData.averageCompletionRate,
        total_notes: mockSummaryData.totalNotes,
        total_bookmarks: mockSummaryData.totalBookmarks,
        average_playback_speed: mockSummaryData.averagePlaybackSpeed,
        source_breakdown: mockSummaryData.sourceBreakdown,
        subject_breakdown: mockSummaryData.subjectBreakdown
      })
    });
  });

  it('fetches summary data on mount', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/video-analytics/summary/daily'),
      );
    });
  });

  it('includes userId in API call', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('user_id=user-123')
      );
    });
  });

  it('includes date in API call', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    const today = new Date().toISOString().split('T')[0];

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(`date=${today}`)
      );
    });
  });

  it('refetches data when date changes', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const dateInput = screen.getByLabelText('Select date for analytics');
    fireEvent.change(dateInput, { target: { value: '2025-10-27' } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('date=2025-10-27')
      );
    });
  });

  it('handles API errors gracefully', async () => {
    fetchMock.mockRejectedValue(new Error('Network error'));
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to load summary:',
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });
});

describe('VideoAnalyticsDashboard - Stats Cards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      json: async () => ({
        user_id: mockSummaryData.userId,
        period_type: mockSummaryData.periodType,
        period_start: mockSummaryData.periodStart,
        period_end: mockSummaryData.periodEnd,
        total_videos_watched: mockSummaryData.totalVideosWatched,
        total_watch_time: mockSummaryData.totalWatchTime,
        total_videos_completed: mockSummaryData.totalVideosCompleted,
        average_completion_rate: mockSummaryData.averageCompletionRate,
        total_notes: mockSummaryData.totalNotes,
        total_bookmarks: mockSummaryData.totalBookmarks,
        average_playback_speed: mockSummaryData.averagePlaybackSpeed,
        source_breakdown: mockSummaryData.sourceBreakdown,
        subject_breakdown: mockSummaryData.subjectBreakdown
      })
    });
  });

  it('displays total videos watched', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('İzlenen Video')).toBeInTheDocument();
    });
  });

  it('displays total watch time formatted', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('2s 0dk')).toBeInTheDocument();
      expect(screen.getByText('Toplam İzleme Süresi')).toBeInTheDocument();
    });
  });

  it('displays total videos completed', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getByText('Tamamlanan Video')).toBeInTheDocument();
    });
  });

  it('displays average completion rate', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('85.5%')).toBeInTheDocument();
      expect(screen.getByText('Ortalama Tamamlama')).toBeInTheDocument();
    });
  });

  it('displays total notes', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('15')).toBeInTheDocument();
      expect(screen.getByText('Not Alındı')).toBeInTheDocument();
    });
  });

  it('displays total bookmarks', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('Yer İmi Eklendi')).toBeInTheDocument();
    });
  });

  it('displays average playback speed', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('1.25x')).toBeInTheDocument();
      expect(screen.getByText('Ortalama Hız')).toBeInTheDocument();
    });
  });

  it('displays completion ratio', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('80%')).toBeInTheDocument(); // 8/10 = 80%
      expect(screen.getByText('Tamamlama Oranı')).toBeInTheDocument();
    });
  });

  it('shows stat icons', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('📹')).toBeInTheDocument();
      expect(screen.getByText('⏱️')).toBeInTheDocument();
      expect(screen.getByText('✅')).toBeInTheDocument();
      expect(screen.getByText('📈')).toBeInTheDocument();
      expect(screen.getByText('📝')).toBeInTheDocument();
      expect(screen.getByText('🔖')).toBeInTheDocument();
      expect(screen.getByText('⚡')).toBeInTheDocument();
      expect(screen.getByText('🎯')).toBeInTheDocument();
    });
  });
});

describe('VideoAnalyticsDashboard - Duration Formatting', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('formats hours and minutes', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        total_watch_time: 3661, // 1 hour 1 minute 1 second
        total_videos_watched: 1
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('1s 1dk')).toBeInTheDocument();
    });
  });

  it('formats minutes only when less than an hour', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        total_watch_time: 1800, // 30 minutes
        total_videos_watched: 1
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('30dk')).toBeInTheDocument();
    });
  });

  it('formats zero minutes correctly', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        total_watch_time: 0,
        total_videos_watched: 1
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('0dk')).toBeInTheDocument();
    });
  });
});

describe('VideoAnalyticsDashboard - Completion Color Coding', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows green for high completion rate (>=80%)', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        average_completion_rate: 85
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      const completionValue = screen.getByText('85.0%');
      expect(completionValue).toHaveStyle({ color: '#10b981' });
    });
  });

  it('shows yellow for medium completion rate (60-79%)', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        average_completion_rate: 70
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      const completionValue = screen.getByText('70.0%');
      expect(completionValue).toHaveStyle({ color: '#f59e0b' });
    });
  });

  it('shows red for low completion rate (<60%)', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        average_completion_rate: 45
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      const completionValue = screen.getByText('45.0%');
      expect(completionValue).toHaveStyle({ color: '#ef4444' });
    });
  });
});

describe('VideoAnalyticsDashboard - Source Breakdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        source_breakdown: mockSummaryData.sourceBreakdown
      })
    });
  });

  it('displays source breakdown section', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('Kaynak Dağılımı')).toBeInTheDocument();
    });
  });

  it('displays all sources', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('YouTube')).toBeInTheDocument();
      expect(screen.getByText('EBA TV')).toBeInTheDocument();
      expect(screen.getByText('Khan Academy')).toBeInTheDocument();
    });
  });

  it('displays video counts for each source', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('5 video')).toBeInTheDocument();
      expect(screen.getByText('3 video')).toBeInTheDocument();
      expect(screen.getByText('2 video')).toBeInTheDocument();
    });
  });

  it('hides source breakdown when empty', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        source_breakdown: {},
        total_videos_watched: 1
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.queryByText('Kaynak Dağılımı')).not.toBeInTheDocument();
    });
  });

  it('renders progress bars for sources', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      const progressBars = document.querySelectorAll('.breakdown-bar-fill');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  it('sets correct width for source progress bars', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      const progressBars = document.querySelectorAll('.breakdown-bar-fill');
      const youtubeBar = progressBars[0] as HTMLElement;
      expect(youtubeBar.style.width).toBe('50%'); // 5/10 = 50%
    });
  });
});

describe('VideoAnalyticsDashboard - Subject Breakdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        subject_breakdown: mockSummaryData.subjectBreakdown
      })
    });
  });

  it('displays subject breakdown section', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('Ders Dağılımı')).toBeInTheDocument();
    });
  });

  it('displays all subjects', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('Matematik')).toBeInTheDocument();
      expect(screen.getByText('Fizik')).toBeInTheDocument();
      expect(screen.getByText('Kimya')).toBeInTheDocument();
    });
  });

  it('displays video counts for each subject', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      const videoTexts = screen.getAllByText(/video/);
      expect(videoTexts.length).toBeGreaterThan(0);
    });
  });

  it('hides subject breakdown when empty', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        subject_breakdown: {},
        total_videos_watched: 1
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.queryByText('Ders Dağılımı')).not.toBeInTheDocument();
    });
  });
});

describe('VideoAnalyticsDashboard - Insights', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays insights section', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({ ...mockSummaryData })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('İçgörüler')).toBeInTheDocument();
    });
  });

  it('shows success insight for high completion rate', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        average_completion_rate: 85
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText(/Harika! Videoları %85 oranında tamamlıyorsunuz/)).toBeInTheDocument();
    });
  });

  it('shows fast learner insight for high playback speed', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        average_playback_speed: 1.75
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText(/Videoları 1.75x hızda izliyorsunuz/)).toBeInTheDocument();
      expect(screen.getByText(/Hızlı öğrenen!/)).toBeInTheDocument();
    });
  });

  it('shows active learning insight for many notes', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        total_notes: 15
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText(/15 not aldınız. Aktif öğrenme!/)).toBeInTheDocument();
    });
  });

  it('shows warning for no completed videos', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        total_videos_completed: 0,
        total_videos_watched: 5
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText(/Bugün hiç video tamamlamadınız/)).toBeInTheDocument();
    });
  });

  it('does not show warning when no videos watched', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        total_videos_completed: 0,
        total_videos_watched: 0
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.queryByText(/Bugün hiç video tamamlamadınız/)).not.toBeInTheDocument();
    });
  });
});

describe('VideoAnalyticsDashboard - Empty State', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockEmptySummary
      })
    });
  });

  it('shows empty state when no videos watched', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('Bu tarih için video izleme verisi bulunamadı')).toBeInTheDocument();
    });
  });

  it('shows empty state icon', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('📊')).toBeInTheDocument();
    });
  });

  it('does not show stats cards in empty state', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.queryByText('İzlenen Video')).not.toBeInTheDocument();
      expect(screen.queryByText('Toplam İzleme Süresi')).not.toBeInTheDocument();
    });
  });

  it('does not show insights in empty state', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.queryByText('İçgörüler')).not.toBeInTheDocument();
    });
  });
});

describe('VideoAnalyticsDashboard - Edge Cases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles zero completion ratio correctly', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        total_videos_completed: 0,
        total_videos_watched: 5
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('0%')).toBeInTheDocument();
    });
  });

  it('handles 100% completion ratio', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        total_videos_completed: 10,
        total_videos_watched: 10
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  it('handles single video source', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        source_breakdown: { youtube: 10 }
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('YouTube')).toBeInTheDocument();
      expect(screen.getByText('10 video')).toBeInTheDocument();
    });
  });

  it('handles unknown video source', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        source_breakdown: { unknown: 2 },
        total_videos_watched: 2
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('unknown')).toBeInTheDocument();
    });
  });

  it('handles very large numbers', async () => {
    fetchMock.mockResolvedValue({
      json: async () => ({
        ...mockSummaryData,
        total_videos_watched: 999,
        total_watch_time: 999999
      })
    });

    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('999')).toBeInTheDocument();
    });
  });
});

describe('VideoAnalyticsDashboard - Accessibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({
      json: async () => ({ ...mockSummaryData })
    });
  });

  it('uses semantic HTML structure', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Video İzleme Analitikleri' })).toBeInTheDocument();
    });
  });

  it('has accessible date input', () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);
    expect(screen.getByLabelText('Select date for analytics')).toBeInTheDocument();
  });

  it('displays section headings', async () => {
    render(<VideoAnalyticsDashboard userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Kaynak Dağılımı' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Ders Dağılımı' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'İçgörüler' })).toBeInTheDocument();
    });
  });
});

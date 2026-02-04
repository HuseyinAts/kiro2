/**
 * Test Suite: LevelDisplay Component
 * Task 91: Gamification - Level & XP Testing
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LevelDisplay } from '../LevelDisplay';
import * as useGamificationHook from '../../../hooks/useGamification';

vi.mock('../../../hooks/useGamification');
const mockedUseGamification = useGamificationHook as jest.Mocked<typeof useGamificationHook>;

const mockLevelProgress = {
  current_level: 25,
  total_xp: 12500,
  xp_in_current_level: 400,
  xp_needed_for_next: 600,
  progress_percentage: 66.67,
  next_level: 26,
  next_milestone: 30
};

const mockMilestones = [10, 20, 30, 40, 50, 75, 100];

describe('LevelDisplay - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue(mockMilestones),
    });
  });

  it('renders level display', () => {
    render(<LevelDisplay />);
    expect(screen.getByText('Seviye & XP')).toBeInTheDocument();
  });

  it('shows loading spinner when loading and no data', () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: null,
      loading: true,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn(),
    });

    render(<LevelDisplay />);
    expect(document.querySelector('.spinner')).toBeInTheDocument();
  });

  it('shows error message when error occurs', () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: null,
      loading: false,
      error: 'Network error',
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn(),
    });

    render(<LevelDisplay />);
    expect(screen.getByText('Seviye bilgisi yüklenemedi')).toBeInTheDocument();
    expect(screen.getByText('⚠️')).toBeInTheDocument();
  });

  it('shows error when levelProgress is null', () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: null,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn(),
    });

    render(<LevelDisplay />);
    expect(screen.getByText('Seviye bilgisi yüklenemedi')).toBeInTheDocument();
  });
});

describe('LevelDisplay - Level Information', () => {
  beforeEach(() => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });
  });

  it('displays current level', () => {
    render(<LevelDisplay />);
    expect(screen.getByText('25')).toBeInTheDocument();
  });

  it('displays total XP with Turkish locale', () => {
    render(<LevelDisplay />);
    expect(screen.getByText('12.500')).toBeInTheDocument();
  });

  it('displays XP in current level', () => {
    render(<LevelDisplay />);
    expect(screen.getByText('400 XP')).toBeInTheDocument();
  });

  it('displays XP needed for next level', () => {
    render(<LevelDisplay />);
    expect(screen.getByText('600 XP gerekli')).toBeInTheDocument();
  });

  it('displays next level number', () => {
    render(<LevelDisplay />);
    expect(screen.getByText(/Seviye 26'e İlerleme/)).toBeInTheDocument();
  });

  it('displays progress percentage rounded', () => {
    render(<LevelDisplay />);
    expect(screen.getByText('67%')).toBeInTheDocument();
  });

  it('displays next milestone', () => {
    render(<LevelDisplay />);
    expect(screen.getByText(/Seviye 30/)).toBeInTheDocument();
  });

  it('hides next milestone when null', () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, next_milestone: null },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    render(<LevelDisplay />);
    expect(screen.queryByText('Sonraki Milestone:')).not.toBeInTheDocument();
  });
});

describe('LevelDisplay - Progress Bar', () => {
  beforeEach(() => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });
  });

  it('renders progress bar', () => {
    render(<LevelDisplay />);
    const progressBar = document.querySelector('.progress-bar-fill');
    expect(progressBar).toBeInTheDocument();
  });

  it('sets progress bar width based on percentage', () => {
    render(<LevelDisplay />);
    const progressBar = document.querySelector('.progress-bar-fill') as HTMLElement;
    expect(progressBar.style.width).toBe('66.67%');
  });

  it('shows 0% progress correctly', () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, progress_percentage: 0, xp_in_current_level: 0 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    render(<LevelDisplay />);
    const progressBar = document.querySelector('.progress-bar-fill') as HTMLElement;
    expect(progressBar.style.width).toBe('0%');
  });

  it('shows 100% progress correctly', () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, progress_percentage: 100 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    render(<LevelDisplay />);
    const progressBar = document.querySelector('.progress-bar-fill') as HTMLElement;
    expect(progressBar.style.width).toBe('100%');
  });
});

describe('LevelDisplay - Compact Mode', () => {
  beforeEach(() => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });
  });

  it('renders in compact mode', () => {
    render(<LevelDisplay compact />);
    expect(document.querySelector('.level-display.compact')).toBeInTheDocument();
  });

  it('shows level badge in compact mode', () => {
    render(<LevelDisplay compact />);
    expect(screen.getByText('Lv 25')).toBeInTheDocument();
  });

  it('shows lightning emoji in compact mode (non-milestone)', () => {
    render(<LevelDisplay compact />);
    expect(screen.getByText('⚡')).toBeInTheDocument();
  });

  it('hides detailed info in compact mode', () => {
    render(<LevelDisplay compact />);
    expect(screen.queryByText('Seviye & XP')).not.toBeInTheDocument();
    expect(screen.queryByText('Toplam XP')).not.toBeInTheDocument();
  });
});

describe('LevelDisplay - Milestones', () => {
  beforeEach(() => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue(mockMilestones),
    });
  });

  it('loads milestones on mount', async () => {
    const getMilestones = vi.fn().mockResolvedValue(mockMilestones);
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones,
    });

    render(<LevelDisplay showMilestones />);
    await waitFor(() => expect(getMilestones).toHaveBeenCalled());
  });

  it('does not load milestones when showMilestones is false', () => {
    const getMilestones = vi.fn().mockResolvedValue(mockMilestones);
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones,
    });

    render(<LevelDisplay showMilestones={false} />);
    expect(getMilestones).not.toHaveBeenCalled();
  });

  it('displays milestone section', async () => {
    render(<LevelDisplay showMilestones />);
    await waitFor(() => {
      expect(screen.getByText('Milestone Seviyeleri')).toBeInTheDocument();
    });
  });

  it('displays all milestone levels', async () => {
    render(<LevelDisplay showMilestones />);
    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('20')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  it('marks achieved milestones with checkmark', async () => {
    render(<LevelDisplay showMilestones />);
    await waitFor(() => {
      const checkmarks = screen.getAllByText('✓');
      expect(checkmarks.length).toBeGreaterThan(0);
    });
  });

  it('shows trophy for milestone level (level 20)', async () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, current_level: 20 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue(mockMilestones),
    });

    render(<LevelDisplay showMilestones />);
    await waitFor(() => {
      const trophies = screen.getAllByText('🏆');
      expect(trophies.length).toBeGreaterThan(0);
    });
  });

  it('shows milestone badge for current milestone', async () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, current_level: 20 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue(mockMilestones),
    });

    render(<LevelDisplay showMilestones />);
    await waitFor(() => {
      expect(screen.getByText('Milestone!')).toBeInTheDocument();
    });
  });
});

describe('LevelDisplay - Level Up Animation', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('shows level up animation when level increases', () => {
    const { rerender } = render(<LevelDisplay />);

    // Change to higher level
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, current_level: 26 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    rerender(<LevelDisplay />);
    expect(screen.getByText('Seviye Atladın!')).toBeInTheDocument();
    expect(screen.getByText('🎉')).toBeInTheDocument();
    expect(screen.getByText('Seviye 26')).toBeInTheDocument();
  });

  it('calls onLevelUp callback when leveling up', () => {
    const onLevelUp = vi.fn();
    const { rerender } = render(<LevelDisplay onLevelUp={onLevelUp} />);

    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, current_level: 26 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    rerender(<LevelDisplay onLevelUp={onLevelUp} />);
    expect(onLevelUp).toHaveBeenCalledWith(26);
  });

  it('hides level up animation after 3 seconds', () => {
    const { rerender } = render(<LevelDisplay />);

    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, current_level: 26 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    rerender(<LevelDisplay />);
    expect(screen.getByText('Seviye Atladın!')).toBeInTheDocument();

    jest.advanceTimersByTime(3000);
    rerender(<LevelDisplay />);
    expect(document.querySelector('.leveling-up')).not.toHaveClass('leveling-up');
  });

  it('does not show animation when level stays the same', () => {
    const { rerender } = render(<LevelDisplay />);
    rerender(<LevelDisplay />);
    expect(screen.queryByText('Seviye Atladın!')).not.toBeInTheDocument();
  });
});

describe('LevelDisplay - Compact Milestone', () => {
  it('shows trophy in compact mode for milestone level', async () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, current_level: 20 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue(mockMilestones),
    });

    render(<LevelDisplay compact showMilestones />);
    await waitFor(() => {
      expect(screen.getByText('🏆')).toBeInTheDocument();
    });
  });

  it('adds milestone class in compact mode', async () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, current_level: 20 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue(mockMilestones),
    });

    render(<LevelDisplay compact showMilestones />);
    await waitFor(() => {
      expect(document.querySelector('.level-display.compact.milestone')).toBeInTheDocument();
    });
  });
});

describe('LevelDisplay - Edge Cases', () => {
  it('handles level 1 correctly', () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: {
        current_level: 1,
        total_xp: 50,
        xp_in_current_level: 50,
        xp_needed_for_next: 100,
        progress_percentage: 50,
        next_level: 2,
        next_milestone: 10
      },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    render(<LevelDisplay />);
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('50')).toBeInTheDocument();
  });

  it('handles high level (100+) correctly', () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: {
        current_level: 150,
        total_xp: 500000,
        xp_in_current_level: 5000,
        xp_needed_for_next: 10000,
        progress_percentage: 50,
        next_level: 151,
        next_milestone: null
      },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    render(<LevelDisplay />);
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('500.000')).toBeInTheDocument();
  });

  it('handles empty milestones array', async () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    render(<LevelDisplay showMilestones />);
    await waitFor(() => {
      expect(screen.queryByText('Milestone Seviyeleri')).not.toBeInTheDocument();
    });
  });

  it('handles decimal progress percentage', () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: { ...mockLevelProgress, progress_percentage: 33.333333 },
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });

    render(<LevelDisplay />);
    expect(screen.getByText('33%')).toBeInTheDocument();
  });
});

describe('LevelDisplay - Accessibility', () => {
  beforeEach(() => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue([]),
    });
  });

  it('uses semantic HTML structure', () => {
    render(<LevelDisplay />);
    expect(screen.getByRole('heading', { name: 'Seviye & XP' })).toBeInTheDocument();
  });

  it('displays milestone heading', async () => {
    mockedUseGamification.useLevel = vi.fn().mockReturnValue({
      levelProgress: mockLevelProgress,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getLevelLeaderboard: vi.fn(),
      getMilestones: vi.fn().mockResolvedValue(mockMilestones),
    });

    render(<LevelDisplay showMilestones />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Milestone Seviyeleri' })).toBeInTheDocument();
    });
  });
});

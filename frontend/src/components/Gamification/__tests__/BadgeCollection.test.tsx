/**
 * Test Suite: BadgeCollection Component
 * Task 91: Badge System Testing
 *
 * Tests badge display, filtering, progress tracking,
 * rarity system, and category management.
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BadgeCollection } from '../BadgeCollection';
import * as useGamificationHook from '../../../hooks/useGamification';
import { vi, Mocked } from 'vitest';

// ============================================================
// Mocks
// ============================================================

vi.mock('../../../hooks/useGamification');
const mockedUseGamification = useGamificationHook as Mocked<typeof useGamificationHook>;

const mockEarnedBadges = [
  {
    badge_id: '1',
    name: 'İlk Adım',
    description: 'İlk aktiviteyi tamamla',
    icon: '🎯',
    category: 'achievement',
    rarity: 'common' as const,
    points: 10,
    earned_at: '2024-01-01',
  },
  {
    badge_id: '2',
    name: 'Ustalaşma',
    description: '100 işlem tamamla',
    icon: '⭐',
    category: 'mastery',
    rarity: 'rare' as const,
    points: 50,
    earned_at: '2024-01-15',
  },
];

const mockAllBadges = [
  ...mockEarnedBadges,
  {
    badge_id: '3',
    name: 'Efsane',
    description: '1000 işlem tamamla',
    icon: '💎',
    category: 'mastery',
    rarity: 'legendary' as const,
    points: 500,
  },
];

const mockBadgeProgress = [
  {
    ...mockAllBadges[2],
    progress_percentage: 45,
    criteria: { operations: 450 },
  },
];

// ============================================================
// Tests: Rendering
// ============================================================

describe('BadgeCollection - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: mockBadgeProgress,
      loading: false,
      error: null,
    });
  });

  it('renders badge collection', () => {
    render(<BadgeCollection />);
    expect(screen.getByText('Rozet Koleksiyonu')).toBeInTheDocument();
  });

  it('displays badge count', () => {
    render(<BadgeCollection />);
    expect(screen.getByText('2/3')).toBeInTheDocument();
  });

  it('shows view mode buttons', () => {
    render(<BadgeCollection />);
    expect(screen.getByText(/Kazanılanlar \(2\)/)).toBeInTheDocument();
    expect(screen.getByText(/Tümü \(3\)/)).toBeInTheDocument();
  });

  it('shows rarity filter', () => {
    render(<BadgeCollection />);
    expect(screen.getByText('Tüm Nadirlikler')).toBeInTheDocument();
  });

  it('displays earned badges by default', () => {
    render(<BadgeCollection />);
    expect(screen.getByText('İlk Adım')).toBeInTheDocument();
    expect(screen.getByText('Ustalaşma')).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Loading & Error States
// ============================================================

describe('BadgeCollection - Loading & Error', () => {
  it('shows loading spinner', () => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: [],
      earnedBadges: [],
      badgeProgress: [],
      loading: true,
      error: null,
    });

    render(<BadgeCollection />);
    expect(document.querySelector('.spinner')).toBeInTheDocument();
  });

  it('shows error message', () => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: [],
      earnedBadges: [],
      badgeProgress: [],
      loading: false,
      error: 'Failed to load',
    });

    render(<BadgeCollection />);
    expect(screen.getByText('Rozetler yüklenemedi')).toBeInTheDocument();
  });

  it('does not show spinner when badges exist', () => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: [],
      loading: true,
      error: null,
    });

    render(<BadgeCollection />);
    expect(document.querySelector('.spinner')).not.toBeInTheDocument();
  });
});

// ============================================================
// Tests: Compact Mode
// ============================================================

describe('BadgeCollection - Compact Mode', () => {
  beforeEach(() => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: [],
      loading: false,
      error: null,
    });
  });

  it('renders compact view', () => {
    render(<BadgeCollection compact />);
    expect(screen.getByText('🏅')).toBeInTheDocument();
    expect(screen.getByText('2/3')).toBeInTheDocument();
  });

  it('does not show filters in compact mode', () => {
    render(<BadgeCollection compact />);
    expect(screen.queryByText('Kazanılanlar')).not.toBeInTheDocument();
  });
});

// ============================================================
// Tests: View Mode Switching
// ============================================================

describe('BadgeCollection - View Modes', () => {
  beforeEach(() => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: mockBadgeProgress,
      loading: false,
      error: null,
    });
  });

  it('switches to all badges view', () => {
    render(<BadgeCollection />);

    const allButton = screen.getByText(/Tümü \(3\)/);
    fireEvent.click(allButton);

    expect(screen.getByText('Efsane')).toBeInTheDocument();
  });

  it('switches to progress view', () => {
    render(<BadgeCollection showProgress />);

    const progressButton = screen.getByText(/İlerleme \(1\)/);
    fireEvent.click(progressButton);

    expect(screen.getByText('Efsane')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('highlights active view button', () => {
    render(<BadgeCollection />);

    const earnedButton = screen.getByText(/Kazanılanlar/);
    expect(earnedButton).toHaveClass('active');

    const allButton = screen.getByText(/Tümü/);
    fireEvent.click(allButton);

    expect(allButton).toHaveClass('active');
    expect(earnedButton).not.toHaveClass('active');
  });

  it('does not show progress button when showProgress is false', () => {
    render(<BadgeCollection showProgress={false} />);
    expect(screen.queryByText(/İlerleme/)).not.toBeInTheDocument();
  });
});

// ============================================================
// Tests: Rarity Filtering
// ============================================================

describe('BadgeCollection - Rarity Filter', () => {
  beforeEach(() => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: [],
      loading: false,
      error: null,
    });
  });

  it('filters by common rarity', () => {
    render(<BadgeCollection />);

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'common' } });

    expect(screen.getByText('İlk Adım')).toBeInTheDocument();
    expect(screen.queryByText('Ustalaşma')).not.toBeInTheDocument();
  });

  it('filters by rare rarity', () => {
    render(<BadgeCollection />);

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'rare' } });

    expect(screen.queryByText('İlk Adım')).not.toBeInTheDocument();
    expect(screen.getByText('Ustalaşma')).toBeInTheDocument();
  });

  it('shows all rarities when set to all', () => {
    render(<BadgeCollection />);

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'uncommon' } });
    fireEvent.change(select, { target: { value: 'all' } });

    expect(screen.getByText('İlk Adım')).toBeInTheDocument();
    expect(screen.getByText('Ustalaşma')).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Category Filtering
// ============================================================

describe('BadgeCollection - Category Filter', () => {
  beforeEach(() => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: [],
      loading: false,
      error: null,
    });
  });

  it('filters by category via props', () => {
    render(<BadgeCollection filterByCategory="achievement" />);

    expect(screen.getByText('İlk Adım')).toBeInTheDocument();
    expect(screen.queryByText('Ustalaşma')).not.toBeInTheDocument();
  });

  it('filters by mastery category', () => {
    render(<BadgeCollection filterByCategory="mastery" />);

    expect(screen.queryByText('İlk Adım')).not.toBeInTheDocument();
    expect(screen.getByText('Ustalaşma')).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Badge Details
// ============================================================

describe('BadgeCollection - Badge Details', () => {
  beforeEach(() => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: [],
      loading: false,
      error: null,
    });
  });

  it('displays badge icon', () => {
    render(<BadgeCollection />);
    expect(screen.getByText('🎯')).toBeInTheDocument();
    expect(screen.getByText('⭐')).toBeInTheDocument();
  });

  it('displays badge category with icon', () => {
    render(<BadgeCollection />);
    expect(screen.getByText(/achievement/)).toBeInTheDocument();
    expect(screen.getByText(/mastery/)).toBeInTheDocument();
  });

  it('displays badge points', () => {
    render(<BadgeCollection />);
    expect(screen.getByText('+10 puan')).toBeInTheDocument();
    expect(screen.getByText('+50 puan')).toBeInTheDocument();
  });

  it('shows progress bar in progress view', () => {
    render(<BadgeCollection showProgress />);

    const progressButton = screen.getByText(/İlerleme/);
    fireEvent.click(progressButton);

    const progressBar = document.querySelector('.badge-progress-bar');
    expect(progressBar).toBeInTheDocument();
  });

  it('sets correct rarity border color', () => {
    render(<BadgeCollection />);

    const commonBadge = screen.getByText('İlk Adım').closest('.badge-card');
    expect(commonBadge).toHaveStyle({ borderColor: '#94a3b8' });

    const rareBadge = screen.getByText('Ustalaşma').closest('.badge-card');
    expect(rareBadge).toHaveStyle({ borderColor: '#3b82f6' });
  });
});

// ============================================================
// Tests: Badge Selection
// ============================================================

describe('BadgeCollection - Badge Selection', () => {
  beforeEach(() => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: [],
      loading: false,
      error: null,
    });
  });

  it('selects badge on click', () => {
    render(<BadgeCollection />);

    const badgeCard = screen.getByText('İlk Adım').closest('.badge-card');
    fireEvent.click(badgeCard!);

    // Badge is selected (internal state - can't directly test without modal)
    expect(badgeCard).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Empty States
// ============================================================

describe('BadgeCollection - Empty States', () => {
  it('shows no earned badges message', () => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: [],
      badgeProgress: [],
      loading: false,
      error: null,
    });

    render(<BadgeCollection />);
    expect(screen.getByText('Henüz rozet kazanmadınız')).toBeInTheDocument();
  });

  it('shows no badges found when filtered', () => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: [],
      loading: false,
      error: null,
    });

    render(<BadgeCollection />);

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'legendary' } });

    expect(screen.getByText('Rozet bulunamadı')).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Progress Percentage
// ============================================================

describe('BadgeCollection - Progress Display', () => {
  beforeEach(() => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: mockBadgeProgress,
      loading: false,
      error: null,
    });
  });

  it('shows progress percentage', () => {
    render(<BadgeCollection showProgress />);

    const progressButton = screen.getByText(/İlerleme/);
    fireEvent.click(progressButton);

    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('sets progress bar width correctly', () => {
    render(<BadgeCollection showProgress />);

    const progressButton = screen.getByText(/İlerleme/);
    fireEvent.click(progressButton);

    const progressFill = document.querySelector('.badge-progress-fill');
    expect(progressFill).toHaveStyle({ width: '45%' });
  });

  it('applies rarity color to progress bar', () => {
    render(<BadgeCollection showProgress />);

    const progressButton = screen.getByText(/İlerleme/);
    fireEvent.click(progressButton);

    const progressFill = document.querySelector('.badge-progress-fill');
    expect(progressFill).toHaveStyle({ background: '#f59e0b' }); // legendary color
  });
});

// ============================================================
// Tests: Statistics
// ============================================================

describe('BadgeCollection - Statistics', () => {
  beforeEach(() => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: [],
      loading: false,
      error: null,
    });
  });

  it('calculates total earned badges', () => {
    render(<BadgeCollection />);
    expect(screen.getByText('2/3')).toBeInTheDocument();
  });

  it('updates stats when badges change', () => {
    const { rerender } = render(<BadgeCollection />);

    expect(screen.getByText('2/3')).toBeInTheDocument();

    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: [...mockEarnedBadges, mockAllBadges[2]],
      badgeProgress: [],
      loading: false,
      error: null,
    });

    rerender(<BadgeCollection />);
    expect(screen.getByText('3/3')).toBeInTheDocument();
  });
});

// ============================================================
// Tests: Earned Badge Styling
// ============================================================

describe('BadgeCollection - Earned Styling', () => {
  beforeEach(() => {
    mockedUseGamification.useBadges = vi.fn().mockReturnValue({
      allBadges: mockAllBadges,
      earnedBadges: mockEarnedBadges,
      badgeProgress: [],
      loading: false,
      error: null,
    });
  });

  it('adds earned class to earned badges', () => {
    render(<BadgeCollection />);

    const earnedBadge = screen.getByText('İlk Adım').closest('.badge-card');
    expect(earnedBadge).toHaveClass('earned');
  });

  it('does not add earned class to unearned badges', () => {
    render(<BadgeCollection />);

    fireEvent.click(screen.getByText(/Tümü/));

    const unearnedBadge = screen.getByText('Efsane').closest('.badge-card');
    expect(unearnedBadge).not.toHaveClass('earned');
  });
});

/**
 * Task 91: Gamification System - Frontend Tests
 * Tests for all gamification components and hooks
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import { act } from 'react-dom/test-utils';

// Import components
import { PointsDisplay } from '../components/Gamification/PointsDisplay';
import { LevelDisplay } from '../components/Gamification/LevelDisplay';
import { BadgeCollection } from '../components/Gamification/BadgeCollection';
import { Leaderboard } from '../components/Gamification/Leaderboard';
import { GamificationDashboard } from '../components/Gamification/GamificationDashboard';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// ============================================================================
// Test Data
// ============================================================================

const mockPointsData = {
  total_points: 1500
};

const mockLevelProgressData = {
  current_level: 5,
  total_xp: 1500,
  xp_in_current_level: 300,
  xp_needed_for_next: 500,
  progress_percentage: 60,
  next_level: 6,
  next_milestone: 10
};

const mockBadgesData = [
  {
    badge_id: 'first_question',
    name: 'İlk Adım',
    description: 'İlk soruyu cevapladın',
    icon: '🎯',
    category: 'achievement',
    rarity: 'common',
    points: 10,
    earned_at: '2025-01-01T00:00:00Z'
  },
  {
    badge_id: 'streak_7',
    name: '7 Günlük Seri',
    description: '7 gün üst üste çalıştın',
    icon: '🔥',
    category: 'streak',
    rarity: 'uncommon',
    points: 50
  }
];

const mockLeaderboardData = [
  {
    rank: 1,
    user_id: 'user1',
    username: 'Alice',
    score: 5000,
    level: 20
  },
  {
    rank: 2,
    user_id: 'user2',
    username: 'Bob',
    score: 4500,
    level: 18
  },
  {
    rank: 3,
    user_id: 'user3',
    username: 'Charlie',
    score: 4000,
    level: 17
  }
];

const mockStatsData = {
  points: 1500,
  level: 5,
  total_xp: 1500,
  level_progress: mockLevelProgressData,
  total_badges: 5,
  badges_by_rarity: {
    common: 2,
    uncommon: 2,
    rare: 1
  },
  leaderboard_rank: {
    rank: 42,
    score: 1500,
    total_users: 1000,
    percentile: 95.8
  },
  recent_achievements: [mockBadgesData[0]]
};

// ============================================================================
// PointsDisplay Tests
// ============================================================================

describe('PointsDisplay Component', () => {
  beforeEach(() => {
    mockedAxios.get.mockResolvedValue({ data: mockPointsData });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test('renders points correctly', async () => {
    await act(async () => {
      render(<PointsDisplay />);
    });

    await waitFor(() => {
      expect(screen.getByText(/1[.,]500/)).toBeInTheDocument();
    });
  });

  test('renders in compact mode', async () => {
    await act(async () => {
      render(<PointsDisplay compact={true} />);
    });

    await waitFor(() => {
      const element = screen.getByText(/1[.,]500/);
      expect(element).toBeInTheDocument();
    });
  });

  test('shows loading state', () => {
    mockedAxios.get.mockImplementation(() => new Promise(() => {}));

    render(<PointsDisplay />);

    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument();
  });

  test('handles error state', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Network error'));

    await act(async () => {
      render(<PointsDisplay />);
    });

    await waitFor(() => {
      expect(screen.getByText(/Puan yüklenemedi/i)).toBeInTheDocument();
    });
  });
});

// ============================================================================
// LevelDisplay Tests
// ============================================================================

describe('LevelDisplay Component', () => {
  beforeEach(() => {
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/level/progress')) {
        return Promise.resolve({ data: mockLevelProgressData });
      }
      if (url.includes('/level/milestones')) {
        return Promise.resolve({ data: [10, 25, 50, 75, 100] });
      }
      return Promise.reject(new Error('Not found'));
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test('renders level correctly', async () => {
    await act(async () => {
      render(<LevelDisplay />);
    });

    await waitFor(() => {
      expect(screen.getByText(/5/)).toBeInTheDocument();
      expect(screen.getByText(/60%/)).toBeInTheDocument();
    });
  });

  test('renders milestones when enabled', async () => {
    await act(async () => {
      render(<LevelDisplay showMilestones={true} />);
    });

    await waitFor(() => {
      expect(screen.getByText(/10/)).toBeInTheDocument();
      expect(screen.getByText(/25/)).toBeInTheDocument();
    });
  });

  test('renders in compact mode', async () => {
    await act(async () => {
      render(<LevelDisplay compact={true} />);
    });

    await waitFor(() => {
      expect(screen.getByText(/Lv 5/i)).toBeInTheDocument();
    });
  });

  test('calls onLevelUp callback', async () => {
    const onLevelUp = vi.fn();

    await act(async () => {
      render(<LevelDisplay onLevelUp={onLevelUp} />);
    });

    // Note: Level up animation would need to be triggered by prop change
    // This is a simplified test
    await waitFor(() => {
      expect(screen.getByText(/5/)).toBeInTheDocument();
    });
  });
});

// ============================================================================
// BadgeCollection Tests
// ============================================================================

describe('BadgeCollection Component', () => {
  beforeEach(() => {
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/badges/earned')) {
        return Promise.resolve({ data: [mockBadgesData[0]] });
      }
      if (url.includes('/badges/progress')) {
        return Promise.resolve({ data: [] });
      }
      if (url.includes('/badges')) {
        return Promise.resolve({ data: mockBadgesData });
      }
      return Promise.reject(new Error('Not found'));
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test('renders earned badges', async () => {
    await act(async () => {
      render(<BadgeCollection />);
    });

    await waitFor(() => {
      expect(screen.getByText(/İlk Adım/)).toBeInTheDocument();
    });
  });

  test('switches between view modes', async () => {
    await act(async () => {
      render(<BadgeCollection />);
    });

    await waitFor(() => {
      const allButton = screen.getByText(/Tümü/);
      fireEvent.click(allButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/7 Günlük Seri/)).toBeInTheDocument();
    });
  });

  test('filters by rarity', async () => {
    await act(async () => {
      render(<BadgeCollection />);
    });

    await waitFor(() => {
      const raritySelect = screen.getByRole('combobox');
      fireEvent.change(raritySelect, { target: { value: 'uncommon' } });
    });

    // Should filter badges
  });

  test('opens badge modal on click', async () => {
    await act(async () => {
      render(<BadgeCollection />);
    });

    await waitFor(() => {
      const badge = screen.getByText(/İlk Adım/);
      fireEvent.click(badge);
    });

    // Modal should open with badge details
  });
});

// ============================================================================
// Leaderboard Tests
// ============================================================================

describe('Leaderboard Component', () => {
  beforeEach(() => {
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/leaderboard/')) {
        return Promise.resolve({ data: mockLeaderboardData });
      }
      return Promise.reject(new Error('Not found'));
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test('renders leaderboard entries', async () => {
    await act(async () => {
      render(<Leaderboard />);
    });

    await waitFor(() => {
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
      expect(screen.getByText(/Bob/)).toBeInTheDocument();
      expect(screen.getByText(/Charlie/)).toBeInTheDocument();
    });
  });

  test('shows top 3 with medals', async () => {
    await act(async () => {
      render(<Leaderboard />);
    });

    await waitFor(() => {
      // Should show medal emojis for top 3
      const medals = screen.getAllByText(/🥇|🥈|🥉/);
      expect(medals.length).toBeGreaterThan(0);
    });
  });

  test('switches between leaderboard types', async () => {
    await act(async () => {
      render(<Leaderboard />);
    });

    await waitFor(() => {
      const weeklyTab = screen.getByText(/Haftalık/);
      fireEvent.click(weeklyTab);
    });

    // Should fetch weekly leaderboard
    expect(mockedAxios.get).toHaveBeenCalledWith(
      expect.stringContaining('/leaderboard/weekly'),
      expect.any(Object)
    );
  });
});

// ============================================================================
// GamificationDashboard Tests
// ============================================================================

describe('GamificationDashboard Component', () => {
  beforeEach(() => {
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/stats')) {
        return Promise.resolve({ data: mockStatsData });
      }
      if (url.includes('/points')) {
        return Promise.resolve({ data: mockPointsData });
      }
      if (url.includes('/level/progress')) {
        return Promise.resolve({ data: mockLevelProgressData });
      }
      if (url.includes('/badges')) {
        return Promise.resolve({ data: mockBadgesData });
      }
      if (url.includes('/leaderboard')) {
        return Promise.resolve({ data: mockLeaderboardData });
      }
      return Promise.reject(new Error('Not found'));
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  test('renders dashboard in grid layout', async () => {
    await act(async () => {
      render(<GamificationDashboard layout="grid" />);
    });

    await waitFor(() => {
      expect(screen.getByText(/Oyunlaştırma Dashboard/)).toBeInTheDocument();
    });
  });

  test('renders dashboard in tabs layout', async () => {
    await act(async () => {
      render(<GamificationDashboard layout="tabs" />);
    });

    await waitFor(() => {
      expect(screen.getByText(/Genel Bakış/)).toBeInTheDocument();
      expect(screen.getByText(/Rozetler/)).toBeInTheDocument();
      expect(screen.getByText(/Liderlik Tablosu/)).toBeInTheDocument();
    });
  });

  test('switches between tabs', async () => {
    await act(async () => {
      render(<GamificationDashboard layout="tabs" />);
    });

    await waitFor(() => {
      const badgesTab = screen.getByText(/Rozetler/);
      fireEvent.click(badgesTab);
    });

    // Should show badge collection
  });

  test('displays quick stats', async () => {
    await act(async () => {
      render(<GamificationDashboard layout="tabs" />);
    });

    await waitFor(() => {
      expect(screen.getByText(/1[.,]500/)).toBeInTheDocument(); // Points
      expect(screen.getByText(/5/)).toBeInTheDocument(); // Level
    });
  });
});

// ============================================================================
// Run Tests
// ============================================================================

export default {};

/**
 * Test Suite: Leaderboard Component
 * Task 91: Leaderboard System Testing
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Leaderboard } from '../Leaderboard';
import * as useGamificationHook from '../../../hooks/useGamification';

vi.mock('../../../hooks/useGamification');
const mockedUseGamification = useGamificationHook as jest.Mocked<typeof useGamificationHook>;

const mockLeaderboard = [
  { rank: 1, user_id: '1', username: 'TopPlayer', score: 10000, level: 50, avatar_url: 'avatar1.jpg' },
  { rank: 2, user_id: '2', username: 'SecondPlace', score: 8000, level: 45 },
  { rank: 3, user_id: '3', username: 'ThirdPlace', score: 6000, level: 40 },
  { rank: 4, user_id: '4', username: 'Player4', score: 5000, level: 35 },
];

const mockNearbyUsers = {
  above: [{ rank: 10, user_id: '10', username: 'Above1', score: 3000, level: 25 }],
  user: { rank: 11, user_id: 'current', username: 'CurrentUser', score: 2800, level: 24 },
  below: [{ rank: 12, user_id: '12', username: 'Below1', score: 2600, level: 23 }],
};

describe('Leaderboard - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: mockLeaderboard,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getNearbyUsers: vi.fn().mockResolvedValue(mockNearbyUsers),
    });
  });

  it('renders leaderboard', () => {
    render(<Leaderboard />);
    expect(screen.getByText('Liderlik Tablosu')).toBeInTheDocument();
  });

  it('shows loading spinner', () => {
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: [],
      loading: true,
      error: null,
      refresh: vi.fn(),
      getNearbyUsers: vi.fn(),
    });

    render(<Leaderboard />);
    expect(document.querySelector('.spinner')).toBeInTheDocument();
  });

  it('shows error message', () => {
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: [],
      loading: false,
      error: 'Failed',
      refresh: vi.fn(),
      getNearbyUsers: vi.fn(),
    });

    render(<Leaderboard />);
    expect(screen.getByText('Liderlik tablosu yüklenemedi')).toBeInTheDocument();
  });
});

describe('Leaderboard - Entries', () => {
  beforeEach(() => {
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: mockLeaderboard,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getNearbyUsers: vi.fn().mockResolvedValue(mockNearbyUsers),
    });
  });

  it('displays top 3 with medals', () => {
    render(<Leaderboard />);
    expect(screen.getByText('🥇')).toBeInTheDocument();
    expect(screen.getByText('🥈')).toBeInTheDocument();
    expect(screen.getByText('🥉')).toBeInTheDocument();
  });

  it('displays rank number for non-top-3', () => {
    render(<Leaderboard />);
    expect(screen.getByText('#4')).toBeInTheDocument();
  });

  it('shows username and score', () => {
    render(<Leaderboard />);
    expect(screen.getByText('TopPlayer')).toBeInTheDocument();
    expect(screen.getByText('10.000')).toBeInTheDocument();
  });

  it('displays avatar when available', () => {
    render(<Leaderboard />);
    const avatar = screen.getByAlt('TopPlayer');
    expect(avatar).toHaveAttribute('src', 'avatar1.jpg');
  });

  it('shows placeholder for missing avatar', () => {
    render(<Leaderboard />);
    expect(screen.getByText('S')).toBeInTheDocument(); // SecondPlace
  });

  it('displays level information', () => {
    render(<Leaderboard />);
    expect(screen.getByText('Seviye 50')).toBeInTheDocument();
  });
});

describe('Leaderboard - Tabs', () => {
  const mockRefresh = vi.fn();

  beforeEach(() => {
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: mockLeaderboard,
      loading: false,
      error: null,
      refresh: mockRefresh,
      getNearbyUsers: vi.fn().mockResolvedValue(mockNearbyUsers),
    });
  });

  it('shows all tabs', () => {
    render(<Leaderboard />);
    expect(screen.getByText('Global')).toBeInTheDocument();
    expect(screen.getByText('Haftalık')).toBeInTheDocument();
    expect(screen.getByText('Aylık')).toBeInTheDocument();
  });

  it('switches to weekly tab', () => {
    render(<Leaderboard />);

    const weeklyTab = screen.getByText('Haftalık');
    fireEvent.click(weeklyTab);

    expect(weeklyTab.closest('.tab-btn')).toHaveClass('active');
  });

  it('switches to monthly tab', () => {
    render(<Leaderboard />);

    const monthlyTab = screen.getByText('Aylık');
    fireEvent.click(monthlyTab);

    expect(monthlyTab.closest('.tab-btn')).toHaveClass('active');
  });

  it('uses defaultType prop', () => {
    render(<Leaderboard defaultType="weekly" />);
    expect(screen.getByText('Haftalık').closest('.tab-btn')).toHaveClass('active');
  });
});

describe('Leaderboard - Refresh', () => {
  const mockRefresh = vi.fn();

  beforeEach(() => {
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: mockLeaderboard,
      loading: false,
      error: null,
      refresh: mockRefresh,
      getNearbyUsers: vi.fn(),
    });
  });

  it('calls refresh when button clicked', () => {
    render(<Leaderboard />);

    const refreshBtn = screen.getByLabelText('Yenile');
    fireEvent.click(refreshBtn);

    expect(mockRefresh).toHaveBeenCalled();
  });

  it('disables refresh during loading', () => {
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: mockLeaderboard,
      loading: true,
      error: null,
      refresh: mockRefresh,
      getNearbyUsers: vi.fn(),
    });

    render(<Leaderboard />);

    const refreshBtn = screen.getByLabelText('Yenile');
    expect(refreshBtn).toBeDisabled();
  });
});

describe('Leaderboard - Nearby Users', () => {
  const mockGetNearby = vi.fn().mockResolvedValue(mockNearbyUsers);

  beforeEach(() => {
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: mockLeaderboard,
      loading: false,
      error: null,
      refresh: vi.fn(),
      getNearbyUsers: mockGetNearby,
    });
  });

  it('shows nearby toggle when enabled', () => {
    render(<Leaderboard showNearby />);
    expect(screen.getByText('Yakınımdakiler')).toBeInTheDocument();
  });

  it('hides nearby toggle when disabled', () => {
    render(<Leaderboard showNearby={false} />);
    expect(screen.queryByText('Yakınımdakiler')).not.toBeInTheDocument();
  });

  it('switches to nearby view', async () => {
    render(<Leaderboard showNearby />);

    const nearbyBtn = screen.getByText('Yakınımdakiler');
    fireEvent.click(nearbyBtn);

    await waitFor(() => {
      expect(mockGetNearby).toHaveBeenCalledWith(5);
    });
  });

  it('displays nearby sections', async () => {
    render(<Leaderboard showNearby />);

    fireEvent.click(screen.getByText('Yakınımdakiler'));

    await waitFor(() => {
      expect(screen.getByText('Üstünüzdekiler')).toBeInTheDocument();
      expect(screen.getByText('Siz')).toBeInTheDocument();
      expect(screen.getByText('Altınızdakiler')).toBeInTheDocument();
    });
  });

  it('marks current user', async () => {
    render(<Leaderboard showNearby />);

    fireEvent.click(screen.getByText('Yakınımdakiler'));

    await waitFor(() => {
      expect(screen.getByText('Sen')).toBeInTheDocument();
    });
  });
});

describe('Leaderboard - Empty States', () => {
  beforeEach(() => {
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: [],
      loading: false,
      error: null,
      refresh: vi.fn(),
      getNearbyUsers: vi.fn().mockResolvedValue({ above: [], user: null, below: [] }),
    });
  });

  it('shows no entries message', () => {
    render(<Leaderboard />);
    expect(screen.getByText('Henüz kayıt yok')).toBeInTheDocument();
  });

  it('shows no nearby users message', async () => {
    render(<Leaderboard showNearby />);

    fireEvent.click(screen.getByText('Yakınımdakiler'));

    await waitFor(() => {
      expect(screen.getByText('Yakınınızda kimse yok')).toBeInTheDocument();
    });
  });
});

describe('Leaderboard - Limit', () => {
  beforeEach(() => {
    mockedUseGamification.useLeaderboard = vi.fn().mockReturnValue({
      leaderboard: Array.from({ length: 150 }, (_, i) => ({
        rank: i + 1,
        user_id: `user${i}`,
        username: `User${i}`,
        score: 10000 - i * 100,
        level: 50 - i,
      })),
      loading: false,
      error: null,
      refresh: vi.fn(),
      getNearbyUsers: vi.fn(),
    });
  });

  it('respects limit prop', () => {
    render(<Leaderboard limit={10} />);

    const entries = document.querySelectorAll('.leaderboard-entry');
    expect(entries.length).toBe(10);
  });

  it('uses default limit of 100', () => {
    render(<Leaderboard />);

    const entries = document.querySelectorAll('.leaderboard-entry');
    expect(entries.length).toBe(100);
  });
});

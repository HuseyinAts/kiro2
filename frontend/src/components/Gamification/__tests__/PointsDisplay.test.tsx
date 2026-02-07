/**
 * Test Suite: PointsDisplay Component
 * Task 91: Gamification - Points & History Testing
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PointsDisplay } from '../PointsDisplay';
import * as useGamificationHook from '../../../hooks/useGamification';
import { vi, Mocked } from 'vitest';

vi.mock('../../../hooks/useGamification');
const mockedUseGamification = useGamificationHook as Mocked<typeof useGamificationHook>;

const mockHistory = [
  {
    id: 1,
    points: 100,
    reason: 'Quiz tamamlandı',
    timestamp: '2025-10-28T10:00:00Z'
  },
  {
    id: 2,
    points: 50,
    reason: 'Video izlendi',
    timestamp: '2025-10-28T09:30:00Z'
  },
  {
    id: 3,
    points: -20,
    reason: 'Yanlış cevap',
    timestamp: '2025-10-28T09:00:00Z'
  },
  {
    id: 4,
    points: 200,
    reason: 'Başarı rozeti kazanıldı',
    timestamp: '2025-10-27T18:00:00Z'
  }
];

describe('PointsDisplay - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue(mockHistory),
    });
  });

  it('renders points display', () => {
    render(<PointsDisplay />);
    expect(screen.getByText('Puanlarım')).toBeInTheDocument();
  });

  it('shows loading spinner when loading and points are 0', () => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 0,
      loading: true,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn(),
    });

    render(<PointsDisplay />);
    expect(document.querySelector('.spinner')).toBeInTheDocument();
  });

  it('does not show loading when points exist', () => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: true,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn(),
    });

    render(<PointsDisplay />);
    expect(document.querySelector('.spinner')).not.toBeInTheDocument();
    expect(screen.getByText('5.000')).toBeInTheDocument();
  });

  it('shows error message', () => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 0,
      loading: false,
      error: 'Network error',
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn(),
    });

    render(<PointsDisplay />);
    expect(screen.getByText('Puan yüklenemedi')).toBeInTheDocument();
    expect(screen.getByText('⚠️')).toBeInTheDocument();
  });
});

describe('PointsDisplay - Points Display', () => {
  beforeEach(() => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue([]),
    });
  });

  it('displays points with Turkish locale', () => {
    render(<PointsDisplay />);
    expect(screen.getByText('5.000')).toBeInTheDocument();
  });

  it('displays star icon', () => {
    render(<PointsDisplay />);
    const stars = screen.getAllByText('⭐');
    expect(stars.length).toBeGreaterThan(0);
  });

  it('displays "Toplam Puan" label', () => {
    render(<PointsDisplay />);
    expect(screen.getByText('Toplam Puan')).toBeInTheDocument();
  });

  it('handles zero points', () => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 0,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn(),
    });

    render(<PointsDisplay />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('handles large point values', () => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 1234567,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn(),
    });

    render(<PointsDisplay />);
    expect(screen.getByText('1.234.567')).toBeInTheDocument();
  });
});

describe('PointsDisplay - Compact Mode', () => {
  beforeEach(() => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn(),
    });
  });

  it('renders in compact mode', () => {
    render(<PointsDisplay compact />);
    expect(document.querySelector('.points-display.compact')).toBeInTheDocument();
  });

  it('shows points in compact mode', () => {
    render(<PointsDisplay compact />);
    expect(screen.getByText('5.000')).toBeInTheDocument();
  });

  it('shows star icon in compact mode', () => {
    render(<PointsDisplay compact />);
    expect(screen.getByText('⭐')).toBeInTheDocument();
  });

  it('hides detailed info in compact mode', () => {
    render(<PointsDisplay compact />);
    expect(screen.queryByText('Puanlarım')).not.toBeInTheDocument();
    expect(screen.queryByText('Toplam Puan')).not.toBeInTheDocument();
  });

  it('hides history toggle in compact mode', () => {
    render(<PointsDisplay compact showHistory />);
    expect(screen.queryByLabelText('Puan geçmişini göster')).not.toBeInTheDocument();
  });
});

describe('PointsDisplay - History Toggle', () => {
  const mockGetHistory = vi.fn().mockResolvedValue(mockHistory);

  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: mockGetHistory,
    });
  });

  it('shows history toggle button when showHistory is true', () => {
    render(<PointsDisplay showHistory />);
    expect(screen.getByLabelText('Puan geçmişini göster')).toBeInTheDocument();
  });

  it('hides history toggle when showHistory is false', () => {
    render(<PointsDisplay showHistory={false} />);
    expect(screen.queryByLabelText('Puan geçmişini göster')).not.toBeInTheDocument();
  });

  it('shows "Geçmişi Göster" text initially', () => {
    render(<PointsDisplay showHistory />);
    expect(screen.getByText('Geçmişi Göster')).toBeInTheDocument();
  });

  it('shows scroll emoji initially', () => {
    render(<PointsDisplay showHistory />);
    expect(screen.getByText('📜')).toBeInTheDocument();
  });

  it('toggles to "Geçmişi Gizle" when clicked', async () => {
    render(<PointsDisplay showHistory />);

    const toggleButton = screen.getByLabelText('Puan geçmişini göster');
    fireEvent.click(toggleButton);

    await waitFor(() => {
      expect(screen.getByText('Geçmişi Gizle')).toBeInTheDocument();
    });
  });

  it('shows chart emoji when history is visible', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('📊')).toBeInTheDocument();
    });
  });

  it('calls getHistory when toggled on', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(mockGetHistory).toHaveBeenCalledWith(20);
    });
  });

  it('does not call getHistory when toggled off', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));
    await waitFor(() => expect(mockGetHistory).toHaveBeenCalledTimes(1));

    mockGetHistory.mockClear();
    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    expect(mockGetHistory).not.toHaveBeenCalled();
  });
});

describe('PointsDisplay - History Display', () => {
  const mockGetHistory = vi.fn().mockResolvedValue(mockHistory);

  beforeEach(() => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: mockGetHistory,
    });
  });

  it('shows history section when toggled', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('Son İşlemler')).toBeInTheDocument();
    });
  });

  it('displays history items', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('Quiz tamamlandı')).toBeInTheDocument();
      expect(screen.getByText('Video izlendi')).toBeInTheDocument();
      expect(screen.getByText('Yanlış cevap')).toBeInTheDocument();
      expect(screen.getByText('Başarı rozeti kazanıldı')).toBeInTheDocument();
    });
  });

  it('displays positive points with + sign', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('+100')).toBeInTheDocument();
      expect(screen.getByText('+50')).toBeInTheDocument();
      expect(screen.getByText('+200')).toBeInTheDocument();
    });
  });

  it('displays negative points without + sign', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('-20')).toBeInTheDocument();
    });
  });

  it('shows target emoji for positive points', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      const targetEmojis = screen.getAllByText('🎯');
      expect(targetEmojis.length).toBe(3); // 3 positive transactions
    });
  });

  it('shows money emoji for negative points', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('💸')).toBeInTheDocument();
    });
  });

  it('applies positive class to positive points', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      const positiveElement = screen.getByText('+100').closest('.history-points');
      expect(positiveElement).toHaveClass('positive');
    });
  });

  it('applies negative class to negative points', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      const negativeElement = screen.getByText('-20').closest('.history-points');
      expect(negativeElement).toHaveClass('negative');
    });
  });

  it('formats dates in Turkish locale', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      const dates = document.querySelectorAll('.history-date');
      expect(dates.length).toBeGreaterThan(0);
    });
  });
});

describe('PointsDisplay - Empty History', () => {
  beforeEach(() => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue([]),
    });
  });

  it('shows "Henüz işlem yok" when history is empty', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('Henüz işlem yok')).toBeInTheDocument();
    });
  });

  it('does not show history items when empty', async () => {
    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.queryByText('Quiz tamamlandı')).not.toBeInTheDocument();
    });
  });
});

describe('PointsDisplay - Loading Overlay', () => {
  it('shows loading overlay when loading with existing points', () => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: true,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn(),
    });

    render(<PointsDisplay />);
    expect(document.querySelector('.points-loading-overlay')).toBeInTheDocument();
    expect(document.querySelector('.spinner-small')).toBeInTheDocument();
  });

  it('does not show loading overlay when not loading', () => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn(),
    });

    render(<PointsDisplay />);
    expect(document.querySelector('.points-loading-overlay')).not.toBeInTheDocument();
  });
});

describe('PointsDisplay - Edge Cases', () => {
  it('handles history item without id', async () => {
    const historyWithoutIds = mockHistory.map(item => {
      const { id, ...rest } = item;
      return rest;
    });

    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue(historyWithoutIds),
    });

    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('Quiz tamamlandı')).toBeInTheDocument();
    });
  });

  it('handles zero points in history', async () => {
    const historyWithZero = [
      { id: 1, points: 0, reason: 'Neutral action', timestamp: '2025-10-28T10:00:00Z' }
    ];

    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue(historyWithZero),
    });

    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('Neutral action')).toBeInTheDocument();
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  it('handles very long reason text', async () => {
    const historyWithLongText = [
      {
        id: 1,
        points: 100,
        reason: 'Bu çok uzun bir açıklama metnidir ve düzgün şekilde gösterilmelidir',
        timestamp: '2025-10-28T10:00:00Z'
      }
    ];

    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue(historyWithLongText),
    });

    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText(/Bu çok uzun bir açıklama/)).toBeInTheDocument();
    });
  });

  it('handles history with single item', async () => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue([mockHistory[0]]),
    });

    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('Quiz tamamlandı')).toBeInTheDocument();
      expect(screen.queryByText('Video izlendi')).not.toBeInTheDocument();
    });
  });

  it('handles history with many items', async () => {
    const manyItems = Array.from({ length: 50 }, (_, i) => ({
      id: i + 1,
      points: (i % 2 === 0 ? 1 : -1) * 50,
      reason: `İşlem ${i + 1}`,
      timestamp: '2025-10-28T10:00:00Z'
    }));

    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue(manyItems),
    });

    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByText('İşlem 1')).toBeInTheDocument();
      expect(screen.getByText('İşlem 50')).toBeInTheDocument();
    });
  });
});

describe('PointsDisplay - Accessibility', () => {
  beforeEach(() => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue([]),
    });
  });

  it('uses semantic HTML structure', () => {
    render(<PointsDisplay />);
    expect(screen.getByRole('heading', { name: 'Puanlarım' })).toBeInTheDocument();
  });

  it('has accessible history toggle button', () => {
    render(<PointsDisplay showHistory />);
    const button = screen.getByLabelText('Puan geçmişini göster');
    expect(button).toBeInTheDocument();
    expect(button.tagName).toBe('BUTTON');
  });

  it('displays history heading', async () => {
    mockedUseGamification.usePoints = vi.fn().mockReturnValue({
      points: 5000,
      loading: false,
      error: null,
      refresh: vi.fn(),
      awardPoints: vi.fn(),
      getHistory: vi.fn().mockResolvedValue(mockHistory),
    });

    render(<PointsDisplay showHistory />);

    fireEvent.click(screen.getByLabelText('Puan geçmişini göster'));

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Son İşlemler' })).toBeInTheDocument();
    });
  });
});

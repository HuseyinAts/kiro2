/**
 * Test Suite: ManipulativesProgressDashboard Component
 * Task 87.9: Progress Dashboard Testing
 *
 * Tests progress tracking, data visualization, charts,
 * badges, and view switching.
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import ManipulativesProgressDashboard from '../ManipulativesProgressDashboard';
import { vi, Mocked } from 'vitest';

// ============================================================
// Mocks
// ============================================================

vi.mock('axios');
const mockedAxios = axios as Mocked<typeof axios>;

// Mock recharts
vi.mock('recharts', () => ({
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
}));

const mockProgressData = {
  virtualBlocks: {
    total_operations: 45,
    operations_by_type: { add: 15, subtract: 10, multiply: 12, divide: 8 },
    avg_duration: 120,
    mastery_level: 75,
  },
  geogebra: {
    total_activities: 12,
    activities_by_type: { geometry: 5, algebra: 4, calculus: 3 },
    completion_rate: 0.8,
    avg_duration: 300,
  },
  geometry: {
    total_shapes: 28,
    shapes_by_type: { line: 10, circle: 8, rectangle: 6, triangle: 4 },
    measurements_count: 15,
    tools_used: ['ruler', 'protractor'],
  },
  tangram: {
    puzzles_attempted: 10,
    puzzles_completed: 7,
    completion_rate: 0.7,
    avg_attempts: 3.5,
  },
};

const mockBadges = [
  { id: '1', name: 'İlk Adım', description: 'İlk manipülatifi tamamla', icon: '🎯', earned: true, earnedDate: '2024-01-01' },
  { id: '2', name: 'Ustalaşma', description: '100 işlem tamamla', icon: '⭐', earned: false },
];

// ============================================================
// Tests: Rendering
// ============================================================

describe('ManipulativesProgressDashboard - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/badges')) {
        return Promise.resolve({ data: { success: true, data: mockBadges } });
      }
      return Promise.resolve({ data: { success: true, data: mockProgressData } });
    });
  });

  it('renders loading state', () => {
    mockedAxios.get.mockReturnValue(new Promise(() => {}));
    render(<ManipulativesProgressDashboard />);
    expect(screen.getByText('Yükleniyor...')).toBeInTheDocument();
  });

  it('renders dashboard after loading', async () => {
    render(<ManipulativesProgressDashboard />);
    await waitFor(() => {
      expect(screen.getByText('Manipülatifler İlerleme Panosu')).toBeInTheDocument();
    });
  });

  it('renders view selector buttons', async () => {
    render(<ManipulativesProgressDashboard />);
    await waitFor(() => {
      expect(screen.getByText(/Genel Bakış/)).toBeInTheDocument();
      expect(screen.getByText(/Detaylı İstatistikler/)).toBeInTheDocument();
      expect(screen.getByText(/Rozetler/)).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Data Loading
// ============================================================

describe('ManipulativesProgressDashboard - Data Loading', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/badges')) {
        return Promise.resolve({ data: { success: true, data: mockBadges } });
      }
      return Promise.resolve({ data: { success: true, data: mockProgressData } });
    });
  });

  it('fetches progress data on mount', async () => {
    render(<ManipulativesProgressDashboard />);
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/manipulatives/progress/dashboard');
    });
  });

  it('fetches badges on mount', async () => {
    render(<ManipulativesProgressDashboard />);
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/manipulatives/badges');
    });
  });

  it('handles progress data fetch error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.get.mockRejectedValue(new Error('Failed'));

    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });

  it('shows message when no data', async () => {
    mockedAxios.get.mockResolvedValue({ data: { success: false } });

    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText('İlerleme verisi bulunamadı.')).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Overview View
// ============================================================

describe('ManipulativesProgressDashboard - Overview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/badges')) {
        return Promise.resolve({ data: { success: true, data: mockBadges } });
      }
      return Promise.resolve({ data: { success: true, data: mockProgressData } });
    });
  });

  it('displays summary cards', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText('45')).toBeInTheDocument(); // Total operations
      expect(screen.getByText('12')).toBeInTheDocument(); // GeoGebra activities
      expect(screen.getByText('28')).toBeInTheDocument(); // Shapes
      expect(screen.getByText('7')).toBeInTheDocument(); // Completed puzzles
    });
  });

  it('shows mastery levels', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Ustalık: 75%/)).toBeInTheDocument();
    });
  });

  it('shows completion rates', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Tamamlanma: 80%/)).toBeInTheDocument();
      expect(screen.getByText(/Başarı: 70%/)).toBeInTheDocument();
    });
  });

  it('renders charts', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: View Switching
// ============================================================

describe('ManipulativesProgressDashboard - View Switching', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/badges')) {
        return Promise.resolve({ data: { success: true, data: mockBadges } });
      }
      return Promise.resolve({ data: { success: true, data: mockProgressData } });
    });
  });

  it('switches to details view', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Genel Bakış/)).toBeInTheDocument();
    });

    const detailsButton = screen.getByText(/Detaylı İstatistikler/);
    fireEvent.click(detailsButton);

    expect(detailsButton).toHaveClass('bg-blue-500');
  });

  it('switches to badges view', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Rozetler/)).toBeInTheDocument();
    });

    const badgesButton = screen.getByText(/Rozetler/);
    fireEvent.click(badgesButton);

    expect(badgesButton).toHaveClass('bg-blue-500');
  });

  it('highlights active view', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      const overviewButton = screen.getByText(/Genel Bakış/);
      expect(overviewButton).toHaveClass('bg-blue-500', 'text-white');
    });
  });
});

// ============================================================
// Tests: Statistics Display
// ============================================================

describe('ManipulativesProgressDashboard - Statistics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/badges')) {
        return Promise.resolve({ data: { success: true, data: mockBadges } });
      }
      return Promise.resolve({ data: { success: true, data: mockProgressData } });
    });
  });

  it('calculates percentages correctly', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      // 0.8 * 100 = 80%
      expect(screen.getByText(/80%/)).toBeInTheDocument();
      // 0.7 * 100 = 70%
      expect(screen.getByText(/70%/)).toBeInTheDocument();
    });
  });

  it('displays measurement counts', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/15 Ölçüm/)).toBeInTheDocument();
    });
  });

  it('shows puzzle ratios', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/\/ 10 Puzzle/)).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: User ID Props
// ============================================================

describe('ManipulativesProgressDashboard - User ID', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/badges')) {
        return Promise.resolve({ data: { success: true, data: mockBadges } });
      }
      return Promise.resolve({ data: { success: true, data: mockProgressData } });
    });
  });

  it('accepts userId prop', async () => {
    render(<ManipulativesProgressDashboard userId={123} />);

    await waitFor(() => {
      expect(screen.getByText('Manipülatifler İlerleme Panosu')).toBeInTheDocument();
    });
  });

  it('works without userId prop', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Manipülatifler İlerleme Panosu')).toBeInTheDocument();
    });
  });

  it('refetches data when userId changes', async () => {
    const { rerender } = render(<ManipulativesProgressDashboard userId={1} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });

    vi.clearAllMocks();

    rerender(<ManipulativesProgressDashboard userId={2} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalled();
    });
  });
});

// ============================================================
// Tests: Chart Data Preparation
// ============================================================

describe('ManipulativesProgressDashboard - Chart Data', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/badges')) {
        return Promise.resolve({ data: { success: true, data: mockBadges } });
      }
      return Promise.resolve({ data: { success: true, data: mockProgressData } });
    });
  });

  it('transforms operation data for charts', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Sanal Bloklar İşlem Dağılımı')).toBeInTheDocument();
    });
  });

  it('transforms activity data for charts', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      expect(screen.getByText('GeoGebra Aktivite Türleri')).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Accessibility
// ============================================================

describe('ManipulativesProgressDashboard - Accessibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/badges')) {
        return Promise.resolve({ data: { success: true, data: mockBadges } });
      }
      return Promise.resolve({ data: { success: true, data: mockProgressData } });
    });
  });

  it('has proper button labels', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
      buttons.forEach(button => {
        expect(button.textContent).toBeTruthy();
      });
    });
  });

  it('uses semantic headings', async () => {
    render(<ManipulativesProgressDashboard />);

    await waitFor(() => {
      const headings = screen.getAllByRole('heading');
      expect(headings.length).toBeGreaterThan(0);
    });
  });
});

/**
 * Test Suite: ProgramSearch Component
 * Task 101: University Advisory - Program Search & Filters Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ProgramSearch, Program } from '../ProgramSearch';

// Mock fetch
global.fetch = vi.fn();

const mockPrograms: Program[] = [
  {
    id: '1',
    programName: 'Bilgisayar Mühendisliği',
    universityName: 'İTÜ',
    departmentName: 'Mühendislik Fakültesi',
    city: 'İstanbul',
    year: 2024,
    scoreType: 'SAY',
    baseScore: 485.50,
    topScore: 520.30,
    medianScore: 502.15,
    totalQuota: 120,
    filledQuota: 120,
    acceptanceRate: 100,
    scholarship: false,
    tuitionFee: null
  },
  {
    id: '2',
    programName: 'Yazılım Mühendisliği',
    universityName: 'ODTÜ',
    departmentName: 'Mühendislik Fakültesi',
    city: 'Ankara',
    year: 2024,
    scoreType: 'SAY',
    baseScore: 480.00,
    topScore: 515.00,
    medianScore: 495.00,
    totalQuota: 100,
    filledQuota: 95,
    acceptanceRate: 95,
    scholarship: false,
    tuitionFee: null
  },
  {
    id: '3',
    programName: 'Bilgisayar Mühendisliği',
    universityName: 'Bilkent',
    departmentName: 'Mühendislik Fakültesi',
    city: 'Ankara',
    year: 2024,
    scoreType: 'SAY',
    baseScore: 450.00,
    topScore: 490.00,
    medianScore: 470.00,
    totalQuota: 80,
    filledQuota: 80,
    acceptanceRate: 100,
    scholarship: true,
    tuitionFee: 150000
  }
];

const mockCities = ['İstanbul', 'Ankara', 'İzmir', 'Bursa'];

describe('ProgramSearch - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => mockPrograms });
  });

  it('renders search header', async () => {
    render(<ProgramSearch />);
    expect(screen.getByText('Üniversite Programları Arama')).toBeInTheDocument();
  });

  it('renders all filter inputs', async () => {
    render(<ProgramSearch />);

    expect(screen.getByLabelText('Yıl')).toBeInTheDocument();
    expect(screen.getByLabelText('Puan Türü')).toBeInTheDocument();
    expect(screen.getByLabelText('Min. Taban Puan')).toBeInTheDocument();
    expect(screen.getByLabelText('Max. Taban Puan')).toBeInTheDocument();
    expect(screen.getByLabelText('Şehir')).toBeInTheDocument();
    expect(screen.getByLabelText('Üniversite Türü')).toBeInTheDocument();
    expect(screen.getByLabelText('Bölüm Adı')).toBeInTheDocument();
    expect(screen.getByLabelText('Burs')).toBeInTheDocument();
  });

  it('renders search and clear buttons', () => {
    render(<ProgramSearch />);
    expect(screen.getByText('Ara')).toBeInTheDocument();
    expect(screen.getByText('Filtreleri Temizle')).toBeInTheDocument();
  });

  it('shows results count', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('3 Program Bulundu')).toBeInTheDocument();
    });
  });
});

describe('ProgramSearch - Data Loading', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads cities on mount', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => [] });

    render(<ProgramSearch />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/university-advisory/cities')
      );
    });
  });

  it('performs initial search on mount', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => mockPrograms });

    render(<ProgramSearch />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/university-advisory/programs')
      );
    });
  });

  it('displays loading state during search', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockImplementation(() => new Promise(() => {}));

    render(<ProgramSearch />);

    await waitFor(() => {
      const button = screen.getByText('Aranıyor...');
      expect(button).toBeInTheDocument();
      expect(button).toBeDisabled();
    });
  });

  it('displays programs after loading', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => mockPrograms });

    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('Bilgisayar Mühendisliği')).toBeInTheDocument();
      expect(screen.getByText('Yazılım Mühendisliği')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockRejectedValueOnce(new Error('Network error'));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();

    render(<ProgramSearch />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to search programs:',
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });
});

describe('ProgramSearch - Filters', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => mockPrograms });
  });

  it('has default year 2024', () => {
    render(<ProgramSearch />);
    const yearSelect = screen.getByLabelText('Yıl') as HTMLSelectElement;
    expect(yearSelect.value).toBe('2024');
  });

  it('has default score type SAY', () => {
    render(<ProgramSearch />);
    const scoreTypeSelect = screen.getByLabelText('Puan Türü') as HTMLSelectElement;
    expect(scoreTypeSelect.value).toBe('SAY');
  });

  it('changes year filter', () => {
    render(<ProgramSearch />);
    const yearSelect = screen.getByLabelText('Yıl');
    fireEvent.change(yearSelect, { target: { value: '2023' } });
    expect((yearSelect as HTMLSelectElement).value).toBe('2023');
  });

  it('changes score type filter', () => {
    render(<ProgramSearch />);
    const scoreTypeSelect = screen.getByLabelText('Puan Türü');
    fireEvent.change(scoreTypeSelect, { target: { value: 'EA' } });
    expect((scoreTypeSelect as HTMLSelectElement).value).toBe('EA');
  });

  it('sets min score', () => {
    render(<ProgramSearch />);
    const minScoreInput = screen.getByLabelText('Min. Taban Puan') as HTMLInputElement;
    fireEvent.change(minScoreInput, { target: { value: '400' } });
    expect(minScoreInput.value).toBe('400');
  });

  it('sets max score', () => {
    render(<ProgramSearch />);
    const maxScoreInput = screen.getByLabelText('Max. Taban Puan') as HTMLInputElement;
    fireEvent.change(maxScoreInput, { target: { value: '500' } });
    expect(maxScoreInput.value).toBe('500');
  });

  it('selects city', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('İstanbul')).toBeInTheDocument();
    });

    const citySelect = screen.getByLabelText('Şehir');
    fireEvent.change(citySelect, { target: { value: 'İstanbul' } });
    expect((citySelect as HTMLSelectElement).value).toBe('İstanbul');
  });

  it('selects university type', () => {
    render(<ProgramSearch />);
    const universityTypeSelect = screen.getByLabelText('Üniversite Türü');
    fireEvent.change(universityTypeSelect, { target: { value: 'devlet' } });
    expect((universityTypeSelect as HTMLSelectElement).value).toBe('devlet');
  });

  it('enters department name', () => {
    render(<ProgramSearch />);
    const departmentInput = screen.getByLabelText('Bölüm Adı') as HTMLInputElement;
    fireEvent.change(departmentInput, { target: { value: 'Bilgisayar' } });
    expect(departmentInput.value).toBe('Bilgisayar');
  });

  it('selects scholarship filter', () => {
    render(<ProgramSearch />);
    const scholarshipSelect = screen.getByLabelText('Burs');
    fireEvent.change(scholarshipSelect, { target: { value: 'true' } });
    expect((scholarshipSelect as HTMLSelectElement).value).toBe('true');
  });
});

describe('ProgramSearch - Search Button', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => mockPrograms });
  });

  it('triggers search when clicked', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    (global.fetch as jest.Mock).mockClear();
    (global.fetch as jest.Mock).mockResolvedValueOnce({ json: async () => [] });

    const searchButton = screen.getByText('Ara');
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/university-advisory/programs')
      );
    });
  });

  it('includes filters in search request', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('Ara')).toBeInTheDocument();
    });

    const minScoreInput = screen.getByLabelText('Min. Taban Puan');
    fireEvent.change(minScoreInput, { target: { value: '450' } });

    (global.fetch as jest.Mock).mockClear();
    (global.fetch as jest.Mock).mockResolvedValueOnce({ json: async () => [] });

    const searchButton = screen.getByText('Ara');
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('min_score=450')
      );
    });
  });

  it('disables button during search', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockImplementation(() => new Promise(() => {}));

    render(<ProgramSearch />);

    await waitFor(() => {
      const button = screen.getByText('Aranıyor...');
      expect(button).toBeDisabled();
    });
  });
});

describe('ProgramSearch - Clear Filters', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => mockPrograms });
  });

  it('clears all filters', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('Ara')).toBeInTheDocument();
    });

    // Set filters
    const minScoreInput = screen.getByLabelText('Min. Taban Puan') as HTMLInputElement;
    const maxScoreInput = screen.getByLabelText('Max. Taban Puan') as HTMLInputElement;
    const departmentInput = screen.getByLabelText('Bölüm Adı') as HTMLInputElement;

    fireEvent.change(minScoreInput, { target: { value: '400' } });
    fireEvent.change(maxScoreInput, { target: { value: '500' } });
    fireEvent.change(departmentInput, { target: { value: 'Bilgisayar' } });

    // Clear filters
    const clearButton = screen.getByText('Filtreleri Temizle');
    fireEvent.click(clearButton);

    expect(minScoreInput.value).toBe('');
    expect(maxScoreInput.value).toBe('');
    expect(departmentInput.value).toBe('');
  });
});

describe('ProgramSearch - Program Display', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => mockPrograms });
  });

  it('displays program name', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('Bilgisayar Mühendisliği')).toBeInTheDocument();
    });
  });

  it('displays university and city', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText(/İTÜ - İstanbul/)).toBeInTheDocument();
    });
  });

  it('displays base score', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('485.50')).toBeInTheDocument();
    });
  });

  it('displays top score', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('520.30')).toBeInTheDocument();
    });
  });

  it('displays median score', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('502.15')).toBeInTheDocument();
    });
  });

  it('displays quota information', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('120')).toBeInTheDocument();
    });
  });

  it('displays acceptance rate', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('100.0%')).toBeInTheDocument();
    });
  });

  it('shows scholarship badge for scholarship programs', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('Burslu')).toBeInTheDocument();
    });
  });

  it('displays tuition fee when available', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText(/150.000 TL\/yıl/)).toBeInTheDocument();
    });
  });

  it('calls onSelectProgram when program clicked', async () => {
    const onSelectProgram = vi.fn();
    render(<ProgramSearch onSelectProgram={onSelectProgram} />);

    await waitFor(() => {
      expect(screen.getByText('Bilgisayar Mühendisliği')).toBeInTheDocument();
    });

    const programCard = screen.getAllByText('Bilgisayar Mühendisliği')[0].closest('.program-card');
    fireEvent.click(programCard!);

    expect(onSelectProgram).toHaveBeenCalledWith(expect.objectContaining({
      programName: 'Bilgisayar Mühendisliği'
    }));
  });
});

describe('ProgramSearch - Empty State', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => [] });
  });

  it('shows empty state when no programs found', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('Filtrelere uygun program bulunamadı')).toBeInTheDocument();
    });
  });

  it('shows 0 Program Bulundu', async () => {
    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getByText('0 Program Bulundu')).toBeInTheDocument();
    });
  });
});

describe('ProgramSearch - Score Types', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => [] });
  });

  it('shows all score type options', () => {
    render(<ProgramSearch />);

    expect(screen.getByText('SAY (Sayısal)')).toBeInTheDocument();
    expect(screen.getByText('EA (Eşit Ağırlık)')).toBeInTheDocument();
    expect(screen.getByText('SÖZ (Sözel)')).toBeInTheDocument();
    expect(screen.getByText('DİL (Dil)')).toBeInTheDocument();
  });
});

describe('ProgramSearch - University Types', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => [] });
  });

  it('shows university type options', () => {
    render(<ProgramSearch />);

    const universityTypeSelect = screen.getByLabelText('Üniversite Türü');
    expect(universityTypeSelect).toBeInTheDocument();

    fireEvent.click(universityTypeSelect);
    expect(screen.getByText('Devlet')).toBeInTheDocument();
    expect(screen.getByText('Vakıf')).toBeInTheDocument();
  });
});

describe('ProgramSearch - Cities Loading', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays loaded cities in dropdown', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => [] });

    render(<ProgramSearch />);

    await waitFor(() => {
      const citySelect = screen.getByLabelText('Şehir');
      expect(citySelect).toBeInTheDocument();
    });

    const citySelect = screen.getByLabelText('Şehir');
    fireEvent.click(citySelect);

    mockCities.forEach(city => {
      expect(screen.getByText(city)).toBeInTheDocument();
    });
  });

  it('handles city loading errors', async () => {
    (global.fetch as jest.Mock)
      .mockRejectedValueOnce(new Error('Failed to load cities'))
      .mockResolvedValueOnce({ json: async () => [] });

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();

    render(<ProgramSearch />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to load cities:',
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });
});

describe('ProgramSearch - Edge Cases', () => {
  it('handles missing score values', async () => {
    const programWithoutScores = [{
      ...mockPrograms[0],
      baseScore: 0,
      topScore: 0,
      medianScore: 0
    }];

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => programWithoutScores });

    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
    });
  });

  it('handles missing quota values', async () => {
    const programWithoutQuota = [{
      ...mockPrograms[0],
      totalQuota: 0,
      filledQuota: 0
    }];

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => programWithoutQuota });

    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.getAllByText('N/A').length).toBeGreaterThan(0);
    });
  });

  it('does not display tuition fee when null', async () => {
    const programWithoutFee = [{
      ...mockPrograms[0],
      tuitionFee: null
    }];

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ json: async () => mockCities })
      .mockResolvedValueOnce({ json: async () => programWithoutFee });

    render(<ProgramSearch />);

    await waitFor(() => {
      expect(screen.queryByText(/Öğrenim Ücreti:/)).not.toBeInTheDocument();
    });
  });
});

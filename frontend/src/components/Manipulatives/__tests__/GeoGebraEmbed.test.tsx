/**
 * Test Suite: GeoGebraEmbed Component
 * Task 87.2: GeoGebra Integration Testing
 *
 * Tests iframe embedding, applet selection, activity tracking,
 * save/complete functionality, and error handling.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import GeoGebraEmbed from '../GeoGebraEmbed';

// ============================================================
// Mocks
// ============================================================

// Mock Axios
vi.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock window.alert
global.alert = vi.fn();

// ============================================================
// Test Data
// ============================================================

const mockApplets = [
  {
    id: 'geometry-basic',
    name: 'Temel Geometri',
    type: 'geometry',
    url: 'https://www.geogebra.org/material/iframe/id/basic',
    description: 'Temel geometri şekilleri çizimi',
  },
  {
    id: 'algebra-functions',
    name: 'Fonksiyonlar',
    type: 'algebra',
    url: 'https://www.geogebra.org/material/iframe/id/functions',
    description: 'Fonksiyon grafikleri ve dönüşümleri',
  },
  {
    id: 'trigonometry',
    name: 'Trigonometri',
    type: 'geometry',
    url: 'https://www.geogebra.org/material/iframe/id/trig',
    description: 'Birim çember ve trigonometrik fonksiyonlar',
  },
];

const mockSuccessResponse = {
  data: {
    success: true,
    data: mockApplets,
  },
};

// ============================================================
// Tests: Rendering
// ============================================================

describe('GeoGebraEmbed Component - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
  });

  it('renders loading state initially', () => {
    mockedAxios.get.mockReturnValue(new Promise(() => {})); // Never resolves

    render(<GeoGebraEmbed />);

    expect(screen.getByText('Yükleniyor...')).toBeInTheDocument();
  });

  it('renders component after loading', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('GeoGebra İnteraktif Matematik')).toBeInTheDocument();
    });
  });

  it('displays applet selector', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('Aktivite Seç:')).toBeInTheDocument();
    });
  });

  it('displays all available applets', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('Temel Geometri')).toBeInTheDocument();
      expect(screen.getByText('Fonksiyonlar')).toBeInTheDocument();
      expect(screen.getByText('Trigonometri')).toBeInTheDocument();
    });
  });

  it('displays control buttons', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('Kaydet')).toBeInTheDocument();
      expect(screen.getByText('Tamamla')).toBeInTheDocument();
    });
  });

  it('displays help text', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText(/GeoGebra Hakkında/i)).toBeInTheDocument();
      expect(screen.getByText(/dinamik matematik yazılımıdır/i)).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Data Fetching
// ============================================================

describe('GeoGebraEmbed Component - Data Fetching', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
  });

  it('fetches applets on mount', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/manipulatives/geogebra/applets');
    });
  });

  it('loads default applet', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      const iframe = document.querySelector('iframe');
      expect(iframe).toBeInTheDocument();
      expect(iframe?.src).toContain('basic');
    });
  });

  it('handles fetch error gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.get.mockRejectedValue(new Error('Network error'));

    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Applet listesi yüklenemedi:',
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });

  it('shows loading state then applets', async () => {
    render(<GeoGebraEmbed />);

    expect(screen.getByText('Yükleniyor...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText('Yükleniyor...')).not.toBeInTheDocument();
      expect(screen.getByText('GeoGebra İnteraktif Matematik')).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Applet Selection
// ============================================================

describe('GeoGebraEmbed Component - Applet Selection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
  });

  it('selects default applet on load', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      const selectedButton = screen.getByText('Temel Geometri').closest('button');
      expect(selectedButton).toHaveClass('border-blue-500');
    });
  });

  it('changes applet when clicked', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('Fonksiyonlar')).toBeInTheDocument();
    });

    const functionsButton = screen.getByText('Fonksiyonlar').closest('button')!;
    fireEvent.click(functionsButton);

    await waitFor(() => {
      expect(functionsButton).toHaveClass('border-blue-500');
      const iframe = document.querySelector('iframe');
      expect(iframe?.src).toContain('functions');
    });
  });

  it('displays selected applet info', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      expect(screen.getByText(/Temel Geometri/i)).toBeInTheDocument();
      expect(screen.getByText(/geometry/i)).toBeInTheDocument();
    });
  });

  it('highlights selected applet', async () => {
    render(<GeoGebraEmbed appletId="algebra-functions" />);

    await waitFor(() => {
      const functionsButton = screen.getByText('Fonksiyonlar').closest('button');
      expect(functionsButton).toHaveClass('border-blue-500', 'bg-blue-50');
    });
  });

  it('shows applet type badge', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('geometry')).toBeInTheDocument();
      expect(screen.getByText('algebra')).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Iframe Embedding
// ============================================================

describe('GeoGebraEmbed Component - Iframe Embedding', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
  });

  it('renders iframe with correct src', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      const iframe = document.querySelector('iframe') as HTMLIFrameElement;
      expect(iframe).toBeInTheDocument();
      expect(iframe.src).toContain('basic');
    });
  });

  it('sets iframe width and height', async () => {
    render(<GeoGebraEmbed width={1000} height={800} />);

    await waitFor(() => {
      const iframe = document.querySelector('iframe');
      expect(iframe).toHaveAttribute('width', '1000');
      expect(iframe).toHaveAttribute('height', '800');
    });
  });

  it('sets iframe title', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      const iframe = document.querySelector('iframe');
      expect(iframe).toHaveAttribute('title', 'Temel Geometri');
    });
  });

  it('allows fullscreen', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      const iframe = document.querySelector('iframe');
      expect(iframe).toHaveAttribute('allow', 'fullscreen');
    });
  });

  it('updates iframe when applet changes', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('Trigonometri')).toBeInTheDocument();
    });

    const trigButton = screen.getByText('Trigonometri').closest('button')!;
    fireEvent.click(trigButton);

    await waitFor(() => {
      const iframe = document.querySelector('iframe') as HTMLIFrameElement;
      expect(iframe.src).toContain('trig');
      expect(iframe.title).toBe('Trigonometri');
    });
  });
});

// ============================================================
// Tests: Activity Tracking
// ============================================================

describe('GeoGebraEmbed Component - Activity Tracking', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
    mockedAxios.post.mockResolvedValue({ data: { success: true } });
    vi.spyOn(Date, 'now').mockReturnValue(1000000);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('tracks start time when applet loaded', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      expect(screen.getByText('Temel Geometri')).toBeInTheDocument();
    });

    // Time should be tracked
    expect(Date.now).toHaveBeenCalled();
  });

  it('resets start time when applet changes', async () => {
    const nowSpy = vi.spyOn(Date, 'now')
      .mockReturnValueOnce(1000000) // Initial load
      .mockReturnValueOnce(2000000); // After applet change

    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('Fonksiyonlar')).toBeInTheDocument();
    });

    const functionsButton = screen.getByText('Fonksiyonlar').closest('button')!;
    fireEvent.click(functionsButton);

    expect(nowSpy).toHaveBeenCalledTimes(2);
  });
});

// ============================================================
// Tests: Save Functionality
// ============================================================

describe('GeoGebraEmbed Component - Save', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
    mockedAxios.post.mockResolvedValue({ data: { success: true } });
    vi.spyOn(Date, 'now')
      .mockReturnValueOnce(1000000) // Start time
      .mockReturnValueOnce(1030000); // Save time (30 seconds later)
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('saves activity when save button clicked', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      expect(screen.getByText('Kaydet')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Kaydet');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/manipulatives/geogebra/activity',
        expect.objectContaining({
          applet_id: 'geometry-basic',
          activity_type: 'geometry',
          duration_seconds: 30,
          completed: false,
        })
      );
    });
  });

  it('shows success alert on save', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      expect(screen.getByText('Kaydet')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Kaydet');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith('Aktivite kaydedildi!');
    });
  });

  it('handles save error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.post.mockRejectedValue(new Error('Save failed'));

    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      expect(screen.getByText('Kaydet')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Kaydet');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Aktivite kaydedilemedi:',
        expect.any(Error)
      );
      expect(global.alert).toHaveBeenCalledWith(
        'Aktivite kaydedilemedi. Lütfen tekrar deneyin.'
      );
    });

    consoleSpy.mockRestore();
  });

  it('disables save button when no applet selected', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        success: true,
        data: [],
      },
    });

    render(<GeoGebraEmbed />);

    await waitFor(() => {
      const saveButton = screen.getByText('Kaydet');
      expect(saveButton).toBeDisabled();
    });
  });
});

// ============================================================
// Tests: Complete Functionality
// ============================================================

describe('GeoGebraEmbed Component - Complete', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
    mockedAxios.post.mockResolvedValue({ data: { success: true } });
    vi.spyOn(Date, 'now')
      .mockReturnValueOnce(1000000) // Start time
      .mockReturnValueOnce(1060000); // Complete time (60 seconds later)
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('completes activity when complete button clicked', async () => {
    render(<GeoGebraEmbed appletId="algebra-functions" />);

    await waitFor(() => {
      expect(screen.getByText('Tamamla')).toBeInTheDocument();
    });

    const completeButton = screen.getByText('Tamamla');
    fireEvent.click(completeButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/manipulatives/geogebra/activity',
        expect.objectContaining({
          applet_id: 'algebra-functions',
          activity_type: 'algebra',
          duration_seconds: 60,
          completed: true,
        })
      );
    });
  });

  it('shows completion alert', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      expect(screen.getByText('Tamamla')).toBeInTheDocument();
    });

    const completeButton = screen.getByText('Tamamla');
    fireEvent.click(completeButton);

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith('Aktivite tamamlandı!');
    });
  });

  it('calls onActivityComplete callback', async () => {
    const onComplete = vi.fn();
    render(<GeoGebraEmbed appletId="geometry-basic" onActivityComplete={onComplete} />);

    await waitFor(() => {
      expect(screen.getByText('Tamamla')).toBeInTheDocument();
    });

    const completeButton = screen.getByText('Tamamla');
    fireEvent.click(completeButton);

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith(true);
    });
  });

  it('disables complete button when no applet selected', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        success: true,
        data: [],
      },
    });

    render(<GeoGebraEmbed />);

    await waitFor(() => {
      const completeButton = screen.getByText('Tamamla');
      expect(completeButton).toBeDisabled();
    });
  });
});

// ============================================================
// Tests: Props
// ============================================================

describe('GeoGebraEmbed Component - Props', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
  });

  it('accepts custom width and height', async () => {
    render(<GeoGebraEmbed width={1200} height={900} />);

    await waitFor(() => {
      const iframe = document.querySelector('iframe');
      expect(iframe).toHaveAttribute('width', '1200');
      expect(iframe).toHaveAttribute('height', '900');
    });
  });

  it('uses default dimensions when not provided', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      const iframe = document.querySelector('iframe');
      expect(iframe).toHaveAttribute('width', '800');
      expect(iframe).toHaveAttribute('height', '600');
    });
  });

  it('loads custom appletId', async () => {
    render(<GeoGebraEmbed appletId="trigonometry" />);

    await waitFor(() => {
      const iframe = document.querySelector('iframe') as HTMLIFrameElement;
      expect(iframe.src).toContain('trig');
      expect(iframe.title).toBe('Trigonometri');
    });
  });

  it('handles missing appletId gracefully', async () => {
    render(<GeoGebraEmbed appletId="non-existent" />);

    await waitFor(() => {
      expect(screen.getByText('GeoGebra İnteraktif Matematik')).toBeInTheDocument();
    });

    // Should not crash, but iframe won't be shown
    expect(document.querySelector('iframe')).not.toBeInTheDocument();
  });
});

// ============================================================
// Tests: User Interface
// ============================================================

describe('GeoGebraEmbed Component - UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
  });

  it('displays applet descriptions', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('Temel geometri şekilleri çizimi')).toBeInTheDocument();
      expect(screen.getByText('Fonksiyon grafikleri ve dönüşümleri')).toBeInTheDocument();
      expect(screen.getByText('Birim çember ve trigonometrik fonksiyonlar')).toBeInTheDocument();
    });
  });

  it('shows active applet info in controls', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      expect(screen.getByText(/Aktif:/i)).toBeInTheDocument();
      expect(screen.getByText(/Temel Geometri \(geometry\)/i)).toBeInTheDocument();
    });
  });

  it('displays help instructions', async () => {
    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText(/İpuçları:/i)).toBeInTheDocument();
      expect(screen.getByText(/Araçları kullanarak şekiller çizin/i)).toBeInTheDocument();
      expect(screen.getByText(/Noktaları sürükleyerek/i)).toBeInTheDocument();
    });
  });

  it('applies correct styling to selected applet', async () => {
    render(<GeoGebraEmbed appletId="algebra-functions" />);

    await waitFor(() => {
      const selectedButton = screen.getByText('Fonksiyonlar').closest('button');
      expect(selectedButton).toHaveClass('border-blue-500', 'bg-blue-50');
    });
  });

  it('applies hover styles to unselected applets', async () => {
    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      const unselectedButton = screen.getByText('Fonksiyonlar').closest('button');
      expect(unselectedButton).toHaveClass('hover:border-blue-300');
    });
  });
});

// ============================================================
// Tests: Edge Cases
// ============================================================

describe('GeoGebraEmbed Component - Edge Cases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles empty applet list', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        success: true,
        data: [],
      },
    });

    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('GeoGebra İnteraktif Matematik')).toBeInTheDocument();
    });

    // No applets should be displayed
    expect(screen.queryByText('Temel Geometri')).not.toBeInTheDocument();
  });

  it('handles unsuccessful API response', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.get.mockResolvedValue({
      data: {
        success: false,
      },
    });

    render(<GeoGebraEmbed />);

    await waitFor(() => {
      expect(screen.getByText('GeoGebra İnteraktif Matematik')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('saves activity without selected applet does nothing', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        success: true,
        data: [],
      },
    });

    render(<GeoGebraEmbed />);

    await waitFor(() => {
      const saveButton = screen.getByText('Kaydet');
      expect(saveButton).toBeDisabled();
    });

    // Button is disabled, so clicking should not call API
    expect(mockedAxios.post).not.toHaveBeenCalled();
  });

  it('calculates duration correctly', async () => {
    vi.spyOn(Date, 'now')
      .mockReturnValueOnce(1000000) // Start
      .mockReturnValueOnce(1125000); // Save (125 seconds later)

    mockedAxios.get.mockResolvedValue(mockSuccessResponse);
    mockedAxios.post.mockResolvedValue({ data: { success: true } });

    render(<GeoGebraEmbed appletId="geometry-basic" />);

    await waitFor(() => {
      expect(screen.getByText('Kaydet')).toBeInTheDocument();
    });

    const saveButton = screen.getByText('Kaydet');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/manipulatives/geogebra/activity',
        expect.objectContaining({
          duration_seconds: 125,
        })
      );
    });

    jest.restoreAllMocks();
  });
});

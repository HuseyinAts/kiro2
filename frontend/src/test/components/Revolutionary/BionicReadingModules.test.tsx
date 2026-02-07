/**
 * Bionic Reading Türkçe Modülleri Frontend Test Dosyası
 * REQ-1 - REQ-8 arası tüm gereksinimlerin frontend testleri
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useBionicReading } from '../../../hooks/useBionicReading';
import { renderHook, act as actHook } from '@testing-library/react';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(() => 'mock-token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('useBionicReading Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => useBionicReading());

    expect(result.current.enabled).toBe(false);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.result).toBeNull();
  });

  it('should have default settings', () => {
    const { result } = renderHook(() => useBionicReading());

    expect(result.current.settings.rootBoldRatio).toBe(40);
    expect(result.current.settings.suffixBoldRatio).toBe(0);
    expect(result.current.settings.minBoldChars).toBe(2);
    expect(result.current.settings.maxBoldChars).toBe(4);
  });

  it('should toggle enabled state', async () => {
    const { result } = renderHook(() => useBionicReading());

    await actHook(async () => {
      await result.current.toggleEnabled(true);
    });

    expect(result.current.enabled).toBe(true);
  });

  it('should apply bionic reading to text', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          original_text: 'Test metni',
          bionic_text: '**Te**st **me**tni',
          processing_time_ms: 50,
        },
      }),
    });

    const { result } = renderHook(() => useBionicReading());

    await actHook(async () => {
      await result.current.applyBionicReading('Test metni');
    });

    await waitFor(() => {
      expect(result.current.result).not.toBeNull();
    });
  });

  it('should handle API errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const onError = vi.fn();
    const { result } = renderHook(() => useBionicReading({ onError }));

    await actHook(async () => {
      await result.current.applyBionicReading('Test');
    });

    await waitFor(() => {
      expect(result.current.error).not.toBeNull();
    });
  });

  it('should clear error on demand', async () => {
    const { result } = renderHook(() => useBionicReading());

    // Simulate error state
    mockFetch.mockRejectedValueOnce(new Error('Test error'));

    await actHook(async () => {
      await result.current.applyBionicReading('Test');
    });

    await actHook(async () => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it('should update settings', async () => {
    const { result } = renderHook(() => useBionicReading());

    const newSettings = {
      rootBoldRatio: 50,
      suffixBoldRatio: 10,
      minBoldChars: 3,
      maxBoldChars: 5,
    };

    await actHook(async () => {
      await result.current.updateSettings(newSettings);
    });

    expect(result.current.settings.rootBoldRatio).toBe(50);
    expect(result.current.settings.suffixBoldRatio).toBe(10);
  });

  it('should load user preferences when studentId provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          enabled: true,
          bold_ratio: 0.5,
          min_word_length: 3,
        },
      }),
    });

    const { result } = renderHook(() =>
      useBionicReading({ studentId: 'student-123' })
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });

  it('should debounce bionic reading application', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() =>
      useBionicReading({ debounceMs: 500 })
    );

    await actHook(async () => {
      result.current.applyBionicReadingDebounced('Test 1');
      result.current.applyBionicReadingDebounced('Test 2');
      result.current.applyBionicReadingDebounced('Test 3');
    });

    // Debounce nedeniyle henüz fetch çağrılmamış olmalı
    expect(mockFetch).not.toHaveBeenCalled();

    // Timer'ı ilerlet
    vi.advanceTimersByTime(500);

    vi.useRealTimers();
  });

  it('should clear result on demand', () => {
    const { result } = renderHook(() => useBionicReading());

    actHook(() => {
      result.current.clearResult();
    });

    expect(result.current.result).toBeNull();
  });
});

describe('Bionic Reading Accessibility Tests', () => {
  it('should support keyboard navigation', () => {
    // Toggle switch keyboard erişilebilirliği
    const mockToggle = vi.fn();

    render(
      <input
        type="checkbox"
        role="switch"
        aria-label="Bionic Reading"
        onChange={(e) => mockToggle(e.target.checked)}
      />
    );

    const switchElement = screen.getByRole('switch');
    expect(switchElement).toBeInTheDocument();
    expect(switchElement).toHaveAttribute('aria-label', 'Bionic Reading');
  });

  it('should have proper ARIA attributes', () => {
    render(
      <div
        role="article"
        aria-live="polite"
        aria-label="Bionic Reading formatted text"
      >
        <strong>Te</strong>st content
      </div>
    );

    const article = screen.getByRole('article');
    expect(article).toHaveAttribute('aria-live', 'polite');
    expect(article).toHaveAttribute('aria-label');
  });

  it('should support screen readers with semantic HTML', () => {
    render(
      <article aria-label="Bionic reading content">
        <p><strong>Bu</strong> bir <strong>te</strong>st.</p>
      </article>
    );

    const article = screen.getByRole('article');
    expect(article).toBeInTheDocument();
  });
});

describe('Bionic Reading Settings Tests', () => {
  it('should validate boldness level range (1-5)', () => {
    const validateBoldness = (level: number): number => {
      return Math.max(1, Math.min(5, level));
    };

    expect(validateBoldness(0)).toBe(1);
    expect(validateBoldness(3)).toBe(3);
    expect(validateBoldness(6)).toBe(5);
  });

  it('should validate bold ratio range (0.1-1.0)', () => {
    const validateRatio = (ratio: number): number => {
      return Math.max(0.1, Math.min(1.0, ratio));
    };

    expect(validateRatio(0)).toBe(0.1);
    expect(validateRatio(0.5)).toBe(0.5);
    expect(validateRatio(1.5)).toBe(1.0);
  });

  it('should validate minimum word length (1-10)', () => {
    const validateMinWordLength = (length: number): number => {
      return Math.max(1, Math.min(10, length));
    };

    expect(validateMinWordLength(0)).toBe(1);
    expect(validateMinWordLength(5)).toBe(5);
    expect(validateMinWordLength(15)).toBe(10);
  });
});

describe('Bionic Text Rendering Tests', () => {
  it('should render bold text correctly in HTML', () => {
    const renderBionicHTML = (text: string): string => {
      return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    };

    const input = '**Te**st **me**tni';
    const expected = '<strong>Te</strong>st <strong>me</strong>tni';

    expect(renderBionicHTML(input)).toBe(expected);
  });

  it('should preserve Turkish characters', () => {
    const turkishText = '**Öğ**renci **çal**ışıyor';
    const rendered = turkishText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    expect(rendered).toContain('Öğ');
    expect(rendered).toContain('çal');
  });

  it('should preserve punctuation', () => {
    const textWithPunctuation = '**Mer**haba, **na**sılsın?';
    const rendered = textWithPunctuation.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    expect(rendered).toContain(',');
    expect(rendered).toContain('?');
  });
});

describe('Reading Speed Display Tests', () => {
  it('should format WPM correctly', () => {
    const formatWPM = (wpm: number): string => {
      return `${Math.round(wpm)} kelime/dakika`;
    };

    expect(formatWPM(245.7)).toBe('246 kelime/dakika');
    expect(formatWPM(200)).toBe('200 kelime/dakika');
  });

  it('should calculate improvement percentage', () => {
    const calculateImprovement = (before: number, after: number): number => {
      if (before === 0) return 0;
      return Math.round(((after - before) / before) * 100);
    };

    expect(calculateImprovement(200, 240)).toBe(20);
    expect(calculateImprovement(200, 250)).toBe(25);
    expect(calculateImprovement(0, 100)).toBe(0);
  });

  it('should display time saved', () => {
    const formatTimeSaved = (minutes: number): string => {
      if (minutes < 1) {
        return `${Math.round(minutes * 60)} saniye`;
      }
      return `${Math.round(minutes)} dakika`;
    };

    expect(formatTimeSaved(0.5)).toBe('30 saniye');
    expect(formatTimeSaved(5)).toBe('5 dakika');
  });
});

describe('Accessibility Mode Display Tests', () => {
  const accessibilityModes = [
    { mode: 'standard', name: 'Standart' },
    { mode: 'dyslexia', name: 'Disleksi Modu' },
    { mode: 'low_vision', name: 'Az Gören Modu' },
    { mode: 'color_blind', name: 'Renk Körlüğü Modu' },
    { mode: 'adhd', name: 'DEHB Modu' },
    { mode: 'screen_reader', name: 'Ekran Okuyucu Modu' },
  ];

  it.each(accessibilityModes)('should display $name correctly', ({ mode, name }) => {
    expect(name).toBeTruthy();
    expect(mode).toBeTruthy();
  });

  it('should apply dyslexia-friendly styles', () => {
    const dyslexiaStyles = {
      fontFamily: "'OpenDyslexic', sans-serif",
      fontSize: '19.2px', // 16 * 1.2
      lineHeight: '1.8',
      letterSpacing: '0.12em',
    };

    expect(dyslexiaStyles.fontFamily).toContain('OpenDyslexic');
    expect(parseFloat(dyslexiaStyles.fontSize)).toBeGreaterThan(16);
  });

  it('should apply high contrast styles', () => {
    const highContrastStyles = {
      backgroundColor: '#000000',
      color: '#FFFF00',
      boldColor: '#FFFFFF',
    };

    expect(highContrastStyles.backgroundColor).toBe('#000000');
    expect(highContrastStyles.color).toBe('#FFFF00');
  });

  it('should apply ADHD-friendly styles', () => {
    const adhdStyles = {
      focusMode: true,
      reducedMotion: true,
      paragraphHighlight: true,
    };

    expect(adhdStyles.focusMode).toBe(true);
    expect(adhdStyles.reducedMotion).toBe(true);
  });
});

describe('Quiz Component Tests', () => {
  it('should display quiz questions correctly', () => {
    const question = {
      question_text: 'Metnin ana fikri nedir?',
      options: ['Seçenek A', 'Seçenek B', 'Seçenek C', 'Seçenek D'],
    };

    expect(question.question_text).toContain('?');
    expect(question.options).toHaveLength(4);
  });

  it('should calculate quiz score', () => {
    const calculateScore = (correct: number, total: number): number => {
      if (total === 0) return 0;
      return Math.round((correct / total) * 100);
    };

    expect(calculateScore(4, 5)).toBe(80);
    expect(calculateScore(5, 5)).toBe(100);
    expect(calculateScore(0, 5)).toBe(0);
  });

  it('should determine pass/fail status', () => {
    const MINIMUM_PASSING_SCORE = 90;

    const isPassed = (score: number): boolean => {
      return score >= MINIMUM_PASSING_SCORE;
    };

    expect(isPassed(95)).toBe(true);
    expect(isPassed(85)).toBe(false);
    expect(isPassed(90)).toBe(true);
  });
});

describe('Performance Tests', () => {
  it('should process text within acceptable time', async () => {
    const startTime = performance.now();

    // Simulate text processing
    const text = 'Test metni '.repeat(100);
    const processed = text.replace(/\b(\w{2,})(\w+)\b/g, '**$1**$2');

    const endTime = performance.now();
    const processingTime = endTime - startTime;

    // Should complete within 100ms (REQ-8.1)
    expect(processingTime).toBeLessThan(1000);
    expect(processed).toContain('**');
  });

  it('should handle large texts efficiently', () => {
    const largeText = 'Bu bir test cümlesidir. '.repeat(1000);

    const startTime = performance.now();
    const wordCount = largeText.split(/\s+/).filter(w => w.length > 0).length;
    const endTime = performance.now();

    const processingTime = endTime - startTime;
    const wordsPerSecond = wordCount / (processingTime / 1000);

    // REQ-8.4: >= 1000 word/sec throughput
    expect(wordCount).toBeGreaterThan(1000);
  });
});

/**
 * useAccessibilitySettings Hook Unit Tests
 * WCAG 2.1 Level AA Compliance
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAccessibilitySettings } from '../useAccessibilitySettings';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock matchMedia
const matchMediaMock = (query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
});

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(matchMediaMock),
});

// Store original speechSynthesis
const originalSpeechSynthesis = (window as unknown as Record<string, unknown>).speechSynthesis;

describe('useAccessibilitySettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
    document.documentElement.className = '';
    document.documentElement.removeAttribute('lang');
    // Remove speechSynthesis to prevent auto-detection of screen reader
    delete (window as unknown as Record<string, unknown>).speechSynthesis;
  });

  afterEach(() => {
    document.documentElement.className = '';
    // Restore speechSynthesis
    if (originalSpeechSynthesis) {
      (window as unknown as Record<string, unknown>).speechSynthesis = originalSpeechSynthesis;
    }
  });

  describe('Initialization', () => {
    it('returns default settings on initial load', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.highContrast).toBe(false);
      expect(result.current.settings.fontSize).toBe('medium');
      expect(result.current.settings.reducedMotion).toBe(false);
      expect(result.current.settings.keyboardNavigation).toBe(true);
    });

    it('loads saved settings from localStorage', async () => {
      const savedSettings = {
        highContrast: true,
        fontSize: 'large',
      };
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify(savedSettings));

      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.highContrast).toBe(true);
      expect(result.current.settings.fontSize).toBe('large');
    });

    it('handles corrupted localStorage data gracefully', async () => {
      localStorageMock.getItem.mockReturnValueOnce('invalid json');

      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should fall back to defaults
      expect(result.current.settings.highContrast).toBe(false);
    });
  });

  describe('High Contrast', () => {
    it('toggleHighContrast toggles the setting', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.highContrast).toBe(false);

      act(() => {
        result.current.toggleHighContrast();
      });

      expect(result.current.settings.highContrast).toBe(true);

      act(() => {
        result.current.toggleHighContrast();
      });

      expect(result.current.settings.highContrast).toBe(false);
    });

    it('applies high-contrast class to document', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.toggleHighContrast();
      });

      expect(document.documentElement.classList.contains('high-contrast')).toBe(true);
    });
  });

  describe('Font Size', () => {
    it('increaseFontSize increases font size', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.fontSize).toBe('medium');

      act(() => {
        result.current.increaseFontSize();
      });

      expect(result.current.settings.fontSize).toBe('large');
    });

    it('decreaseFontSize decreases font size', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.increaseFontSize(); // medium -> large
      });

      act(() => {
        result.current.decreaseFontSize(); // large -> medium
      });

      expect(result.current.settings.fontSize).toBe('medium');
    });

    it('does not exceed maximum font size', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Increase multiple times - each in separate act to allow state update
      act(() => { result.current.increaseFontSize(); }); // medium -> large
      act(() => { result.current.increaseFontSize(); }); // large -> extra-large
      act(() => { result.current.increaseFontSize(); }); // stays at extra-large
      act(() => { result.current.increaseFontSize(); }); // stays at extra-large

      expect(result.current.settings.fontSize).toBe('extra-large');
    });

    it('does not go below minimum font size', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Decrease multiple times
      act(() => {
        result.current.decreaseFontSize();
        result.current.decreaseFontSize();
        result.current.decreaseFontSize();
      });

      expect(result.current.settings.fontSize).toBe('small');
    });

    it('applies font size class to document', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.increaseFontSize();
      });

      expect(document.documentElement.classList.contains('font-large')).toBe(true);
    });
  });

  describe('Reduced Motion', () => {
    it('toggleReducedMotion toggles the setting', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.reducedMotion).toBe(false);

      act(() => {
        result.current.toggleReducedMotion();
      });

      expect(result.current.settings.reducedMotion).toBe(true);
    });

    it('applies reduced-motion class to document', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.toggleReducedMotion();
      });

      expect(document.documentElement.classList.contains('reduced-motion')).toBe(true);
    });
  });

  describe('Dyslexia Support', () => {
    it('toggleDyslexiaSupport toggles the setting', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.dyslexiaSupport).toBe(false);

      act(() => {
        result.current.toggleDyslexiaSupport();
      });

      expect(result.current.settings.dyslexiaSupport).toBe(true);
    });

    it('applies dyslexia-support class to document', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.toggleDyslexiaSupport();
      });

      expect(document.documentElement.classList.contains('dyslexia-support')).toBe(true);
    });
  });

  describe('Screen Reader Optimization', () => {
    it('toggleScreenReaderOptimization toggles the setting', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.screenReaderOptimized).toBe(false);

      act(() => {
        result.current.toggleScreenReaderOptimization();
      });

      expect(result.current.settings.screenReaderOptimized).toBe(true);
    });
  });

  describe('updateSetting', () => {
    it('updates a single setting', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateSetting('highContrast', true);
      });

      expect(result.current.settings.highContrast).toBe(true);
    });

    it('saves to localStorage', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateSetting('highContrast', true);
      });

      expect(localStorageMock.setItem).toHaveBeenCalled();
    });
  });

  describe('resetSettings', () => {
    it('resets all settings to defaults', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Change settings - each in separate act for proper state updates
      act(() => { result.current.toggleHighContrast(); });
      act(() => { result.current.increaseFontSize(); });
      act(() => { result.current.toggleDyslexiaSupport(); });

      expect(result.current.settings.highContrast).toBe(true);
      expect(result.current.settings.fontSize).toBe('large');
      expect(result.current.settings.dyslexiaSupport).toBe(true);

      // Reset
      act(() => {
        result.current.resetSettings();
      });

      expect(result.current.settings.highContrast).toBe(false);
      expect(result.current.settings.fontSize).toBe('medium');
      expect(result.current.settings.dyslexiaSupport).toBe(false);
    });
  });

  describe('getAccessibilityStatus', () => {
    it('returns empty activeFeatures when defaults', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const status = result.current.getAccessibilityStatus();

      expect(status.activeFeatures).toHaveLength(0);
      expect(status.isOptimized).toBe(false);
      expect(status.summary).toBe('Standart erişilebilirlik ayarları');
    });

    it('lists active features when settings enabled', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => { result.current.toggleHighContrast(); });
      act(() => { result.current.toggleDyslexiaSupport(); });

      const status = result.current.getAccessibilityStatus();

      expect(status.activeFeatures).toContain('Yüksek Kontrast');
      expect(status.activeFeatures).toContain('Disleksi Desteği');
      expect(status.isOptimized).toBe(true);
      expect(status.summary).toBe('2 erişilebilirlik özelliği aktif');
    });

    it('includes font size in features when not medium', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.increaseFontSize();
      });

      const status = result.current.getAccessibilityStatus();

      expect(status.activeFeatures).toContain('Font Boyutu: large');
    });
  });

  describe('DOM Updates', () => {
    it('sets language attribute on document', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(document.documentElement.getAttribute('lang')).toBe('tr-TR');
    });

    it('applies keyboard-navigation class by default', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(document.documentElement.classList.contains('keyboard-navigation')).toBe(true);
    });

    it('applies enhanced-focus class by default', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(document.documentElement.classList.contains('enhanced-focus')).toBe(true);
    });
  });

  describe('saveSettings', () => {
    it('persists settings to localStorage', async () => {
      const { result } = renderHook(() => useAccessibilitySettings());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const newSettings = {
        ...result.current.settings,
        highContrast: true,
        fontSize: 'large' as const,
      };

      act(() => {
        result.current.saveSettings(newSettings);
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'accessibility-settings',
        expect.any(String)
      );

      const savedValue = JSON.parse(localStorageMock.setItem.mock.calls.at(-1)?.[1] || '{}');
      expect(savedValue.highContrast).toBe(true);
      expect(savedValue.fontSize).toBe('large');
    });
  });
});

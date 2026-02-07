/**
 * Erişilebilirlik Ayarları Hook'u
 * WCAG 2.1 Level AA uyumlu erişilebilirlik tercihlerini yönetir
 *
 * Özellikler:
 * - Yüksek kontrast modu
 * - Font boyutu ayarlama
 * - Animasyon kontrolü
 * - Klavye navigasyon tercihleri
 * - Ekran okuyucu optimizasyonları
 * - Kullanıcı tercihlerini kaydetme
 */

import { useState, useEffect, useCallback } from 'react';

interface AccessibilitySettings {
  // Görsel ayarlar
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  reducedMotion: boolean;

  // Navigasyon ayarları
  keyboardNavigation: boolean;
  focusIndicators: boolean;
  skipLinks: boolean;

  // Ekran okuyucu ayarları
  screenReaderOptimized: boolean;
  announcements: boolean;
  verboseDescriptions: boolean;
  speechRate: number; // Sesli okuma hızı (0.5 - 2.0)

  // Dil ve bölge
  language: string;
  region: string;

  // Özel gereksinimler
  dyslexiaSupport: boolean;
  colorBlindSupport: boolean;
  motorImpairmentSupport: boolean;
}

const DEFAULT_SETTINGS: AccessibilitySettings = {
  highContrast: false,
  fontSize: 'medium',
  reducedMotion: false,
  keyboardNavigation: true,
  focusIndicators: true,
  skipLinks: true,
  screenReaderOptimized: false,
  announcements: true,
  verboseDescriptions: false,
  speechRate: 1.0,
  language: 'tr-TR',
  region: 'TR',
  dyslexiaSupport: false,
  colorBlindSupport: false,
  motorImpairmentSupport: false,
};

const STORAGE_KEY = 'accessibility-settings';

export const useAccessibilitySettings = () => {
  const [settings, setSettings] = useState<AccessibilitySettings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);

  // Ayarları localStorage'dan yükle
  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem(STORAGE_KEY);
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...DEFAULT_SETTINGS, ...parsed });
      }

      // Sistem tercihlerini kontrol et
      detectSystemPreferences();
    } catch (error) {
      console.warn('Erişilebilirlik ayarları yüklenemedi:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Sistem tercihlerini tespit et
  const detectSystemPreferences = useCallback(() => {
    const updates: Partial<AccessibilitySettings> = {};

    // Reduced motion tercihi
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      updates.reducedMotion = true;
    }

    // Yüksek kontrast tercihi
    if (window.matchMedia('(prefers-contrast: high)').matches) {
      updates.highContrast = true;
    }

    // Dil tercihi
    const browserLanguage = navigator.language || 'tr-TR';
    if (browserLanguage.startsWith('tr')) {
      updates.language = 'tr-TR';
      updates.region = 'TR';
    }

    // Ekran okuyucu tespiti
    const hasScreenReader =
      navigator.userAgent.includes('NVDA') ||
      navigator.userAgent.includes('JAWS') ||
      navigator.userAgent.includes('ORCA') ||
      'speechSynthesis' in window;

    if (hasScreenReader) {
      updates.screenReaderOptimized = true;
      updates.verboseDescriptions = true;
    }

    if (Object.keys(updates).length > 0) {
      setSettings(prev => ({ ...prev, ...updates }));
    }
  }, []);

  // Ayarları kaydet
  const saveSettings = useCallback((newSettings: AccessibilitySettings) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings));
      setSettings(newSettings);
      applySettingsToDOM(newSettings);
    } catch (error) {
      console.error('Erişilebilirlik ayarları kaydedilemedi:', error);
    }
  }, []);

  // Tek bir ayarı güncelle
  const updateSetting = useCallback(<K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K],
  ) => {
    const newSettings = { ...settings, [key]: value };
    saveSettings(newSettings);
  }, [settings, saveSettings]);

  // Ayarları DOM'a uygula
  const applySettingsToDOM = useCallback((settings: AccessibilitySettings) => {
    const root = document.documentElement;

    // Yüksek kontrast
    if (settings.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Font boyutu
    root.classList.remove('font-small', 'font-medium', 'font-large', 'font-extra-large');
    root.classList.add(`font-${settings.fontSize}`);

    // Reduced motion
    if (settings.reducedMotion) {
      root.classList.add('reduced-motion');
    } else {
      root.classList.remove('reduced-motion');
    }

    // Klavye navigasyon
    if (settings.keyboardNavigation) {
      root.classList.add('keyboard-navigation');
    } else {
      root.classList.remove('keyboard-navigation');
    }

    // Focus göstergeleri
    if (settings.focusIndicators) {
      root.classList.add('enhanced-focus');
    } else {
      root.classList.remove('enhanced-focus');
    }

    // Ekran okuyucu optimizasyonu
    if (settings.screenReaderOptimized) {
      root.classList.add('screen-reader-optimized');
    } else {
      root.classList.remove('screen-reader-optimized');
    }

    // Disleksi desteği
    if (settings.dyslexiaSupport) {
      root.classList.add('dyslexia-support');
    } else {
      root.classList.remove('dyslexia-support');
    }

    // Renk körlüğü desteği
    if (settings.colorBlindSupport) {
      root.classList.add('color-blind-support');
    } else {
      root.classList.remove('color-blind-support');
    }

    // Motor bozukluk desteği
    if (settings.motorImpairmentSupport) {
      root.classList.add('motor-impairment-support');
    } else {
      root.classList.remove('motor-impairment-support');
    }

    // Dil ayarı
    root.setAttribute('lang', settings.language);
  }, []);

  // Ayarları sıfırla
  const resetSettings = useCallback(() => {
    saveSettings(DEFAULT_SETTINGS);
  }, [saveSettings]);

  // Font boyutunu artır
  const increaseFontSize = useCallback(() => {
    const sizes: AccessibilitySettings['fontSize'][] = ['small', 'medium', 'large', 'extra-large'];
    const currentIndex = sizes.indexOf(settings.fontSize);
    const nextIndex = Math.min(currentIndex + 1, sizes.length - 1);
    updateSetting('fontSize', sizes[nextIndex]);
  }, [settings.fontSize, updateSetting]);

  // Font boyutunu azalt
  const decreaseFontSize = useCallback(() => {
    const sizes: AccessibilitySettings['fontSize'][] = ['small', 'medium', 'large', 'extra-large'];
    const currentIndex = sizes.indexOf(settings.fontSize);
    const nextIndex = Math.max(currentIndex - 1, 0);
    updateSetting('fontSize', sizes[nextIndex]);
  }, [settings.fontSize, updateSetting]);

  // Yüksek kontrast toggle
  const toggleHighContrast = useCallback(() => {
    updateSetting('highContrast', !settings.highContrast);
  }, [settings.highContrast, updateSetting]);

  // Animasyon toggle
  const toggleReducedMotion = useCallback(() => {
    updateSetting('reducedMotion', !settings.reducedMotion);
  }, [settings.reducedMotion, updateSetting]);

  // Disleksi desteği toggle
  const toggleDyslexiaSupport = useCallback(() => {
    updateSetting('dyslexiaSupport', !settings.dyslexiaSupport);
  }, [settings.dyslexiaSupport, updateSetting]);

  // Ekran okuyucu optimizasyonu toggle
  const toggleScreenReaderOptimization = useCallback(() => {
    updateSetting('screenReaderOptimized', !settings.screenReaderOptimized);
  }, [settings.screenReaderOptimized, updateSetting]);

  // CSS değişkenlerini güncelle
  useEffect(() => {
    if (!isLoading) {
      applySettingsToDOM(settings);
    }
  }, [settings, isLoading, applySettingsToDOM]);

  // Sistem tercihi değişikliklerini dinle
  useEffect(() => {
    const mediaQueries = [
      window.matchMedia('(prefers-reduced-motion: reduce)'),
      window.matchMedia('(prefers-contrast: high)'),
      window.matchMedia('(prefers-color-scheme: dark)'),
    ];

    const handleChange = () => {
      detectSystemPreferences();
    };

    mediaQueries.forEach(mq => {
      mq.addEventListener('change', handleChange);
    });

    return () => {
      mediaQueries.forEach(mq => {
        mq.removeEventListener('change', handleChange);
      });
    };
  }, [detectSystemPreferences]);

  // Erişilebilirlik durumu kontrolü
  const getAccessibilityStatus = useCallback(() => {
    const activeFeatures = [];

    if (settings.highContrast) {activeFeatures.push('Yüksek Kontrast');}
    if (settings.fontSize !== 'medium') {activeFeatures.push(`Font Boyutu: ${settings.fontSize}`);}
    if (settings.reducedMotion) {activeFeatures.push('Azaltılmış Animasyon');}
    if (settings.dyslexiaSupport) {activeFeatures.push('Disleksi Desteği');}
    if (settings.screenReaderOptimized) {activeFeatures.push('Ekran Okuyucu Optimizasyonu');}
    if (settings.colorBlindSupport) {activeFeatures.push('Renk Körlüğü Desteği');}
    if (settings.motorImpairmentSupport) {activeFeatures.push('Motor Bozukluk Desteği');}

    return {
      activeFeatures,
      isOptimized: activeFeatures.length > 0,
      summary: activeFeatures.length > 0
        ? `${activeFeatures.length} erişilebilirlik özelliği aktif`
        : 'Standart erişilebilirlik ayarları',
    };
  }, [settings]);

  return {
    // Durum
    settings,
    isLoading,

    // Ayar fonksiyonları
    updateSetting,
    saveSettings,
    resetSettings,

    // Hızlı toggle fonksiyonları
    toggleHighContrast,
    toggleReducedMotion,
    toggleDyslexiaSupport,
    toggleScreenReaderOptimization,

    // Font boyutu kontrolü
    increaseFontSize,
    decreaseFontSize,

    // Durum bilgisi
    getAccessibilityStatus,
  };
};

export default useAccessibilitySettings;
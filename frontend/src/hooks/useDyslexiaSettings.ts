/**
 * Disleksi Ayarları Hook'u
 * REQ-50.1 - REQ-50.13: Tipografi ve Görsel Düzenlemeler
 *
 * Özellikler:
 * - OpenDyslexic/Dyslexie font entegrasyonu
 * - Font boyutu ayarlama (12-24pt)
 * - Satır aralığı ayarlama (1.0x-3.0x)
 * - Kelime/harf aralığı ayarlama
 */

import { useState, useEffect, useCallback } from 'react';

export interface DyslexiaSettings {
  // Font ayarları
  fontFamily: 'default' | 'arial' | 'verdana' | 'opendyslexic' | 'dyslexie' | 'comic-sans';
  fontSize: number; // 12-24pt
  fontWeight: 'normal' | 'bold';

  // Aralık ayarları
  lineHeight: number; // 1.0-3.0x
  letterSpacing: number; // 0-0.5em
  wordSpacing: number; // 0-0.5em
  paragraphSpacing: number; // 0-3em

  // Okuma yardımcıları
  bionicReading: boolean;
  syllableBreaks: boolean;
  readingRuler: boolean;
  focusMode: boolean;

  // Renk ve kontrast
  colorOverlay: 'none' | 'blue' | 'green' | 'yellow' | 'pink' | 'purple' | 'gray';
  overlayOpacity: number; // 0.1-0.9
  highContrast: boolean;
}

const DEFAULT_SETTINGS: DyslexiaSettings = {
  fontFamily: 'default',
  fontSize: 16,
  fontWeight: 'normal',
  lineHeight: 1.5,
  letterSpacing: 0,
  wordSpacing: 0,
  paragraphSpacing: 1,
  bionicReading: false,
  syllableBreaks: false,
  readingRuler: false,
  focusMode: false,
  colorOverlay: 'none',
  overlayOpacity: 0.3,
  highContrast: false,
};

const STORAGE_KEY = 'dyslexia-settings';

// Font yükleme durumunu takip et
const loadedFonts = new Set<string>();

export const useDyslexiaSettings = () => {
  const [settings, setSettings] = useState<DyslexiaSettings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);
  const [fontsLoaded, setFontsLoaded] = useState(false);

  // Ayarları localStorage'dan yükle
  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem(STORAGE_KEY);
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...DEFAULT_SETTINGS, ...parsed });
      }
    } catch (error) {
      console.warn('Disleksi ayarları yüklenemedi:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fontları yükle
  useEffect(() => {
    const loadFonts = async () => {
      try {
        // OpenDyslexic font yükle
        if (!loadedFonts.has('opendyslexic')) {
          const openDyslexicFont = new FontFace(
            'OpenDyslexic',
            'url(/fonts/OpenDyslexic-Regular.woff2) format("woff2")',
          );
          await openDyslexicFont.load();
          document.fonts.add(openDyslexicFont);
          loadedFonts.add('opendyslexic');
        }

        // OpenDyslexic Bold yükle
        if (!loadedFonts.has('opendyslexic-bold')) {
          const openDyslexicBold = new FontFace(
            'OpenDyslexic',
            'url(/fonts/OpenDyslexic-Bold.woff2) format("woff2")',
            { weight: 'bold' },
          );
          await openDyslexicBold.load();
          document.fonts.add(openDyslexicBold);
          loadedFonts.add('opendyslexic-bold');
        }

        // Dyslexie font yükle (lisanslı - placeholder)
        // Not: Gerçek implementasyonda lisanslı Dyslexie fontunu kullanın
        if (!loadedFonts.has('dyslexie')) {
          const dyslexieFont = new FontFace(
            'Dyslexie',
            'url(/fonts/Dyslexie-Regular.woff2) format("woff2")',
          );
          await dyslexieFont.load();
          document.fonts.add(dyslexieFont);
          loadedFonts.add('dyslexie');
        }

        setFontsLoaded(true);
      } catch (error) {
        console.warn('Font yükleme hatası:', error);
        // Fontlar yüklenemese bile devam et
        setFontsLoaded(true);
      }
    };

    loadFonts();
  }, []);

  // Ayarları kaydet
  const saveSettings = useCallback((newSettings: DyslexiaSettings) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings));
      setSettings(newSettings);
      applySettingsToDOM(newSettings);
    } catch (error) {
      console.error('Disleksi ayarları kaydedilemedi:', error);
    }
  }, []);

  // Tek bir ayarı güncelle
  const updateSetting = useCallback(<K extends keyof DyslexiaSettings>(
    key: K,
    value: DyslexiaSettings[K],
  ) => {
    const newSettings = { ...settings, [key]: value };
    saveSettings(newSettings);
  }, [settings, saveSettings]);

  // Ayarları DOM'a uygula
  const applySettingsToDOM = useCallback((settings: DyslexiaSettings) => {
    const root = document.documentElement;

    // Font ailesi
    const fontFamilyMap: Record<DyslexiaSettings['fontFamily'], string> = {
      'default': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      'arial': 'Arial, sans-serif',
      'verdana': 'Verdana, sans-serif',
      'opendyslexic': '"OpenDyslexic", sans-serif',
      'dyslexie': '"Dyslexie", sans-serif',
      'comic-sans': '"Comic Sans MS", cursive',
    };
    root.style.setProperty('--font-family', fontFamilyMap[settings.fontFamily]);

    // Font boyutu (12-24pt)
    root.style.setProperty('--font-size-base', `${settings.fontSize}px`);

    // Font kalınlığı
    root.style.setProperty('--font-weight', settings.fontWeight);

    // Satır aralığı (1.0-3.0x) - REQ-50.8
    root.style.setProperty('--line-height', settings.lineHeight.toString());

    // REQ-50.9: Paragraf aralığını satır aralığının 1.5 katı olarak otomatik ayarla
    // 100ms içinde uygulanır (CSS transition ile)
    const autoParagraphSpacing = settings.lineHeight * 1.5;
    root.style.setProperty('--auto-paragraph-spacing', `${autoParagraphSpacing}em`);

    // Harf aralığı (0-0.5em)
    root.style.setProperty('--letter-spacing', `${settings.letterSpacing}em`);

    // Kelime aralığı (0-0.5em)
    root.style.setProperty('--word-spacing', `${settings.wordSpacing}em`);

    // Paragraf aralığı (0-3em) - kullanıcı manuel ayarı
    root.style.setProperty('--paragraph-spacing', `${settings.paragraphSpacing}em`);

    // REQ-50.10: Satır aralığı 1.5x veya üzerinde ise optimal okuma genişliği uygula
    if (settings.lineHeight >= 1.5) {
      root.style.setProperty('--optimal-line-length', '75ch'); // 75 karakter
      root.style.setProperty('--text-align', 'left'); // Sola yasla
      root.classList.add('optimal-reading-width');
    } else {
      root.style.setProperty('--optimal-line-length', 'none');
      root.style.setProperty('--text-align', 'inherit');
      root.classList.remove('optimal-reading-width');
    }

    // Renk overlay
    if (settings.colorOverlay !== 'none') {
      const overlayColors: Record<Exclude<DyslexiaSettings['colorOverlay'], 'none'>, string> = {
        'blue': '173, 216, 230',
        'green': '144, 238, 144',
        'yellow': '255, 255, 224',
        'pink': '255, 192, 203',
        'purple': '221, 160, 221',
        'gray': '211, 211, 211',
      };
      root.style.setProperty('--overlay-color', overlayColors[settings.colorOverlay]);
      root.style.setProperty('--overlay-opacity', settings.overlayOpacity.toString());
      root.classList.add('color-overlay-active');
    } else {
      root.classList.remove('color-overlay-active');
    }

    // Yüksek kontrast
    if (settings.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }

    // Bionic reading
    if (settings.bionicReading) {
      root.classList.add('bionic-reading');
    } else {
      root.classList.remove('bionic-reading');
    }

    // Hece ayırma
    if (settings.syllableBreaks) {
      root.classList.add('syllable-breaks');
    } else {
      root.classList.remove('syllable-breaks');
    }

    // Okuma cetveli
    if (settings.readingRuler) {
      root.classList.add('reading-ruler-active');
    } else {
      root.classList.remove('reading-ruler-active');
    }

    // Odak modu
    if (settings.focusMode) {
      root.classList.add('focus-mode');
    } else {
      root.classList.remove('focus-mode');
    }

    // Disleksi desteği aktif class'ı
    root.classList.add('dyslexia-support-active');
  }, []);

  // Font boyutunu artır
  const increaseFontSize = useCallback(() => {
    const newSize = Math.min(settings.fontSize + 1, 24);
    updateSetting('fontSize', newSize);
  }, [settings.fontSize, updateSetting]);

  // Font boyutunu azalt
  const decreaseFontSize = useCallback(() => {
    const newSize = Math.max(settings.fontSize - 1, 12);
    updateSetting('fontSize', newSize);
  }, [settings.fontSize, updateSetting]);

  // Satır aralığını artır
  const increaseLineHeight = useCallback(() => {
    const newHeight = Math.min(settings.lineHeight + 0.1, 3.0);
    updateSetting('lineHeight', Math.round(newHeight * 10) / 10);
  }, [settings.lineHeight, updateSetting]);

  // Satır aralığını azalt
  const decreaseLineHeight = useCallback(() => {
    const newHeight = Math.max(settings.lineHeight - 0.1, 1.0);
    updateSetting('lineHeight', Math.round(newHeight * 10) / 10);
  }, [settings.lineHeight, updateSetting]);

  // Harf aralığını artır
  const increaseLetterSpacing = useCallback(() => {
    const newSpacing = Math.min(settings.letterSpacing + 0.05, 0.5);
    updateSetting('letterSpacing', Math.round(newSpacing * 100) / 100);
  }, [settings.letterSpacing, updateSetting]);

  // Harf aralığını azalt
  const decreaseLetterSpacing = useCallback(() => {
    const newSpacing = Math.max(settings.letterSpacing - 0.05, 0);
    updateSetting('letterSpacing', Math.round(newSpacing * 100) / 100);
  }, [settings.letterSpacing, updateSetting]);

  // Kelime aralığını artır
  const increaseWordSpacing = useCallback(() => {
    const newSpacing = Math.min(settings.wordSpacing + 0.05, 0.5);
    updateSetting('wordSpacing', Math.round(newSpacing * 100) / 100);
  }, [settings.wordSpacing, updateSetting]);

  // Kelime aralığını azalt
  const decreaseWordSpacing = useCallback(() => {
    const newSpacing = Math.max(settings.wordSpacing - 0.05, 0);
    updateSetting('wordSpacing', Math.round(newSpacing * 100) / 100);
  }, [settings.wordSpacing, updateSetting]);

  // Ayarları sıfırla
  const resetSettings = useCallback(() => {
    saveSettings(DEFAULT_SETTINGS);
  }, [saveSettings]);

  // Preset ayarlar
  const applyPreset = useCallback((preset: 'mild' | 'moderate' | 'severe') => {
    const presets: Record<string, Partial<DyslexiaSettings>> = {
      mild: {
        fontFamily: 'verdana',
        fontSize: 16,
        lineHeight: 1.6,
        letterSpacing: 0.05,
        wordSpacing: 0.05,
      },
      moderate: {
        fontFamily: 'opendyslexic',
        fontSize: 18,
        lineHeight: 1.8,
        letterSpacing: 0.1,
        wordSpacing: 0.1,
        paragraphSpacing: 1.5,
      },
      severe: {
        fontFamily: 'opendyslexic',
        fontSize: 20,
        lineHeight: 2.0,
        letterSpacing: 0.15,
        wordSpacing: 0.15,
        paragraphSpacing: 2,
        bionicReading: true,
        syllableBreaks: true,
      },
    };

    const newSettings = { ...settings, ...presets[preset] };
    saveSettings(newSettings);
  }, [settings, saveSettings]);

  // CSS değişkenlerini güncelle
  useEffect(() => {
    if (!isLoading && fontsLoaded) {
      applySettingsToDOM(settings);
    }
  }, [settings, isLoading, fontsLoaded, applySettingsToDOM]);

  return {
    // Durum
    settings,
    isLoading,
    fontsLoaded,

    // Ayar fonksiyonları
    updateSetting,
    saveSettings,
    resetSettings,
    applyPreset,

    // Hızlı ayarlama fonksiyonları
    increaseFontSize,
    decreaseFontSize,
    increaseLineHeight,
    decreaseLineHeight,
    increaseLetterSpacing,
    decreaseLetterSpacing,
    increaseWordSpacing,
    decreaseWordSpacing,
  };
};

export default useDyslexiaSettings;

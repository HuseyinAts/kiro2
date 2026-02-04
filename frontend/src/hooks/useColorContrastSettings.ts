/**
 * Renk ve Kontrast Ayarları Hook'u
 * REQ-50.14 - REQ-50.27: Renk ve Kontrast Ayarları
 * 
 * Özellikler:
 * - Renkli overlay (6 renk: mavi, yeşil, sarı, pembe, mor, gri)
 * - Opacity ayarlama (%10-%90)
 * - Yüksek kontrast modları
 * - WCAG AAA uyumluluk (7:1 kontrast oranı)
 */

import { useState, useEffect, useCallback } from 'react';

export interface ColorContrastSettings {
  // Renkli overlay - REQ-50.14, REQ-50.15
  colorOverlay: 'none' | 'blue' | 'green' | 'yellow' | 'pink' | 'purple' | 'gray';
  overlayOpacity: number; // 0.1-0.9 (REQ-50.16, REQ-50.18)
  
  // Kontrast modları - REQ-50.21, REQ-50.22
  contrastMode: 'normal' | 'high' | 'dark' | 'custom';
  customContrastRatio: number; // 1-21 (REQ-50.23)
  
  // Renk ayarları
  textColor: string;
  backgroundColor: string;
  
  // Link renkleri
  linkColor: string;
  visitedLinkColor: string;
  
  // Vurgu renkleri
  highlightColor: string;
  focusColor: string;
}

const DEFAULT_SETTINGS: ColorContrastSettings = {
  colorOverlay: 'none',
  overlayOpacity: 0.3,
  contrastMode: 'normal',
  customContrastRatio: 4.5,
  textColor: '#000000',
  backgroundColor: '#FFFFFF',
  linkColor: '#0066CC',
  visitedLinkColor: '#551A8B',
  highlightColor: '#FFFF00',
  focusColor: '#0066CC',
};

// WCAG AAA kontrast oranı minimum: 7:1 (REQ-50.25)
const WCAG_AAA_RATIO = 7.0;
const WCAG_AA_RATIO = 4.5;

const STORAGE_KEY = 'color-contrast-settings';

// Renk overlay RGB değerleri
const OVERLAY_COLORS: Record<Exclude<ColorContrastSettings['colorOverlay'], 'none'>, string> = {
  'blue': '173, 216, 230',
  'green': '144, 238, 144',
  'yellow': '255, 255, 224',
  'pink': '255, 192, 203',
  'purple': '221, 160, 221',
  'gray': '211, 211, 211',
};

export const useColorContrastSettings = () => {
  const [settings, setSettings] = useState<ColorContrastSettings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);

  // Ayarları localStorage'dan yükle
  useEffect(() => {
    try {
      const savedSettings = localStorage.getItem(STORAGE_KEY);
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...DEFAULT_SETTINGS, ...parsed });
      }
    } catch (error) {
      console.warn('Renk ve kontrast ayarları yüklenemedi:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Ayarları kaydet - REQ-50.20
  const saveSettings = useCallback((newSettings: ColorContrastSettings) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newSettings));
      setSettings(newSettings);
      applySettingsToDOM(newSettings);
    } catch (error) {
      console.error('Renk ve kontrast ayarları kaydedilemedi:', error);
    }
  }, []);

  // Tek bir ayarı güncelle
  const updateSetting = useCallback(<K extends keyof ColorContrastSettings>(
    key: K,
    value: ColorContrastSettings[K]
  ) => {
    const newSettings = { ...settings, [key]: value };
    
    // REQ-50.17: Overlay uygulandığında kontrast oranını otomatik ayarla
    if (key === 'colorOverlay' && value !== 'none') {
      // Metin okunabilirliğini korumak için kontrast kontrolü
      const contrastRatio = calculateContrastRatioForSettings(newSettings);
      if (contrastRatio < WCAG_AA_RATIO) {
        // Kontrast yetersizse metin rengini ayarla
        newSettings.textColor = '#000000';
      }
    }
    
    saveSettings(newSettings);
  }, [settings, saveSettings]);

  // Ayarları DOM'a uygula - REQ-50.15, REQ-50.19, REQ-50.24
  const applySettingsToDOM = useCallback((settings: ColorContrastSettings) => {
    const root = document.documentElement;
    
    // Renkli overlay - REQ-50.15
    if (settings.colorOverlay !== 'none') {
      root.style.setProperty('--overlay-color', OVERLAY_COLORS[settings.colorOverlay]);
      root.style.setProperty('--overlay-opacity', settings.overlayOpacity.toString());
      root.classList.add('color-overlay-active');
    } else {
      root.classList.remove('color-overlay-active');
    }
    
    // Kontrast modu - REQ-50.21, REQ-50.22, REQ-50.24
    root.classList.remove('contrast-normal', 'contrast-high', 'contrast-dark', 'contrast-custom');
    root.classList.add(`contrast-${settings.contrastMode}`);
    
    if (settings.contrastMode === 'high') {
      // Yüksek kontrast modu
      root.style.setProperty('--text-color', '#000000');
      root.style.setProperty('--background-color', '#FFFFFF');
      root.style.setProperty('--link-color', '#0000EE');
      root.style.setProperty('--border-color', '#000000');
    } else if (settings.contrastMode === 'dark') {
      // Karanlık mod - REQ-50.22
      root.style.setProperty('--text-color', '#FFFFFF');
      root.style.setProperty('--background-color', '#121212');
      root.style.setProperty('--link-color', '#8AB4F8');
      root.style.setProperty('--border-color', '#FFFFFF');
    } else if (settings.contrastMode === 'custom') {
      // Özel kontrast - REQ-50.23
      root.style.setProperty('--text-color', settings.textColor);
      root.style.setProperty('--background-color', settings.backgroundColor);
      root.style.setProperty('--custom-contrast-ratio', settings.customContrastRatio.toString());
    } else {
      // Normal mod
      root.style.setProperty('--text-color', settings.textColor);
      root.style.setProperty('--background-color', settings.backgroundColor);
    }
    
    // Link renkleri
    root.style.setProperty('--link-color', settings.linkColor);
    root.style.setProperty('--visited-link-color', settings.visitedLinkColor);
    
    // Vurgu renkleri
    root.style.setProperty('--highlight-color', settings.highlightColor);
    root.style.setProperty('--focus-color', settings.focusColor);
    
    // Renk ve kontrast desteği aktif class'ı
    root.classList.add('color-contrast-support-active');
  }, []);

  // Opacity artır - REQ-50.18
  const increaseOpacity = useCallback(() => {
    const newOpacity = Math.min(settings.overlayOpacity + 0.1, 0.9);
    updateSetting('overlayOpacity', Math.round(newOpacity * 10) / 10);
  }, [settings.overlayOpacity, updateSetting]);

  // Opacity azalt - REQ-50.18
  const decreaseOpacity = useCallback(() => {
    const newOpacity = Math.max(settings.overlayOpacity - 0.1, 0.1);
    updateSetting('overlayOpacity', Math.round(newOpacity * 10) / 10);
  }, [settings.overlayOpacity, updateSetting]);

  // Kontrast oranını hesapla - REQ-50.26
  const calculateContrastRatio = useCallback((): number => {
    return calculateContrastRatioForSettings(settings);
  }, [settings]);

  // WCAG AAA uyumluluğunu kontrol et - REQ-50.25
  const isWCAGAAACompliant = useCallback((): boolean => {
    const ratio = calculateContrastRatio();
    return ratio >= WCAG_AAA_RATIO;
  }, [calculateContrastRatio]);

  // WCAG AA uyumluluğunu kontrol et
  const isWCAGAACompliant = useCallback((): boolean => {
    const ratio = calculateContrastRatio();
    return ratio >= WCAG_AA_RATIO;
  }, [calculateContrastRatio]);

  // Ayarları sıfırla
  const resetSettings = useCallback(() => {
    saveSettings(DEFAULT_SETTINGS);
  }, [saveSettings]);

  // Preset ayarlar
  const applyPreset = useCallback((preset: 'reading' | 'exam' | 'night') => {
    const presets: Record<string, Partial<ColorContrastSettings>> = {
      reading: {
        colorOverlay: 'yellow',
        overlayOpacity: 0.2,
        contrastMode: 'normal',
        textColor: '#000000',
        backgroundColor: '#FFFFF0',
      },
      exam: {
        colorOverlay: 'blue',
        overlayOpacity: 0.15,
        contrastMode: 'high',
        textColor: '#000000',
        backgroundColor: '#FFFFFF',
      },
      night: {
        colorOverlay: 'none',
        overlayOpacity: 0.3,
        contrastMode: 'dark',
        textColor: '#E0E0E0',
        backgroundColor: '#121212',
      },
    };
    
    const newSettings = { ...settings, ...presets[preset] };
    saveSettings(newSettings);
  }, [settings, saveSettings]);

  // CSS değişkenlerini güncelle
  useEffect(() => {
    if (!isLoading) {
      applySettingsToDOM(settings);
    }
  }, [settings, isLoading, applySettingsToDOM]);

  return {
    // Durum
    settings,
    isLoading,
    
    // Ayar fonksiyonları
    updateSetting,
    saveSettings,
    resetSettings,
    applyPreset,
    
    // Hızlı ayarlama fonksiyonları
    increaseOpacity,
    decreaseOpacity,
    
    // Kontrast hesaplama - REQ-50.26
    calculateContrastRatio,
    isWCAGAAACompliant,
    isWCAGAACompliant,
  };
};

// Yardımcı fonksiyonlar

// Hex rengi RGB'ye çevir
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

// Relative luminance hesapla (WCAG 2.1)
function getRelativeLuminance(r: number, g: number, b: number): number {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

// Kontrast oranını hesapla (WCAG 2.1) - REQ-50.26
function calculateContrastRatioForSettings(settings: ColorContrastSettings): number {
  const textRgb = hexToRgb(settings.textColor);
  const bgRgb = hexToRgb(settings.backgroundColor);
  
  if (!textRgb || !bgRgb) {
    return 1; // Geçersiz renk
  }
  
  const textLuminance = getRelativeLuminance(textRgb.r, textRgb.g, textRgb.b);
  const bgLuminance = getRelativeLuminance(bgRgb.r, bgRgb.g, bgRgb.b);
  
  const lighter = Math.max(textLuminance, bgLuminance);
  const darker = Math.min(textLuminance, bgLuminance);
  
  return (lighter + 0.05) / (darker + 0.05);
}

export default useColorContrastSettings;

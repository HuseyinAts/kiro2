/**
 * Okuma Yardımcıları Hook'u
 * REQ-50.28 - REQ-50.42: Okuma Yardımcıları
 *
 * Özellikler:
 * - Okuma cetveli (reading ruler)
 * - Odak modu (focus mode)
 * - Kelime vurgulama
 * - Hece ayırma
 */

import { useState, useEffect, useCallback } from 'react';

export interface ReadingRulerSettings {
  enabled: boolean;
  height: number; // 30-100px
  followCursor: boolean;
  color: string;
  opacity: number; // 0.1-0.9
}

export interface FocusModeSettings {
  enabled: boolean;
  focusArea: 'line' | 'paragraph' | 'sentence';
  dimIntensity: number; // 0.1-0.9
  highlightColor: string;
}

export interface WordHighlightSettings {
  enabled: boolean;
  mode: 'hover' | 'click' | 'both';
  multiColor: boolean;
  colors: string[]; // Array of highlight colors
}

export interface SyllableBreaksSettings {
  enabled: boolean;
  separator: 'dot' | 'dash' | 'space';
  visualMarker: boolean;
  markerColor: string;
}

export interface ReadingHelpersSettings {
  readingRuler: ReadingRulerSettings;
  focusMode: FocusModeSettings;
  wordHighlight: WordHighlightSettings;
  syllableBreaks: SyllableBreaksSettings;
}

const DEFAULT_SETTINGS: ReadingHelpersSettings = {
  readingRuler: {
    enabled: false,
    height: 50,
    followCursor: true,
    color: '#ffeb3b',
    opacity: 0.3,
  },
  focusMode: {
    enabled: false,
    focusArea: 'line',
    dimIntensity: 0.7,
    highlightColor: '#ffffff',
  },
  wordHighlight: {
    enabled: false,
    mode: 'hover',
    multiColor: false,
    colors: ['#ffeb3b', '#4caf50', '#2196f3', '#ff9800', '#e91e63'],
  },
  syllableBreaks: {
    enabled: false,
    separator: 'dot',
    visualMarker: false,
    markerColor: '#2196f3',
  },
};

const STORAGE_KEY = 'reading-helpers-settings';

export const useReadingHelpers = () => {
  const [settings, setSettings] = useState<ReadingHelpersSettings>(DEFAULT_SETTINGS);
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
      console.warn('Okuma yardımcıları ayarları yüklenemedi:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Ayarları localStorage'a kaydet
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      } catch (error) {
        console.warn('Okuma yardımcıları ayarları kaydedilemedi:', error);
      }
    }
  }, [settings, isLoading]);

  // Ayarları DOM'a uygula
  useEffect(() => {
    if (!isLoading) {
      applySettingsToDOM(settings);
    }

    // Cleanup: Component unmount olduğunda tüm DOM değişikliklerini temizle
    return () => {
      removeReadingRuler();
      disableFocusMode();
      disableWordHighlight();
      disableSyllableBreaks();

      // CSS class'larını temizle
      document.body.classList.remove(
        'reading-ruler-active',
        'focus-mode-active',
        'word-highlight-active',
        'syllable-breaks-active',
      );
    };
  }, [settings, isLoading]);

  // Ayarları güncelle
  const updateSetting = useCallback(<K extends keyof ReadingHelpersSettings>(
    key: K,
    value: ReadingHelpersSettings[K],
  ) => {
    setSettings(prev => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  // Ayarları sıfırla
  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  // Preset uygula
  const applyPreset = useCallback((preset: 'basic' | 'focus' | 'advanced') => {
    switch (preset) {
      case 'basic':
        setSettings({
          ...DEFAULT_SETTINGS,
          readingRuler: {
            ...DEFAULT_SETTINGS.readingRuler,
            enabled: true,
          },
          wordHighlight: {
            ...DEFAULT_SETTINGS.wordHighlight,
            enabled: true,
            mode: 'hover',
          },
        });
        break;
      case 'focus':
        setSettings({
          ...DEFAULT_SETTINGS,
          focusMode: {
            ...DEFAULT_SETTINGS.focusMode,
            enabled: true,
            focusArea: 'paragraph',
            dimIntensity: 0.8,
          },
          readingRuler: {
            ...DEFAULT_SETTINGS.readingRuler,
            enabled: true,
          },
        });
        break;
      case 'advanced':
        setSettings({
          readingRuler: {
            ...DEFAULT_SETTINGS.readingRuler,
            enabled: true,
          },
          focusMode: {
            ...DEFAULT_SETTINGS.focusMode,
            enabled: true,
            focusArea: 'line',
          },
          wordHighlight: {
            ...DEFAULT_SETTINGS.wordHighlight,
            enabled: true,
            mode: 'both',
            multiColor: true,
          },
          syllableBreaks: {
            ...DEFAULT_SETTINGS.syllableBreaks,
            enabled: true,
            visualMarker: true,
          },
        });
        break;
    }
  }, []);

  return {
    settings,
    isLoading,
    updateSetting,
    resetSettings,
    applyPreset,
  };
};

// Ayarları DOM'a uygula
function applySettingsToDOM(settings: ReadingHelpersSettings) {
  const root = document.documentElement;

  // Okuma Cetveli CSS değişkenleri
  root.style.setProperty('--reading-ruler-enabled', settings.readingRuler.enabled ? '1' : '0');
  root.style.setProperty('--reading-ruler-height', `${settings.readingRuler.height}px`);
  root.style.setProperty('--reading-ruler-color', settings.readingRuler.color);
  root.style.setProperty('--reading-ruler-opacity', settings.readingRuler.opacity.toString());

  // Odak Modu CSS değişkenleri
  root.style.setProperty('--focus-mode-enabled', settings.focusMode.enabled ? '1' : '0');
  root.style.setProperty('--focus-dim-intensity', settings.focusMode.dimIntensity.toString());
  root.style.setProperty('--focus-highlight-color', settings.focusMode.highlightColor);

  // Kelime Vurgulama CSS değişkenleri
  root.style.setProperty('--word-highlight-enabled', settings.wordHighlight.enabled ? '1' : '0');
  settings.wordHighlight.colors.forEach((color, index) => {
    root.style.setProperty(`--word-highlight-color-${index + 1}`, color);
  });

  // Hece Ayırma CSS değişkenleri
  root.style.setProperty('--syllable-breaks-enabled', settings.syllableBreaks.enabled ? '1' : '0');
  root.style.setProperty('--syllable-marker-color', settings.syllableBreaks.markerColor);

  // Body class'ları
  document.body.classList.toggle('reading-ruler-active', settings.readingRuler.enabled);
  document.body.classList.toggle('focus-mode-active', settings.focusMode.enabled);
  document.body.classList.toggle('word-highlight-active', settings.wordHighlight.enabled);
  document.body.classList.toggle('syllable-breaks-active', settings.syllableBreaks.enabled);

  // Okuma cetveli element'ini oluştur/güncelle
  if (settings.readingRuler.enabled) {
    createOrUpdateReadingRuler(settings.readingRuler);
  } else {
    removeReadingRuler();
  }

  // Odak modu event listener'ları
  if (settings.focusMode.enabled) {
    enableFocusMode(settings.focusMode);
  } else {
    disableFocusMode();
  }

  // Kelime vurgulama event listener'ları
  if (settings.wordHighlight.enabled) {
    enableWordHighlight(settings.wordHighlight);
  } else {
    disableWordHighlight();
  }

  // Hece ayırma
  if (settings.syllableBreaks.enabled) {
    enableSyllableBreaks(settings.syllableBreaks);
  } else {
    disableSyllableBreaks();
  }
}

// Okuma cetveli oluştur/güncelle
function createOrUpdateReadingRuler(settings: ReadingRulerSettings) {
  let ruler = document.getElementById('reading-ruler');

  // Eski event listener'ı temizle (memory leak fix)
  if (ruler && (ruler as HTMLDivElement & { _mouseMoveHandler?: (e: MouseEvent) => void })._mouseMoveHandler) {
    document.removeEventListener('mousemove', (ruler as HTMLDivElement & { _mouseMoveHandler: (e: MouseEvent) => void })._mouseMoveHandler);
    delete (ruler as HTMLDivElement & { _mouseMoveHandler?: (e: MouseEvent) => void })._mouseMoveHandler;
  }

  if (!ruler) {
    ruler = document.createElement('div');
    ruler.id = 'reading-ruler';
    ruler.className = 'reading-ruler';
    document.body.appendChild(ruler);
  }

  ruler.style.height = `${settings.height}px`;
  ruler.style.backgroundColor = settings.color;
  ruler.style.opacity = settings.opacity.toString();
  ruler.style.position = 'fixed';
  ruler.style.left = '0';
  ruler.style.right = '0';
  ruler.style.pointerEvents = 'none';
  ruler.style.zIndex = '9998';
  ruler.style.transition = 'top 0.1s ease-out';

  if (settings.followCursor) {
    const handleMouseMove = (e: MouseEvent) => {
      const rulerElement = document.getElementById('reading-ruler');
      if (rulerElement) {
        rulerElement.style.top = `${e.clientY - settings.height / 2}px`;
      }
    };
    document.addEventListener('mousemove', handleMouseMove);
    (ruler as HTMLDivElement & { _mouseMoveHandler: (e: MouseEvent) => void })._mouseMoveHandler = handleMouseMove;
  }
}

// Okuma cetvelini kaldır
function removeReadingRuler() {
  const ruler = document.getElementById('reading-ruler') as HTMLDivElement & { _mouseMoveHandler?: (e: MouseEvent) => void } | null;
  if (ruler) {
    if (ruler._mouseMoveHandler) {
      document.removeEventListener('mousemove', ruler._mouseMoveHandler);
      delete ruler._mouseMoveHandler;
    }
    ruler.remove();
  }
}

// Type for overlay element with focus handler
type FocusModeOverlay = HTMLDivElement & { _focusHandler?: (e: MouseEvent) => void };

// Odak modunu etkinleştir
function enableFocusMode(settings: FocusModeSettings) {
  // Odak modu overlay'i oluştur
  let overlay = document.getElementById('focus-mode-overlay') as FocusModeOverlay | null;

  // Eski event listener'ı temizle (memory leak fix)
  if (overlay && overlay._focusHandler) {
    document.removeEventListener('mousemove', overlay._focusHandler);
    delete overlay._focusHandler;
  }

  if (!overlay) {
    overlay = document.createElement('div') as FocusModeOverlay;
    overlay.id = 'focus-mode-overlay';
    overlay.className = 'focus-mode-overlay';
    document.body.appendChild(overlay);
  }

  overlay.style.position = 'fixed';
  overlay.style.top = '0';
  overlay.style.left = '0';
  overlay.style.right = '0';
  overlay.style.bottom = '0';
  overlay.style.backgroundColor = `rgba(0, 0, 0, ${settings.dimIntensity})`;
  overlay.style.pointerEvents = 'none';
  overlay.style.zIndex = '9997';

  // Odak alanını vurgula
  const handleFocus = (e: MouseEvent) => {
    const target = e.target as HTMLElement;

    // Odak alanını bul
    let focusElement: HTMLElement | null = null;

    switch (settings.focusArea) {
      case 'line':
        // En yakın satırı bul (p, div, span, etc.)
        focusElement = target.closest('p, div, span, li, td, th') as HTMLElement;
        break;
      case 'paragraph':
        focusElement = target.closest('p, div, article, section') as HTMLElement;
        break;
      case 'sentence':
        // Cümle tespiti için özel mantık gerekir
        focusElement = target.closest('p, div, span') as HTMLElement;
        break;
    }

    if (focusElement) {
      // Önceki vurgulamayı kaldır
      document.querySelectorAll('.focus-highlighted').forEach(el => {
        el.classList.remove('focus-highlighted');
      });

      // Yeni vurgulamayı ekle
      focusElement.classList.add('focus-highlighted');
      focusElement.style.position = 'relative';
      focusElement.style.zIndex = '9999';
      focusElement.style.backgroundColor = settings.highlightColor;
    }
  };

  document.addEventListener('mousemove', handleFocus);
  overlay._focusHandler = handleFocus;
}

// Odak modunu devre dışı bırak
function disableFocusMode() {
  const overlay = document.getElementById('focus-mode-overlay') as FocusModeOverlay | null;
  if (overlay) {
    if (overlay._focusHandler) {
      document.removeEventListener('mousemove', overlay._focusHandler);
      delete overlay._focusHandler;
    }
    overlay.remove();
  }

  // Vurgulamaları temizle
  document.querySelectorAll('.focus-highlighted').forEach(el => {
    el.classList.remove('focus-highlighted');
    (el as HTMLElement).style.position = '';
    (el as HTMLElement).style.zIndex = '';
    (el as HTMLElement).style.backgroundColor = '';
  });
}

// Type for word highlight handlers
interface WordHighlightHandlers {
  hover: (e: MouseEvent) => void;
  mouseOut: (e: MouseEvent) => void;
  click: (e: MouseEvent) => void;
}

type BodyWithWordHighlight = HTMLBodyElement & { _wordHighlightHandlers?: WordHighlightHandlers };

// Kelime vurgulamayı etkinleştir
function enableWordHighlight(settings: WordHighlightSettings) {
  // Eski event listener'ları temizle (memory leak fix)
  const body = document.body as BodyWithWordHighlight;
  if (body._wordHighlightHandlers) {
    document.removeEventListener('mouseover', body._wordHighlightHandlers.hover);
    document.removeEventListener('mouseout', body._wordHighlightHandlers.mouseOut);
    document.removeEventListener('click', body._wordHighlightHandlers.click);
    delete body._wordHighlightHandlers;
  }

  let colorIndex = 0;

  const highlightWord = (element: HTMLElement) => {
    if (element.classList.contains('word-highlighted')) {
      return;
    }

    const color = settings.multiColor
      ? settings.colors[colorIndex % settings.colors.length]
      : settings.colors[0];

    element.style.backgroundColor = color;
    element.style.padding = '2px 4px';
    element.style.borderRadius = '3px';
    element.classList.add('word-highlighted');

    if (settings.multiColor) {
      colorIndex++;
    }
  };

  const unhighlightWord = (element: HTMLElement) => {
    if (settings.mode === 'click') {
      return; // Tiklama modunda vurgulama kalici
    }

    element.style.backgroundColor = '';
    element.style.padding = '';
    element.style.borderRadius = '';
    element.classList.remove('word-highlighted');
  };

  const handleHover = (e: MouseEvent) => {
    const target = e.target as HTMLElement;

    if (target.tagName === 'SPAN' && target.classList.contains('word')) {
      highlightWord(target);
    }
  };

  const handleMouseOut = (e: MouseEvent) => {
    const target = e.target as HTMLElement;

    if (target.tagName === 'SPAN' && target.classList.contains('word')) {
      unhighlightWord(target);
    }
  };

  const handleClick = (e: MouseEvent) => {
    const target = e.target as HTMLElement;

    if (target.tagName === 'SPAN' && target.classList.contains('word')) {
      if (target.classList.contains('word-highlighted')) {
        unhighlightWord(target);
      } else {
        highlightWord(target);
      }
    }
  };

  if (settings.mode === 'hover' || settings.mode === 'both') {
    document.addEventListener('mouseover', handleHover);
    document.addEventListener('mouseout', handleMouseOut);
  }

  if (settings.mode === 'click' || settings.mode === 'both') {
    document.addEventListener('click', handleClick);
  }

  // Event handler'lari sakla
  body._wordHighlightHandlers = {
    hover: handleHover,
    mouseOut: handleMouseOut,
    click: handleClick,
  };
}

// Kelime vurgulamayi devre disi birak
function disableWordHighlight() {
  const body = document.body as BodyWithWordHighlight;
  const handlers = body._wordHighlightHandlers;

  if (handlers) {
    document.removeEventListener('mouseover', handlers.hover);
    document.removeEventListener('mouseout', handlers.mouseOut);
    document.removeEventListener('click', handlers.click);
    delete body._wordHighlightHandlers;
  }

  // Vurgulamalari temizle
  document.querySelectorAll('.word-highlighted').forEach(el => {
    (el as HTMLElement).style.backgroundColor = '';
    (el as HTMLElement).style.padding = '';
    (el as HTMLElement).style.borderRadius = '';
    el.classList.remove('word-highlighted');
  });
}

// Hece ayırmayı etkinleştir
function enableSyllableBreaks(settings: SyllableBreaksSettings) {
  // Türkçe hece kuralları
  const syllabify = (word: string): string[] => {
    // Basit Türkçe hece ayırma algoritması
    // Gerçek implementasyon için Zemberek NLP kullanılabilir
    const syllables: string[] = [];
    const vowels = 'aeıioöuüAEIİOÖUÜ';
    let currentSyllable = '';

    for (let i = 0; i < word.length; i++) {
      const char = word[i];
      currentSyllable += char;

      // Sesli harf bulundu
      if (vowels.includes(char)) {
        // Sonraki karakter sessiz mi kontrol et
        if (i + 1 < word.length && !vowels.includes(word[i + 1])) {
          // Sessiz harf varsa, bir sonraki sesli harfe kadar devam et
          let j = i + 1;
          while (j < word.length && !vowels.includes(word[j])) {
            j++;
          }

          // Sessiz harf sayısına göre hece ayır
          const consonants = j - i - 1;
          if (consonants > 1) {
            // Çift sessiz: ilk sessizi mevcut heceye ekle
            currentSyllable += word[i + 1];
            syllables.push(currentSyllable);
            currentSyllable = '';
            i++;
          } else if (j < word.length) {
            // Tek sessiz: sonraki heceye geç
            syllables.push(currentSyllable);
            currentSyllable = '';
          }
        } else if (i + 1 >= word.length) {
          // Son harf
          syllables.push(currentSyllable);
          currentSyllable = '';
        }
      }
    }

    if (currentSyllable) {
      syllables.push(currentSyllable);
    }

    return syllables.length > 0 ? syllables : [word];
  };

  // Metindeki kelimeleri hecele
  const processText = (element: HTMLElement) => {
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      null,
    );

    const textNodes: Text[] = [];
    let node: Node | null;

    while ((node = walker.nextNode())) {
      textNodes.push(node as Text);
    }

    textNodes.forEach(textNode => {
      const words = textNode.textContent?.split(/\s+/) || [];
      const syllabifiedWords = words.map(word => {
        const syllables = syllabify(word);
        let separator = '';

        switch (settings.separator) {
          case 'dot':
            separator = '·';
            break;
          case 'dash':
            separator = '-';
            break;
          case 'space':
            separator = ' ';
            break;
        }

        return syllables.join(separator);
      });

      const newText = syllabifiedWords.join(' ');
      if (textNode.textContent !== newText) {
        textNode.textContent = newText;
      }
    });
  };

  // Tüm metin içeren elementleri işle
  document.querySelectorAll('p, div, span, li, td, th, h1, h2, h3, h4, h5, h6').forEach(el => {
    if (!el.classList.contains('syllabified')) {
      processText(el as HTMLElement);
      el.classList.add('syllabified');
    }
  });
}

// Hece ayırmayı devre dışı bırak
function disableSyllableBreaks() {
  // Sayfa yenilenmesi gerekir çünkü metin değiştirildi
  // Alternatif olarak, orijinal metni saklamak gerekir
  document.querySelectorAll('.syllabified').forEach(el => {
    el.classList.remove('syllabified');
  });
}

export default useReadingHelpers;

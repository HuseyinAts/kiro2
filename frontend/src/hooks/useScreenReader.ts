/**
 * Ekran Okuyucu Desteği Hook'u
 * WCAG 2.1 Level AA uyumlu ekran okuyucu optimizasyonları
 */

import { useCallback, useEffect, useRef } from 'react';

import { useAccessibilitySettings } from './useAccessibilitySettings';

interface ScreenReaderHook {
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
  announcePageChange: (pageTitle: string, pageDescription?: string) => void;
  announceFormError: (fieldName: string, errorMessage: string) => void;
  announceSuccess: (message: string) => void;
  announceLoading: (isLoading: boolean, message?: string) => void;
  announceContentChange: (message: string) => void;
  announceLandmark: (landmarkType: string, landmarkName?: string) => void;
  manageFocus: (element: HTMLElement | null, reason?: string) => void;
  createSkipLink: (targetId: string, linkText: string) => HTMLAnchorElement;
  isScreenReaderActive: boolean;
}

export const useScreenReader = (): ScreenReaderHook => {
  const { settings } = useAccessibilitySettings();
  const liveRegionRef = useRef<HTMLDivElement | null>(null);
  const assertiveRegionRef = useRef<HTMLDivElement | null>(null);
  const statusRegionRef = useRef<HTMLDivElement | null>(null);
  const isScreenReaderActiveRef = useRef<boolean>(false);

  // Ekran okuyucu tespiti
  useEffect(() => {
    const detectScreenReader = () => {
      // Çeşitli ekran okuyucu tespiti yöntemleri
      const hasScreenReader =
        // NVDA, JAWS, ORCA gibi ekran okuyucular
        navigator.userAgent.includes('NVDA') ||
        navigator.userAgent.includes('JAWS') ||
        navigator.userAgent.includes('ORCA') ||
        // Speech Synthesis API varlığı
        'speechSynthesis' in window ||
        // Accessibility API'leri
        'getComputedAccessibleNode' in document ||
        // Windows Narrator
        navigator.userAgent.includes('Windows NT') && 'speechSynthesis' in window ||
        // Kullanıcı ayarları
        settings.screenReaderOptimized;

      isScreenReaderActiveRef.current = hasScreenReader;

      // Ekran okuyucu tespit edilirse optimizasyonları etkinleştir
      if (hasScreenReader) {
        document.documentElement.classList.add('screen-reader-active');

        // Reduced motion'ı otomatik etkinleştir
        if (!settings.reducedMotion) {
          document.documentElement.classList.add('reduced-motion');
        }
      }
    };

    detectScreenReader();
  }, [settings.screenReaderOptimized, settings.reducedMotion]);

  // Live region'ları oluştur
  useEffect(() => {
    // Polite live region
    if (!liveRegionRef.current) {
      const politeRegion = document.createElement('div');
      politeRegion.setAttribute('aria-live', 'polite');
      politeRegion.setAttribute('aria-atomic', 'true');
      politeRegion.setAttribute('aria-relevant', 'additions text');
      politeRegion.className = 'sr-only';
      politeRegion.style.cssText = `
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        white-space: nowrap !important;
        border: 0 !important;
      `;
      document.body.appendChild(politeRegion);
      liveRegionRef.current = politeRegion;
    }

    // Assertive live region
    if (!assertiveRegionRef.current) {
      const assertiveRegion = document.createElement('div');
      assertiveRegion.setAttribute('aria-live', 'assertive');
      assertiveRegion.setAttribute('aria-atomic', 'true');
      assertiveRegion.setAttribute('aria-relevant', 'additions text');
      assertiveRegion.className = 'sr-only';
      assertiveRegion.style.cssText = liveRegionRef.current?.style.cssText || '';
      document.body.appendChild(assertiveRegion);
      assertiveRegionRef.current = assertiveRegion;
    }

    // Status region
    if (!statusRegionRef.current) {
      const statusRegion = document.createElement('div');
      statusRegion.setAttribute('role', 'status');
      statusRegion.setAttribute('aria-live', 'polite');
      statusRegion.setAttribute('aria-atomic', 'false');
      statusRegion.className = 'sr-only';
      statusRegion.style.cssText = liveRegionRef.current?.style.cssText || '';
      document.body.appendChild(statusRegion);
      statusRegionRef.current = statusRegion;
    }

    // Cleanup
    return () => {
      if (liveRegionRef.current) {
        document.body.removeChild(liveRegionRef.current);
        liveRegionRef.current = null;
      }
      if (assertiveRegionRef.current) {
        document.body.removeChild(assertiveRegionRef.current);
        assertiveRegionRef.current = null;
      }
      if (statusRegionRef.current) {
        document.body.removeChild(statusRegionRef.current);
        statusRegionRef.current = null;
      }
    };
  }, []);

  // Genel duyuru fonksiyonu
  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!message.trim()) {return;}

    const region = priority === 'assertive' ? assertiveRegionRef.current : liveRegionRef.current;

    if (region) {
      // Önceki mesajı temizle
      region.textContent = '';

      // Kısa bir gecikme ile yeni mesajı ekle (ekran okuyucunun algılaması için)
      setTimeout(() => {
        region.textContent = message;
      }, 100);

      // Mesajı belirli bir süre sonra temizle
      setTimeout(() => {
        if (region.textContent === message) {
          region.textContent = '';
        }
      }, 5000);
    }

    // Console'a da log et (geliştirme amaçlı)
    console.log(`[Screen Reader ${priority.toUpperCase()}]:`, message);
  }, []);

  // Sayfa değişikliği duyurusu
  const announcePageChange = useCallback((pageTitle: string, pageDescription?: string) => {
    let message = `Sayfa değişti: ${pageTitle}`;
    if (pageDescription) {
      message += `. ${pageDescription}`;
    }

    announce(message, 'assertive');

    // Sayfa başlığını güncelle
    document.title = pageTitle;

    // Ana içeriğe odaklan
    setTimeout(() => {
      const mainContent = document.querySelector('main, [role="main"], #main-content');
      if (mainContent instanceof HTMLElement) {
        mainContent.focus();
      }
    }, 100);
  }, [announce]);

  // Form hatası duyurusu
  const announceFormError = useCallback((fieldName: string, errorMessage: string) => {
    const message = `${fieldName} alanında hata: ${errorMessage}`;
    announce(message, 'assertive');
  }, [announce]);

  // Başarı duyurusu
  const announceSuccess = useCallback((message: string) => {
    announce(`Başarılı: ${message}`, 'polite');
  }, [announce]);

  // Yükleme durumu duyurusu
  const announceLoading = useCallback((isLoading: boolean, message?: string) => {
    if (isLoading) {
      const loadingMessage = message || 'İçerik yükleniyor, lütfen bekleyin';
      announce(loadingMessage, 'polite');
    } else {
      const completedMessage = message || 'İçerik yükleme tamamlandı';
      announce(completedMessage, 'polite');
    }
  }, [announce]);

  // İçerik değişikliği duyurusu
  const announceContentChange = useCallback((message: string) => {
    if (statusRegionRef.current) {
      statusRegionRef.current.textContent = message;

      setTimeout(() => {
        if (statusRegionRef.current) {
          statusRegionRef.current.textContent = '';
        }
      }, 3000);
    }
  }, []);

  // Landmark duyurusu
  const announceLandmark = useCallback((landmarkType: string, landmarkName?: string) => {
    let message = `${landmarkType} bölümü`;
    if (landmarkName) {
      message += `: ${landmarkName}`;
    }
    announce(message, 'polite');
  }, [announce]);

  // Odak yönetimi
  const manageFocus = useCallback((element: HTMLElement | null, reason?: string) => {
    if (!element) {return;}

    // Element'in odaklanabilir olduğundan emin ol
    if (!element.hasAttribute('tabindex') && !element.matches('a, button, input, select, textarea, [tabindex]')) {
      element.setAttribute('tabindex', '-1');
    }

    // Odaklan
    element.focus();

    // Odaklanma nedenini duyur
    if (reason) {
      setTimeout(() => {
        announce(reason, 'polite');
      }, 100);
    }

    // Odak göstergesini geliştir
    element.style.outline = '2px solid #005fcc';
    element.style.outlineOffset = '2px';

    // Odak kaybedildiğinde outline'ı kaldır
    const handleBlur = () => {
      element.style.outline = '';
      element.style.outlineOffset = '';
      element.removeEventListener('blur', handleBlur);
    };

    element.addEventListener('blur', handleBlur);
  }, [announce]);

  // Skip link oluşturma
  const createSkipLink = useCallback((targetId: string, linkText: string): HTMLAnchorElement => {
    const skipLink = document.createElement('a');
    skipLink.href = `#${targetId}`;
    skipLink.textContent = linkText;
    skipLink.className = 'skip-link';

    // Skip link stilleri
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      background: #000;
      color: #fff;
      padding: 8px;
      text-decoration: none;
      border-radius: 4px;
      z-index: 9999;
      transition: top 0.3s;
    `;

    // Focus olduğunda görünür yap
    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px';
    });

    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px';
    });

    // Tıklandığında hedef elemente odaklan
    skipLink.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.getElementById(targetId);
      if (target) {
        manageFocus(target, `${linkText} bölümüne geçildi`);
      }
    });

    return skipLink;
  }, [manageFocus]);

  // Klavye navigasyon yardımcıları
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Alt + M: Ana içeriğe geç
      if (event.altKey && event.key === 'm') {
        event.preventDefault();
        const mainContent = document.querySelector('main, [role="main"], #main-content');
        if (mainContent instanceof HTMLElement) {
          manageFocus(mainContent, 'Ana içeriğe geçildi');
        }
      }

      // Alt + N: Navigasyona geç
      if (event.altKey && event.key === 'n') {
        event.preventDefault();
        const navigation = document.querySelector('nav, [role="navigation"]');
        if (navigation instanceof HTMLElement) {
          manageFocus(navigation, 'Navigasyona geçildi');
        }
      }

      // Alt + S: Arama kutusuna geç
      if (event.altKey && event.key === 's') {
        event.preventDefault();
        const searchInput = document.querySelector('input[type="search"], [role="searchbox"]');
        if (searchInput instanceof HTMLElement) {
          manageFocus(searchInput, 'Arama kutusuna geçildi');
        }
      }

      // Alt + H: Başlıklar listesi (gelecekte implement edilecek)
      if (event.altKey && event.key === 'h') {
        event.preventDefault();
        announce('Başlıklar listesi özelliği yakında eklenecek', 'polite');
      }
    };

    if (settings.keyboardNavigation) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [settings.keyboardNavigation, manageFocus, announce]);

  // Sayfa yüklendiğinde ilk odağı ayarla
  useEffect(() => {
    const setInitialFocus = () => {
      // Skip link'i sayfanın başına ekle
      const existingSkipLink = document.querySelector('.skip-link');
      if (!existingSkipLink) {
        const skipLink = createSkipLink('main-content', 'Ana içeriğe geç');
        document.body.insertBefore(skipLink, document.body.firstChild);
      }

      // Ana başlığa odaklan
      const mainHeading = document.querySelector('h1');
      if (mainHeading instanceof HTMLElement) {
        manageFocus(mainHeading, 'Sayfa yüklendi');
      }
    };

    if (document.readyState === 'complete') {
      setInitialFocus();
    } else {
      window.addEventListener('load', setInitialFocus);
      return () => window.removeEventListener('load', setInitialFocus);
    }
  }, [createSkipLink, manageFocus]);

  return {
    announce,
    announcePageChange,
    announceFormError,
    announceSuccess,
    announceLoading,
    announceContentChange,
    announceLandmark,
    manageFocus,
    createSkipLink,
    isScreenReaderActive: isScreenReaderActiveRef.current,
  };
};

export default useScreenReader;
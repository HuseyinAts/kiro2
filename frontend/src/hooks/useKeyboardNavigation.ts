/**
 * Klavye Navigasyon Hook'u
 * WCAG 2.1 Level AA uyumlu klavye navigasyonu
 */

import { useCallback, useEffect, useRef } from 'react';

import { useAccessibilitySettings } from './useAccessibilitySettings';

interface KeyboardNavigationHook {
  focusNext: () => void;
  focusPrevious: () => void;
  focusFirst: () => void;
  focusLast: () => void;
  trapFocus: (container: HTMLElement) => () => void;
  createFocusableElementsList: (container?: HTMLElement) => HTMLElement[];
  handleArrowNavigation: (
    event: KeyboardEvent,
    items: HTMLElement[],
    currentIndex: number,
    orientation?: 'horizontal' | 'vertical' | 'both'
  ) => number;
  announceCurrentFocus: () => void;
}

export const useKeyboardNavigation = (): KeyboardNavigationHook => {
  const { settings } = useAccessibilitySettings();
  const currentFocusIndex = useRef<number>(-1);
  const focusableElements = useRef<HTMLElement[]>([]);

  // Odaklanabilir elementlerin selector'ı
  const FOCUSABLE_SELECTORS = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
    'audio[controls]',
    'video[controls]',
    'details > summary',
    '[role="button"]:not([aria-disabled="true"])',
    '[role="link"]:not([aria-disabled="true"])',
    '[role="menuitem"]:not([aria-disabled="true"])',
    '[role="tab"]:not([aria-disabled="true"])',
    '[role="checkbox"]:not([aria-disabled="true"])',
    '[role="radio"]:not([aria-disabled="true"])',
    '[role="slider"]:not([aria-disabled="true"])',
    '[role="spinbutton"]:not([aria-disabled="true"])',
    '[role="textbox"]:not([aria-disabled="true"])',
  ].join(', ');

  // Odaklanabilir elementleri bul
  const createFocusableElementsList = useCallback((container: HTMLElement = document.body): HTMLElement[] => {
    const elements = Array.from(container.querySelectorAll(FOCUSABLE_SELECTORS)) as HTMLElement[];

    return elements.filter(element => {
      // Görünür ve erişilebilir elementleri filtrele
      const style = window.getComputedStyle(element);
      const isVisible = style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       style.opacity !== '0' &&
                       element.offsetWidth > 0 &&
                       element.offsetHeight > 0;

      const isAccessible = !element.hasAttribute('aria-hidden') ||
                          element.getAttribute('aria-hidden') !== 'true';

      return isVisible && isAccessible;
    });
  }, []);

  // Odaklanabilir elementleri güncelle
  const updateFocusableElements = useCallback(() => {
    focusableElements.current = createFocusableElementsList();
  }, [createFocusableElementsList]);

  // Mevcut odaklanmış elementin index'ini bul
  const getCurrentFocusIndex = useCallback((): number => {
    const activeElement = document.activeElement as HTMLElement;
    return focusableElements.current.indexOf(activeElement);
  }, []);

  // Sonraki elemente odaklan
  const focusNext = useCallback(() => {
    updateFocusableElements();
    const currentIndex = getCurrentFocusIndex();
    const nextIndex = (currentIndex + 1) % focusableElements.current.length;

    if (focusableElements.current[nextIndex]) {
      focusableElements.current[nextIndex].focus();
      currentFocusIndex.current = nextIndex;
    }
  }, [updateFocusableElements, getCurrentFocusIndex]);

  // Önceki elemente odaklan
  const focusPrevious = useCallback(() => {
    updateFocusableElements();
    const currentIndex = getCurrentFocusIndex();
    const previousIndex = currentIndex <= 0
      ? focusableElements.current.length - 1
      : currentIndex - 1;

    if (focusableElements.current[previousIndex]) {
      focusableElements.current[previousIndex].focus();
      currentFocusIndex.current = previousIndex;
    }
  }, [updateFocusableElements, getCurrentFocusIndex]);

  // İlk elemente odaklan
  const focusFirst = useCallback(() => {
    updateFocusableElements();
    if (focusableElements.current[0]) {
      focusableElements.current[0].focus();
      currentFocusIndex.current = 0;
    }
  }, [updateFocusableElements]);

  // Son elemente odaklan
  const focusLast = useCallback(() => {
    updateFocusableElements();
    const lastIndex = focusableElements.current.length - 1;
    if (focusableElements.current[lastIndex]) {
      focusableElements.current[lastIndex].focus();
      currentFocusIndex.current = lastIndex;
    }
  }, [updateFocusableElements]);

  // Focus trap (modal, dialog vb. için)
  const trapFocus = useCallback((container: HTMLElement): (() => void) => {
    const focusableInContainer = createFocusableElementsList(container);

    if (focusableInContainer.length === 0) {
      // Eğer odaklanabilir element yoksa container'ı kendisini odaklanabilir yap
      container.setAttribute('tabindex', '-1');
      container.focus();
      return () => {};
    }

    const firstElement = focusableInContainer[0];
    const lastElement = focusableInContainer[focusableInContainer.length - 1];

    // İlk elemente odaklan
    firstElement.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') {return;}

      if (event.shiftKey) {
        // Shift + Tab (geriye doğru)
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab (ileriye doğru)
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    // Event listener'ı ekle
    container.addEventListener('keydown', handleKeyDown);

    // Cleanup fonksiyonu
    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [createFocusableElementsList]);

  // Ok tuşları ile navigasyon
  const handleArrowNavigation = useCallback((
    event: KeyboardEvent,
    items: HTMLElement[],
    currentIndex: number,
    orientation: 'horizontal' | 'vertical' | 'both' = 'both',
  ): number => {
    let newIndex = currentIndex;

    switch (event.key) {
      case 'ArrowUp':
        if (orientation === 'vertical' || orientation === 'both') {
          event.preventDefault();
          newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        }
        break;

      case 'ArrowDown':
        if (orientation === 'vertical' || orientation === 'both') {
          event.preventDefault();
          newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        }
        break;

      case 'ArrowLeft':
        if (orientation === 'horizontal' || orientation === 'both') {
          event.preventDefault();
          newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        }
        break;

      case 'ArrowRight':
        if (orientation === 'horizontal' || orientation === 'both') {
          event.preventDefault();
          newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        }
        break;

      case 'Home':
        event.preventDefault();
        newIndex = 0;
        break;

      case 'End':
        event.preventDefault();
        newIndex = items.length - 1;
        break;

      case 'PageUp':
        event.preventDefault();
        newIndex = Math.max(0, currentIndex - 10);
        break;

      case 'PageDown':
        event.preventDefault();
        newIndex = Math.min(items.length - 1, currentIndex + 10);
        break;
    }

    // Yeni elemente odaklan
    if (newIndex !== currentIndex && items[newIndex]) {
      items[newIndex].focus();
    }

    return newIndex;
  }, []);

  // Mevcut odağı duyur
  const announceCurrentFocus = useCallback(() => {
    const activeElement = document.activeElement as HTMLElement;
    if (!activeElement) {return;}

    let announcement = '';

    // Element tipini belirle
    const tagName = activeElement.tagName.toLowerCase();
    const role = activeElement.getAttribute('role');
    const ariaLabel = activeElement.getAttribute('aria-label');
    const ariaLabelledBy = activeElement.getAttribute('aria-labelledby');

    // Label'ı bul
    let label = ariaLabel;
    if (!label && ariaLabelledBy) {
      const labelElement = document.getElementById(ariaLabelledBy);
      label = labelElement?.textContent || '';
    }
    if (!label && tagName === 'input') {
      const labelElement = document.querySelector(`label[for="${activeElement.id}"]`);
      label = labelElement?.textContent || '';
    }
    if (!label) {
      label = activeElement.textContent || '';
    }

    // Element tipini duyur
    const elementType = role || tagName;
    switch (elementType) {
      case 'button':
        announcement = `Buton: ${label}`;
        break;
      case 'link':
      case 'a':
        announcement = `Bağlantı: ${label}`;
        break;
      case 'input': {
        const inputType = (activeElement as HTMLInputElement).type;
        announcement = `${inputType === 'text' ? 'Metin kutusu' : inputType} girişi: ${label}`;
        break;
      }
      case 'select':
        announcement = `Seçim kutusu: ${label}`;
        break;
      case 'textarea':
        announcement = `Metin alanı: ${label}`;
        break;
      case 'checkbox': {
        const checked = (activeElement as HTMLInputElement).checked;
        announcement = `Onay kutusu: ${label}, ${checked ? 'işaretli' : 'işaretsiz'}`;
        break;
      }
      case 'radio': {
        const radioChecked = (activeElement as HTMLInputElement).checked;
        announcement = `Radyo düğmesi: ${label}, ${radioChecked ? 'seçili' : 'seçili değil'}`;
        break;
      }
      case 'tab':
        announcement = `Sekme: ${label}`;
        break;
      case 'menuitem':
        announcement = `Menü öğesi: ${label}`;
        break;
      default:
        announcement = label || 'İsimsiz element';
    }

    // Durumu duyur
    const ariaExpanded = activeElement.getAttribute('aria-expanded');
    if (ariaExpanded === 'true') {
      announcement += ', genişletilmiş';
    } else if (ariaExpanded === 'false') {
      announcement += ', daraltılmış';
    }

    const ariaSelected = activeElement.getAttribute('aria-selected');
    if (ariaSelected === 'true') {
      announcement += ', seçili';
    }

    const ariaDisabled = activeElement.getAttribute('aria-disabled');
    if (ariaDisabled === 'true' || (activeElement as HTMLInputElement).disabled) {
      announcement += ', devre dışı';
    }

    // Pozisyon bilgisi
    const ariaSetSize = activeElement.getAttribute('aria-setsize');
    const ariaPosInSet = activeElement.getAttribute('aria-posinset');
    if (ariaSetSize && ariaPosInSet) {
      announcement += `, ${ariaPosInSet} / ${ariaSetSize}`;
    }

    // Duyuruyu yap (live region kullanarak)
    const liveRegion = document.querySelector('[aria-live="polite"]');
    if (liveRegion) {
      liveRegion.textContent = announcement;
    }
  }, []);

  // Global klavye event listener'ları
  useEffect(() => {
    if (!settings.keyboardNavigation) {return;}

    const handleGlobalKeyDown = (event: KeyboardEvent) => {
      // Tab navigasyonu için özel işlemler
      if (event.key === 'Tab') {
        // Mevcut odağı güncelle
        setTimeout(() => {
          currentFocusIndex.current = getCurrentFocusIndex();
        }, 0);
      }

      // F6: Landmark'lar arası geçiş
      if (event.key === 'F6') {
        event.preventDefault();
        const landmarks = document.querySelectorAll(
          'main, nav, aside, header, footer, section, [role="main"], [role="navigation"], [role="complementary"], [role="banner"], [role="contentinfo"]',
        );

        if (landmarks.length > 0) {
          const currentLandmark = Array.from(landmarks).find(landmark =>
            landmark.contains(document.activeElement),
          );

          let nextIndex = 0;
          if (currentLandmark) {
            const currentIndex = Array.from(landmarks).indexOf(currentLandmark);
            nextIndex = (currentIndex + 1) % landmarks.length;
          }

          const nextLandmark = landmarks[nextIndex] as HTMLElement;
          if (nextLandmark) {
            nextLandmark.setAttribute('tabindex', '-1');
            nextLandmark.focus();
          }
        }
      }

      // Ctrl + Home: Sayfanın başına git
      if (event.ctrlKey && event.key === 'Home') {
        event.preventDefault();
        focusFirst();
      }

      // Ctrl + End: Sayfanın sonuna git
      if (event.ctrlKey && event.key === 'End') {
        event.preventDefault();
        focusLast();
      }
    };

    document.addEventListener('keydown', handleGlobalKeyDown);
    return () => document.removeEventListener('keydown', handleGlobalKeyDown);
  }, [settings.keyboardNavigation, getCurrentFocusIndex, focusFirst, focusLast]);

  // Focus değişikliklerini izle
  useEffect(() => {
    if (!settings.keyboardNavigation) {return;}

    const handleFocusChange = () => {
      // Odaklanabilir elementleri güncelle
      updateFocusableElements();

      // Mevcut odağı duyur (sadece klavye navigasyonu ile)
      if (document.activeElement && document.activeElement !== document.body) {
        setTimeout(() => {
          if (settings.screenReaderOptimized) {
            announceCurrentFocus();
          }
        }, 100);
      }
    };

    document.addEventListener('focusin', handleFocusChange);
    return () => document.removeEventListener('focusin', handleFocusChange);
  }, [settings.keyboardNavigation, settings.screenReaderOptimized, updateFocusableElements, announceCurrentFocus]);

  // Sayfa yüklendiğinde odaklanabilir elementleri güncelle
  useEffect(() => {
    updateFocusableElements();
  }, [updateFocusableElements]);

  return {
    focusNext,
    focusPrevious,
    focusFirst,
    focusLast,
    trapFocus,
    createFocusableElementsList,
    handleArrowNavigation,
    announceCurrentFocus,
  };
};

export default useKeyboardNavigation;
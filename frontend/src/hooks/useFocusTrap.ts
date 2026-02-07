/**
 * useFocusTrap Hook
 * Traps keyboard focus within a container (for modals, dialogs, etc.)
 * WCAG 2.1 compliant focus management
 */

import { useEffect, useRef, RefObject } from 'react';

interface UseFocusTrapOptions {
  /**
   * Whether the focus trap is active
   */
  enabled?: boolean;

  /**
   * Auto-focus the first focusable element on mount
   */
  autoFocus?: boolean;

  /**
   * Element to focus when trap is enabled
   */
  initialFocus?: HTMLElement | null;

  /**
   * Element to focus when trap is disabled
   */
  returnFocus?: HTMLElement | null;

  /**
   * Allow ESC key to deactivate trap
   */
  escapeDeactivates?: boolean;

  /**
   * Callback when ESC is pressed
   */
  onEscape?: () => void;
}

/**
 * Get all focusable elements within a container
 */
const getFocusableElements = (container: HTMLElement): HTMLElement[] => {
  const focusableSelectors = [
    'a[href]',
    'area[href]',
    'input:not([disabled]):not([type="hidden"])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    'button:not([disabled])',
    'iframe',
    'object',
    'embed',
    '[contenteditable]',
    '[tabindex]:not([tabindex="-1"])',
  ];

  const elements = container.querySelectorAll<HTMLElement>(focusableSelectors.join(','));

  return Array.from(elements).filter((element) => {
    // Check if element is visible
    const style = window.getComputedStyle(element);
    return (
      style.display !== 'none' &&
      style.visibility !== 'hidden' &&
      element.offsetParent !== null
    );
  });
};

/**
 * Focus trap hook for modals and dialogs
 */
export const useFocusTrap = <T extends HTMLElement = HTMLDivElement>(
  options: UseFocusTrapOptions = {},
): RefObject<T> => {
  const {
    enabled = true,
    autoFocus = true,
    initialFocus,
    returnFocus,
    escapeDeactivates = true,
    onEscape,
  } = options;

  const containerRef = useRef<T>(null);
  const previouslyFocusedElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!enabled || !containerRef.current) {
      return;
    }

    const container = containerRef.current;

    // Save currently focused element to return focus later
    previouslyFocusedElement.current = document.activeElement as HTMLElement;

    // Focus initial element
    if (autoFocus) {
      if (initialFocus) {
        initialFocus.focus();
      } else {
        const focusableElements = getFocusableElements(container);
        if (focusableElements.length > 0) {
          focusableElements[0].focus();
        }
      }
    }

    // Handle Tab key navigation
    const handleKeyDown = (event: KeyboardEvent) => {
      // ESC key
      if (escapeDeactivates && event.key === 'Escape') {
        event.preventDefault();
        if (onEscape) {
          onEscape();
        }
        return;
      }

      // Tab key
      if (event.key === 'Tab') {
        const focusableElements = getFocusableElements(container);

        if (focusableElements.length === 0) {
          event.preventDefault();
          return;
        }

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        const activeElement = document.activeElement as HTMLElement;

        // Shift + Tab (backwards)
        if (event.shiftKey) {
          if (activeElement === firstElement || !container.contains(activeElement)) {
            event.preventDefault();
            lastElement.focus();
          }
        }
        // Tab (forwards)
        else {
          if (activeElement === lastElement || !container.contains(activeElement)) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    // Add event listener
    document.addEventListener('keydown', handleKeyDown);

    // Cleanup
    return () => {
      document.removeEventListener('keydown', handleKeyDown);

      // Return focus to previously focused element
      const elementToFocus = returnFocus || previouslyFocusedElement.current;
      if (elementToFocus && document.body.contains(elementToFocus)) {
        elementToFocus.focus();
      }
    };
  }, [enabled, autoFocus, initialFocus, returnFocus, escapeDeactivates, onEscape]);

  return containerRef;
};

/**
 * Example Usage:
 *
 * const Modal = ({ isOpen, onClose }) => {
 *   const trapRef = useFocusTrap<HTMLDivElement>({
 *     enabled: isOpen,
 *     escapeDeactivates: true,
 *     onEscape: onClose,
 *   });
 *
 *   if (!isOpen) return null;
 *
 *   return (
 *     <div ref={trapRef} role="dialog" aria-modal="true">
 *       <h2>Modal Title</h2>
 *       <button onClick={onClose}>Close</button>
 *     </div>
 *   );
 * };
 */

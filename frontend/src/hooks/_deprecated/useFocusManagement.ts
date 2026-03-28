/**
 * useFocusManagement Hook
 * Advanced focus management utilities for forms and interactive elements
 */

import { useRef, useEffect, useCallback } from 'react';

interface UseFocusManagementOptions {
  /**
   * Auto-focus on mount
   */
  autoFocus?: boolean;

  /**
   * Select text content on focus (for input fields)
   */
  selectOnFocus?: boolean;

  /**
   * Focus on a specific condition
   */
  focusWhen?: boolean;
}

/**
 * Basic focus management hook
 */
export const useFocusManagement = <T extends HTMLElement>(
  options: UseFocusManagementOptions = {},
) => {
  const { autoFocus = false, selectOnFocus = false, focusWhen } = options;
  const elementRef = useRef<T>(null);

  useEffect(() => {
    if ((autoFocus || focusWhen) && elementRef.current) {
      elementRef.current.focus();

      if (selectOnFocus && elementRef.current instanceof HTMLInputElement) {
        elementRef.current.select();
      }
    }
  }, [autoFocus, selectOnFocus, focusWhen]);

  const focus = useCallback(() => {
    if (elementRef.current) {
      elementRef.current.focus();
    }
  }, []);

  const blur = useCallback(() => {
    if (elementRef.current) {
      elementRef.current.blur();
    }
  }, []);

  return { ref: elementRef, focus, blur };
};

/**
 * Hook to manage focus on first error in form validation
 */
export const useFocusOnError = () => {
  const focusFirstError = useCallback((errors: Record<string, any>) => {
    const firstErrorField = Object.keys(errors)[0];
    if (firstErrorField) {
      const element = document.querySelector<HTMLElement>(
        `[name="${firstErrorField}"], #${firstErrorField}`,
      );
      if (element) {
        element.focus();
        if (element instanceof HTMLInputElement) {
          element.select();
        }
      }
    }
  }, []);

  return { focusFirstError };
};

/**
 * Hook to manage focus sequence (for multi-step forms, wizards)
 */
export const useFocusSequence = (sequence: string[]) => {
  const currentIndex = useRef(0);

  const focusNext = useCallback(() => {
    currentIndex.current = Math.min(currentIndex.current + 1, sequence.length - 1);
    const nextId = sequence[currentIndex.current];
    const element = document.querySelector<HTMLElement>(`#${nextId}, [name="${nextId}"]`);
    if (element) {
      element.focus();
    }
  }, [sequence]);

  const focusPrevious = useCallback(() => {
    currentIndex.current = Math.max(currentIndex.current - 1, 0);
    const prevId = sequence[currentIndex.current];
    const element = document.querySelector<HTMLElement>(`#${prevId}, [name="${prevId}"]`);
    if (element) {
      element.focus();
    }
  }, [sequence]);

  const focusIndex = useCallback(
    (index: number) => {
      if (index >= 0 && index < sequence.length) {
        currentIndex.current = index;
        const id = sequence[index];
        const element = document.querySelector<HTMLElement>(`#${id}, [name="${id}"]`);
        if (element) {
          element.focus();
        }
      }
    },
    [sequence],
  );

  return { focusNext, focusPrevious, focusIndex, currentIndex: currentIndex.current };
};

/**
 * Hook to restore focus after an action (like closing a modal)
 */
export const useRestoreFocus = () => {
  const previousFocus = useRef<HTMLElement | null>(null);

  const saveFocus = useCallback(() => {
    previousFocus.current = document.activeElement as HTMLElement;
  }, []);

  const restoreFocus = useCallback(() => {
    if (previousFocus.current && document.body.contains(previousFocus.current)) {
      previousFocus.current.focus();
      previousFocus.current = null;
    }
  }, []);

  return { saveFocus, restoreFocus };
};

/**
 * Hook for skip links (accessibility feature)
 */
export const useSkipLink = () => {
  const skipToContent = useCallback((targetId: string) => {
    const target = document.getElementById(targetId);
    if (target) {
      target.tabIndex = -1;
      target.focus();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  return { skipToContent };
};

/**
 * Hook to prevent focus on disabled state
 */
export const useFocusDisabled = (disabled: boolean) => {
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (disabled && elementRef.current && elementRef.current === document.activeElement) {
      elementRef.current.blur();
    }
  }, [disabled]);

  return elementRef;
};

/**
 * Example Usage:
 *
 * // Basic focus management
 * const MyInput = () => {
 *   const { ref, focus } = useFocusManagement<HTMLInputElement>({
 *     autoFocus: true,
 *     selectOnFocus: true,
 *   });
 *
 *   return <input ref={ref} />;
 * };
 *
 * // Focus on first error
 * const MyForm = () => {
 *   const { focusFirstError } = useFocusOnError();
 *
 *   const handleSubmit = (values) => {
 *     const errors = validate(values);
 *     if (Object.keys(errors).length > 0) {
 *       focusFirstError(errors);
 *     }
 *   };
 * };
 *
 * // Multi-step form
 * const Wizard = () => {
 *   const { focusNext, focusPrevious } = useFocusSequence(['step1', 'step2', 'step3']);
 *
 *   return (
 *     <>
 *       <button onClick={focusPrevious}>Previous</button>
 *       <button onClick={focusNext}>Next</button>
 *     </>
 *   );
 * };
 *
 * // Modal with focus restoration
 * const Modal = ({ isOpen, onClose }) => {
 *   const { saveFocus, restoreFocus } = useRestoreFocus();
 *
 *   useEffect(() => {
 *     if (isOpen) {
 *       saveFocus();
 *     }
 *   }, [isOpen]);
 *
 *   const handleClose = () => {
 *     restoreFocus();
 *     onClose();
 *   };
 * };
 */

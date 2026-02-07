/**
 * Exam Keyboard Navigation Hook
 *
 * Provides keyboard shortcuts for exam navigation:
 * - Arrow Left/Right: Navigate between questions
 * - 1-5 keys: Select answer options A-E
 * - Enter: Confirm answer / Go to next question
 * - F: Flag/unflag current question
 * - Escape: Open exit dialog
 *
 * ACCESSIBILITY: Supports keyboard-only navigation for WCAG 2.1 AA compliance
 */

import { useEffect, useCallback } from 'react';

export interface ExamKeyboardOptions {
  /** Callback for navigating to next question */
  onNextQuestion: () => void
  /** Callback for navigating to previous question */
  onPreviousQuestion: () => void
  /** Callback for selecting an answer option (A=0, B=1, C=2, D=3, E=4) */
  onSelectOption: (optionIndex: number) => void
  /** Callback for flagging/unflagging current question */
  onToggleFlag: () => void
  /** Callback for opening exit dialog */
  onOpenExitDialog: () => void
  /** Callback for confirming current answer */
  onConfirmAnswer?: () => void
  /** Whether keyboard navigation is disabled (e.g., during submission) */
  disabled?: boolean
  /** Whether user is at first question */
  isFirstQuestion?: boolean
  /** Whether user is at last question */
  isLastQuestion?: boolean
  /** Number of available options (default: 5 for A-E) */
  optionCount?: number
}

/**
 * Hook for exam keyboard navigation
 *
 * @example
 * ```tsx
 * useExamKeyboard({
 *   onNextQuestion: () => handleNext(),
 *   onPreviousQuestion: () => handlePrev(),
 *   onSelectOption: (index) => selectAnswer(index),
 *   onToggleFlag: () => toggleFlag(),
 *   onOpenExitDialog: () => setShowExitDialog(true),
 *   disabled: isSubmitting,
 *   isFirstQuestion: currentIndex === 0,
 *   isLastQuestion: currentIndex === totalQuestions - 1
 * })
 * ```
 */
export function useExamKeyboard(options: ExamKeyboardOptions): void {
  const {
    onNextQuestion,
    onPreviousQuestion,
    onSelectOption,
    onToggleFlag,
    onOpenExitDialog,
    onConfirmAnswer,
    disabled = false,
    isFirstQuestion = false,
    isLastQuestion = false,
    optionCount = 5,
  } = options;

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Don't handle keys when disabled or when user is typing in an input
    if (disabled) {return;}

    const target = event.target as HTMLElement;
    const isInputElement = target.tagName === 'INPUT' ||
                          target.tagName === 'TEXTAREA' ||
                          target.isContentEditable;

    // Allow certain keys even in input elements
    const alwaysAllowedKeys = ['Escape'];

    if (isInputElement && !alwaysAllowedKeys.includes(event.key)) {
      return;
    }

    switch (event.key) {
      // Navigation: Arrow keys
      case 'ArrowRight':
        if (!isLastQuestion) {
          event.preventDefault();
          onNextQuestion();
        }
        break;

      case 'ArrowLeft':
        if (!isFirstQuestion) {
          event.preventDefault();
          onPreviousQuestion();
        }
        break;

      // Option selection: Number keys 1-5
      case '1':
      case '2':
      case '3':
      case '4':
      case '5': {
        const optionIndex = parseInt(event.key) - 1;
        if (optionIndex < optionCount) {
          event.preventDefault();
          onSelectOption(optionIndex);
        }
        break;
      }

      // Option selection: Letter keys A-E (alternative)
      case 'a':
      case 'A':
        event.preventDefault();
        onSelectOption(0);
        break;
      case 'b':
      case 'B':
        event.preventDefault();
        onSelectOption(1);
        break;
      case 'c':
      case 'C':
        event.preventDefault();
        onSelectOption(2);
        break;
      case 'd':
      case 'D':
        event.preventDefault();
        onSelectOption(3);
        break;
      case 'e':
      case 'E':
        if (optionCount >= 5) {
          event.preventDefault();
          onSelectOption(4);
        }
        break;

      // Confirm: Enter key
      case 'Enter':
        if (onConfirmAnswer) {
          event.preventDefault();
          onConfirmAnswer();
        } else if (!isLastQuestion) {
          event.preventDefault();
          onNextQuestion();
        }
        break;

      // Flag: F key
      case 'f':
      case 'F':
        event.preventDefault();
        onToggleFlag();
        break;

      // Exit: Escape key
      case 'Escape':
        event.preventDefault();
        onOpenExitDialog();
        break;

      // Help: ? key (optional - could show keyboard shortcuts dialog)
      case '?':
        // Could implement help dialog here
        break;

      default:
        // Ignore other keys
        break;
    }
  }, [
    disabled,
    isFirstQuestion,
    isLastQuestion,
    optionCount,
    onNextQuestion,
    onPreviousQuestion,
    onSelectOption,
    onToggleFlag,
    onOpenExitDialog,
    onConfirmAnswer,
  ]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
}

/**
 * Keyboard shortcuts help text (Turkish)
 * Can be displayed in a help dialog
 */
export const EXAM_KEYBOARD_SHORTCUTS = [
  { key: '← / →', description: 'Önceki / Sonraki soru' },
  { key: '1-5 veya A-E', description: 'Cevap seçeneği seç' },
  { key: 'Enter', description: 'Sonraki soruya geç' },
  { key: 'F', description: 'Soruyu işaretle/işareti kaldır' },
  { key: 'Escape', description: 'Çıkış menüsünü aç' },
] as const;

export default useExamKeyboard;

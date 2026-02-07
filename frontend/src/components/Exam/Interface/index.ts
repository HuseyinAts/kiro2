/**
 * Exam Interface Components Barrel Export
 *
 * Central export for exam interface components
 * Refactored from OSYMExamInterface.tsx (2025-01-24)
 */

// Header
export { ExamHeader } from './ExamHeader';
export type { ExamHeaderProps } from './ExamHeader';

// Question Panel
export { QuestionPanel } from './QuestionPanel';
export type { QuestionPanelProps } from './QuestionPanel';

// Answer Panel
export { AnswerPanel } from './AnswerPanel';
export type { AnswerPanelProps, AnswerOption } from './AnswerPanel';

// Navigation
export { ExamNavigation } from './ExamNavigation';
export type { ExamNavigationProps, QuestionStatus } from './ExamNavigation';

// Dialogs
export { ExamSubmitDialog, ExamExitDialog } from './ExamDialogs';
export type { ExamSubmitDialogProps, ExamExitDialogProps } from './ExamDialogs';

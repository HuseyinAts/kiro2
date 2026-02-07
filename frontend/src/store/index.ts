/**
 * Central Store Exports
 *
 * Single entry point for all Zustand stores
 * Makes imports cleaner throughout the application
 *
 * STATE MANAGEMENT ARCHITECTURE (2025-01-24):
 * Bu proje 5 Zustand store kullaniyor. Hiyerarsi:
 *
 * 1. CORE STORES:
 *    - authStore.ts - Authentication state (user, tokens, login/logout)
 *    - examStore.ts - Exam session state (questions, answers, timer)
 *    - settingsStore.ts - User preferences (accessibility, display)
 *
 * 2. UI STORES:
 *    - uiStore.ts - UI state (sidebar, toasts, loading, theme)
 *    - notificationStore.ts - Notifications and alerts
 *
 * 3. CONTEXT (Legacy - Passthrough):
 *    - context/AuthProvider.tsx - Backward compat wrapper
 *
 * IMPORTANT: Yeni state icin:
 * - Global state: Bu store'lardan birini kullan
 * - Component-local state: useState kullan
 * - Server state: React Query (hooks/queries/) kullan
 * - localStorage: settingsStore.persist ile yonet
 *
 * @example
 * import { useAuthStore, useExamStore, useUIStore, useSettingsStore } from '@/store'
 */

// Auth Store
export {
  useAuthStore,
  useUser,
  useIsAuthenticated,
  useAuthLoading,
  useAuthError,
} from './authStore';

export type { default as AuthStore } from './authStore';

// Exam Store
export {
  useExamStore,
  useExamSession,
  useCurrentQuestion,
  useExamPerformance,
  useExamTimer,
  useExamLoading,
  useExamAnswers,
  useFlaggedQuestions,
} from './examStore';

export type { default as ExamStore } from './examStore';

// UI Store
export {
  useUIStore,
  useSidebarOpen,
  useSidebarCollapsed,
  useMobileSidebarOpen,
  useToasts,
  useGlobalLoading,
  usePageLoading,
  useBreadcrumbs,
  usePageTitle,
  useIsDarkMode,
  useIsFullscreen,
  useSearchQuery,
} from './uiStore';

export type {
  default as UIStore,
  Toast,
  Modal,
  Breadcrumb,
  NotificationType,
} from './uiStore';

// Settings Store
export {
  useSettingsStore,
  useAccessibilitySettings,
  useDisplaySettings,
  useNotificationSettings,
  usePrivacySettings,
  useExamSettings,
  useDyslexiaMode,
  useDyscalculiaMode,
  useFontSize,
  useLanguage,
  useAutoSaveInterval,
} from './settingsStore';

export type {
  default as SettingsStore,
  AccessibilitySettings,
  DisplaySettings,
  NotificationSettings,
  PrivacySettings,
  ExamSettings,
} from './settingsStore';

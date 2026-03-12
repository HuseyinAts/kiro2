/**
 * Settings Store (Zustand)
 *
 * Centralized user preferences and accessibility settings
 * Manages all user-configurable options with persistent storage
 *
 * Features:
 * - Accessibility settings (dyslexia, dyscalculia, color blind modes)
 * - Language preferences
 * - Notification settings
 * - Display preferences (font size, contrast, animations)
 * - Audio/Speech settings
 * - Privacy preferences
 * - Persistent storage with localStorage
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

// Accessibility settings
export interface AccessibilitySettings {
  // Dyslexia support
  dyslexiaMode: boolean
  dyslexiaFont: 'opendyslexic' | 'comic-sans' | 'arial' | 'default'
  letterSpacing: number // 0-5
  lineHeight: number // 1.0-2.0
  wordSpacing: number // 0-5

  // Dyscalculia support
  dyscalculiaMode: boolean
  visualCalculator: boolean
  stepByStepSolutions: boolean
  colorCodedNumbers: boolean

  // Visual accessibility
  highContrast: boolean
  darkMode: boolean
  colorBlindMode: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia'
  fontSize: number // 12-24
  cursorSize: 'small' | 'medium' | 'large'

  // Motion & Animations
  reduceMotion: boolean
  disableAnimations: boolean

  // Screen reader
  screenReaderEnabled: boolean
  textToSpeech: boolean
  speechRate: number // 0.5-2.0
  speechVolume: number // 0-1

  // Keyboard navigation
  keyboardNavigation: boolean
  focusHighlight: boolean
}

// Display preferences
export interface DisplaySettings {
  language: 'tr' | 'en'
  dateFormat: 'dd/MM/yyyy' | 'MM/dd/yyyy' | 'yyyy-MM-dd'
  timeFormat: '12h' | '24h'
  timezone: string
  compactView: boolean
  showHints: boolean
  showProgressBars: boolean
}

// Notification preferences
export interface NotificationSettings {
  enableNotifications: boolean
  emailNotifications: boolean
  pushNotifications: boolean
  soundEnabled: boolean
  notifyOnNewMessage: boolean
  notifyOnExamReminder: boolean
  notifyOnGoalProgress: boolean
  notifyOnAchievement: boolean
  quietHoursEnabled: boolean
  quietHoursStart: string // HH:mm
  quietHoursEnd: string // HH:mm
}

// Privacy settings
export interface PrivacySettings {
  showOnlineStatus: boolean
  allowAnalytics: boolean
  allowPerformanceTracking: boolean
  shareProgressWithTeachers: boolean
  shareProgressWithParents: boolean
  publicProfile: boolean
}

// Exam preferences
export interface ExamSettings {
  autoSaveInterval: number // seconds
  showTimer: boolean
  showProgressIndicator: boolean
  confirmBeforeSubmit: boolean
  flaggedQuestionsReminder: boolean
  calculatorEnabled: boolean
  formulaSheetEnabled: boolean
}

interface SettingsState {
  accessibility: AccessibilitySettings
  display: DisplaySettings
  notifications: NotificationSettings
  privacy: PrivacySettings
  exam: ExamSettings
  initialized: boolean
}

interface SettingsActions {
  // Accessibility actions
  updateAccessibility: (settings: Partial<AccessibilitySettings>) => void
  toggleDyslexiaMode: () => void
  toggleDyscalculiaMode: () => void
  toggleHighContrast: () => void
  toggleReduceMotion: () => void
  setFontSize: (size: number) => void
  setLineHeight: (height: number) => void
  setColorBlindMode: (mode: AccessibilitySettings['colorBlindMode']) => void

  // Display actions
  updateDisplay: (settings: Partial<DisplaySettings>) => void
  setLanguage: (language: 'tr' | 'en') => void
  toggleCompactView: () => void

  // Notification actions
  updateNotifications: (settings: Partial<NotificationSettings>) => void
  toggleNotifications: () => void
  toggleSoundEnabled: () => void

  // Privacy actions
  updatePrivacy: (settings: Partial<PrivacySettings>) => void
  toggleAnalytics: () => void

  // Exam actions
  updateExam: (settings: Partial<ExamSettings>) => void
  setAutoSaveInterval: (interval: number) => void

  // Bulk actions
  resetToDefaults: () => void
  importSettings: (settings: Partial<SettingsState>) => void
  exportSettings: () => SettingsState

  // Initialization
  initialize: () => void
}

type SettingsStore = SettingsState & SettingsActions

const defaultAccessibilitySettings: AccessibilitySettings = {
  dyslexiaMode: false,
  dyslexiaFont: 'default',
  letterSpacing: 0,
  lineHeight: 1.5,
  wordSpacing: 0,
  dyscalculiaMode: false,
  visualCalculator: false,
  stepByStepSolutions: false,
  colorCodedNumbers: false,
  highContrast: false,
  darkMode: false,
  colorBlindMode: 'none',
  fontSize: 16,
  cursorSize: 'medium',
  reduceMotion: false,
  disableAnimations: false,
  screenReaderEnabled: false,
  textToSpeech: false,
  speechRate: 1.0,
  speechVolume: 1.0,
  keyboardNavigation: true,
  focusHighlight: true,
};

const defaultDisplaySettings: DisplaySettings = {
  language: 'tr',
  dateFormat: 'dd/MM/yyyy',
  timeFormat: '24h',
  timezone: 'Europe/Istanbul',
  compactView: false,
  showHints: true,
  showProgressBars: true,
};

const defaultNotificationSettings: NotificationSettings = {
  enableNotifications: true,
  emailNotifications: true,
  pushNotifications: false,
  soundEnabled: true,
  notifyOnNewMessage: true,
  notifyOnExamReminder: true,
  notifyOnGoalProgress: true,
  notifyOnAchievement: true,
  quietHoursEnabled: false,
  quietHoursStart: '22:00',
  quietHoursEnd: '07:00',
};

const defaultPrivacySettings: PrivacySettings = {
  showOnlineStatus: true,
  allowAnalytics: true,
  allowPerformanceTracking: true,
  shareProgressWithTeachers: true,
  shareProgressWithParents: true,
  publicProfile: false,
};

const defaultExamSettings: ExamSettings = {
  autoSaveInterval: 30,
  showTimer: true,
  showProgressIndicator: true,
  confirmBeforeSubmit: true,
  flaggedQuestionsReminder: true,
  calculatorEnabled: true,
  formulaSheetEnabled: true,
};

const initialState: SettingsState = {
  accessibility: defaultAccessibilitySettings,
  display: defaultDisplaySettings,
  notifications: defaultNotificationSettings,
  privacy: defaultPrivacySettings,
  exam: defaultExamSettings,
  initialized: false,
};

export const useSettingsStore = create<SettingsStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Initialize settings (can load from server or detect system preferences)
        initialize: () => {
          // Detect system dark mode preference
          if (typeof window !== 'undefined' && window.matchMedia) {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

            set((state) => ({
              accessibility: {
                ...state.accessibility,
                darkMode: state.accessibility.darkMode || prefersDark,
                reduceMotion: state.accessibility.reduceMotion || prefersReducedMotion,
              },
              initialized: true,
            }));
          } else {
            set({ initialized: true });
          }
        },

        // Accessibility actions
        updateAccessibility: (settings: Partial<AccessibilitySettings>) => {
          set((state) => ({
            accessibility: { ...state.accessibility, ...settings },
          }));
        },

        toggleDyslexiaMode: () => {
          set((state) => ({
            accessibility: {
              ...state.accessibility,
              dyslexiaMode: !state.accessibility.dyslexiaMode,
            },
          }));
        },

        toggleDyscalculiaMode: () => {
          set((state) => ({
            accessibility: {
              ...state.accessibility,
              dyscalculiaMode: !state.accessibility.dyscalculiaMode,
            },
          }));
        },

        toggleHighContrast: () => {
          set((state) => ({
            accessibility: {
              ...state.accessibility,
              highContrast: !state.accessibility.highContrast,
            },
          }));
        },

        toggleReduceMotion: () => {
          set((state) => ({
            accessibility: {
              ...state.accessibility,
              reduceMotion: !state.accessibility.reduceMotion,
            },
          }));
        },

        setFontSize: (size: number) => {
          const clampedSize = Math.max(12, Math.min(24, size));
          set((state) => ({
            accessibility: {
              ...state.accessibility,
              fontSize: clampedSize,
            },
          }));
        },

        setLineHeight: (height: number) => {
          const clamped = Math.max(1.0, Math.min(2.0, height));
          set((state) => ({
            accessibility: {
              ...state.accessibility,
              lineHeight: clamped,
            },
          }));
        },

        setColorBlindMode: (mode: AccessibilitySettings['colorBlindMode']) => {
          set((state) => ({
            accessibility: {
              ...state.accessibility,
              colorBlindMode: mode,
            },
          }));
        },

        // Display actions
        updateDisplay: (settings: Partial<DisplaySettings>) => {
          set((state) => ({
            display: { ...state.display, ...settings },
          }));
        },

        setLanguage: (language: 'tr' | 'en') => {
          set((state) => ({
            display: { ...state.display, language },
          }));

          // Update HTML lang attribute
          if (typeof document !== 'undefined') {
            document.documentElement.lang = language;
          }
        },

        toggleCompactView: () => {
          set((state) => ({
            display: {
              ...state.display,
              compactView: !state.display.compactView,
            },
          }));
        },

        // Notification actions
        updateNotifications: (settings: Partial<NotificationSettings>) => {
          set((state) => ({
            notifications: { ...state.notifications, ...settings },
          }));
        },

        toggleNotifications: () => {
          set((state) => ({
            notifications: {
              ...state.notifications,
              enableNotifications: !state.notifications.enableNotifications,
            },
          }));
        },

        toggleSoundEnabled: () => {
          set((state) => ({
            notifications: {
              ...state.notifications,
              soundEnabled: !state.notifications.soundEnabled,
            },
          }));
        },

        // Privacy actions
        updatePrivacy: (settings: Partial<PrivacySettings>) => {
          set((state) => ({
            privacy: { ...state.privacy, ...settings },
          }));
        },

        toggleAnalytics: () => {
          set((state) => ({
            privacy: {
              ...state.privacy,
              allowAnalytics: !state.privacy.allowAnalytics,
            },
          }));
        },

        // Exam actions
        updateExam: (settings: Partial<ExamSettings>) => {
          set((state) => ({
            exam: { ...state.exam, ...settings },
          }));
        },

        setAutoSaveInterval: (interval: number) => {
          const clampedInterval = Math.max(10, Math.min(300, interval));
          set((state) => ({
            exam: {
              ...state.exam,
              autoSaveInterval: clampedInterval,
            },
          }));
        },

        // Bulk actions
        resetToDefaults: () => {
          set(initialState);
        },

        importSettings: (settings: Partial<SettingsState>) => {
          set((state) => ({
            ...state,
            ...settings,
          }));
        },

        exportSettings: (): SettingsState => {
          return get();
        },
      }),
      {
        name: 'settings-storage',
        version: 1,
      },
    ),
    { name: 'SettingsStore' },
  ),
);

/**
 * Selector hooks for better performance
 */
export const useAccessibilitySettings = () => useSettingsStore((state) => state.accessibility);
export const useDisplaySettings = () => useSettingsStore((state) => state.display);
export const useNotificationSettings = () => useSettingsStore((state) => state.notifications);
export const usePrivacySettings = () => useSettingsStore((state) => state.privacy);
export const useExamSettings = () => useSettingsStore((state) => state.exam);

// Specific accessors for commonly used settings
export const useDyslexiaMode = () => useSettingsStore((state) => state.accessibility.dyslexiaMode);
export const useDyscalculiaMode = () => useSettingsStore((state) => state.accessibility.dyscalculiaMode);
export const useFontSize = () => useSettingsStore((state) => state.accessibility.fontSize);
export const useLanguage = () => useSettingsStore((state) => state.display.language);
export const useAutoSaveInterval = () => useSettingsStore((state) => state.exam.autoSaveInterval);

export default useSettingsStore;

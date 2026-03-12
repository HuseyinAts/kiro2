/**
 * useNeurodiversityPrefs — F17 extended neurodiversity preferences
 *
 * Manages prefs that are not (yet) part of the Zustand settingsStore:
 *   - focusMode       Single question per screen (ADHD-friendly)
 *   - persistentTimer Always-visible countdown during exams/quizzes
 *   - showBreadcrumb  "Where am I?" breadcrumb navigation bar
 *
 * fontSize and lineHeight are owned by settingsStore.accessibility and are
 * NOT included here — use useSettingsStore / useFontSize for those.
 *
 * Persists to localStorage under the key 'kiro2-neurodiversity-ext'.
 */

import { useEffect, useState } from 'react';

export interface NeurodiversityExtPrefs {
  /** Show only one question per screen — ADHD-friendly focus mode. */
  focusMode: boolean;
  /** Always-visible countdown timer during exam/quiz sessions. */
  persistentTimer: boolean;
  /** "Where am I?" breadcrumb navigation bar. */
  showBreadcrumb: boolean;
}

const STORAGE_KEY = 'kiro2-neurodiversity-ext';

const DEFAULTS: NeurodiversityExtPrefs = {
  focusMode: false,
  persistentTimer: false,
  showBreadcrumb: true,
};

export function useNeurodiversityPrefs(): {
  prefs: NeurodiversityExtPrefs;
  setPrefs: React.Dispatch<React.SetStateAction<NeurodiversityExtPrefs>>;
} {
  const [prefs, setPrefs] = useState<NeurodiversityExtPrefs>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return { ...DEFAULTS, ...(JSON.parse(stored) as Partial<NeurodiversityExtPrefs>) };
      }
    } catch {
      // Malformed JSON — fall through to defaults.
    }
    return DEFAULTS;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  }, [prefs]);

  return { prefs, setPrefs };
}

export default useNeurodiversityPrefs;

/**
 * Difficulty Translation Utility
 *
 * Converts between Turkish and English difficulty levels
 * Backend uses Turkish: kolay, orta, zor
 * Frontend uses English: beginner, intermediate, advanced
 */

export type DifficultyTurkish = 'kolay' | 'orta' | 'zor';
export type DifficultyEnglish = 'beginner' | 'intermediate' | 'advanced';

/**
 * Convert English difficulty to Turkish for backend API calls
 */
export function difficultyToTurkish(difficulty: DifficultyEnglish): DifficultyTurkish {
  const mapping: Record<DifficultyEnglish, DifficultyTurkish> = {
    'beginner': 'kolay',
    'intermediate': 'orta',
    'advanced': 'zor'
  };

  return mapping[difficulty] || 'orta'; // Default to 'orta' if unknown
}

/**
 * Convert Turkish difficulty to English for frontend display
 */
export function difficultyToEnglish(difficulty: DifficultyTurkish): DifficultyEnglish {
  const mapping: Record<DifficultyTurkish, DifficultyEnglish> = {
    'kolay': 'beginner',
    'orta': 'intermediate',
    'zor': 'advanced'
  };

  return mapping[difficulty] || 'intermediate'; // Default to 'intermediate' if unknown
}

/**
 * Get Turkish display text for difficulty
 */
export function getDifficultyLabel(difficulty: DifficultyEnglish | DifficultyTurkish): string {
  const labels: Record<string, string> = {
    'beginner': 'Kolay',
    'intermediate': 'Orta',
    'advanced': 'Zor',
    'kolay': 'Kolay',
    'orta': 'Orta',
    'zor': 'Zor'
  };

  return labels[difficulty] || 'Orta';
}

/**
 * Get color for difficulty level
 */
export function getDifficultyColor(difficulty: DifficultyEnglish | DifficultyTurkish): 'success' | 'warning' | 'error' {
  const isEasy = difficulty === 'beginner' || difficulty === 'kolay';
  const isMedium = difficulty === 'intermediate' || difficulty === 'orta';

  if (isEasy) return 'success';
  if (isMedium) return 'warning';
  return 'error';
}

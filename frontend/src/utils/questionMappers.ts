/**
 * API soru formatı → QuizInterface.Question dönüştürücü
 *
 * Backend _serialize_question() formatı ile QuizInterface.Question
 * interface'i uyumsuz. Bu mapper aradaki farkları kapatır:
 * - question_text → question
 * - options dict {A,B,C,D,E} → string[] array
 * - difficulty_level (KOLAY...) → difficulty (easy/medium/hard)
 * - type ve points eksik alanları doldurur
 */

import type { Question } from '../components/Quiz/QuizInterface';

export interface ApiQuestion {
  id: string;
  question_text: string;
  options: Record<string, string | null>;
  correct_answer: string;
  explanation?: string;
  explanation_video_url?: string;
  difficulty_level?: string;
  subject_area?: string;
}

const DIFFICULTY_MAP: Record<string, 'easy' | 'medium' | 'hard'> = {
  COK_KOLAY: 'easy',
  KOLAY: 'easy',
  ORTA: 'medium',
  ZOR: 'hard',
  COK_ZOR: 'hard',
};

export function mapApiToQuizQuestion(q: ApiQuestion): Question {
  const optionEntries = Object.entries(q.options)
    .filter(([, v]) => v != null);
  const options = optionEntries.map(([key, value]) => `${key}) ${value}`);

  // correctAnswer must match option format: "A) İstanbul" not just "A"
  const correctKey = q.correct_answer; // e.g. "A"
  const correctEntry = optionEntries.find(([key]) => key === correctKey);
  const correctAnswer = correctEntry
    ? `${correctEntry[0]}) ${correctEntry[1]}`
    : correctKey; // fallback to raw key if not found

  return {
    id: q.id,
    type: 'multiple-choice',
    question: q.question_text,
    options,
    correctAnswer,
    explanation: q.explanation,
    difficulty: DIFFICULTY_MAP[q.difficulty_level || ''] || 'medium',
    points: 1,
  };
}

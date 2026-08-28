/**
 * usePlacementSession — Placement Test API hook
 * /api/v1/placement
 */
import { useState, useCallback } from 'react';

const API = '';

export interface PlacementQuestion {
  question_id: string;
  stem: string;                     // question_text
  options: Record<string, string>;  // {A, B, C, D}
  topic_id?: string;
  subject_id?: string;
}

export interface PlacementSessionState {
  session_id: string;
  question: PlacementQuestion;
  progress: { current: number; max: number };
  level_hint: string;
  is_complete: boolean;
}

export interface PlacementAnswerResult {
  is_complete: boolean;
  theta: number;
  se: number;
  n_questions: number;
  next_question: PlacementQuestion | null;
  level_hint: string | null;
  feedback: { is_correct: boolean };
  result?: {
    theta_final: number;
    se_final: number;
    level: string;
    level_label: string;
    recommended_subjects: string[];
  };
}

type PlacementPhase = 'idle' | 'loading' | 'active' | 'answering' | 'complete' | 'error';

export function usePlacementSession(token?: string | null) {
  const [phase, setPhase] = useState<PlacementPhase>('idle');
  const [session, setSession] = useState<PlacementSessionState | null>(null);
  const [lastResult, setLastResult] = useState<PlacementAnswerResult | null>(null);
  const [finalResult, setFinalResult] = useState<PlacementAnswerResult['result'] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {headers['Authorization'] = `Bearer ${token}`;}

  const startSession = useCallback(async (subject_id: string, school_type = 'default') => {
    setPhase('loading');
    setError(null);
    try {
      const res = await fetch(`${API}/api/v1/placement/start`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ subject_id, school_type }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data: PlacementSessionState = await res.json();
      setSession(data);
      setPhase('active');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Placement başlatılamadı');
      setPhase('error');
    }
  }, [token]);

  const submitAnswer = useCallback(async (selected_option: string) => {
    if (!session) {return;}
    setPhase('answering');
    try {
      const res = await fetch(`${API}/api/v1/placement/${session.session_id}/answer`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({
          question_id: session.question.question_id,
          answer: selected_option,   // backend 'answer' fieldını bekliyor
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const result: PlacementAnswerResult = await res.json();
      setLastResult(result);
      if (result.is_complete) {
        setFinalResult(result.result ?? null);
        setPhase('complete');
      } else if (result.next_question) {
        setSession(prev => prev ? {
          ...prev,
          question: result.next_question!,
          progress: { ...prev.progress, current: prev.progress.current + 1 },
          level_hint: result.level_hint ?? prev.level_hint,
        } : null);
        setPhase('active');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Cevap gönderilemedi');
      setPhase('error');
    }
  }, [session, token]);

  const reset = useCallback(() => {
    setPhase('idle');
    setSession(null);
    setLastResult(null);
    setFinalResult(null);
    setError(null);
  }, []);

  return { phase, session, lastResult, finalResult, error, startSession, submitAnswer, reset };
}

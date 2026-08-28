/**
 * useCATSession — CAT Engine API hook
 * /api/v1/cat/sessions
 */
import { useState, useCallback } from 'react';

const API = '';

export interface CATQuestion {
  question_id: string;
  stem: string;
  options: Record<string, string>;
  topic_id: string;
  subject_id: string;
  irt: { difficulty: number; discrimination: number; guessing: number };
}

export interface CATSessionState {
  session_id: string;
  question: CATQuestion;
  theta: number;
  se: number;
  n_questions: number;
  phase: string;
  is_complete: boolean;
  subject_id?: string;  // CAT başlatılırken set edilir
}

export interface CATResult {
  is_complete: boolean;
  theta: number;
  se: number;
  n_questions: number;
  termination_reason: string | null;
  next_question: CATQuestion | null;
  phase: string | null;
  feedback: { is_correct: boolean; correct_option: string | null };
}

type SessionPhase = 'idle' | 'loading' | 'active' | 'answering' | 'complete' | 'error';

export function useCATSession(token?: string | null) {
  const [phase, setPhase] = useState<SessionPhase>('idle');
  const [session, setSession] = useState<CATSessionState | null>(null);
  const [lastResult, setLastResult] = useState<CATResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // httpOnly cookie ile auth — token sadece varsa Bearer ekle
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {headers['Authorization'] = `Bearer ${token}`;}

  const startSession = useCallback(async (subject_id: string) => {
    setPhase('loading');
    setError(null);
    try {
      const res = await fetch(`${API}/api/v1/cat/sessions`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({ subject_id }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data: CATSessionState = await res.json();
      setSession({ ...data, subject_id });  // subject_id'yi sakla
      setPhase('active');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'CAT başlatılamadı');
      setPhase('error');
    }
  }, [token]);

  const submitAnswer = useCallback(async (selected_option: string, response_ms?: number) => {
    if (!session) {return;}
    setPhase('answering');
    try {
      const res = await fetch(`${API}/api/v1/cat/sessions/${session.session_id}/answer`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({
          question_id: session.question.question_id,
          selected_option,
          response_ms: response_ms ?? null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const result: CATResult & { plan_refresh_needed?: boolean } = await res.json();
      setLastResult(result);
      if (result.is_complete) {
        setPhase('complete');
        setSession(prev => prev ? { ...prev, theta: result.theta, se: result.se, is_complete: true } : null);
        // CAT bitti → daily-plan sayfasını yenile (backend'den plan_refresh_needed: true gelir)
        if (result.plan_refresh_needed) {
          // React Query cache'ini invalidate et veya navigasyon ile yenile
          window.dispatchEvent(new CustomEvent('cat-complete', { detail: { theta: result.theta, subject: session?.subject_id } }));
        }
      } else if (result.next_question) {
        setSession(prev => prev ? {
          ...prev,
          question: result.next_question!,
          theta: result.theta,
          se: result.se,
          n_questions: result.n_questions,
          phase: result.phase ?? prev.phase,
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
    setError(null);
  }, []);

  return { phase, session, lastResult, error, startSession, submitAnswer, reset };
}

/**
 * useStudentProfile — Öğrencinin gerçek zamanlı profilini çeker
 * θ değerleri, FSRS vadesi, günlük plan özeti
 */
import { useState, useEffect, useCallback } from 'react';

export interface SubjectStatus {
  subject: string;
  theta: number;
  mastery_pct: number;
  fsrs_due_count: number;
  zpd_lower: number;
  zpd_upper: number;
  priority_score: number;
  level_label: string;
}

export interface DailyPlanSummary {
  days_remaining: number;
  total_minutes: number;
  fsrs_review_count: number;
  weak_subject: string | null;
  strong_subject: string | null;
  motivational_note: string;
  block_count: number;
}

export interface StudentProfile {
  statuses: SubjectStatus[];
  plan: DailyPlanSummary | null;
  loading: boolean;
  error: string;
  refresh: () => void;
}

const LP_API = '/api/v1/learning-path';

export function useStudentProfile(): StudentProfile {
  const [statuses, setStatuses] = useState<SubjectStatus[]>([]);
  const [plan, setPlan] = useState<DailyPlanSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetch_data = useCallback(async () => {
    setLoading(true);
    const token = localStorage.getItem('access_token');
    if (!token) { setLoading(false); return; }
    const headers = { Authorization: `Bearer ${token}` };

    try {
      const [statusRes, planRes] = await Promise.all([
        fetch(`${LP_API}/status`, { headers }),
        fetch(`${LP_API}/today`, { headers }),
      ]);

      if (statusRes.ok) {
        const data = await statusRes.json();
        if (Array.isArray(data)) setStatuses(data);
      }

      if (planRes.ok) {
        const data = await planRes.json();
        if (data && !data.detail) {
          setPlan({
            days_remaining: data.days_remaining,
            total_minutes: data.total_minutes,
            fsrs_review_count: data.fsrs_review_count,
            weak_subject: data.weak_subject,
            strong_subject: data.strong_subject,
            motivational_note: data.motivational_note,
            block_count: (data.blocks || []).length,
          });
        }
      }
    } catch (e) {
      setError('Profil yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch_data(); }, [fetch_data]);

  return { statuses, plan, loading, error, refresh: fetch_data };
}

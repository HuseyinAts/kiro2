/**
 * Sınav Performans Metrikleri Hook'u
 * Sınav sırasında performans ve davranış analizi
 */
import { useState, useEffect, useRef, useCallback } from 'react';

import { ExamSessionResponse, QuestionResponse } from '../services/examService';
import { SinavOturumu, SinavSorusu } from '../types';

interface ExamMetrics {
  // Zaman metrikleri
  totalTimeSpent: number
  averageTimePerQuestion: number
  timePerQuestion: Record<string, number>

  // Cevap metrikleri
  answerChanges: Record<string, number>
  flaggedQuestions: string[]

  // Davranış metrikleri
  questionVisits: Record<string, number>
  navigationPattern: Array<{
    questionId: string
    timestamp: number
    action: 'visit' | 'answer' | 'flag' | 'unflag'
  }>

  // Performans metrikleri
  focusLossCount: number
  tabSwitchCount: number
  pageReloadCount: number

  // İstatistikler
  completionRate: number
  flaggedRate: number
  averageAnswerTime: number
}

interface UseExamMetricsOptions {
  oturum: SinavOturumu | ExamSessionResponse | null
  mevcutSoru: SinavSorusu | QuestionResponse | null
  enabled?: boolean
}

export const useExamMetrics = ({
  oturum,
  mevcutSoru,
  enabled = true,
}: UseExamMetricsOptions) => {
  const [metrics, setMetrics] = useState<ExamMetrics>({
    totalTimeSpent: 0,
    averageTimePerQuestion: 0,
    timePerQuestion: {},
    answerChanges: {},
    flaggedQuestions: [],
    questionVisits: {},
    navigationPattern: [],
    focusLossCount: 0,
    tabSwitchCount: 0,
    pageReloadCount: 0,
    completionRate: 0,
    flaggedRate: 0,
    averageAnswerTime: 0,
  });

  // Referanslar
  const startTimeRef = useRef<number>(Date.now());
  const questionStartTimeRef = useRef<number>(Date.now());
  const currentQuestionIdRef = useRef<string | null>(null);
  const previousAnswersRef = useRef<Record<string, string>>({});
  const isPageVisibleRef = useRef<boolean>(true);
  const focusStartTimeRef = useRef<number>(Date.now());

  /**
   * Navigasyon olayını kaydet
   */
  const recordNavigation = useCallback((action: 'visit' | 'answer' | 'flag' | 'unflag', questionId?: string) => {
    if (!enabled || !oturum) {return;}

    const targetQuestionId = questionId || (mevcutSoru && 'soru_id' in mevcutSoru ? mevcutSoru.soru_id : (mevcutSoru && 'id' in mevcutSoru ? (mevcutSoru as any).id : undefined));
    if (!targetQuestionId) {return;}

    setMetrics(prev => ({
      ...prev,
      navigationPattern: [
        ...prev.navigationPattern,
        {
          questionId: targetQuestionId,
          timestamp: Date.now(),
          action,
        },
      ],
    }));
  }, [enabled, oturum, mevcutSoru]);

  /**
   * Soru ziyaret sayısını artır
   */
  const recordQuestionVisit = useCallback((questionId: string) => {
    if (!enabled) {return;}

    setMetrics(prev => ({
      ...prev,
      questionVisits: {
        ...prev.questionVisits,
        [questionId]: (prev.questionVisits[questionId] || 0) + 1,
      },
    }));

    recordNavigation('visit', questionId);
  }, [enabled, recordNavigation]);

  /**
   * Cevap değişikliğini kaydet
   */
  const recordAnswerChange = useCallback((questionId: string, newAnswer: string) => {
    if (!enabled) {return;}

    const previousAnswer = previousAnswersRef.current[questionId];

    if (previousAnswer && previousAnswer !== newAnswer) {
      setMetrics(prev => ({
        ...prev,
        answerChanges: {
          ...prev.answerChanges,
          [questionId]: (prev.answerChanges[questionId] || 0) + 1,
        },
      }));
    }

    previousAnswersRef.current[questionId] = newAnswer;
    recordNavigation('answer', questionId);
  }, [enabled, recordNavigation]);

  /**
   * Soru işaretleme durumunu kaydet
   */
  const recordQuestionFlag = useCallback((questionId: string, flagged: boolean) => {
    if (!enabled) {return;}

    setMetrics(prev => ({
      ...prev,
      flaggedQuestions: flagged
        ? [...prev.flaggedQuestions.filter(id => id !== questionId), questionId]
        : prev.flaggedQuestions.filter(id => id !== questionId),
    }));

    recordNavigation(flagged ? 'flag' : 'unflag', questionId);
  }, [enabled, recordNavigation]);

  /**
   * Soru değişikliğini takip et
   */
  useEffect(() => {
    if (!enabled || !mevcutSoru) {return;}

    const currentQuestionId = 'soru_id' in mevcutSoru ? mevcutSoru.soru_id : mevcutSoru.id;
    const previousQuestionId = currentQuestionIdRef.current;

    // Önceki soru için süre kaydet
    if (previousQuestionId && previousQuestionId !== currentQuestionId) {
      const timeSpent = Date.now() - questionStartTimeRef.current;

      setMetrics(prev => ({
        ...prev,
        timePerQuestion: {
          ...prev.timePerQuestion,
          [previousQuestionId]: (prev.timePerQuestion[previousQuestionId] || 0) + timeSpent,
        },
      }));
    }

    // Yeni soru için başlangıç zamanını kaydet
    questionStartTimeRef.current = Date.now();
    currentQuestionIdRef.current = currentQuestionId;

    // Soru ziyaretini kaydet
    recordQuestionVisit(currentQuestionId);
  }, [mevcutSoru, enabled, recordQuestionVisit]);

  /**
   * Sayfa görünürlüğünü takip et
   */
  useEffect(() => {
    if (!enabled) {return;}

    const handleVisibilityChange = () => {
      const isVisible = !document.hidden;

      if (isPageVisibleRef.current && !isVisible) {
        // Sayfa gizlendi - focus kaybı
        setMetrics(prev => ({
          ...prev,
          focusLossCount: prev.focusLossCount + 1,
        }));
      } else if (!isPageVisibleRef.current && isVisible) {
        // Sayfa tekrar görünür oldu
        focusStartTimeRef.current = Date.now();
      }

      isPageVisibleRef.current = isVisible;
    };

    const handleBeforeUnload = () => {
      setMetrics(prev => ({
        ...prev,
        pageReloadCount: prev.pageReloadCount + 1,
      }));
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [enabled]);

  /**
   * Tab değişikliğini takip et
   */
  useEffect(() => {
    if (!enabled) {return;}

    const handleFocus = () => {
      focusStartTimeRef.current = Date.now();
    };

    const handleBlur = () => {
      setMetrics(prev => ({
        ...prev,
        tabSwitchCount: prev.tabSwitchCount + 1,
      }));
    };

    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);

    return () => {
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, [enabled]);

  /**
   * Metrikleri güncelle
   */
  useEffect(() => {
    if (!enabled || !oturum) {return;}

    const totalQuestions = 'toplam_soru_sayisi' in oturum ? oturum.toplam_soru_sayisi : oturum.total_questions;
    const answeredQuestionsCount = 'cevaplanan_sorular' in oturum ? Object.keys(oturum.cevaplanan_sorular).length : 0;
    const flaggedQuestionsCount = 'isaretlenen_sorular' in oturum ? oturum.isaretlenen_sorular.length : 0;

    const totalTimeSpent = Date.now() - startTimeRef.current;
    const questionTimes = Object.values(metrics.timePerQuestion);
    const averageTimePerQuestion = questionTimes.length > 0
      ? questionTimes.reduce((sum, time) => sum + time, 0) / questionTimes.length
      : 0;

    setMetrics(prev => ({
      ...prev,
      totalTimeSpent,
      averageTimePerQuestion,
      completionRate: totalQuestions > 0 ? (answeredQuestionsCount / totalQuestions) * 100 : 0,
      flaggedRate: totalQuestions > 0 ? (flaggedQuestionsCount / totalQuestions) * 100 : 0,
      averageAnswerTime: averageTimePerQuestion,
    }));
  }, [enabled, oturum, metrics.timePerQuestion]);

  /**
   * Metrikleri sıfırla
   */
  const resetMetrics = useCallback(() => {
    setMetrics({
      totalTimeSpent: 0,
      averageTimePerQuestion: 0,
      timePerQuestion: {},
      answerChanges: {},
      flaggedQuestions: [],
      questionVisits: {},
      navigationPattern: [],
      focusLossCount: 0,
      tabSwitchCount: 0,
      pageReloadCount: 0,
      completionRate: 0,
      flaggedRate: 0,
      averageAnswerTime: 0,
    });

    startTimeRef.current = Date.now();
    questionStartTimeRef.current = Date.now();
    currentQuestionIdRef.current = null;
    previousAnswersRef.current = {};
  }, []);

  /**
   * Performans raporu oluştur
   */
  const generatePerformanceReport = useCallback(() => {
    if (!oturum) {return null;}

    const report = {
      examId: 'sinav_id' in oturum ? oturum.sinav_id : oturum.session_id,
      examType: 'sinav_tipi' in oturum ? oturum.sinav_tipi : oturum.exam_type,
      duration: metrics.totalTimeSpent,

      // Zaman analizi
      timeAnalysis: {
        totalTime: metrics.totalTimeSpent,
        averagePerQuestion: metrics.averageTimePerQuestion,
        slowestQuestions: Object.entries(metrics.timePerQuestion)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 5)
          .map(([questionId, time]) => ({ questionId, time })),
        fastestQuestions: Object.entries(metrics.timePerQuestion)
          .sort(([,a], [,b]) => a - b)
          .slice(0, 5)
          .map(([questionId, time]) => ({ questionId, time })),
      },

      // Davranış analizi
      behaviorAnalysis: {
        focusLossCount: metrics.focusLossCount,
        tabSwitchCount: metrics.tabSwitchCount,
        pageReloadCount: metrics.pageReloadCount,
        mostVisitedQuestions: Object.entries(metrics.questionVisits)
          .sort(([,a], [,b]) => b - a)
          .slice(0, 10)
          .map(([questionId, visits]) => ({ questionId, visits })),
        answerChanges: Object.entries(metrics.answerChanges)
          .map(([questionId, changes]) => ({ questionId, changes }))
          .filter(item => item.changes > 0),
      },

      // Performans metrikleri
      performance: {
        completionRate: metrics.completionRate,
        flaggedRate: metrics.flaggedRate,
        averageAnswerTime: metrics.averageAnswerTime,
        navigationEfficiency: oturum
          ? metrics.navigationPattern.length / ('toplam_soru_sayisi' in oturum ? oturum.toplam_soru_sayisi : oturum.total_questions || 1)
          : 0,
      },

      timestamp: new Date().toISOString(),
    };

    return report;
  }, [oturum, metrics]);

  return {
    metrics,
    recordAnswerChange,
    recordQuestionFlag,
    resetMetrics,
    generatePerformanceReport,
    isEnabled: enabled,
  };
};

export default useExamMetrics;
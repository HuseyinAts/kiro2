/**
 * useExamResults Hook
 *
 * Custom hook for loading exam results and advanced analysis
 * Separates data fetching logic from UI components
 */

import { useState, useEffect } from 'react';

import { advancedReportsService, AdvancedExamReport } from '../services/advancedReportsService';
import { examService } from '../services/examService';
import { SinavSonucu, performanceToSinavSonucu, SinavTipi } from '../types';

interface UseExamResultsReturn {
  sonuc: SinavSonucu | null
  gelismisRapor: AdvancedExamReport | null
  loading: boolean
  error: string | null
  reload: () => Promise<void>
}

/**
 * Hook for fetching exam results with advanced analysis
 *
 * @param sinavId - Exam ID to fetch results for
 * @returns Exam results data, loading state, error, and reload function
 *
 * @example
 * const { sonuc, gelismisRapor, loading, error } = useExamResults(sinavId)
 */
export const useExamResults = (sinavId: string): UseExamResultsReturn => {
  const [sonuc, setSonuc] = useState<SinavSonucu | null>(null);
  const [gelismisRapor, setGelismisRapor] = useState<AdvancedExamReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadResults = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch basic results and advanced report in parallel
      const [sonucData, gelismisRaporData] = await Promise.allSettled([
        examService.getExamResult(sinavId),
        advancedReportsService.getAdvancedExamReport(sinavId),
      ]);

      if (sonucData.status === 'fulfilled') {
        // Convert PerformanceResponse to SinavSonucu
        const performanceData = sonucData.value;
        const convertedResult = performanceToSinavSonucu(
          performanceData,
          sinavId,
          'unknown', // studentId not available here
          SinavTipi.TYT, // default exam type
        );
        setSonuc(convertedResult);
      } else {
        throw new Error('Temel sınav sonucu yüklenemedi');
      }

      if (gelismisRaporData.status === 'fulfilled') {
        setGelismisRapor(gelismisRaporData.value);
      } else {
        console.warn('Gelişmiş rapor yüklenemedi:', gelismisRaporData.reason);
        // Don't throw - advanced report is optional
      }
    } catch (err: any) {
      setError(err.message || 'Sonuçlar yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sinavId) {
      loadResults();
    }
  }, [sinavId]);

  return {
    sonuc,
    gelismisRapor,
    loading,
    error,
    reload: loadResults,
  };
};

export default useExamResults;

/**
 * Bionic Reading Hook
 * Real-time Bionic Reading toggle functionality
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { BionicReadingResult, ApiResponse } from '../types/revolutionary';

interface BionicReadingSettings {
  rootBoldRatio: number;
  suffixBoldRatio: number;
  minBoldChars: number;
  maxBoldChars: number;
}

interface UseBionicReadingOptions {
  studentId?: string;
  autoApply?: boolean;
  debounceMs?: number;
  onError?: (error: string) => void;
  onSuccess?: (result: BionicReadingResult) => void;
}

export const useBionicReading = (options: UseBionicReadingOptions = {}) => {
  const {
    studentId,
    autoApply = false,
    debounceMs = 500,
    onError,
    onSuccess
  } = options;

  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BionicReadingResult | null>(null);
  const [settings, setSettings] = useState<BionicReadingSettings>({
    rootBoldRatio: 40,
    suffixBoldRatio: 0,
    minBoldChars: 2,
    maxBoldChars: 4
  });

  const debounceRef = useRef<NodeJS.Timeout>();
  const abortControllerRef = useRef<AbortController>();

  // Kullanıcı tercihlerini yükle
  const loadPreferences = useCallback(async () => {
    if (!studentId) return;

    try {
      const response = await fetch('/api/v1/bionic-reading/preferences', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        }
      });

      if (response.ok) {
        const apiResult: ApiResponse<any> = await response.json();
        if (apiResult.success && apiResult.data) {
          const prefs = apiResult.data;
          setEnabled(prefs.enabled || false);
          setSettings({
            rootBoldRatio: (prefs.bold_ratio || 0.4) * 100,
            suffixBoldRatio: 0,
            minBoldChars: prefs.min_word_length || 2,
            maxBoldChars: 4
          });
        }
      }
    } catch (error) {
      console.warn('Kullanıcı tercihleri yüklenemedi:', error);
    }
  }, [studentId]);

  // Kullanıcı tercihlerini kaydet
  const savePreferences = useCallback(async (
    newEnabled: boolean,
    newSettings: BionicReadingSettings
  ) => {
    if (!studentId) return;

    try {
      const preferences = {
        enabled: newEnabled,
        bold_ratio: newSettings.rootBoldRatio / 100,
        min_word_length: newSettings.minBoldChars,
        auto_apply: autoApply,
        font_weight: "bold",
        highlight_color: "#000000"
      };

      await fetch('/api/v1/bionic-reading/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(preferences)
      });
    } catch (error) {
      console.warn('Kullanıcı tercihleri kaydedilemedi:', error);
    }
  }, [studentId, autoApply]);

  // Bionic Reading uygula
  const applyBionicReading = useCallback(async (text: string) => {
    if (!text.trim()) {
      setResult(null);
      return null;
    }

    // Önceki isteği iptal et
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Yeni AbortController oluştur
    abortControllerRef.current = new AbortController();

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/bionic-reading/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          text: text,
          use_cache: true
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult: ApiResponse<any> = await response.json();
      
      if (!apiResult.success) {
        throw new Error(apiResult.message || 'Bionic Reading işlemi başarısız');
      }

      const bionicResult: BionicReadingResult = {
        orijinal_metin: apiResult.data.original_text,
        bionic_metin: apiResult.data.bionic_text,
        kok_ek_analizi: [],
        complexity_score: 0,
        readability_score: 0,
        processing_time: apiResult.data.processing_time_ms || 0
      };
      
      setResult(bionicResult);
      onSuccess?.(bionicResult);
      return bionicResult;
      
    } catch (err: any) {
      if (err.name === 'AbortError') {
        return null; // İstek iptal edildi, hata gösterme
      }

      const errorMessage = err.message || 'Bionic Reading işlemi başarısız';
      setError(errorMessage);
      onError?.(errorMessage);
      
      // Fallback: Mock implementation
      const mockResult: BionicReadingResult = {
        orijinal_metin: text,
        bionic_metin: applyMockBionicReading(text),
        kok_ek_analizi: [],
        complexity_score: 0,
        readability_score: 0,
        processing_time: 800
      };
      
      setResult(mockResult);
      return mockResult;
      
    } finally {
      setLoading(false);
    }
  }, [onSuccess, onError]);

  // Debounced Bionic Reading
  const applyBionicReadingDebounced = useCallback((text: string) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      applyBionicReading(text);
    }, debounceMs);
  }, [applyBionicReading, debounceMs]);

  // Real-time toggle
  const toggleEnabled = useCallback(async (newEnabled: boolean) => {
    setEnabled(newEnabled);
    await savePreferences(newEnabled, settings);
  }, [settings, savePreferences]);

  // Ayarları güncelle
  const updateSettings = useCallback(async (newSettings: BionicReadingSettings) => {
    setSettings(newSettings);
    await savePreferences(enabled, newSettings);
  }, [enabled, savePreferences]);

  // Mock Bionic Reading
  const applyMockBionicReading = useCallback((text: string): string => {
    const words = text.split(/(\s+)/);
    return words.map(word => {
      if (word.trim().length < 3 || /^\s+$/.test(word)) return word;
      
      const cleanWord = word.replace(/[.,!?;:]/g, '');
      const punctuation = word.replace(cleanWord, '');
      
      const boldLength = Math.max(2, Math.floor(cleanWord.length * (settings.rootBoldRatio / 100)));
      const boldPart = cleanWord.substring(0, boldLength);
      const normalPart = cleanWord.substring(boldLength);
      
      return `**${boldPart}**${normalPart}${punctuation}`;
    }).join('');
  }, [settings.rootBoldRatio]);

  // Component mount edildiğinde tercihleri yükle
  useEffect(() => {
    loadPreferences();
  }, [loadPreferences]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    // State
    enabled,
    loading,
    error,
    result,
    settings,

    // Actions
    toggleEnabled,
    updateSettings,
    applyBionicReading,
    applyBionicReadingDebounced,
    loadPreferences,
    savePreferences,

    // Utilities
    clearError: () => setError(null),
    clearResult: () => setResult(null)
  };
};

export default useBionicReading;
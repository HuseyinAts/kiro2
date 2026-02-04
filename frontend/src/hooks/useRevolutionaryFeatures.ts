/**
 * Revolutionary Features Hook
 * Devrimsel özellikler için merkezi state yönetimi ve API çağrıları
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  FSRSCard, 
  FSRSSchedule, 
  BionicReadingResult, 
  MultiAgentStatus,
  AgentCoordination,
  BlackboardEvent,
  RevolutionaryFeatureSettings,
  SimplificationResult,
  TurkishZPDRange,
  ZPDRecommendation
} from '../types';
import revolutionaryFeaturesService from '../services/revolutionaryFeaturesService';

interface UseRevolutionaryFeaturesOptions {
  studentId: string;
  autoLoad?: boolean;
}

interface RevolutionaryFeaturesState {
  // FSRS
  fsrsCards: FSRSCard[];
  fsrsSchedules: FSRSSchedule[];
  
  // Bionic Reading
  bionicResult: BionicReadingResult | null;
  
  // Multi-Agent
  agentStatus: MultiAgentStatus[];
  agentCoordination: AgentCoordination | null;
  blackboardEvents: BlackboardEvent[];
  
  // Settings
  settings: RevolutionaryFeatureSettings | null;
  
  // Loading states
  loading: {
    fsrs: boolean;
    bionic: boolean;
    multiAgent: boolean;
    settings: boolean;
    global: boolean;
  };
  
  // Error states
  errors: {
    fsrs: string | null;
    bionic: string | null;
    multiAgent: string | null;
    settings: string | null;
    global: string | null;
  };
}

const initialState: RevolutionaryFeaturesState = {
  fsrsCards: [],
  fsrsSchedules: [],
  bionicResult: null,
  agentStatus: [],
  agentCoordination: null,
  blackboardEvents: [],
  settings: null,
  loading: {
    fsrs: false,
    bionic: false,
    multiAgent: false,
    settings: false,
    global: false
  },
  errors: {
    fsrs: null,
    bionic: null,
    multiAgent: null,
    settings: null,
    global: null
  }
};

export const useRevolutionaryFeatures = ({ 
  studentId, 
  autoLoad = true 
}: UseRevolutionaryFeaturesOptions) => {
  const [state, setState] = useState<RevolutionaryFeaturesState>(initialState);

  // Error handling utility
  const handleError = useCallback((category: keyof RevolutionaryFeaturesState['errors'], error: any) => {
    const errorMessage = error instanceof Error ? error.message : 'Beklenmeyen hata oluştu';
    setState(prev => ({
      ...prev,
      errors: {
        ...prev.errors,
        [category]: errorMessage
      }
    }));
    console.error(`Revolutionary Features Error (${category}):`, error);
  }, []);

  // Loading state utility
  const setLoading = useCallback((category: keyof RevolutionaryFeaturesState['loading'], loading: boolean) => {
    setState(prev => ({
      ...prev,
      loading: {
        ...prev.loading,
        [category]: loading
      }
    }));
  }, []);

  // Clear error utility
  const clearError = useCallback((category: keyof RevolutionaryFeaturesState['errors']) => {
    setState(prev => ({
      ...prev,
      errors: {
        ...prev.errors,
        [category]: null
      }
    }));
  }, []);

  // FSRS Functions
  const loadFSRSData = useCallback(async (subject?: string) => {
    if (!studentId) return;

    setLoading('fsrs', true);
    clearError('fsrs');

    try {
      const [cards, schedules] = await Promise.all([
        revolutionaryFeaturesService.getFSRSCards(studentId, subject),
        revolutionaryFeaturesService.getFSRSSchedules(studentId, subject)
      ]);

      setState(prev => ({
        ...prev,
        fsrsCards: cards,
        fsrsSchedules: schedules
      }));
    } catch (error) {
      handleError('fsrs', error);
    } finally {
      setLoading('fsrs', false);
    }
  }, [studentId, setLoading, clearError, handleError]);

  const reviewFSRSCard = useCallback(async (cardId: string, grade: 1 | 2 | 3 | 4) => {
    if (!studentId) return;

    try {
      await revolutionaryFeaturesService.reviewFSRSCard(studentId, cardId, grade);
      
      // Kartı listeden kaldır veya güncelle
      setState(prev => ({
        ...prev,
        fsrsCards: prev.fsrsCards.filter(card => card.card_id !== cardId)
      }));
      
      // Zamanlamaları yenile
      await loadFSRSData();
    } catch (error) {
      handleError('fsrs', error);
    }
  }, [studentId, loadFSRSData, handleError]);

  // Bionic Reading Functions
  const applyBionicReading = useCallback(async (text: string, settings?: any) => {
    if (!text.trim()) {
      setState(prev => ({ ...prev, bionicResult: null }));
      return;
    }

    setLoading('bionic', true);
    clearError('bionic');

    try {
      const result = await revolutionaryFeaturesService.applyBionicReading(text, studentId, settings);
      setState(prev => ({ ...prev, bionicResult: result }));
    } catch (error) {
      handleError('bionic', error);
    } finally {
      setLoading('bionic', false);
    }
  }, [studentId, setLoading, clearError, handleError]);

  // Multi-Agent Functions
  const loadMultiAgentData = useCallback(async () => {
    if (!studentId) return;

    setLoading('multiAgent', true);
    clearError('multiAgent');

    try {
      const [status, coordination, events] = await Promise.all([
        revolutionaryFeaturesService.getMultiAgentStatus(studentId),
        revolutionaryFeaturesService.getAgentCoordination(studentId),
        revolutionaryFeaturesService.getBlackboardEvents(studentId, 10)
      ]);

      setState(prev => ({
        ...prev,
        agentStatus: status,
        agentCoordination: coordination,
        blackboardEvents: events
      }));
    } catch (error) {
      handleError('multiAgent', error);
    } finally {
      setLoading('multiAgent', false);
    }
  }, [studentId, setLoading, clearError, handleError]);

  // Settings Functions
  const loadSettings = useCallback(async () => {
    if (!studentId) return;

    setLoading('settings', true);
    clearError('settings');

    try {
      const settings = await revolutionaryFeaturesService.getRevolutionarySettings(studentId);
      setState(prev => ({ ...prev, settings }));
    } catch (error) {
      handleError('settings', error);
    } finally {
      setLoading('settings', false);
    }
  }, [studentId, setLoading, clearError, handleError]);

  const updateSettings = useCallback(async (newSettings: RevolutionaryFeatureSettings) => {
    if (!studentId) return;

    setLoading('settings', true);
    clearError('settings');

    try {
      await revolutionaryFeaturesService.updateRevolutionarySettings(studentId, newSettings);
      setState(prev => ({ ...prev, settings: newSettings }));
    } catch (error) {
      handleError('settings', error);
      throw error; // Re-throw to allow component to handle
    } finally {
      setLoading('settings', false);
    }
  }, [studentId, setLoading, clearError, handleError]);

  const resetSettings = useCallback(async () => {
    if (!studentId) return;

    setLoading('settings', true);
    clearError('settings');

    try {
      const defaultSettings = await revolutionaryFeaturesService.resetRevolutionarySettings(studentId);
      setState(prev => ({ ...prev, settings: defaultSettings }));
      return defaultSettings;
    } catch (error) {
      handleError('settings', error);
      throw error;
    } finally {
      setLoading('settings', false);
    }
  }, [studentId, setLoading, clearError, handleError]);

  // Load all data
  const loadAllData = useCallback(async () => {
    if (!studentId) return;

    setLoading('global', true);
    clearError('global');

    try {
      await Promise.all([
        loadFSRSData(),
        loadMultiAgentData(),
        loadSettings()
      ]);
    } catch (error) {
      handleError('global', error);
    } finally {
      setLoading('global', false);
    }
  }, [studentId, loadFSRSData, loadMultiAgentData, loadSettings, setLoading, clearError, handleError]);

  // Auto-load on mount
  useEffect(() => {
    if (autoLoad && studentId) {
      loadAllData();
    }
  }, [autoLoad, studentId, loadAllData]);

  // Computed values
  const isAnyLoading = Object.values(state.loading).some(loading => loading);
  const hasAnyError = Object.values(state.errors).some(error => error !== null);

  return {
    // State
    ...state,
    
    // Computed
    isAnyLoading,
    hasAnyError,
    
    // FSRS Actions
    loadFSRSData,
    reviewFSRSCard,
    
    // Bionic Reading Actions
    applyBionicReading,
    
    // Multi-Agent Actions
    loadMultiAgentData,
    
    // Settings Actions
    loadSettings,
    updateSettings,
    resetSettings,
    
    // Global Actions
    loadAllData,
    clearError,
    
    // Utilities
    refresh: loadAllData
  };
};

export default useRevolutionaryFeatures;
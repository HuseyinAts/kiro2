/**
 * Sequential Thinking Custom Hook
 * React hook for step-by-step problem solving with Multi-LLM support
 *
 * Supports: Gemini, OpenAI, Claude, Qwen
 * Features: Ensemble voting, caching, real-time step tracking
 */

import { useState, useCallback, useRef } from 'react';

import {
  reasoningService,
  SolveResponse,
  DecomposeResponse,
  CompareResponse,
  ReasoningSession,
  LLMProvider,
  ProvidersListResponse,
} from '../services/reasoningService';

interface UseSequentialThinkingState {
  // Current solution data
  solution: SolveResponse | null
  decomposition: DecomposeResponse | null
  comparison: CompareResponse | null
  session: ReasoningSession | null
  sessions: ReasoningSession[]
  providers: ProvidersListResponse | null

  // UI state
  loading: boolean
  error: string | null
  currentStep: number

  // Metadata
  selectedProvider: LLMProvider | null
  useEnsemble: boolean
  fromCache: boolean
}

interface UseSequentialThinkingActions {
  // Core actions
  solve: (problem: string, options?: {
    provider?: LLMProvider
    useEnsemble?: boolean
    maxSteps?: number
    useCache?: boolean
  }) => Promise<SolveResponse | null>

  // Provider-specific shortcuts
  solveWithGemini: (problem: string) => Promise<SolveResponse | null>
  solveWithOpenAI: (problem: string) => Promise<SolveResponse | null>
  solveWithClaude: (problem: string) => Promise<SolveResponse | null>
  solveWithQwen: (problem: string) => Promise<SolveResponse | null>
  solveWithEnsemble: (problem: string) => Promise<SolveResponse | null>

  // Advanced operations
  decompose: (problem: string, provider?: LLMProvider) => Promise<DecomposeResponse | null>
  compare: (problem: string) => Promise<CompareResponse | null>

  // Session management
  loadSession: (sessionId: string) => Promise<void>
  loadMySessions: (limit?: number) => Promise<void>

  // Navigation
  goToStep: (stepNumber: number) => void
  nextStep: () => void
  previousStep: () => void

  // Utilities
  loadProviders: () => Promise<void>
  reset: () => void
  clearError: () => void
}

export type UseSequentialThinkingReturn = UseSequentialThinkingState & UseSequentialThinkingActions

const initialState: UseSequentialThinkingState = {
  solution: null,
  decomposition: null,
  comparison: null,
  session: null,
  sessions: [],
  providers: null,
  loading: false,
  error: null,
  currentStep: 1,
  selectedProvider: null,
  useEnsemble: false,
  fromCache: false,
};

export function useSequentialThinking(): UseSequentialThinkingReturn {
  const [state, setState] = useState<UseSequentialThinkingState>(initialState);
  const isLoadingRef = useRef<boolean>(false);

  // Update partial state
  const updateState = useCallback((updates: Partial<UseSequentialThinkingState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Core solve function
  const solve = useCallback(async (
    problem: string,
    options?: {
      provider?: LLMProvider
      useEnsemble?: boolean
      maxSteps?: number
      useCache?: boolean
    },
  ): Promise<SolveResponse | null> => {
    // Prevent duplicate requests
    if (isLoadingRef.current) {
      return null;
    }
    isLoadingRef.current = true;

    updateState({
      loading: true,
      error: null,
      solution: null,
      selectedProvider: options?.provider || null,
      useEnsemble: options?.useEnsemble || false,
    });

    try {
      const response = await reasoningService.solve({
        problem,
        provider: options?.provider,
        use_ensemble: options?.useEnsemble,
        max_steps: options?.maxSteps || 10,
        use_cache: options?.useCache ?? true,
      });

      if (response.success && response.data) {
        updateState({
          solution: response.data,
          currentStep: 1,
          fromCache: response.data.from_cache,
          loading: false,
        });
        return response.data;
      } else {
        updateState({
          error: response.message || 'Cozum olusturulamadi',
          loading: false,
        });
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bir hata olustu';
      updateState({ error: errorMessage, loading: false });
      return null;
    } finally {
      isLoadingRef.current = false;
    }
  }, [updateState]);

  // Provider-specific shortcuts
  const solveWithGemini = useCallback(
    (problem: string) => solve(problem, { provider: 'gemini' }),
    [solve],
  );

  const solveWithOpenAI = useCallback(
    (problem: string) => solve(problem, { provider: 'openai' }),
    [solve],
  );

  const solveWithClaude = useCallback(
    (problem: string) => solve(problem, { provider: 'claude' }),
    [solve],
  );

  const solveWithQwen = useCallback(
    (problem: string) => solve(problem, { provider: 'qwen' }),
    [solve],
  );

  const solveWithEnsemble = useCallback(
    (problem: string) => solve(problem, { useEnsemble: true }),
    [solve],
  );

  // Decompose problem
  const decompose = useCallback(async (
    problem: string,
    provider?: LLMProvider,
  ): Promise<DecomposeResponse | null> => {
    updateState({ loading: true, error: null, decomposition: null });

    try {
      const response = await reasoningService.decompose({ problem, provider });

      if (response.success && response.data) {
        updateState({ decomposition: response.data, loading: false });
        return response.data;
      } else {
        updateState({
          error: response.message || 'Problem ayristirilamadi',
          loading: false,
        });
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bir hata olustu';
      updateState({ error: errorMessage, loading: false });
      return null;
    }
  }, [updateState]);

  // Compare providers
  const compare = useCallback(async (problem: string): Promise<CompareResponse | null> => {
    updateState({ loading: true, error: null, comparison: null });

    try {
      const response = await reasoningService.compareProviders(problem);

      if (response.success && response.data) {
        updateState({ comparison: response.data, loading: false });
        return response.data;
      } else {
        updateState({
          error: response.message || 'Karsilastirma yapilamadi',
          loading: false,
        });
        return null;
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bir hata olustu';
      updateState({ error: errorMessage, loading: false });
      return null;
    }
  }, [updateState]);

  // Load session by ID
  const loadSession = useCallback(async (sessionId: string): Promise<void> => {
    updateState({ loading: true, error: null });

    try {
      const response = await reasoningService.getSession(sessionId);

      if (response.success && response.data) {
        updateState({
          session: response.data,
          currentStep: 1,
          loading: false,
        });
      } else {
        updateState({
          error: response.message || 'Oturum bulunamadi',
          loading: false,
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bir hata olustu';
      updateState({ error: errorMessage, loading: false });
    }
  }, [updateState]);

  // Load user's sessions
  const loadMySessions = useCallback(async (limit = 20): Promise<void> => {
    updateState({ loading: true, error: null });

    try {
      const response = await reasoningService.getMySessions(limit);

      if (response.success && response.data) {
        updateState({
          sessions: response.data.sessions,
          loading: false,
        });
      } else {
        updateState({
          error: response.message || 'Oturumlar yuklenemedi',
          loading: false,
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bir hata olustu';
      updateState({ error: errorMessage, loading: false });
    }
  }, [updateState]);

  // Step navigation
  const goToStep = useCallback((stepNumber: number) => {
    const maxSteps = state.solution?.steps.length || state.session?.total_steps || 1;
    const newStep = Math.max(1, Math.min(stepNumber, maxSteps));
    updateState({ currentStep: newStep });
  }, [state.solution, state.session, updateState]);

  const nextStep = useCallback(() => {
    goToStep(state.currentStep + 1);
  }, [state.currentStep, goToStep]);

  const previousStep = useCallback(() => {
    goToStep(state.currentStep - 1);
  }, [state.currentStep, goToStep]);

  // Load providers list
  const loadProviders = useCallback(async (): Promise<void> => {
    try {
      const response = await reasoningService.getProviders();
      if (response.success && response.data) {
        updateState({ providers: response.data });
      }
    } catch (err) {
      console.error('Failed to load providers:', err);
    }
  }, [updateState]);

  // Reset state
  const reset = useCallback(() => {
    isLoadingRef.current = false;
    setState(initialState);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    updateState({ error: null });
  }, [updateState]);

  return {
    ...state,
    solve,
    solveWithGemini,
    solveWithOpenAI,
    solveWithClaude,
    solveWithQwen,
    solveWithEnsemble,
    decompose,
    compare,
    loadSession,
    loadMySessions,
    goToStep,
    nextStep,
    previousStep,
    loadProviders,
    reset,
    clearError,
  };
}

export default useSequentialThinking;

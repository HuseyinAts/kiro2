/**
 * Sequential Reasoning Service
 * API client for step-by-step problem solving with Multi-LLM support
 *
 * Supports: Gemini, OpenAI, Claude, Qwen
 * Features: Ensemble voting, caching, verification
 */

import { apiClient, ApiResponse } from './modernApiClient';

// Types
export type LLMProvider = 'gemini' | 'openai' | 'claude' | 'qwen'
export type ReasoningStepType = 'understanding' | 'decomposition' | 'calculation' | 'inference' | 'verification' | 'conclusion'
export type SessionStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'timeout'

export interface ReasoningStep {
  id?: string
  step_number: number
  step_type: ReasoningStepType
  description: string
  reasoning: string
  result?: string
  confidence: number
  is_verified?: boolean
  verification_result?: string
  latency_ms?: number
  parent_step_id?: string
}

export interface SubProblem {
  id: string
  order_index: number
  title: string
  description: string
  dependencies: string[]
  difficulty: number
  estimated_steps: number
  is_solved: boolean
  solution?: string
  solution_steps?: Record<string, unknown>[]
}

export interface ReasoningSession {
  id: string
  problem: string
  problem_type?: string
  provider?: LLMProvider
  model_name?: string
  use_ensemble: boolean
  status: SessionStatus
  understanding?: string
  final_answer?: string
  verification?: string
  confidence: number
  total_steps: number
  latency_ms: number
  tokens_used?: number
  cost_usd?: number
  ensemble_scores?: Record<string, number>
  winning_provider?: string
  created_at: string
  completed_at?: string
  steps: ReasoningStep[]
}

export interface SolveRequest {
  problem: string
  provider?: LLMProvider
  use_ensemble?: boolean
  max_steps?: number
  use_cache?: boolean
}

export interface SolveResponse {
  session_id?: string
  problem: string
  understanding?: string
  steps: ReasoningStep[]
  final_answer: string
  verification?: string
  confidence: number
  provider?: LLMProvider
  model?: string
  latency_ms: number
  from_cache: boolean
  ensemble_scores?: Record<string, number>
}

export interface DecomposeRequest {
  problem: string
  provider?: LLMProvider
}

export interface DecomposeResponse {
  main_problem: string
  sub_problems: SubProblem[]
  solving_order: number[]
  total_steps: number
}

export interface CompareResponse {
  problem: string
  providers: Record<string, {
    answer: string
    confidence: number
    latency_ms: number
    steps_count: number
    error?: string
  }>
  best_provider?: LLMProvider
  fastest_provider?: LLMProvider
}

export interface ProviderInfo {
  name: LLMProvider
  display_name: string
  model: string
  capabilities: string[]
  recommended_for: string
}

export interface ProvidersListResponse {
  providers: ProviderInfo[]
  default_provider: LLMProvider
  ensemble_enabled: boolean
}

// Mermaid visualization types (REQ-6.2)
export interface MermaidResponse {
  mermaid: string
  node_count: number
  edge_count: number
  critical_path: string[]
  has_branches: boolean
  tree_data?: {
    nodes: Array<{
      id: string
      step_number: number
      step_type: string
      description: string
      reasoning: string
      result?: string
      confidence: number
      is_verified: boolean
    }>
    edges: Array<{
      source: string
      target: string
      type: string
    }>
    metadata: Record<string, unknown>
  }
}

// API endpoints
const REASONING_API = '/api/v1/reasoning';

class ReasoningService {
  /**
   * Solve a problem with step-by-step reasoning
   */
  async solve(request: SolveRequest): Promise<ApiResponse<SolveResponse>> {
    return apiClient.post<SolveResponse>(`${REASONING_API}/solve`, request);
  }

  /**
   * Solve with specific provider
   */
  async solveWithProvider(
    problem: string,
    provider: LLMProvider,
    maxSteps = 10,
  ): Promise<ApiResponse<SolveResponse>> {
    return this.solve({
      problem,
      provider,
      use_ensemble: false,
      max_steps: maxSteps,
      use_cache: true,
    });
  }

  /**
   * Solve with ensemble voting
   */
  async solveWithEnsemble(
    problem: string,
    maxSteps = 10,
  ): Promise<ApiResponse<SolveResponse>> {
    return this.solve({
      problem,
      use_ensemble: true,
      max_steps: maxSteps,
      use_cache: true,
    });
  }

  /**
   * Get a reasoning session by ID
   */
  async getSession(sessionId: string): Promise<ApiResponse<ReasoningSession>> {
    return apiClient.get<ReasoningSession>(`${REASONING_API}/session/${sessionId}`);
  }

  /**
   * Get all steps for a session
   */
  async getSessionSteps(sessionId: string): Promise<ApiResponse<{
    session_id: string
    steps: ReasoningStep[]
  }>> {
    return apiClient.get(`${REASONING_API}/session/${sessionId}/steps`);
  }

  /**
   * Get Mermaid diagram for a session (REQ-6.2)
   *
   * Returns a Mermaid flowchart visualization of the reasoning steps.
   */
  async getSessionMermaid(
    sessionId: string,
    options?: {
      orientation?: 'TD' | 'LR'
      showConfidence?: boolean
      includeTreeData?: boolean
    },
  ): Promise<ApiResponse<MermaidResponse>> {
    const params = {
      orientation: options?.orientation || 'TD',
      show_confidence: options?.showConfidence ?? true,
      include_tree_data: options?.includeTreeData ?? true,
    };
    return apiClient.get<MermaidResponse>(
      `${REASONING_API}/session/${sessionId}/mermaid`,
      { params },
    );
  }

  /**
   * Decompose a complex problem into sub-problems
   */
  async decompose(request: DecomposeRequest): Promise<ApiResponse<DecomposeResponse>> {
    return apiClient.post<DecomposeResponse>(`${REASONING_API}/decompose`, request);
  }

  /**
   * Compare all providers on the same problem
   */
  async compareProviders(problem: string): Promise<ApiResponse<CompareResponse>> {
    return apiClient.post<CompareResponse>(`${REASONING_API}/compare`, { problem });
  }

  /**
   * Invalidate cache for a specific problem or all expired entries
   */
  async invalidateCache(problem?: string): Promise<ApiResponse<{ invalidated_count: number }>> {
    return apiClient.post(`${REASONING_API}/cache/invalidate`, { problem });
  }

  /**
   * Get current user's recent reasoning sessions
   */
  async getMySessions(limit = 20): Promise<ApiResponse<{ sessions: ReasoningSession[] }>> {
    return apiClient.get(`${REASONING_API}/my-sessions`, { params: { limit } });
  }

  /**
   * List available LLM providers
   */
  async getProviders(): Promise<ApiResponse<ProvidersListResponse>> {
    return apiClient.get<ProvidersListResponse>(`${REASONING_API}/providers`, { cache: true });
  }

  /**
   * Check reasoning service health
   */
  async healthCheck(): Promise<ApiResponse<{ status: string; service: string; version: string }>> {
    return apiClient.get(`${REASONING_API}/health`);
  }
}

// Singleton instance
export const reasoningService = new ReasoningService();

// Named exports for convenience
export const {
  solve: solveReasoning,
  solveWithProvider,
  solveWithEnsemble,
  getSession: getReasoningSession,
  getSessionSteps: getReasoningSteps,
  getSessionMermaid: getReasoningMermaid,
  decompose: decomposeProblem,
  compareProviders,
  invalidateCache: invalidateReasoningCache,
  getMySessions: getMyReasoningSessions,
  getProviders: getReasoningProviders,
} = reasoningService;

export default reasoningService;

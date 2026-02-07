/**
 * Sequential Thinking Viewer Component
 * Main component for displaying step-by-step problem solving
 *
 * Features:
 * - Multi-LLM provider support (Gemini, OpenAI, Claude, Qwen)
 * - Ensemble voting display
 * - Progressive step disclosure
 * - Cache indicator
 */

import {
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  Send,
  RotateCcw,
  Clock,
  Database,
  Layers,
  Trophy,
  GitBranch,
  Share2,
} from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect, useCallback  } from 'react';

import { useSequentialThinking } from '../../hooks/useSequentialThinking';
import { reasoningService, type LLMProvider, type MermaidResponse } from '../../services/reasoningService';

import { MermaidThoughtTree } from './MermaidThoughtTree';
import { ProviderBadge, EnsembleScores } from './ProviderBadge';
import { ReasoningStepCard } from './ReasoningStepCard';
import { ThoughtTree } from './ThoughtTree';

interface SequentialThinkingViewerProps {
  initialProblem?: string
  defaultProvider?: LLMProvider
  enableEnsemble?: boolean
  enableVisualization?: boolean
  onSolutionComplete?: (answer: string) => void
  onStepClick?: (stepId: string) => void
  className?: string
}

export const SequentialThinkingViewer: React.FC<SequentialThinkingViewerProps> = ({
  initialProblem = '',
  defaultProvider,
  enableEnsemble = true,
  enableVisualization = true,
  onSolutionComplete,
  onStepClick,
  className = '',
}) => {
  const [problemInput, setProblemInput] = useState(initialProblem);
  const [showAllSteps, setShowAllSteps] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider | 'ensemble'>(
    defaultProvider || 'gemini',
  );

  // Visualization state (REQ-6.2)
  const [showVisualization, setShowVisualization] = useState(false);
  const [visualizationType, setVisualizationType] = useState<'mermaid' | 'tree'>('mermaid');
  const [mermaidData, setMermaidData] = useState<MermaidResponse | null>(null);
  const [visualizationLoading, setVisualizationLoading] = useState(false);

  const {
    solution,
    loading,
    error,
    currentStep,
    fromCache,
    providers,
    solve,
    solveWithEnsemble,
    nextStep,
    previousStep,
    goToStep,
    loadProviders,
    reset,
    clearError,
  } = useSequentialThinking();

  // Load providers on mount
  useEffect(() => {
    loadProviders();
  }, [loadProviders]);

  // Set initial problem
  useEffect(() => {
    if (initialProblem) {
      setProblemInput(initialProblem);
    }
  }, [initialProblem]);

  // Handle solution complete
  useEffect(() => {
    if (solution?.final_answer && onSolutionComplete) {
      onSolutionComplete(solution.final_answer);
    }
  }, [solution?.final_answer, onSolutionComplete]);

  // Load Mermaid diagram when visualization is enabled (REQ-6.2)
  useEffect(() => {
    const loadMermaidDiagram = async () => {
      if (!showVisualization || !solution?.session_id || visualizationType !== 'mermaid') {
        return;
      }

      setVisualizationLoading(true);
      try {
        const response = await reasoningService.getSessionMermaid(
          solution.session_id,
          { showConfidence: true, includeTreeData: true },
        );
        if (response.success && response.data) {
          setMermaidData(response.data);
        }
      } catch (err) {
        console.error('Failed to load Mermaid diagram:', err);
      } finally {
        setVisualizationLoading(false);
      }
    };

    loadMermaidDiagram();
  }, [showVisualization, solution?.session_id, visualizationType]);

  // Handle step click for visualization
  const handleStepClick = useCallback((stepId: string) => {
    // Find step index from ID
    const stepIndex = solution?.steps.findIndex(s => s.id === stepId);
    if (stepIndex !== undefined && stepIndex >= 0) {
      goToStep(stepIndex + 1);
    }
    onStepClick?.(stepId);
  }, [solution?.steps, goToStep, onStepClick]);

  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!problemInput.trim()) {return;}

    if (selectedProvider === 'ensemble') {
      await solveWithEnsemble(problemInput.trim());
    } else {
      await solve(problemInput.trim(), { provider: selectedProvider as LLMProvider });
    }
  }, [problemInput, selectedProvider, solve, solveWithEnsemble]);

  const handleReset = useCallback(() => {
    reset();
    setProblemInput('');
    setShowVisualization(false);
    setMermaidData(null);
  }, [reset]);

  const totalSteps = solution?.steps.length || 0;

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      {/* Input Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <form onSubmit={handleSubmit}>
          <label htmlFor="problem-input" className="block text-lg font-semibold text-gray-800 mb-3">
            Problemi Girin
          </label>

          <div className="flex gap-3 mb-4">
            <input
              id="problem-input"
              type="text"
              value={problemInput}
              onChange={(e) => setProblemInput(e.target.value)}
              placeholder="Ornek: x^2 + 5x + 6 = 0 denklemini coz"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !problemInput.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center gap-2 font-medium transition-colors"
            >
              <Send size={20} />
              <span>Coz</span>
            </button>
          </div>

          {/* Provider Selection */}
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-medium text-gray-600">Provider:</span>

            {providers?.providers.map((p) => (
              <button
                key={p.name}
                type="button"
                onClick={() => setSelectedProvider(p.name)}
                className={`
                  px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                  ${selectedProvider === p.name
                    ? 'bg-blue-600 text-white ring-2 ring-blue-300'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                {p.display_name}
              </button>
            ))}

            {enableEnsemble && (
              <button
                type="button"
                onClick={() => setSelectedProvider('ensemble')}
                className={`
                  px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1
                  ${selectedProvider === 'ensemble'
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white ring-2 ring-purple-300'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                `}
              >
                <Trophy size={14} />
                <span>Ensemble</span>
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <p className="text-red-700">{error}</p>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 text-sm underline"
            >
              Kapat
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg shadow-md p-8 mb-6 flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Problem cozuluyor...</p>
          <p className="text-sm text-gray-500 mt-2">
            {selectedProvider === 'ensemble'
              ? 'Tum provider\'lar sorgulanıyor...'
              : `${selectedProvider} ile cozum aranıyor...`
            }
          </p>
        </div>
      )}

      {/* Solution Display */}
      {solution && !loading && (
        <>
          {/* Solution Header */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-800 mb-2">Cozum</h2>
                <p className="text-gray-600">{solution.problem}</p>
              </div>

              <button
                onClick={handleReset}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="Sifirla"
              >
                <RotateCcw size={20} />
              </button>
            </div>

            {/* Metadata */}
            <div className="flex flex-wrap gap-3 mb-4">
              {solution.provider && (
                <ProviderBadge provider={solution.provider} />
              )}

              <div className="flex items-center gap-1 px-3 py-1 bg-gray-100 rounded-full text-sm">
                <Layers size={14} />
                <span>{totalSteps} adim</span>
              </div>

              <div className="flex items-center gap-1 px-3 py-1 bg-gray-100 rounded-full text-sm">
                <Clock size={14} />
                <span>{solution.latency_ms.toFixed(0)}ms</span>
              </div>

              {fromCache && (
                <div className="flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                  <Database size={14} />
                  <span>Cache</span>
                </div>
              )}

              <div className={`
                px-3 py-1 rounded-full text-sm font-medium
                ${solution.confidence >= 0.8
                  ? 'bg-green-100 text-green-700'
                  : solution.confidence >= 0.5
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-red-100 text-red-700'
                }
              `}>
                Guven: %{(solution.confidence * 100).toFixed(0)}
              </div>
            </div>

            {/* Understanding */}
            {solution.understanding && (
              <div className="bg-blue-50 rounded-lg p-4 mb-4">
                <h3 className="font-semibold text-blue-800 mb-2">Problemi Anlama</h3>
                <p className="text-blue-700">{solution.understanding}</p>
              </div>
            )}

            {/* Ensemble Scores */}
            {solution.ensemble_scores && Object.keys(solution.ensemble_scores).length > 0 && (
              <div className="border-t pt-4 mt-4">
                <h3 className="font-semibold text-gray-800 mb-3">Provider Skorlari</h3>
                <EnsembleScores
                  scores={solution.ensemble_scores}
                  winningProvider={solution.provider}
                />
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="bg-white rounded-lg shadow-md p-4 mb-6">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowAllSteps(!showAllSteps)}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium text-gray-700 transition-colors"
                >
                  {showAllSteps ? (
                    <>
                      <EyeOff size={20} />
                      <span>Adim Adim Goster</span>
                    </>
                  ) : (
                    <>
                      <Eye size={20} />
                      <span>Tumunu Goster</span>
                    </>
                  )}
                </button>

                {/* Visualization Toggle (REQ-6.2) */}
                {enableVisualization && (
                  <button
                    onClick={() => setShowVisualization(!showVisualization)}
                    className={`
                      flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
                      ${showVisualization
                        ? 'bg-purple-600 text-white hover:bg-purple-700'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }
                    `}
                    title="Dusunce agaci gorsellestirmesi"
                  >
                    <GitBranch size={20} />
                    <span>Gorsellestir</span>
                  </button>
                )}
              </div>

              {/* Step Progress */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Adim:</span>
                <div className="flex items-center gap-1">
                  {solution.steps.map((_, i) => (
                    <button
                      key={i}
                      onClick={() => goToStep(i + 1)}
                      className={`
                        w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-all
                        ${i + 1 === currentStep
                          ? 'bg-blue-600 text-white ring-2 ring-blue-300'
                          : i + 1 < currentStep
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                        }
                      `}
                    >
                      {i + 1}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Visualization Type Selector */}
            {showVisualization && (
              <div className="flex items-center gap-3 mt-4 pt-4 border-t">
                <span className="text-sm font-medium text-gray-600">Gorsellestirme Tipi:</span>
                <button
                  onClick={() => setVisualizationType('mermaid')}
                  className={`
                    flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                    ${visualizationType === 'mermaid'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                  `}
                >
                  <Share2 size={14} />
                  <span>Mermaid</span>
                </button>
                <button
                  onClick={() => setVisualizationType('tree')}
                  className={`
                    flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                    ${visualizationType === 'tree'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                  `}
                >
                  <GitBranch size={14} />
                  <span>Tree</span>
                </button>
              </div>
            )}
          </div>

          {/* Visualization Panel (REQ-6.2) */}
          {showVisualization && (
            <div className="bg-white rounded-lg shadow-md mb-6 overflow-hidden">
              <div className="px-4 py-3 bg-purple-50 border-b flex items-center justify-between">
                <h3 className="font-semibold text-purple-800 flex items-center gap-2">
                  <GitBranch size={18} />
                  Dusunce Agaci
                </h3>
                {mermaidData && (
                  <div className="flex items-center gap-3 text-sm text-purple-600">
                    <span>{mermaidData.node_count} dugum</span>
                    <span>{mermaidData.edge_count} baglanti</span>
                    {mermaidData.has_branches && <span className="bg-purple-100 px-2 py-0.5 rounded">Dallanmalar var</span>}
                  </div>
                )}
              </div>

              {visualizationLoading ? (
                <div className="flex items-center justify-center p-12">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600" />
                </div>
              ) : visualizationType === 'mermaid' && mermaidData ? (
                <MermaidThoughtTree
                  mermaidCode={mermaidData.mermaid}
                  criticalPath={mermaidData.critical_path}
                  onNodeClick={handleStepClick}
                  theme="default"
                  showControls={true}
                />
              ) : (
                <ThoughtTree
                  steps={solution.steps}
                  orientation="vertical"
                  currentStep={currentStep}
                  onStepClick={(stepNumber) => {
                    goToStep(stepNumber);
                    const step = solution.steps.find(s => s.step_number === stepNumber);
                    if (step?.id) {onStepClick?.(step.id);}
                  }}
                  className="p-4"
                />
              )}
            </div>
          )}

          {/* Steps */}
          <div className="space-y-4">
            {showAllSteps
              ? solution.steps.map((step, i) => (
                  <ReasoningStepCard
                    key={step.id || i}
                    step={step}
                    isActive={i + 1 === currentStep}
                    isCompleted={i + 1 < currentStep}
                    onStepClick={() => goToStep(i + 1)}
                  />
                ))
              : solution.steps
                  .filter((_, i) => i + 1 === currentStep)
                  .map((step, i) => (
                    <ReasoningStepCard
                      key={step.id || i}
                      step={step}
                      isActive={true}
                      showDetails={true}
                    />
                  ))
            }
          </div>

          {/* Navigation */}
          {!showAllSteps && (
            <div className="bg-white rounded-lg shadow-md p-4 mt-6">
              <div className="flex items-center justify-between">
                <button
                  onClick={previousStep}
                  disabled={currentStep === 1}
                  className={`
                    flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors
                    ${currentStep === 1
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                    }
                  `}
                >
                  <ChevronLeft size={20} />
                  <span>Onceki</span>
                </button>

                <div className="text-center">
                  <p className="text-sm text-gray-600">
                    Adim {currentStep} / {totalSteps}
                  </p>
                </div>

                <button
                  onClick={nextStep}
                  disabled={currentStep === totalSteps}
                  className={`
                    flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors
                    ${currentStep === totalSteps
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                    }
                  `}
                >
                  <span>Sonraki</span>
                  <ChevronRight size={20} />
                </button>
              </div>
            </div>
          )}

          {/* Final Answer */}
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-6 mt-6">
            <h3 className="font-bold text-green-800 mb-2 flex items-center gap-2">
              <Trophy className="text-green-600" size={24} />
              Son Cevap
            </h3>
            <p className="text-green-900 text-lg font-medium">{solution.final_answer}</p>

            {solution.verification && (
              <div className="mt-4 pt-4 border-t border-green-200">
                <h4 className="font-semibold text-green-700 mb-1">Dogrulama</h4>
                <p className="text-green-600 text-sm">{solution.verification}</p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default SequentialThinkingViewer;

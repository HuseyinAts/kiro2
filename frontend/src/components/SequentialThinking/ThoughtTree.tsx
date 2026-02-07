/**
 * Thought Tree Component
 * Visual representation of reasoning steps as a tree/diagram
 *
 * Uses Mermaid-like visualization for step dependencies
 */

import {
  Lightbulb,
  GitBranch,
  Calculator,
  Brain,
  CheckCircle2,
  Target,
  ArrowDown,
} from 'lucide-react';
import * as React from 'react';
import {  useMemo  } from 'react';

import type { ReasoningStep, SubProblem, ReasoningStepType } from '../../services/reasoningService';

interface ThoughtTreeProps {
  steps?: ReasoningStep[]
  subProblems?: SubProblem[]
  currentStep?: number
  onStepClick?: (stepNumber: number) => void
  orientation?: 'vertical' | 'horizontal'
  compact?: boolean
  className?: string
}

const STEP_ICONS: Record<ReasoningStepType, React.ElementType> = {
  understanding: Lightbulb,
  decomposition: GitBranch,
  calculation: Calculator,
  inference: Brain,
  verification: CheckCircle2,
  conclusion: Target,
};

const STEP_COLORS: Record<ReasoningStepType, string> = {
  understanding: 'bg-yellow-100 border-yellow-400 text-yellow-800',
  decomposition: 'bg-purple-100 border-purple-400 text-purple-800',
  calculation: 'bg-blue-100 border-blue-400 text-blue-800',
  inference: 'bg-indigo-100 border-indigo-400 text-indigo-800',
  verification: 'bg-green-100 border-green-400 text-green-800',
  conclusion: 'bg-red-100 border-red-400 text-red-800',
};

export const ThoughtTree: React.FC<ThoughtTreeProps> = ({
  steps = [],
  subProblems = [],
  currentStep = 1,
  onStepClick,
  orientation = 'vertical',
  compact = false,
  className = '',
}) => {
  // Group steps by type for visualization (kept for future use)
  const _stepGroups = useMemo(() => {
    const groups: Record<string, ReasoningStep[]> = {};
    steps.forEach(step => {
      const type = step.step_type || 'inference';
      if (!groups[type]) {
        groups[type] = [];
      }
      groups[type].push(step);
    });
    return groups;
  }, [steps]);

  // Mark as available for future use
  void _stepGroups;

  if (steps.length === 0 && subProblems.length === 0) {
    return (
      <div className={`text-center text-gray-500 p-8 ${className}`}>
        Henuz adim yok
      </div>
    );
  }

  // Vertical layout
  if (orientation === 'vertical') {
    return (
      <div className={`${className}`}>
        {/* Legend */}
        <div className="flex flex-wrap gap-2 mb-6 p-3 bg-gray-50 rounded-lg">
          {Object.entries(STEP_ICONS).map(([type, Icon]) => (
            <div key={type} className="flex items-center gap-1 text-xs">
              <div className={`p-1 rounded ${STEP_COLORS[type as ReasoningStepType]}`}>
                <Icon size={12} />
              </div>
              <span className="capitalize text-gray-600">{type}</span>
            </div>
          ))}
        </div>

        {/* Steps Tree */}
        <div className="relative">
          {steps.map((step, index) => {
            const stepType = step.step_type || 'inference';
            const Icon = STEP_ICONS[stepType];
            const colorClass = STEP_COLORS[stepType];
            const isActive = step.step_number === currentStep;
            const isCompleted = step.step_number < currentStep;

            return (
              <div key={step.id || index} className="relative">
                {/* Connector Line */}
                {index > 0 && (
                  <div className="flex justify-center py-2">
                    <ArrowDown
                      className={`
                        ${isCompleted ? 'text-green-500' : 'text-gray-300'}
                      `}
                      size={20}
                    />
                  </div>
                )}

                {/* Step Node */}
                <div
                  onClick={() => onStepClick?.(step.step_number)}
                  className={`
                    flex items-start gap-3 p-4 rounded-lg border-2 transition-all
                    ${isActive
                      ? 'ring-2 ring-blue-400 shadow-lg'
                      : isCompleted
                      ? 'opacity-75'
                      : ''
                    }
                    ${colorClass}
                    ${onStepClick ? 'cursor-pointer hover:shadow-md' : ''}
                  `}
                >
                  {/* Step Number & Icon */}
                  <div className="flex flex-col items-center gap-1">
                    <div
                      className={`
                        w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm
                        ${isCompleted
                          ? 'bg-green-500 text-white'
                          : isActive
                          ? 'bg-blue-500 text-white'
                          : 'bg-white border-2 border-current'
                        }
                      `}
                    >
                      {isCompleted ? <CheckCircle2 size={16} /> : step.step_number}
                    </div>
                    <Icon size={16} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className={`font-medium ${compact ? 'text-sm' : ''}`}>
                      {step.description}
                    </p>

                    {!compact && step.result && (
                      <p className="text-sm mt-1 opacity-80">
                        Sonuc: {step.result}
                      </p>
                    )}

                    {/* Confidence */}
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex-1 h-1.5 bg-white/50 rounded-full overflow-hidden">
                        <div
                          className={`
                            h-full rounded-full transition-all
                            ${step.confidence >= 0.8
                              ? 'bg-green-500'
                              : step.confidence >= 0.5
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                            }
                          `}
                          style={{ width: `${step.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium">
                        %{(step.confidence * 100).toFixed(0)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Horizontal layout
  return (
    <div className={`overflow-x-auto ${className}`}>
      <div className="flex items-center gap-4 min-w-max p-4">
        {steps.map((step, index) => {
          const stepType = step.step_type || 'inference';
          const Icon = STEP_ICONS[stepType];
          const colorClass = STEP_COLORS[stepType];
          const isActive = step.step_number === currentStep;
          const isCompleted = step.step_number < currentStep;

          return (
            <React.Fragment key={step.id || index}>
              {/* Connector */}
              {index > 0 && (
                <div
                  className={`
                    w-8 h-0.5
                    ${isCompleted ? 'bg-green-500' : 'bg-gray-300'}
                  `}
                />
              )}

              {/* Node */}
              <div
                onClick={() => onStepClick?.(step.step_number)}
                className={`
                  flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all
                  min-w-[120px] max-w-[160px]
                  ${isActive ? 'ring-2 ring-blue-400 shadow-lg' : ''}
                  ${colorClass}
                  ${onStepClick ? 'cursor-pointer hover:shadow-md' : ''}
                `}
              >
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm
                    ${isCompleted
                      ? 'bg-green-500 text-white'
                      : isActive
                      ? 'bg-blue-500 text-white'
                      : 'bg-white border-2 border-current'
                    }
                  `}
                >
                  {isCompleted ? <CheckCircle2 size={16} /> : step.step_number}
                </div>

                <Icon size={20} />

                <p className="text-xs text-center font-medium line-clamp-2">
                  {step.description}
                </p>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

// Sub-problems tree for decomposition
interface SubProblemTreeProps {
  subProblems: SubProblem[]
  onSubProblemClick?: (id: string) => void
  className?: string
}

export const SubProblemTree: React.FC<SubProblemTreeProps> = ({
  subProblems,
  onSubProblemClick,
  className = '',
}) => {
  // Sort by solving order
  const sortedProblems = useMemo(() =>
    [...subProblems].sort((a, b) => a.order_index - b.order_index),
    [subProblems],
  );

  if (subProblems.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <h3 className="font-semibold text-gray-800 flex items-center gap-2">
        <GitBranch size={20} />
        Alt Problemler
      </h3>

      <div className="grid gap-3 md:grid-cols-2">
        {sortedProblems.map((sp) => (
          <div
            key={sp.id}
            onClick={() => onSubProblemClick?.(sp.id)}
            className={`
              p-4 rounded-lg border-2 transition-all
              ${sp.is_solved
                ? 'bg-green-50 border-green-300'
                : 'bg-gray-50 border-gray-200 hover:border-gray-300'
              }
              ${onSubProblemClick ? 'cursor-pointer' : ''}
            `}
          >
            <div className="flex items-start gap-3">
              <div
                className={`
                  w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                  ${sp.is_solved
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-300 text-gray-700'
                  }
                `}
              >
                {sp.order_index}
              </div>

              <div className="flex-1">
                <h4 className="font-medium text-gray-800">{sp.title}</h4>
                <p className="text-sm text-gray-600 mt-1">{sp.description}</p>

                <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                  <span>Zorluk: {(sp.difficulty * 100).toFixed(0)}%</span>
                  <span>~{sp.estimated_steps} adim</span>
                </div>

                {sp.dependencies.length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    Bagimliliklar: {sp.dependencies.length} alt problem
                  </div>
                )}
              </div>

              {sp.is_solved && (
                <CheckCircle2 className="text-green-500" size={20} />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ThoughtTree;

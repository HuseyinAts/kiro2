/**
 * Reasoning Step Card Component
 * Displays a single reasoning step with type indicator and details
 */

import {
  Lightbulb,
  GitBranch,
  Calculator,
  Brain,
  CheckCircle2,
  Target,
  ChevronDown,
  ChevronUp,
  Check,
} from 'lucide-react';
import * as React from 'react';
import {  useState  } from 'react';

import type { ReasoningStep, ReasoningStepType } from '../../services/reasoningService';

interface ReasoningStepCardProps {
  step: ReasoningStep
  isActive?: boolean
  isCompleted?: boolean
  showDetails?: boolean
  onStepClick?: () => void
}

const STEP_TYPE_CONFIG: Record<ReasoningStepType, {
  icon: React.ElementType
  label: string
  color: string
  bgColor: string
  borderColor: string
}> = {
  understanding: {
    icon: Lightbulb,
    label: 'Anlama',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
  },
  decomposition: {
    icon: GitBranch,
    label: 'Ayristirma',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
  },
  calculation: {
    icon: Calculator,
    label: 'Hesaplama',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
  },
  inference: {
    icon: Brain,
    label: 'Cikarim',
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
  },
  verification: {
    icon: CheckCircle2,
    label: 'Dogrulama',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
  },
  conclusion: {
    icon: Target,
    label: 'Sonuc',
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
  },
};

export const ReasoningStepCard: React.FC<ReasoningStepCardProps> = ({
  step,
  isActive = false,
  isCompleted = false,
  showDetails = true,
  onStepClick,
}) => {
  const [isExpanded, setIsExpanded] = useState(showDetails);

  const stepType = step.step_type || 'inference';
  const config = STEP_TYPE_CONFIG[stepType] || STEP_TYPE_CONFIG.inference;
  const Icon = config.icon;

  const confidenceColor = step.confidence >= 0.8
    ? 'text-green-600'
    : step.confidence >= 0.5
    ? 'text-yellow-600'
    : 'text-red-600';

  return (
    <div
      className={`
        rounded-lg border-2 transition-all duration-200
        ${isActive
          ? 'border-blue-400 ring-2 ring-blue-100 shadow-lg'
          : isCompleted
          ? 'border-green-300 bg-green-50/30'
          : 'border-gray-200 hover:border-gray-300'
        }
        ${onStepClick ? 'cursor-pointer' : ''}
      `}
      onClick={onStepClick}
    >
      {/* Header */}
      <div
        className={`
          flex items-center justify-between p-4
          ${config.bgColor} rounded-t-lg
        `}
      >
        <div className="flex items-center gap-3">
          {/* Step Number */}
          <div
            className={`
              w-8 h-8 rounded-full flex items-center justify-center
              ${isCompleted
                ? 'bg-green-500 text-white'
                : isActive
                ? 'bg-blue-500 text-white'
                : 'bg-white border-2 border-gray-300 text-gray-600'
              }
              font-bold text-sm
            `}
          >
            {isCompleted ? <Check size={16} /> : step.step_number}
          </div>

          {/* Step Type */}
          <div className="flex items-center gap-2">
            <Icon className={config.color} size={20} />
            <span className={`font-medium ${config.color}`}>{config.label}</span>
          </div>
        </div>

        {/* Confidence & Toggle */}
        <div className="flex items-center gap-3">
          <span className={`text-sm font-medium ${confidenceColor}`}>
            %{(step.confidence * 100).toFixed(0)}
          </span>

          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="p-1 hover:bg-white/50 rounded-full transition-colors"
          >
            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 bg-white rounded-b-lg">
        {/* Description */}
        <p className="text-gray-800 font-medium mb-2">{step.description}</p>

        {/* Expandable Details */}
        {isExpanded && (
          <div className="mt-4 space-y-3">
            {/* Reasoning */}
            {step.reasoning && (
              <div className="bg-gray-50 rounded-lg p-3">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Gerekce
                </span>
                <p className="mt-1 text-gray-700 text-sm">{step.reasoning}</p>
              </div>
            )}

            {/* Result */}
            {step.result && (
              <div className="bg-blue-50 rounded-lg p-3">
                <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider">
                  Sonuc
                </span>
                <p className="mt-1 text-blue-800 font-medium">{step.result}</p>
              </div>
            )}

            {/* Verification */}
            {step.is_verified && step.verification_result && (
              <div className="bg-green-50 rounded-lg p-3 border border-green-200">
                <span className="text-xs font-semibold text-green-600 uppercase tracking-wider flex items-center gap-1">
                  <CheckCircle2 size={14} />
                  Dogrulandi
                </span>
                <p className="mt-1 text-green-700 text-sm">{step.verification_result}</p>
              </div>
            )}

            {/* Metadata */}
            {step.latency_ms !== undefined && step.latency_ms > 0 && (
              <div className="flex items-center gap-4 text-xs text-gray-500 pt-2 border-t">
                <span>Latency: {step.latency_ms.toFixed(0)}ms</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReasoningStepCard;

/**
 * Provider Badge Component
 * Displays LLM provider indicator with icon and color coding
 */

import { Sparkles, Zap, Brain, Cpu } from 'lucide-react';
import * as React from 'react';

import type { LLMProvider } from '../../services/reasoningService';

interface ProviderBadgeProps {
  provider: LLMProvider | string | null
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const PROVIDER_CONFIG: Record<string, {
  icon: React.ElementType
  label: string
  bgColor: string
  textColor: string
  borderColor: string
}> = {
  gemini: {
    icon: Sparkles,
    label: 'Gemini',
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
    borderColor: 'border-blue-200',
  },
  openai: {
    icon: Zap,
    label: 'OpenAI',
    bgColor: 'bg-green-50',
    textColor: 'text-green-700',
    borderColor: 'border-green-200',
  },
  claude: {
    icon: Brain,
    label: 'Claude',
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-700',
    borderColor: 'border-orange-200',
  },
  qwen: {
    icon: Cpu,
    label: 'Qwen',
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-700',
    borderColor: 'border-purple-200',
  },
  ensemble: {
    icon: Sparkles,
    label: 'Ensemble',
    bgColor: 'bg-gradient-to-r from-blue-50 via-green-50 to-orange-50',
    textColor: 'text-gray-700',
    borderColor: 'border-gray-300',
  },
};

const SIZE_CONFIG = {
  sm: {
    padding: 'px-2 py-0.5',
    text: 'text-xs',
    iconSize: 12,
    gap: 'gap-1',
  },
  md: {
    padding: 'px-3 py-1',
    text: 'text-sm',
    iconSize: 16,
    gap: 'gap-1.5',
  },
  lg: {
    padding: 'px-4 py-1.5',
    text: 'text-base',
    iconSize: 20,
    gap: 'gap-2',
  },
};

export const ProviderBadge: React.FC<ProviderBadgeProps> = ({
  provider,
  showLabel = true,
  size = 'md',
  className = '',
}) => {
  if (!provider) {return null;}

  const providerKey = provider.toLowerCase();
  const config = PROVIDER_CONFIG[providerKey] || PROVIDER_CONFIG.gemini;
  const sizeConfig = SIZE_CONFIG[size];
  const Icon = config.icon;

  return (
    <span
      className={`
        inline-flex items-center ${sizeConfig.gap}
        ${sizeConfig.padding} ${sizeConfig.text}
        ${config.bgColor} ${config.textColor}
        border ${config.borderColor}
        rounded-full font-medium
        ${className}
      `.trim()}
      title={`Provider: ${config.label}`}
    >
      <Icon size={sizeConfig.iconSize} />
      {showLabel && <span>{config.label}</span>}
    </span>
  );
};

// Ensemble scores display
interface EnsembleScoresProps {
  scores: Record<string, number>
  winningProvider?: string | null
}

export const EnsembleScores: React.FC<EnsembleScoresProps> = ({
  scores,
  winningProvider,
}) => {
  return (
    <div className="flex flex-wrap gap-2">
      {Object.entries(scores).map(([provider, score]) => (
        <div
          key={provider}
          className={`
            flex items-center gap-2 px-3 py-1.5 rounded-lg
            ${provider === winningProvider
              ? 'bg-green-100 border-2 border-green-400'
              : 'bg-gray-50 border border-gray-200'
            }
          `}
        >
          <ProviderBadge provider={provider} size="sm" showLabel={false} />
          <span className="text-sm font-medium">
            {(score * 100).toFixed(0)}%
          </span>
          {provider === winningProvider && (
            <span className="text-xs text-green-600 font-semibold">Kazanan</span>
          )}
        </div>
      ))}
    </div>
  );
};

export default ProviderBadge;

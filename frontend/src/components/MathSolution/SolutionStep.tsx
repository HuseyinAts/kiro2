/**
 * Tek Çözüm Adımı Bileşeni
 * Requirements: REQ-51.21-51.25, REQ-51.26-51.30 (Animasyonlu geçişler)
 *
 * Bu bileşen:
 * - Tek bir çözüm adımını gösterir
 * - Animasyonlu geçişler sağlar
 * - İpucu sistemi entegrasyonu
 * - Hata vurgulama desteği
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Lightbulb, AlertCircle, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import { useState, useEffect } from 'react';

import { useAnimationContext } from './AnimationController';
import HintSystem from './HintSystem';
import MathExpressionAnimated from './MathExpressionAnimated';

interface SolutionStepProps {
  step: {
    step_number: number;
    step_type: string;
    title: string;
    description: string;
    math_expression: string;
    explanation: string;
    visual_aids?: string[];
    color_coding?: Record<string, string>;
    hints: string[];
    common_errors: string[];
    duration_estimate_seconds: number;
  };
  problemId: string;
  isActive: boolean;
  isCompleted: boolean;
  showAnimations: boolean;
  previousExpression?: string;
}

const SolutionStep: React.FC<SolutionStepProps> = ({
  step,
  problemId,
  isActive,
  isCompleted,
  showAnimations,
  previousExpression,
}) => {
  const [showHints, setShowHints] = useState(false);
  const [showCommonErrors, setShowCommonErrors] = useState(false);
  const [isExpanded, setIsExpanded] = useState(isActive);
  // Animation context is available via useAnimationContext hook if needed
  void useAnimationContext();

  // Active olduğunda otomatik aç
  useEffect(() => {
    if (isActive) {
      setIsExpanded(true);
    }
  }, [isActive]);

  // Adım türüne göre renk
  const getStepTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      setup: 'bg-blue-100 text-blue-800',
      simplification: 'bg-green-100 text-green-800',
      operation: 'bg-yellow-100 text-yellow-800',
      substitution: 'bg-purple-100 text-purple-800',
      verification: 'bg-pink-100 text-pink-800',
      conclusion: 'bg-indigo-100 text-indigo-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  // Adım türü ikon
  const getStepTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      setup: '📝',
      simplification: '🔄',
      operation: '➗',
      substitution: '🔀',
      verification: '✅',
      conclusion: '🎯',
    };
    return icons[type] || '📌';
  };

  // Animation variants
  const containerVariants = {
    hidden: {
      opacity: 0,
      y: 20,
      scale: 0.95,
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: 0.4,
        ease: 'easeOut',
      },
    },
    exit: {
      opacity: 0,
      y: -20,
      scale: 0.95,
      transition: {
        duration: 0.3,
      },
    },
  };

  const contentVariants = {
    collapsed: {
      height: 0,
      opacity: 0,
      transition: {
        duration: 0.3,
      },
    },
    expanded: {
      height: 'auto',
      opacity: 1,
      transition: {
        duration: 0.4,
        ease: 'easeOut',
      },
    },
  };

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={step.step_number}
        variants={showAnimations ? containerVariants : {}}
        initial={showAnimations ? 'hidden' : undefined}
        animate="visible"
        exit={showAnimations ? 'exit' : undefined}
        className={`bg-white rounded-lg shadow-md overflow-hidden border-2 transition-all ${
          isActive
            ? 'border-blue-500 ring-2 ring-blue-200'
            : isCompleted
            ? 'border-green-500'
            : 'border-gray-200'
        }`}
      >
        {/* Header */}
        <div
          className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Step Number */}
              <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                isCompleted
                  ? 'bg-green-500 text-white'
                  : isActive
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-600'
              }`}>
                {isCompleted ? <CheckCircle2 size={24} /> : step.step_number}
              </div>

              {/* Title & Type */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-2xl">{getStepTypeIcon(step.step_type)}</span>
                  <h3 className="text-lg font-semibold text-gray-800">
                    {step.title}
                  </h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStepTypeColor(step.step_type)}`}>
                    {step.step_type}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{step.description}</p>
              </div>
            </div>

            {/* Expand/Collapse Icon */}
            <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
              {isExpanded ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
            </button>
          </div>
        </div>

        {/* Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              variants={contentVariants}
              initial="collapsed"
              animate="expanded"
              exit="collapsed"
              className="border-t border-gray-200"
            >
              <div className="p-6 space-y-6">
                {/* Math Expression - Animated */}
                <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                  <MathExpressionAnimated
                    expression={step.math_expression}
                    previousExpression={previousExpression}
                    highlightColor="#FCD34D"
                  />
                </div>

                {/* Explanation */}
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white">
                      💡
                    </div>
                    <div>
                      <h4 className="font-semibold text-blue-900 mb-1">Açıklama</h4>
                      <p className="text-blue-800">{step.explanation}</p>
                    </div>
                  </div>
                </div>

                {/* Duration Estimate */}
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span>⏱️</span>
                  <span>Tahmini Süre: {step.duration_estimate_seconds} saniye</span>
                </div>

                {/* Hints Section */}
                {step.hints.length > 0 && (
                  <div>
                    <button
                      onClick={() => setShowHints(!showHints)}
                      className="flex items-center gap-2 px-4 py-2 bg-yellow-100 hover:bg-yellow-200 rounded-lg text-yellow-800 font-medium transition-colors"
                    >
                      <Lightbulb size={20} />
                      <span>{showHints ? 'İpuçlarını Gizle' : 'İpuçlarını Göster'}</span>
                    </button>

                    <AnimatePresence>
                      {showHints && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3 }}
                          className="mt-4"
                        >
                          <HintSystem
                            problemId={problemId}
                            stepNumber={step.step_number}
                            hints={step.hints}
                          />
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Common Errors Section */}
                {step.common_errors.length > 0 && (
                  <div>
                    <button
                      onClick={() => setShowCommonErrors(!showCommonErrors)}
                      className="flex items-center gap-2 px-4 py-2 bg-red-100 hover:bg-red-200 rounded-lg text-red-800 font-medium transition-colors"
                    >
                      <AlertCircle size={20} />
                      <span>{showCommonErrors ? 'Yaygın Hataları Gizle' : 'Yaygın Hataları Göster'}</span>
                    </button>

                    <AnimatePresence>
                      {showCommonErrors && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3 }}
                          className="mt-4 space-y-2"
                        >
                          {step.common_errors.map((error, index) => (
                            <div
                              key={index}
                              className="bg-red-50 border border-red-200 rounded-lg p-3"
                            >
                              <div className="flex items-start gap-2">
                                <span className="text-red-600 font-bold">⚠️</span>
                                <p className="text-red-800 text-sm">{error}</p>
                              </div>
                            </div>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Visual Aids */}
                {step.visual_aids && step.visual_aids.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Görsel Yardımcılar</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {step.visual_aids.map((url, index) => (
                        <img
                          key={index}
                          src={url}
                          alt={`Görsel ${index + 1}`}
                          className="rounded-lg border border-gray-200"
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </AnimatePresence>
  );
};

export default SolutionStep;

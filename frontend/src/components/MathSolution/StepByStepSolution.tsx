/**
 * Adım Adım Matematik Çözüm Bileşeni
 * Requirements: REQ-51.21-51.25 (Her adımı ayrı gösterme)
 *
 * Bu bileşen:
 * - Her çözüm adımını ayrı bir bölüm olarak gösterir
 * - Progressive disclosure (adımları teker teker açma) desteği
 * - İleri/geri navigasyon
 * - "Tümünü Göster" seçeneği
 */

import { ChevronLeft, ChevronRight, Eye, EyeOff, CheckCircle } from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { useMathSolution } from '../../hooks/useMathSolution';

import AnimationController, { AnimationProvider } from './AnimationController';
import SolutionStep from './SolutionStep';

interface StepByStepSolutionProps {
  problemId: string;
  problemStatement: string;
  problemType: string;
  difficultyLevel?: 'easy' | 'medium' | 'hard' | 'very_hard';
  onComplete?: () => void;
}

const StepByStepSolution: React.FC<StepByStepSolutionProps> = ({
  problemId,
  problemStatement,
  problemType,
  difficultyLevel = 'medium',
  onComplete,
}) => {
  const {
    solution,
    loading,
    error,
    generateSolution,
    getStep: _getStep,
    currentStep,
    setCurrentStep,
  } = useMathSolution();

  const [showAllSteps, setShowAllSteps] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [progressiveMode, setProgressiveMode] = useState(true);

  // Çözümü yükle
  useEffect(() => {
    generateSolution(problemId, problemStatement, problemType, difficultyLevel);
  }, [problemId, problemStatement, problemType, difficultyLevel]);

  // İleri git
  const handleNext = () => {
    if (solution && currentStep < solution.total_steps) {
      const nextStep = currentStep + 1;
      setCurrentStep(nextStep);

      // Mevcut adımı tamamlandı olarak işaretle
      setCompletedSteps(prev => new Set(prev).add(currentStep));

      // Son adımsa onComplete callback'i çağır
      if (nextStep === solution.total_steps && onComplete) {
        onComplete();
      }
    }
  };

  // Geri git
  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Belirli bir adıma git
  const handleGoToStep = (stepNumber: number) => {
    if (solution && stepNumber >= 1 && stepNumber <= solution.total_steps) {
      setCurrentStep(stepNumber);
    }
  };

  // Tümünü göster/gizle
  const toggleShowAll = () => {
    setShowAllSteps(!showAllSteps);
    setProgressiveMode(showAllSteps); // Tümünü gösterirken progressive mode'u kapat
  };

  // Adım tamamlandı mı?
  const isStepCompleted = (stepNumber: number) => {
    return completedSteps.has(stepNumber) || stepNumber < currentStep;
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-4 text-gray-600">Çözüm hazırlanıyor...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Hata Oluştu</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  // No solution state
  if (!solution) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <p className="text-gray-600">Çözüm bulunamadı.</p>
      </div>
    );
  }

  return (
    <AnimationProvider defaultEnabled={true} defaultSpeed="normal">
      <div className="max-w-4xl mx-auto p-6">
        {/* Animation Controller */}
        <AnimationController className="mb-6" />

        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Adım Adım Çözüm
        </h2>
        <p className="text-gray-600 mb-4">{problemStatement}</p>

        {/* Problem Info */}
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700">Tür:</span>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
              {solution.problem_type}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700">Zorluk:</span>
            <span className={`px-3 py-1 rounded-full ${
              solution.difficulty_level === 'easy' ? 'bg-green-100 text-green-800' :
              solution.difficulty_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              solution.difficulty_level === 'hard' ? 'bg-orange-100 text-orange-800' :
              'bg-red-100 text-red-800'
            }`}>
              {solution.difficulty_level}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700">Toplam Adım:</span>
            <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full">
              {solution.total_steps}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700">Tahmini Süre:</span>
            <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full">
              {Math.ceil(solution.total_duration_estimate_seconds / 60)} dakika
            </span>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Progressive Mode Toggle */}
            <button
              onClick={() => setProgressiveMode(!progressiveMode)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                progressiveMode
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {progressiveMode ? 'Adım Adım Mod' : 'Serbest Mod'}
            </button>

            {/* Show All Toggle */}
            <button
              onClick={toggleShowAll}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium text-gray-700 transition-colors"
            >
              {showAllSteps ? (
                <>
                  <EyeOff size={20} />
                  <span>Adım Adım Göster</span>
                </>
              ) : (
                <>
                  <Eye size={20} />
                  <span>Tümünü Göster</span>
                </>
              )}
            </button>
          </div>

          {/* Progress Indicator */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">İlerleme:</span>
            <div className="flex items-center gap-1">
              {Array.from({ length: solution.total_steps }, (_, i) => i + 1).map((stepNum) => (
                <div
                  key={stepNum}
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold cursor-pointer transition-all ${
                    isStepCompleted(stepNum)
                      ? 'bg-green-500 text-white'
                      : stepNum === currentStep
                      ? 'bg-blue-600 text-white ring-2 ring-blue-300'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                  onClick={() => !progressiveMode && handleGoToStep(stepNum)}
                  title={`Adım ${stepNum}`}
                >
                  {isStepCompleted(stepNum) ? <CheckCircle size={16} /> : stepNum}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

        {/* Steps Display */}
        <div className="space-y-6">
          {showAllSteps ? (
            // Tüm adımları göster
            solution.steps.map((step, index) => (
              <SolutionStep
                key={step.step_number}
                step={step}
                problemId={problemId}
                isActive={step.step_number === currentStep}
                isCompleted={isStepCompleted(step.step_number)}
                showAnimations={false}
                previousExpression={index > 0 ? solution.steps[index - 1].math_expression : undefined}
              />
            ))
          ) : (
            // Sadece mevcut adımı göster (Progressive Disclosure)
            <>
              {solution.steps
                .filter((step) =>
                  progressiveMode
                    ? step.step_number === currentStep
                    : step.step_number <= currentStep,
                )
                .map((step, index, filteredSteps) => (
                  <SolutionStep
                    key={step.step_number}
                    step={step}
                    problemId={problemId}
                    isActive={step.step_number === currentStep}
                    isCompleted={isStepCompleted(step.step_number)}
                    showAnimations={true}
                    previousExpression={
                      index > 0
                        ? filteredSteps[index - 1].math_expression
                        : step.step_number > 1
                        ? solution.steps[step.step_number - 2]?.math_expression
                        : undefined
                    }
                  />
                ))}
            </>
          )}
        </div>

      {/* Navigation */}
      {!showAllSteps && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex items-center justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                currentStep === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              <ChevronLeft size={20} />
              <span>Önceki Adım</span>
            </button>

            <div className="text-center">
              <p className="text-sm text-gray-600">
                Adım {currentStep} / {solution.total_steps}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {solution.steps[currentStep - 1]?.title}
              </p>
            </div>

            <button
              onClick={handleNext}
              disabled={currentStep === solution.total_steps}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                currentStep === solution.total_steps
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              <span>Sonraki Adım</span>
              <ChevronRight size={20} />
            </button>
          </div>
        </div>
      )}

      {/* Prerequisites & Related Concepts */}
      {(solution.prerequisites.length > 0 || solution.related_concepts.length > 0) && (
        <div className="bg-white rounded-lg shadow-md p-6 mt-6">
          <div className="grid md:grid-cols-2 gap-6">
            {solution.prerequisites.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-800 mb-3">Ön Koşul Konular</h3>
                <ul className="space-y-2">
                  {solution.prerequisites.map((prereq, index) => (
                    <li key={index} className="flex items-center gap-2 text-gray-600">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>{prereq}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {solution.related_concepts.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-800 mb-3">İlgili Kavramlar</h3>
                <ul className="space-y-2">
                  {solution.related_concepts.map((concept, index) => (
                    <li key={index} className="flex items-center gap-2 text-gray-600">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>{concept}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
      </div>
    </AnimationProvider>
  );
};

export default StepByStepSolution;

/**
 * Task 94.3: Step-by-Step Guide Component
 * Adım adım rehber - numaralandırılmış adımlar, ilerleme göstergeleri
 */
import * as React from 'react';
import {  useState  } from 'react';
import './StepByStepGuide.css';

export interface GuideStep {
  id: string;
  title: string;
  description: string;
  icon?: string;
  image?: string;
  tip?: string;
}

export interface StepByStepGuideProps {
  title: string;
  steps: GuideStep[];
  currentStep?: number;
  osbMode?: boolean;
  onStepComplete?: (stepIndex: number) => void;
}

export const StepByStepGuide: React.FC<StepByStepGuideProps> = ({
  title,
  steps,
  currentStep = 0,
  osbMode = true,
  onStepComplete,
}) => {
  const [activeStep, setActiveStep] = useState(currentStep);

  const goToStep = (index: number) => {
    if (index >= 0 && index < steps.length) {
      setActiveStep(index);
    }
  };

  const step = steps[activeStep];
  const progress = ((activeStep + 1) / steps.length) * 100;

  return (
    <div className={`step-guide ${osbMode ? 'osb-mode' : ''}`}>
      <div className="guide-header">
        <h2 className="guide-title">📋 {title}</h2>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
          <span className="progress-text">
            Adım {activeStep + 1} / {steps.length}
          </span>
        </div>
      </div>

      <div className="guide-content">
        <div className="step-indicator">
          <span className="step-number">{activeStep + 1}</span>
          <span className="step-total">/ {steps.length}</span>
        </div>

        <div className="step-details">
          {step.icon && <div className="step-icon">{step.icon}</div>}
          <h3 className="step-title">{step.title}</h3>
          <p className="step-description">{step.description}</p>
          {step.image && (
            <img src={step.image} alt={step.title} className="step-image" />
          )}
          {step.tip && (
            <div className="step-tip">
              <span className="tip-icon">💡</span>
              <span className="tip-text">{step.tip}</span>
            </div>
          )}
        </div>

        <div className="step-navigation">
          <button
            onClick={() => goToStep(activeStep - 1)}
            disabled={activeStep === 0}
            className="nav-button"
          >
            ← Önceki Adım
          </button>
          <button
            onClick={() => {
              onStepComplete?.(activeStep);
              goToStep(activeStep + 1);
            }}
            className="nav-button primary"
          >
            {activeStep === steps.length - 1 ? '✓ Tamamla' : 'Sonraki Adım →'}
          </button>
        </div>
      </div>

      <div className="steps-overview">
        {steps.map((s, index) => (
          <button
            key={s.id}
            onClick={() => goToStep(index)}
            className={`overview-step ${index === activeStep ? 'active' : ''} ${index < activeStep ? 'completed' : ''}`}
          >
            <span className="overview-number">{index + 1}</span>
            <span className="overview-title">{s.title}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default StepByStepGuide;

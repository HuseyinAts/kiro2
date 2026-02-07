/**
 * Task 95: Clear Instructions Component
 * Net ve Açık Talimatlar - OSB desteği
 *
 * Combines all Task 95 sub-tasks:
 * - 95.1: Plain language (basit dil)
 * - 95.2: Short sentences (kısa cümleler)
 * - 95.3: Numbered steps (numaralandırılmış adımlar)
 * - 95.4: Examples (örnekler)
 */

import * as React from 'react';
import './InstructionBox.css';

export interface InstructionStep {
  number: number;
  text: string;
  example?: string;
  image?: string;
  tip?: string;
}

export interface InstructionBoxProps {
  /** Talimat başlığı - basit dil */
  title: string;

  /** Kısa açıklama */
  description?: string;

  /** Numaralandırılmış adımlar */
  steps: InstructionStep[];

  /** Genel örnek (tüm adımlar için) */
  overallExample?: {
    title: string;
    description: string;
    image?: string;
  };

  /** İkon */
  icon?: string;

  /** Talimat tipi */
  type?: 'info' | 'warning' | 'success' | 'instruction';

  /** OSB modu */
  osbMode?: boolean;
}

/**
 * Clear Instruction Box
 * OSB öğrenciler için net, açık, anlaşılır talimatlar
 *
 * Özellikler:
 * - Basit dil (deyim yok, kelimeler anlamında)
 * - Kısa cümleler (tek fikir)
 * - Numaralandırılmış adımlar
 * - Somut örnekler
 */
export const InstructionBox: React.FC<InstructionBoxProps> = ({
  title,
  description,
  steps,
  overallExample,
  icon = '📝',
  type = 'instruction',
  osbMode = true,
}) => {
  const typeColors = {
    info: '#0dcaf0',
    warning: '#ffc107',
    success: '#198754',
    instruction: '#0d6efd',
  };

  const typeIcons = {
    info: 'ℹ️',
    warning: '⚠️',
    success: '✅',
    instruction: '📝',
  };

  const displayIcon = icon || typeIcons[type];
  const borderColor = typeColors[type];

  return (
    <div
      className={`instruction-box instruction-box--${type} ${osbMode ? 'osb-mode' : ''}`}
      style={{ borderColor }}
    >
      {/* Header */}
      <div className="instruction-header" style={{ backgroundColor: borderColor }}>
        <span className="instruction-icon" aria-hidden="true">{displayIcon}</span>
        <h3 className="instruction-title">{title}</h3>
      </div>

      {/* Description - Kısa ve net */}
      {description && (
        <div className="instruction-description">
          <p>{description}</p>
        </div>
      )}

      {/* Steps - Numaralandırılmış adımlar */}
      <div className="instruction-steps">
        {steps.map((step) => (
          <div key={step.number} className="instruction-step">
            {/* Step number - Büyük ve belirgin */}
            <div className="step-number-box" style={{ backgroundColor: borderColor }}>
              <span className="step-number">{step.number}</span>
            </div>

            {/* Step content */}
            <div className="step-content">
              {/* Step text - Kısa cümle, tek fikir */}
              <p className="step-text">{step.text}</p>

              {/* Example - Somut örnek */}
              {step.example && (
                <div className="step-example">
                  <span className="example-label">
                    <span className="example-icon" aria-hidden="true">💡</span>
                    Örnek:
                  </span>
                  <span className="example-text">{step.example}</span>
                </div>
              )}

              {/* Image */}
              {step.image && (
                <div className="step-image">
                  <img src={step.image} alt={`Adım ${step.number} görseli`} />
                </div>
              )}

              {/* Tip - İpucu */}
              {step.tip && (
                <div className="step-tip">
                  <span className="tip-icon" aria-hidden="true">💭</span>
                  <span className="tip-text">{step.tip}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Overall Example - Genel örnek */}
      {overallExample && (
        <div className="overall-example">
          <div className="overall-example-header">
            <span className="overall-example-icon" aria-hidden="true">🎯</span>
            <h4 className="overall-example-title">{overallExample.title}</h4>
          </div>
          <p className="overall-example-description">{overallExample.description}</p>
          {overallExample.image && (
            <div className="overall-example-image">
              <img src={overallExample.image} alt={overallExample.title} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default InstructionBox;

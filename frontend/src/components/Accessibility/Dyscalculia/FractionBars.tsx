/**
 * FractionBars Component - Diskalkuli Desteği
 *
 * Kesir çubuğu modelleri ile kesirleri görselleştiren interaktif component.
 * Öğrencilerin kesir kavramını, denk kesirleri ve kesir işlemlerini somut olarak anlamalarına yardımcı olur.
 *
 * Gereksinimler: REQ-51.6 - REQ-51.10
 */

import * as React from 'react';
import {  useState, useCallback, useMemo  } from 'react';
import './FractionBars.css';

interface Fraction {
  numerator: number;
  denominator: number;
}

interface FractionBarsProps {
  initialFraction?: Fraction;
  showEquivalent?: boolean;
  showComparison?: boolean;
  onFractionChange?: (fraction: Fraction) => void;
  readOnly?: boolean;
}

const FractionBars: React.FC<FractionBarsProps> = ({
  initialFraction = { numerator: 1, denominator: 2 },
  showEquivalent = true,
  showComparison = true,
  onFractionChange,
  readOnly = false,
}) => {
  const [fraction1, setFraction1] = useState<Fraction>(initialFraction);
  const [fraction2, setFraction2] = useState<Fraction>({ numerator: 1, denominator: 4 });
  const [animating, setAnimating] = useState(false);
  const [operation, setOperation] = useState<'add' | 'subtract' | 'multiply' | 'divide' | null>(null);

  // REQ-51.6: Kesir çubuğu modellerini görselleştir
  const fractionColors = useMemo(() => [
    '#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3',
    '#A8E6CF', '#FFD3B6', '#FFAAA5', '#FF8B94',
  ], []);

  // REQ-51.7: Denk kesirleri hesapla
  const getEquivalentFractions = useCallback((fraction: Fraction): Fraction[] => {
    const equivalents: Fraction[] = [];
    const gcd = (a: number, b: number): number => b === 0 ? a : gcd(b, a % b);
    const commonDivisor = gcd(fraction.numerator, fraction.denominator);

    // Sadeleştirilmiş hali
    const simplified = {
      numerator: fraction.numerator / commonDivisor,
      denominator: fraction.denominator / commonDivisor,
    };

    // Denk kesirler üret
    for (let i = 1; i <= 4; i++) {
      equivalents.push({
        numerator: simplified.numerator * i,
        denominator: simplified.denominator * i,
      });
    }

    return equivalents;
  }, []);

  // REQ-51.9: İki kesri karşılaştır
  const compareFractions = useCallback((f1: Fraction, f2: Fraction): string => {
    const value1 = f1.numerator / f1.denominator;
    const value2 = f2.numerator / f2.denominator;

    if (Math.abs(value1 - value2) < 0.0001) {return '=';}
    return value1 > value2 ? '>' : '<';
  }, []);

  // REQ-51.8: Kesir işlemleri
  const performOperation = useCallback((op: 'add' | 'subtract' | 'multiply' | 'divide') => {
    setOperation(op);
    setAnimating(true);

    setTimeout(() => {
      let result: Fraction;
      const gcd = (a: number, b: number): number => b === 0 ? a : gcd(b, a % b);

      switch (op) {
        case 'add':
          result = {
            numerator: fraction1.numerator * fraction2.denominator + fraction2.numerator * fraction1.denominator,
            denominator: fraction1.denominator * fraction2.denominator,
          };
          break;
        case 'subtract':
          result = {
            numerator: fraction1.numerator * fraction2.denominator - fraction2.numerator * fraction1.denominator,
            denominator: fraction1.denominator * fraction2.denominator,
          };
          break;
        case 'multiply':
          result = {
            numerator: fraction1.numerator * fraction2.numerator,
            denominator: fraction1.denominator * fraction2.denominator,
          };
          break;
        case 'divide':
          result = {
            numerator: fraction1.numerator * fraction2.denominator,
            denominator: fraction1.denominator * fraction2.numerator,
          };
          break;
      }

      // Sadeleştir
      const divisor = gcd(Math.abs(result.numerator), Math.abs(result.denominator));
      result = {
        numerator: result.numerator / divisor,
        denominator: result.denominator / divisor,
      };

      setFraction1(result);
      onFractionChange?.(result);
      setAnimating(false);
      setOperation(null);
    }, 800);
  }, [fraction1, fraction2, onFractionChange]);

  // REQ-51.10: Gerçek zamanlı kesir değerini göster
  const renderFractionBar = (fraction: Fraction, _label: string, showValue: boolean = true) => {
    const { numerator, denominator } = fraction;
    const percentage = (numerator / denominator) * 100;
    const decimalValue = (numerator / denominator).toFixed(3);

    return (
      <div className="fraction-bar-wrapper">
        <div className="fraction-label">
          <span className="fraction-text">
            <span className="numerator">{numerator}</span>
            <span className="fraction-line">/</span>
            <span className="denominator">{denominator}</span>
          </span>
          {showValue && (
            <span className="decimal-value">= {decimalValue}</span>
          )}
        </div>

        <div className="fraction-bar-container">
          <div className="fraction-bar-background">
            {Array.from({ length: denominator }).map((_, index) => (
              <div
                key={index}
                className={`fraction-segment ${index < numerator ? 'filled' : 'empty'} ${animating ? 'animating' : ''}`}
                style={{
                  width: `${100 / denominator}%`,
                  backgroundColor: index < numerator ? fractionColors[index % fractionColors.length] : '#f0f0f0',
                }}
              >
                <span className="segment-label">{index + 1}</span>
              </div>
            ))}
          </div>
          <div className="percentage-label">{percentage.toFixed(1)}%</div>
        </div>
      </div>
    );
  };

  const handleFractionChange = (
    fractionNum: 1 | 2,
    part: 'numerator' | 'denominator',
    value: number,
  ) => {
    if (readOnly) {return;}

    const newValue = Math.max(1, Math.min(value, 20));
    const setter = fractionNum === 1 ? setFraction1 : setFraction2;
    const current = fractionNum === 1 ? fraction1 : fraction2;

    const newFraction = {
      ...current,
      [part]: newValue,
    };

    // Payın paydadan büyük olmasını engelle
    if (part === 'denominator' && newFraction.numerator > newValue) {
      newFraction.numerator = newValue;
    }

    setter(newFraction);
    if (fractionNum === 1) {
      onFractionChange?.(newFraction);
    }
  };

  const equivalentFractions = useMemo(() =>
    getEquivalentFractions(fraction1),
    [fraction1, getEquivalentFractions],
  );

  const comparisonSymbol = useMemo(() =>
    compareFractions(fraction1, fraction2),
    [fraction1, fraction2, compareFractions],
  );

  return (
    <div className="fraction-bars-container" role="region" aria-label="Fraction bars visualization">
      <div className="fraction-bars-header">
        <h3>Kesir Çubukları</h3>
      </div>

      <div className="fraction-input-section">
        <div className="fraction-input-group">
          <label htmlFor="fraction1-numerator">Kesir 1:</label>
          <div className="fraction-inputs">
            <input
              id="fraction1-numerator"
              type="number"
              value={fraction1.numerator}
              onChange={(e) => handleFractionChange(1, 'numerator', parseInt(e.target.value) || 1)}
              min={1}
              max={fraction1.denominator}
              disabled={readOnly}
              aria-label="Fraction 1 numerator"
            />
            <span>/</span>
            <input
              id="fraction1-denominator"
              type="number"
              value={fraction1.denominator}
              onChange={(e) => handleFractionChange(1, 'denominator', parseInt(e.target.value) || 1)}
              min={1}
              max={20}
              disabled={readOnly}
              aria-label="Fraction 1 denominator"
            />
          </div>
        </div>

        {showComparison && (
          <div className="fraction-input-group">
            <label htmlFor="fraction2-numerator">Kesir 2:</label>
            <div className="fraction-inputs">
              <input
                id="fraction2-numerator"
                type="number"
                value={fraction2.numerator}
                onChange={(e) => handleFractionChange(2, 'numerator', parseInt(e.target.value) || 1)}
                min={1}
                max={fraction2.denominator}
                disabled={readOnly}
                aria-label="Fraction 2 numerator"
              />
              <span>/</span>
              <input
                id="fraction2-denominator"
                type="number"
                value={fraction2.denominator}
                onChange={(e) => handleFractionChange(2, 'denominator', parseInt(e.target.value) || 1)}
                min={1}
                max={20}
                disabled={readOnly}
                aria-label="Fraction 2 denominator"
              />
            </div>
          </div>
        )}
      </div>

      <div className="fraction-visualization">
        {renderFractionBar(fraction1, 'Kesir 1')}

        {showComparison && (
          <>
            <div className="comparison-symbol">
              <span className="symbol">{comparisonSymbol}</span>
            </div>
            {renderFractionBar(fraction2, 'Kesir 2')}
          </>
        )}
      </div>

      {!readOnly && showComparison && (
        <div className="operation-controls">
          <h4>Kesir İşlemleri</h4>
          <div className="operation-buttons">
            <button onClick={() => performOperation('add')} className="op-btn" disabled={animating}>
              Topla (+)
            </button>
            <button onClick={() => performOperation('subtract')} className="op-btn" disabled={animating}>
              Çıkar (−)
            </button>
            <button onClick={() => performOperation('multiply')} className="op-btn" disabled={animating}>
              Çarp (×)
            </button>
            <button onClick={() => performOperation('divide')} className="op-btn" disabled={animating}>
              Böl (÷)
            </button>
          </div>
          {operation && animating && (
            <div className="operation-animation">
              İşlem yapılıyor: {operation}...
            </div>
          )}
        </div>
      )}

      {showEquivalent && (
        <div className="equivalent-fractions">
          <h4>Denk Kesirler</h4>
          <div className="equivalent-list">
            {equivalentFractions.map((frac, index) => (
              <div key={index} className="equivalent-item">
                {renderFractionBar(frac, `Denk ${index + 1}`, false)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FractionBars;

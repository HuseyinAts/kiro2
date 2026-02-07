import * as React from 'react';
import {  useEffect, useRef, useState  } from 'react';

import { generateMathDescription } from '../../utils/mathAccessibility';

declare global {
  interface Window {
    MathJax: any;
  }
}

interface MathFormulaProps {
  /**
   * LaTeX formula string (e.g., "\\frac{a}{b}" or "x^2 + 2x + 1 = 0")
   */
  formula: string;

  /**
   * Display mode: 'inline' or 'block'
   */
  displayMode?: 'inline' | 'block';

  /**
   * Optional Turkish description for screen readers
   */
  ariaLabel?: string;

  /**
   * Optional CSS class name
   */
  className?: string;

  /**
   * Unique identifier for the formula
   */
  id?: string;
}

/**
 * Accessible Math Formula Component
 * Renders LaTeX formulas with MathJax and provides screen reader accessibility
 * with Turkish language support
 */
export const MathFormula: React.FC<MathFormulaProps> = ({
  formula,
  displayMode = 'inline',
  ariaLabel,
  className = '',
  id,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [description, setDescription] = useState<string>('');

  useEffect(() => {
    // Generate Turkish description for screen readers
    const desc = ariaLabel || generateMathDescription(formula);
    setDescription(desc);
  }, [formula, ariaLabel]);

  useEffect(() => {
    // Check if MathJax is loaded
    if (!window.MathJax) {
      console.error('MathJax is not loaded. Please include MathJax script in your HTML.');
      return;
    }

    // Initialize MathJax if not already initialized
    if (!window.MathJax.Hub && !window.MathJax.startup) {
      initializeMathJax();
    }

    // Typeset the formula
    typesetFormula();
  }, [formula]);

  const initializeMathJax = () => {
    // MathJax 3.x configuration
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
        packages: { '[+]': ['ams', 'newcommand', 'configmacros'] },
      },
      svg: {
        fontCache: 'global',
      },
      options: {
        enableMenu: true,
        enableAssistiveMml: true,
        menuOptions: {
          settings: {
            assistiveMml: true,
            collapsible: true,
            explorer: true,
            inTabOrder: false,
          },
        },
      },
      startup: {
        pageReady: () => {
          return window.MathJax.startup.defaultPageReady().then(() => {
            console.log('MathJax with accessibility features loaded');
            setIsLoaded(true);
          });
        },
      },
    };
  };

  const typesetFormula = () => {
    if (containerRef.current && window.MathJax) {
      // For MathJax 3.x
      if (window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise([containerRef.current])
          .then(() => {
            setIsLoaded(true);
            // Add accessible attributes after typesetting
            addAccessibleAttributes();
          })
          .catch((err: Error) => console.error('MathJax typeset error:', err));
      }
      // For MathJax 2.x (fallback)
      else if (window.MathJax.Hub) {
        window.MathJax.Hub.Queue(['Typeset', window.MathJax.Hub, containerRef.current]);
        window.MathJax.Hub.Queue(() => {
          setIsLoaded(true);
          addAccessibleAttributes();
        });
      }
    }
  };

  const addAccessibleAttributes = () => {
    if (!containerRef.current) {return;}

    // Find the rendered math element
    const mathElement = containerRef.current.querySelector('[data-mathml]') ||
                        containerRef.current.querySelector('.MathJax') ||
                        containerRef.current.querySelector('mjx-container');

    if (mathElement) {
      mathElement.setAttribute('role', 'math');
      mathElement.setAttribute('aria-label', description);

      // Add Turkish language attribute
      mathElement.setAttribute('lang', 'tr');
    }
  };

  const getDelimiters = () => {
    if (displayMode === 'block') {
      return { start: '\\[', end: '\\]' };
    }
    return { start: '\\(', end: '\\)' };
  };

  const delimiters = getDelimiters();
  const wrappedFormula = `${delimiters.start}${formula}${delimiters.end}`;

  return (
    <div
      ref={containerRef}
      id={id}
      className={`math-formula ${displayMode === 'block' ? 'math-block' : 'math-inline'} ${className} ${!isLoaded ? 'math-loading' : 'math-loaded'}`}
      role="math"
      aria-label={description}
      lang="tr"
      data-formula={formula}
      style={{
        display: displayMode === 'block' ? 'block' : 'inline-block',
        margin: displayMode === 'block' ? '1em 0' : '0 0.2em',
      }}
    >
      {/* Hidden text description for screen readers */}
      <span className="sr-only">{description}</span>

      {/* LaTeX formula for MathJax rendering */}
      <span aria-hidden="true">
        {wrappedFormula}
      </span>

      {/* Loading indicator */}
      {!isLoaded && (
        <span className="math-loading-indicator" aria-live="polite">
          Matematik formülü yükleniyor...
        </span>
      )}
    </div>
  );
};

/**
 * Common Turkish Math Formulas - Pre-configured components
 */

export const QuadraticFormula: React.FC = () => (
  <MathFormula
    formula="x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}"
    displayMode="block"
    ariaLabel="İkinci dereceden denklem çözüm formülü: x eşittir, eksi b artı eksi karekök b kare eksi 4 a c, bölü 2 a"
  />
);

export const PythagoreanTheorem: React.FC = () => (
  <MathFormula
    formula="a^2 + b^2 = c^2"
    displayMode="block"
    ariaLabel="Pisagor teoremi: a kare artı b kare eşittir c kare"
  />
);

export const AreaOfCircle: React.FC = () => (
  <MathFormula
    formula="A = \pi r^2"
    displayMode="block"
    ariaLabel="Dairenin alanı: A eşittir pi çarpı r kare"
  />
);

export const Derivative: React.FC<{ func?: string }> = ({ func = 'f(x)' }) => (
  <MathFormula
    formula={`\frac{d}{dx}${func}`}
    displayMode="inline"
    ariaLabel={`${func} fonksiyonunun x'e göre türevi`}
  />
);

export const Integral: React.FC<{ func?: string; from?: string; to?: string }> = ({
  func = 'f(x)',
  from = 'a',
  to = 'b',
}) => (
  <MathFormula
    formula={`\\int_{${from}}^{${to}} ${func} \\, dx`}
    displayMode="block"
    ariaLabel={`${from} den ${to} ye ${func} fonksiyonunun integrali`}
  />
);

export const Fraction: React.FC<{ numerator: string; denominator: string }> = ({
  numerator,
  denominator,
}) => (
  <MathFormula
    formula={`\\frac{${numerator}}{${denominator}}`}
    displayMode="inline"
    ariaLabel={`${numerator} bölü ${denominator}`}
  />
);

export const SquareRoot: React.FC<{ value: string }> = ({ value }) => (
  <MathFormula
    formula={`\\sqrt{${value}}`}
    displayMode="inline"
    ariaLabel={`Karekök ${value}`}
  />
);

export const Exponent: React.FC<{ base: string; power: string }> = ({ base, power }) => (
  <MathFormula
    formula={`${base}^{${power}}`}
    displayMode="inline"
    ariaLabel={`${base} üssü ${power}`}
  />
);

export default MathFormula;

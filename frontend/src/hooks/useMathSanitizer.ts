import { useMemo } from 'react';
import { sanitizeMathML } from '../utils/sanitize';

/**
 * Hook to sanitize MathML or LaTeX content before passing it to UI components.
 * This abstracts DOMPurify away from dumb UI components, allowing them to remain pure.
 */
export const useMathSanitizer = (content: string | undefined, type: 'mathml' | 'latex' = 'mathml'): string => {
  return useMemo(() => {
    if (!content) {return '';}

    let mathmlContent = content;

    // If the input is LaTeX, convert it to MathML first
    // (This logic is moved from the UI component to this hook)
    if (type === 'latex') {
      let mathmlStr = '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block">';
      if (content.includes('\\frac')) {
        const fracMatch = content.match(/\\frac\{([^}]+)\}\{([^}]+)\}/);
        if (fracMatch) {
          mathmlStr += `<mfrac><mi>${fracMatch[1]}</mi><mi>${fracMatch[2]}</mi></mfrac>`;
        }
      } else if (content.includes('^')) {
        const supMatch = content.match(/([a-zA-Z])\^(\d+)/);
        if (supMatch) {
          mathmlStr += `<msup><mi>${supMatch[1]}</mi><mn>${supMatch[2]}</mn></msup>`;
        }
      } else if (content.includes('_')) {
        const subMatch = content.match(/([a-zA-Z])_(\d+)/);
        if (subMatch) {
          mathmlStr += `<msub><mi>${subMatch[1]}</mi><mn>${subMatch[2]}</mn></msub>`;
        }
      } else if (content.includes('\\sqrt')) {
        const sqrtMatch = content.match(/\\sqrt\{([^}]+)\}/);
        if (sqrtMatch) {
          mathmlStr += `<msqrt><mi>${sqrtMatch[1]}</mi></msqrt>`;
        }
      } else {
        mathmlStr += `<mi>${content}</mi>`;
      }
      mathmlStr += '</math>';
      mathmlContent = mathmlStr;
    }

    return sanitizeMathML(mathmlContent);
  }, [content, type]);
};

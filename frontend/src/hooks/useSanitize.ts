import { useMemo } from 'react';
import { sanitizeHTML, sanitizeSVG, sanitizeBionicText } from '../utils/sanitize';

/**
 * Hook to sanitize HTML content before passing it to UI components.
 * This abstracts DOMPurify away from dumb UI components, allowing them to remain pure.
 */
export const useHTMLSanitizer = (content: string | undefined): string => {
  return useMemo(() => {
    if (!content) {return '';}
    return sanitizeHTML(content);
  }, [content]);
};

/**
 * Hook to sanitize SVG content before passing it to UI components.
 */
export const useSVGSanitizer = (content: string | undefined): string => {
  return useMemo(() => {
    if (!content) {return '';}
    return sanitizeSVG(content);
  }, [content]);
};

/**
 * Hook to sanitize Bionic Reading text content before passing it to UI components.
 */
export const useBionicSanitizer = (content: string | undefined): string => {
  return useMemo(() => {
    if (!content) {return '';}
    return sanitizeBionicText(content);
  }, [content]);
};

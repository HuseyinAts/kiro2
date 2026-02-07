/**
 * WCAG Test Utilities
 * Helpers for accessibility testing with real WCAG validation
 */

import * as React from 'react';
import { render, RenderResult } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { validateWCAG, ValidationResult } from '../../utils/wcagValidator';

const defaultTheme = createTheme();

interface WCAGRenderOptions {
  theme?: ReturnType<typeof createTheme>;
  wrapper?: React.ComponentType<{ children: React.ReactNode }>;
}

interface WCAGRenderResult extends RenderResult {
  wcagResult: ValidationResult;
  expectWCAGCompliant: (minScore?: number) => void;
  expectNoCriticalErrors: () => void;
  getWCAGScore: () => number;
}

/**
 * Render a component and run WCAG validation
 * @param component - React component to render
 * @param options - Render options
 * @returns Render result with WCAG validation
 */
export const renderWithWCAGValidation = (
  component: React.ReactElement,
  options: WCAGRenderOptions = {}
): WCAGRenderResult => {
  const { theme = defaultTheme, wrapper: Wrapper } = options;

  const ThemeWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <ThemeProvider theme={theme}>{children}</ThemeProvider>
  );

  const FinalWrapper = Wrapper
    ? ({ children }: { children: React.ReactNode }) => (
        <ThemeWrapper>
          <Wrapper>{children}</Wrapper>
        </ThemeWrapper>
      )
    : ThemeWrapper;

  const renderResult = render(component, { wrapper: FinalWrapper });

  // Run WCAG validation
  const wcagResult = validateWCAG(renderResult.container as HTMLElement);

  return {
    ...renderResult,
    wcagResult,
    expectWCAGCompliant: (minScore = 80) => {
      expect(wcagResult.score).toBeGreaterThanOrEqual(minScore);
    },
    expectNoCriticalErrors: () => {
      const criticalErrors = wcagResult.errors.filter(e => e.severity === 'critical');
      expect(criticalErrors).toHaveLength(0);
    },
    getWCAGScore: () => wcagResult.score,
  };
};

/**
 * Check if a color combination meets WCAG contrast requirements
 * @param foreground - Foreground color (hex or rgb)
 * @param background - Background color (hex or rgb)
 * @param level - WCAG level ('AA' or 'AAA')
 * @param isLargeText - Whether the text is large (18px+ or 14px+ bold)
 */
export const checkContrastRequirement = (
  foreground: string,
  background: string,
  level: 'AA' | 'AAA' = 'AA',
  isLargeText = false
): { passed: boolean; ratio: number; required: number } => {
  const { calculateContrastRatio } = require('../../utils/wcagValidator');

  const ratio = calculateContrastRatio(foreground, background);

  const requirements = {
    AA: isLargeText ? 3 : 4.5,
    AAA: isLargeText ? 4.5 : 7,
  };

  const required = requirements[level];

  return {
    passed: ratio >= required,
    ratio: Math.round(ratio * 100) / 100,
    required,
  };
};

/**
 * Test keyboard navigation for an element
 * @param element - Element to test
 * @returns Navigation test results
 */
export const testKeyboardNavigation = (element: HTMLElement): {
  isFocusable: boolean;
  hasTabIndex: boolean;
  tabIndexValue: number | null;
  isInteractive: boolean;
} => {
  const tabIndex = element.getAttribute('tabindex');
  const interactiveTags = ['A', 'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT'];

  return {
    isFocusable: element.tabIndex >= 0,
    hasTabIndex: tabIndex !== null,
    tabIndexValue: tabIndex !== null ? parseInt(tabIndex, 10) : null,
    isInteractive: interactiveTags.includes(element.tagName) || element.hasAttribute('onclick'),
  };
};

/**
 * Check if an element has proper ARIA attributes
 * @param element - Element to check
 */
export const checkARIAAttributes = (element: HTMLElement): {
  hasRole: boolean;
  role: string | null;
  hasAriaLabel: boolean;
  ariaLabel: string | null;
  hasAriaDescribedBy: boolean;
  hasAriaLabelledBy: boolean;
  isValid: boolean;
} => {
  const role = element.getAttribute('role');
  const ariaLabel = element.getAttribute('aria-label');
  const ariaDescribedBy = element.getAttribute('aria-describedby');
  const ariaLabelledBy = element.getAttribute('aria-labelledby');

  // Basic validity check
  const validRoles = [
    'alert', 'alertdialog', 'button', 'checkbox', 'dialog', 'grid',
    'link', 'listbox', 'menu', 'menuitem', 'option', 'progressbar',
    'radio', 'slider', 'spinbutton', 'tab', 'tablist', 'tabpanel',
    'textbox', 'tooltip', 'tree', 'treeitem', 'form', 'navigation',
    'main', 'banner', 'complementary', 'contentinfo', 'region',
    'status', 'timer', 'log', 'presentation', 'img', 'heading',
  ];

  const isValid = !role || validRoles.includes(role);

  return {
    hasRole: role !== null,
    role,
    hasAriaLabel: ariaLabel !== null,
    ariaLabel,
    hasAriaDescribedBy: ariaDescribedBy !== null,
    hasAriaLabelledBy: ariaLabelledBy !== null,
    isValid,
  };
};

/**
 * Check heading hierarchy in a container
 * @param container - Container element
 */
export const checkHeadingHierarchy = (container: HTMLElement): {
  headings: Array<{ level: number; text: string }>;
  hasSkippedLevels: boolean;
  hasMultipleH1: boolean;
  hasEmptyHeadings: boolean;
  errors: string[];
} => {
  const headings = Array.from(container.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => ({
    level: parseInt(h.tagName.substring(1), 10),
    text: h.textContent?.trim() || '',
  }));

  const errors: string[] = [];
  let previousLevel = 0;

  headings.forEach((heading, index) => {
    if (heading.level > previousLevel + 1 && previousLevel !== 0) {
      errors.push(`Heading level skipped: h${previousLevel} → h${heading.level}`);
    }
    if (!heading.text) {
      errors.push(`Empty heading at index ${index}`);
    }
    previousLevel = heading.level;
  });

  const h1Count = headings.filter(h => h.level === 1).length;
  if (h1Count > 1) {
    errors.push(`Multiple h1 elements found: ${h1Count}`);
  }

  return {
    headings,
    hasSkippedLevels: errors.some(e => e.includes('skipped')),
    hasMultipleH1: h1Count > 1,
    hasEmptyHeadings: errors.some(e => e.includes('Empty')),
    errors,
  };
};

/**
 * Check form accessibility
 * @param form - Form element
 */
export const checkFormAccessibility = (form: HTMLElement): {
  inputs: Array<{
    id: string | null;
    hasLabel: boolean;
    hasAriaLabel: boolean;
    isRequired: boolean;
    hasRequiredIndicator: boolean;
  }>;
  hasErrorHandling: boolean;
  isAccessible: boolean;
} => {
  const inputs = Array.from(form.querySelectorAll('input, textarea, select')).map(input => {
    const id = input.id;
    const hasLabel = !!id && !!document.querySelector(`label[for="${id}"]`);
    const hasAriaLabel = input.hasAttribute('aria-label') || input.hasAttribute('aria-labelledby');
    const isRequired = input.hasAttribute('required');
    const hasRequiredIndicator = input.hasAttribute('aria-required') ||
      (hasLabel && document.querySelector(`label[for="${id}"]`)?.textContent?.includes('*'));

    return {
      id,
      hasLabel,
      hasAriaLabel,
      isRequired,
      hasRequiredIndicator: !!hasRequiredIndicator,
    };
  });

  const allInputsLabeled = inputs.every(i => i.hasLabel || i.hasAriaLabel);
  const requiredFieldsMarked = inputs.filter(i => i.isRequired).every(i => i.hasRequiredIndicator);

  return {
    inputs,
    hasErrorHandling: !!form.querySelector('[role="alert"]') || !!form.querySelector('[aria-invalid]'),
    isAccessible: allInputsLabeled && requiredFieldsMarked,
  };
};

/**
 * Check touch target size (WCAG 2.5.5)
 * @param element - Element to check
 * @param minSize - Minimum size in pixels (default: 44)
 */
export const checkTouchTargetSize = (
  element: HTMLElement,
  minSize = 44
): { width: number; height: number; meetsRequirement: boolean } => {
  const rect = element.getBoundingClientRect();
  const computedStyle = window.getComputedStyle(element);

  // Check actual dimensions or computed minHeight/minWidth
  const width = rect.width || parseFloat(computedStyle.minWidth) || 0;
  const height = rect.height || parseFloat(computedStyle.minHeight) || 0;

  return {
    width,
    height,
    meetsRequirement: width >= minSize && height >= minSize,
  };
};

// Export types
export type { WCAGRenderOptions, WCAGRenderResult };

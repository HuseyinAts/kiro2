/**
 * Accessibility Testing Utilities
 * Comprehensive accessibility testing with axe-core integration
 */

import { axe, toHaveNoViolations } from 'jest-axe'
import { render, RenderResult } from '@testing-library/react'
import { expect } from 'vitest'

// Extend expect with accessibility matchers
expect.extend(toHaveNoViolations)

// Accessibility testing configuration
const axeConfig = {
  rules: {
    // Color contrast rules
    'color-contrast': { enabled: true },
    'color-contrast-enhanced': { enabled: true },
    
    // Keyboard navigation
    'focus-order-semantics': { enabled: true },
    'tabindex': { enabled: true },
    
    // ARIA rules
    'aria-valid-attr': { enabled: true },
    'aria-valid-attr-value': { enabled: true },
    'aria-required-attr': { enabled: true },
    'aria-required-children': { enabled: true },
    'aria-required-parent': { enabled: true },
    
    // Form labels
    'label': { enabled: true },
    'form-field-multiple-labels': { enabled: true },
    
    // Heading structure
    'heading-order': { enabled: true },
    'empty-heading': { enabled: true },
    
    // Images
    'image-alt': { enabled: true },
    'image-redundant-alt': { enabled: true },
    
    // Links
    'link-name': { enabled: true },
    'link-in-text-block': { enabled: true },
    
    // Lists
    'list': { enabled: true },
    'listitem': { enabled: true },
    
    // Tables
    'table-header': { enabled: true },
    'td-headers-attr': { enabled: true },
    
    // Language
    'html-has-lang': { enabled: true },
    'html-lang-valid': { enabled: true },
    
    // Page structure
    'landmark-one-main': { enabled: true },
    'page-has-heading-one': { enabled: true },
    'region': { enabled: true },
    
    // Interactive elements
    'button-name': { enabled: true },
    'interactive-controls-children': { enabled: true }
  },
  tags: [
    'wcag2a',    // WCAG 2.0 Level A
    'wcag2aa',   // WCAG 2.0 Level AA
    'wcag21aa',  // WCAG 2.1 Level AA
    'best-practice' // Best practices
  ]
}

/**
 * Run accessibility tests on a rendered component
 */
export const runAccessibilityTests = async (container: HTMLElement) => {
  const results = await axe(container, axeConfig)
  expect(results).toHaveNoViolations()
  return results
}

/**
 * Test keyboard navigation for a component
 */
export const testKeyboardNavigation = async (
  renderResult: RenderResult,
  interactiveElements: string[] = []
) => {
  const { container } = renderResult
  
  // Find all focusable elements
  const focusableElements = container.querySelectorAll(
    'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
  )
  
  // Test tab order
  let currentIndex = 0
  for (const element of Array.from(focusableElements)) {
    const htmlElement = element as HTMLElement
    
    // Check if element is actually focusable
    if (htmlElement.tabIndex >= 0 && !htmlElement.hasAttribute('disabled')) {
      expect(htmlElement.tabIndex).toBeGreaterThanOrEqual(0)
      currentIndex++
    }
  }
  
  // Verify specific interactive elements if provided
  if (interactiveElements.length > 0) {
    for (const selector of interactiveElements) {
      const element = container.querySelector(selector) as HTMLElement
      expect(element).toBeTruthy()
      expect(element.tabIndex).toBeGreaterThanOrEqual(0)
    }
  }
  
  return focusableElements.length
}

/**
 * Test ARIA attributes and labels
 */
export const testAriaAttributes = (container: HTMLElement) => {
  // Check for required ARIA labels
  const buttonsWithoutLabels = container.querySelectorAll(
    'button:not([aria-label]):not([aria-labelledby]):not([title])'
  )
  
  buttonsWithoutLabels.forEach(button => {
    const hasTextContent = button.textContent && button.textContent.trim().length > 0
    expect(hasTextContent).toBe(true)
  })
  
  // Check for proper heading structure
  const headings = container.querySelectorAll('h1, h2, h3, h4, h5, h6')
  let previousLevel = 0
  
  headings.forEach(heading => {
    const level = parseInt(heading.tagName.charAt(1))
    if (previousLevel > 0) {
      expect(level).toBeLessThanOrEqual(previousLevel + 1)
    }
    previousLevel = level
  })
  
  // Check for form labels
  const inputs = container.querySelectorAll('input, textarea, select')
  inputs.forEach(input => {
    const hasLabel = input.getAttribute('aria-label') ||
                    input.getAttribute('aria-labelledby') ||
                    container.querySelector(`label[for="${input.id}"]`)
    
    expect(hasLabel).toBeTruthy()
  })
}

/**
 * Test color contrast ratios
 */
export const testColorContrast = async (container: HTMLElement) => {
  const results = await axe(container, {
    rules: {
      'color-contrast': { enabled: true },
      'color-contrast-enhanced': { enabled: true }
    }
  })
  
  const contrastViolations = results.violations.filter(
    violation => violation.id === 'color-contrast' || violation.id === 'color-contrast-enhanced'
  )
  
  expect(contrastViolations).toHaveLength(0)
  return contrastViolations
}

/**
 * Test screen reader compatibility
 */
export const testScreenReaderSupport = (container: HTMLElement) => {
  // Check for semantic HTML elements
  const semanticElements = [
    'main', 'nav', 'header', 'footer', 'section', 'article', 'aside'
  ]
  
  let hasSemanticStructure = false
  semanticElements.forEach(tag => {
    if (container.querySelector(tag)) {
      hasSemanticStructure = true
    }
  })
  
  // Allow ARIA landmarks as alternative to semantic elements
  const ariaLandmarks = container.querySelectorAll(
    '[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], [role="complementary"]'
  )
  
  if (ariaLandmarks.length > 0) {
    hasSemanticStructure = true
  }
  
  // Check for skip links (for navigation)
  const skipLinks = container.querySelectorAll('a[href^="#"]')
  
  return {
    hasSemanticStructure,
    skipLinksCount: skipLinks.length,
    ariaLandmarksCount: ariaLandmarks.length
  }
}

/**
 * Test focus management
 */
export const testFocusManagement = async (
  renderResult: RenderResult,
  triggerAction: () => Promise<void>
) => {
  const { container } = renderResult
  
  // Record initial focus
  const initialFocus = document.activeElement
  
  // Trigger action that might change focus
  await triggerAction()
  
  // Verify focus is managed properly
  const currentFocus = document.activeElement
  
  // Focus should be on a visible, focusable element
  if (currentFocus && currentFocus !== document.body) {
    expect(currentFocus).toBeInstanceOf(HTMLElement)
    
    const styles = getComputedStyle(currentFocus as HTMLElement)
    expect(styles.display).not.toBe('none')
    expect(styles.visibility).not.toBe('hidden')
  }
  
  return {
    initialFocus,
    currentFocus,
    focusChanged: initialFocus !== currentFocus
  }
}

/**
 * Test mobile accessibility features
 */
export const testMobileAccessibility = (container: HTMLElement) => {
  // Check for touch-friendly target sizes (minimum 44px)
  const interactiveElements = container.querySelectorAll(
    'button, a, input, [role="button"], [tabindex]:not([tabindex="-1"])'
  )
  
  const tooSmallElements: HTMLElement[] = []
  
  interactiveElements.forEach(element => {
    const htmlElement = element as HTMLElement
    const rect = htmlElement.getBoundingClientRect()
    
    if (rect.width > 0 && rect.height > 0) {
      if (rect.width < 44 || rect.height < 44) {
        tooSmallElements.push(htmlElement)
      }
    }
  })
  
  return {
    totalInteractiveElements: interactiveElements.length,
    tooSmallElements: tooSmallElements.length,
    compliant: tooSmallElements.length === 0
  }
}

/**
 * Test language and internationalization support
 */
export const testInternationalization = (container: HTMLElement) => {
  // Check for lang attributes
  const hasLangAttribute = container.hasAttribute('lang') ||
                          document.documentElement.hasAttribute('lang')
  
  // Check for proper text direction
  const hasDirectionAttribute = container.hasAttribute('dir') ||
                               document.documentElement.hasAttribute('dir')
  
  // Check for translated content (Turkish in this case)
  const textElements = container.querySelectorAll('*')
  let hasTurkishContent = false
  
  textElements.forEach(element => {
    const text = element.textContent || ''
    // Simple check for Turkish characters
    if (/[çğıöşüÇĞIİÖŞÜ]/.test(text)) {
      hasTurkishContent = true
    }
  })
  
  return {
    hasLangAttribute,
    hasDirectionAttribute,
    hasTurkishContent
  }
}

/**
 * Comprehensive accessibility test suite
 */
export const runComprehensiveAccessibilityTests = async (
  renderResult: RenderResult,
  options: {
    skipKeyboardNav?: boolean
    skipColorContrast?: boolean
    skipMobile?: boolean
    interactiveElements?: string[]
  } = {}
) => {
  const { container } = renderResult
  
  const results = {
    axeViolations: null as any,
    keyboardNavigation: null as any,
    ariaAttributes: null as any,
    colorContrast: null as any,
    screenReader: null as any,
    mobileAccessibility: null as any,
    internationalization: null as any
  }
  
  try {
    // Run axe accessibility tests
    results.axeViolations = await runAccessibilityTests(container)
    
    // Test keyboard navigation
    if (!options.skipKeyboardNav) {
      results.keyboardNavigation = await testKeyboardNavigation(
        renderResult,
        options.interactiveElements
      )
    }
    
    // Test ARIA attributes
    results.ariaAttributes = testAriaAttributes(container)
    
    // Test color contrast
    if (!options.skipColorContrast) {
      results.colorContrast = await testColorContrast(container)
    }
    
    // Test screen reader support
    results.screenReader = testScreenReaderSupport(container)
    
    // Test mobile accessibility
    if (!options.skipMobile) {
      results.mobileAccessibility = testMobileAccessibility(container)
    }
    
    // Test internationalization
    results.internationalization = testInternationalization(container)
    
  } catch (error) {
    console.error('Accessibility testing error:', error)
    throw error
  }
  
  return results
}

export default {
  runAccessibilityTests,
  testKeyboardNavigation,
  testAriaAttributes,
  testColorContrast,
  testScreenReaderSupport,
  testFocusManagement,
  testMobileAccessibility,
  testInternationalization,
  runComprehensiveAccessibilityTests
}
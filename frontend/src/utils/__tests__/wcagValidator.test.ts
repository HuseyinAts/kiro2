/**
 * WCAG 2.1 Level AA Validator Unit Tests
 * Comprehensive tests for wcagValidator.ts utility
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  calculateContrastRatio,
  checkContrastCompliance,
  validateForms,
  validateImages,
  validateKeyboardAccess,
  validateARIA,
  validateHeadings,
  validateLanguage,
  validateWCAG,
  generateAccessibilityReport,
  ValidationResult,
} from '../wcagValidator';

describe('WCAG Validator', () => {
  // Reset DOM before each test
  beforeEach(() => {
    document.body.innerHTML = '';
    document.documentElement.removeAttribute('lang');
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('calculateContrastRatio', () => {
    it('calculates 21:1 ratio for black on white', () => {
      const ratio = calculateContrastRatio('#000000', '#FFFFFF');
      expect(ratio).toBeCloseTo(21, 0);
    });

    it('calculates 21:1 ratio for white on black', () => {
      const ratio = calculateContrastRatio('#FFFFFF', '#000000');
      expect(ratio).toBeCloseTo(21, 0);
    });

    it('calculates 1:1 ratio for same colors', () => {
      const ratio = calculateContrastRatio('#808080', '#808080');
      expect(ratio).toBeCloseTo(1, 0);
    });

    it('handles rgb color format', () => {
      const ratio = calculateContrastRatio('rgb(0, 0, 0)', 'rgb(255, 255, 255)');
      expect(ratio).toBeCloseTo(21, 0);
    });

    it('handles rgba color format', () => {
      const ratio = calculateContrastRatio('rgba(0, 0, 0, 1)', 'rgba(255, 255, 255, 1)');
      expect(ratio).toBeCloseTo(21, 0);
    });

    it('calculates correct ratio for gray combinations (WCAG AA boundary)', () => {
      // #767676 on white gives approximately 4.54:1 (just above AA)
      const ratio = calculateContrastRatio('#767676', '#FFFFFF');
      expect(ratio).toBeGreaterThanOrEqual(4.5);
    });

    it('handles colors with whitespace', () => {
      const ratio = calculateContrastRatio('  #000000  ', '  #FFFFFF  ');
      expect(ratio).toBeCloseTo(21, 0);
    });

    it('defaults to black for invalid color format', () => {
      const ratio = calculateContrastRatio('invalid', '#FFFFFF');
      expect(ratio).toBeCloseTo(21, 0); // Black vs white
    });
  });

  describe('checkContrastCompliance', () => {
    describe('Normal text (< 18px)', () => {
      it('passes AA for ratio >= 4.5:1', () => {
        const result = checkContrastCompliance(4.5, 16, 400, 'AA');
        expect(result.passed).toBe(true);
        expect(result.level).toBe('AA');
      });

      it('fails AA for ratio < 4.5:1', () => {
        const result = checkContrastCompliance(4.4, 16, 400, 'AA');
        expect(result.passed).toBe(false);
        expect(result.level).toBe('fail');
      });

      it('passes AAA for ratio >= 7:1', () => {
        const result = checkContrastCompliance(7.0, 16, 400, 'AAA');
        expect(result.passed).toBe(true);
        expect(result.level).toBe('AAA');
      });

      it('fails AAA for ratio < 7:1', () => {
        const result = checkContrastCompliance(6.9, 16, 400, 'AAA');
        expect(result.passed).toBe(false);
      });
    });

    describe('Large text (>= 18px or bold >= 14px)', () => {
      it('passes AA for ratio >= 3:1 at 18px', () => {
        const result = checkContrastCompliance(3.0, 18, 400, 'AA');
        expect(result.passed).toBe(true);
        expect(result.level).toBe('AA');
      });

      it('passes AA for ratio >= 3:1 at 14px bold', () => {
        const result = checkContrastCompliance(3.0, 14, 700, 'AA');
        expect(result.passed).toBe(true);
        expect(result.level).toBe('AA');
      });

      it('passes AAA for ratio >= 4.5:1 at 18px', () => {
        const result = checkContrastCompliance(4.5, 18, 400, 'AAA');
        expect(result.passed).toBe(true);
        expect(result.level).toBe('AAA');
      });
    });

    it('defaults to AA level when not specified', () => {
      const result = checkContrastCompliance(4.5, 16, 400);
      expect(result.passed).toBe(true);
    });
  });

  describe('validateForms', () => {
    it('detects input without label', () => {
      document.body.innerHTML = '<input type="text" id="test-input" />';
      const errors = validateForms(document.body);

      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.rule === 'Form Label')).toBe(true);
    });

    it('passes input with proper label', () => {
      document.body.innerHTML = `
        <label for="test-input">İsim</label>
        <input type="text" id="test-input" />
      `;
      const errors = validateForms(document.body);

      expect(errors.filter(e => e.rule === 'Form Label')).toHaveLength(0);
    });

    it('passes input with aria-label', () => {
      document.body.innerHTML = '<input type="text" aria-label="İsim" />';
      const errors = validateForms(document.body);

      expect(errors.filter(e => e.rule === 'Form Label')).toHaveLength(0);
    });

    it('passes input with aria-labelledby', () => {
      document.body.innerHTML = `
        <span id="label-text">İsim</span>
        <input type="text" aria-labelledby="label-text" />
      `;
      const errors = validateForms(document.body);

      expect(errors.filter(e => e.rule === 'Form Label')).toHaveLength(0);
    });

    it('detects required field without visual indicator', () => {
      document.body.innerHTML = `
        <label for="test-input">İsim</label>
        <input type="text" id="test-input" required />
      `;
      const errors = validateForms(document.body);

      expect(errors.some(e => e.rule === 'Required Field Indicator')).toBe(true);
    });

    it('passes required field with asterisk indicator', () => {
      document.body.innerHTML = `
        <label for="test-input">İsim *</label>
        <input type="text" id="test-input" required />
      `;
      const errors = validateForms(document.body);

      expect(errors.filter(e => e.rule === 'Required Field Indicator')).toHaveLength(0);
    });

    it('passes required field with aria-required', () => {
      document.body.innerHTML = `
        <label for="test-input">İsim</label>
        <input type="text" id="test-input" required aria-required="true" />
      `;
      const errors = validateForms(document.body);

      expect(errors.filter(e => e.rule === 'Required Field Indicator')).toHaveLength(0);
    });

    it('detects invalid field without error message', () => {
      document.body.innerHTML = `
        <label for="test-input">İsim</label>
        <input type="text" id="test-input" aria-invalid="true" />
      `;
      const errors = validateForms(document.body);

      expect(errors.some(e => e.rule === 'Error Message')).toBe(true);
    });

    it('passes invalid field with aria-describedby', () => {
      document.body.innerHTML = `
        <label for="test-input">İsim</label>
        <input type="text" id="test-input" aria-invalid="true" aria-describedby="error-msg" />
        <span id="error-msg">Hatalı giriş</span>
      `;
      const errors = validateForms(document.body);

      expect(errors.filter(e => e.rule === 'Error Message')).toHaveLength(0);
    });

    it('validates textarea elements', () => {
      document.body.innerHTML = '<textarea id="comment"></textarea>';
      const errors = validateForms(document.body);

      expect(errors.some(e => e.rule === 'Form Label')).toBe(true);
    });

    it('validates select elements', () => {
      document.body.innerHTML = `
        <select id="city">
          <option>İstanbul</option>
          <option>Ankara</option>
        </select>
      `;
      const errors = validateForms(document.body);

      expect(errors.some(e => e.rule === 'Form Label')).toBe(true);
    });
  });

  describe('validateImages', () => {
    it('detects image without alt text', () => {
      document.body.innerHTML = '<img src="test.jpg" />';
      const errors = validateImages(document.body);

      expect(errors.length).toBeGreaterThan(0);
      expect(errors.some(e => e.rule === 'Image Alt Text')).toBe(true);
    });

    it('passes image with alt text', () => {
      document.body.innerHTML = '<img src="test.jpg" alt="Test görsel" />';
      const errors = validateImages(document.body);

      expect(errors).toHaveLength(0);
    });

    it('passes decorative image with empty alt', () => {
      document.body.innerHTML = '<img src="decorative.jpg" alt="" />';
      const errors = validateImages(document.body);

      expect(errors).toHaveLength(0);
    });

    it('passes decorative image with role="presentation"', () => {
      document.body.innerHTML = '<img src="decorative.jpg" role="presentation" />';
      const errors = validateImages(document.body);

      expect(errors).toHaveLength(0);
    });

    it('detects alt text longer than 150 characters', () => {
      const longAlt = 'A'.repeat(151);
      document.body.innerHTML = `<img src="test.jpg" alt="${longAlt}" />`;
      const errors = validateImages(document.body);

      expect(errors.some(e => e.rule === 'Alt Text Length')).toBe(true);
    });

    it('passes alt text at 150 characters', () => {
      const alt = 'A'.repeat(150);
      document.body.innerHTML = `<img src="test.jpg" alt="${alt}" />`;
      const errors = validateImages(document.body);

      expect(errors.filter(e => e.rule === 'Alt Text Length')).toHaveLength(0);
    });
  });

  describe('validateKeyboardAccess', () => {
    it('detects onclick without keyboard access', () => {
      document.body.innerHTML = '<div onclick="alert()">Click me</div>';
      const errors = validateKeyboardAccess(document.body);

      expect(errors.some(e => e.rule === 'Keyboard Accessibility')).toBe(true);
    });

    it('passes onclick element with tabindex="0"', () => {
      document.body.innerHTML = '<div onclick="alert()" tabindex="0">Click me</div>';
      const errors = validateKeyboardAccess(document.body);

      expect(errors.filter(e => e.rule === 'Keyboard Accessibility')).toHaveLength(0);
    });

    it('passes native button element', () => {
      document.body.innerHTML = '<button onclick="alert()">Click me</button>';
      const errors = validateKeyboardAccess(document.body);

      expect(errors.filter(e => e.rule === 'Keyboard Accessibility')).toHaveLength(0);
    });

    it('passes native anchor element', () => {
      document.body.innerHTML = '<a href="#" onclick="alert()">Click me</a>';
      const errors = validateKeyboardAccess(document.body);

      expect(errors.filter(e => e.rule === 'Keyboard Accessibility')).toHaveLength(0);
    });

    it('detects negative tabindex with onclick', () => {
      document.body.innerHTML = '<div onclick="alert()" tabindex="-1">Click me</div>';
      const errors = validateKeyboardAccess(document.body);

      expect(errors.some(e => e.rule === 'Negative Tabindex')).toBe(true);
    });
  });

  describe('validateARIA', () => {
    it('detects invalid ARIA role', () => {
      document.body.innerHTML = '<div role="invalidrole">Content</div>';
      const errors = validateARIA(document.body);

      expect(errors.some(e => e.rule === 'Invalid ARIA Role')).toBe(true);
    });

    it('passes valid ARIA role', () => {
      document.body.innerHTML = '<div role="button">Button</div>';
      const errors = validateARIA(document.body);

      expect(errors.filter(e => e.rule === 'Invalid ARIA Role')).toHaveLength(0);
    });

    it('validates all standard ARIA roles', () => {
      const validRoles = ['alert', 'button', 'checkbox', 'dialog', 'link', 'menu', 'progressbar', 'tab', 'tabpanel'];

      validRoles.forEach(role => {
        document.body.innerHTML = `<div role="${role}">Content</div>`;
        const errors = validateARIA(document.body);
        expect(errors.filter(e => e.rule === 'Invalid ARIA Role')).toHaveLength(0);
      });
    });

    it('detects missing aria-labelledby reference', () => {
      document.body.innerHTML = '<div aria-labelledby="non-existent-id">Content</div>';
      const errors = validateARIA(document.body);

      expect(errors.some(e => e.rule === 'ARIA Reference')).toBe(true);
    });

    it('passes valid aria-labelledby reference', () => {
      document.body.innerHTML = `
        <span id="label-id">Label</span>
        <div aria-labelledby="label-id">Content</div>
      `;
      const errors = validateARIA(document.body);

      expect(errors.filter(e => e.rule === 'ARIA Reference')).toHaveLength(0);
    });

    it('detects missing aria-describedby reference', () => {
      document.body.innerHTML = '<div aria-describedby="non-existent-id">Content</div>';
      const errors = validateARIA(document.body);

      expect(errors.some(e => e.rule === 'ARIA Reference')).toBe(true);
    });

    it('passes valid aria-describedby reference', () => {
      document.body.innerHTML = `
        <span id="desc-id">Description</span>
        <div aria-describedby="desc-id">Content</div>
      `;
      const errors = validateARIA(document.body);

      expect(errors.filter(e => e.rule === 'ARIA Reference')).toHaveLength(0);
    });

    it('handles multiple space-separated IDs in aria-labelledby', () => {
      document.body.innerHTML = `
        <span id="label1">Label 1</span>
        <span id="label2">Label 2</span>
        <div aria-labelledby="label1 label2">Content</div>
      `;
      const errors = validateARIA(document.body);

      expect(errors.filter(e => e.rule === 'ARIA Reference')).toHaveLength(0);
    });

    it('detects one missing ID in multiple aria-labelledby', () => {
      document.body.innerHTML = `
        <span id="label1">Label 1</span>
        <div aria-labelledby="label1 missing-id">Content</div>
      `;
      const errors = validateARIA(document.body);

      expect(errors.some(e => e.rule === 'ARIA Reference')).toBe(true);
    });
  });

  describe('validateHeadings', () => {
    it('detects skipped heading levels', () => {
      document.body.innerHTML = '<h1>Title</h1><h3>Subtitle</h3>';
      const errors = validateHeadings(document.body);

      expect(errors.some(e => e.rule === 'Heading Hierarchy')).toBe(true);
    });

    it('passes proper heading hierarchy', () => {
      document.body.innerHTML = '<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>';
      const errors = validateHeadings(document.body);

      expect(errors.filter(e => e.rule === 'Heading Hierarchy')).toHaveLength(0);
    });

    it('detects empty heading', () => {
      document.body.innerHTML = '<h1></h1>';
      const errors = validateHeadings(document.body);

      expect(errors.some(e => e.rule === 'Empty Heading')).toBe(true);
    });

    it('detects heading with only whitespace', () => {
      document.body.innerHTML = '<h1>   </h1>';
      const errors = validateHeadings(document.body);

      expect(errors.some(e => e.rule === 'Empty Heading')).toBe(true);
    });

    it('passes heading with content', () => {
      document.body.innerHTML = '<h1>Ana Başlık</h1>';
      const errors = validateHeadings(document.body);

      expect(errors.filter(e => e.rule === 'Empty Heading')).toHaveLength(0);
    });

    it('detects multiple h1 elements', () => {
      document.body.innerHTML = '<h1>First</h1><h1>Second</h1>';
      const errors = validateHeadings(document.body);

      expect(errors.some(e => e.rule === 'Multiple H1')).toBe(true);
    });

    it('passes single h1 element', () => {
      document.body.innerHTML = '<h1>Only One</h1>';
      const errors = validateHeadings(document.body);

      expect(errors.filter(e => e.rule === 'Multiple H1')).toHaveLength(0);
    });

    it('allows h2 without h1', () => {
      document.body.innerHTML = '<h2>Subtitle</h2>';
      const errors = validateHeadings(document.body);

      // h2 without h1 is allowed (h1 might be outside the validated area)
      expect(errors.filter(e => e.rule === 'Heading Hierarchy')).toHaveLength(0);
    });
  });

  describe('validateLanguage', () => {
    it('detects missing lang attribute', () => {
      document.documentElement.removeAttribute('lang');
      const errors = validateLanguage();

      expect(errors.some(e => e.rule === 'Page Language')).toBe(true);
    });

    it('passes with lang attribute set', () => {
      document.documentElement.setAttribute('lang', 'tr');
      const errors = validateLanguage();

      expect(errors).toHaveLength(0);
    });

    it('passes with any valid lang attribute', () => {
      document.documentElement.setAttribute('lang', 'en');
      const errors = validateLanguage();

      expect(errors).toHaveLength(0);
    });
  });

  describe('validateWCAG (comprehensive)', () => {
    it('returns high score for compliant HTML', () => {
      document.documentElement.setAttribute('lang', 'tr');
      document.body.innerHTML = `
        <h1>Ana Başlık</h1>
        <h2>Alt Başlık</h2>
        <label for="name">İsim *</label>
        <input type="text" id="name" required aria-required="true" />
        <img src="test.jpg" alt="Test görsel" />
        <button>Gönder</button>
      `;

      const result = validateWCAG(document.body);

      // Score should be >= 90 for mostly compliant HTML
      expect(result.score).toBeGreaterThanOrEqual(90);
      expect(result.errors.filter(e => e.severity === 'critical')).toHaveLength(0);
    });

    it('returns score < 100 for non-compliant HTML', () => {
      document.body.innerHTML = `
        <img src="test.jpg" />
        <input type="text" />
      `;

      const result = validateWCAG(document.body);

      expect(result.score).toBeLessThan(100);
      expect(result.passed).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('calculates score correctly based on error severity', () => {
      document.documentElement.setAttribute('lang', 'tr');
      document.body.innerHTML = `
        <h1>Title</h1>
        <img src="test.jpg" /> <!-- critical: -10 -->
        <input type="text" id="test" /> <!-- critical: -10 -->
      `;

      const result = validateWCAG(document.body);

      // 2 critical errors = -20 points
      expect(result.score).toBe(80);
    });

    it('includes errors from all validation functions', () => {
      document.body.innerHTML = `
        <h1>Title</h1>
        <h3>Skipped h2</h3>
        <img src="test.jpg" />
        <input type="text" />
        <div role="invalid">Content</div>
      `;

      const result = validateWCAG(document.body);

      // Should have errors from multiple validators
      expect(result.errors.some(e => e.rule === 'Heading Hierarchy')).toBe(true);
      expect(result.errors.some(e => e.rule === 'Image Alt Text')).toBe(true);
      expect(result.errors.some(e => e.rule === 'Form Label')).toBe(true);
      expect(result.errors.some(e => e.rule === 'Invalid ARIA Role')).toBe(true);
      expect(result.errors.some(e => e.rule === 'Page Language')).toBe(true);
    });

    it('returns correct structure', () => {
      document.documentElement.setAttribute('lang', 'tr');
      document.body.innerHTML = '<h1>Test</h1>';

      const result = validateWCAG(document.body);

      expect(result).toHaveProperty('passed');
      expect(result).toHaveProperty('errors');
      expect(result).toHaveProperty('warnings');
      expect(result).toHaveProperty('score');
      expect(typeof result.passed).toBe('boolean');
      expect(Array.isArray(result.errors)).toBe(true);
      expect(Array.isArray(result.warnings)).toBe(true);
      expect(typeof result.score).toBe('number');
    });
  });

  describe('generateAccessibilityReport', () => {
    it('generates report for passing result', () => {
      const result: ValidationResult = {
        passed: true,
        errors: [],
        warnings: [],
        score: 100,
      };

      const report = generateAccessibilityReport(result);

      expect(report).toContain('WCAG 2.1 Level AA');
      expect(report).toContain('100/100');
      expect(report).toContain('Geçti');
    });

    it('generates report for failing result', () => {
      const result: ValidationResult = {
        passed: false,
        errors: [
          {
            rule: 'Image Alt Text',
            wcagRef: 'WCAG 2.1 SC 1.1.1',
            severity: 'critical',
            description: 'Görsel için alternatif metin yok',
            suggestion: 'Alt metni ekleyin',
          },
        ],
        warnings: [],
        score: 90,
      };

      const report = generateAccessibilityReport(result);

      expect(report).toContain('90/100');
      expect(report).toContain('Başarısız');
      expect(report).toContain('Image Alt Text');
      expect(report).toContain('Kritik');
    });

    it('includes all error details', () => {
      const result: ValidationResult = {
        passed: false,
        errors: [
          {
            rule: 'Test Rule',
            wcagRef: 'WCAG 2.1 SC 1.1.1',
            severity: 'serious',
            description: 'Test description',
            suggestion: 'Test suggestion',
          },
        ],
        warnings: [],
        score: 95,
      };

      const report = generateAccessibilityReport(result);

      expect(report).toContain('Test Rule');
      expect(report).toContain('WCAG 2.1 SC 1.1.1');
      expect(report).toContain('Ciddi');
      expect(report).toContain('Test description');
      expect(report).toContain('Test suggestion');
    });

    it('includes warnings section when present', () => {
      const result: ValidationResult = {
        passed: true,
        errors: [],
        warnings: [
          {
            rule: 'Warning Rule',
            wcagRef: 'WCAG 2.1 SC 2.2.2',
            description: 'Warning description',
            suggestion: 'Warning suggestion',
          },
        ],
        score: 100,
      };

      const report = generateAccessibilityReport(result);

      expect(report).toContain('Uyarılar');
      expect(report).toContain('Warning Rule');
    });
  });
});

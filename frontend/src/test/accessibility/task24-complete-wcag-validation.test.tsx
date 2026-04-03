import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  validateWCAG,
  validateTextContrast,
  validateForms,
  validateImages,
  validateKeyboardAccess,
  validateARIA,
  validateHeadings,
  calculateContrastRatio,
  checkContrastCompliance,
} from '../../utils/wcagValidator';
import AccessibleVideoPlayer from '../../components/Common/AccessibleVideoPlayer';
import { MathFormula } from '../../components/Accessibility/MathFormula';

/**
 * Task 24.4: Comprehensive WCAG 2.1 Level AA Validation Tests
 * Tests all accessibility validation utilities and components
 */

describe('Task 24.4: WCAG 2.1 Level AA Validation', () => {
  describe('Contrast Ratio Validation', () => {
    it('should calculate correct contrast ratio', () => {
      // Black on white
      const ratio1 = calculateContrastRatio('#000000', '#FFFFFF');
      expect(ratio1).toBeCloseTo(21, 1);

      // White on black
      const ratio2 = calculateContrastRatio('#FFFFFF', '#000000');
      expect(ratio2).toBeCloseTo(21, 1);

      // Gray on white
      const ratio3 = calculateContrastRatio('#767676', '#FFFFFF');
      expect(ratio3).toBeGreaterThan(4.5);
    });

    it('should validate AA compliance for normal text', () => {
      const result = checkContrastCompliance(4.5, 16, 400, 'AA');
      expect(result.passed).toBe(true);
      expect(result.level).toBe('AA');
    });

    it('should validate AA compliance for large text', () => {
      const result = checkContrastCompliance(3.2, 18, 400, 'AA');
      expect(result.passed).toBe(true);
      expect(result.level).toBe('AA');
    });

    it('should fail validation for insufficient contrast', () => {
      const result = checkContrastCompliance(2.5, 16, 400, 'AA');
      expect(result.passed).toBe(false);
      expect(result.level).toBe('fail');
    });

    it('should validate text contrast on page', () => {
      document.body.innerHTML = `
        <div style="color: #000; background-color: #fff;">
          <p>High contrast text</p>
        </div>
      `;

      const errors = validateTextContrast(document.body);
      expect(errors.length).toBe(0);
    });

    it('should detect insufficient text contrast', () => {
      document.body.innerHTML = `
        <div style="color: #ccc; background-color: #fff;">
          <p>Low contrast text</p>
        </div>
      `;

      const errors = validateTextContrast(document.body);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].rule).toBe('Contrast Ratio');
    });
  });

  describe('Form Validation', () => {
    it('should validate form labels', () => {
      document.body.innerHTML = `
        <form>
          <label for="name">Name:</label>
          <input type="text" id="name" />
        </form>
      `;

      const errors = validateForms(document.body);
      expect(errors.length).toBe(0);
    });

    it('should detect missing form labels', () => {
      document.body.innerHTML = `
        <form>
          <input type="text" id="email" />
        </form>
      `;

      const errors = validateForms(document.body);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].rule).toBe('Form Label');
      expect(errors[0].wcagRef).toContain('3.3.2');
    });

    it('should accept aria-label as alternative', () => {
      document.body.innerHTML = `
        <form>
          <input type="text" aria-label="Search" />
        </form>
      `;

      const errors = validateForms(document.body);
      expect(errors.length).toBe(0);
    });

    it('should validate required field indicators', () => {
      document.body.innerHTML = `
        <form>
          <label for="email">Email *</label>
          <input type="email" id="email" required />
        </form>
      `;

      const errors = validateForms(document.body);
      expect(errors.length).toBe(0);
    });

    it('should validate error messages', () => {
      document.body.innerHTML = `
        <form>
          <label for="email">Email</label>
          <input type="email" id="email" aria-invalid="true" aria-describedby="email-error" />
          <span id="email-error">Invalid email format</span>
        </form>
      `;

      const errors = validateForms(document.body);
      expect(errors.length).toBe(0);
    });
  });

  describe('Image Validation', () => {
    it('should validate alt text presence', () => {
      document.body.innerHTML = `
        <img src="test.jpg" alt="Test image" />
      `;

      const errors = validateImages(document.body);
      expect(errors.length).toBe(0);
    });

    it('should detect missing alt text', () => {
      document.body.innerHTML = `
        <img src="test.jpg" />
      `;

      const errors = validateImages(document.body);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].rule).toBe('Image Alt Text');
      expect(errors[0].wcagRef).toBe('WCAG 2.1 SC 1.1.1');
    });

    it('should accept empty alt for decorative images', () => {
      document.body.innerHTML = `
        <img src="decorative.jpg" alt="" />
      `;

      const errors = validateImages(document.body);
      expect(errors.length).toBe(0);
    });

    it('should detect overly long alt text', () => {
      const longAlt = 'A'.repeat(200);
      document.body.innerHTML = `
        <img src="test.jpg" alt="${longAlt}" />
      `;

      const errors = validateImages(document.body);
      expect(errors.some(e => e.rule === 'Alt Text Length')).toBe(true);
    });
  });

  describe('Keyboard Accessibility Validation', () => {
    it('should validate keyboard accessible buttons', () => {
      document.body.innerHTML = `
        <button onclick="handleClick()">Click me</button>
      `;

      const errors = validateKeyboardAccess(document.body);
      expect(errors.length).toBe(0);
    });

    it('should detect non-keyboard accessible elements', () => {
      document.body.innerHTML = `
        <div onclick="handleClick()">Click me</div>
      `;

      const errors = validateKeyboardAccess(document.body);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].rule).toBe('Keyboard Accessibility');
    });

    it('should validate custom interactive elements with tabindex', () => {
      document.body.innerHTML = `
        <div role="button" tabindex="0" onclick="handleClick()">Custom button</div>
      `;

      const errors = validateKeyboardAccess(document.body);
      expect(errors.length).toBe(0);
    });
  });

  describe('ARIA Validation', () => {
    it('should validate correct ARIA roles', () => {
      document.body.innerHTML = `
        <div role="navigation">
          <a href="#">Link</a>
        </div>
      `;

      const errors = validateARIA(document.body);
      expect(errors.length).toBe(0);
    });

    it('should detect invalid ARIA roles', () => {
      document.body.innerHTML = `
        <div role="invalid-role">Content</div>
      `;

      const errors = validateARIA(document.body);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].rule).toBe('Invalid ARIA Role');
    });

    it('should validate aria-labelledby references', () => {
      document.body.innerHTML = `
        <div id="label">Label</div>
        <button aria-labelledby="label">Button</button>
      `;

      const errors = validateARIA(document.body);
      expect(errors.length).toBe(0);
    });

    it('should detect missing aria-labelledby references', () => {
      document.body.innerHTML = `
        <button aria-labelledby="nonexistent">Button</button>
      `;

      const errors = validateARIA(document.body);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].rule).toBe('ARIA Reference');
    });
  });

  describe('Heading Hierarchy Validation', () => {
    it('should validate correct heading hierarchy', () => {
      document.body.innerHTML = `
        <h1>Main Title</h1>
        <h2>Subtitle</h2>
        <h3>Section</h3>
      `;

      const errors = validateHeadings(document.body);
      expect(errors.length).toBe(0);
    });

    it('should detect skipped heading levels', () => {
      document.body.innerHTML = `
        <h1>Main Title</h1>
        <h3>Skipped h2</h3>
      `;

      const errors = validateHeadings(document.body);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].rule).toBe('Heading Hierarchy');
    });

    it('should detect empty headings', () => {
      document.body.innerHTML = `
        <h1></h1>
      `;

      const errors = validateHeadings(document.body);
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].rule).toBe('Empty Heading');
    });

    it('should detect multiple h1 elements', () => {
      document.body.innerHTML = `
        <h1>First Title</h1>
        <h1>Second Title</h1>
      `;

      const errors = validateHeadings(document.body);
      expect(errors.some(e => e.rule === 'Multiple H1')).toBe(true);
    });
  });

  describe('Comprehensive WCAG Validation', () => {
    it('should pass validation for accessible page', () => {
      document.documentElement.setAttribute('lang', 'tr');
      document.body.innerHTML = `
        <main>
          <h1>Accessible Page</h1>
          <p style="color: #000; background-color: #fff;">High contrast text</p>
          <img src="test.jpg" alt="Test image" />
          <form>
            <label for="name">Name:</label>
            <input type="text" id="name" />
          </form>
          <button>Submit</button>
        </main>
      `;

      const result = validateWCAG(document.body);
      expect(result.score).toBeGreaterThan(80);
    });

    it('should calculate score based on errors', () => {
      document.body.innerHTML = `
        <div>
          <img src="test.jpg" />
          <input type="text" />
        </div>
      `;

      const result = validateWCAG(document.body);
      expect(result.score).toBeLessThan(100);
      expect(result.passed).toBe(false);
    });
  });

  describe('Accessible Video Player', () => {
    it('should render with keyboard shortcuts', () => {
      const { container } = render(
        <AccessibleVideoPlayer
          src="test-video.mp4"
          title="Test Video"
        />
      );

      const videoPlayer = container.querySelector('.accessible-video-player');
      expect(videoPlayer).toBeInTheDocument();
      expect(videoPlayer).toHaveAttribute('role', 'region');
    });

    it('should have ARIA labels for controls', () => {
      const { container } = render(
        <AccessibleVideoPlayer
          src="test-video.mp4"
          title="Test Video"
        />
      );

      const playButton = screen.getByLabelText(/Oynat|Duraklat/);
      expect(playButton).toBeInTheDocument();
    });
  });

  describe('Accessible Math Formulas', () => {
    it('should render with Turkish ARIA label', () => {
      const { container } = render(
        <MathFormula
          formula="x^2 + 2x + 1 = 0"
          ariaLabel="x kare artı 2 x artı 1 eşittir sıfır"
        />
      );

      const mathElement = container.querySelector('[role="math"]');
      expect(mathElement).toBeInTheDocument();
      expect(mathElement).toHaveAttribute('lang', 'tr');
    });
  });
});

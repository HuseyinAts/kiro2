/**
 * WCAG 2.1 Level AA Validation Utilities
 * Comprehensive accessibility validation for the entire platform
 */

export interface ValidationResult {
  passed: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  score: number; // 0-100
}

export interface ValidationError {
  rule: string;
  wcagRef: string;
  severity: 'critical' | 'serious';
  element?: HTMLElement;
  description: string;
  suggestion: string;
}

export interface ValidationWarning {
  rule: string;
  wcagRef: string;
  element?: HTMLElement;
  description: string;
  suggestion: string;
}

interface ContrastResult {
  ratio: number;
  passed: boolean;
  level: 'AA' | 'AAA' | 'fail';
}

/**
 * Calculate contrast ratio between two colors
 * @param color1 - First color (hex or rgb)
 * @param color2 - Second color (hex or rgb)
 * @returns Contrast ratio (1-21)
 */
export const calculateContrastRatio = (color1: string, color2: string): number => {
  const rgb1 = parseColor(color1);
  const rgb2 = parseColor(color2);

  const l1 = getRelativeLuminance(rgb1);
  const l2 = getRelativeLuminance(rgb2);

  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  return (lighter + 0.05) / (darker + 0.05);
};

/**
 * Parse color string to RGB values
 */
const parseColor = (color: string): [number, number, number] => {
  // Remove whitespace
  color = color.trim();

  // Hex color
  if (color.startsWith('#')) {
    const hex = color.substring(1);
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return [r, g, b];
  }

  // RGB color
  if (color.startsWith('rgb')) {
    const match = color.match(/\d+/g);
    if (match && match.length >= 3) {
      return [parseInt(match[0]), parseInt(match[1]), parseInt(match[2])];
    }
  }

  // Default to black
  return [0, 0, 0];
};

/**
 * Calculate relative luminance
 */
const getRelativeLuminance = ([r, g, b]: [number, number, number]): number => {
  const [rs, gs, bs] = [r, g, b].map((c) => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
};

/**
 * Check if contrast ratio meets WCAG standards
 */
export const checkContrastCompliance = (
  ratio: number,
  fontSize: number,
  fontWeight: number,
  level: 'AA' | 'AAA' = 'AA',
): ContrastResult => {
  const isLargeText = fontSize >= 18 || (fontSize >= 14 && fontWeight >= 700);

  const thresholds = {
    AA: isLargeText ? 3 : 4.5,
    AAA: isLargeText ? 4.5 : 7,
  };

  const passed = ratio >= thresholds[level];
  const levelAAA = ratio >= thresholds.AAA;

  return {
    ratio,
    passed,
    level: levelAAA ? 'AAA' : passed ? 'AA' : 'fail',
  };
};

/**
 * Validate all text elements on the page for contrast
 */
export const validateTextContrast = (root: HTMLElement = document.body): ValidationError[] => {
  const errors: ValidationError[] = [];
  const textElements = root.querySelectorAll<HTMLElement>('p, h1, h2, h3, h4, h5, h6, span, a, button, label, li');

  textElements.forEach((element) => {
    const styles = window.getComputedStyle(element);
    const color = styles.color;
    const backgroundColor = styles.backgroundColor;
    const fontSize = parseFloat(styles.fontSize);
    const fontWeight = parseInt(styles.fontWeight);

    // Skip if background is transparent
    if (backgroundColor === 'rgba(0, 0, 0, 0)' || backgroundColor === 'transparent') {
      return;
    }

    const ratio = calculateContrastRatio(color, backgroundColor);
    const result = checkContrastCompliance(ratio, fontSize, fontWeight, 'AA');

    if (!result.passed) {
      errors.push({
        rule: 'Contrast Ratio',
        wcagRef: 'WCAG 2.1 SC 1.4.3',
        severity: 'serious',
        element,
        description: `Yetersiz kontrast oranı: ${ratio.toFixed(2)}:1 (minimum 4.5:1 gerekli)`,
        suggestion: 'Metin rengini veya arka plan rengini değiştirin',
      });
    }
  });

  return errors;
};

/**
 * Validate form elements
 */
export const validateForms = (root: HTMLElement = document.body): ValidationError[] => {
  const errors: ValidationError[] = [];
  const inputs = root.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(
    'input, textarea, select',
  );

  inputs.forEach((input) => {
    // Check for label
    const id = input.id;
    const hasLabel = id && document.querySelector(`label[for="${id}"]`);
    const hasAriaLabel = input.hasAttribute('aria-label') || input.hasAttribute('aria-labelledby');

    if (!hasLabel && !hasAriaLabel) {
      errors.push({
        rule: 'Form Label',
        wcagRef: 'WCAG 2.1 SC 1.3.1, 3.3.2',
        severity: 'critical',
        element: input,
        description: 'Form elemanının etiketi (label) yok',
        suggestion: 'Her form elemanı için bir <label> veya aria-label ekleyin',
      });
    }

    // Check for required field indicator
    if (input.hasAttribute('required')) {
      const label = id ? document.querySelector(`label[for="${id}"]`) : null;
      if (label && !label.textContent?.includes('*') && !input.hasAttribute('aria-required')) {
        errors.push({
          rule: 'Required Field Indicator',
          wcagRef: 'WCAG 2.1 SC 3.3.2',
          severity: 'serious',
          element: input,
          description: 'Zorunlu alan görsel olarak belirtilmemiş',
          suggestion: 'Zorunlu alanları * veya "zorunlu" metni ile işaretleyin',
        });
      }
    }

    // Check for error messages
    if (input.hasAttribute('aria-invalid') && input.getAttribute('aria-invalid') === 'true') {
      const hasErrorMessage = input.hasAttribute('aria-describedby');
      if (!hasErrorMessage) {
        errors.push({
          rule: 'Error Message',
          wcagRef: 'WCAG 2.1 SC 3.3.1',
          severity: 'critical',
          element: input,
          description: 'Hata mesajı ekran okuyuculara erişilemiyor',
          suggestion: 'aria-describedby ile hata mesajını bağlayın',
        });
      }
    }
  });

  return errors;
};

/**
 * Validate images for alt text
 */
export const validateImages = (root: HTMLElement = document.body): ValidationError[] => {
  const errors: ValidationError[] = [];
  const images = root.querySelectorAll<HTMLImageElement>('img');

  images.forEach((img) => {
    const hasAlt = img.hasAttribute('alt');
    const alt = img.getAttribute('alt');
    const isDecorative = img.hasAttribute('role') && img.getAttribute('role') === 'presentation';

    if (!hasAlt && !isDecorative) {
      errors.push({
        rule: 'Image Alt Text',
        wcagRef: 'WCAG 2.1 SC 1.1.1',
        severity: 'critical',
        element: img,
        description: 'Görsel için alternatif metin (alt) yok',
        suggestion: 'Tüm görsellere anlamlı alt metni ekleyin veya dekoratif görseller için alt="" kullanın',
      });
    } else if (hasAlt && alt && alt.length > 150) {
      errors.push({
        rule: 'Alt Text Length',
        wcagRef: 'WCAG 2.1 SC 1.1.1',
        severity: 'serious',
        element: img,
        description: `Alt metin çok uzun (${alt.length} karakter)`,
        suggestion: 'Alt metnini 150 karakterin altına indirin, detaylı açıklama için longdesc kullanın',
      });
    }
  });

  return errors;
};

/**
 * Validate keyboard accessibility
 */
export const validateKeyboardAccess = (root: HTMLElement = document.body): ValidationError[] => {
  const errors: ValidationError[] = [];
  const interactive = root.querySelectorAll<HTMLElement>(
    'button, a, input, textarea, select, [onclick], [role="button"], [role="link"]',
  );

  interactive.forEach((element) => {
    // Check if element is focusable
    const tabIndex = element.getAttribute('tabindex');
    const isFocusable = element.tabIndex >= 0 || ['A', 'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName);

    if (!isFocusable && element.hasAttribute('onclick')) {
      errors.push({
        rule: 'Keyboard Accessibility',
        wcagRef: 'WCAG 2.1 SC 2.1.1',
        severity: 'critical',
        element,
        description: 'Tıklanabilir eleman klavye ile erişilemiyor',
        suggestion: 'tabindex="0" ekleyin veya <button> elemanı kullanın',
      });
    }

    // Check for negative tabindex
    if (tabIndex && parseInt(tabIndex) < 0 && element.hasAttribute('onclick')) {
      errors.push({
        rule: 'Negative Tabindex',
        wcagRef: 'WCAG 2.1 SC 2.1.1',
        severity: 'serious',
        element,
        description: 'tabindex="-1" elemanı klavye erişimini engelliyor',
        suggestion: 'tabindex="-1" sadece programatik odaklanma için kullanılmalı',
      });
    }
  });

  return errors;
};

/**
 * Validate ARIA attributes
 */
export const validateARIA = (root: HTMLElement = document.body): ValidationError[] => {
  const errors: ValidationError[] = [];
  const ariaElements = root.querySelectorAll<HTMLElement>('[aria-label], [aria-labelledby], [aria-describedby], [role]');

  ariaElements.forEach((element) => {
    // Check for valid roles
    const role = element.getAttribute('role');
    if (role) {
      const validRoles = [
        'alert', 'alertdialog', 'application', 'article', 'banner', 'button',
        'checkbox', 'combobox', 'complementary', 'contentinfo', 'dialog',
        'directory', 'document', 'feed', 'figure', 'form', 'grid', 'gridcell',
        'group', 'heading', 'img', 'link', 'list', 'listbox', 'listitem',
        'log', 'main', 'marquee', 'math', 'menu', 'menubar', 'menuitem',
        'navigation', 'note', 'option', 'presentation', 'progressbar',
        'radio', 'radiogroup', 'region', 'row', 'rowgroup', 'scrollbar',
        'search', 'searchbox', 'separator', 'slider', 'spinbutton', 'status',
        'switch', 'tab', 'table', 'tablist', 'tabpanel', 'term', 'textbox',
        'timer', 'toolbar', 'tooltip', 'tree', 'treegrid', 'treeitem',
      ];

      if (!validRoles.includes(role)) {
        errors.push({
          rule: 'Invalid ARIA Role',
          wcagRef: 'WCAG 2.1 SC 4.1.2',
          severity: 'serious',
          element,
          description: `Geçersiz ARIA role: "${role}"`,
          suggestion: 'Geçerli bir ARIA role kullanın veya role attribute\'ünü kaldırın',
        });
      }
    }

    // Check for aria-labelledby references
    const labelledby = element.getAttribute('aria-labelledby');
    if (labelledby) {
      const ids = labelledby.split(' ');
      ids.forEach((id) => {
        if (!document.getElementById(id)) {
          errors.push({
            rule: 'ARIA Reference',
            wcagRef: 'WCAG 2.1 SC 4.1.2',
            severity: 'critical',
            element,
            description: `aria-labelledby referansı mevcut değil: "${id}"`,
            suggestion: 'Referans verilen ID\'nin sayfada mevcut olduğundan emin olun',
          });
        }
      });
    }

    // Check for aria-describedby references
    const describedby = element.getAttribute('aria-describedby');
    if (describedby) {
      const ids = describedby.split(' ');
      ids.forEach((id) => {
        if (!document.getElementById(id)) {
          errors.push({
            rule: 'ARIA Reference',
            wcagRef: 'WCAG 2.1 SC 4.1.2',
            severity: 'critical',
            element,
            description: `aria-describedby referansı mevcut değil: "${id}"`,
            suggestion: 'Referans verilen ID\'nin sayfada mevcut olduğundan emin olun',
          });
        }
      });
    }
  });

  return errors;
};

/**
 * Validate headings hierarchy
 */
export const validateHeadings = (root: HTMLElement = document.body): ValidationError[] => {
  const errors: ValidationError[] = [];
  const headings = root.querySelectorAll<HTMLHeadingElement>('h1, h2, h3, h4, h5, h6');
  let previousLevel = 0;

  headings.forEach((heading) => {
    const level = parseInt(heading.tagName.substring(1));

    // Check for skipped levels
    if (level > previousLevel + 1 && previousLevel !== 0) {
      errors.push({
        rule: 'Heading Hierarchy',
        wcagRef: 'WCAG 2.1 SC 1.3.1',
        severity: 'serious',
        element: heading,
        description: `Başlık seviyesi atlandı: h${previousLevel} → h${level}`,
        suggestion: 'Başlık seviyelerini sırayla kullanın (h1, h2, h3...)',
      });
    }

    // Check for empty headings
    if (!heading.textContent?.trim()) {
      errors.push({
        rule: 'Empty Heading',
        wcagRef: 'WCAG 2.1 SC 2.4.6',
        severity: 'critical',
        element: heading,
        description: 'Boş başlık elemanı',
        suggestion: 'Başlık elemanlarına anlamlı metin ekleyin',
      });
    }

    previousLevel = level;
  });

  // Check for multiple h1
  const h1Count = root.querySelectorAll('h1').length;
  if (h1Count > 1) {
    errors.push({
      rule: 'Multiple H1',
      wcagRef: 'WCAG 2.1 SC 1.3.1',
      severity: 'serious',
      description: `Sayfada birden fazla h1 elemanı var (${h1Count} adet)`,
      suggestion: 'Sayfada sadece bir h1 elemanı olmalı',
    });
  }

  return errors;
};

/**
 * Validate page language
 */
export const validateLanguage = (): ValidationError[] => {
  const errors: ValidationError[] = [];
  const html = document.documentElement;

  if (!html.hasAttribute('lang')) {
    errors.push({
      rule: 'Page Language',
      wcagRef: 'WCAG 2.1 SC 3.1.1',
      severity: 'critical',
      description: 'Sayfa dili belirtilmemiş',
      suggestion: '<html> elemanına lang="tr" attribute\'ü ekleyin',
    });
  }

  return errors;
};

/**
 * Run comprehensive WCAG validation
 */
export const validateWCAG = (root: HTMLElement = document.body): ValidationResult => {
  const errors: ValidationError[] = [];
  const warnings: ValidationWarning[] = [];

  // Run all validation checks
  errors.push(...validateTextContrast(root));
  errors.push(...validateForms(root));
  errors.push(...validateImages(root));
  errors.push(...validateKeyboardAccess(root));
  errors.push(...validateARIA(root));
  errors.push(...validateHeadings(root));
  errors.push(...validateLanguage());

  // Calculate score
  const criticalCount = errors.filter((e) => e.severity === 'critical').length;
  const seriousCount = errors.filter((e) => e.severity === 'serious').length;
  const score = Math.max(0, 100 - (criticalCount * 10 + seriousCount * 5));

  return {
    passed: errors.length === 0,
    errors,
    warnings,
    score,
  };
};

/**
 * Generate accessibility report
 */
export const generateAccessibilityReport = (result: ValidationResult): string => {
  let report = '# WCAG 2.1 Level AA Erişilebilirlik Raporu\n\n';
  report += `**Skor**: ${result.score}/100\n`;
  report += `**Durum**: ${result.passed ? '✅ Geçti' : '❌ Başarısız'}\n`;
  report += `**Toplam Hata**: ${result.errors.length}\n`;
  report += `**Toplam Uyarı**: ${result.warnings.length}\n\n`;

  if (result.errors.length > 0) {
    report += '## Hatalar\n\n';
    result.errors.forEach((error, index) => {
      report += `### ${index + 1}. ${error.rule} (${error.wcagRef})\n`;
      report += `- **Önem**: ${error.severity === 'critical' ? '🔴 Kritik' : '🟠 Ciddi'}\n`;
      report += `- **Açıklama**: ${error.description}\n`;
      report += `- **Öneri**: ${error.suggestion}\n\n`;
    });
  }

  if (result.warnings.length > 0) {
    report += '## Uyarılar\n\n';
    result.warnings.forEach((warning, index) => {
      report += `### ${index + 1}. ${warning.rule} (${warning.wcagRef})\n`;
      report += `- **Açıklama**: ${warning.description}\n`;
      report += `- **Öneri**: ${warning.suggestion}\n\n`;
    });
  }

  return report;
};

export default validateWCAG;

/**
 * Erişilebilirlik Bileşenleri
 * WCAG 2.1 Level AA uyumlu erişilebilirlik özellikleri
 */

// Disleksi Desteği
export { TypographySettings } from './TypographySettings';
export { ColorContrastSettings } from './ColorContrastSettings';
export { ReadingHelpers } from './ReadingHelpers';
export { TextToSpeech } from './TextToSpeech';
export { default as TypographySettingsDefault } from './TypographySettings';
export { default as ReadingHelpersDefault } from './ReadingHelpers';
export { default as TextToSpeechDefault } from './TextToSpeech';

// Diskalkuli Desteği - Görsel Matematik Temsilleri
export {
  NumberBlocks,
  FractionBars,
  GeometricShapes3D,
  GraphPlotter,
} from './Dyscalculia';

// DEHB Desteği - Dikkat Yönetimi
export { VisualTimer } from './ADHD';

// Video Erişilebilirliği (canonical: Common/AccessibleVideoPlayer)
export { default as AccessibleVideoPlayer } from '../Common/AccessibleVideoPlayer';
export { default as AccessibleVideoPlayerDefault } from '../Common/AccessibleVideoPlayer';

// Matematik Formül Erişilebilirliği
export {
  MathFormula,
  QuadraticFormula,
  PythagoreanTheorem,
  AreaOfCircle,
  Derivative,
  Integral,
  Fraction,
  SquareRoot,
  Exponent,
} from './MathFormula';
export { default as MathFormulaDefault } from './MathFormula';

// WCAG Doğrulama
export { AccessibilityValidator } from './AccessibilityValidator';
export { default as AccessibilityValidatorDefault } from './AccessibilityValidator';

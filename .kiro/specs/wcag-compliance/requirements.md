# Requirements Document - WCAG 2.1 Level AA Compliance

## Introduction

Bu spec, WCAG 2.1 Level AA uyumluluğunu sağlayan sistemi tanımlar. Perceivable, Operable, Understandable, Robust prensipleriyle tam erişilebilirlik sağlar.

## Glossary

- **WCAG**: Web Content Accessibility Guidelines
- **Perceivable**: Algılanabilir
- **Operable**: İşletilebilir
- **Understandable**: Anlaşılabilir
- **Robust**: Sağlam
- **ARIA**: Accessible Rich Internet Applications

## Requirements

### Requirement 1: Perceivable - Text Alternatives
**User Story:** As a görme engelli kullanıcı, I want text alternatives, so that içeriği anlayayım.
#### Acceptance Criteria
1. **REQ-1.1** WHEN image kullanıldığında, THE System SHALL meaningful alt text sağlar
2. **REQ-1.2** WHEN decorative image olduğunda, THE System SHALL empty alt attribute (alt="") kullanır
3. **REQ-1.3** WHEN complex image (chart, diagram) olduğunda, THE System SHALL detailed description sağlar
4. **REQ-1.4** WHEN icon button kullanıldığında, THE System SHALL aria-label ekler
5. **REQ-1.5** WHEN video content olduğunda, THE System SHALL caption ve transcript sağlar
6. **REQ-1.6** WHEN audio content olduğunda, THE System SHALL transcript sağlar

### Requirement 2: Perceivable - Color Contrast
**User Story:** As a görme zorluğu olan kullanıcı, I want high contrast, so that metni okuyabileyim.
#### Acceptance Criteria
1. **REQ-2.1** WHEN text display edildiğinde, THE System SHALL 4.5:1 contrast ratio (normal text) sağlar
2. **REQ-2.2** WHEN large text (18pt+) kullanıldığında, THE System SHALL 3:1 contrast ratio sağlar
3. **REQ-2.3** WHEN UI component olduğunda, THE System SHALL 3:1 contrast ratio (border, icon) sağlar
4. **REQ-2.4** WHEN color-only information kullanıldığında, THE System SHALL additional indicator (icon, pattern) ekler
5. **REQ-2.5** WHEN contrast check yapıldığında, THE System SHALL automated testing tool kullanır
6. **REQ-2.6** WHEN dark mode kullanıldığında, THE System SHALL WCAG contrast maintain eder

### Requirement 3: Operable - Keyboard Navigation
**User Story:** As a klavye kullanıcısı, I want keyboard navigation, so that mouse olmadan kullanayım.
#### Acceptance Criteria
1. **REQ-3.1** WHEN interactive element olduğunda, THE System SHALL keyboard accessible yapar
2. **REQ-3.2** WHEN focus indicator gösterildiğinde, THE System SHALL visible focus outline sağlar
3. **REQ-3.3** WHEN tab order set edildiğinde, THE System SHALL logical sequence kullanır
4. **REQ-3.4** WHEN keyboard trap avoid edildiğinde, THE System SHALL focus escape mechanism sağlar
5. **REQ-3.5** WHEN keyboard shortcut sağlandığında, THE System SHALL documented shortcut list sunar
6. **REQ-3.6** WHEN skip link eklediğinde, THE System SHALL "Skip to main content" link sağlar

### Requirement 4: Operable - Timing
**User Story:** As a yavaş okuyan kullanıcı, I want timing control, so that yeterli zamanım olsun.
#### Acceptance Criteria
1. **REQ-4.1** WHEN time limit olduğunda, THE System SHALL adjustable, extendable, disableable yapar
2. **REQ-4.2** WHEN timeout warning verildiğinde, THE System SHALL 20 second advance warning sağlar
3. **REQ-4.3** WHEN auto-refresh kullanıldığında, THE System SHALL user control sağlar
4. **REQ-4.4** WHEN moving content olduğunda, THE System SHALL pause, stop, hide mechanism sağlar
5. **REQ-4.5** WHEN carousel kullanıldığında, THE System SHALL auto-play disable option sağlar
6. **REQ-4.6** WHEN session timeout olduğunda, THE System SHALL data loss prevention sağlar

### Requirement 5: Understandable - Readable
**User Story:** As a kullanıcı, I want readable content, so that anlayabileyim.
#### Acceptance Criteria
1. **REQ-5.1** WHEN page language set edildiğinde, THE System SHALL lang attribute kullanır
2. **REQ-5.2** WHEN language change olduğunda, THE System SHALL lang attribute update eder
3. **REQ-5.3** WHEN unusual word kullanıldığında, THE System SHALL definition sağlar
4. **REQ-5.4** WHEN abbreviation kullanıldığında, THE System SHALL expansion sağlar
5. **REQ-5.5** WHEN reading level yüksek olduğunda, THE System SHALL simplified version option sağlar
6. **REQ-5.6** WHEN pronunciation gerektiğinde, THE System SHALL phonetic guide sağlar

### Requirement 6: Understandable - Predictable
**User Story:** As a bilişsel engelli kullanıcı, I want predictable interface, so that şaşırmayayım.
#### Acceptance Criteria
1. **REQ-6.1** WHEN focus change olduğunda, THE System SHALL unexpected context change yapmaz
2. **REQ-6.2** WHEN input change olduğunda, THE System SHALL automatic submission yapmaz
3. **REQ-6.3** WHEN navigation consistent olduğunda, THE System SHALL same order maintain eder
4. **REQ-6.4** WHEN component consistent olduğunda, THE System SHALL same function için same label kullanır
5. **REQ-6.5** WHEN change request edildiğinde, THE System SHALL user-initiated action gerektirir
6. **REQ-6.6** WHEN help mechanism sağlandığında, THE System SHALL consistent location kullanır

### Requirement 7: Understandable - Input Assistance
**User Story:** As a kullanıcı, I want input assistance, so that hata yapmayayım.
#### Acceptance Criteria
1. **REQ-7.1** WHEN form field olduğunda, THE System SHALL clear label sağlar
2. **REQ-7.2** WHEN error detect edildiğinde, THE System SHALL error message gösterir
3. **REQ-7.3** WHEN error suggestion verildiğinde, THE System SHALL correction hint sağlar
4. **REQ-7.4** WHEN legal/financial transaction olduğunda, THE System SHALL review, confirm, reverse mechanism sağlar
5. **REQ-7.5** WHEN required field olduğunda, THE System SHALL required indicator gösterir
6. **REQ-7.6** WHEN input format gerektiğinde, THE System SHALL format instruction sağlar

### Requirement 8: Robust - Compatible
**User Story:** As a yardımcı teknoloji kullanıcısı, I want compatibility, so that screen reader çalışsın.
#### Acceptance Criteria
1. **REQ-8.1** WHEN HTML markup yazıldığında, THE System SHALL valid, semantic HTML kullanır
2. **REQ-8.2** WHEN ARIA attribute kullanıldığında, THE System SHALL correct role, state, property kullanır
3. **REQ-8.3** WHEN custom component oluşturulduğunda, THE System SHALL ARIA pattern follow eder
4. **REQ-8.4** WHEN name, role, value set edildiğinde, THE System SHALL programmatically determinable yapar
5. **REQ-8.5** WHEN status message gösterildiğinde, THE System SHALL aria-live region kullanır
6. **REQ-8.6** WHEN accessibility test edildiğinde, THE System SHALL automated tool (axe, WAVE) + manual test yapar

## Bağımlılıklar
- **axe-core**: Accessibility testing
- **react-aria**: ARIA components
- **eslint-plugin-jsx-a11y**: Linting
- **pa11y**: Automated testing
- **lighthouse**: Audit tool

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 2 hafta
**Beklenen WCAG Compliance:** %100 Level AA

## Success Metrics
1. **WCAG 2.1 Level AA Compliance:** %100
2. **Automated Test Pass Rate:** %100
3. **Manual Test Pass Rate:** >= %95
4. **Screen Reader Compatibility:** %100
5. **Keyboard Navigation Coverage:** %100

## Verification Flow
1. **Automated Testing**: axe-core, pa11y, Lighthouse
2. **Manual Testing**: Screen reader (NVDA, JAWS), keyboard-only navigation
3. **User Testing**: Real users with disabilities
4. **Compliance Audit**: Third-party WCAG audit
5. **Continuous Monitoring**: CI/CD accessibility checks

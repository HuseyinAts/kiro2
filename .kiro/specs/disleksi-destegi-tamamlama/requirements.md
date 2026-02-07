# Requirements Document - Disleksi Desteği Tamamlama

## Introduction

Bu spec, disleksi öğrenciler için erişilebilirlik özelliklerini tanımlar. Font customization, reading aids, text-to-speech ile disleksi-friendly platform sağlar.

## Glossary

- **Disleksi**: Okuma güçlüğü
- **OpenDyslexic**: Disleksi dostu font
- **Text-to-Speech**: Metinden sese
- **Reading Ruler**: Okuma cetveli
- **Line Spacing**: Satır aralığı
- **Word Spacing**: Kelime aralığı

## Requirements

### Requirement 1: Font Customization
**User Story:** As a disleksi öğrenci, I want font customization, so that okumam kolaylaşsın.
#### Acceptance Criteria
1. **REQ-1.1** WHEN font seçildiğinde, THE System SHALL OpenDyslexic, Comic Sans, Arial options sağlar
2. **REQ-1.2** WHEN font size adjust edildiğinde, THE System SHALL 14-24px range destekler
3. **REQ-1.3** WHEN font weight set edildiğinde, THE System SHALL normal, bold options sağlar
4. **REQ-1.4** WHEN font preference save edildiğinde, THE System SHALL user profile'da saklar
5. **REQ-1.5** WHEN font apply edildiğinde, THE System SHALL tüm text content'e uygular
6. **REQ-1.6** WHEN font preview gösterildiğinde, THE System SHALL sample text ile demo sağlar

### Requirement 2: Text Spacing
**User Story:** As a disleksi öğrenci, I want text spacing, so that kelimeler net görünsin.
#### Acceptance Criteria
1. **REQ-2.1** WHEN line spacing adjust edildiğinde, THE System SHALL 1.5x-2.5x range destekler
2. **REQ-2.2** WHEN word spacing adjust edildiğinde, THE System SHALL 0.1em-0.5em range destekler
3. **REQ-2.3** WHEN letter spacing adjust edildiğinde, THE System SHALL 0.05em-0.2em range destekler
4. **REQ-2.4** WHEN paragraph spacing set edildiğinde, THE System SHALL 1.5em-3em range destekler
5. **REQ-2.5** WHEN spacing preset kullanıldığında, THE System SHALL "Comfortable", "Extra Comfortable" options sağlar
6. **REQ-2.6** WHEN spacing apply edildiğinde, THE System SHALL CSS custom properties kullanır

### Requirement 3: Reading Aids
**User Story:** As a disleksi öğrenci, I want reading aids, so that odaklanmam artsın.
#### Acceptance Criteria
1. **REQ-3.1** WHEN reading ruler enable edildiğinde, THE System SHALL highlight current line gösterir
2. **REQ-3.2** WHEN reading mask kullanıldığında, THE System SHALL dimmed overlay sağlar
3. **REQ-3.3** WHEN focus mode aktif olduğunda, THE System SHALL distraction-free view sağlar
4. **REQ-3.4** WHEN syllable highlighting enable edildiğinde, THE System SHALL hece vurgulama yapar
5. **REQ-3.5** WHEN word highlighting kullanıldığında, THE System SHALL hover'da kelime highlight eder
6. **REQ-3.6** WHEN reading guide customize edildiğinde, THE System SHALL color, opacity, height adjust destekler

### Requirement 4: Text-to-Speech
**User Story:** As a disleksi öğrenci, I want text-to-speech, so that dinleyerek öğreneyim.
#### Acceptance Criteria
1. **REQ-4.1** WHEN TTS enable edildiğinde, THE System SHALL Web Speech API kullanır
2. **REQ-4.2** WHEN voice seçildiğinde, THE System SHALL Turkish voice options sağlar
3. **REQ-4.3** WHEN speech rate adjust edildiğinde, THE System SHALL 0.5x-2x range destekler
4. **REQ-4.4** WHEN pitch adjust edildiğinde, THE System SHALL 0.5-2 range destekler
5. **REQ-4.5** WHEN text highlight edildiğinde, THE System SHALL okunan kelimeyi vurgular
6. **REQ-4.6** WHEN playback control sağlandığında, THE System SHALL play, pause, stop, skip buttons ekler

### Requirement 5: Color and Contrast
**User Story:** As a disleksi öğrenci, I want color customization, so that göz yorgunluğum azalsın.
#### Acceptance Criteria
1. **REQ-5.1** WHEN background color seçildiğinde, THE System SHALL cream, light blue, light green options sağlar
2. **REQ-5.2** WHEN text color adjust edildiğinde, THE System SHALL high contrast options sağlar
3. **REQ-5.3** WHEN color scheme apply edildiğinde, THE System SHALL WCAG AA contrast ratio sağlar
4. **REQ-5.4** WHEN dark mode enable edildiğinde, THE System SHALL disleksi-friendly dark theme kullanır
5. **REQ-5.5** WHEN color overlay kullanıldığında, THE System SHALL tinted screen filter sağlar
6. **REQ-5.6** WHEN color blindness mode aktif olduğunda, THE System SHALL appropriate palette kullanır

### Requirement 6: Content Simplification
**User Story:** As a disleksi öğrenci, I want content simplification, so that anlamam kolaylaşsın.
#### Acceptance Criteria
1. **REQ-6.1** WHEN text simplify edildiğinde, THE System SHALL complex sentence'ları basitleştirir
2. **REQ-6.2** WHEN vocabulary adapt edildiğinde, THE System SHALL zor kelimeleri basit synonym'le replace eder
3. **REQ-6.3** WHEN summary generate edildiğinde, THE System SHALL key point'leri extract eder
4. **REQ-6.4** WHEN visual aid eklediğinde, THE System SHALL icon, image ile destekler
5. **REQ-6.5** WHEN definition provide edildiğinde, THE System SHALL hover tooltip ile açıklama gösterir
6. **REQ-6.6** WHEN reading level adjust edildiğinde, THE System SHALL age-appropriate content sağlar

### Requirement 7: Progress Tracking
**User Story:** As a disleksi öğrenci, I want progress tracking, so that gelişimimi görebileyim.
#### Acceptance Criteria
1. **REQ-7.1** WHEN reading time track edildiğinde, THE System SHALL session duration kaydeder
2. **REQ-7.2** WHEN reading speed ölçüldüğünde, THE System SHALL words per minute hesaplar
3. **REQ-7.3** WHEN comprehension test edildiğinde, THE System SHALL quiz score track eder
4. **REQ-7.4** WHEN progress visualize edildiğinde, THE System SHALL chart, graph gösterir
5. **REQ-7.5** WHEN milestone achieve edildiğinde, THE System SHALL encouragement message gösterir
6. **REQ-7.6** WHEN progress report oluşturulduğunda, THE System SHALL weekly summary sağlar

### Requirement 8: Accessibility Settings Persistence
**User Story:** As a disleksi öğrenci, I want settings persistence, so that tercihlerim kaydolsun.
#### Acceptance Criteria
1. **REQ-8.1** WHEN settings change edildiğinde, THE System SHALL automatic save yapar
2. **REQ-8.2** WHEN user login olduğunda, THE System SHALL saved settings load eder
3. **REQ-8.3** WHEN settings export edildiğinde, THE System SHALL JSON format kullanır
4. **REQ-8.4** WHEN settings import edildiğinde, THE System SHALL validation yapar
5. **REQ-8.5** WHEN settings reset edildiğinde, THE System SHALL default values restore eder
6. **REQ-8.6** WHEN settings sync edildiğinde, THE System SHALL cross-device sync destekler

## Bağımlılıklar
- **opendyslexic-font**: Disleksi font
- **web-speech-api**: Text-to-speech
- **react-speech-kit**: TTS component
- **reading-ruler**: Reading aid
- **text-simplifier**: Content simplification

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 2 hafta
**Beklenen User Satisfaction:** >= %85

## Success Metrics
1. **Feature Adoption:** >= %60
2. **Reading Speed Improvement:** >= %30
3. **Comprehension Improvement:** >= %25
4. **User Satisfaction:** >= %85
5. **Settings Persistence:** %100

# Requirements Document - Diskalkuli Desteği

## Introduction

Bu spec, diskalkuli (matematik öğrenme güçlüğü) öğrenciler için erişilebilirlik özelliklerini tanımlar. Visual math aids, step-by-step solutions, interactive tools ile diskalkuli-friendly platform sağlar.

## Glossary

- **Diskalkuli**: Matematik öğrenme güçlüğü
- **Visual Math**: Görsel matematik
- **Manipulatives**: Somut araçlar
- **Number Line**: Sayı doğrusu
- **Step-by-Step**: Adım adım
- **Math Anxiety**: Matematik kaygısı

## Requirements

### Requirement 1: Visual Math Representation
**User Story:** As a diskalkuli öğrenci, I want visual math, so that sayıları görsel anlayayım.
#### Acceptance Criteria
1. **REQ-1.1** WHEN math problem gösterildiğinde, THE System SHALL visual representation sağlar
2. **REQ-1.2** WHEN number display edildiğinde, THE System SHALL dot pattern, tally marks, number line options sağlar
3. **REQ-1.3** WHEN fraction gösterildiğinde, THE System SHALL pie chart, bar model visualization kullanır
4. **REQ-1.4** WHEN geometry problem olduğunda, THE System SHALL interactive shape tool sağlar
5. **REQ-1.5** WHEN graph çizildiğinde, THE System SHALL color-coded, labeled visualization kullanır
6. **REQ-1.6** WHEN visual aid customize edildiğinde, THE System SHALL size, color, style adjust destekler

### Requirement 2: Step-by-Step Solutions
**User Story:** As a diskalkuli öğrenci, I want step-by-step solutions, so that işlem adımlarını anlayayım.
#### Acceptance Criteria
1. **REQ-2.1** WHEN solution gösterildiğinde, THE System SHALL her adımı ayrı gösterir
2. **REQ-2.2** WHEN step explanation verildiğinde, THE System SHALL why this step açıklaması ekler
3. **REQ-2.3** WHEN step navigate edildiğinde, THE System SHALL previous, next, jump to step destekler
4. **REQ-2.4** WHEN step highlight edildiğinde, THE System SHALL current step'i vurgular
5. **REQ-2.5** WHEN step audio sağlandığında, THE System SHALL TTS ile step'leri okur
6. **REQ-2.6** WHEN step practice yapıldığında, THE System SHALL guided practice mode sağlar

### Requirement 3: Interactive Math Tools
**User Story:** As a diskalkuli öğrenci, I want interactive tools, so that somut deneyim yaşayayım.
#### Acceptance Criteria
1. **REQ-3.1** WHEN virtual manipulatives kullanıldığında, THE System SHALL base-10 blocks, counters, fraction bars sağlar
2. **REQ-3.2** WHEN number line tool kullanıldığında, THE System SHALL draggable marker, zoom, label destekler
3. **REQ-3.3** WHEN calculator sağlandığında, THE System SHALL large button, clear display, history kullanır
4. **REQ-3.4** WHEN graph tool kullanıldığında, THE System SHALL interactive plotting, zoom, pan destekler
5. **REQ-3.5** WHEN equation solver kullanıldığında, THE System SHALL step-by-step solution gösterir
6. **REQ-3.6** WHEN tool accessibility sağlandığında, THE System SHALL keyboard navigation, screen reader support ekler

### Requirement 4: Multi-Sensory Learning
**User Story:** As a diskalkuli öğrenci, I want multi-sensory learning, so that farklı duyularla öğreneyim.
#### Acceptance Criteria
1. **REQ-4.1** WHEN audio feedback verildiğinde, THE System SHALL correct/incorrect sound effect çalar
2. **REQ-4.2** WHEN haptic feedback kullanıldığında, THE System SHALL mobile device vibration sağlar
3. **REQ-4.3** WHEN color coding uygulandığında, THE System SHALL operation type'a göre color assign eder
4. **REQ-4.4** WHEN animation kullanıldığında, THE System SHALL concept visualization için animate eder
5. **REQ-4.5** WHEN rhythm-based learning sağlandığında, THE System SHALL counting rhythm, pattern music kullanır
6. **REQ-4.6** WHEN multi-sensory combine edildiğinde, THE System SHALL visual + audio + tactile integrate eder

### Requirement 5: Scaffolded Practice
**User Story:** As a diskalkuli öğrenci, I want scaffolded practice, so that kademeli öğreneyim.
#### Acceptance Criteria
1. **REQ-5.1** WHEN practice başladığında, THE System SHALL easy problem'lerle başlar
2. **REQ-5.2** WHEN difficulty adjust edildiğinde, THE System SHALL adaptive difficulty kullanır
3. **REQ-5.3** WHEN hint sağlandığında, THE System SHALL progressive hint system kullanır
4. **REQ-5.4** WHEN partial credit verildiğinde, THE System SHALL correct step'leri recognize eder
5. **REQ-5.5** WHEN mastery check edildiğinde, THE System SHALL 3 consecutive correct gerektirir
6. **REQ-5.6** WHEN practice feedback verildiğinde, THE System SHALL encouraging, specific feedback sağlar

### Requirement 6: Math Anxiety Reduction
**User Story:** As a diskalkuli öğrenci, I want anxiety reduction, so that rahat hissedeyim.
#### Acceptance Criteria
1. **REQ-6.1** WHEN timed test disable edildiğinde, THE System SHALL untimed mode sağlar
2. **REQ-6.2** WHEN mistake yapıldığında, THE System SHALL non-judgmental feedback verir
3. **REQ-6.3** WHEN progress celebrate edildiğinde, THE System SHALL positive reinforcement kullanır
4. **REQ-6.4** WHEN break reminder verildiğinde, THE System SHALL periodic rest suggestion sağlar
5. **REQ-6.5** WHEN stress level monitor edildiğinde, THE System SHALL difficulty auto-adjust yapar
6. **REQ-6.6** WHEN growth mindset promote edildiğinde, THE System SHALL effort-based praise kullanır

### Requirement 7: Number Sense Development
**User Story:** As a diskalkuli öğrenci, I want number sense, so that sayı kavramını geliştireyim.
#### Acceptance Criteria
1. **REQ-7.1** WHEN number comparison yapıldığında, THE System SHALL visual magnitude representation kullanır
2. **REQ-7.2** WHEN estimation practice edildiğinde, THE System SHALL reasonable range feedback verir
3. **REQ-7.3** WHEN place value öğretildiğinde, THE System SHALL base-10 block visualization kullanır
4. **REQ-7.4** WHEN mental math practice edildiğinde, THE System SHALL strategy suggestion sağlar
5. **REQ-7.5** WHEN number pattern recognize edildiğinde, THE System SHALL visual pattern highlight eder
6. **REQ-7.6** WHEN number fluency build edildiğinde, THE System SHALL spaced repetition kullanır

### Requirement 8: Progress Monitoring
**User Story:** As a diskalkuli öğrenci, I want progress monitoring, so that gelişimimi görebileyim.
#### Acceptance Criteria
1. **REQ-8.1** WHEN skill mastery track edildiğinde, THE System SHALL per-concept progress gösterir
2. **REQ-8.2** WHEN strength/weakness identify edildiğinde, THE System SHALL skill heatmap kullanır
3. **REQ-8.3** WHEN growth visualize edildiğinde, THE System SHALL timeline chart gösterir
4. **REQ-8.4** WHEN goal set edildiğinde, THE System SHALL achievable milestone'lar oluşturur
5. **REQ-8.5** WHEN report generate edildiğinde, THE System SHALL parent/teacher dashboard sağlar
6. **REQ-8.6** WHEN intervention suggest edildiğinde, THE System SHALL targeted practice recommend eder

## Bağımlılıklar
- **mathjs**: Math computation
- **katex**: Math rendering
- **d3.js**: Visualization
- **fabric.js**: Interactive canvas
- **howler.js**: Audio feedback

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 2 hafta
**Beklenen Math Confidence:** >= %40 artış

## Success Metrics
1. **Feature Adoption:** >= %50
2. **Math Confidence Improvement:** >= %40
3. **Problem Solving Accuracy:** >= %30 artış
4. **Math Anxiety Reduction:** >= %35
5. **User Engagement:** >= %75

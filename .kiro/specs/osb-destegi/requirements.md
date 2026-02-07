# Requirements Document - OSB Desteği

## Introduction

Bu spec, OSB (Otizm Spektrum Bozukluğu) öğrenciler için erişilebilirlik özelliklerini tanımlar. Predictable interface, sensory controls, social stories ile OSB-friendly platform sağlar.

## Glossary

- **OSB**: Otizm Spektrum Bozukluğu
- **Predictability**: Öngörülebilirlik
- **Sensory Overload**: Duyusal aşırı yüklenme
- **Social Story**: Sosyal hikaye
- **Visual Schedule**: Görsel program
- **Routine**: Rutin

## Requirements

### Requirement 1: Predictable Interface
**User Story:** As a OSB öğrenci, I want predictable interface, so that rahat hissedeyim.
#### Acceptance Criteria
1. **REQ-1.1** WHEN interface design edildiğinde, THE System SHALL consistent layout kullanır
2. **REQ-1.2** WHEN navigation yapıldığında, THE System SHALL same location'da button'lar bulunur
3. **REQ-1.3** WHEN color scheme kullanıldığında, THE System SHALL consistent color coding uygular
4. **REQ-1.4** WHEN icon kullanıldığında, THE System SHALL familiar, standard icon set kullanır
5. **REQ-1.5** WHEN change yapıldığında, THE System SHALL advance warning verir
6. **REQ-1.6** WHEN interface customize edildiğinde, THE System SHALL saved layout preserve eder

### Requirement 2: Sensory Controls
**User Story:** As a OSB öğrenci, I want sensory controls, so that duyusal aşırı yüklenme önlensin.
#### Acceptance Criteria
1. **REQ-2.1** WHEN animation disable edildiğinde, THE System SHALL tüm motion effect'leri remove eder
2. **REQ-2.2** WHEN sound control sağlandığında, THE System SHALL volume adjust, mute options sunar
3. **REQ-2.3** WHEN visual clutter reduce edildiğinde, THE System SHALL minimal, clean interface kullanır
4. **REQ-2.4** WHEN brightness adjust edildiğinde, THE System SHALL low-light mode destekler
5. **REQ-2.5** WHEN contrast reduce edildiğinde, THE System SHALL soft color palette kullanır
6. **REQ-2.6** WHEN sensory profile save edildiğinde, THE System SHALL preference persist eder

### Requirement 3: Visual Schedule
**User Story:** As a OSB öğrenci, I want visual schedule, so that ne olacağını bileyim.
#### Acceptance Criteria
1. **REQ-3.1** WHEN daily schedule gösterildiğinde, THE System SHALL icon-based timeline kullanır
2. **REQ-3.2** WHEN current activity highlight edildiğinde, THE System SHALL "now" indicator gösterir
3. **REQ-3.3** WHEN next activity preview edildiğinde, THE System SHALL upcoming task gösterir
4. **REQ-3.4** WHEN schedule change olduğunda, THE System SHALL advance notification verir
5. **REQ-3.5** WHEN task complete edildiğinde, THE System SHALL visual checkmark ekler
6. **REQ-3.6** WHEN schedule customize edildiğinde, THE System SHALL personal routine support eder

### Requirement 4: Clear Instructions
**User Story:** As a OSB öğrenci, I want clear instructions, so that ne yapacağımı anlayayım.
#### Acceptance Criteria
1. **REQ-4.1** WHEN instruction verildiğinde, THE System SHALL simple, direct language kullanır
2. **REQ-4.2** WHEN step-by-step guide sağlandığında, THE System SHALL numbered list kullanır
3. **REQ-4.3** WHEN visual support eklediğinde, THE System SHALL icon, image ile destekler
4. **REQ-4.4** WHEN example gösterildiğinde, THE System SHALL concrete, specific example kullanır
5. **REQ-4.5** WHEN ambiguity avoid edildiğinde, THE System SHALL literal language kullanır
6. **REQ-4.6** WHEN instruction repeat edildiğinde, THE System SHALL consistent wording kullanır

### Requirement 5: Social Stories
**User Story:** As a OSB öğrenci, I want social stories, so that sosyal durumları anlayayım.
#### Acceptance Criteria
1. **REQ-5.1** WHEN social situation explain edildiğinde, THE System SHALL story format kullanır
2. **REQ-5.2** WHEN story present edildiğinde, THE System SHALL first-person perspective kullanır
3. **REQ-5.3** WHEN visual support eklediğinde, THE System SHALL relevant image/icon kullanır
4. **REQ-5.4** WHEN expected behavior describe edildiğinde, THE System SHALL clear, specific description verir
5. **REQ-5.5** WHEN story customize edildiğinde, THE System SHALL personalized scenario destekler
6. **REQ-5.6** WHEN story library sağlandığında, THE System SHALL common situation'lar içerir

### Requirement 6: Routine Support
**User Story:** As a OSB öğrenci, I want routine support, so that günlük rutinime uyayım.
#### Acceptance Criteria
1. **REQ-6.1** WHEN routine oluşturulduğunda, THE System SHALL customizable sequence sağlar
2. **REQ-6.2** WHEN routine reminder verildiğinde, THE System SHALL gentle, predictable notification kullanır
3. **REQ-6.3** WHEN routine track edildiğinde, THE System SHALL completion checklist gösterir
4. **REQ-6.4** WHEN routine break olduğunda, THE System SHALL advance warning + explanation verir
5. **REQ-6.5** WHEN routine reinforce edildiğinde, THE System SHALL positive feedback sağlar
6. **REQ-6.6** WHEN routine analytics gösterildiğinde, THE System SHALL consistency pattern track eder

### Requirement 7: Communication Support
**User Story:** As a OSB öğrenci, I want communication support, so that iletişim kurayım.
#### Acceptance Criteria
1. **REQ-7.1** WHEN AAC (Augmentative Communication) kullanıldığında, THE System SHALL symbol-based communication destekler
2. **REQ-7.2** WHEN choice board sağlandığında, THE System SHALL visual choice options gösterir
3. **REQ-7.3** WHEN emotion expression desteklendiğinde, THE System SHALL emotion icon/scale kullanır
4. **REQ-7.4** WHEN request system kullanıldığında, THE System SHALL "I need" template sağlar
5. **REQ-7.5** WHEN communication log tutulduğunda, THE System SHALL interaction history kaydeder
6. **REQ-7.6** WHEN communication preference save edildiğinde, THE System SHALL preferred method persist eder

### Requirement 8: Stress Management
**User Story:** As a OSB öğrenci, I want stress management, so that sakinleşeyim.
#### Acceptance Criteria
1. **REQ-8.1** WHEN stress level yüksek olduğunda, THE System SHALL calming activity önerir
2. **REQ-8.2** WHEN break space sağlandığında, THE System SHALL quiet, minimal stimulation area sunar
3. **REQ-8.3** WHEN breathing exercise verildiğinde, THE System SHALL guided breathing animation kullanır
4. **REQ-8.4** WHEN sensory tool sağlandığında, THE System SHALL virtual fidget, stress ball ekler
5. **REQ-8.5** WHEN coping strategy teach edildiğinde, THE System SHALL visual coping card kullanır
6. **REQ-8.6** WHEN stress pattern track edildiğinde, THE System SHALL trigger identification yapar

## Bağımlılıklar
- **react-icons**: Icon library
- **framer-motion**: Animation (optional)
- **react-calendar**: Schedule component
- **howler.js**: Audio control
- **fabric.js**: Visual tools

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 2 hafta
**Beklenen Comfort Level:** >= %70 artış

## Success Metrics
1. **Feature Adoption:** >= %55
2. **Routine Adherence:** >= %80
3. **Stress Reduction:** >= %45
4. **Communication Effectiveness:** >= %60 artış
5. **User Comfort:** >= %70 artış

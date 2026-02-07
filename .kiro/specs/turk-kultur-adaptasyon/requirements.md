# Requirements Document - Türk Kültür Adaptasyon Motoru

## Introduction

Bu spec, AI agent'ın Türk kültürüne uygun davranış ve içerik üretme sistemini tanımlar. Cultural context, idiom translation, formality detection ile kültürel uyum sağlar.

## Glossary

- **Cultural Context**: Kültürel bağlam
- **Idiom**: Deyim/atasözü
- **Formality**: Resmiyet seviyesi
- **Honorific**: Saygı ifadesi
- **Localization**: Yerelleştirme
- **Cultural Sensitivity**: Kültürel duyarlılık

## Requirements

### Requirement 1: Formality Detection
**User Story:** As a content generator, I want formality detection, so that uygun üslup kullanayım.
#### Acceptance Criteria
1. **REQ-1.1** WHEN text analiz edildiğinde, THE System SHALL formality level (1-5) tespit eder
2. **REQ-1.2** WHEN informal context tespit edildiğinde, THE System SHALL "sen" form kullanır
3. **REQ-1.3** WHEN formal context tespit edildiğinde, THE System SHALL "siz" form kullanır
4. **REQ-1.4** WHEN professional setting olduğunda, THE System SHALL business Turkish register uygular
5. **REQ-1.5** WHEN educational content üretildiğinde, THE System SHALL pedagogical formality kullanır
6. **REQ-1.6** WHEN formality mismatch tespit edildiğinde, THE System SHALL warning verir

### Requirement 2: Idiom and Proverb Integration
**User Story:** As a Turkish teacher, I want idiom integration, so that doğal Türkçe kullanayım.
#### Acceptance Criteria
1. **REQ-2.1** WHEN appropriate context bulunduğunda, THE System SHALL relevant deyim/atasözü önerir
2. **REQ-2.2** WHEN idiom database query edildiğinde, THE System SHALL >= 1000 Turkish idiom içerir
3. **REQ-2.3** WHEN idiom meaning explain edildiğinde, THE System SHALL literal vs figurative translation sağlar
4. **REQ-2.4** WHEN idiom usage validate edildiğinde, THE System SHALL context appropriateness check yapar
5. **REQ-2.5** WHEN modern equivalent önerildiğinde, THE System SHALL archaic idiom'ları update eder
6. **REQ-2.6** WHEN idiom frequency ölçüldüğünde, THE System SHALL overuse prevention (max 1 per paragraph) uygular

### Requirement 3: Honorific System
**User Story:** As a social interaction agent, I want honorific system, so that saygılı hitap edeyim.
#### Acceptance Criteria
1. **REQ-3.1** WHEN elder person detect edildiğinde, THE System SHALL "Sayın", "Hocam" gibi honorific kullanır
2. **REQ-3.2** WHEN professional title olduğunda, THE System SHALL "Dr.", "Prof.", "Müh." prefix ekler
3. **REQ-3.3** WHEN family relation tespit edildiğinde, THE System SHALL "Abla", "Ağabey", "Teyze" gibi term kullanır
4. **REQ-3.4** WHEN religious context olduğunda, THE System SHALL appropriate greeting ("Selamünaleyküm") kullanır
5. **REQ-3.5** WHEN gender-neutral option gerektiğinde, THE System SHALL inclusive language tercih eder
6. **REQ-3.6** WHEN honorific override edildiğinde, THE System SHALL user preference'ı respect eder

### Requirement 4: Cultural Reference Detection
**User Story:** As a content moderator, I want cultural reference detection, so that uygunsuz içerik önlensin.
#### Acceptance Criteria
1. **REQ-4.1** WHEN sensitive topic tespit edildiğinde, THE System SHALL religion, politics, ethnicity flag eder
2. **REQ-4.2** WHEN taboo subject bulunduğunda, THE System SHALL alternative phrasing önerir
3. **REQ-4.3** WHEN historical reference yapıldığında, THE System SHALL Turkish history context validate eder
4. **REQ-4.4** WHEN regional difference olduğunda, THE System SHALL dialect/accent awareness gösterir
5. **REQ-4.5** WHEN cultural stereotype tespit edildiğinde, THE System SHALL bias warning verir
6. **REQ-4.6** WHEN cultural sensitivity score hesaplandığında, THE System SHALL >= 0.9 threshold gerektirir

### Requirement 5: Holiday and Calendar Awareness
**User Story:** As a scheduling agent, I want calendar awareness, so that Türk tatillerini biliyim.
#### Acceptance Criteria
1. **REQ-5.1** WHEN date check edildiğinde, THE System SHALL Turkish national holidays recognize eder
2. **REQ-5.2** WHEN religious holiday tespit edildiğinde, THE System SHALL Ramazan, Kurban Bayramı dates hesaplar
3. **REQ-5.3** WHEN greeting generate edildiğinde, THE System SHALL holiday-appropriate message kullanır
4. **REQ-5.4** WHEN business day calculate edildiğinde, THE System SHALL holiday'leri exclude eder
5. **REQ-5.5** WHEN regional celebration olduğunda, THE System SHALL local festival'leri recognize eder
6. **REQ-5.6** WHEN calendar sync yapıldığında, THE System SHALL Hijri + Gregorian calendar destekler

### Requirement 6: Food and Cuisine Context
**User Story:** As a recommendation agent, I want cuisine context, so that Türk mutfağını anlayayım.
#### Acceptance Criteria
1. **REQ-6.1** WHEN food mention edildiğinde, THE System SHALL Turkish cuisine knowledge kullanır
2. **REQ-6.2** WHEN dietary restriction tespit edildiğinde, THE System SHALL helal/haram awareness gösterir
3. **REQ-6.3** WHEN regional dish önerildiğinde, THE System SHALL geographic origin belirtir
4. **REQ-6.4** WHEN recipe translate edildiğinde, THE System SHALL Turkish ingredient name kullanır
5. **REQ-6.5** WHEN meal time reference yapıldığında, THE System SHALL Turkish eating schedule (kahvaltı, öğle, akşam) kullanır
6. **REQ-6.6** WHEN food metaphor kullanıldığında, THE System SHALL culturally appropriate analogy seçer

### Requirement 7: Education System Context
**User Story:** As a education agent, I want education context, so that Türk eğitim sistemini anlayayım.
#### Acceptance Criteria
1. **REQ-7.1** WHEN exam mention edildiğinde, THE System SHALL LGS, YKS, KPSS gibi Turkish exam'ları recognize eder
2. **REQ-7.2** WHEN grade level tespit edildiğinde, THE System SHALL Turkish education system (ilkokul, ortaokul, lise) kullanır
3. **REQ-7.3** WHEN curriculum reference yapıldığında, THE System SHALL MEB müfredatını dikkate alır
4. **REQ-7.4** WHEN university mention edildiğinde, THE System SHALL Turkish university ranking awareness gösterir
5. **REQ-7.5** WHEN academic term kullanıldığında, THE System SHALL Turkish academic calendar (güz/bahar dönemi) bilir
6. **REQ-7.6** WHEN education advice verildiğinde, THE System SHALL Turkish context-appropriate guidance sağlar

### Requirement 8: Localization Quality Assurance
**User Story:** As a QA engineer, I want localization QA, so that kültürel uyum validate edilsin.
#### Acceptance Criteria
1. **REQ-8.1** WHEN content generate edildiğinde, THE System SHALL cultural appropriateness score hesaplar
2. **REQ-8.2** WHEN translation validate edildiğinde, THE System SHALL literal vs cultural translation check yapar
3. **REQ-8.3** WHEN tone consistency kontrol edildiğinde, THE System SHALL formality level consistency sağlar
4. **REQ-8.4** WHEN cultural reference verify edildiğinde, THE System SHALL Turkish native speaker review simüle eder
5. **REQ-8.5** WHEN A/B test yapıldığında, THE System SHALL Turkish user preference track eder
6. **REQ-8.6** WHEN quality metric raporlandığında, THE System SHALL cultural fit score >= 0.85 hedefler

## Bağımlılıklar
- **zemberek-nlp**: Turkish NLP
- **turkish-holidays**: Holiday calendar
- **cultural-db**: Cultural knowledge base
- **sentiment-analysis**: Tone detection
- **translation-memory**: Localization cache

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 2 hafta
**Beklenen Cultural Fit:** >= %85

## Success Metrics
1. **Formality Accuracy:** >= %90
2. **Cultural Appropriateness:** >= %85
3. **Idiom Usage Quality:** >= %80
4. **User Satisfaction:** >= %85
5. **Cultural Sensitivity:** >= %95

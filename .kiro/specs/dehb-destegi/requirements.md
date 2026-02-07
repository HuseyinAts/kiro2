# Requirements Document - DEHB Desteği

## Introduction

Bu spec, DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) öğrenciler için erişilebilirlik özelliklerini tanımlar. Focus tools, break reminders, gamification ile DEHB-friendly platform sağlar.

## Glossary

- **DEHB**: Dikkat Eksikliği Hiperaktivite Bozukluğu
- **Focus Mode**: Odaklanma modu
- **Pomodoro**: Zaman yönetimi tekniği
- **Gamification**: Oyunlaştırma
- **Break Reminder**: Mola hatırlatıcısı
- **Distraction Blocker**: Dikkat dağıtıcı engelleyici

## Requirements

### Requirement 1: Focus Mode
**User Story:** As a DEHB öğrenci, I want focus mode, so that dikkatim dağılmasın.
#### Acceptance Criteria
1. **REQ-1.1** WHEN focus mode enable edildiğinde, THE System SHALL distraction-free interface gösterir
2. **REQ-1.2** WHEN notification disable edildiğinde, THE System SHALL tüm alert'leri suspend eder
3. **REQ-1.3** WHEN minimal UI kullanıldığında, THE System SHALL sadece essential element'leri gösterir
4. **REQ-1.4** WHEN background noise sağlandığında, THE System SHALL white noise, ambient sound options sunar
5. **REQ-1.5** WHEN focus timer set edildiğinde, THE System SHALL countdown display gösterir
6. **REQ-1.6** WHEN focus session complete olduğunda, THE System SHALL completion celebration gösterir

### Requirement 2: Pomodoro Timer
**User Story:** As a DEHB öğrenci, I want Pomodoro timer, so that zaman yönetimi yapayım.
#### Acceptance Criteria
1. **REQ-2.1** WHEN Pomodoro başladığında, THE System SHALL 25 min work + 5 min break cycle kullanır
2. **REQ-2.2** WHEN timer customize edildiğinde, THE System SHALL work/break duration adjust destekler
3. **REQ-2.3** WHEN break reminder verildiğinde, THE System SHALL gentle notification + sound kullanır
4. **REQ-2.4** WHEN long break schedule edildiğinde, THE System SHALL 4 cycle sonrası 15-30 min break sağlar
5. **REQ-2.5** WHEN timer pause edildiğinde, THE System SHALL resume option sağlar
6. **REQ-2.6** WHEN Pomodoro complete track edildiğinde, THE System SHALL daily/weekly count gösterir

### Requirement 3: Task Chunking
**User Story:** As a DEHB öğrenci, I want task chunking, so that büyük görevleri parçalayayım.
#### Acceptance Criteria
1. **REQ-3.1** WHEN large task verildiğinde, THE System SHALL automatic sub-task breakdown önerir
2. **REQ-3.2** WHEN sub-task oluşturulduğunda, THE System SHALL 5-15 min duration hedefler
3. **REQ-3.3** WHEN task progress gösterildiğinde, THE System SHALL visual progress bar kullanır
4. **REQ-3.4** WHEN task complete edildiğinde, THE System SHALL immediate positive feedback verir
5. **REQ-3.5** WHEN task sequence organize edildiğinde, THE System SHALL priority-based ordering kullanır
6. **REQ-3.6** WHEN task overwhelm tespit edildiğinde, THE System SHALL simplification suggest eder

### Requirement 4: Gamification
**User Story:** As a DEHB öğrenci, I want gamification, so that motivasyonum artsın.
#### Acceptance Criteria
1. **REQ-4.1** WHEN point system kullanıldığında, THE System SHALL task completion için point verir
2. **REQ-4.2** WHEN badge earn edildiğinde, THE System SHALL achievement unlock gösterir
3. **REQ-4.3** WHEN streak track edildiğinde, THE System SHALL consecutive day count gösterir
4. **REQ-4.4** WHEN leaderboard gösterildiğinde, THE System SHALL optional peer comparison sağlar
5. **REQ-4.5** WHEN level system kullanıldığında, THE System SHALL progressive difficulty unlock eder
6. **REQ-4.6** WHEN reward customize edildiğinde, THE System SHALL personalized incentive destekler

### Requirement 5: Attention Monitoring
**User Story:** As a DEHB öğrenci, I want attention monitoring, so that dikkat durumum track edilsin.
#### Acceptance Criteria
1. **REQ-5.1** WHEN activity track edildiğinde, THE System SHALL engagement pattern analiz eder
2. **REQ-5.2** WHEN attention drift tespit edildiğinde, THE System SHALL gentle redirect sağlar
3. **REQ-5.3** WHEN optimal focus time identify edildiğinde, THE System SHALL personalized schedule önerir
4. **REQ-5.4** WHEN fatigue detect edildiğinde, THE System SHALL break suggestion verir
5. **REQ-5.5** WHEN attention span ölçüldüğünde, THE System SHALL average focus duration hesaplar
6. **REQ-5.6** WHEN attention report oluşturulduğunda, THE System SHALL pattern visualization sağlar

### Requirement 6: Hyperactivity Accommodation
**User Story:** As a DEHB öğrenci, I want hyperactivity accommodation, so that enerji yönetimi yapayım.
#### Acceptance Criteria
1. **REQ-6.1** WHEN movement break suggest edildiğinde, THE System SHALL physical activity reminder verir
2. **REQ-6.2** WHEN fidget tool sağlandığında, THE System SHALL interactive widget (spinner, clicker) ekler
3. **REQ-6.3** WHEN standing option sunulduğunda, THE System SHALL sit/stand reminder verir
4. **REQ-6.4** WHEN kinesthetic learning desteklendiğinde, THE System SHALL interactive, hands-on activity sağlar
5. **REQ-6.5** WHEN energy level track edildiğinde, THE System SHALL high/low energy task match yapar
6. **REQ-6.6** WHEN movement integrate edildiğinde, THE System SHALL gesture-based interaction destekler

### Requirement 7: Impulsivity Management
**User Story:** As a DEHB öğrenci, I want impulsivity management, so that düşünerek karar vereyim.
#### Acceptance Criteria
1. **REQ-7.1** WHEN quick decision gerektiğinde, THE System SHALL "pause and think" prompt gösterir
2. **REQ-7.2** WHEN answer submit edildiğinde, THE System SHALL review reminder verir
3. **REQ-7.3** WHEN undo option sağlandığında, THE System SHALL easy mistake correction destekler
4. **REQ-7.4** WHEN reflection prompt verildiğinde, THE System SHALL "Are you sure?" confirmation kullanır
5. **REQ-7.5** WHEN strategy teach edildiğinde, THE System SHALL stop-think-act framework öğretir
6. **REQ-7.6** WHEN impulsive pattern tespit edildiğinde, THE System SHALL awareness feedback verir

### Requirement 8: Personalized Learning Pace
**User Story:** As a DEHB öğrenci, I want personalized pace, so that kendi hızımda öğreneyim.
#### Acceptance Criteria
1. **REQ-8.1** WHEN learning pace adjust edildiğinde, THE System SHALL adaptive speed kullanır
2. **REQ-8.2** WHEN content chunk edildiğinde, THE System SHALL bite-sized lesson'lar sağlar
3. **REQ-8.3** WHEN review frequency set edildiğinde, THE System SHALL spaced repetition optimize eder
4. **REQ-8.4** WHEN skip option sağlandığında, THE System SHALL known content bypass destekler
5. **REQ-8.5** WHEN pace feedback verildiğinde, THE System SHALL too fast/slow indicator gösterir
6. **REQ-8.6** WHEN pace analytics gösterildiğinde, THE System SHALL optimal learning time identify eder

## Bağımlılıklar
- **react-timer-hook**: Timer component
- **react-confetti**: Celebration effect
- **howler.js**: Audio feedback
- **framer-motion**: Animation
- **chart.js**: Progress visualization

## Kabul Kriterleri Özeti
**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P1 (Yüksek)
**Tahmini Süre:** 2 hafta
**Beklenen Focus Improvement:** >= %50

## Success Metrics
1. **Feature Adoption:** >= %65
2. **Focus Duration Improvement:** >= %50
3. **Task Completion Rate:** >= %40 artış
4. **User Engagement:** >= %80
5. **Satisfaction Score:** >= %85

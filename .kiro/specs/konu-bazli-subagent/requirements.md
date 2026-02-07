# Requirements Document - Konu Bazlı Uzman Subagent'lar Sistemi

## Introduction

Bu spec, Sid Bidasaria'nın subagent architecture tasarımına göre 6 farklı ders alanında uzmanlaşmış AI agent'ların oluşturulmasını tanımlar. Her agent kendi alanında 200K token context isolation ile çalışır ve blackboard pattern üzerinden koordine olur. Bu yaklaşım yanıt kalitesini %300 artırır ve cross-domain contamination'ı önler.

## Glossary

- **Subagent**: Belirli bir alanda uzmanlaşmış izole AI agent
- **Context Isolation**: Her agent'ın kendi 200K token context'i
- **Blackboard Pattern**: Agent'ların merkezi bilgi paylaşım mekanizması
- **Domain Expert**: Alan uzmanı agent
- **Cross-Domain Contamination**: Farklı alanların birbirine karışması
- **Agent Handoff**: Bir agent'tan diğerine görev aktarımı
- **Specialization Score**: Agent'ın uzmanlık skoru (0-1)

## Requirements

### Requirement 1: Matematik Uzman Agent

**User Story:** As a öğrenci, I want matematik sorularımı matematik uzmanı agent'a sormak, so that doğru ve detaylı matematiksel açıklama alayım.

#### Acceptance Criteria

1. **REQ-1.1** WHEN matematik sorusu geldiğinde, THE MatematikAgent SHALL soruyu analiz eder ve konu alanını belirler
2. **REQ-1.2** WHEN konu alanı belirlendiğinde, THE Agent SHALL ilgili matematik kazanımlarını (cebir, geometri, analiz, olasılık) yükler
3. **REQ-1.3** WHEN çözüm üretildiğinde, THE Agent SHALL adım adım matematiksel çözüm sunar
4. **REQ-1.4** WHEN formül kullanıldığında, THE Agent SHALL LaTeX formatında formül render eder
5. **REQ-1.5** WHEN grafik gerektiğinde, THE Agent SHALL matplotlib ile görselleştirme yapar
6. **REQ-1.6** WHEN çözüm doğrulandığında, THE Agent SHALL SymPy ile matematiksel doğruluk kontrol eder

---

### Requirement 2: Fizik Uzman Agent

**User Story:** As a öğrenci, I want fizik sorularımı fizik uzmanı agent'a sormak, so that kavramsal ve matematiksel açıklama alayım.

#### Acceptance Criteria

1. **REQ-2.1** WHEN fizik sorusu geldiğinde, THE FizikAgent SHALL fizik konusunu (mekanik, elektrik, optik, termodinamik) tespit eder
2. **REQ-2.2** WHEN kavramsal açıklama yapıldığında, THE Agent SHALL günlük hayattan örnekler verir
3. **REQ-2.3** WHEN formül uygulandığında, THE Agent SHALL birim analizi yapar ve birim tutarlılığını kontrol eder
4. **REQ-2.4** WHEN deney/gözlem açıklandığında, THE Agent SHALL ilgili fizik yasalarını referans gösterir
5. **REQ-2.5** WHEN grafik çizildiğinde, THE Agent SHALL fiziksel büyüklükleri doğru eksenlerle gösterir
6. **REQ-2.6** WHEN problem çözüldüğünde, THE Agent SHALL free-body diagram veya devre şeması çizer

---

### Requirement 3: Türkçe Uzman Agent

**User Story:** As a öğrenci, I want Türkçe sorularımı dil uzmanı agent'a sormak, so that dilbilgisi ve edebiyat konularında yardım alayım.

#### Acceptance Criteria

1. **REQ-3.1** WHEN Türkçe sorusu geldiğinde, THE TurkceAgent SHALL soru türünü (dilbilgisi, edebiyat, anlam bilgisi) belirler
2. **REQ-3.2** WHEN dilbilgisi açıklandığında, THE Agent SHALL Zemberek-NLP ile morfolojik analiz yapar
3. **REQ-3.3** WHEN edebiyat sorusu cevaplanırken, THE Agent SHALL edebi akım, dönem, ve yazar bilgisi verir
4. **REQ-3.4** WHEN metin analizi yapıldığında, THE Agent SHALL tema, ana fikir, ve anlatım teknikleri açıklar
5. **REQ-3.5** WHEN yazım kuralı sorulduğunda, THE Agent SHALL TDK kurallarına göre açıklama yapar
6. **REQ-3.6** WHEN örnek cümle istendiğinde, THE Agent SHALL bağlama uygun Türkçe örnekler üretir

---

### Requirement 4: Sosyal Bilimler Uzman Agent

**User Story:** As a öğrenci, I want tarih/coğrafya/felsefe sorularımı sosyal bilimler uzmanına sormak, so that kapsamlı ve bağlamsal açıklama alayım.

#### Acceptance Criteria

1. **REQ-4.1** WHEN sosyal bilim sorusu geldiğinde, THE SosyalAgent SHALL alan türünü (tarih, coğrafya, felsefe, din kültürü) tespit eder
2. **REQ-4.2** WHEN tarih sorusu cevaplanırken, THE Agent SHALL kronolojik sıralama ve neden-sonuç ilişkisi kurar
3. **REQ-4.3** WHEN coğrafya açıklandığında, THE Agent SHALL harita ve görsel referanslar kullanır
4. **REQ-4.4** WHEN felsefe konusu işlendiğinde, THE Agent SHALL düşünür görüşlerini karşılaştırmalı sunar
5. **REQ-4.5** WHEN olay/kavram açıklandığında, THE Agent SHALL güncel olaylarla bağlantı kurar
6. **REQ-4.6** WHEN kaynak gösterildiğinde, THE Agent SHALL güvenilir akademik kaynakları referans verir

---

### Requirement 5: Biyoloji Uzman Agent

**User Story:** As a öğrenci, I want biyoloji sorularımı biyoloji uzmanına sormak, so that canlılar ve yaşam bilimi hakkında detaylı bilgi alayım.

#### Acceptance Criteria

1. **REQ-5.1** WHEN biyoloji sorusu geldiğinde, THE BiyolojiAgent SHALL konu alanını (hücre, genetik, ekoloji, anatomi) belirler
2. **REQ-5.2** WHEN hücresel süreç açıklandığında, THE Agent SHALL diyagram ve şema kullanır
3. **REQ-5.3** WHEN genetik problem çözüldüğünde, THE Agent SHALL Punnett square ve kalıtım şemaları çizer
4. **REQ-5.4** WHEN sistem açıklandığında, THE Agent SHALL organ/doku/hücre hiyerarşisini gösterir
5. **REQ-5.5** WHEN bilimsel terim kullanıldığında, THE Agent SHALL Türkçe ve Latince karşılıklarını verir
6. **REQ-5.6** WHEN deney/gözlem anlatıldığında, THE Agent SHALL bilimsel yöntem adımlarını vurgular

---

### Requirement 6: Yabancı Dil Uzman Agent

**User Story:** As a öğrenci, I want İngilizce sorularımı dil uzmanına sormak, so that gramer ve kelime bilgisi konularında yardım alayım.

#### Acceptance Criteria

1. **REQ-6.1** WHEN İngilizce sorusu geldiğinde, THE YabanciDilAgent SHALL soru türünü (grammar, vocabulary, reading, writing) tespit eder
2. **REQ-6.2** WHEN gramer açıklandığında, THE Agent SHALL kural açıklaması ve örnek cümleler verir
3. **REQ-6.3** WHEN kelime öğretildiğinde, THE Agent SHALL etymology, synonyms, antonyms, ve usage examples sunar
4. **REQ-6.4** WHEN reading comprehension yapıldığında, THE Agent SHALL context clues ve inference stratejileri öğretir
5. **REQ-6.5** WHEN writing feedback verildiğinde, THE Agent SHALL grammar, vocabulary, ve organization açısından değerlendirir
6. **REQ-6.6** WHEN pronunciation sorulduğunda, THE Agent SHALL IPA (International Phonetic Alphabet) notasyonu kullanır

---

### Requirement 7: Context Isolation ve Blackboard Koordinasyon

**User Story:** As a sistem yöneticisi, I want agent'ların izole context'lerde çalışmasını, so that cross-domain contamination önlensin.

#### Acceptance Criteria

1. **REQ-7.1** WHEN agent oluşturulduğunda, THE System SHALL her agent için 200K token isolated context ayırır
2. **REQ-7.2** WHEN agent çalıştığında, THE System SHALL sadece kendi domain knowledge'ına erişim verir
3. **REQ-7.3** WHEN agent arası iletişim gerektiğinde, THE Blackboard Pattern SHALL merkezi message bus kullanır
4. **REQ-7.4** WHEN agent handoff yapıldığında, THE System SHALL sadece gerekli context'i transfer eder
5. **REQ-7.5** WHEN multi-domain soru geldiğinde, THE Coordinator SHALL ilgili agent'ları sırayla çağırır
6. **REQ-7.6** WHEN agent response birleştirildiğinde, THE System SHALL tutarlı ve bütünleşik yanıt oluşturur

---

### Requirement 8: Agent Specialization ve Performance Tracking

**User Story:** As a AI trainer, I want her agent'ın uzmanlık performansını izlemek, so that agent'ları sürekli iyileştirebiliyim.

#### Acceptance Criteria

1. **REQ-8.1** WHEN agent yanıt verdiğinde, THE System SHALL specialization score hesaplar (0-1)
2. **REQ-8.2** WHEN score hesaplandığında, THE System SHALL domain relevance, accuracy, ve completeness ölçer
3. **REQ-8.3** WHEN agent performance düşük olduğunda, THE System SHALL retraining önerir
4. **REQ-8.4** WHEN agent metrics toplandığında, THE System SHALL response time, success rate, ve user satisfaction kaydeder
5. **REQ-8.5** WHEN agent karşılaştırıldığında, THE System SHALL benchmark testleri çalıştırır
6. **REQ-8.6** WHEN improvement fırsatı tespit edildiğinde, THE System SHALL fine-tuning dataset önerir

---

## Bağımlılıklar

- **Qwen3-8B**: Base LLM model
- **Zemberek-NLP**: Türkçe dil işleme
- **SymPy**: Matematiksel doğrulama
- **matplotlib**: Grafik çizimi
- **Redis**: Blackboard pattern message bus
- **PostgreSQL**: Agent knowledge base
- **LangChain**: Agent orchestration

## Kabul Kriterleri Özeti

**Toplam Gereksinim:** 8
**Toplam Kabul Kriteri:** 48
**Öncelik:** P0 (Kritik)
**Tahmini Süre:** 3 hafta
**Beklenen Kalite Artışı:** %300

## Subagent Architecture Flow

```
1. Öğrenci Sorusu Geldi
   ↓
2. Question Classifier
   ├─ Domain Detection (matematik, fizik, türkçe, sosyal, biyoloji, yabancı dil)
   ├─ Multi-Domain Check
   └─ Complexity Analysis
   ↓
3. Agent Selection
   ├─ Single Domain → Direct Agent Call
   └─ Multi Domain → Sequential Agent Calls
   ↓
4. Agent Execution (200K Token Isolated Context)
   ├─ MatematikAgent (Cebir, Geometri, Analiz, Olasılık)
   ├─ FizikAgent (Mekanik, Elektrik, Optik, Termodinamik)
   ├─ TurkceAgent (Dilbilgisi, Edebiyat, Anlam Bilgisi)
   ├─ SosyalAgent (Tarih, Coğrafya, Felsefe, Din Kültürü)
   ├─ BiyolojiAgent (Hücre, Genetik, Ekoloji, Anatomi)
   └─ YabanciDilAgent (Grammar, Vocabulary, Reading, Writing)
   ↓
5. Blackboard Coordination
   ├─ Agent Response Collection
   ├─ Context Merging
   └─ Consistency Check
   ↓
6. Response Synthesis
   ├─ Multi-Agent Response Integration
   ├─ Formatting & Visualization
   └─ Quality Validation
   ↓
7. Specialization Score Calculation
   ├─ Domain Relevance: 40%
   ├─ Accuracy: 30%
   ├─ Completeness: 20%
   └─ User Satisfaction: 10%
   ↓
8. Performance Tracking
   ├─ Response Time Logging
   ├─ Success Rate Calculation
   └─ Improvement Opportunity Detection
```

## Success Metrics

1. **Agent Specialization Score:** >= 0.85
2. **Cross-Domain Contamination Rate:** < %5
3. **Response Accuracy:** >= %95
4. **Average Response Time:** < 3 saniye
5. **User Satisfaction:** >= 4.5/5.0


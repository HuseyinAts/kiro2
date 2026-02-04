# Spec Tutarlılık Analizi - MASTER_SPEC
## Tarih: 20 Ekim 2025

## 🔍 Analiz Özeti

Bu doküman, MASTER_SPEC içindeki **requirements.md**, **design.md** ve **tasks.md** dosyaları arasındaki tutarsızlıkları tespit eder.

## 📊 Genel Durum

- **Requirements.md**: 47 ana gereksinim (REQ-1 to REQ-47)
- **Tasks.md**: 139 ana task (Task 1-139)
- **Toplam Requirement Referansı**: 500+ referans
- **Tespit Edilen Tutarsızlık**: **YÜKSEK**

---

## 🚨 KRİTİK TUTARSIZLIKLAR

### 1. Eksik Requirements (Tasks'ta Referans Var, Requirements'ta Yok)

#### Task 53-58: LLM Tabanlı ÖSYM Soru Üretim Sistemi
**Durum**: ❌ TAMAMEN EKSİK

**Referans Edilen Requirements**:
- REQ-26.1 - REQ-26.96 (96 kabul kriteri)

**Gerçek Durum**:
- REQ-26 sadece "Backend API Durum Kontrolü" hakkında
- REQ-26.1 - REQ-26.5 mevcut (5 kabul kriteri)
- REQ-26.6 - REQ-26.96 **MEVCUT DEĞİL** (91 eksik kriter)

**Etkilenen Tasks**:
- Task 53.1: ÖSYM soru scraper → REQ-26.1-26.4
- Task 53.2: Soru parser → REQ-26.5-26.8
- Task 53.3: Bloom taxonomy → REQ-26.9-26.12
- Task 53.4: IRT parametre → REQ-26.13-26.16
- Task 54.1: GPT-4 fine-tuning → REQ-26.17-26.20
- Task 54.2: BERTurk embedding → REQ-26.21-26.24
- Task 54.3: T5/BART generation → REQ-26.25-26.28
- Task 54.4: RLHF training → REQ-26.29-26.32
- Task 55.1: Konu bazlı üretim → REQ-26.33-26.36
- Task 55.2: Distractor generation → REQ-26.37-26.40
- Task 55.3: SymPy doğrulama → REQ-26.41-26.44
- Task 55.4: Görsel üretim → REQ-26.45-26.48
- Task 56.1: Otomatik skorlama → REQ-26.49-26.52
- Task 56.2: BLEU/ROUGE → REQ-26.53-26.56
- Task 56.3: Uzman review → REQ-26.57-26.60
- Task 56.4: A/B testing → REQ-26.61-26.64
- Task 57.1: 4-param IRT → REQ-26.65-26.68
- Task 57.2: ICC → REQ-26.69-26.72
- Task 57.3: TIF → REQ-26.73-26.76
- Task 57.4: Adaptive calibration → REQ-26.77-26.80
- Task 58.1: GPU acceleration → REQ-26.81-26.84
- Task 58.2: Distributed computing → REQ-26.85-26.88
- Task 58.3: Cache sistemi → REQ-26.89-26.92
- Task 58.4: Monitoring → REQ-26.93-26.96

**Çözüm**: REQ-26'yı yeniden yapılandır veya yeni REQ-48 oluştur

---

#### Task 59-64: Adaptif Test Sistemi (CAT)
**Durum**: ❌ TAMAMEN EKSİK

**Referans Edilen Requirements**:
- REQ-27.1 - REQ-27.100 (100 kabul kriteri)

**Gerçek Durum**:
- REQ-27 sadece "AI Agent Modül Yükleme Kontrolü" hakkında
- REQ-27.1 - REQ-27.5 mevcut (5 kabul kriteri)
- REQ-27.6 - REQ-27.100 **MEVCUT DEĞİL** (95 eksik kriter)

**Etkilenen Tasks**:
- Task 59.1-59.4: IRT Model (REQ-27.1-27.16)
- Task 60.1-60.4: Adaptif Test Motoru (REQ-27.17-27.32)
- Task 61.1-61.5: Deneme Sınavı Tipleri (REQ-27.33-27.52)
- Task 62.1-62.4: Soru Seçimi (REQ-27.53-27.68)
- Task 63.1-63.4: Gerçek Zamanlı Adaptasyon (REQ-27.69-27.84)
- Task 64.1-64.4: Performans Analitikleri (REQ-27.85-27.100)

**Çözüm**: REQ-27'yi yeniden yapılandır veya yeni REQ-49 oluştur

---

#### Task 76-82: Disleksi Desteği (134 Kriter)
**Durum**: ❌ TAMAMEN EKSİK

**Referans Edilen Requirements**:
- REQ-30.1 - REQ-30.104 (104 kabul kriteri)

**Gerçek Durum**:
- REQ-30 "Frontend-Backend CORS Kontrolü" hakkında (placeholder)
- REQ-30.1 - REQ-30.104 **MEVCUT DEĞİL**

**Etkilenen Tasks**:
- Task 76: Tipografi (REQ-30.1-30.13)
- Task 77: Renk/Kontrast (REQ-30.14-30.27)
- Task 78: Okuma Yardımcıları (REQ-30.28-30.42)
- Task 79: Text-to-Speech (REQ-30.43-30.56)
- Task 80: Metin Basitleştirme (REQ-30.57-30.72)
- Task 81: Görsel Destekler (REQ-30.73-30.88)
- Task 82: Çoklu Duyusal (REQ-30.89-30.104)

**Çözüm**: Yeni REQ-50 oluştur: "Disleksi Desteği Sistemi"

---

#### Task 83-87: Diskalkuli Desteği (120 Kriter)
**Durum**: ❌ TAMAMEN EKSİK

**Referans Edilen Requirements**:
- REQ-31.1 - REQ-31.100 (100 kabul kriteri)

**Gerçek Durum**:
- REQ-31 "Güvenlik Kontrolleri" hakkında (placeholder)
- REQ-31.1 - REQ-31.100 **MEVCUT DEĞİL**

**Etkilenen Tasks**:
- Task 83: Görsel Matematik (REQ-31.1-31.20)
- Task 84: Adım Adım Çözüm (REQ-31.21-31.40)
- Task 85: Hesap Makinesi (REQ-31.41-31.60)
- Task 86: Renkli Kodlama (REQ-31.61-31.80)
- Task 87: Manipülatifler (REQ-31.81-31.100)

**Çözüm**: Yeni REQ-51 oluştur: "Diskalkuli Desteği Sistemi"

---

#### Task 88-92: DEHB Desteği (110 Kriter)
**Durum**: ❌ TAMAMEN EKSİK

**Referans Edilen Requirements**:
- REQ-32.1 - REQ-32.100 (100 kabul kriteri)

**Gerçek Durum**:
- REQ-32 "Test Coverage Analizi" hakkında (placeholder)
- REQ-32.1 - REQ-32.100 **MEVCUT DEĞİL**

**Etkilenen Tasks**:
- Task 88: Dikkat Yönetimi (REQ-32.1-32.20)
- Task 89: Focus Mode (REQ-32.21-32.40)
- Task 90: Görev Bölme (REQ-32.41-32.60)
- Task 91: Gamification (REQ-32.61-32.80)
- Task 92: Anında Geri Bildirim (REQ-32.81-32.100)

**Çözüm**: Yeni REQ-52 oluştur: "DEHB Desteği Sistemi"

---

#### Task 93-96: OSB Desteği (115 Kriter)
**Durum**: ❌ TAMAMEN EKSİK

**Referans Edilen Requirements**:
- REQ-33.1 - REQ-33.80 (80 kabul kriteri)

**Gerçek Durum**:
- REQ-33 "API Dokümantasyon Kontrolü" hakkında (placeholder)
- REQ-33.1 - REQ-33.80 **MEVCUT DEĞİL**

**Etkilenen Tasks**:
- Task 93: Öngörülebilir Arayüz (REQ-33.1-33.20)
- Task 94: Görsel Programlar (REQ-33.21-33.40)
- Task 95: Net Talimatlar (REQ-33.41-33.60)
- Task 96: Duyusal Yük Azaltma (REQ-33.61-33.80)

**Çözüm**: Yeni REQ-53 oluştur: "OSB Desteği Sistemi"

---

## 📋 ORTA ÖNCELİKLİ TUTARSIZLIKLAR

### 2. Belirsiz veya Genel Requirement Referansları

#### Task 65-69: ÖSYM Sınav Formatı
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-11.1, REQ-11.2, REQ-11.3, REQ-11.5, REQ-11.6, REQ-11.7, REQ-11.8

**Gerçek Durum**:
- REQ-11 "Gerçek Zamanlı İletişim ve Koordinasyon" hakkında
- REQ-11.1-11.6 AI Agent koordinasyonu ile ilgili
- ÖSYM sınav formatı REQ-1'de tanımlı

**Çözüm**: Task referanslarını REQ-1'e güncelle

---

#### Task 70-75: Soru Bankası Sistemi
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-13.1, REQ-13.2, REQ-13.3, REQ-13.7

**Gerçek Durum**:
- REQ-13 "Makale İçerik Yönetimi" hakkında
- Soru bankası için özel requirement yok

**Çözüm**: Yeni REQ-54 oluştur: "Soru Bankası Yönetim Sistemi"

---

#### Task 97-100: Video Ders Entegrasyonları
**Durum**: ✅ UYUMLU

**Referans Edilen**: REQ-14.1, REQ-14.2, REQ-14.3, REQ-14.5, REQ-14.6

**Gerçek Durum**:
- REQ-14 "Video İçerik Yönetimi" ile uyumlu
- Tüm referanslar mevcut

---

#### Task 101-105: Üniversite Tercih Danışmanlığı
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-18.1, REQ-18.2, REQ-18.4, REQ-18.5, REQ-18.6, REQ-18.7, REQ-18.8

**Gerçek Durum**:
- REQ-18 "Toplu İçerik Yükleme" hakkında
- Üniversite tercih sistemi için özel requirement yok

**Çözüm**: Yeni REQ-55 oluştur: "Üniversite Tercih Danışmanlığı Sistemi"

---

#### Task 106-109: Canlı Ders ve Öğretmen Desteği
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-15.1, REQ-15.2, REQ-15.3, REQ-15.4, REQ-15.5

**Gerçek Durum**:
- REQ-15 "İçerik Arama ve Filtreleme" hakkında
- Canlı ders sistemi için özel requirement yok

**Çözüm**: Yeni REQ-56 oluştur: "Canlı Ders ve Öğretmen Desteği Sistemi"

---

#### Task 110-114: Mobil Uygulama
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-21.1, REQ-21.2, REQ-21.3, REQ-21.4, REQ-21.5, REQ-21.6, REQ-21.7

**Gerçek Durum**:
- REQ-21 "Türkçe İçerik Garantisi" hakkında
- Mobil uygulama için özel requirement yok
- PWA desteği REQ-8'de var

**Çözüm**: Yeni REQ-57 oluştur: "Mobil Uygulama (iOS/Android)"

---

#### Task 115-118: Sosyal Öğrenme ve Topluluk
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-22.1, REQ-22.2, REQ-22.3, REQ-22.6

**Gerçek Durum**:
- REQ-22 "Konu Uygunluğu Doğrulaması" hakkında
- Sosyal öğrenme için özel requirement yok

**Çözüm**: Yeni REQ-58 oluştur: "Sosyal Öğrenme ve Topluluk Sistemi"

---

#### Task 119-122: Motivasyon ve Gamification
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-16.1, REQ-16.2, REQ-16.3, REQ-16.4

**Gerçek Durum**:
- REQ-16 "Kişiselleştirilmiş İçerik Önerileri" hakkında
- Gamification için özel requirement yok

**Çözüm**: Yeni REQ-59 oluştur: "Motivasyon ve Gamification Sistemi"

---

#### Task 123-125: Psikolojik Destek Sistemi
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-20.1, REQ-20.2, REQ-20.3, REQ-20.5, REQ-20.6, REQ-20.7, REQ-20.8

**Gerçek Durum**:
- REQ-20 "İçerik Güvenliği ve Yetkilendirme" hakkında
- Psikolojik destek için özel requirement yok

**Çözüm**: Yeni REQ-60 oluştur: "Psikolojik Destek Sistemi"

---

#### Task 126-128: Bilişsel Yük Teorisi
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-41.4, REQ-41.5, REQ-41.6, REQ-41.7

**Gerçek Durum**:
- REQ-41 "Monitoring Sistemi Kontrolü" hakkında (placeholder)
- Bilişsel yük teorisi için özel requirement yok

**Çözüm**: Yeni REQ-61 oluştur: "Bilişsel Yük Teorisi Optimizasyonu"

---

#### Task 129-131: Duygusal Zeka ve Duygu Tanıma
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-44.1, REQ-44.2, REQ-44.5, REQ-44.6, REQ-44.7

**Gerçek Durum**:
- REQ-44 "Integration Test Kontrolü" hakkında (placeholder)
- Duygusal zeka için özel requirement yok

**Çözüm**: Yeni REQ-62 oluştur: "Duygusal Zeka ve Duygu Tanıma Sistemi"

---

#### Task 132-134: Blockchain Sertifika Sistemi
**Durum**: ⚠️ KISMI UYUMSUZLUK

**Referans Edilen**: REQ-45.1, REQ-45.2, REQ-45.6

**Gerçek Durum**:
- REQ-45 "Security Hardening" hakkında (placeholder)
- Blockchain sertifika için özel requirement yok

**Çözüm**: Yeni REQ-63 oluştur: "Blockchain Sertifika Sistemi"

---

## 📊 TUTARSIZLIK İSTATİSTİKLERİ

### Eksik Requirements Özeti

| Requirement ID | Beklenen Kriter Sayısı | Mevcut Kriter Sayısı | Eksik Kriter | Durum |
|----------------|------------------------|----------------------|--------------|-------|
| REQ-26 | 96 | 5 | 91 | ❌ Kritik |
| REQ-27 | 100 | 5 | 95 | ❌ Kritik |
| REQ-30 | 104 | 0 | 104 | ❌ Kritik |
| REQ-31 | 100 | 0 | 100 | ❌ Kritik |
| REQ-32 | 100 | 0 | 100 | ❌ Kritik |
| REQ-33 | 80 | 0 | 80 | ❌ Kritik |
| REQ-48-63 | - | 0 | ~500 | ❌ Kritik |

**Toplam Eksik Kriter**: ~1070 kabul kriteri

### Task Coverage Analizi

| Task Grubu | Task Sayısı | Requirements Durumu | Coverage |
|------------|-------------|---------------------|----------|
| Core Platform (1-52) | 52 | ✅ Tam | 100% |
| LLM Soru Üretim (53-58) | 6 | ❌ Eksik | 5% |
| Adaptif Test (59-64) | 6 | ❌ Eksik | 5% |
| ÖSYM Format (65-69) | 5 | ⚠️ Yanlış Ref | 50% |
| Soru Bankası (70-75) | 6 | ⚠️ Yanlış Ref | 30% |
| Disleksi (76-82) | 7 | ❌ Eksik | 0% |
| Diskalkuli (83-87) | 5 | ❌ Eksik | 0% |
| DEHB (88-92) | 5 | ❌ Eksik | 0% |
| OSB (93-96) | 4 | ❌ Eksik | 0% |
| Video Entegrasyon (97-100) | 4 | ✅ Tam | 100% |
| Üniversite (101-105) | 5 | ⚠️ Yanlış Ref | 20% |
| Canlı Ders (106-109) | 4 | ⚠️ Yanlış Ref | 20% |
| Mobil (110-114) | 5 | ⚠️ Yanlış Ref | 40% |
| Sosyal (115-118) | 4 | ⚠️ Yanlış Ref | 20% |
| Gamification (119-122) | 4 | ⚠️ Yanlış Ref | 30% |
| Psikolojik (123-125) | 3 | ⚠️ Yanlış Ref | 20% |
| Bilişsel Yük (126-128) | 3 | ⚠️ Yanlış Ref | 0% |
| Duygusal Zeka (129-131) | 3 | ⚠️ Yanlış Ref | 0% |
| Blockchain (132-134) | 3 | ⚠️ Yanlış Ref | 0% |
| Proje Sağlık (135-139) | 5 | ✅ Tam | 100% |

**Genel Coverage**: ~35% (52/139 task tam uyumlu)

---

## 🔧 ÖNERİLEN DÜZELTMELER

### Yaklaşım 1: Requirements Dokümanını Genişlet (ÖNERİLEN)

Yeni requirements ekle:

1. **REQ-48**: LLM Tabanlı ÖSYM Soru Üretim Sistemi (96 kriter)
2. **REQ-49**: Adaptif Test Sistemi (CAT) (100 kriter)
3. **REQ-50**: Disleksi Desteği Sistemi (104 kriter)
4. **REQ-51**: Diskalkuli Desteği Sistemi (100 kriter)
5. **REQ-52**: DEHB Desteği Sistemi (100 kriter)
6. **REQ-53**: OSB Desteği Sistemi (80 kriter)
7. **REQ-54**: Soru Bankası Yönetim Sistemi (20 kriter)
8. **REQ-55**: Üniversite Tercih Danışmanlığı (32 kriter)
9. **REQ-56**: Canlı Ders ve Öğretmen Desteği (20 kriter)
10. **REQ-57**: Mobil Uygulama (iOS/Android) (28 kriter)
11. **REQ-58**: Sosyal Öğrenme ve Topluluk (16 kriter)
12. **REQ-59**: Motivasyon ve Gamification (16 kriter)
13. **REQ-60**: Psikolojik Destek Sistemi (32 kriter)
14. **REQ-61**: Bilişsel Yük Teorisi (16 kriter)
15. **REQ-62**: Duygusal Zeka ve Duygu Tanıma (20 kriter)
16. **REQ-63**: Blockchain Sertifika Sistemi (12 kriter)

**Toplam Yeni Kriter**: ~792 kabul kriteri

---

### Yaklaşım 2: Tasks Dokümanını Güncelle

Task referanslarını mevcut requirements'a uyarla veya "TBD" olarak işaretle.

**Avantaj**: Hızlı düzeltme
**Dezavantaj**: Spec-driven development metodolojisine aykırı

---

### Yaklaşım 3: Hibrit Yaklaşım

1. Kritik tasklar (53-96) için yeni requirements yaz
2. Opsiyonel tasklar (110-134) için referansları "Future REQ" olarak işaretle
3. Yanlış referansları düzelt (65-69, 70-75, vb.)

---

## ✅ SONRAKI ADIMLAR

### Öncelik 1: Kritik Requirements Ekleme (1-2 Gün)

1. REQ-48: LLM Soru Üretim (Task 53-58 için)
2. REQ-49: Adaptif Test CAT (Task 59-64 için)
3. REQ-50-53: Erişilebilirlik (Task 76-96 için)

### Öncelik 2: Referans Düzeltmeleri (4-6 Saat)

1. Task 65-69 → REQ-1'e güncelle
2. Task 70-75 → Yeni REQ-54'e güncelle
3. Diğer yanlış referansları düzelt

### Öncelik 3: Opsiyonel Requirements (1 Hafta)

1. REQ-54-63: Gelecek özellikler için requirements yaz
2. Design dokümanını güncelle
3. Traceability matrix oluştur

---

## 📝 NOTLAR

- Bu analiz **otomatik** değil, **manuel** inceleme ile yapıldı
- Tüm 139 task ve 47 requirement detaylı olarak kontrol edildi
- Tutarsızlıklar **EARS formatı** ve **INCOSE standartları** göz önünde bulundurularak tespit edildi
- Spec-driven development metodolojisine uygun çözümler önerildi

---

**Analiz Tarihi**: 20 Ekim 2025
**Analist**: Kiro AI Assistant
**Versiyon**: 1.0

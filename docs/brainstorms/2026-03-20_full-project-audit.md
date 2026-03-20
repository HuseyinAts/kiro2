# Brainstorm: TUM PROJENIN TUM KISIMLARI YAPILARI TUM BILESENLERI
Tarih: 2026-03-20 | Domain: architecture + strategy | Perspektifler: Sistem Mimari, Frontend/UX, Veri/Pipeline, Urun Stratejisti

## TL;DR
KIRO2 77K soruyla rakiplerinin 2 kati icerige sahip ama 125 API / 173 servis / 70 sayfa ile MVP degil "feature monster". En kritik: 4 ogrenme algoritmasi (IRT-FSRS-ZPD-BKT) birbirinden habersiz calisiyor ve IRT parametreleri hic kalibre edilmemis. Acil: scope %60 kes, algoritmalari birlestir, dead code temizle.

## Proje Boyutlari (Dogrulanmis)

| Katman | Dosya Sayisi | MVP icin Makul | Durum |
|--------|-------------|----------------|-------|
| Backend API Routers | 125 (99'u loader'da aktif) | 20-25 | Asiri |
| Backend Services | 173 | 30-40 | Asiri |
| Backend Models | 76 | 20-30 | Buyuk ama makul |
| Backend Core | 186 | 40-50 | ALARM — junk drawer |
| Backend Algorithms | 21 | 5-8 | Zengin ama silo |
| Frontend Pages | 70 (27 Modern* wrapper) | 8-12 | Asiri |
| Frontend Components | 65 dizin | 20-25 | Asiri |
| Frontend Hooks | 45 | 15-20 | Buyuk |
| Frontend Services | 30+ | 10-15 | Buyuk |
| Frontend Stores | 6 | 6-8 | Uygun |
| Docker Compose | 9 | 2-3 | Asiri |
| YouTube Modules | 14 | 5-6 | Asiri |

## Top 5 Aksiyon

| # | Aksiyon | Etki | Zorluk | Kaynak |
|---|---------|------|--------|--------|
| 1 | **MVP scope %60 kes** — 8 sayfa ogrenci core loop, 4 rol->1 rol, 17 nis servis devre disi | 5/5 | Orta | Urun Stratejisti |
| 2 | **Algoritma orkestrasyon katmani** — BKT->ZPD->IRT->FSRS pipeline, StudentLearningState aggregate | 5/5 | Zor | Veri/Pipeline |
| 3 | **IRT cold-start bootstrap** — 77K sorunun tamami difficulty=0.0, heuristik prior'lardan basla | 5/5 | Orta | Veri/Pipeline |
| 4 | **Modern* wrapper katmanini yok et** — 27 bos wrapper sil, App.tsx'te direkt import | 4/5 | Kolay | Frontend/UX |
| 5 | **Core dizinini alt paketlere bol** — 186 duz dosya -> 8-10 domain paketi | 4/5 | Orta | Sistem Mimari |

## Konsensus (2+ perspektif hemfikir)

1. **Scope fazla, kesim sart** — Mimari (26 kayitsiz router), Frontend (27 bos wrapper + 18 Revolutionary dead code), Strateji (68 sayfa vs 8-12 yeterli). 3/4 perspektif.
2. **Dead code ciddi yuk** — Revolutionary dizini (18 component, 0 import), useRevolutionaryFeatures (330 satir, 0 kullanim), UI primitive duplikasyonu (Button 3 versiyon), 24 kayitsiz router, 17 nis servis.
3. **Algoritmalar silo** — 4 bagimsiz sistem, IRT kalibre degil, FSRS kulturel parametreleri dogrulanmamis.

## Catismalar

| Konu | Taraf A | Taraf B | Karar |
|------|---------|---------|-------|
| Gamification kapsami | Strateji: "XP+Streak yeter, 12 tablo ertele" | Frontend: "learningPathStore lazim" | Strateji hakli — 3 tablo core, ama learningPathStore eklenmeli |
| Accessibility hooks | Frontend: "Revolutionary sil, accessibility DOKUNMA" | Strateji: "Nis ozellikler MVP'de olmasin" | Frontend hakli — 5378 sayili Kanun, accessibility kalmali |
| Qwen3-8B vs API | Strateji: "2 alan, geri kalan API'ye devret" | Pipeline: "Turkce NLP kalitesi duser" | Hibrit — soru uretimi + Sokratik = Qwen, embedding + siniflandirma = API |
| Docker compose | Mimari: "9->3 yeter" | DevOps: "Profil farkliliklari kaybolur" | Mimari hakli — profiles: ile 3 dosyada 9 konfigurasyon mumkun |

## Perspektif Detaylari

### 1. Sistem Mimari

**Karar: Moduler Monolith ama Core Katmani Kaotik**

Application factory temiz, router loader 99 mapping/14 kategori ile duzgun. Ancak core/ "junk drawer": 186 dosyanin 72'si cross-cutting concern. Auth icin 6 ayri dosya (auth.py, auth_dependencies.py, auth_middleware.py, auth_rate_limiting.py, auth_security_utils.py, consolidated_auth_dependencies.py).

**Oneriler:**
1. Core dizinini domain-bounded alt paketlere bol (auth/, cache/, monitoring/) — Etki: 4/5, Zorluk: Orta
2. Docker Compose 9->3 (base+dev+prod, profiles ile) — Etki: 3/5, Zorluk: Kolay
3. Router/Servis eslesme auditi + olum kodu temizligi — Etki: 5/5, Zorluk: Orta

**Kor nokta:** Dual table audit eksik — 173 servisten kaci hala bos questions tablosunu sorguluyor?
**Uyari:** Microservice'e gecmeyin — <4ms p95 Uvicorn scaling ile yeterli.

### 2. Frontend/UX Uzmani

**Modern* Wrapper Pattern: 20+ sayfa tamamen bos wrapper (sadece import+return)**

StudentDashboardPage -> StudentDashboard -> ModernStudentDashboard = 3 katman. Revolutionary/ dizini (18 component) hicbir aktif sayfadan import edilmiyor. UI primitive'lerde ModernButton + modern-button + button = 3 versiyon.

**Oneriler:**
1. Modern* wrapper'lari sil, direkt import — Etki: 4/5, Zorluk: Kolay
2. Revolutionary + dead code temizle — Etki: 3/5, Zorluk: Kolay
3. UI primitive'leri tek konvansiyona birlestir — Etki: 3/5, Zorluk: Orta

**Kor nokta:** learningPathStore yok — client-side state tutarsizligi.
**Uyari:** Accessibility hook'larini silmeyin — 5378 sayili Engelliler Kanunu.

### 3. Veri/Pipeline Uzmani

**4 algoritma SILO: IRT kalibre degil, FSRS kulturel parametreler dogrulanmamis**

77,336 sorunun tamami irt_difficulty=0.0, is_calibrated=False, calibration_sample_size=0. FSRS "10,000 Turk ogrenci" iddiasi dogrulanamaz (17 sabit sayi). Hicbir merkezi "algorithm router" yok.

**Oneriler:**
1. IRT cold-start bootstrap — heuristik prior'lar + EM/MCMC kalibrasyon — Etki: 5/5, Zorluk: Orta
2. Algoritma orkestrasyon katmani (BKT->ZPD->IRT->FSRS pipeline) — Etki: 5/5, Zorluk: Zor
3. FSRS kulturel parametrelerin A/B test ile dogrulama — Etki: 3/5, Zorluk: Orta

**Kor nokta:** 4 algoritma birbirinden habersiz — tutarsiz zorluk onerisi.
**Uyari:** Veri olmadan parametre fine-tune etmeyin.

### 4. Urun Stratejisti

**Feature Monster: 68 sayfa, 123 router, 200 servis — MVP degil**

Rakip karsilastirma: KIRO2 77K soru (rakipler 30-50K), AI (rakiplerde yok), 4 rol (rakipler 1-2). Ama 17 nis servis (YOLO, Bloom taxonomy, cultural adaptation, revolutionary, sequential reasoning) hicbir rakibin MVP'sinde yok — cunku gerekli degil.

**Oneriler:**
1. %60 kes — 8 sayfa ogrenci core loop, tek rol — Etki: 5/5, Zorluk: Orta
2. Qwen3-8B'yi 2 alana sinirla (soru uretimi + Sokratik chat) — Etki: 4/5, Zorluk: Kolay
3. Gamification'i XP+Streak+5 rozet ile sinirla — Etki: 4/5, Zorluk: Kolay

**Kor nokta:** D7 retention metrigi tanimlanmamis — ozellik sayisi basari olcusu degil.
**Uyari:** 4 rolu ayni anda cikarmayin.

## Kor Noktalar & Uyarilar (Birlesik)

### Kor Noktalar
1. Dual table audit eksik — 173 servisten kaci bos questions tablosunu sorguluyor? (Mimari)
2. LearningPath store yok — client-side state tutarsizligi (Frontend)
3. 4 algoritma birbirinden habersiz — tutarsiz zorluk onerisi (Pipeline)
4. D7 retention metrigi tanimlanmamis (Strateji)

### Uyarilar
1. Microservice'e gecmeyin — <4ms p95, Uvicorn scaling yeterli (Mimari)
2. Accessibility hook'larini silmeyin — 5378 sayili Kanun (Frontend)
3. Veri olmadan FSRS/IRT fine-tune etmeyin (Pipeline)
4. 4 rolu ayni anda cikarmayin (Strateji)

---
*4 paralel perspektif, Read-based analiz, 2026-03-20*

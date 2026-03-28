# Brainstorm: Connectivity Skorunu 5.6'dan 6.0+'ya Cikarma Stratejisi
Tarih: 2026-03-29 | Domain: architecture | Perspektifler: Performans, Bakim, Maliyet/ROI

## TL;DR

LP v2-Daily baglantisi (0/10) ve Recommendations mock'u (1/10) en dusuk skorlar — bu ikisini 5'e cikarmak tek basina +0.53 puan saglar ve 6.0+ hedefini astirir. En kritik risk: orchestrator'un `user_theta` tablosu StudentAbility ile uyumsuz, sessizce bos donuyor.

## Top 5 Aksiyon

| # | Aksiyon | Etki | Effort | Kaynak |
|---|---------|------|--------|--------|
| 1 | **LP Daily endpoint'ini LP v2 sayfasina wire'la** — Backend hazir (SubjectStatusOut theta/ZPD/prereq donuyor), sadece frontend fetch + render | LP v2<->Daily: 0->5 (+0.29) | 3-4 saat | Maliyet + Performans |
| 2 | **DailyPlanPage interface'ine v2 field ekle** — theta_se, prereq_blocked, zpd_zone optional field + prereq uyari render | LP Daily: 6->8 (+0.12) | 1 saat | Bakim |
| 3 | **Recommendation mock'u gercek veriye bagla** — priority_score + YouTube search API zaten var, mock'u `/daily-plan` + YouTube ile degistir | Recommendations: 1->5 (+0.24) | 4-5 saat | Maliyet |
| 4 | **parentService 404 graceful fallback** — catch'te 404 kontrolu, bos/default obje don | Parent: 5->7 (+0.12) | 1 saat | Bakim |
| 5 | **chatService bionic-reading client-side** — kelime ilk yarisini bold regex, backend gerektirmez | Chat: 6->8 (+0.12) | 2 saat | Bakim |

**Toplam potansiyel:** +0.89 (5.6 -> 6.5) — ilk 2 aksiyon tek basina +0.41 ile 6.0 hedefini tutar.

## Konsensus (2+ Perspektif Hemfikir)

1. **LP v2 ve Daily'yi baglamak en yuksek ROI** — 3 perspektif de birinci oncelik olarak isaret etti. Backend hazir, frontend glue yeterli.
2. **Orchestrator'u canlandirmak DEGMEZ** — Performans ve Maliyet hemfikir: %94 dormant olmasi dogru, aktive etmek bakim maliyetini 5x artirir, skor 1 puan bile artmaz.
3. **Frontend interface eksiklikleri dusuk effort/yuksek etki** — Bakim ve Maliyet hemfikir: 3 satir TypeScript degisikligi ile LP Daily skoru 2 puan artar.
4. **Recommendation backend yazilmadan da ilerlenebilir** — Maliyet ve Performans: mevcut daily-plan + YouTube API'yi adapter pattern ile recommendation format'ina map'le.

## Catismalar

| Konu | Taraf A | Taraf B | Onerilen Karar |
|------|---------|---------|----------------|
| LP facade kaldir mi, zenginlestir mi? | Performans: Facade'i orchestrator'a merge et (0->5+) | Maliyet: Facade'a daily summary ekle (3->6) | Once facade zenginlestir (kolay), merge'u ayri session'a birak (zor) |
| Bionic-reading: client vs backend? | Bakim: Client-side regex (2 saat, %80 cozum) | Performans: Backend endpoint (tam cozum) | Client-side once yap, backend sonra. Turkce hece riski var ama fallback mevcut |
| Recommendation: yeni backend mi, adapter mi? | Performans: Orchestrator ciktisini adapter'la | Maliyet: Mevcut daily-plan + YouTube mix | Adapter + YouTube mix birlesimi (her iki kaynak da mevcut) |

## Perspektif Detaylari

### Performans Muhendisi

**Oneriler:**
1. Facade `get_student_path`'i orchestrator'un `_fetch_thetas_with_se`'ye delege et — LP facade->DB: 3->7 (Orta) Risk: Session/transaction leak
2. `/api/v1/recommendations` thin endpoint yaz — orchestrator daily ciktisini map'le — Recommendations: 1->6 (Kolay) Risk: Response shape uyumsuzlugu
3. Facade'i orchestrator'a merge et, in-memory cache'i Redis L1'e tasi — LP v2<->Daily: 0->5, facade->DB: 7->8 (Zor) Risk: 12+ import chain kirilir

**Kor nokta:** Orchestrator raw SQL (`text(...)`) ORM bypass ediyor. `user_theta` tablosu aslinda `student_abilities` — schema degisirse sessizce bos donecek.

**Uyari:** Orchestrator'un 24 dormant modulunu canlandirmayin. %94 dormant = dogru. Aktive etmek performans ve bakim maliyetini 5x artirir.

### Bakim Muhendisi

**Oneriler:**
1. DailyPlanPage interface'ine v2 field ekle (theta_se, prereq_blocked, prereq_topic) — LP Daily: 0->3 (Kolay) Risk: Dusuk
2. parentService 404'leri graceful fallback'e cevir — Parent: 5->7 (Kolay) Risk: Dusuk
3. chatService bionic-reading client-side regex — Chat: 6->8 (Orta) Risk: Turkce hece kenar vakalari

**Kor nokta:** parentService backend endpoint'leri hic implement edilmemis olabilir — sadece frontend 404 fix degil, backend router eksikligi de kontrol edilmeli.

**Uyari:** Oneri 1+2 birlikte ~2 saat ve skor 5.6->6.3. Rush commit yapilirsa NFC normalizasyon bugu riski var.

### Maliyet/ROI Analisti

**Oneriler:**
1. LP v2 -> LP Daily bagla: daily endpoint'i LP v2 sayfasina wire'la — 3-4 saat, +0.29 (Dusuk zorluk)
2. Recommendation mock'u gercek veriye: priority_score + YouTube search — 4-5 saat, +0.24 (Orta zorluk)
3. LP facade zenginlestirme: daily summary + recommendation count ekle — 2-3 saat, +0.18 (Dusuk zorluk)

**Kor nokta:** recommendationService singleton her zaman mock data donuyor — kullanici bunu gercek oneri sanabilir.

**Uyari:** Oneri 1 ve 2 paralel yapilirsa ayni sayfada 2 yeni API call = UX latency riski. Once 1'i yap, olc, sonra 2'yi ekle.

## Kor Noktalar & Uyarilar

### Kor Noktalar
- **user_theta vs student_abilities**: Orchestrator `user_theta` tablosunu sorguluyor, production'da `student_abilities` var. Sessizce bos donuyor, exception yutulup warning log'a gidiyor. HER fix'ten once bu align edilmeli.
- **parentService backend SIFIR**: 4 endpoint'in sadece frontend'de degil, backend'de de implement edilmesi lazim. Graceful fallback gecici cozum.
- **Recommendation mock gizli**: Kullanici gercek oneri aliyor sanabilir — mock oldugu UI'da belli degil.
- **Facade multi-worker tutarsizlik**: Gunicorn worker'lar arasi in-memory cache paylasimi YOK — ayni ogrenci farkli worker'dan farkli path gorebilir.

### Uyarilar
- Orchestrator 24 dormant modulu canlandirMAyin (5x maliyet, ~0 skor artisi)
- Rush commit yapmayin (NFC, Turkce hece, TypeScript strict mode riskleri)
- Paralel API call dikkat (ayni sayfada 2+ yeni fetch = latency)
- Frontend-only fix'ler kalici cozum DEGIL — backend endpoint eksiklikleri ayri session'da ele alinmali

## Skor Projeksiyon Tablosu

| Senaryo | Aksiyonlar | Effort | Skor |
|---------|-----------|--------|------|
| Minimum (6.0) | #1 + #2 | 4-5 saat | ~6.0 |
| Hedef (6.5) | #1 + #2 + #3 | 8-10 saat | ~6.5 |
| Agresif (7.0) | #1-#5 + user_theta fix | 15-18 saat | ~7.0 |
| Maksimum (8.0+) | + Faz D-F tam uygulama | 40+ saat | ~8.0 |

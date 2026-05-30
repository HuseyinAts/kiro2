# KIRO2 Ürün-Kalite Değerlendirmesi — %95'e Giden Yol Haritası

**Tarih:** 30 Mayıs 2026
**Yöntem:** Çok-ajanlı read-only workflow (`yks-quality-95-roadmap`, run `wf_8e02601b-340`) — 9 ajan, 1.43M token, ~14 dk. 3 faz: Map (4 eksen paralel canlı-kod keşif) → Verify (eksen başına adversarial phantom-filtre) → Synthesize.
**Kapsam:** Ürün kalitesi (kod kalitesi değil) — "öğrenciyi YKS'ye gerçekten hazırlıyor mu + sıkılmadan bağlı tutuyor mu". Kod **dokunulmadı**.
**Hedef:** Kalite %95.

> **Mega Audit Lock notu:** Bu read-only bir değerlendirme; kod mutasyonu yok, önceki audit backlog'unu kilitlemez. Verify fazı her bulguyu canlı koddan doğruladı.

---

## Yönetici Özeti

KIRO2'nin **çekirdek mimarisi gerçek ve üretim-kalite**: öğrenci-facing adaptif akış (EAP-3PL CAT + DB-backed BKT/FSRS + ZPD/DAG orkestratörü) tam bir geri-besleme döngüsü kuruyor; oyunlaştırma omurgası (XP/streak/rozet/düello) gerçek öğrenme aktivitesine bağlı; çekirdek yolculuk (kayıt→dashboard→sınav→FSRS→ilerleme) uçtan uca DB-backed. **Adversarial denetimde 4 eksende de 0 saf phantom çıktı** — nadiren görülen bir disiplin.

%95'e giden yolda **iki yapısal risk** baskın (ikisi de cila değil, döngünün açık halkaları):

1. **İçerik güveni (en düşük eksen — 56):** Gold pool'un %16.6'sı problemli olduğu audit ile kanıtlandı; A-bias OCR root cause #1 hâlâ açık (yeni ingest %50.7 A+E biased); Phase 7 rationale DB cevabını ground-truth varsayıp yanlış cevapları rasyonalize ediyor (%26.7 kabul edilemez); ~787/905 "temizlenen" soru **manuel değil otomatik consensus** ile gold pool'a geri dönmüş (A-bias kontamine riski).
2. **Retention + onboarding kopukluğu:** Öğrenciyi ertesi gün geri getiren tek mekanizma (streak push) **sadece log yazıyor + celery beat'te kayıtlı değil = hiç çalışmıyor**; dedike onboarding/ilk-gün akışı **hiç yok** — yeni öğrenci 14 eşit kutuyla boş dashboard'a düşüyor.

IRT parametreleri %100 bootstrap prior (gerçek yanıt-kalibrasyonu yok) ama manuel-tetiklenebilir `calibrate_irt_batch` endpoint'i **mevcut** — eksik olan otomatik scheduler.

**En büyük net risk: yanlış öğretme (içerik) + günlük-dönüş kopukluğu (retention/onboarding) — cila değil.**

---

## Eksen Skorları

| Eksen | Skor | En Büyük Açık |
|-------|------|---------------|
| Eğitsel Etkinlik (adaptif motor) | **71** | IRT %100 bootstrap prior (otomatik kalibrasyon scheduler yok); iki çelişen OSYM net formülü; AYT FELSEFE/DIN/COĞRAFYA + YDT havuzu eksik |
| İçerik Kalitesi (cevap anahtarı güveni) | **56** | A-bias root #1 açık; Phase 7 circular rationale; ~787 soru otomatik geri-promote (kontamine); v_safe_for_beta ~10,535 < MVP 45K |
| Bağlılık / Oyunlaştırma | **66** | Retention push ölü; badge slug-set uyuşmazlığı (kazanılan rozetler UI'da görünmez); 5 eksik gamification endpoint; self-report farming |
| Öğrenci Akışı / UX | **68** | Onboarding sihirbazı yok; sınav hedefi gömülü + sessiz 7-Haziran default; Veli Paneli ölü-kutu; placement persist yok |
| **BİRLEŞİK** | **63** | İçerik + retention/onboarding baskın risk |

**Phantom not:** Verify fazı 2 önemli düzeltme yaptı — (a) içerik ajanının "905 pending hâlâ Curator manuel bekliyor" iddiası **stale** çıktı (S195+S198 ~787'sini otomatik consensus ile zaten geri-promote etmiş — bu da P0 #2'nin kaynağı); (b) eğitsel ajanın "kalibrasyon endpoint'i yok" iddiası **kısmen phantom** (`orchestrator_api.py:101-174 calibrate_irt_batch` gerçek). Bu da CLAUDE.md "%30-70 phantom" uyarısının canlı kanıtı.

---

## P0 — Beta Öncesi Zorunlu (2)

### P0.1 — Retention geri-getirme mekanizmasını canlıya al
**Eksen:** Bağlılık · **Effort:** M
**Neden:** Öğrenciyi ertesi gün geri getiren TEK mekanizma çalışmıyor. `push_tasks.py:52-56` sadece `logger.debug` + "TODO VAPID"; `celery_app.py` beat_schedule'da `send_streak_reminders` **kayıtlı değil** (Read ile doğrulandı). 16 yaşında öğrenci streak kaybını haber alamaz → D1/D7 retention dramatik düşük.
**Dosyalar:** `backend/tasks/push_tasks.py`, `backend/core/celery_app.py`, `backend/core/realtime_notification_system.py`
**Bitti-kriteri:** beat_schedule'a `send_streak_reminders` (örn. 20:00) eklenmiş; push gerçek kanaldan gönderiyor (VAPID veya en az in-app notification INSERT); `users[:10]` test-limiti kalkmış; streak-riskte bildirim oluştuğunu doğrulayan entegrasyon testi PASS.

### P0.2 — Beta-safe havuzun A-bias kontamine olmadığını doğrula
**Eksen:** İçerik · **Effort:** L
**Neden:** 12-subject audit 905 cevap anahtarı hatasını gold pool'dan çıkardı, AMA S195+S198 ~787'sini **manuel değil otomatik LLM-consensus** ile geri-promote etti. MEMORY `beta-pool-growth` notu "pending-high bulk promote ~17K hatalı soru" diye açıkça uyarıyor ve A-bias root #1 hâlâ açık. "Temizlendi" sanılan soruların çoğu kontamine kanaldan geri dönmüş olabilir → öğrenci yanlış cevap anahtarlı soru görebilir. **Yanlış öğretme = en büyük ürün riski.**
**Dosyalar:** `backend/api/curator.py`, `d-dataset/scripts/cross_validate_answers.py`, `docs/audits/2026-05-23_remaining_subjects_audit.md`, `docs/audits/2026-05-23_a_bias_root_cause.md`
**Bitti-kriteri:** Otomatik-promote denetim trail'i çıkarılmış (`pipeline_metadata.curator_apply` sorgusu); 30-50 sample insan spot-check %95+ değilse kohort 'pending'e geri alınmış; `auto_judged_high` kohortunun A+E oranı uniform'a yakın (<%45) DB ile doğrulanmış.

---

## P1 — %95 İçin Kritik (9)

| # | Başlık | Eksen | Effort | Bitti-kriteri (özet) |
|---|--------|-------|--------|----------------------|
| P1.1 | A-bias OCR root #1'i kapat: page_inline çıkarımı multi-model consensus'e bağla | İçerik | L | Pilot 200-sample A+E <%45 + spot-check %95+ |
| P1.2 | Phase 7 rationale'ı DB-cevap-bağımsız yap (LLM bağımsız çözsün, uyuşmazlıkta flag) | İçerik | M | Yeni 50-sample "kabul edilemez" <%10, circular <%15 |
| P1.3 | Dedike onboarding/ilk-gün sihirbazı (hedef + seviye tespiti zorunlu adım) | Akış | L | E2E: yeni-kullanıcı → onboarding → dashboard yolu doğrulanıyor |
| P1.4 | Sınav hedefini onboarding'e taşı + sessiz 7-Haziran default'u görünür kıl | Akış | S | Hedef yoksa banner; days_remaining "belirsiz" testi PASS |
| P1.5 | İki çelişen OSYM net formülünü tek kaynakta birleştir (cezasız 2023+) | Eğitsel | S | İki endpoint aynı cevap setiyle aynı net döndürüyor (test PASS) |
| P1.6 | Badge slug-set uyuşmazlığını çöz (kazanılan rozetler UI'da görünsün) | Bağlılık | M | Quiz tamamlama → /badges yanıtı earned:true (entegrasyon testi) |
| P1.7 | 5 eksik gamification endpoint'i ekle veya hook'u /profile'a hizala | Bağlılık | M | Her veri kartı 404 yerine veri alıyor (frontend testi) |
| P1.8 | IRT otomatik kalibrasyon scheduler'ı (mevcut calibrate_irt_batch'i periyodik çalıştır) | Eğitsel | M | beta'da standard_error>0 kayıt sayısı artıyor (DB doğrulama) |

> P1.3 + P1.4 tek akış olarak birlikte ele alınmalı (ikisi de onboarding).

---

## P2 — Cila / Temizlik (6)

| # | Başlık | Eksen | Effort |
|---|--------|-------|--------|
| P2.1 | CAT ZPD image-exclusion regex daralmasını ölç + görsel-ağırlıklı derslerde alternatif | Eğitsel | M |
| P2.2 | Daily quest + dungeon /complete self-report'u sunucu-türevli ilerlemeye bağla | Bağlılık | M |
| P2.3 | Veli Paneli ölü quick-action'ı öğrenci dashboard'undan kaldır (cerrahi, tek satır) | Akış | S |
| P2.4 | Vector search endpoint'ine quality_review_status filtresi (öğrenci-facing ise) | İçerik | S |
| P2.5 | PlacementAssessment sayfa-level özetini sunucuya persist et | Akış | S |
| P2.6 | AYT eksik dersler + YDT havuzunu tamamla veya UI'da "yakında" işaretle | Eğitsel | L |

---

## %95'e Giden Yol (sıralı projeksiyon)

Başlangıç birleşik **~63**:

1. **P0.1** (retention push) → bağlılık 66→74, günlük-dönüş halkası kapanır → **~66**
2. **P0.2** (beta-safe kontamine doğrulama/temizleme) → içerik 56→64, en büyük yanlış-öğretme riski düşer → **~68**
3. **P1.1 + P1.2** (A-bias root #1 + Phase 7) → içerik 64→76, yeni ingest güvenli + açıklamalar doğru → **~72**
4. **P1.3 + P1.4** (onboarding + hedef) → akış 68→82, ilk-temas conversion → **~76**
5. **P1.5–P1.8** (net formül + badge + endpoint + IRT scheduler) → eğitsel 71→82, bağlılık 74→82 → **~82**
6. **P2 temizlikleri + canlı-DB doğrulamaları** → cila tamamlanır → **~88-92**

> **Gerçekçi tavan:** Son 3-5 puan **beta-yanıt verisine bağımlı, salt-kod değil**. İçerik kalitesi insan-curated beta verisi biriktikçe ve IRT gerçek-kalibrasyon dolunca 95'e ulaşır. Yani %95 = kod düzeltmeleri (→~90) + beta veri döngüsü (→95).

---

## İnsan DB Doğrulaması Gereken İddialar (psql -p 5434)

Bu workflow read-only ve psql çalıştırmadı; aşağıdakiler canlı DB ile kesinleştirilmeli:

1. **v_safe_for_beta canlı count** — docs'ta 0/12,362/10,535 çelişkili; view tanımı "human_verified ONLY" mi auto_judged_high dahil mi; MVP 45K ile kıyas.
2. **auto_judged_high cevap-şık dağılımı** — `SELECT correct_answer, COUNT(*) GROUP BY`; A+E <%45 mi yoksa kontamine mi. Özellikle S195+S198'de otomatik-promote ~787 soru.
3. **Otomatik-promote denetim trail'i** — `pipeline_metadata.curator_apply/curator_verdict` ile manuel vs otomatik kohort büyüklüğü.
4. **IRT kalibrasyon durumu** — `SELECT COUNT(*) FROM irt_calibration_history WHERE standard_error>0` (gerçekten 0 mı).
5. **AYT ders havuzu** — `SELECT DISTINCT subject_area FROM question_bank WHERE exam_type='AYT'`; FELSEFE/DIN/COĞRAFYA/YDT gerçekten yok mu (kod yorumu eski mi).
6. **Badge seed** — `SELECT id, slug FROM badges`; check_quiz_badges slug'ları eşleşiyor mu (FK join çöküyor mu).
7. **CAT image-exclusion daralması** — subject başına regex öncesi/sonrası COUNT (Geometri/Fizik theta yakınsama riski).
8. **question_bank status dağılımı** — MEMORY snapshot'ı (13,595 vs ...) canlı mı.

---

## Yöntem Şeffaflığı

- **Sample:** Tam codebase (backend/api, services, algorithms, scripts; frontend/src; docs/audits) — truncation yok, file:line kanıt.
- **Phantom filtre:** Her eksende top bulgular "çürüt" modunda adversarial denetlendi. Saf phantom: 0/4 eksen. Partial/stale düzeltme: 2 (içerik 905-pending, eğitsel kalibrasyon-endpoint).
- **Reproducible:** Evet — script `workflows/scripts/yks-quality-95-roadmap-wf_8e02601b-340.js`.
- **Sınır:** DB-state iddiaları (yukarıdaki 8 madde) kod-dışı, psql doğrulaması bekliyor.

---

*Oluşturulma: 30 Mayıs 2026. Workflow run: wf_8e02601b-340. Sonraki adım: P0.1/P0.2 ayrı turlarda TDD + debugging-first gate ile (kullanıcı onayıyla).*

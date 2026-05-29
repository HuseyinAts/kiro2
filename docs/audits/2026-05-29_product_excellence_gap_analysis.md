# KIRO2 Ürün Mükemmelliği Gap Analizi Raporu

**Tarih:** 2026-05-29
**Kapsam:** Misyon Uyumu, Sınav-Hazırlık Etkinliği, İçerik Kalitesi, Bağlılık (Engagement), Rekabet Farklılaşması
**Yöntem:** Doğrulanmış (adversarial verify'lı) denetim JSON sentezi + phantom filtresi
**Workflow:** `kiro2-product-excellence-gap-analysis` — 40 ajan, 6.9M token, ~54 dk
**Genel Skor:** **47 / 100**

---

## 1. Yönetici Özeti & Genel Skor Gerekçesi

KIRO2 **enterprise-ready altyapı eşiğini geçmiş** (orchestrator v2.5, IRT 4PL + FSRS + ZPD + CAT, 1163 endpoint, 416 .tsx, golden flow 164/166 PASS). Sorun mühendislikte değil, **ürün değer zincirinin teslimatında.**

Genel skor **47/100**. Düşük olmasının nedeni iki P0'ın birbirini güçlendirmesi:

1. **DailyPlanPage'in backend endpoint'leri yok** — öğrenci çekirdek giriş noktasına (günlük plan) hiç ulaşamıyor (404).
2. **Soruların >%97'si kalibre edilmemiş IRT parametresi** kullanıyor — CAT'ın adaptif çekirdeği çalışmıyor.

Bu ikisi birlikte: "kişiselleştirilmiş YKS hazırlığı" vaadi şu an **teknik olarak teslim edilemiyor.** Öğrenci plana ulaşamıyor; ulaşsa bile soru zorluğu rastgele. Üstüne beta-hazır havuz toplam içeriğin **<%8'i** ve gold pool'da öğrenci açıklaması (rationale) kapsamı **%0**.

Skor 0 değil çünkü altyapı gerçekten sağlam, fixler tanımlı, işin büyük kısmı **entegrasyon + veri** (sıfırdan yapım değil).

> **DÜRÜSTLÜK NOTU (kanıt zayıflığı):** Sağlanan denetim JSON'u `engagement` boyutunun ortasında (G5 verdict) **kesilmiş**, ve istenen 5. boyut **`rekabet_farklilasma` hiç gelmemiş.** Bu rapor 4 tam boyut üzerinden sentezlenmiştir. Engagement P2 detayları (G5+) ve rekabet skoru **eksik kanıt** olarak işaretlenmiştir. Rekabet skoru 0 = "ölçülemedi", "kötü" değil.

---

## 2. Boyut-Bazlı Skorlar

| Boyut | Skor | Tek Cümle Değerlendirme |
|-------|------|--------------------------|
| Misyon Uyumu (mission_fit) | **58** | Altyapı tutarlı ama özellikler silo; onboarding akışı kırık (DailyPlan 404). |
| Sınav-Hazırlık Etkinliği (exam_efficacy) | **42** | Algoritma kodu titiz ama IRT havuzu kalibre değil → adaptiflik kâğıt üstünde. |
| İçerik Kalitesi (content_quality) | **42** | Temel bütünlük tam (%100 NOT-NULL, %99 görüntü) ama cevap anahtarı hatası ~%9 + rationale %0. |
| Bağlılık (engagement) | **52** | Zengin gamification altyapısı var ama mastery'den kopuk + re-engagement hook'u yok. |
| Rekabet Farklılaşması | **0 (ölçülemedi)** | Denetim verisi sağlanmadı — aşağıda nitel bahisler verildi, skor verilmedi. |

---

## 3. Sıralı P0 Gap Listesi (Sadece Doğrulanmış-Gerçek)

### P0-1 — DailyPlanPage backend endpoint'leri yok: onboarding tamamen kırık
**Boyut:** mission_fit · **Kaynak:** G-05-CAT-PLACEMENT-DISCONNECTED (verdict: P0'a yükseltildi)

- **Etki:** Öğrenci çekirdek giriş noktasına (günlük çalışma planı) ulaşamıyor. DailyPlanPage `/today` ve `/status` çağırıyor ama bu endpoint'ler `learning_path_v2.py`'de **yok** → sayfa çift 404 ile yükleniyor. CAT/placement kodu mevcut ama bu akıştan **erişilemez (orphan)**. "Kişiselleştirilmiş günlük plan" vaadi sıfır kullanıcıya teslim ediliyor. Orijinal denetim bunu "opsiyonel side-quest" sanmış; gerçekte **komple blocker.**
- **Öneri:** `GET /today` (günlük plan üret) + `GET /status` (theta/SE/mastery/ZPD/FSRS-due) endpoint'lerini frontend'in beklediği şemaya birebir ekle. Sıra: (1) frontend fetch path + payload'ı çıkar, (2) handler yaz, (3) golden_flow E2E (login → /today 200, asla 500), (4) Docker smoke gerçek DB'de.

### P0-2 — Soruların >%97'si kalibre edilmemiş IRT parametresi: CAT adaptifliği çalışmıyor
**Boyut:** exam_efficacy · **Kaynak:** G1-IRT-PARAM-DESERT (verdict: REAL, confirmed)

- **Etki:** 167K sorunun ~598'i kalibre; gerisi default `a=1.0, b=0.0, c=0.25`. EAP posterior'u likelihood kadar iyi → yanlış item parametresi posterior'u prior'a çökertir → theta geçersiz → ZPD filtreleme gürültü → öğrenci rastgele zorlukta soru görür → **adaptif kazanım sıfır.** CAT'ın tüm değer önerisi teslim edilemiyor. Kod doğru, veri eksik.
- **Öneri:** `n_responses>=30` olan tüm sorularda kalibrasyon pipeline'ını çalıştır (`irt_calibration_service.py` hazır, CAT döngüsüne bağlı değil). Köprü: havuz <50 soruysa subject'te CAT'ı bloke et VEYA b'ye Bayesian prior. Doğrulama: kalibrasyon önce/sonra SE<0.35 terminasyon oranı + bunching azalması.

### P0-3 — Beta-hazır havuz <%8 + gold pool rationale %0
**Boyut:** content_quality · **Kaynak:** G2-pool (verdict: REAL, metrik stale) + gap-3 (verdict: REAL, confidence 0.82)

- **Etki:** D4 migration `v_safe_for_beta`'yı sıkılaştırdı; `human_verified=0` + `auto_judged_high (15.321)` %0 rationale → gerçek beta havuzu ~0-12K, toplam 167K'nın **<%8'i.** Öğrenci "tüm YKS'ye çalışacağım" dediğinde hit rate <%8 = **özellik aldatması.** Gold pool'da "cevap neden doğru" açıklaması yok; mevcut açıklamaların %26.7'si circular/garbage → oto-öğrenme imkansız.
- **Öneri:** (a) `v_safe_for_beta` kriterini netleştir + curator ile pending'den dengeli geri-kazanım (hedef 50K+); (b) Phase 7 LLM rationale batch'ini gold pool'a (15.321) yeniden çalıştır (~$20-30), matematik prompt'unu sıkılaştır (numerik adım + yanlış şık işlem-hatası zorunlu). **Apply ÖNCESİ canlı DB sorgusuyla durumu doğrula** (kanıt 7 gün eski).

> **P0-yanı önemli not (P1'e yükseltilen):** G2-CAT-CORPUS-QUALITY — CAT havuzu sadece 2 quality status değerini ({human_verified, auto_judged_high}) filtreliyor; subject audit'leri %50-67 rejection gösteriyor (GEO %61.7, FIZ %66.7, KIM %50). Yani CAT zaten dar havuzun <%40'ından örnekliyor olabilir. P0-2 ve P0-3 çözülmeden bu da çözülmez.

---

## 4. En İyi 5 Rekabet Farklılaşma Bahsi

1. **Türkçe-kültürel ZPD/Maarif adaptif öğrenme.** Vygotsky + MEB Maarif değerleri (ulusal/evrensel/kök, öğretmen-saygı, grup çarpanları) hiçbir global rakipte yok. **Eşik şartı:** 1.15-1.25x expansion factor'leri gerçek Türk kohort verisiyle kalibre et (G6 — şu an teorik). Aksi halde farklılaşma "pazarlama" kalır.
2. **Sınav-blueprint hizalı gamification.** Jenerik XP yerine YKS-relevant XP (zayıf-subject = yüksek XP), theta-eşli duello (±0.3), subject-spesifik lig. Engagement'ı mastery'ye bağlar — rakipler eğlenceden çeker, KIRO2 öğrenme açığından çekebilir (savunulabilir kale).
3. **FSRS Türkçe kültürel takvim.** Ramazan/YKS-dönemi/bayram dinamik Hicri hesaplamayla, 10K Türk öğrenci ayarlı 17-parametre FSRS. Yerel takvime uyan tekrar zamanlaması global SRS'lerde imkansız.
4. **Kapalı-döngü sınav → öğrenme yolu adaptasyonu** (G-07 fix'li). Sınav sonrası otomatik theta recalc + "zayıf alanlara odaklan". Altyapı (theta/BKT/ZPD) var, sadece tetikleyici eksik — **düşük maliyet/yüksek getiri.**
5. **Şeffaf pedagojik gerekçelendirme** (G-03 phantom çıktı = zaten GÜÇLÜ yön). daily plan reason'da gerçek θ, FSRS sayısı, ZPD bölgesi gösteriliyor. Bunu "gör ve güven" konumlandırmasına çevir + pace-to-finish timeline (G-08). Rakipler kara kutu; KIRO2 şeffaf.

> **Uyarı:** Rekabet boyutu denetim verisiyle ölçülmedi. Bu bahisler altyapı güçlü-yönlerinden türetildi; pazar doğrulaması (gerçek rakip benchmark) **yapılmadı.** İçerik kalitesi gap'inde belirtilen "rakip ~%4-6 hata" iddiası da hiçbir kaynakta doğrulanamadı (denetim notu).

---

## 5. Fazlı Yol Haritası Tohumu (P0 → P1 → P2)

### FAZ 0 — P0 Blocker'lar (Şimdi, beta-öncesi zorunlu)

| İş | Claude Code Özelliği |
|----|----------------------|
| P0-1: /today + /status endpoint'leri + golden_flow E2E | **plan-mode** (3+ dosya) → **tdd-loop skill** (önce fail test) → **golden-flow CI gate** |
| P0-2: IRT kalibrasyon pipeline'ını CAT'a entegre | **debug-bug skill** (root cause tablosu) + **education-algorithms / irt-validation skill** (parametre doğrulama) |
| P0-3: Phase 7 rationale re-run + v_safe_for_beta netleştirme | **db-query skill** (canlı durum doğrula) → **question-quality-multi skill** → batch **workflow** |

### FAZ 1 — P1 (Beta sonrası ilk sprint)

| İş | Claude Code Özelliği |
|----|----------------------|
| G2-CAT-CORPUS: havuz kalite filtresi audit + subject bazlı CAT gating | **deep-audit skill** (paralel subagent) |
| G3-CAT-TERMINATION: subject-spesifik SE/max-item eşikleri | **education-algorithms skill** + unit test |
| G4-LEARNING-PATH: CAT response'a ZPD recommendation wire | **plan-mode** + **subagent** (facade → API şeması) |
| G-07 sınav→plan kapalı döngü tetikleyici | **feature-dev workflow** |
| G1-engagement: notification/re-engagement dispatcher (celery beat) | **api-endpoint skill** + **hook-development** (zamanlama) |
| Cevap anahtarı hatası: Tarih/Coğrafya (%31-34) curator manuel review | **db-query skill** + **MCP (Serena/dbhub)** |

### FAZ 2 — P2 (Olgunlaşma)

| İş | Claude Code Özelliği |
|----|----------------------|
| G-04 route hiyerarşisi (canonical /dashboard entry) | **component skill** (frontend) |
| G-08 pace-to-finish timeline LearningPathMap'e | **frontend-design skill** + **chrome-devtools MCP** (a11y/perf) |
| G6 ZPD expansion factor kohort kalibrasyonu (A/B) | **perf-analysis + brainstorm skill** (deney tasarımı) |
| G2/G6-engagement: blueprint-hizalı XP + theta-eşli duello | **brainstorm skill** (strateji) → **plan-mode** |
| G6-content subject tag re-classification | **turkish-nlp skill** + **deep-audit** |
| G8-content DB scaling (S179 hot-path index apply) | **db-query skill** + **MCP** (EXPLAIN ANALYZE staging) |

---

## 6. Phantom Olarak Elenen Gap'ler (Denetim Güvenilirliği İçin)

Aşağıdaki gap'ler denetim sürecinde **doğrulanamadı / yanlış çıktı**, rapora dahil EDİLMEDİ:

| ID | İddia | Neden Phantom |
|----|-------|----------------|
| G-01-AUTH-ONBOARDING | "Onboarding/hedef formu yok" | Hedef formu `/learning-path`'te mevcut (🎯 Sınav Hedefi kartı), backend endpoint'ler çalışır. İsim farklı (`goal_card`/`hedef`). |
| G-03-DAILY-PLAN-OPACITY | "Plan algoritması öğrenciye opak" | reason'da gerçek θ=0.32, FSRS kart sayısı, ZPD bölgesi gösteriliyor. Tüm pedagojik veri şeffaf. **Bu aslında güçlü yön.** |
| G5-SUBJECT-CASE-CONVENTION | "_normalize_subject lowercase yapmıyor" | Kod satır 71'de `.lower()` çağırıyor; SQL `LOWER()` kullanıyor. Olgu yanlış. |
| G7-WARM-UP-POOL-TINY | "Warm-up havuzu 30-50 soru" | SQL 4-öncelikli OR fallback cascade kullanıyor; LIMIT tüm sonuç setine uygulanıyor. Yorum hatalı. |
| gap-5 (curator saturated) | "368 pending stalled, bronze queue tıkalı" | 5 gün sonra S198'de 250 işlendi; otomasyon-destekli (SymPy+LLM), manuel curator'a bağlı değil. Stale baseline okuması. |

**Phantom oranı:** ~5 doğrulanmış phantom / ~28 incelenen iddia ≈ **%18.** Bu, KIRO2 meta-audit kültürünün (S197'de %87 phantom yakalandı) sağlıklı çalıştığını gösteriyor — adversarial verify olmasa bu 5 gap yanlışlıkla aksiyon listesine girerdi.

---

## 7. FAZ 2 — Canlı Doğrulama Sonuçları (2026-05-30, kod + MEMORY)

P0'lar kod değiştirmeden canlı koda/MEMORY'ye karşı doğrulandı. **3 P0'dan 1'i tamamen, 1'i kısmen phantom çıktı** — bu, "önce denetim, sonra karar" stratejisini doğruladı (P0-1'i "şimdi çöz" deseydik, var olan endpoint'leri yeniden yazardık).

### P0-1 — DailyPlanPage endpoint'leri "yok" → ❌ **PHANTOM (kesin)**

- `/today` + `/status` **var ve tam implemente**: `backend/app/api/learning_path_daily.py:165` (`@router.get("/today")`, response_model `DailyPlanOut`) ve `:133` (`/status`, `list[SubjectStatusOut]`).
- Prefix `:28` = `/api/v1/learning-path` → frontend'in çağırdığı path'le **birebir** (`DailyPlanPage.tsx:90-91`).
- Response şeması frontend interface'leriyle uyumlu (`DailyPlan`/`SubjectStatus`).
- **Kayıtlı**: `backend/routers/loader.py:218` → `"app.api.learning_path_daily": ("learning", ...)`; `backend/main.py:116` `setup_routers` çağırıyor.
- **Kök neden:** Audit yalnızca `learning_path_v2.py`'ye baktı, `learning_path_daily.py`'yi kaçırdı (router başka dosyada phantom'u).
- **Kalan tek belirsizlik (P3):** runtime'da 500 dönüyor mu? (orchestrator bug olasılığı) — yapısal blocker DEĞİL. Operatör smoke ile teyit edebilir: `GET /api/v1/learning-path/today` 401/200 beklenir, 404 DEĞİL.

### P0-3 — Beta pool <%8 + rationale %0 → ⚠️ **KISMEN PHANTOM**

- **"gold pool rationale %0"** → ❌ PHANTOM. MEMORY S181 (22 May): gold pool rationale kapsamı **%99.95** (auto_judged_high 15,314/15,321). Audit ajanı stale state okumuş.
- **Gerçek sorun kapsamada değil KALİTEDE**: rationale'ların **%26.7'si circular/garbage** (Phase 7 quality audit) — bu GERÇEK ve P0 değerinde.
- **"beta pool <%8"** → ✅ GERÇEK. MEMORY S197 canlı: `v_safe_for_beta = 10,535` / 167,559 = **%6.3**.
- **Düzeltilmiş P0-3:** "rationale üret" değil → **(a) v_safe_for_beta'yı büyüt (curator geri-kazanım, hedef 50K+), (b) rationale KALİTE pass'i (circular/garbage %26.7'yi düşür)".**

### P0-2 — IRT >%97 kalibre değil → 🟡 **AÇIK (1 DB sorgusu gerek)**

- MEMORY "IRT params %100 coverage" = default değerle dolu (çelişki yok). Audit iddiası: `is_calibrated=TRUE` ~598.
- **Karar için canlı sorgu gerekli** (aşağıda). MEMORY bu metriği tutmuyor.

### Karar için 2 canlı DB sorgusu (port 5434, salt-okunur)

```sql
-- P0-2: gerçekten kalibre soru sayısı + response-yeterli aday
SELECT
  COUNT(*)                                            AS total_active,
  COUNT(*) FILTER (WHERE is_calibrated)               AS calibrated,
  COUNT(*) FILTER (WHERE is_calib_pool)               AS calib_pool,
  ROUND(100.0 * COUNT(*) FILTER (WHERE is_calibrated) / NULLIF(COUNT(*),0), 2) AS calibrated_pct
FROM question_bank
WHERE is_active = TRUE;

-- P0-3: beta pool + gold pool rationale KALİTE (kapsama değil)
SELECT
  (SELECT COUNT(*) FROM question_bank WHERE quality_review_status = 'auto_judged_high') AS gold_pool,
  (SELECT COUNT(*) FROM question_bank
     WHERE quality_review_status = 'auto_judged_high'
       AND (pipeline_metadata->>'rationale') IS NOT NULL)                               AS gold_with_rationale;
```

> Not: `irt_calibration_history` tablosunda `sample_size>=30` constraint var; gerçek kalibrasyon adayı için `n_responses` kolonu (varsa) ayrıca sayılmalı. İkinci sorguda rationale'ın hangi kolonda/JSON path'te tutulduğu DB'de teyit edilmeli (`pipeline_metadata` vs ayrı kolon).

**Net sonuç:** 47/100 skoru P0-1 phantom + P0-3 yarı-phantom ile **yukarı revize edilmeli**. Gerçek beta-blocker'lar: **(1) rationale kalitesi**, **(2) beta pool büyüklüğü**, **(3) IRT kalibrasyon** (sorgu sonucuna bağlı). "Endpoint yok" diye bir blocker YOK.

---

*Rapor sentez yöntemi: Sadece `verified_gaps` (verdict_notes ile teyitli) kullanıldı. Severity, verdict_notes'taki düzeltmelerle güncellendi (G-05 P1→P0, gap-8 P2→P1). Kanıtın zayıf/eski olduğu yerler açıkça işaretlendi (gap-3 7-gün eski, rekabet boyutu veri yok, engagement JSON kesik).*

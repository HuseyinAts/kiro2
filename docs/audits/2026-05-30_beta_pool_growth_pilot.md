# Beta Pool Büyütme — Pilot Sonucu & Batch Planı

**Tarih:** 2026-05-30
**Yöntem:** unverified havuzundan subject başına ~30 soru stratified örneklem (328 soru), Claude subagent LLM-as-judge (PROMOTE / PENDING / REJECT). 4 paralel ajan, ~610K token.
**Mevcut beta pool (v_safe_for_beta):** 10,705 (%6.4) · **Hedef:** 50K+
**Not:** Workflow framework subagent'ları bu oturumda 0-token bug verdi; kanıtlanmış S198 deseni (Agent tool subagent) ile yürütüldü.

---

## 1. Pilot Sonuçları (subject bazlı)

| Subject | Judged | PROMOTE | PENDING | REJECT | promote_rate | Tam unverified | Baskın REJECT sebebi |
|---------|--------|---------|---------|--------|--------------|----------------|----------------------|
| MATEMATIK | 30 | 13 | 17 | 0 | %43.3 | 27,401 | — (muhafazakâr: emin değilse PENDING) |
| GEOMETRI | 30 | 13 | 10 | 7 | %43.3 | 3,460 | şekil/figür yok |
| FIZIK | 30 | 20 | 6 | 4 | %66.7 | 5,403 | grafik/şekil referansı yok |
| KIMYA | 30 | 23 | 6 | 1 | %76.7 | 9,684 | şekil referansı yok |
| BIYOLOJI | 30 | 25 | 4 | 1 | %83.3 | 3,700 | bozuk şık |
| TURKCE | 30 | 21 | 4 | 5 | %70.0 | 6,347 | eksik paragraf/metin |
| EDEBIYAT | 30 | 23 | 2 | 5 | %76.7 | 2,597 | eksik parça + OCR bozulması |
| TARIH | 30 | 28 | 2 | 0 | %93.3 | 2,074 | — |
| COGRAFYA | 30 | 25 | 1 | 4 | %83.3 | 494 | eksik harita/tablo |
| SOSYAL | 30 | 27 | 0 | 3 | %90.0 | 294 | eksik ayet/hadis/paragraf |
| GENEL | 26 | 8 | 2 | 16 | %30.8 | 26 | eksik paragraf + garbage |
| FEN | 2 | 1 | 0 | 1 | %50.0 | 2 | bozuk şık |
| **TOPLAM** | **328** | **227** | **54** | **47** | **%69.2** | **61,482** | |

---

## 2. Projeksiyon — Beta Pool Büyümesi

Her subject'in pilot promote_rate'i tam unverified count'a uygulanır:

| Senaryo | Yeni promote | Yeni pool toplam |
|---------|--------------|------------------|
| **Ham** (rate × full_count) | ~36,500 | **~47,200** |
| **İhtiyatlı** (×0.85 verify-iskonto) | ~31,000 | **~41,700** |

> **Sonuç: Yalnızca unverified havuzdan, 50K hedefine çok yaklaşılır (~42-47K).** En büyük katkı MATEMATIK (27K havuz, %43 oran → ~11.9K) ve KIMYA (~7.4K). MATEMATIK oranı muhafazakâr (judge "emin değilse PENDING" verdi, 17/30 pending) — gerçek promote daha yüksek olabilir.

50K'yı garantilemek için **pending havuzundan (36,517) cevap-anahtarı düzeltilmiş geri-kazanım** (A-bias fix + S182-S198 audit'leri zaten bu yönde) ek katkı sağlar.

---

## 3. Kalite Notları (dürüstlük)

- **Tek-geçiş judge**, adversarial verify çalıştırılamadı (workflow bug). S198'de aynı desen spot-check ile %95+ doğrulanmıştı; yine de promote'lar **apply öncesi spot-check** gerektirir.
- **REJECT'lerin baskın sebebi şekil/paragraf referansının metinde olmaması** — bunlar `question_image_url` ile birleştirilince (görsel %99 mevcut) bir kısmı kurtarılabilir; pilot sadece metni gördü, görseli değil. Yani REJECT oranı (%14) muhtemelen **abartılı** (gerçekte daha düşük).
- **PENDING (%16):** cevap anahtarı şüpheli — S182-S198 audit havuzuyla örtüşür, ayrı düzeltme akışı.
- Birkaç **doğrulanmış cevap-anahtarı hatası** tespit edildi (örn. BIYOLOJI #1, KIMYA #182/#184/#190) — bunlar pending'e düşürülmeli.

---

## 4. Önerilen Batch Planı (S198 pattern)

**Tam judge'ı Claude subagent ile yapmak pahalı** (328 soru ~610K token → 61K için ~115M token). Gerçek batch **Gemini Batch** ile:

| Adım | Aksiyon |
|------|---------|
| 1 | Gemini Batch judge — 61,482 unverified soru. **Maliyet ~$25** (~$0.0004/soru, gemini-flash). Görsel dahil edilirse REJECT düşer. |
| 2 | Subject öncelik: yüksek-oran + düşük-risk önce (TARIH/SOSYAL/BIYOLOJI/KIMYA), MATEMATIK en sona (en büyük + en çok pending). |
| 3 | PROMOTE → `auto_judged_high` (S198 marker + backup tablo). PENDING → curator kuyruğu. REJECT → `rejected` (görsel-kurtarma denenebilir). |
| 4 | **Apply öncesi:** subject başına 5-10 spot-check (insan onayı), backup tablo, batch UPDATE (id VARCHAR — `::uuid` cast YASAK). |
| 5 | v_safe_for_beta gate'leri (demoted/fallback/tier1_page_inline) otomatik uygulanır → gerçek pool artışı ölçülür. |

**Hızlı kazanç:** Bu pilotta zaten **227 soru PROMOTE** olarak yargılandı (id'ler kayıtlı). İstenirse spot-check sonrası hemen promote edilebilir (küçük ama sıfır-maliyet).

---

## 5. Karar Noktası

- **(A)** Gemini Batch'i kur ve tam 61K judge'ı çalıştır (~$25, GEMINI_API_KEY gerek — MEMORY: rotate beklemede).
- **(B)** Önce 227 pilot-promote'u spot-check + apply (küçük kazanç, framework doğrulama).
- **(C)** Pending havuzu (cevap-anahtarı) düzeltme akışını paralel başlat.

*Pilot verisi: `backend/scripts/quality/_beta_pool_tmp/unverified_sample.jsonl` (328 soru) + bu rapordaki promote_id listeleri.*

---

## 6. EK PİLOT — 'high'-confidence PENDING segmenti (KRİTİK BULGU)

Pending havuzu (36,517) incelendiğinde çoğunun cevap-anahtarı audit'inden değil **`beta_pool_nuke_v1` toplu demote**'undan geldiği görüldü. İçinde **25,301 soru `confidence_level='high'` + DB cevabı pipeline `best_answer` ile %100 uyumlu + %100 açıklamalı** — sözde "en güvenli geri-kazanım adayı". Bu, metadata'ya güvenilse pool'u ~3 kat (10,705→36,000) büyütürdü.

**Ama bu 'high' confidence'ı üreten pipeline A-bias bug'lıydı** (`project_a-bias-bug-fixed`). Bağımsız doğrulama için 240 soru (20/subject × 12) Claude judge ile yargılandı:

| Subject | Judged | PROMOTE | PENDING (anahtar yanlış) | REJECT |
|---------|--------|---------|--------------------------|--------|
| BIYOLOJI | 20 | 12 | 8 | 0 |
| GENEL | 20 | 12 | 7 | 1 |
| KIMYA | 20 | 10 | 7 | 3 |
| MATEMATIK | 20 | 8 | 7 | 5 |
| FIZIK | 20 | 8 | 5 | 7 |
| GEOMETRI | 20 | 7 | 4 | 9 |
| COGRAFYA | 20 | 6 | 10 | 4 |
| SOSYAL | 20 | 6 | 12 | 2 |
| FEN | 20 | 4 | 14 | 2 |
| TARIH | 20 | 3 | 17 | 0 |
| TURKCE | 20 | 2 | 13 | 5 |
| EDEBIYAT | 20 | 2 | 17 | 1 |
| **TOPLAM** | **240** | **80 (%33)** | **121 (%50)** | **39 (%16)** |

### Sonuç: 'high'-confidence pending bir RECOVERY FIRSATI DEĞİL, doğru demote edilmiş kötü havuz

- **Promote oranı %33** (unverified'in %69'unun yarısı). `beta_pool_nuke_v1` A-bias-kontamine soruları doğru hedeflemiş.
- **Eğer metadata'ya güvenip 25,301 bulk-promote edilseydi:** ~16,900 hatalı soru (yanlış anahtar %50 + garbage %16) beta pool'a girerdi → YKS ürünü için kritik hata (öğrenci yanlış cevap öğrenir).
- **Sözlü dersler felaket:** TÜRKÇE/EDEBİYAT %10, TARİH %15 promote. 115 doğrulanmış cevap-anahtarı hatası tespit edildi (doğru cevaplar `wrong_key_examples`'da kayıtlı).
- **`verify-first` bu pool'u ~17K çöp sorudan korudu.**

### Düzeltilmiş Beta Pool Stratejisi

1. **unverified (61K, %69) birincil hedef** — Gemini Batch judge → promote-only.
2. **pending-high (25K, %33) ikincil** — bulk promote YASAK; sadece per-question judge ile %33 kurtarılır. Metadata 'high' confidence güvenilmez.
3. **115+ wrong-key bonus** — judge'ların bulduğu doğru cevaplar (`_beta_pool_tmp` çıktıları) cevap-anahtarı düzeltme akışına girer (apply öncesi ikinci doğrulama + spot-check).
4. **Hiçbir bulk-promote metadata güvenine dayanamaz** — A-bias contamination kanıtlandı.

*Ek pilot verisi: `backend/scripts/quality/_beta_pool_tmp/pending_high_sample.jsonl` (240 soru).*

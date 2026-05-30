# Beyin Fırtınası — Görsel-türevli Havuz + Kapalı Görsel + Bozuk OCR Metni

**Tarih:** 30 Mayıs 2026
**Yöntem:** Çok-ajanlı brainstorm workflow (`wf_16736bc2-71d`, 11 ajan, ~9 dk). 5 uzman lensi paralel fikir üretti → her yaklaşım adversarial puanlandı (feasibility/beta-fit/quality/scalability + killer-risk) → sentez.
**Bağlam:** P0.2 araştırması sırasında bulunan kök sorun (bkz. `docs/audits/2026-05-30_yks_quality_95_roadmap.md`).

## Problem

Öğrenci görseli göremiyor (frontend suppress, `ModernOSYMExamInterface.tsx:551` `false &&`, "Bug #11" cevap-leak gerekçesi) ve yalnızca `question_text` görüyor; ama `question_text` sık bozuk/AI-paraphrase (gerçek soru çoğu kez `image_ocr_text`'te). Cevap %96 doğru olsa bile öğrenci **soruyu okuyamıyor**. Beta kalitesi tamamen OCR-metin sadakatine bağlı, ve metin bozuk. Gold pool 13,595 / v_safe_for_beta 10,705 = **%100 has_image**.

## ⚠️ Kritik phantom: "tüm görseller leak" premise'i doğrulanmamış

İki ideation ajanı **canlı crop çekti ve cevap-leak GÖRMEDİ.** Bug #11 (18 May 2026) tüm görselleri kapattı ama bu premise spot-check'siz genelleme olabilir. Eğer leak <%100 ise, görseli geri açmak (re-OCR'dan çok daha basit) en büyük kazanç. **Faz 0 bunu ölçer — her şeyin önündeki kapı.**

## Önerilen Yol Haritası (sıralı, hibrit)

| Faz | Aksiyon | Effort | Beta'yı açar | Süre |
|-----|---------|--------|--------------|------|
| **0 — Ölçüm kapısı** | DB'den ölç: (a) gold pool'da `image_ocr_text` NULL-olmayan oran, (b) 100 random crop'ta GERÇEK leak oranı (Bug #11 premise doğrula). Truncate yok. | S | — | 1 gün |
| **1 — Quick win: best_text** | Backend serializer'a kalite-bazlı `best_text` ekle (`image_ocr_text` doluysa + `question_text`'ten temizse → uzunluk + Türkçe-kelime-oranı + LaTeX-bozukluk skoru). Frontend zaten `cq.content\|\|cq.question_text` fallback yapıyor, oraya besle. Aynı anda `cat_session.py:247/283` dup regex'i tek helper'a taşı (DRY). | M | ✅ | 3-5 gün |
| **2 — Temiz beta çekirdeği** | `_beta_pool_tmp` verify-first workflow'unu ölçekle: gold pool subject-bazlı JSONL → her soruya "görsel OLMADAN çözülebilir mi? solvable/needs_image/garbage" judge (S198 6-paralel Claude subagent, $0). solvable→beta_clean, diğeri→pending/rejected. %5+ insan spot-check ZORUNLU. | M | ✅ | 3-5 gün |
| **3 — Kalıcı %95: Vision re-gen** | `metadata_phase7_batch_gemini.py`'a image-part wiring (Files API per-image, batch 5K'ya böl). Prompt: crop'tan temiz question_text + 5 seçenek çıkar, "işaretli cevabı DAHİL ETME". correct_answer DB ground-truth kalır. Pilot 50 W4r pixel-onay → %95+ ise full UPDATE+backup. parse_fail retry (16K token + responseMimeType:json + temp 0.1). | XL | — (paralel/sonrası) | 2.5-3.5 hafta |
| **4 — Koşullu: leak-safe re-crop** | SADECE Faz 0 leak<%100 çıkarsa: figür-şıklı vs text-şıklı sınıflandır, text-şıklılarda option-band y-tespiti + crop ile gövde-only görsel üret, `false &&` kaldır. Figür-şıklı (geo/grafik) sorular beta-safe'den dışarıda. | L | — | post-beta |

## Quick Win (en hızlı + en güvenli)

**`best_text` serializer:** `image_ocr_text` doluysa ve `question_text`'ten daha temizse (uzunluk + Türkçe-kelime-oranı + LaTeX-bozukluk skoru) onu seç, frontend'in mevcut `cq.content||cq.question_text` fallback'ına besle. **Görsel kapalı kalır → sıfır leak riski, $0 API, ~12-18 insan-saat**, mevcut 42-sample kör consensus ile A/B doğrulanır. Tek dosya yüzeyi.

## Long Game (kalıcı %95)

Vision full re-gen (Faz 3): crop'tan temiz metin+şık sıfırdan üret, leak'i prompt-seviyesinde ele, correct_answer DB ground-truth. "İki bozuk metinden iyisini seçme" tavanını aşan tek yol. Vision'ın da yanıldığı çekirdek-zor azınlık (küçük-font) için W4r upscale + Curator manuel kuyruğu residual'a.

## Reddedilenler (KISS disiplini)

- **Blur-reveal (CSS client-side):** DevTools "remove style" leak'i anında gösterir — güvenlik tiyatrosu, server-side çözmez.
- **Sıfırdan re-detect / tam-sayfa re-crop:** 3-4 hafta + 405 kitap NTFS yavaş + $40-80; mevcut meta.json bbox zaten YOLO q-detection (>0.7 conf) — Karpathy sadelik ihlali.
- **Sabit-oran gövde crop (ön-koşulsuz):** per-soru option-band y-koordinatı deterministik değil; figür-şıklı sorularda şık diyagramı DB-text'ten render edilemez.
- **Vision re-gen + auto leak-safe crop tek pakette:** bbox halüsinasyonu = leak sızar; 13.6K'ya W4r pixel-onay ölçeklenmez. Metin (Faz 3) ile crop (Faz 4) ayrıldı.
- **Regex tek-başına sertleştirme:** beta_eligible_filter_v2 R5a/R5b İPTAL dersi — rule-based bozuk-metin tespiti yanlış-pozitif (meşru fill-in-blank elenir); AI-paraphrase gramer-sağlıklı bozuk metni regex asla yakalamaz.

## Açık Sorular (Hüseyin kararı)

1. **Beta min soru sayısı?** best_text+judge sonrası temiz havuz ~10.7K'nın altına (örn. 5-7K) düşerse subject/difficulty kapsama yeterli mi, yoksa Faz 3 beta-blocker'a mı döner?
2. **Leak-tolerans:** Faz 0 leak'i örn. %30 bulursa, leak-free %70'i görselli açmak kabul edilebilir mi, yoksa SIFIR leak zorunlu mu?
3. **Bütçe:** Faz 3 vision re-gen ~$25-60 (Flash) + ~25-35 insan-saat; Pro'da 8-10×. Tavan? Beta-önce mi sonra mı?
4. **GEMINI_API_KEY rotate (AUP P0)** ne zaman? Faz 2 judge $0 (Claude subagent) ama Faz 3 vision için geçerli key şart — rotate beta takvimini blokluyor mu?
5. **Diagram-gerçekten-gereken sorular** (geometri şekli, grafik) beta v1'den tamamen çıkarılsın mı yoksa Faz 4 beta-blocker mı?

---

*Workflow run: wf_16736bc2-71d. Sonraki adım: Faz 0 ölçüm kapısı (image_ocr_text coverage psql + 100-crop leak spot-check).*

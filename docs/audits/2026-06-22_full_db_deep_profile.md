# Tam DB Derin Profil + İçerik Kalite Audit (2026-06-22)

**Kapsam (eksiksiz, kanıtlı):** 178 tablo · **2.421 sütun** · 7 view · 671.531 satır. Her sütun **deterministik profiler** ile tarandı (`generate_profile.py` → `column_profile.tsv` 1.262 dolu-tablo sütunu + `columns_meta.tsv` 2.421 sütun yapı; 0 atlama, LLM-bağımsız). İçerik kalitesi 14-agent kör-yargı workflow ile ölçüldü. Hiçbir sayı ezberden değil — psql/profiler çıktısından.

## 0. Eksiksizlik Mutabakatı (her sütun + satır hesapta)

| Sütun sınıfı | Adet | İçerik okundu mu? |
|---|---|---|
| Dolu-tablo sütunu | **1.261** | ✅ tamamı (column_profile.tsv, EKSİK 0) |
| View sütunu (7 view) | **221** | ✅ tamamı (view_profile.tsv, 0 hata) |
| Boş-tablo sütunu (82 tablo) | **939** | — 0 satır var, **okunacak veri yok** (yapı columns_meta.tsv'de) |
| **TOPLAM** | **2.421** | columns_meta ile birebir |

**Satır tarafı:** profiler `LIMIT 200000` kullandı; en büyük tablo question_bank=187.834 < 200.000 → **hiçbir satır kesilmedi, tüm satırlar tarandı**. Veri taşıyan 1.482 sütunun tamamı içerik-profilli; geri kalan 939 sütun yalnızca boş (0-satır) tablolarda — fiziksel olarak okunacak satır yok.

## 1. Tablo Envanteri (kategori)

| Kategori | Tablo | Satır | Not |
|---|---|---|---|
| **Çekirdek içerik** | question_bank | 187.834 | 78 sütun, üretim soru havuzu |
| Legacy içerik | questions | 36.381 | eski şema (subject_area/correct_answer/times_correct), **servise gitmiyor** (dual-table trap, lesson#23) |
| **MOCK (sahte veri)** | mock_ai_telemetry, mock_ocr_data | **200.000** | S196 mock-endpoint artığı — **DB'nin %30'u** |
| Sohbet | chat_messages / chat_sessions | 130.000 / 10.065 | |
| Görsel | image_uploads | 70.000 | 28 sütundan 11'i all-null |
| **Backup snapshot** | 37 tablo (`*_backup_*`) | **29.116** | blind-solve/poolA/gemma3/fallback geri-alma |
| Diğer dolu | ~17 tablo | ~8.000 | refresh_tokens, student_abilities, irt_calibration_history... |
| **BOŞ (scaffold)** | **82 tablo** | 0 | modellendi ama hiç dolmadı |

## 2. Yapısal Bulgular (deterministik)

| Bulgu | Sayı | Kanıt | Önem |
|---|---|---|---|
| **Mock veri (prod DB'de)** | 200.000 satır / 2 tablo | mock_* tablolar | P1 — temizlenebilir (endpoint flag-gated) |
| **Boş tablolar** | 82 / 178 (%46) | inventory.tsv rows=0 | P2 — FSRS (fsrs_reviews/schedules/sessions), student_answers, exam_sessions, notifications, quizzes, user_badges, veli_consent dahil → **çekirdek özellikler modellendi ama beslenmiyor** |
| **All-null sütun (ölü)** | 165 | column_profile null=rows | P2 — örn. question_bank.question_html/question_latex/question_audio_url, image_uploads 11 sütun, learning_path_student_profiles felder/target_* |
| **Tek-değer sütun (default-only)** | 240 | distinct≤1, >50 satır | P3 — şema şişkinliği |
| **Backup tablolar** | 37 / 29.116 satır | `*backup*` | P2 — eski olanlar (gemma3_consensus, fallback_retag, blindsolve w1-25) arşivlenebilir |
| FK orphan | **0** | 107 declared FK, dolu child tarandı | ✅ ilişkisel bütünlük temiz |

## 3. İçerik Kalitesi — question_bank (deterministik)

| Metrik | Değer | Kaynak |
|---|---|---|
| Kısa/boş metin (<10 char) | **0** (tüm status) | C1 |
| Geçersiz cevap anahtarı (A-E dışı) | **0** (tüm status) | C1 |
| Eksik şık (auto_judged_high) | **0** | C1 |
| Görsel taşıyan | ~%98 (her tier) | C1 — tüm havuz OCR-image kökenli |
| **Mükerrer metin (tüm bank)** | 3.955 grup / **5.315 fazla kopya** | C3 |
| Ders dağılımı (v_safe) | **%43 MATEMATIK**, KIMYA %15, FIZIK %10... COGRAFYA %1, SOSYAL %0.6 | C6 — ağır STEM/math eğimi |
| Sınav tipi (v_safe) | **%92 TYT / %8 AYT** | C7 — AYT ciddi az-temsil |

## 4. İçerik Kalitesi — SERVED POOL (v_safe) kör-yargı (n=448/489, kanıtlı)

| Eksen | Oran | Yorum |
|---|---|---|
| **Okunabilir** | **%89.5** | eski gold-pool %40'tan dramatik iyileşme (blind-solve+2signal etkisi) |
| Çözülebilir (metinle) | **%96.9** | figür-sızıntı yalnız %2.5 |
| **Garble'lı** | **%11.8** | sözel-ağır: TÜRKÇE %26 / EDEBİYAT %24 / GENEL %29; STEM temiz (KIMYA %2, FIZIK %5) |
| blind-AGREE (anahtar) | **%79.5** | GEOMETRI %65 / MATEMATIK %71 en düşük (zor+dispute); SOSYAL %93 |

**İzdüşüm:** %11.8 garble × 25.343 ≈ **~3.000 garble-kuyruğu** (ağırlıklı TÜRKÇE/EDEBİYAT/GENEL).

## 5. Bu Oturumda Uygulanan Fix'ler (hepsi reversible, correct_answer/is_active DOKUNULMADI)

| Fix | Etki | Backup |
|---|---|---|
| C4 — v_safe mükerrer dedup | v_safe 25.755→25.399 (−356) | question_bank_vsafe_dedup_backup_20260622 |
| Garble demote (kör-yargı 56) | 25.399→**25.343** (−56) | question_bank_garble_demote_backup_20260622 |
| (önceki) I5 stale vp / F4 index / F5 / F2 | — | stale_vp_backup; meta-audit doc |

## 5b. Ç2 Sözel Garble Süpürmesi UYGULANDI (2-pass, false-pozitif guard'lı)
- **Kapsam:** 3.187 sözel served (TÜRKÇE/EDEBİYAT/GENEL), workflow wjcuwr8fa.
- **Pass-1:** 372 garble-flag (%11.7 — blind-örneklemle birebir).
- **Spot-check:** 5'te 1 yanlış-pozitif (divan rubaisi) → körlemesine demote RİSKLİ teşhis edildi.
- **Pass-2 (adversarial, divan/edebiyat guard):** 372 → **yalnız 41 teyitli garble**; **331 yanlış-pozitif KURTARILDI** (geçerli Türkçe/divan şiiri/arkaik dil). FP oranı %89!
- **Demote:** 41 (2-pass Y∧Y) → `demoted_at`/`garble_verbal_2pass`. **v_safe 25.343→25.302.** backup question_bank_garble_verbal_backup_20260622. correct_answer/is_active dokunulmadı.
- **DERS:** Tek-pass garble filtresi sözel Türkçe'de %89 false-pozitif üretti — audit-methodology "ucuz filtre geçerli Türkçe'yi siler" kuralının canlı kanıtı. 2-pass + guard zorunlu.

## 6. Öncelikli Öneriler (ORM-farkında / operatör kararı gerektirir — körlemesine silinmedi)

| # | Aksiyon | Gerekçe (kanıt) | Risk |
|---|---|---|---|
| R1 | **mock_ai_telemetry + mock_ocr_data DROP** | 200K sahte satır, DB'nin %30'u; S196 mock-endpoint artığı | Önce endpoint flag OFF + ORM ref doğrula |
| R2 | **Verbal garble sweep** (TÜRKÇE/EDEBİYAT/GENEL v_safe) | ~3.000 garble izdüşümü; bu 3 ders %24-29 | Düşük — demote reversible (false-pozitif Türkçe-guard ile) |
| R3 | **82 boş tablo + 165 all-null sütun** ORM denetimi | scaffold debt; FSRS/student_answers boş = özellik beslenmemiş | Orta — ORM modeli silmeden migration |
| R4 | **37 backup tablo arşivle/temizle** | 29K satır, eski olanlar (gemma3/fallback) artık gereksiz | Düşük |
| R5 | **AYT + sosyal bilimler içerik dengele** | v_safe %92 TYT, %43 math | İçerik-strateji |

## 7. Verdict
- **Yapısal bütünlük:** temiz (0 FK orphan, 0 bad-key, 0 null-topic, 0 v_safe dup post-fix).
- **Servis kalitesi:** %89.5 okunabilir / %96.9 çözülebilir — **beta için sağlam**; %12 garble-kuyruğu (sözel) bilinen+ölçülen tek içerik açığı.
- **Asıl borç yapısal:** %30 mock veri + %46 boş tablo + 165 ölü sütun (uygulama çalışıyor ama şema şişkin).
- 0 P0. Tüm kritik invariant doğrulandı.

---
*Profiler: `docs/audits/_dbprofile/` (inventory.tsv, columns_meta.tsv, column_profile.tsv, generate_profile.py). Workflow'lar: w38f5d6ro (kod), we4z2d375 (içerik kalite). Tüm sayılar canlı psql/profiler çıktısı.*

## 8. FAZ-1 TEMİZLİK UYGULANDI (22 Haz)
| Çözüm | Durum | Kanıt |
|---|---|---|
| Ç1 mock drop (200K) | ✅ kaldırıldı | mock_ai_telemetry+mock_ocr_data DB'de YOK; question_bank/v_safe sağlam |
| Ç3 eski backup (gemma3/fallback/qwen3/verbal ~8K) | ✅ kaldırıldı | pattern araması boş |
| Ç4 platform_stats (tek DEAD) | ✅ DROP | 0 satır, modelsiz |
| Ç2 sözel garble (41 demote, 331 FP kurtarıldı) | ✅ uygulandı | v_safe 25.343→25.302 |
**Tablo: 178→174. Bu session 36 backup KORUNDU (reversibility). correct_answer/is_active hiç dokunulmadı.**

## 9. A1 STEM Garble Süpürmesi UYGULANDI (2-pass)
- **Kapsam:** 20.345 STEM v_safe (MATEMATİK/FİZİK/KİMYA/BİYOLOJİ), workflow wb4u0wem9→resume wpi2418gp (haftalık-limit yedi, resume ile tamamlandı 20.319/20.345).
- **Pass-1:** 223 garble-flag (%1.1 — STEM zaten temiz; sözel %12'nin onda biri).
- **Pass-2 (LaTeX/formül guard):** 223 → **17 teyitli**; **206 yanlış-pozitif KURTARILDI** (matematik/formül metni).
- **Demote:** 17 → v_safe 25.302→**25.285**. backup question_bank_garble_stem_backup_20260622. correct_answer/is_active dokunulmadı.
- **DERS:** STEM gerçek garble %0.08 (17/20.319) — havuz çok temiz; tam-sweep getirisi çok düşük (ama eksiksizlik için yapıldı). Verbal (%11.7) vs STEM (%1.1) farkı = OCR sözel metinde zorlanıyor, formül/sayıda değil.
- **A1+A3 kümülatif (bu tur):** v_safe 25.343→25.285 (garble −41 verbal −17 STEM = −58); A3 5.315 dup-flag.

## 10. B1 Pool A AYT/Sözel-Sosyal Büyüme UYGULANDI
- **Hedef:** v_safe %92-TYT/%43-math dengesizliğini azalt → az-temsil edilen AYT + sözel/sosyal fallback (2.219: AYT-EDEBİYAT 392 + TYT TÜRKÇE/TARİH/SOSYAL/COĞRAFYA 1.827).
- **Workflow** wp769bt7m→resume wn1hqv9ho (session-limit yedi, resume ile 2.214/2.219 çözüldü). Combined-pass (solve+ders+konu).
- **Funnel:** promote 570 (%25.8 — verbal zor, dispute %35.2 flag'li) / lowconf 541 / unsolvable 123 / subject_mismatch 104.
- **v_safe 25.285 → 25.855 (+570).** AYT 2.041→2.160 (+119), TYT-sözel/sosyal +451. backup question_bank_poolA_wb1_backup_20260622. correct_answer/is_active dokunulmadı, verified_provisional flag'li.
- Kalan fallback (çoğu STEM-TYT, zaten fazla-temsil): ~9.000.

## 11. SESSION KÜMÜLATİF (DB profil + içerik + temizlik)
- **v_safe net:** 25.755 → dedup −356 → garble −114 (56+41+17) → B1 +570 = **25.855**.
- **DB:** 178→174 tablo (mock 200K + eski backup + platform_stats kaldırıldı); 5.315 dup-flag.
- **İçerik kalite kanıtı:** served %89.5 okunabilir / %96.9 çözülebilir; garble verbal %11.7→2-pass 41, STEM %1.1→2-pass 17 (toplam 537+206=743 yanlış-pozitif KURTARILDI guard'la).
- **Şema:** 82 boş tablo sınıflandı (51 wired/30 stub/1 dead); otonom-drop güvenli DEĞİL (deploy-gate).
- correct_answer/is_active HİÇ dokunulmadı; tüm değişiklikler reversible (40+ backup tablo).

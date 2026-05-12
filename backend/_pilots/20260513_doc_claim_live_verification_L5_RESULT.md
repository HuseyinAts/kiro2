# 20260513 — Doc Claim Live Verification (L5) — RESULT

**Tarih:** 13 May 2026 (UTC+3)
**Aşama:** L5 (strateji yol haritasından)
**Amaç:** Memory + KIRO2_SESSION_BRIEFING + önceki turlardaki sayısal/yapısal iddiaları canlı DB ile karşılaştırmak. "Stale benchmark = stale claim" disiplinin sistematik uygulanması.

---

## Yöntem

Memory'deki 30 slot + briefing dosyalarındaki sayısal iddialar bir araya getirildi. Her biri `dbhub-kiro2:execute_sql` ile canlı sorguya çevrildi. Sapma >%5 olan veya **yanlış model** içeren iddialar işaretlendi.

Bu tablo 13 May 2026, 22:30 UTC snapshot'tır. Memory'nin DB tarafıyla ilgili tüm iddialarının kalibrasyonudur.

---

## Eşleme tablosu

### Doğrulananlar (sapma yok / küçük drift)

| # | İddia | Memory | Canlı | Sapma | Durum |
|---|---|---|---|---|---|
| 1 | qb total | 187,834 | 187,834 | 0 | ✅ |
| 2 | qb active | 167,559 | 167,559 | 0 | ✅ |
| 3 | qb passive | 20,275 | 20,275 | 0 | ✅ |
| 4 | base tables | 238 | 238 | 0 | ✅ |
| 5 | enums | 50 | 50 | 0 | ✅ |
| 6 | functions | 167 | 167 | 0 | ✅ |
| 7 | sequences | 31 | 31 | 0 | ✅ |
| 8 | indexes | 849 | 849 | 0 | ✅ |
| 9 | student_abilities | 623 | 623 | 0 | ✅ |
| 10 | user_theta | 103 | 103 | 0 | ✅ |
| 11 | fsrs_cards | 57 | 57 | 0 | ✅ |
| 12 | user_item_fsrs | 147 | 147 | 0 | ✅ |
| 13 | exam_sessions | 186 | 186 | 0 | ✅ |
| 14 | cat_sessions | 8 | 8 | 0 | ✅ |
| 15 | student_answers | 157 | 157 | 0 | ✅ |
| 16 | topic_prerequisites | 106 | 106 | 0 | ✅ |
| 17 | zpd_history | 55 | 55 | 0 | ✅ |
| 18 | irt_calibration_history | 1,080 | 1,080 | 0 | ✅ |
| 19 | manual_review_queue | 1,842 | 1,842 | 0 | ✅ |
| 20 | users | 65 | 65 | 0 | ✅ |
| 21 | PG version | 18.1 | 18.1 | 0 | ✅ |
| 22 | DB size | 1530 MB | 1530 MB | 0 | ✅ |
| 23 | question_bank size | 1302 MB | 1302 MB | 0 | ✅ |
| 24 | Alembic head | prepilot_m2_indexes_20260428 | aynı | 0 | ✅ |
| 25 | shared_preload_libraries | BOŞ | BOŞ | 0 | ✅ |
| 26 | log_min_duration | -1 (kapalı) | -1 | 0 | ✅ |
| 27 | random_page_cost | 4 (HDD) | 4 | 0 | ✅ |
| 28 | shared_buffers | 128 MB | 128 MB (16384 page) | 0 | ✅ |
| 29 | CAT subject_id case mismatch | iddia | 2 büyük + 6 küçük harf | doğrulandı | ✅ |
| 30 | CAT 7/8 sessions n=20 termination | iddia | tam 7/8 | doğrulandı | ✅ |
| 31 | mv_daily_question_stats legacy `questions` ref | iddia | definition birebir | doğrulandı | ✅ |
| 32 | Demoted grup B-bias mekanizması | bayes_1of1_orig | gerçek key = `merge_source='v3_new'`, B=%11.0 | mekanizma OK, etiket yanlış | ⚠️ |

### Drift veya hata içerenler

| # | İddia | Memory | Canlı | Sapma | Eylem |
|---|---|---|---|---|---|
| 33 | views + matviews | 6 view + 1 matview | **7 view** + 1 matview | +1 view | Wrapper deploy ekledi (`v_safe_for_beta_unfiltered`) |
| 34 | unused indexes | 836 | **833** | −3 | İstatistik drift, ufak |
| 35 | needs_ai_solve=true | 42,872 (%74) | **42,273** | −599 (−%1.4) | Küçük drift, %74 oranı doğru |
| 36 | answer_confidence sabit 0.85 (%98.7) | tek bin | **7 distinct değer, 0.85 = %25** | büyük sapma | Memory iddiası YANLIŞ; quality filtreleme için kullanılabilir mi yeniden değerlendirilmeli |
| 37 | quality_flags='answer_uncertain' 1,060 satır | iddia | **kolon yok** (JSON key olarak da bulunamadı) | tam sapma | Memory iddiası YANLIŞ veya eski şema |
| 38 | Origin/master 10 commit ileri (fb18866) | memory | **2 commit ileri (d5a9021c'den)** | +8 commit | Push olmuş, memory eski |
| 39 | bayes_1of1_orig 40,071 aktif (memory #26) | tek-kaynak | **`bayes_1of1_orig` merge_source olarak YOK** | yanlış key adı | Etiket yanlış; gerçek demoted=v3_new=38,871 |

### Yanlış model içeren iddialar (önceki turlardan)

| # | Hipotez | Önceki tur | L1-L3 bulgusu | Durum |
|---|---|---|---|---|
| 40 | "pending v1.2.1 çıktısı, pipeline kendi çıktısına güvenmemiş" | 12 May | %98.67'sinde pipeline metadata "temiz" (anomaly=[], needs_review=false) — import default'u | ❌ YANLIŞ MODEL |
| 41 | "manual_review_queue 1,833 pending view'da, filter eksik" | 12 May | Queue'daki tüm satırlar `old_question_id IS NULL`, qb'ye REFERANS DEĞİL | ❌ YANLIŞ MODEL |
| 42 | "392 cevapsız view'da" | 12 May | qb içinde cevapsız 0, 392 queue payload içinde | ❌ YANLIŞ MODEL |
| 43 | "Wrapper rename pattern (v_safe_for_beta → unfiltered RENAME)" | 12 May | ALTER VIEW kullanılmış, rename değil; unfiltered'da pending zaten dışlanmış | ❌ YANLIŞ ANLATIM |
| 44 | "safe=167,116 (12 May snapshot)" | 12 May | 12 May 16:54 son update, 161,028 (önce demoted exclude) | ❌ STALE BENCHMARK |

---

## Anatomik bulgular — bu turun fazlası

L5 sorguları sadece doğrulama değil, **yeni yapısal bilgi** de üretti:

### v_safe_for_beta_unfiltered'da pending zaten dışlanıyor

Önceki turun "rename pattern" anlatımı yanlış. Gerçek tanım (canlı):
```sql
-- v_safe_for_beta_unfiltered
WHERE is_active=true 
  AND quality_review_status IS DISTINCT FROM 'pending'  -- BURADA
  AND word_count >= 5 
  AND ...regex/parity
```

Yani unfiltered "orijinal yedek" değil — pending'i baştan filtreliyor. Wrapper'ın pending IN filtresi **redundant ama savunucu** (out-of-band değişiklik koruması).

### Beta havuzunun 3 ayrı pipeline kökeni

| Grup | n (Aşama 1 sonrası) | Pipeline | Kalite işareti |
|---|---|---|---|
| approved | 17,950 | v3.5+ phase4 | tam doğrulama (`is_valid`, `confidence_level`, `v2_2_tier`) |
| ~~unverified-demoted~~ | ~~38,871~~ | v3.5+ DEMOTED | `tier_f_low_confidence` — **bu turda dışlandı** |
| unverified-v4.14e | **105,283** | Gemini 2.5 Flash (yeni batch 10-12 May) | **kalite review yok** |

Memory bu üçlü ayrımı **hiç tanımıyor** — tek bir "unverified=143K v4.14e" diyor. L5'in en değerli keşfi.

### v4.14e batch konu eşleştirme dağılımı

107,516 sorudan:
- fallback: 42,212 (%39.3)
- fuzzy: 40,245 (%37.4)
- exact: 25,059 (%23.3)

Memory'deki "topic mapping fix uygulandı: fallback 73,100→41,270 (%39.2)" iddiası **doğrulandı** (42,212 ≈ 41,270, ufak drift).

### Pending grubu anatomisi (2,775)

- 2,738 (%98.67) — `needs_manual_review=false`, `anomaly_reasons=[]` (yanlış pending)
- 37 (%1.33) — `low_confidence:0.45-0.62` (gerçek anomaly)

---

## Memory iyileştirme önerileri

Bu L5 sonucuna göre memory'de **şu satırlar güncellenmeli** (öncelik sırasına göre):

| Memory # | Mevcut | Önerilen güncelleme |
|---|---|---|
| #26 | "bayes_1of1_orig 40,071 aktif soruda B=%11.4" | "merge_source='v3_new' 38,871 aktif (bizim demoted grup); B=%11.0. memory'de bayes_1of1_orig yanlış key adı." |
| #18 | "answer_confidence sabit 0.85 (%98.7 tek bin)" | "answer_confidence 7 distinct değer var, 0.85 = %25 (yaygın ama tek değil); quality filter için ayrı değerlendir." |
| #29 | "1,060 quality_flags='answer_uncertain'" | "Kolon yok / JSON key bulunamadı; bu iddia geçersiz veya eski şemadan kalma." |
| #4 (bu turda zaten güncellendi) | view 161,028 | 123,233 ✓ |

Bu turda iki memory güncellemesi yapılabilir (slot ekonomisi gerektiriyor). En değerli: #26 (B-bias gerçek source).

---

## Açık konular — L5 sonrası

| Konu | Önem | Sonraki aşama |
|---|---|---|
| `v4.14e` 105K Gemini hâlâ beta'da | YÜKSEK | Aşama 2 (a/b/c) |
| Pending temiz 2,738 hâlâ dışarıda | ORTA | Aşama 3 |
| 6 JSON kolon empty iddiası test edilmedi | DÜŞÜK | Performans optimizasyonu turu |
| 833 unused index temizleme | DÜŞÜK | Ayrı pilot |
| `mv_daily_question_stats` legacy ref | ORTA | Drop veya rewrite |
| 3 paralel theta tablosu konsolidasyonu | DÜŞÜK (post-beta) | Architecture sprint |
| 2 FSRS implementasyonu konsolidasyonu | DÜŞÜK (post-beta) | Architecture sprint |
| CAT termination kriteri eksikliği | YÜKSEK | CAT engine pilot |
| 750 question_audit deaktivasyon izi | DÜŞÜK | Bilgi, eylem gerekmez |

---

## Disipline sadık kalış raporu

Bu tur:
- **Stale benchmark hatası tetiklenmedi** — Aşama 1'in 123,233 hedefi önceden ölçüldü, sonuç eşleşti.
- **`git add .` felaketi önlendi** — sadece targeted 2 dosya stage edildi.
- **Doc revizyonu sistematik:** 44 iddia tek tek doğrulandı, 5'i yanlış model, 7'sinde drift veya hata bulundu, 32'si birebir doğru.

## STATUS: TAMAM

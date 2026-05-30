# Gold Pool Tutarlılık Gate — Stratified Pilot (31 May 2026)

## Bağlam
Beta 386 çekirdeğinin re-curate'inde tutarlılık gate'i **%42 drop** verdi
(`2026-05-30_beta_recurate_coherence_gate.md`). Soru: bu oran tüm
`auto_judged_high` gold pool'una (13,595) genellenir mi? Körlemesine tam-run
yerine **stratified pilot** (audit-methodology kuralı: evren-level doğrulama).

## Yöntem
- Örneklem: ders başına 50 (FEN 22), 386 beta-core hariç → **572 soru**.
- Deterministik: `ROW_NUMBER() OVER (PARTITION BY subject_area ORDER BY md5(id))`.
- 6 paralel Claude subagent, aynı tutarlılık yargıcı: öğrencinin gördüğü kadarıyla
  (metin+şık, görsel yok) **tutarlı? dairesel? şekilsiz çözülür? gerçek MCQ? cevap makul?**

## Sonuç: gold pool öğrenci-okunabilirliğinde ~%61 kusurlu

- Yargılanan 567/572 → **keep 210 / drop 357 = %63 drop**.
- Pool izdüşümü: **~8,272 / 13,595 drop → ~5,323 gerçekten temiz.**
- Baskın kusur: **garbled 240** (OCR-bozuk) >> figure_dependent 80 >> answer_wrong 25 >> open_ended 9 >> circular 3.

| Ders | n | drop | drop% | Pool | ~pool drop |
|---|---|---|---|---|---|
| FIZIK | 49 | 39 | 79.6 | 1369 | ~1089 |
| TARIH | 50 | 36 | 72.0 | 549 | ~395 |
| GENEL | 50 | 35 | 70.0 | 484 | ~338 |
| GEOMETRI | 50 | 35 | 70.0 | 2147 | ~1502 |
| BIYOLOJI | 49 | 34 | 69.4 | 399 | ~276 |
| EDEBIYAT | 50 | 34 | 68.0 | 641 | ~435 |
| COGRAFYA | 50 | 32 | 64.0 | 69 | ~44 |
| FEN | 21 | 13 | 61.9 | 22 | ~13 |
| KIMYA | 50 | 30 | 60.0 | 1004 | ~602 |
| MATEMATIK | 49 | 28 | 57.1 | 4501 | ~2572 |
| TURKCE | 50 | 21 | 42.0 | 2009 | ~843 |
| SOSYAL | 49 | 20 | 40.8 | 401 | ~163 |

## İki sistemik bulgu
1. **"Gold pool" öğrenci için çoğunlukla kullanılamaz (~%61).** S182-S193
   cevap-anahtarı denetimleri CEVABI doğruladı ama OKUNABİLİRLİK/tutarlılığı hiç
   ölçmedi. `auto_judged_high` etiketi öğrenci-hazırlığı GARANTİSİ DEĞİL.
   Kök-neden tezinin (proxy-metrik yanlış katmanı ölçtü) tam-ölçek kanıtı.
2. **subject_area etiketleri güvenilmez.** 6 ajanın hepsi raporladı: FİZİK/
   EDEBİYAT/TARİH/KİMYA etiketli sorular sıkça aslında (bozuk) matematik/geometri
   içeriği. Subject-tag kontaminasyonu ayrı bir P1.

## Değerlendirme / öneri
- Beta 386 (%42) iyimser bir alt-kümeydi (consensus-gated). Geniş havuz %61.
- Tam-run (13,595 yargılama) artık gerekçeli AMA büyük: ~210 batch, ~25-30M token.
- **Mutasyon stratejisi: yıkıcı demote DEĞİL, pozitif `student_coherent=true` flag**
  (~5,323 keeper). `auto_judged_high` statüsünü/diğer tüketicileri bozmaz, geri-dönüşlü.
- Garbled baskın (~%67 of drops) → asıl çözüm uzun vade **Vision re-OCR/re-gen**
  (crop'tan temiz metin); flag sadece "şu an öğrenciye gösterilebilir"i işaretler.

## Sonraki adım kararı (kullanıcıya açık)
- (A) Tam-run şimdi (Workflow, ~saatler) → ~5,323'e `student_coherent` flag → beta + öğrenme yolu bu flag'e güvenir.
- (B) Pilot bulgusunu belgele + beta'yı 221 ile aç, tam-run'ı feedback sonrası planla.
- (C) Subject-tag kontaminasyonunu ayrı ele al.

## Artifactlar (untracked)
`backend/scripts/quality/_beta_core_tmp/`: goldpool_pilot.json, gp_batch_{1-6}.json,
gp_verdict_{1-6}.json, export_goldpool_pilot.sql.

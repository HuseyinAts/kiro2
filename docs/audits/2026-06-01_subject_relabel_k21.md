# K21 Subject Relabel — 1,251 subject_mismatch (2-sinyal)

**Tarih:** 2026-06-01
**Amaç:** verified_core'un işaretlediği subject_mismatch (blind_true_subject) — gold pool'da
yanlış kategoride sorular (MAT→GEO, TURKCE→MAT vb.). 2. bağımsız kör subject-classification
ile teyit edip `subject_area` düzelt.

## Güvenlik ön-kontrolü (kritik)
DB'de geçerli `subject_area` değerleri: MATEMATIK, GEOMETRI, FIZIK, KIMYA, BIYOLOJI, TURKCE,
EDEBIYAT, TARIH, GENEL, SOSYAL, COGRAFYA, FEN (+ TDE/INGILIZCE tiny). **FELSEFE ve DIN DB'de
subject_area DEĞİL** (sistem SOSYAL şemsiyesi). → bunlara relabel downstream'i bozardı, hariç tutuldu.

## 2-sinyal konsensüs
Sinyal 1: blind_true_subject (verified_core). Sinyal 2: yeni kör classify (Workflow
`wf_96d7bb8f-04c`, 32 batch, 1251/1251, 3.4M token).
- new == true AND true GEÇERLİ AND true != db → RELABEL
- new == db → FALSE_MISMATCH (db doğru, flag temizle)
- true ∈ {FELSEFE,DIN} → UMBRELLA (SOSYAL, relabel YOK)
- diğer → SPLIT (curator)

## Sonuç (1,251)
| Verdict | Sayı | Aksiyon |
|---|---|---|
| **RELABEL** | **991** | subject_area = true (MAT 366, GEO 285, TARIH 123, COGRAFYA 83, FIZIK 40, GENEL 25, EDEBIYAT 23, TURKCE 20, KIMYA 16, BIYO 10) |
| FALSE_MISMATCH | 39 | db doğru, blind_true_subject temizlendi |
| UMBRELLA (FELSEFE/DIN) | 136 | SOSYAL şemsiyesi, relabel yok, işaretlendi |
| SPLIT | 85 | curator |

991/1251 = **%79** 2-sinyal hizalanma. Spot: GENEL→MATEMATIK ("a=2,b=3,c=4,d=5 ifadeleri") doğru.

## DB Apply
Backup `question_bank_subj_relabel_backup_20260601` (1251, subject_area+metadata). Marker
`subject_relabeled` + `subject_relabel_run=2026_06_01`. Doğrulama: relabeled 991, subject_area
hedefe eşit, GENEL 1996→1856, SOSYAL 1525→1411.

## Çözdü
K21 — 991 yanlış-kategori soru doğru derse taşındı (kategorizasyon/serving düzelir). Düşük risk
(reversible, cevap değişmez). Kalan: 136 umbrella (FELSEFE/DIN — sistem SOSYAL kullanıyor, fine)
+ 85 split → curator/opsiyonel.

## Artifactlar (untracked)
`_beta_core_tmp/`: subj_solve_input.jsonl, subj_key.jsonl, subj_batches/, subj_classify.json,
consensus_apply_subj.py, apply_subj.sql. Workflow: `wf_96d7bb8f-04c`.

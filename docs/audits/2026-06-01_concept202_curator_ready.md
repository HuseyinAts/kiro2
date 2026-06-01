# 202 Concept REAL_ERROR — Curator-Ready Paketleme

**Tarih:** 2026-06-01
**Amaç:** 480 real_error'ın MAT+GEO-dışı **202 concept** sorusu (Türkçe/kimya/genel/fizik/
tarih...) — bunlar deterministik DEĞİL (3 LLM hizalansa bile ortak-bias riski), bu yüzden
**auto-correct EDİLMEZ**. Bunun yerine 2-solver kanıtını curator'a yüzeye çıkar → insan hızlı
onaylar/reddeder.

## Neden auto-correct değil
MAT/GEO'da 3-sinyal = neredeyse-kanıt (deterministik). Concept'te LLM yargısı; 3 model aynı
yanlışı paylaşabilir. Karpathy: deterministik olanı otomatikle, yargı-bazlıyı insana bırak.

## Yapılan (2 parça, cerrahi)
1. **DB enrich** (backup `question_bank_concept202_backup_20260601`): 202 soruya
   `pipeline_metadata.dispute_suggestion = {suggested(blind), db, reason(628-workflow new_blind),
   conf, method:"2blind_agree"}`. correct_answer DOKUNULMADI.
2. **Backend** (`backend/api/curator.py`, commit 2e91e4e52): `QueueItem.dispute_suggestion`
   alanı + `_row_to_queue_item` pipeline_metadata'dan okur → curator API kanıtı sunar.
   Container smoke PASS (KIMYA: db=A, suggested=B, gerçek reason döndü).

## Curator deneyimi (önce/sonra)
- ÖNCE: curator yalnız mevcut DB cevabını görüyordu (yanlış olduğu bilinmiyordu).
- SONRA: "DB: A — ama 2 bağımsız kör solver: B (conf 0.85) — gerekçe: ..." → hızlı karar.

## İnsan worklist (frontend beklemeden)
`_beta_core_tmp/concept202_review_worklist.csv` (202 satır): id, subject, db_ans, suggested,
conf, question_preview, reason. Hüseyin Excel'de accept/reject işaretler → bulk apply.

## Subject dağılımı
TURKCE 62, KIMYA 50, GENEL 31, FIZIK 22, TARIH 13, SOSYAL 11, EDEBIYAT 7, BIYOLOJI 5, FEN 1.

## Takip (opsiyonel)
- Frontend curator queue component'i `dispute_suggestion`'ı render etsin (API hazır, UI küçük ekleme).
- Worklist Hüseyin onayı sonrası: accept → correct_answer=suggested (3-sinyal MAT/GEO pattern'i), reject → status koru.

## Artifactlar (untracked)
`_beta_core_tmp/`: concept202.tsv, enrich_concept202.sql, concept202_review_worklist.csv.

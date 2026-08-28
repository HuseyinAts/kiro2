# WAVE1 PILOT RESULT — AYT-Edebiyat: consensus GATE FAILED → 4-WAY narrowing → +56 SHIPPED

Tarih: 2026-06-19.
- **Faz 1 (consensus gate): KALDI** — TIER-A %75 / TIER-B %50 blind precision (<%95). Promote YAPILMADI.
- **Faz 2 (4-yönlü narrowing): SHIPPED** — Opus 199 TIER-A'yı kör çözdü, gemma==qwen==stored==Opus = 169;
  bunların view-uygun 58'i (42 demoted_at + 69 fallback + 41 tier1 ELENDİ) promote edildi; 56'sı v_safe'e girdi
  (2'si is_public=false). **v_safe 6544→6600, AYT-Edebiyat 233→289 (+56, +%24). leak=0, correct_answer/is_active DOKUNULMADI.**
  backup `question_bank_wave1_ayt_edebiyat_backup_20260619` (58), flag `pipeline_metadata.wave1_run`, view D7.

## Methodology
- Aday evreni: 4.564 AYT-Edebiyat (v_safe DIŞI, shaped). Pilot = ilk 60 batch / 1.200 soru (`ORDER BY md5(id)`).
- İki bağımsız KÖR solver: gemma3:12b-it-qat (1.089/1.200 A-E) + qwen3:14b (1.026/1.200 A-E). Anahtar solver'a GİTMEDİ (yalnız master.csv'de).
- Gate (`wave1_gate.py`): coherence (broken=dup/OCR/iki-model-abstain) → survivorlarda TIER.
- Opus (Claude) blind validation: TIER-A 20 örnek + TIER-B 30 örnek KÖR çözüldü, SONRA key açıldı.

## Gate dağılımı (1.200 judged)
| Bucket | n | % |
|---|---|---|
| DROP_broken | 55 | 4.6 |
| PROMOTE_A (g==q==key) | 199 | 16.6 |
| PROMOTE_B (tek model==key) | 281 | 23.4 |
| DROP_wrongkey (iki A-E, ikisi≠key) | 544 | 45.3 |
| DROP_unresolved | 121 | 10.1 |

## Opus blind precision (ASIL KAPI)
- **TIER-A: 15/20 = %75** stored-key blind-agreement.
- **TIER-B: 15/30 = %50** stored-key blind-agreement.
- Gate eşiği **≥%95** → **HER İKİ TIER de KALDI.**

## Kanıtlanmış yanlış anahtarlar (curator backlog — correct_answer DOKUNULMADI)
İki zayıf model de kaçırdığı (consensus yanlış-key'i "doğruladı") vakalar:

| Tier | id | stored | doğru | kanıt |
|---|---|---|---|---|
| A | 46541467-1d50-515b-bd15-dd15f23200f8 | B | A | İntibah (Mehpeyker/Dilaşub/Fatma Hanım) = Namık Kemal |
| B | 2e5c4a36-f118-5c98-a539-88d838c8dcc8 | E | D | Kabusnâme çeviren = Mercimek Ahmet (XV. yy) |
| B | dbeae55b-1604-54e7-8c71-2b36f5532767 | E | A | "ersin/ersin" cinaslı kafiye; E "için/için" değil |
| B | be27b14a-64a2-5bc7-9644-d711cc323a42 | B | A | Akif gerçek anlam → "mecaz" söylenemez |

## Kök neden
AYT-Edebiyat, gemma3/qwen3 için ZOR + OCR-garble + sübjektif ("hangisi yanlıştır").
İki zayıf model **ortak-mod hata** ile sıkça AYNI yanlış-key'de buluşuyor → "iki model doğruladı"
sinyali bu branşta zayıf. DROP_wrongkey %45 erken uyarıydı. Net subjects'te işe yarayan
consensus-gate, AYT-Edebiyat'ta SERVING havuzu için güvenli değil.

## Sonuç / öneri
1. **Bu dalga promote edilmedi** (0 risk, 0 rollback). v_safe AYT-Edebiyat 233'te kaldı.
2. Bu branşta cheap consensus-promotion BIRAK. Seçenekler:
   - **4-yönlü gate:** TIER-A 199'un TAMAMINI Opus kör-çöz, yalnız gemma==qwen==stored==Opus
     promote et (~%75 → ~150 temiz). Ayrı adanmış pass (tek turda 199 soru kalite riskli).
   - **Curator/insan review** AYT-Edebiyat için (subject zorluğu otomatik gate'i aşıyor).
   - **Daha güçlü solver** (örn. Claude-blind tüm aday) — maliyet/hacim dengesi ayrı karar.
3. Diğer branşlar (TYT-Biyoloji 4.546, TYT-Tarih 2.911) için consensus-gate yeniden denenebilir
   — ama her branşta önce Opus-blind precision ölçülmeli (AYT-Edebiyat dersi: branş-bağımlı).

## Üretilen artefaktlar (transient, gitignore'lı)
- `preds_gemma/` (60) + `preds_qwen/` (60) — blind preds
- `wave1_gate.py`, `wave1_breakdown.json`, `promote_A_ids.json` (199), `promote_B_ids.json` (281)
- `opus_A.txt`+`opus_A_key.csv`, `opus_B.txt`+`opus_B_key.csv` — blind validation
- `gen_promote_sql.py`, `D7_part2_view.sql`, `D7_rollback.sql` — HAZIR ama ÇALIŞTIRILMADI
  (4-yönlü narrowing kararı verilirse gen_promote_sql + D7 kullanılabilir)

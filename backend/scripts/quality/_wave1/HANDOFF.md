# WAVE1 HANDOFF — AYT-Edebiyat Pool-Growth (Claude Code devam brief'i)

> Bu dosya tek başına yeterli. Claude Code yeni session'da bunu + `CLAUDE.md` + `.claude/sessions/latest.md` okuyarak kaldığı yerden devam etmeli. Tarih: 2026-06-19.

---

## 0) TEK CÜMLE DURUM
v_safe (servis havuzu) %100 doğrulanmış ama **dengesiz** (TYT-Mat 2.627 vs AYT-Edebiyat 233). Karar: **hedefli pool-growth, AYT-öncelikli, pilot = AYT-Edebiyat** (4.564 promote adayı). gemma3 pilot çözümü (ilk 60 batch / 1.200 soru) **BİTTİ**; sıradaki adım qwen3.

## 1) ŞU AN NEREDEYIZ (kesin)
- `_wave1/master.csv` = 4.564 AYT-Edebiyat sorusu (v_safe DIŞI, shaped: 5 şık + geçerli key + word_count≥5), `ORDER BY md5(id)`.
- `_wave1/split.py` → `_wave1/batches/batch_000..228.jsonl` (229 batch × 20, blind: anahtar YOK).
- **gemma3 pilot DONE:** ilk 60 batch çözüldü, **1.089/1.200 A-E** (~%9 UNSOLVABLE = figür/garble/bozuk). preds `_wave1/batches/preds_000..059.json` (taşınmamışsa).
- qwen3 HENÜZ çalışmadı.

## 2) HEMEN SIRADAKI KOMUT (pilot devam)
```powershell
# (a) gemma preds'i ayır
New-Item -ItemType Directory -Force "C:/Users/husey/kiro2/backend/scripts/quality/_wave1/preds_gemma" | Out-Null
Move-Item "C:/Users/husey/kiro2/backend/scripts/quality/_wave1/batches/preds_*.json" "C:/Users/husey/kiro2/backend/scripts/quality/_wave1/preds_gemma/" -Force

# (b) qwen3'ü AYNI ilk 60 batch'e çalıştır (resume: preds taşındı → 000-059 sıfırdan)
cd C:\Users\husey\kiro2\backend\scripts\quality
python ollama_blind_solve.py --batch-dir _wave1\batches --model qwen3:14b --cooldown 8 --max-new 60

# (c) qwen preds'i ayır
New-Item -ItemType Directory -Force "C:/Users/husey/kiro2/backend/scripts/quality/_wave1/preds_qwen" | Out-Null
Move-Item "C:/Users/husey/kiro2/backend/scripts/quality/_wave1/batches/preds_*.json" "C:/Users/husey/kiro2/backend/scripts/quality/_wave1/preds_qwen/" -Force
```
Doğrulama: `preds_gemma` ve `preds_qwen` her biri **60 dosya** olmalı (eksikse solver'ı tekrar çalıştır, resume eder).

## 3) PIPELINE — 5 AŞAMA (pilot 60 batch, sonra kalan 169)
1. **Export+split** ✅ DONE
2. **Kör-çöz** — gemma3 ✅(60) + qwen3 ⏳ . Model tag'leri: `gemma3:12b-it-qat`, `qwen3:14b`. Solver: `backend/scripts/quality/ollama_blind_solve.py` (`--batch-dir`, `--model`, `--cooldown`, `--max-new`; resume = var olan `preds_*.json` atlanır; OLLAMA=`localhost:11434`, CONCURRENCY=4).
3. **Coherence gate** — bozukları ELE. Template: `_gate2b/gate2c_breakdown.py` ve `_gate2b/coherence_gate.py`. Bozuk = dup şık VEYA OCR çift-prefix (`^[A-E]\)`) VEYA **iki model birden UNSOLVABLE**. (answer-wrong taramasında ~%10-12 bozuk çıkmıştı; burada da bekle.)
4. **Consensus + Opus validate** — **SIRA: önce coherence gate (§3) ile broken'ları DROP et, SONRA hayatta kalanlarda TIER hesapla.** promote TIER'leri:
   - **TIER-A (yüksek):** `gemma==qwen==stored` (3'lü mutabakat) → promote-ready.
   - **TIER-B (orta):** tam bir model==stored, diğeri A-E farklı → Opus ~30 örnek key doğrula.
   - **DROP:** ikisi de stored'dan farklı + ikisi de A-E (muhtemel yanlış-key VEYA zor) → promote'a ALMA (konservatif; answer-wrong taramam bunların %73'ünün aslında doğru-key/zor olduğunu gösterdi ama promote için riskli, dışarıda bırak).
   - **Opus rolü:** Ben (Claude/Opus) TIER-A'dan ~20 + TIER-B'den ~30 örneği KÖR çöz, stored ile karşılaştır. Precision ≥%95 ise TIER promote, değilse daralt. (Faz A/B/C deseni: ~150 örnek → net DB-hatası 0.)
   - **⚠️ Beklenen yield ÖLÇÜLMEDİ** — qwen3 + gate çıktısı görülene kadar tahmin. TIER-A (3'lü mutabakat) kriteri **kolay/net sorulara biaslı** (iki zayıf modelin de doğru bulduğu = açık sorular); zor-ama-geçerli soruları TIER-B'ye/dışarı iter. Bu ilk dalga için kabul edilebilir (hacim+denge öncelik); zorluk dengesi ayrı IRT işi. Gerçek yield qwen+gate sonrası raporla, ezbere sayı verme.
5. **Promote** — temizleri v_safe'e ekle (DETAY §5).

## 4) GATE SCRIPT'LERİNİ NASIL ADAPTE ET
`_gate2b/gate2c_combined.py`'yi kopyala → `_wave1/wave1_gate.py`. Değişiklikler:
- `BASE = .../_wave1`
- preds_gemma + preds_qwen + master.csv oku (master'da `key` VAR).
- Coverage gate (her iki model 60 batch = ~1.200 pred dolu mu; eksikse DUR).
- Kategoriler: PROMOTE_A (g==q==key), PROMOTE_B (tam biri==key), DROP_wrongkey (ikisi≠key, ikisi A-E), DROP_broken (dup/ocr/iki-UNSOLVABLE).
- Çıktı: `promote_A_ids.json`, `promote_B_ids.json`, `opus_A.txt`+`opus_A_key.csv` (~20), `opus_B.txt`+`opus_B_key.csv` (~30) — blind (anahtar ayrı csv).
- **Blind bütünlük:** Opus, `.txt`'ten çözer, SONRA `_key.csv` açılır. (Bkz `_gate2b` aynı desen.)

## 5) PROMOTE ADIMI (ZORUNLU detaylar — Faz A/B/C deseni)
**A. Backup ÖNCE** (reversible):
```sql
CREATE TABLE question_bank_wave1_ayt_edebiyat_backup_20260619 AS
SELECT id, quality_review_status, pipeline_metadata
FROM question_bank WHERE id IN (<promote ids>);
```
**B. Promote UPDATE** — `correct_answer`/`is_active`'e DOKUNMA. Sadece status + provenance flag:
```sql
UPDATE question_bank
SET quality_review_status='auto_judged_high',
    pipeline_metadata = jsonb_set(
      COALESCE(pipeline_metadata::jsonb,'{}'::jsonb),
      '{wave1_run}', 'true'::jsonb)
WHERE id IN (<promote ids>);
```
**C. v_safe'e girmesi için view (D7):** v_safe_for_beta predicate'i şu bayrakları içeriyor: `student_coherent / verified_provisional / consensus_2signal_run / math_promote_run / verbal_promote_run`. **`wave1_run` LİSTEDE YOK** → ya (i) `verbal_promote_run` bayrağını kullan (AYT-Edebiyat zaten verbal; view değişmez), ya da (ii) **D7 view edit** ile `OR pipeline_metadata::jsonb ? 'wave1_run'` ekle (provenance için temiz; `_gate2b/D6_part2_view.sql`'i template al, canlı `pg_get_viewdef('v_safe_for_beta',true)` ile birebir kopyala — EZBERDEN YAZMA).
   - **⚠️ KRİTİK:** Canlı viewdef ARTIK D6'nın `AND id NOT IN (SELECT id FROM gate2c_demoted)` satırını İÇERİR. `OR 'wave1_run'`'i **bayrak-grubu parantezinin İÇİNE** ekle (`...OR ? 'verbal_promote_run')` → `...OR ? 'verbal_promote_run' OR ? 'wave1_run')`). gate2c exclusion `AND`'ini BOZMA, parantez dışına taşma — yoksa ya view malformed ya gate2c demote'ları geri sızar. Apply sonrası `SELECT count(*) FROM v_safe_for_beta WHERE id IN (SELECT id FROM gate2c_demoted)` = **0** olmalı (sızıntı yok kontrolü).
   - **Öneri:** provenance için (ii) D7 — yeni bayrak + view'a ekle. Rollback dosyası da yaz (`D7_rollback.sql`).
**D. Doğrula:** `SELECT count(*) FROM v_safe_for_beta` artışı = promote sayısı; `SELECT count(*) FROM v_safe_for_beta WHERE exam_type='AYT' AND subject_area='EDEBIYAT'` (233 → yeni).

## 6) HARD RULES / TUZAKLAR (ihlal etme)
- **İki Ollama instance:** solver `kiro2-ollama` **container**'ına (`localhost:11434`) bağlanır. Model yoksa: `docker exec kiro2-ollama ollama pull <tag>`. Native Ollama'ya pull = "model not found" 404 tuzağı.
- **`correct_answer` / `is_active` ASLA değişmez.** Pool-growth yalnız `quality_review_status` + `pipeline_metadata` (flag) yazar.
- **Türkçe SQL:** daima `psql -f dosya.sql` (inline `-c "..."` Türkçe karakteri bozar / 0xfe error). psql yolu: `"C:/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2`.
- **DB servisi:** native PG18 `postgresql-x64-18` (port 5434). Durmuşsa `Start-Process powershell -Verb RunAs -ArgumentList "Start-Service postgresql-x64-18"` (admin).
- **bash VM güvenilmez** — tüm script'ler HOST PowerShell ile, human-in-loop. Onaysız çalıştırma.
- **md5 order:** export `ORDER BY md5(id)` (deterministik karışık örnekleme). SELECT DISTINCT+ORDER BY md5 tuzağı için alt-sorgu (bkz CLAUDE.md).
- **Blind solve:** solver'a anahtar GİTMEZ; key yalnız master.csv'de, gate karşılaştırması için.
- **Reversible-first:** her DB yazımından önce backup tablo + rollback SQL.

## 7) DOĞRULANMIŞ FACTS (bu session, ölçülü)
- v_safe = **6.544** (D5 6.606→ gate2c D6 62 demote → 6.544). %100 doğrulanmış (2.626 coherent taranmış + 3.918 promoted Opus-sample). Denetlenmemiş = 0.
- gate2c_demoted tablosu = 62 (geri-alınabilir exclusion).
- AYT toplam promote arzı 12.767; sonraki hedefler (AYT-Edebiyat sonrası): TYT-Biyoloji 4.546, TYT-Tarih 2.911, AYT-Kimya 1.021, AYT-Fizik 877, AYT-Biyoloji 648.
- Consensus yöntemi: coherence için güvenilir; küçük modeller ZOR soruyu çözemez (answer-wrong %27 precision) → promote'ta DROP_wrongkey'i alma.

## 8) AÇIK İŞLER (wave1 dışı, backlog)
1. 3 wrong-key adayı (manuel onay, `correct_answer` korumalı): `f41b7323`(C→D güçlü), `e9c247a6`(B→A), `e829870c`(E→C bozuk).
2. ~25 bozuk soru (answer-wrong taramasında bulundu) → gate2c'ye demote.
3. `offline_sync_service.py` I001 import sort + PLR0912 (pre-existing, kozmetik).

## 9) COMMIT'LER (bu session, branch `feature/self-evolution-optimization`, push'lu)
- `7c6731940` serving-path gate (placement+offline v_safe)
- `cce6807fe` offline_sync F821 fix
- `42639b85e` handoff chore
- **Uncommitted:** `_wave1/*` (bu pilot), `.claude/sessions/latest.md` güncellemesi, gate2c answer-wrong transient'leri.

## 10) ÇALIŞMA ŞEKLİ (KIRO2)
Bug fix → önce Root Cause tablosu + fail-eden test (TDD red→green). 3+ dosya → plan. Veriye dayalı, ezber yok; her iddia canlı çıktıdan. Subagent'lara dosya YOLU ver. Push öncesi >100MB dosya kontrolü.

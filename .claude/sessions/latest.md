# Session Handoff — 2026-06-20/21 (DERİN)

**Branch:** `feature/self-evolution-optimization`
**Son commit:** `ca0cb3e1d` blind-solve wave20
**Working tree:** temiz. **TÜM commit'ler LOCAL — push EDİLMEDİ** (feature branch).
**Infra:** PG18 5434 `pg_ctl` ile manuel açık (servis admin gerektiriyor; makine restart'ında DÜŞER → `pg_ctl -D "C:/Program Files/PostgreSQL/18/data" -l C:/Users/husey/pg18_manual_start.log start`). Backend/frontend DOWN.

## ⭐ TOPLAM BU SESSION: v_safe 7.812 → 20.907 (+13.095, +%168)

Tüm değişiklikler **reversible** (her adımın backup tablosu var), **correct_answer/is_active DOKUNULMADI** (yalnız `quality_review_status` + `pipeline_metadata` flag).

| Faz | Kazanç | Commit'ler |
|---|---|---|
| Fallback re-tag (ana) | +1.636 | `60a1843cb` |
| 422 taksonomi (eşik-0.70 + KIMYA 4 yeni topic) | +276 | `daa1efef3` |
| Blind-solve (calib + 20 dalga + 2 partial) | +11.183 | `d03891ae6`…`ca0cb3e1d` |

## 1) Fallback re-tag (TAMAMLANDI)
2.058 fallback-vp sorunun topic-etiketi LLM batch-classify ile düzeltildi. Kalan 146 (gerçek yanlış-ders SOSYAL din/felsefe = subject-relabel gerek). KIMYA taksonomisine 4 kalıcı topic eklendi (`topic_hierarchy`): Çözeltiler ve Karışımlar / Maddenin Halleri ve Gazlar / Çevre Kimyası / Mol ve Kimyasal Hesaplamalar. Detay: `backend/scripts/quality/_vp_unlock/VP_RETAG_RESULT.md`.

## 2) Blind-solve #1 (DEVAM EDİYOR — ana iş)
**Mekanizma:** unverified soruyu KÖR çöz (cevap-anahtarı verilmez) → blind==DB key = AGREE = 2-sinyal → `verified_provisional`=true + status `auto_judged_high`. **Hedef havuz = "direkt-kazanç"** (unfiltered/content-temiz ∧ status-only-blocked ∧ NOT fallback/demoted/gate2c/tier1) → AGREE'de DİREKT v_safe'e girer.
- **20 tam dalga + calib + 2 partial koşuldu. blind_total=11.183. AGREE kararlı ~%56-58. promote ~%37/dalga (AGREE∧conf≥0.80).**
- **KALAN direkt-kazanç: 7.251 (~5 dalga, ~+2.700 v_safe daha → ~23.600).**
- Her dalga: 1.600 aday, 40 batch (40 soru/agent), WAVE=3, ~40dk, 0 throttle.
- promote-edilmeyen solved adaylar `blind_seen` flag'li → export bunları hariç tutar (çakışma yok).

### SONRAKİ SESSION — wave-21 reçetesi (kopyala-çalıştır):
```bash
cd C:/Users/husey/kiro2/backend/scripts/quality/_blindsolve
PSQL="C:/Program Files/PostgreSQL/18/bin/psql.exe"
# setseed her dalgada DEĞİŞ (kullanılanlar dahil yeni bir değer, örn 0.43)
sed 's/setseed(0.59)/setseed(0.43)/; s/wave20_master.csv/wave21_master.csv/' export_wave20.sql > export_wave21.sql
"$PSQL" -p 5434 -U postgres -d kiro2 -f export_wave21.sql
# python ile w21batches/ (40'lık) + wave21_keymap.json üret (önceki dalga python bloğunu kopyala)
# Workflow scriptPath: .../blind-solve-calib-420-wf_34005c63-076.js , args = w21manifest (40 dosya)
# Sonuç: apply (AGREE∧conf>=0.80 → vp+status) + flag_seen + commit. apply_w20.sql şablon.
```
**Apply şablonu (her dalga aynı):** AGREE∧conf≥0.80 → `quality_review_status='auto_judged_high'` + `pipeline_metadata` jsonb_set `verified_provisional=true` + `blind_solve_wave='...'`. backup tablo + `blind_seen` flag (promote-edilmeyen solved). Scriptler `_blindsolve/` altında.

## ⚠️ RATE-LIMIT — İKİ AYRI ŞEY (memory: reference_workflow-rate-limit-batching)
1. **529 "Server temporarily limiting"** = sunucu RPM throttle. ÇÖZÜM: büyük-batch (40-80 soru/agent) + WAVE=3 + 45sn cooldown. Tekil-agent (1 soru=1 çağrı) YASAK.
2. **"You've hit your session limit · resets HH:MM"** = hesabın GERÇEK token kotası. Çözümü YOK — reset bekle. Bu session'da 2 kez vuruldu. Her seferinde partial salvage edildi (psql lokal kota yemez). Reset sonrası 1-batch probe ile test et, geçerse full dalga.

## Açık kalemler (ROI sıralı)
1. **Blind-solve devam** — kalan 7.251 direkt-kazanç (~5 dalga). Sonra fallback'li 16K (re-tag de gerek) + geniş unverified evreni.
2. **PUSH** — tüm session commit'leri LOCAL; `git push` (kullanıcı isterse).
3. **Beta E2E smoke** — 20.907 havuzla AYT simülasyonu (backend up gerek).
4. **DISAGREE havuzu** (~%24/dalga) — DB-key-hatası VEYA solver-hatası; 2. FARKLI-model sinyaliyle ayrış (gold terfi; A-bias var, single-blind gold için yetmez).
5. **146 fallback artığı + SOSYAL yanlış-ders** — subject-relabel (topic değil).

## Kararlar (tekrar tartışma)
- vp bari = single-blind AGREE∧conf≥0.80. Gold terfi 2. farklı-model şart (A-bias hafif: solver A'yı ~%5 fazla seçer ama dağılım DB'ye yakın = key sızmıyor).
- promote yalnız status + pipeline_metadata flag; **correct_answer ASLA**.
- LLM batch işlerinde ≥15-80 öğe/agent ZORUNLU (rate-limit).

## Doğrulama (yeni session açılışında)
```sql
SELECT count(*) FROM v_safe_for_beta;  -- 20.907 olmalı
SELECT count(*) FROM question_bank WHERE pipeline_metadata::jsonb ? 'blind_solve_wave';  -- 11.183
```
Eşleşmiyorsa MEMORY/handoff drift — kullanıcıya bildir.

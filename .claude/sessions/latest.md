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

---

## 🚀 YENİ SESSION AÇILIŞ PROMPT'U (kopyala-yapıştır — sınır-zorlayan otonom mod)

> Bu prompt'u yeni session'ın İLK mesajı olarak yapıştır. Dalga-başına dur-sor YOK;
> pool kuruyana veya session-limit'e kadar otomatik zincirler, her dalga commit'li
> (loss-free). Proven reçete (40 soru/agent, WAVE=3) değişmez.

```
KIRO2 blind-solve devam — OTONOM ÇOK-DALGA MOD. Şu sırayı uygula, dalgalar arası BANA SORMA:

ADIM 0 — HANDOFF + INFRA:
1. .claude/sessions/latest.md'yi OKU (bu dosya). Reçete + iki rate-limit tipi orada.
2. PG18'i ayağa kaldır (restart'ta düşmüş olabilir; pg_ctl PATH'te YOK, tam yol şart):
   "C:/Program Files/PostgreSQL/18/bin/pg_ctl.exe" -D "C:/Program Files/PostgreSQL/18/data" -l C:/Users/husey/pg18_manual_start.log start
   Zaten açıksa "another server might be running" döner — sorun değil, devam.

ADIM 1 — DOĞRULAMA GATE (eşleşmezse DUR + bana bildir, devam ETME):
   PSQL="C:/Program Files/PostgreSQL/18/bin/psql.exe"
   "$PSQL" -p 5434 -U postgres -d kiro2 -c "SELECT count(*) FROM v_safe_for_beta;"           -- 20907 bekle
   "$PSQL" -p 5434 -U postgres -d kiro2 -c "SELECT count(*) FROM question_bank WHERE pipeline_metadata::jsonb ? 'blind_solve_wave';"  -- 11183 bekle
   Sayılar tutmuyorsa = drift → DUR, raporla.

ADIM 2 — DALGA DÖNGÜSÜ (wave-21'den başla, POOL KURUYANA KADAR zincirle):
   cd C:/Users/husey/kiro2/backend/scripts/quality/_blindsolve
   Yardımcı scriptler bu dizinde KALICI: split_wave.py, aggregate_wave.py, blind_solve_wave.js
   Her dalga için (<N> = 21,22,...):
   a) EXPORT: sed 's/setseed(0.59)/setseed(0.<YENİ>)/; s/wave20_master.csv/wave<N>_master.csv/' export_wave20.sql > export_wave<N>.sql
      setseed her dalgada FARKLI. KULLANILMIŞ (tekrarlama): 0.05 0.07 0.13 0.19 0.23 0.29 0.31 0.37 0.42 0.49 0.53 0.59 0.61 0.67 0.71 0.77 0.83 0.89 0.91
      BOŞ öneri (w21→w25): 0.43 0.47 0.03 0.17 0.73
      "$PSQL" -p 5434 -U postgres -d kiro2 -f export_wave<N>.sql   → wave<N>_master.csv (1600 satır, KEY dahil)
   b) SPLIT: python split_wave.py <N>   → w<N>batches/g01..g40.json (KEY YOK=kör) + w<N>manifest.json
   c) WORKFLOW (kör çöz): Workflow tool, scriptPath=C:/Users/husey/kiro2/backend/scripts/quality/_blindsolve/blind_solve_wave.js
      args = w<N>manifest.json İÇERİĞİ (JSON array, 40 obje). WAVE=3 script içinde, ~40dk.
      Dönen {rows:[{id,ans,conf}]} sonucunu w<N>_solved.json dosyasına YAZ (Write tool).
   d) AGGREGATE: python aggregate_wave.py <N>   → apply_w<N>.sql + flag_seen_w<N>.sql ÜRETİR (AGREE∧conf≥0.80, backup dahil). Çıktı satırı: solved/agree/promote sayıları.
   e) APPLY: "$PSQL" -p 5434 -U postgres -d kiro2 -f apply_w<N>.sql
   f) FLAG_SEEN: "$PSQL" -p 5434 -U postgres -d kiro2 -f flag_seen_w<N>.sql   (bu dalganın 1600'ü blind_seen → sonraki export hariç tutar)
   g) CHECKPOINT: git add -A && git commit -m "feat(quality): blind-solve wave<N> v_safe promote"
   h) VERIFY: v_safe + blind_total say (ADIM 1 SQL'i), önceki dalgaya göre arttığını DOĞRULA, bana 1 satır rapor ver, SONRAKİ DALGAYA GEÇ (sorma).
   Direkt-kazanç pool'u (~7.251) bitince (export <50 satır döner) VEYA 5 dalga dolunca DUR.

RATE-LIMIT — İKİ AYRI ŞEY (handoff §⚠️):
   • 529 "Server temporarily limiting" → RPM throttle. Workflow'u retry et, gerekirse batch'i 40→60 büyüt + 45sn cooldown. DURMA.
   • "session limit · resets HH:MM" → GERÇEK token kotası, çözümü YOK. O ANKİ dalganın partial sonucunu salvage et (psql lokal, kota yemez) → apply + flag_seen + commit → DUR, reset saatini bana yaz.

KISITLAR (ihlal etme):
   • correct_answer / is_active ASLA dokunma — yalnız quality_review_status + pipeline_metadata.
   • Her dalga backup tablolu + reversible.
   • Workflow schema KULLANMA (StructuredOutput güvenilmez); düz JSON text parse.
   • Tekil-agent (1 soru = 1 çağrı) YASAK — min 40 soru/agent.

Hazırsan ADIM 0'dan başla, bitince her dalgayı 1 satır raporla ama durma.
```

*Eklendi: 2026-06-21 — sınır-zorlayan otonom çok-dalga açılış prompt'u (insan-round-trip elendi, loss-free checkpoint korundu).*

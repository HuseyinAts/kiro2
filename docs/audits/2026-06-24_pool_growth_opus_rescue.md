# Pool-Growth — Opus-Rescue (Konu Dengesi) + tier1 Yanlış-Anahtar Bulgusu (2026-06-24)

## Bağlam
Konu dengesi (TYT %92 / AYT %8) için AYT-fen (en ince: Biyoloji 50, Fizik 91,
Kimya 108) büyütülmek istendi. "Promotable supply" ölçüldüğünde (unverified/pending,
v_safe dışı, şekilli) Kimya 943 / Fizik 851 / Biyoloji 561 göründü — AMA bu arzın
**~%97'si demote-edilmiş `tier1_page_inline`** çıktı (taze-nontier1 havuzu 1+6+4=11).

## KRİTİK BULGU — tier1_page_inline ~%50 yanlış-anahtar
`tier1_page_inline` = cevap anahtarı **sayfa-pozisyonundan** eşlenmiş (text-doğrulama
YOK) → en güvenilmez matching metodu. Opus (ben) 68 self-contained soruyu kör-çözüp
stored anahtarla karşılaştırdım: **yalnız 33'ü (%49) eşleşti.** Geri kalanların çoğunda
anahtar açıkça yanlış (aritmetikle kanıtlı):
- Çözünürlük 40g/100g × 300g = **120g**, anahtar "420" (imkânsız).
- %50/%10→%20 kaldıraç = **1/3**, anahtar "7".
- CₙH₂ₙ+Br₂ M=202 → **C₃H₆**, anahtar C₃H₈ (alkan, olamaz).
- 0,25M·4L, 3L su buharlaş → **1M**, anahtar 2M.
- Kanser alternatif tedavi → **nanoteknoloji**, anahtar "antropoloji".

Blanket tier1-demote **DOĞRUYMUŞ** — pozisyon-eşleşmesi gerçekten ~yarı yanlış-anahtar
üretmiş. Bu yüzden bu havuzdan pool-growth ZORUNLU olarak Opus-doğrulamadan geçmeli.
(Not: tier1 sorular v_safe'e normalde girmez; ama `verified_provisional` flag'i olanlar
girer — blind_solve bulk bunu yaptı; ayrı re-gate konusu, bkz 2026-06-23 rootcause.)

## Yöntem — Opus-Rescue (reversible)
Opus = gemma3/qwen3'ten güçlü doğrulayıcı. Akış:
1. Demote-tier1 adayını kör çek (anahtarsız), `ORDER BY md5(id||'pg1')` deterministik.
2. Yalnız **self-contained** (şekle-bağımsız) soruları Opus kör-çöz; figür-zorunlu +
   belirsiz (iki-doğru/iki-yanlış) atlanır.
3. **Promote yalnız Opus-cevabı == stored anahtar** olanlara (iki bağımsız kaynak
   uyuşması = güçlü kanıt anahtar doğru) → corroborated.
4. Promote DB yazımı (reversible):
   - backup: `opus_promote_log (id, old_status, old_metadata, opus_answer, subject)`.
   - `quality_review_status` → `auto_judged_high`.
   - `pipeline_metadata`: `demoted_at` SİL + `verified_provisional`=true (v_safe flag-grubu)
     + `opus_promote`=true (izlenebilir geri-alma).
   - `correct_answer` / `is_active` ASLA dokunulmadı.

## Sonuç (6 batch, 270 soru kör-çözüldü)
- Eşleşme oranı tutarlı ~%46: b1 12/31, b2 21/37, b3 16/38, b4 16/34, b5 14/30, b6 14/31.
  → tier1 havuzunun ~yarısı doğru-anahtar (Opus-corroborated), ~yarısı yanlış-anahtar (sabit).
- **Dedup kapısı:** promote sonrası normalize-prefix kontrolü; mevcut v_safe ile mükerrer
  çıkan **8 P-kopya geri alındı** (X zaten doğru-anahtarla orada). Batch içi twin'ler ve
  near-dup'lar ön-filtrelendi. Son durum **0 mükerrer**.
- v_safe'e net giren: **82** (1 "Yukarıya..." unfiltered figure-guard `^yukar(ı|ıdaki)`
  yanlış-pozitifinde takıldı — bilinen guard kusuru, düşük öncelik).

| Konu | Önce | Sonra | Δ |
|---|---|---|---|
| AYT-Kimya | 108 | 137 | +29 |
| AYT-Fizik | 91 | 109 | +18 |
| AYT-Biyoloji | 50 | 85 | +35 |
| v_safe | 25.096 | 25.178 | +82 net |

Net yield ~13-14 soru/batch (figür-bağımsız + Opus==anahtar + mükerrer-değil). Fizik
en düşük (çoğu figür-zorunlu). `opus_promote_log` = 83 satır (82 v_safe'te + 1 guard-blok).

## Geri-alma
```sql
-- promote'u tümüyle geri al (eski status + metadata restore):
UPDATE question_bank q SET quality_review_status = l.old_status,
       pipeline_metadata = l.old_metadata
FROM opus_promote_log l WHERE q.id = l.id;
-- (veya yalnız flag temizle: pipeline_metadata'dan opus_promote + verified_provisional çıkar,
--  demoted_at geri ekle — ama old_metadata restore en temizi.)
```

## İki yol — ölçek kararı (kullanıcıya)
1. **Elle Opus-rescue devam** (otonom, ben): ~16 soru/batch, ~%49 yield. Birkaç batch
   daha ince konulara +50-80 ekler. Tam dengeye (yüzlerce) elle ulaşılmaz.
2. **GPU 2-model re-gate (ölçekli)**: tüm ~10K+ demote-tier1'i gemma3+qwen3 ile çöz,
   2-model-consensus==anahtar olanları Opus-örneklemle doğrula. Driver hazır:
   `backend/scripts/quality/_blindsolve/regate/` (~7-8h GPU, user çalıştırır).
   Gerçek balans için ölçeklenebilir tek yol.

## İlişkili
- `docs/audits/2026-06-23_blindsolve_rootcause.md` — blind_solve bulk kök-neden + v2 gate.
- v_safe exclusion/flag deseni: `gate2c_demoted` (demote) ↔ `opus_promote_log` (promote).

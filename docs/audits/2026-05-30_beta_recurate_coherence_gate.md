# Beta Çekirdek Re-Curate — Tutarlılık Gate'i (30 May 2026)

## Tetikleyici
Beta Pratik Testi browser E2E doğrulamasında, gerçek UI'da render edilen ilk soru:
> "ABC üçgenünde A açısının ölçüsü 60° olduğuna göre, A açısının ölçüsü kaç derecedir?"

**Hüseyin (insan, gerçek UI) yakaladı**: bu dairesel/garbled bir soru — öncül cevabı
söylüyor. Otomatik kontroller (backend E2E + tip-check) kaçırmıştı.

## Kök neden: kör 3-solver gate'in kör noktası
386 "beta clean core", kör 3-solver gate'inden geçmişti (3 bağımsız solver
`question_text`+şıkları okuyup cevap verir, consensus==DB → "doğrulanmış"). Bu gate'in
kör noktası: **dairesel/garbled soru, metin kendini cevaplıyorsa geçer** — 3 solver da
trivially "A) 60°" deyip uzlaşır, figüre hiç ihtiyaç duymaz. Yani "çözülebildi" ≠ "iyi soru".

## İkinci gate: tutarlılık yargıcı
6 paralel Claude subagent, 386'yı öğrencinin gördüğü kadarıyla (yalnız metin+şık, görsel yok)
yeniden yargıladı. Kriter: **tutarlı mı? dairesel mi? şekilsiz çözülebilir mi? gerçek MCQ mu?
cevap makul mü?**

### Sonuç
| | Sayı |
|---|---|
| Toplam çekirdek | 386 |
| **keep (temiz)** | **221** |
| drop | 165 (160 yargı + 5 yargısız→muhafazakâr drop) |

**Drop defect dağılımı:** garbled 75, circular 34, answer_wrong 30, open_ended 13, figure_dependent 8.

**Çekirdeğin ~%42'si öğrenci için aslında temiz değilmiş.** Tek insan-gözlemi sistemik soruna işaret etti.

### Spot-check (yargıç ayrım gücü)
- Hüseyin'in gördüğü soru (+ 2 kopyası) → **drop/circular** ✅
- Meşru benzerleri korundu: "A=60°, B=45° → C=75°" → keep; "A=60°, B=40° → C" → keep ✅
- KEEP örnekleri (mutlak değer, orta nokta, ideal gaz, ortalama hız, üçgen 20-12-16) → hepsi metinle çözülebilir ✅
- DROP örnekleri (formül-yok, "...yazınız" açık-uçlu, "dik açı 90°... dik açı 90°" garbled) → hepsi gerçekten kusurlu ✅

## Uygulama
- Backup: `question_bank_beta_recurate_backup_20260530` (386 satır, rollback hazır)
- 165 drop: `pipeline_metadata.beta_clean_verified` → `false` + audit `beta_recurate_2026_05_30`
  (verdict/defect/reason). **`correct_answer` ve `status` DOKUNULMADI** (metadata-only).
- Doğrulama: `beta_clean_verified='true'` → **221** | drop 165 | backup 386 | audit-marked 165.
- Engine in-memory pool cache (`BETA:clean:all`, TTL 1h) restart ile temizlendi → beta artık 221'den çekiyor (canlı doğrulandı: 20 soru, all_clean).

## Meta-ders
Kök-neden tezi **canlı kanıtlandı**: gerçek kullanıcı, gerçek UI'da, hiçbir otomatik proxy'nin
yakalayamadığı kaliteyi yakaladı. "Kalite-task çıktısı gerçek kullanıcıya gösterilene kadar
tamamlanmadı" kuralının doğrudan teyidi. İkinci gate o kör noktayı kapattı; beta artık 221
gerçekten-okunabilir-ve-çözülebilir soruyla açılabilir.

## Sonraki
- Beta davet (10-20 öğrenci) → 221 çekirdek üzerinden.
- (P1) Aynı tutarlılık-gate'i tüm `auto_judged_high` gold pool'a uygula — bu kör nokta
  386 ile sınırlı değil, gold pool'un tamamında olası (~%42 ekstrapolasyon ürkütücü).
- Drop'lar (özellikle figure_dependent + garbled) Vision re-gen adayı (GEMINI key AUP bekliyor).

## Artifactlar (untracked working data)
`backend/scripts/quality/_beta_core_tmp/`: beta_386.json, judge_batch_{1-6}.json,
judge_verdict_{1-6}.json, beta_keep_ids.json, beta_drop_ids.json, apply_recurate.sql,
verify_recurate.sql.

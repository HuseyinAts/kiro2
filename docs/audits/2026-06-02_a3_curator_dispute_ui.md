# A3 — Curator Manuel Kuyruğu + dispute_suggestion UI

**Tarih:** 2 Haziran 2026
**Track:** Track 1 / A3

## Durum (keşif)

| Parça | Durum |
|-------|-------|
| 202 concept worklist CSV | ✅ hazır (`_beta_core_tmp/concept202_review_worklist.csv`, 48KB) |
| Backend `dispute_suggestion` alanı | ✅ var (`curator.py:83,217`) |
| Frontend `dispute_suggestion` render | ❌ → **bu commit'te eklendi** |
| Kalan flag'ler (4 wrong_answer + 1 circular + 3 other) | ✅ curator `/flagged` köprüsünde görünür (önceki oturum) |

## Yapılan (kod)

- `frontend/src/hooks/useCuratorQueue.ts` — `QueueItem.dispute_suggestion`
  tipi (`{suggested, db, reason, conf, method}`)
- `frontend/src/pages/Admin/CuratorPage.tsx` — DB cevabı ≠ önerilen ise
  kırmızı uyarı bloğu: "DB cevabı X yanlış olabilir → 2 bağımsız kör solver: Y
  (güven %N)" + gerekçe. `data-testid=curator-dispute-suggestion`.
- `CuratorPage.test.tsx` — render testi (10/10 PASS)
- Doğrulama: `tsc --noEmit` exit 0; vitest 10/10 PASS. ESLint: 19 hata
  **önceden var** (>500. satır klavye handler), eklenen blokta hata yok.

## Kalan (kod-dışı)

1. **Frontend docker rebuild** (operatör): `dispute_suggestion` UI'sini canlıya
   almak için `docker compose build frontend && up -d --no-deps frontend`.
2. **202 concept manuel inceleme** (Hüseyin): worklist CSV'de her satır
   `id, subject, db_ans, suggested, conf, question_preview, reason` →
   accept (correct_answer=suggested) / reject (DB koru). MAT/GEO 3-sinyal
   pattern'i ile bulk apply.
3. **Kalan beta flag'leri** (4 wrong_answer + 1 circular): curator `/flagged`
   sekmesinde görünür; verdict ile çözülür (köprü canlı).

## Sonuç — Track 1 tamamlandı

- A1: 44 flag'li soru beta'dan çıkarıldı (2734→2690)
- A2: 1 figür yanlış-negatif (2690→2689); havuz figür-temiz doğrulandı
- A3: dispute_suggestion UI eklendi; manuel kuyruk Hüseyin'e hazır

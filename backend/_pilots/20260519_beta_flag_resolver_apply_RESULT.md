# Beta Flag Resolver — APPLY RESULT

**Date:** 2026-05-19
**Beta user:** beta01@kiro2.com
**Toplam flag:** 15 (E2E smoke testi 3 hariç)

## Kategori Dağılımı

| Kategori | Sayı |
|---|---|
| image_bound (frontend image suppress) | 9 |
| wrong_answer | 1 |
| incomplete_text | 2 |
| broken_text | 2 |
| latex_render_bug | 1 |

## Aksiyon Sonuçları

- Rejected: 15
- Flag resolved: 15

## Notes

- 9 image_bound soru: Bug #11 fix frontend `question_image_url` suppress eder
  → bu sorular image olmadan çözülemez, pool'dan çıkarıldı.
  Sprint sonrası vision re-crop ile geri kazanılır.
- 1 wrong_answer (`38261f49`): math doğrulanır E=4 yanlış, A=72 doğru.
  Şu an rejected; manuel cevap düzeltmesi sonra (curator).
- 1 latex_render_bug (`7c49c4d7`): opsiyonlarda raw `\frac` görünüyor.
  Bug #1 fix sadece question_text MathText wrap yaptı, opsiyonlar için
  yapılmamış. Sprint follow-up: ayrı commit.

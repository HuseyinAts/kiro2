# A2 — Sistemik Figür-Bağımlı Süpürme (kör-yargı)

**Tarih:** 2 Haziran 2026
**Track:** Track 1 / A2
**Amaç:** Flag beklemeden, beta havuzundaki figür-bağımlı yanlış-negatifleri yakala.

## Yöntem

1. **Aday tespiti (deterministik):** Beta havuzu (2,690) içinde güçlü
   figür-atıf ifadesi ("şekildeki", "grafikte", "şekilde verilen", "şemada",
   "tablodaki", "koordinat düzlemin") içeren sorular → **36 aday**
   (GEOMETRI 28, MATEMATIK 5, GENEL 2, FIZIK 1).
   - Geniş anahtar (şekil/tablo/yukarıda) = 1,220 ama çok gürültülü
     (false-positive yüksek) → kullanılmadı.
2. **Kör-yargı (dairesellik panzehiri):** 36 aday cevap anahtarı GÖRÜLMEDEN
   bir ajana yargılatıldı — "figür gizliyken (frontend `false &&`) metin+şık
   ile çözülebilir mi?"

## Sonuç

| Verdict | Sayı |
|---------|------|
| SOLVABLE | **35** |
| NEEDS_FIGURE | **1** |
| UNSURE | 0 |

35 "SOLVABLE": analitik geometri — "grafikte/koordinat düzleminde" yalnız
çerçeve, gerekli koordinat/denklem metinde mevcut. **verified_core'un
"figürsüz" filtresi DOĞRU çalışmış.**

1 NEEDS_FIGURE (`5a3db833`, GEOMETRI): "Aşağıdaki şemada ABC üçgeni
verilmiştir. Hangisi doğru değildir?" — üçgenin şekli görülmeden
(AB=AC mi vb.) çözülemez. Spot-check ile doğrulandı.

## Yapılan

- Backup: `question_bank_a2_figure_sweep_backup_20260602` (1 satır)
- 1 soru → `verified_provisional="false"` + `beta_pull{reason:figure_needed,
  source:a2_blind_judge}`. correct_answer DOKUNULMADI.
- Beta havuzu: **2690 → 2689**

## Değerlendirme

Beta havuzu büyük ölçüde **figür-temiz**. A1'in 35 öğrenci-flag'i gerçek
figür-bağımlıları yakaladı; A2 yalnız 1 ek yanlış-negatif buldu. Geniş
keyword setine (1,220) kör-yargı yapmak düşük getirili (çoğu SOLVABLE
çıkacak) → yapılmadı. Figür-bağımlılık artık birincil beta kirleticisi değil.

## Sonraki

- **A3:** Curator manuel kuyruğu (202 concept cevap-hatası + splits +
  wrong_answer/circular flag'leri).

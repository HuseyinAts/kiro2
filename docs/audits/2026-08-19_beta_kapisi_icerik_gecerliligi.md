# Beta kapısının içerik geçerliliği — 40 soruluk stratifiye okuma

**Tarih:** 19 Ağustos 2026 · **Bağlam:** Y4 (zorluk kalibrasyonu) Adım 2 pilotu
**Sonuç:** Y4 **anlamsız** — kalibre edilecek havuz servis edilebilir değil.

---

## Methodology

| Alan | Değer |
|---|---|
| Evren | `mv_safe_for_beta` (öğrenci kapısı) **27.073** satır |
| Örneklem | 5 ders × 8 soru = **40** (MATEMATIK, TURKCE, FIZIK, EDEBIYAT, GEOMETRI) |
| Seçim | `ORDER BY md5(qb.id::text) LIMIT 8` → deterministik, tekrarlanabilir |
| Truncation | **YOK** — soru metni ve 5 seçenek tam (altın kural, 14 May 2026 vakası) |
| Kontrol kolu | `SELECT count(*) FROM mv_safe_for_beta` = 27.073 (>0) → örneklem geçerli |
| Yargılayan | Claude (bu oturum), her soru tek tek okundu; aritmetiği elle doğrulandı |

Ham örneklem: bu commit'te `docs/audits/2026-08-19_beta_kapisi_orneklem.txt`.

---

## Sonuç: 40'ın **0'ı** servis edilebilir

| Sınıf | Adet | Oran |
|---|---|---|
| Yanıtlanabilir **ve** cevap anahtarı doğru | **0** | %0 |
| Yanıtlanabilir ama **cevap anahtarı YANLIŞ** | **5** | %12,5 |
| Yanıtlanamaz / bozuk / soru değil | **35** | %87,5 |

### Cevap anahtarı yanlış olan 5 (aritmetik elle doğrulandı)

| Soru | Doğrusu | DB | Kanıt |
|---|---|---|---|
| `MATEMATIK-7` | **A** (`2x²+2`) | D | `f(x)=x²+2x+1`, `f(-x)=x²-2x+1` → toplam `2x²+2` |
| `FIZIK-3` | **A** | B | Gaz ısıtılınca hacim ve/veya basınç **artar**; B "ikisi de azalır" diyor |
| `GEOMETRI-4` | **E** (8 cm) | D | Çevre 24, bir kenar 4 → `2(4+x)=24` → `x=8` |
| `GEOMETRI-7` | **A** (180°) | C | Üçgenin iç açıları toplamı 180° |
| `GEOMETRI-8` | **C** (20 cm) | E | `a` zaten A'nın karşısındaki kenar, `a=20` verilmiş |

### 35 çöpün başlıca kalıpları

- **Soru değil, başlık/özet parçası:** `MATEMATIK-3` "Parabol (Kısmi Özet)", `FIZIK-5` "MANİYETİZMA MELER ÖĞRENİCİGİZ?"
- **Seçenekler birbirinin kopyası:** `EDEBIYAT-1` (B=C=D=E), `EDEBIYAT-2` (5'i de aynı), `EDEBIYAT-5`, `FIZIK-4` (A=C=E)
- **10'un kuvvetleri şıkkı** (uydurma imzası): `MATEMATIK-1` (100/1000/10⁴/10⁵/10⁶), `FIZIK-1` (148.9 / 148.90 / 148.900 …)
- **Anlamsız Türkçe / yabancı kelime:** `FIZIK-6` "Präzesente vla. oğur for evet çöse servosu", `TURKCE-8` "RİALİTİ ŞOWLARININ DEPREMLEŞİMLİ TAKİMLARINA", `MATEMATIK-4` "eşitkenler"
- **Veri yok, yanıtlanamaz:** `GEOMETRI-1` (kutu kenarı), `GEOMETRI-3` (gölün yüksekliği), `TURKCE-6` (paragraf **eksik**)
- **Kendi içinde çelişik:** `GEOMETRI-2` (aynı açı hem 90° hem 60°), `GEOMETRI-5` (`360-90-36=135` — aritmetik **yanlış**, 234)
- **Aritmetik olarak imkânsız:** `TURKCE-7` (fark 11, en büyük şık 6)
- **Ders etiketi yanlış:** `FIZIK-1` coğrafya, `FIZIK-8`/`EDEBIYAT-4` geometri, `MATEMATIK-8` kimya
- **Figür/tablo bağımlı, figür yok:** `MATEMATIK-2`, `MATEMATIK-6`, `EDEBIYAT-6`
- **Uygunsuz içerik:** `EDEBIYAT-3` ("cinsel görsel data")

---

## Bu bir örneklem şansı DEĞİL — kapı sistematik

Örneklem yanlılığı hipotezi tek sorguyla çürütüldü:

```
mv_safe_for_beta kapisinda  source_book NULL = 27.073 / 27.073   (DOLU = 0)
                            auto_imported=true = 27.073 / 27.073
                            student_coherent=true = 27.073 / 27.073
TUM question_bank           auto_imported=true = 36.967 / 36.967
```

Yani:

1. **Hiçbir sorunun kaynak kitabı yok.** CLAUDE.md'nin anlattığı "405 kaynak kitaptan derlenmiş" korpus **bu DB'de değil**.
2. **36.967 satırın 36.967'si `auto_imported`.** Tamamı otomatik üretim/içe-aktarma.
3. **`student_coherent=true` HAK EDİLMEMİŞ.** Kapının dayandığı bayrak 27.073 satıra toptan basılmış; okunan 40'ın en az 35'inde **yanlış**.
4. Aynı satırlar `quality_review_status='auto_judged_high'` taşıyor — kalite hattı bunları **onaylamış**.

Bu, 31 May 2026'da kaydedilen sınıfın (`gold pool ~%61 öğrenci-çöp`, `gerçek temiz ~%3,2 vs "%100 PASS"`) daha kötü hâli ve muhtemelen **5 Ağu 2026 içerik kaybının** (takipsiz `TRUNCATE`) ardından konan sentetik dolgu.

---

## Gerçek korpus KAYIP DEĞİL — diskte duruyor

```
d-dataset/eslesmis_sorucevap.jsonl   116 MB   77.336 satir
  anahtarlar: book_name, page_number, question_number, answer, text,
              options, quality_score, is_valid, confidence_level, ...
backups/kiro2_pre_schema_restore_20260727.dump   976 MB (pre-split, 76 kolon)
```

Yani sorun **kurtarma** sorunudur, yeniden-üretme sorunu değil.

---

## Sonuçlar (öncelik sırasını değiştirir)

| Kalem | Durum |
|---|---|
| **Y4 (zorluk kalibrasyonu)** | **ANLAMSIZ** — 0/40 servis edilebilir havuzun zorluğunu kalibre etmek değer üretmez. Askıya alınmalı. |
| **Y2 (CAT/yerleştirme JOIN göçü)** | Kod doğru ve gerekli, ama **çöp servis ediyor**. Değeri içerik düzelene kadar 0. |
| **B2C açılışı** | Bu havuzla **kesinlikle açılamaz**: öğrenci parasını verip yanıtlanamaz soru ve yanlış cevap anahtarı alır. |
| **YENİ P0** | Beta kapısının içeriğini gerçek korpustan yeniden kur; `student_coherent` gibi hak edilmemiş bayrakları geçersiz kıl. |

## Bekçi boşluğu

Bu durumu yakalayacak **hiçbir test yok**. Hacim bekçisi var (satır sayısı), içerik geçerliliği bekçisi yok — bu yüzden 27.073 satır "kapıdan geçti" ve kimse fark etmedi. `mv_safe_for_beta` içinden örneklem alıp
yanıtlanabilirlik/şık-tekrarı/anahtar-tutarlılığı sınayan bir bekçi, bu sınıfı CI'da kırmızıya çevirirdi.

# Y11 sayısal-ders yargı turu — 240 soruluk MALİYET + KESİNLİK pilotu

**Tarih:** 19 Ağustos 2026 · **Oturum:** S232-C
**Karar:** Tam tur **TEK YARGIÇ + DB anahtarı** kuralıyla koşulacak (~101M token).
**Ham örneklem:** `docs/audits/2026-08-19_y11_sayisal_pilot_KOR.txt` (240 soru, anahtarsız)
**Alet:** `backend/scripts/quality/y11_sayisal_pilot_uret.sql`

---

## Evren ve tahsis

`kiro2_temp` kapı eşdeğeri, yalnız sayısal dersler = **24.954**
(MATEMATIK 14.119 · KIMYA 4.419 · FIZIK 3.468 · GEOMETRI 2.948)

Pilot orantılı: MAT 136 / KIM 42 / FIZ 33 / GEO 29 = **240**.
Tuz `y11pilot` — önceki iki çekimden (`y12salt`, `y11s232`) farklı. Anahtar sızıntısı **0**.

---

## Sonuç (iki bağımsız kör tur, n=240)

| Sınıf | Adet | Oran |
|---|---|---|
| **KABUL** (A = B = DB anahtarı) | **178** | **%74,2** |
| Çöp (iki tur da yanıtlanamaz dedi) | 42 | %17,5 |
| **FİGÜR** (ayrı sınıf, çöp değil) | 12 | %5,0 |
| Ayrışma (hakem gerekli) | 5 | %2,1 |
| Anahtar uyuşmaz | 3 | %1,2 |

**İki tur mutabakatı: %92,9.**

### Ders kırılımı

| Ders | n | Kabul | Çöp | Figür | Ayrışma |
|---|---|---|---|---|---|
| MATEMATIK | 136 | 99 (**%73**) | 25 | 8 | 3 |
| KIMYA | 42 | 36 (**%86**) | 4 | 1 | 1 |
| FIZIK | 33 | 27 (**%82**) | 4 | 1 | 0 |
| GEOMETRI | 29 | 16 (**%55**) | 9 | 2 | 1 |

GEOMETRI belirgin şekilde en kirli — tam turda ayrı ele alınmalı.

### Nokta-kontrol (deponun apply-öncesi kapısı): **5/5**

Kabul edilen 5 soru Claude tarafından bağımsız çözüldü, 5'i de DB anahtarıyla uyuştu:
`FIZIK-17` 2kW×2sa×30=120 kWh×0,75=90 TL → C · `GEOMETRI-11` √(25+144)=13 → E ·
`KIMYA-19` hidrojen bağı F/O/N ister, HCl → B · `MATEMATIK-7` a>8 ∨ a<−2 → 9+(−3)=6 → D ·
`MATEMATIK-63` 2. çekilişte kalan 8 karttan 5'i mutfak → 5/8 → E.

---

## 🔴 İKİNCİ YARGIÇ FİYATINI HAK ETMİYOR — ölçüldü

| Kural | Kabul | Fark |
|---|---|---|
| TEK yargıç + DB anahtarı | 179 / 240 (%74,6) | — |
| İKİ yargıç + DB anahtarı | 178 / 240 (%74,2) | **1 karar (%0,4)** |

İkinci yargıç 240 kararın **yalnız 1'ini** değiştirdi (`MATEMATIK-129` — B turu
"doğru cevap şıklarda yok" dedi) ve maliyeti **ikiye katlıyor**.

Bu, deponun kayıtlı dersinin doğrulanmasıdır:
**"Blind-solve A-bias: same-model DISPUTE ≠ DB hatası; farklı-model 2. sinyal şart."**
Aynı modelden ikinci yargıç bağımsız sinyal taşımıyor. Asıl ikinci kaynak zaten
**kitabın cevap anahtarı**; yargıcın onunla buluşması hâlihazırda iki-kaynak mutabakatı.

⚠️ **Sınır:** S232-B'deki n=43 kalibrasyonunda "ikinci yargıç" **ana bağlamdaki Claude**
idi ve 3/32 yanlış kabulü yakalamıştı (%9,4). Burada ikinci yargıç aynı modelden bir
alt-ajan ve yalnız %0,4 yakaladı. Yani **farklı-perspektif** yargıç değerli,
**aynı-model** yargıç değil. Tam turda kalite güvencesi ikinci ajan turu değil,
**parti başına insan/ana-bağlam nokta-kontrolü** olmalı.

---

## Maliyet (ölçüldü, tahmin değil)

| Kalem | Değer |
|---|---|
| Pilot toplam token | **1.936.949** |
| Yargı sayısı | 480 (240 × 2 tur) |
| **Yargı başına** | **4.035 token** |
| Önceki tur (sıkılaştırılmamış istem) | 8.169 / yargı |
| **Sıkılaştırmanın kazancı** | **%51 düşüş** |
| 24.954 soru × İKİ yargıç | **201M token** |
| **24.954 soru × TEK yargıç** | **101M token** |

Sıkılaştırma = gerekçe ≤15 kelime + "gereksiz keşif yapma, dosyayı bir kez oku".

---

## Tam tur için beklenen çıktı

Verim %74,6 → **~18.600 kabul edilmiş soru**, artı ~1.250 figür sınıfı
(görselleri mevcut, ayrı değerlendirilecek).

Karşılaştırma: canlı kapı **27.073 satır / 0 servis edilebilir**.

---

## Tam tur tasarımı (uygulanacak)

1. **Tek yargıç** + DB anahtarı mutabakatı. Ders ders, GEOMETRI ayrı ele alınacak (%55).
2. Parti başına **5 nokta-kontrol** ana bağlamda (kapı: 5/5).
3. Verdikt **ek tabloya** yazılacak — soru içeriği DEĞİŞTİRİLMEYECEK (additive, geri alınabilir).
4. `FIGUR` sınıfı ayrı tutulacak; görselleri mevcut olduğu için çöp değil.
5. Ayrışma/anahtar-uyuşmaz sınıfı (%3,3) kuyruğa alınacak, otomatik kabul/red YOK.

---

## İlgili

- `docs/audits/2026-08-19_y11_kaynak_olcumu.md` — `kiro2_temp` %65-75, eşik %95 karşılanmıyor
- `docs/audits/2026-08-19_y12_kontrol_kolu.md` — Y12 metrik doğrulama kapısı

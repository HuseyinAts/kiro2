# Y11 ön koşulu — `kiro2_temp` kaynak ölçümü (60 soruluk orantılı stratifiye kör okuma)

**Tarih:** 19 Ağustos 2026 · **Oturum:** S232
**Karar:** Y11 **DÜZ GÖÇ OLARAK YAPILAMAZ** — eşik karşılanmıyor.
**Ham örneklem:** `docs/audits/2026-08-19_kiro2temp_orneklem_KOR.txt` (64 soru, anahtarsız)
**Aletler:** `backend/scripts/quality/y11_orneklem_uret.sql` · `y11_kitap_kontrol_kolu.sql`

---

## Kullanıcının önceden ilan ettiği eşik

> yeni 40 örneklemde **≥38/40** yanıtlanabilir-ve-doğru · `source_book` NULL **< %5** ·
> `student_coherent` **tek değer olmayacak**

Eşiğin fix'ten ÖNCE ilan edilmiş olması bu deponun kuralıdır
(`L-s229-maskenin-altinda-maske`). Bu belge o eşiğe karşı ölçümdür.

---

## Methodology

| Alan | Değer |
|---|---|
| Evren | `kiro2_temp` kapı eşdeğeri: `quality_review_status IN ('human_verified','auto_judged_high') AND is_active` = **34.982** |
| Örneklem | **60** orantılı stratifiye (MATEMATIK 24 · KIMYA 8 · FIZIK 6 · TURKCE 6 · GEOMETRI 5 · BIYOLOJI 3 · TARIH 3 · EDEBIYAT 3 · COGRAFYA 1 · SOSYAL 1) |
| + Kapsama | **4** (GENEL 2 + FEN 2) — popülasyonun %0,85'i, **orana GİRMEZ** |
| Seçim | `row_number() OVER (PARTITION BY subject_area ORDER BY md5(id::text \|\| 'y11s232'))` — deterministik, tekrarlanabilir |
| Tuz | `y11s232` — S232'de okunan 12 sorunun tuzundan (`y12salt`) **farklı** → bağımsız çekim |
| Truncation | **YOK** (14 May 2026 altın kuralı) |
| Yargı | **KÖR**: cevap anahtarı çıktı dosyasına yazılmadı (`grep` ile 0 sızıntı doğrulandı) |
| Yargılayanlar | Claude (elle, 64/64) + 8 paralel ajan (2 çerçeveleme × 4 parti) |

**S231'in örneklem kusuru düzeltildi:** S231 canlı kapının %65,8'ini oluşturan `Genel`
dersini hiç örneklememişti. Bu turda tahsis orantılı yapıldı ve tüm dersler kapsandı.

---

## Sonuç — eşik KARŞILANMIYOR

| Ölçüm | Servis edilebilir | Yöntem |
|---|---|---|
| **Claude, kör, figürsüz** | **39/60 = %65,0** | 19 yanıtlanamaz + 2 anahtar yanlış |
| **Ajanlar, kör, figürsüz** | **43/60 = %71,7** | 16 yanıtlanamaz + 1 anahtar yanlış |
| **Claude, figür düzeltmeli** | **45/60 = %75,0** | 6 figür-bağımlı soru kurtarıldı |
| Kapsama (`GENEL`+`FEN`) | **0/4** | orana dahil değil |

**Eşik %95 · ölçülen %65-75.** Üç bağımsız yargı da eşiğin çok altında yakınsıyor.

Düz göç yapılırsa 34.982 satırın **~9.000-12.000'i** servis edilemez içerik olarak
öğrenciye açılır.

### Eşiğin diğer iki maddesi GEÇİYOR
- `source_book` NULL oranı: **0,0000** (eşik <%5) ✅
- `student_coherent` benzeri tek-değerli bayrak: `pipeline_metadata` distinct **34.916** ✅

Yani kusur köken/izlenebilirlikte değil, **içerik kalitesinde**.

---

## 🔴 KENDİ ÖLÇÜMÜMDE KUSUR BULUNDU VE DÜZELTİLDİ — figür bağımlılığı

İlk yargımda 19 soruyu "yanıtlanamaz" saydım. Bunların **6'sı figür-bağımlıydı** ve
ben yalnız metne bakmıştım. Ölçüldü:

    kiro2_temp: question_image_url dolu = 34.901 / 34.982  (%99,8)
    diskte    : d-dataset/output/crops → 528.651 PNG / 430 dizin
    container : C:\...\d-dataset\output\crops → /app/static/crops (ro) BAĞLI
    6 sorunun 6'sında da görsel dosyası MEVCUT (4 kırpılmış + 2 tam sayfa)

İki görsel açılıp bakıldı (`345 Geometri p0225_q01` eşkenar üçgen boyalı bölgeler,
`C1CELL Matematik p0284_q01` A×B kartezyen grafiği) — **ikisi de soruyu kurtarıyor**.

Bu, canlı kapıyla arasındaki en keskin farklardan biri: canlıda
`question_image_url` **0/27.073**, burada **34.901/34.982**. Canlıdaki
"figür-bağımlı ama figür yok" sınıfı orada gerçek kusur, burada değil.

---

## Kalan kusur sınıfları (figürler hesaba katıldıktan SONRA, 13/60 = %21,7)

| Sınıf | Örnek |
|---|---|
| Anlamsız Türkçe / uydurma terim | `"Atomojiklerin atomik ağırlıkları"` · `"denge notası (D)"` · `"Açır modelde değişik yapılandırılarak"` |
| **Geometrik olarak imkânsız veri** | `A=60°, AB=3, BC=2` → kosinüs teoremi `b²−3b+5=0`, **diskriminant −11**; böyle bir üçgen yok, hiçbir şık denklemi sağlamıyor |
| Birebir aynı iki şık | `MATEMATIK-18` C=E · `TARIH-2` B=C=D=E |
| Eksik önceki-veri | `"Daha önce verilen verilerle birlikte..."` — o veri yok |
| Ders etiketi yanlış + veri yok | `TURKCE-5` geometri sorusu, veri yok · `EDEBIYAT-3` matematik sorusu |
| Şıkla eşleşmeyen sonuç | `MATEMATIK-11` "yuvarlak tabanlı prizma" V=375π, hiçbir şık yakın değil |

---

## 🔴 ÇÜRÜTÜLEN HİPOTEZ — çöp kitap düzeyinde yoğunlaşmıyor

**Hipotez:** örneklemde `FIZIK-1`+`FIZIK-2` aynı kitaptan, `TARIH-2`+`TARIH-3` aynı
kitaptan, `FEN-1`+`FEN-2` aynı kitaptan bozuk çıktı → çöp kitap düzeyinde
yoğunlaşmış olabilir → **deterministik kitap elemesi** filtre olabilir.

**Kontrol kolu (`y11_kitap_kontrol_kolu.sql`): ÇÜRÜTÜLDÜ.**

| Kitap (insan yargısıyla 2/2 bozuk) | Y12 mekanik bayrak | Mekanik sıra |
|---|---|---|
| Neofizik Ayt Fizik Soru Bankası 2025 | %3,7 | **80 / 350** |
| Esen Aps Tyt Ayt Tarih Soru Bankası | %1,8 | **127 / 350** |
| Aramot Tyt 2023 Fen Bilimleri Model Sorular | %1,6 | **135 / 350** |

Mekanik olarak **en kirli** kitaplar ise Türkçe/Dil Bilgisi/Paragraf kitapları
(en yüksek %24,6) — örneklemimde özellikle bozuk çıkmayanlar. Yani mekanik kitap
sıralaması insan yargısını **öngörmüyor**; kitap elemesi gerçek çöpü yerinde
bırakır ve muhtemelen sağlam kitapları atar.

Yoğunlaşma özeti: `>%20` = 4 kitap / 121 soru · `>%10` = 25 kitap / 1.347 soru ·
`<=%3` = 255 kitap / 26.230 soru · genel bayrak **%2,40**.

---

## Y12'nin bu havuzdaki erişimi — 9x boşluk

Y12'nin doğrulanmış 6 mekanik kuralı `kiro2_temp`'te **%2,40-2,56** bayrak veriyor.
İnsan yargısıyla ölçülen gerçek çöp **%21,7-35**. Yani mekanik filtre gerçek
kusurun **onda birinden azını** görüyor.

Bu beklenen bir sonuçtu ve önceden ölçülmüştü (kural kümesinin duyarlılığı **%30**,
`2026-08-19_y12_kontrol_kolu.md`). Somut anlamı: **Y12 tek başına göç filtresi
olamaz** ve olması da hedeflenmemişti — Y12 bir *bekçidir*, bir *ayıklayıcı* değil.

---

## Kalan tek yol: ölçekte semantik yargı

%70 → %95 için kalan tek yöntem, bu deponun **zaten başarıyla koştuğu** desen:
kör çözüm + konsensüs + nokta-kontrol, ders ders, backup tablosu ve geri
alınabilir UPDATE ile (S182-S198: MATEMATIK, GEOMETRI, FIZIK, KIMYA, TURKCE,
EDEBIYAT turları).

Ölçek: ~34.982 soru. Bu **çok oturumlu bir proje**, bu turda başlatılmadı —
veri değiştiren, pahalı ve ayrı onay gerektiren bir iş.

---

## Ölçüm aletinde arıza (dürüst kayıt)

İki bağımsız kör tur (A: doğrudan çözüm, B: eleme) tasarlandı ve 8 ajanın 8'i
döndü. **Ama turlar ayrıştırılamadı:** workflow journal'ı ajan etiketini hash
olarak saklıyor (`key: "v2:35c02da1..."`), `is` alanı sonuç nesnesinde yok, iki
tur aynı sözlüğe yazıp üzerine bindi (`turA=64, turB=0`). Dolayısıyla
**tur-arası anlaşmazlık sinyali ÜRETİLEMEDİ**; ajan sonucu tek kör tur olarak
geçerlidir. Bir sonraki turda tur kimliği **sonuç şemasının içine** konmalı.

---

## İlgili

- `docs/audits/2026-08-19_beta_kapisi_icerik_gecerliligi.md` — canlı kapı 0/40 (S231)
- `docs/audits/2026-08-19_y12_kontrol_kolu.md` — Y12 metrik doğrulama kapısı
- `backend/tests/integration/test_icerik_gecerliligi.py` — Y12 bekçisi (8 xfail)

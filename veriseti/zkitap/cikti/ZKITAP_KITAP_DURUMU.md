# zkitap -- KITAP DURUM RAPORU (kalici kayit)

Tarih: 23 Eyl 2026. Kapsam: `veriseti/zkitap/screenshots/` altindaki 280 klasor (278'inde PNG var; `Edebiyat Sokagi Ayt Yeni Nesil Soru Bankasi` ve `kitap_20251206_181525` bos). DB durumu: canli DB'den 23 Eyl 2026 03:48'de alinan `source_book` sayimi (salt-okunur).

Bu belge onceki envanteri (`ZKITAP_ENVANTER.md`, klasor ADINA gore eslestirilmisti, yerel) ve `ZKITAP_ISLEME_PLANI.md` / `GEO_DALGA_D_KESIF.md` icindeki iki baski hukmunu OLCUMLE duzeltir (bolum 2). Olcum verisinin tamami: `zkitap_kitap_durumu_olcum.json`.

## 1. Ozet

| kalem | adet |
|---|---|
| PNG iceren klasor | 278 |
| tekil kitap (ayni icerikli klasorler birlestirildi) | 237 |
| modern hatla islenmis ve DB'ye PASIF ithal edilmis | 13 kitap (345 Geometri 2 cilt = 14 grup) |
| islenmis, ithal EDILMEMIS (Orijinal 2024 Geometri, Faz 3 bitti) | 1 |
| islenmemis | 222 |
| -- bunlardan DB'de HIC satiri olmayan | 100 |
| -- bunlardan eski hattan deneme satiri olan (klasor adiyla `source_book`) | 122 |
| kitap olmayan / kullanilamaz klasor | 6 |

Modern ithal toplami (13 kitap): **18273 satir**. Canli DB'deki toplam `source_book` satiri: 24330 (199 farkli ad).

## 2. Onceki belgelerdeki hukumlerin DUZELTILMESI (olculdu + gozle dogrulandi)

1. **`Mikro Orijinal-Tyt Ayt-Geometri Soru Bankasi 2` (plan #8) islenmis Mikro 2025 kitabinin ONCEKI BASKISIDIR, ayri kitap/ikinci cilt DEGIL.** `GEO_DALGA_D_KESIF.md` (b) ayni sayfa NUMARASINDAKI iki sayfayi karsilastirip 'tamamen farkli' demisti; oysa ayni testler birkac sayfa kaymis durumda. Sekme basligi: `MIKRO - ORJINAL - 2024 - TYT - AYT - GEOMETRI - SB`. Olcum: 16 ornek sayfanin 11-13'u islenmis 2025 baskisinda bulundu (sayfa kaymasi 0-7). Gozle: 2024 s247 = 2025 s243 (Kare, Ornek 1-6 birebir), 2024 s399 = 2025 s399 (Piramitler), 2024 s94 = 2025 s82 (Eskenar Ucgen, orneklerin cogu ayni), 2024 s150 = 2025 s145 (Kazanim Testi, Ucgende Alan). **Islenirse sorularin cogu ikinci kez girer.**
2. **`Orijinal-2024-Geometri Soru Bankasi` (#3) ile `Orijinal-Tyt Ayt Geometri Soru Bankasi` (#4) 'ayni yakalama' DEGIL**, 2024 ve 2025 baskilaridir (`GEO_ORIJINAL_2024_FAZ1.md` bolum 18.1 bunu zaten dogru yaziyor; plan ve kesif fisleri eski hukmu tasiyor). 432 sayfanin tamami ayni indekste karsilastirildi: kart piksel farki medyani %1,9, 87 sayfada >%5. Gozle: s227'de 7. ve 10. sorular degismis, 8/9/11/12 ayni; s146 'OSYM'de Cikmis Sorular' sayfasinda 2025 sorulari eklenmis (9, 11, 12 yeni). Revize baski; olculen ortaklik en az %69. Kart farki orani dusuk gorunur cunku kartin cogu beyazdir; tek bir soru degisse de oran %1-3 kalir.
3. **`ACIL-TYT-AYT-Geometri Soru Bankasi` islenmis DEGIL.** Yerel envanter klasor adina gore onu islenmis ACIL 2023-2024'e eslemisti. Sekme: `ACIL - 2025 - TYT - AYT - Geometri Soru Bankasi`; icerik ortakligi %0 (`GEO_ACIL_2025_KURS_KESIF.md`: farkli ISBN, KURS serisi). Sahip karari 'ikisi de' -- sirada.
4. **345 2024 AYT Biyoloji / 345 2024 TYT Biyoloji** yerel envanterde islenmis gorunuyordu; ikisi de 2024 baskisi. Islenmis 2025 baskilariyla ortaklik: AYT en az %69 (bu olcum; `BIO_345_2024_KESIF.md` cevap dizisi hizalamasi %85,2 -- tutarli), TYT en az %72.
5. **Bilgi Sarmal AYT Edebiyat:** plan 8.1 '#6 islendi, #7 islenmedi' diyor; birincil kaynak (`BILGI_SARMAL_EDEBIYAT_YONTEM.md` satir 5, ithal araci docstring) ithal edilen baskinin **2024** klasoru (`...Soru Bankasi 2024`) oldugunu, 2023-2024 klasorunun kurtarma kanali oldugunu soyluyor. Plan satiri ters.
6. **Klasor adlari guvenilmez.** Ornekler: `Esen Ayt Tarih Soru Bankasi` = AYT Cografya; `Esen Aylik Planli Biyoloji` = 2025 APS AYT Kimya; `Esen Apt Ayt Fizik 2025` = 2025 APS AYT Biyoloji; `Esen Aps Fizik Soru Bankasi 3` = APS TYT Fizik; `Vaf Capli Paragraf` = CAP Capli Paragraf; `Bilgi Sarmali-2022-2023-Tyt-Matematik` = 2022-2023 BS **AYT** Matematik; `ACIL-2025-TYT-Soeu Bankasi` = ACIL 2025 **AYT** SB; `345 Tyt *` klasorleri 2024 baskisi. Tam eslesme bolum 7'de.

## 3. Yontem, kalibrasyon, sinirlar

* **Kimlik:** her klasorun ornek sayfalarinda okuyucu (FERNUS) aktif sekmesi (renk 207,228,255) otomatik kirpildi; 278 baslik gozle okundu. 9 ornek sayfada sekme genisligi izlendi -> klasor icinde kitap degisimi yakalandi (`Cap Ayt Tarih`: s193'ten itibaren baska baski).
* **Sayfa olcusu:** murekkep maskesi (gri<150). A'dan 16 ornek sayfa; B'nin TUM sayfalari 1/4 cozunurlukte FFT kaydirmasiyla taranir, en iyi 3 aday tam cozunurlukte +-3 px ince kaydirma ve 2 px toleransla puanlanir. Sayfa >=0.80 = ayni ya da buyuk olcude ayni.
* **Soru-blogu olcusu (yerlesimden bagimsiz):** okuyucunun mor buyutec simgesi (glif 69,39,160) her sorunun basini isaretler; blok = simgeden ayni sutundaki sonraki simgeye. Blok kendi murekkep kutusuna kirpilir, B'nin tum bloklariyla (en-boy +-10%, genislik +-25%, yogunluk +-30%) karsilastirilir. AYNI kurali: 1 px toleransli >=0.95 VEYA kati (+-1 px) >=0.70.
* **Ortaklik** = max(sayfa orani, blok orani / 0.8) -- blok olcusunun birebir ayni kitapta olculen geri cagirimi ~0.8.
* **Kalibrasyon:** bilinen piksel-ozdes cift (BS Turkce 2022-2023, iki klasor) %100; farkli denemeler (Mikro 12'li 1/10) %0; gozle FARKLI dogrulanan uc cift (ACIL geo 23-24/2025, Aromat 2023-24 Mat/2023 AYT Mat, SURE Paragraf Gunlukleri/Paragrafin Suresi) %0-5.
* **Gozle dogrulama:** 17 ciftte sayfalar yan yana acildi (esik civari ve kritik ciftler).
* **Yakalama kalitesi:** tum sayfalarda (1/4 maske) yuklenmemis gri sayfa ve art arda ayni sayfa sayildi; `Orijinal-2024-Matematik Soru Bankasi` sayfalari bayt-ozdes (sha256 ile teyit).
* **SINIR:** olcumler ALT SINIRDIR. Soru baska sayfaya tasininca, sayfa olceklenince ya da okuyucu simgesi baskida baska yere konunca olcu kacirabilir; 5 ciftte gozle olcumden fazla ortaklik goruldu (ACIL AYT Mat 19-20/20-21, ACIL Geometrinin Ilaci, PES Kurgulu/TYT-AYT Paragraf, Orijinal Analitik, Apotemi Modern Fizik). %15 alti 'bagimsiz' sayildi. Kesin soru duzeyi ortusme her kitabin kendi Faz 1'inde `soru_hash` ile olculmeli.

## 4. Yayinevine gore TUM kitaplar

Sutunlar: **durum** (ISLENDI = modern ithal / HAZIR = ithal bekliyor / ISLENMEDI); **klasor** = islenecek/islenmis en iyi yakalama; **ayni icerik** = >=%75 ortak diger klasorler (ayri islenmez); **DB** = modern ithal satir/aktif ya da eski hat deneme satiri/aktif; **ortaklik** = baska kitaplarla olculen alt sinir.

### 345 (17 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 345 2024 AYT Biyoloji Soru Bankasi | ISLENMEDI | `345 2024 Ayt Biyoloji Soru Bankasi` | 376 | - | yok | 345 2025 AYT Biyoloji SB %69 | - | SAHIP KARARI: 345 2025 AYT Biyoloji SB ile en az %69 ortak -> atla ya da yalniz farki isle |
| 345 2025 AYT Fizik SB | **ISLENDI** | `345 2025 Ayt Fizik Soru Bankasi` | 392 | `345 2024 Ayt Fizik Soru Bankasi` | modern 1308 / aktif 1297 | - | - | TAMAM (modern ithal) |
| 345 2024 AYT Kimya Soru Bankasi | ISLENMEDI | `345 2024 Ayt Kimya Soru Bankasi` | 336 | `345 2025 Ayt Kimya Soru Bankasi` | eski hat 202 / aktif 202 | - | - | ISLENEBILIR |
| 345 2024 AYT Matematik SB | ISLENMEDI | `345 2024 Ayt Matematik Soru Bankasi` | 399 | `345 2025 Ayt Matematik Soru Bankasi` | eski hat 11 / aktif 11 | - | - | ISLENEBILIR |
| 345 2024 TYT Biyoloji SB | ISLENMEDI | `345 Tyt Biyoloji Soru Bankasi` | 232 | - | yok | 345 2025 TYT Biyoloji SB %72 | - | SAHIP KARARI: 345 2025 TYT Biyoloji SB ile en az %72 ortak -> atla ya da yalniz farki isle |
| 345 2024 TYT-AYT Geometri SB | **ISLENDI** | `345 Tyt Ayt Geometri Soru Bankasi` | 440 | `345 2025 Tyt Ayt Geometri Soru Bankasi 1` | modern 2708 / aktif 2702 | - | - | TAMAM (modern ithal) |
| 345 2025 AYT Biyoloji SB | **ISLENDI** | `345 2025 Ayt Biyoloji Soru Bankasi` | 374 | - | modern 1315 / aktif 1315 | 345 2024 AYT Biyoloji Soru Bankasi %69 | - | TAMAM (modern ithal) |
| 345 2025 AYT Turk Edebiyati SB | ISLENMEDI | `345 2025 Ayt Turk Edebiyati Soru Bankasi` | 348 | - | yok | - | 20 sayfa art arda ayni (cift/takili yakalama) | ISLENEBILIR |
| 345 2025 Paragraf Sifir Risk SB | ISLENMEDI | `345 2025 Paragraf Sifir Risk Soru Bankasi` | 368 | - | eski hat 8 / aktif 8 | - | - | ISLENEBILIR |
| 345 2025 Start Matematik | ISLENMEDI | `345 2025 Start Matematik` | 323 | - | eski hat 3 / aktif 3 | - | - | ISLENEBILIR |
| 345 2025 TYT Biyoloji SB | **ISLENDI** | `345 2025 Tyt Biyoloji Soru Bankasi` | 235 | - | modern 1023 / aktif 1022 | 345 2024 TYT Biyoloji SB %72 | - | TAMAM (modern ithal) |
| 345 2025 TYT Fizik SB | ISLENMEDI | `345 2025 Tyt Fizik Soru Bankasi` | 368 | `345 Tyt Fizik Soru Bankasi` | yok | - | - | ISLENEBILIR |
| 345 2025 TYT Kimya SB | ISLENMEDI | `345 2025 Tyt Kimya Soru Bankasi` | 280 | `345 Tyt Kimya Soru Bankasi` | eski hat 294 / aktif 294 | - | - | ISLENEBILIR |
| 345 2025 TYT Matematik SB | ISLENMEDI | `345 2025 Tyt Matematik Soru Bankasi` | 422 | `345 2024 Tyt Matematik Soru Bankasi` | eski hat 18 / aktif 18 | - | - | ISLENEBILIR |
| 345 2025 TYT Sosyal Bilgiler SB | ISLENMEDI | `345 2025 Tyt Sosyal Bilgiler Soru Bankasi` | 312 | `345 Tyt Sosyal Bilgiler Soru Bankasi` | eski hat 26 / aktif 26 | - | - | ISLENEBILIR |
| 345 2025 TYT Turkce SB | ISLENMEDI | `345 2025 Tyt Turkce Soru Bankasi` | 440 | `345 Tyt Turkce Soru Bankasi` | eski hat 18 / aktif 18 | - | - | ISLENEBILIR |
| 345 2025 TYT-AYT Geometri SB 2 | **ISLENDI** | `345 Tyt Ayt Geometri Soru Bankasi 2` | 336 | - | modern 2708 / aktif 2702 | - | - | TAMAM (modern ithal) |

### ACIL (23 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2019-2020 ACIL AYT Matematik Soru Bankasi | ISLENMEDI | `2019-2020-ACIL-AYT-Matematik Soru Bankasi` | 433 | - | eski hat 4 / aktif 4 | 2020-2021 ACIL AYT Matematik Soru Bankasi %31 (gozle) | - | AILE: yalniz biri islenmeli (2020-2021 ACIL AYT Matematik Soru Bankasi %31 gozle) |
| 2019-2020 Acil Matematigin Ilaci-1 | ISLENMEDI | `2019-2020-Acil Matematigin ilaci-1` | 382 | - | eski hat 21 / aktif 21 | 2023-2024 ACIL TYT Matematigin Ilaci %31 | - | AILE: yalniz biri islenmeli (2023-2024 ACIL TYT Matematigin Ilaci %31) |
| 2019-2020 Acil TYT Soru Bankasi | ISLENMEDI | `2019-2020-ACIL-TYT-Soru Bankasi` | 432 | - | eski hat 9 / aktif 9 | - | - | ISLENEBILIR |
| 2020-2021 ACIL AYT Matematik Soru Bankasi | ISLENMEDI | `2020-2021-ACIL-AYT Matematik Soru Bankasi` | 449 | - | eski hat 5 / aktif 5 | 2019-2020 ACIL AYT Matematik Soru Bankasi %31 (gozle) | - | AILE: yalniz biri islenmeli (2019-2020 ACIL AYT Matematik Soru Bankasi %31 gozle) |
| 2020-2021 ACIL TYT Matematik Soru Bankasi | ISLENMEDI | `2020-2021-ACIL-TYT Matematik Soru Bankasi` | 448 | - | eski hat 27 / aktif 27 | - | - | ISLENEBILIR |
| 2020-2021 Acil Problemlerin Ilaci | ISLENMEDI | `2020-2021-Acil-Problemlerin ilaci` | 191 | - | eski hat 9 / aktif 9 | ACIL 2025 Problemlerin Ilaci %82 | - | AILE: yalniz biri islenmeli (ACIL 2025 Problemlerin Ilaci %82) |
| 2020-2021 Acil TYT-AYT Geometrinin Ilaci Soru Bankasi | ISLENMEDI | `2020-2021-Acil-Tyt Ayt Geometrinin ilaci Soru Bankasi` | 288 | - | yok | 2023-2024 ACIL TYT-AYT Geometrinin Ilaci %17 (gozle) | - | AILE: yalniz biri islenmeli (2023-2024 ACIL TYT-AYT Geometrinin Ilaci %17 gozle) |
| 2022-2023 ACIL Analitik Geometri | ISLENMEDI | `2022-2023-ACIL-Analitik Geometri` | 176 | - | eski hat 1 / aktif 1 | - | - | ISLENEBILIR |
| 2022-2023 ACIL Kati Cisimler | ISLENMEDI | `2022-2023-ACIL-Kati Cisimler` | 160 | - | yok | - | - | ISLENEBILIR |
| 2023-2024 ACIL AYT Matematik Soru Bankasi | ISLENMEDI | `2023-2024 ACIL- AYT Matematik Soru Bankasi` | 417 | - | eski hat 11 / aktif 11 | ACIL 2025 AYT Soru Bankasi %36 | - | AILE: yalniz biri islenmeli (ACIL 2025 AYT Soru Bankasi %36) |
| 2023-2024 ACIL TYT Matematigin Ilaci | ISLENMEDI | `2023-2024-ACIL-TYT-Matematigin Ilaci` | 324 | `2019-2020-Acil-Matematigin ilaci Tyt Matematik Soru Bankasi`; `2019-2020-Acil-Matematigin ilaci Tyt Matematik Soru Bankasi` | eski hat 58 / aktif 58 | 2019-2020 Acil Matematigin Ilaci-1 %31 | `2019-2020-Acil-Matematigin ilaci Tyt Matematik Soru Bankasi`: 18 sayfa art arda ayni (cift/takili yakalama) | AILE: yalniz biri islenmeli (2019-2020 Acil Matematigin Ilaci-1 %31) |
| 2023-2024 ACIL TYT Matematik Soru Bankasi | ISLENMEDI | `2023-2024-ACIL-TYT Matematik Soru Bankasi` | 416 | - | eski hat 29 / aktif 29 | ACIL 2025 TYT Soru Bankasi %33 | - | AILE: yalniz biri islenmeli (ACIL 2025 TYT Soru Bankasi %33) |
| 2023-2024 ACIL TYT-AYT Geometri Soru Bankasi | **ISLENDI** | `2023-2024-ACIL-TYT-AYT Geometri Soru Bankasi` | 448 | - | modern 1730 / aktif 1728 | - | - | TAMAM (modern ithal) |
| 2023-2024 ACIL TYT-AYT Geometrinin Ilaci | ISLENMEDI | `2023-2024-ACIL-TYT-AYT-Geometrinin Ilaci` | 290 | - | yok | 2020-2021 Acil TYT-AYT Geometrinin Ilaci Soru Bankasi %17 (gozle) | - | AILE: yalniz biri islenmeli (2020-2021 Acil TYT-AYT Geometrinin Ilaci Soru Bankasi %17 gozle) |
| 2024 ACIL TYT Matematik Geometri Kitap-1 | ISLENMEDI | `2024-ACIL TYT Matematik Geometri Kitap-1` | 208 | - | eski hat 12 / aktif 12 | - | - | ISLENEBILIR |
| ACIL 2025 AYT Soru Bankasi | ISLENMEDI | `ACIL-2025-TYT-Soeu Bankasi` | 416 | - | eski hat 11 / aktif 11 | 2023-2024 ACIL AYT Matematik Soru Bankasi %36 | - | AILE: yalniz biri islenmeli (2023-2024 ACIL AYT Matematik Soru Bankasi %36) |
| ACIL 2025 Matematigin Ilaci Polinom | ISLENMEDI | `ACIL-2025-Matematigin Ilaci Polinom` | 288 | - | eski hat 53 / aktif 53 | - | - | ISLENEBILIR |
| ACIL 2025 Matematigin Ilaci Sayilar-1 | ISLENMEDI | `ACIL-2025-Matematigin Ilaci Sayilar-1` | 176 | - | eski hat 23 / aktif 23 | - | - | ISLENEBILIR |
| ACIL 2025 Matematigin Ilaci Sayilar-2 | ISLENMEDI | `ACIL-2025-Matematigin Ilaci Sayilar-2` | 192 | - | eski hat 53 / aktif 53 | - | - | ISLENEBILIR |
| ACIL 2025 Problemlerin Ilaci | ISLENMEDI | `ACIL-2025-Problemin Ilaci` | 196 | - | eski hat 5 / aktif 5 | 2020-2021 Acil Problemlerin Ilaci %82 | - | AILE: yalniz biri islenmeli (2020-2021 Acil Problemlerin Ilaci %82) |
| ACIL 2025 TYT Soru Bankasi | ISLENMEDI | `ACIL-2025-TYT-Soru Bankasi` | 400 | - | eski hat 22 / aktif 22 | 2023-2024 ACIL TYT Matematik Soru Bankasi %33 | - | AILE: yalniz biri islenmeli (2023-2024 ACIL TYT Matematik Soru Bankasi %33) |
| ACIL 2025 TYT-AYT Geometri Soru Bankasi | ISLENMEDI | `ACIL-TYT-AYT-Geometri Soru Bankasi` | 400 | - | yok | - | - | ISLENEBILIR |
| Acil 2024 AYT Matematik Kitap-1 | ISLENMEDI | `Acil-2024-AYT Matematik Kitap-1` | 224 | - | eski hat 7 / aktif 7 | - | - | ISLENEBILIR |

### AKTIF / ALTYAPI (Kartlarla) (12 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2019-2020 Aktif 0'dan Baslayanlara Aktif Kimya | ISLENMEDI | `Aktif Ogrenme 0 Baslayanlara Kimya 2019 2020` | 368 | - | eski hat 520 / aktif 520 | - | - | ISLENEBILIR |
| 2019-2020 Aktif AYT Kimya | ISLENMEDI | `Aktif Ogrenme Ayt Kimya 2019 2020` | 416 | - | eski hat 490 / aktif 490 | - | - | ISLENEBILIR |
| 2022-2023 ALTYAPI Kartlarla TYT Fizik | ISLENMEDI | `Altyapi 2022 2023 Tyt Fizik` | 128 | - | yok | 2022-2023 Kartlarla AYT Fizik %25 | - | AILE: yalniz biri islenmeli (2022-2023 Kartlarla AYT Fizik %25) |
| 2022-2023 ALTYAPI Kartlarla TYT Kimya | ISLENMEDI | `Altyapi Tyt Kartlarla Kimya` | 176 | - | eski hat 1 / aktif 1 | - | - | ISLENEBILIR |
| 2022-2023 ALTYAPI Kartlarla TYT Tarih | ISLENMEDI | `Altyapi Tyt Kartlarla Tarih` | 192 | - | yok | - | - | ISLENEBILIR |
| 2022-2023 Kartlarla AYT Fizik | ISLENMEDI | `Altyapi 2022 2023 Kartlarla Ayt Fizik` | 144 | - | yok | 2022-2023 ALTYAPI Kartlarla TYT Fizik %25 | - | AILE: yalniz biri islenmeli (2022-2023 ALTYAPI Kartlarla TYT Fizik %25) |
| 2022-2023 Kartlarla AYT Kimya | ISLENMEDI | `Aktif Ogrenme Ayt Kartlarla Kimya 2022 2023` | 176 | - | yok | - | - | ISLENEBILIR |
| 2022-2023 Kartlarla AYT Roman Ozetleri | ISLENMEDI | `Ayt Kartlarla Roman Ozetleri 2022 2023` | 144 | - | yok | - | 15 sayfa art arda ayni (cift/takili yakalama) | ISLENEBILIR |
| 2023-2024 AKTIF Biyoloji | ISLENMEDI | `Aktif Ogrenme 2023 2024 Biyoloji` | 272 | - | yok | - | 51 sayfa art arda ayni (cift/takili yakalama) | ISLENEBILIR |
| AKTIF 2025 TYT Dil Bilgisi Soru Bankasi | **ISLENDI** | `Aktif Ogrenme Tyt Dilbilgisi Soru Bankasi 2025` | 224 | - | modern 695 / aktif 661 | - | - | TAMAM (modern ithal) |
| AKTIF 2025 TYT Fizik Soru Bankasi | ISLENMEDI | `Aktif Ogrenme 2025 Tyt Fizik Soru Bankasi` | 352 | - | yok | - | - | ISLENEBILIR |
| AKTIF 2025 TYT Paragraf Soru Bankasi | ISLENMEDI | `Aktif Ogrenme Tyt Paragraf Soru Bankasi 2025` | 144 | - | eski hat 19 / aktif 19 | - | - | ISLENEBILIR |

### APOTEMI (15 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2019-2020 APOTEMI TYT Matematik Soru Bankasi | ISLENMEDI | `2019-2020-Apotemi-Tyt Matematik Soru Bankasi` | 324 | - | eski hat 9 / aktif 9 | - | - | ISLENEBILIR |
| 2019-2020 Apotemi Modern Fizik Konu Anlatimli SB | ISLENMEDI | `Apotemi 2019 2020 Modern Fizik Konu Anlatimli Soru Bankasi` | 256 | - | yok | 2022-2023 Apotemi Modern Fizik %48 (gozle) | - | AILE: yalniz biri islenmeli (2022-2023 Apotemi Modern Fizik %48 gozle) |
| 2019-2020 Apotemi TYT-AYT Fizik Soru Bankasi | ISLENMEDI | `Apotemi 2019 2020 Tyt Ayt Fizik Soru Bankasi` | 448 | - | yok | - | - | ISLENEBILIR |
| 2019-2020 Apotemi TYT-AYT Kimya Soru Bankasi | ISLENMEDI | `Apotemi Tyt Ayt Kimya 2019-2020` | 352 | - | eski hat 345 / aktif 345 | - | - | ISLENEBILIR |
| 2020-2021 APOTEMI Modern Kimya | ISLENMEDI | `Apotemi 2020 2021 Modern Kimya` | 300 | - | eski hat 59 / aktif 59 | - | - | ISLENEBILIR |
| 2020-2021 APOTEMI TYT-AYT Geometri Maestro Soru Bankasi | ISLENMEDI | `2020-2021-Apotemi-Tyt Ayt-Geometri Maestro Soru Bankasi` | 320 | - | yok | - | - | ISLENEBILIR |
| 2021-2022 Apotemi Limit ve Sureklilik | ISLENMEDI | `2021-2022-Apotemi-Limit` | 128 | - | yok | - | - | ISLENEBILIR |
| 2021-2022 Apotemi Problemler | ISLENMEDI | `2021-2022-Apotemi-Problemler` | 240 | - | yok | - | - | ISLENEBILIR |
| 2021-2022 Apotemi Trigonometri | ISLENMEDI | `2021-2022-Apotemi-Trigonometri` | 224 | - | yok | - | - | ISLENEBILIR |
| 2022 Apotemi Integral | ISLENMEDI | `2022-Apotemi-integral` | 224 | - | yok | - | - | ISLENEBILIR |
| 2022 Apotemi Turev | ISLENMEDI | `2022-Apotemi-Turev` | 224 | - | yok | - | - | ISLENEBILIR |
| 2022-2023 APOTEMI Fonksiyonlar | ISLENMEDI | `2022-2023-Apotemi-Fonksiyonlar` | 144 | - | yok | - | - | ISLENEBILIR |
| 2022-2023 Apotemi Modern Fizik | ISLENMEDI | `Apotemi 2022 2023 Modern Fizik` | 256 | - | yok | 2019-2020 Apotemi Modern Fizik Konu Anlatimli SB %48 (gozle) | - | AILE: yalniz biri islenmeli (2019-2020 Apotemi Modern Fizik Konu Anlatimli SB %48 gozle) |
| APOTEMI 2024 AYT Kimya Soru Bankasi | ISLENMEDI | `Apotemi 2024 Ayt Kimya Soru Bankasi` | 268 | - | eski hat 262 / aktif 262 | - | - | ISLENEBILIR |
| Apotemi 2024 AYT Edebiyat Konu Ozeti | ISLENMEDI | `Apotemi Ayt Edebiyat Konu Ozeti` | 208 | - | yok | - | - | ISLENEBILIR |

### AROMAT (13 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2023-2024 AROMAT AYT Fizik Soru Bankasi | ISLENMEDI | `Aromat Ayt 2023 2024 Fizik Soru Bankasi` | 320 | - | yok | - | - | ISLENEBILIR |
| 2023-2024 AROMAT Fizik Soru Bankasi | ISLENMEDI | `Aromat Tyt 2023 2024 Fizik Soru Bankasi` | 320 | - | yok | - | - | ISLENEBILIR |
| 2023-2024 AROMAT Matematik Soru Bankasi | ISLENMEDI | `Aromat -2023-2024-Matematik Soru Bankasi` | 400 | - | eski hat 14 / aktif 14 | - | - | ISLENEBILIR |
| 2023-2024 AROMAT Paragraf Soru Bankasi | ISLENMEDI | `Aromat Paragraf Soru Bankasi` | 304 | - | eski hat 6 / aktif 6 | - | - | ISLENEBILIR |
| AROMAT 2023 AYT Matematik Soru Bankasi | ISLENMEDI | `Aromat-2023-Ayt-Matematik Soru Bankasi` | 336 | - | eski hat 13 / aktif 13 | - | - | ISLENEBILIR |
| AROMAT 2023 TYT Fen Bilimleri Model Sorular | ISLENMEDI | `Aramot Tyt 2023 Fen Bilimleri Model Sorular` | 80 | - | eski hat 18 / aktif 18 | - | - | ISLENEBILIR |
| AROMAT 2023 TYT Matematik Model Sorular | ISLENMEDI | `Aromat-2023-Tyt-Matematik Net 30` | 80 | - | yok | - | - | ISLENEBILIR |
| AROMAT 2023 TYT Sosyal Bilimler Model Sorular | ISLENMEDI | `Aromat Tyt Sosyal Bilimler Model Sorular 2023` | 80 | - | eski hat 17 / aktif 17 | - | - | ISLENEBILIR |
| AROMAT 2023 TYT Turkce Model Sorular | ISLENMEDI | `Aromat Tyt Turkce Model Sorular` | 80 | - | eski hat 9 / aktif 9 | - | - | ISLENEBILIR |
| AROMAT 2024 AYT Fen Bilimleri Model Sorular | ISLENMEDI | `Aromat 2024 Ayt Fen Bilimleri Model Sorular` | 83 | `Aromat Ayt 2024 Fen Bilimleri Model Sorular Net 30`; `Aromat Ayt 2024 Fen Bilimleri Net 30` | eski hat 12 / aktif 12 | Aromat 2024 AYT Fen Bilimleri Net-30 %26 | - | AILE: yalniz biri islenmeli (Aromat 2024 AYT Fen Bilimleri Net-30 %26) |
| Aromat 2024 AYT Edebiyat Net-30 | ISLENMEDI | `Aromat Ayt Edebiyat` | 82 | - | yok | - | - | ISLENEBILIR |
| Aromat 2024 AYT Fen Bilimleri Net-30 | ISLENMEDI | `Aromat 2024 Ayt Fen Bilimleri` | 82 | `Aromat 2024 Ayt Fen Bilimleri Net 30` | eski hat 18 / aktif 18 | AROMAT 2024 AYT Fen Bilimleri Model Sorular %26 | - | AILE: yalniz biri islenmeli (AROMAT 2024 AYT Fen Bilimleri Model Sorular %26) |
| Aromat 2024 AYT Matematik Net-30 | ISLENMEDI | `Aromat-2024-Matematik Net 30` | 82 | - | yok | - | - | ISLENEBILIR |

### BILGI SARMAL (32 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2020-2021 BS TYT Tarih Soru Bankasi | ISLENMEDI | `Bilgi Sarmal Tyt Tarih Soru Bankasi` | 272 | `Bilgi Sarmal Tyt Tarih Soru Bankasi 2020 2021` | eski hat 10 / aktif 10 | 2023-2024 BS TYT Tarih Soru Bankasi %60; BILGI SARMAL 2024 TYT Tarih Soru Bankasi %42 | `Bilgi Sarmal Tyt Tarih Soru Bankasi`: 56 sayfa yuklenmemis (gri) | AILE: yalniz biri islenmeli (2023-2024 BS TYT Tarih Soru Bankasi %60; BILGI SARMAL 2024 TYT Tarih Soru Bankasi %42) + eksik (gri) sayfalar yeniden yakalanmali |
| 2021-2022 BS AYT Tarih Soru Bankasi | ISLENMEDI | `Bilgi Sarmali Ayt Tarih Soru Bankasi 2021 2022` | 288 | `Bilgi Sarmal Ayt Tarih Soru Bankasi 2020 2021`; `Bilgi Sarmal Ayt Soru Bankasi 2020 2021` | eski hat 15 / aktif 15 | - | `Bilgi Sarmali Ayt Tarih Soru Bankasi 2021 2022`: 22 sayfa yuklenmemis (gri); `Bilgi Sarmal Ayt Tarih Soru Bankasi 2020 2021`: 25 sayfa yuklenmemis (gri) | ISLENEBILIR + eksik (gri) sayfalar yeniden yakalanmali |
| 2022-2023 BS AYT Matematik Soru Bankasi | ISLENMEDI | `Bilgi Sarmali-2022-2023-Tyt-Matematik Soru Bankasi` | 440 | - | eski hat 16 / aktif 16 | 2023-2024 BS AYT Matematik Soru Bankasi %48; BS 2024 AYT Matematik Soru Bankasi %27 | - | AILE: yalniz biri islenmeli (2023-2024 BS AYT Matematik Soru Bankasi %48; BS 2024 AYT Matematik Soru Bankasi %27) |
| 2022-2023 BS TYT Problemler Soru Bankasi | ISLENMEDI | `Bilgi Sarmali-2022-2023-Tyt-Problemler Soru Bankasi` | 176 | `Bilgi Sarmali-2023-2024-Problemler Soru Bankasi`; `Bilgi Sarmali-2024-Tyt Problemler Soru Bankasi` | eski hat 5 / aktif 5 | - | `Bilgi Sarmali-2024-Tyt Problemler Soru Bankasi`: 175 sayfa art arda ayni (cift/takili yakalama) | ISLENEBILIR |
| 2022-2023 BS TYT Turkce Soru Bankasi | **ISLENDI** | `Bilgi Sarmal  Tyt Turkce Soru Bankasi` | 336 | `Bilgi Sarmal Tyt Turkce Soru Bankasi 2022 2023` | modern 1481 / aktif 12 | BILGI SARMAL 2024 TYT Turkce Soru Bankasi %62 | - | TAMAM (modern ithal) |
| 2022-2023 BS TYT-AYT Geometri Soru Bankasi | ISLENMEDI | `Bilgi Sarmali-2022-2023-Tyt Ayt-Geometri Soru Bankasi` | 402 | `Bilgi Sarmali-2023-2024-Tyt Ayt-Geometri Soru Bankasi`; `Bilgi Sarmali-Tyt Ayt-Geometri Soru Bankasi` | eski hat 1 / aktif 1 | BILGI SARMAL 2025 TYT-AYT Geometri Soru Bankasi %29 | `Bilgi Sarmali-Tyt Ayt-Geometri Soru Bankasi`: 5 sayfa yuklenmemis (gri) | AILE: yalniz biri islenmeli (BILGI SARMAL 2025 TYT-AYT Geometri Soru Bankasi %29) |
| BS 2024 AYT Edebiyat SB | **ISLENDI** | `Bilgi Sarmal Ayt Edebiyat Soru Bankasi 2024` | 416 | `Bilgi Sarmal Ayt Edebiyat Soru Bankasi` | modern 1597 / aktif 0 | - | - | TAMAM (modern ithal) |
| 2023-2024 BS AYT Matematik Soru Bankasi | ISLENMEDI | `Bilgi Sarmali-2023-2024-Ayt-Matematik Soru Bankasi` | 420 | - | eski hat 10 / aktif 10 | BS 2024 AYT Matematik Soru Bankasi %62; 2022-2023 BS AYT Matematik Soru Bankasi %48 | - | AILE: yalniz biri islenmeli (BS 2024 AYT Matematik Soru Bankasi %62; 2022-2023 BS AYT Matematik Soru Bankasi %48) |
| 2023-2024 BS TYT Matematik Soru Bankasi | ISLENMEDI | `Bilgi Sarmali-2023-2024-Tyt-Matematik Soru Bankasi` | 403 | - | eski hat 24 / aktif 24 | BILGI SARMAL 2025 TYT Matematik Soru Bankasi %62 | - | AILE: yalniz biri islenmeli (BILGI SARMAL 2025 TYT Matematik Soru Bankasi %62) |
| 2023-2024 BS TYT Problemler Brans DS Yildizlar Yarisiyor | ISLENMEDI | `Bilgi Sarmali-2023-2024-Problemler Brans DS Yildizlar Yarisiyor` | 112 | `Bilgi Sarmali-2023-2024-Problemler Yildizlar Yarisiyor` | yok | - | - | ISLENEBILIR |
| 2023-2024 BS TYT Tarih Soru Bankasi | ISLENMEDI | `Bilgi Sarmal Tyt Tarih Soru Bankasi 2023 2024` | 272 | - | eski hat 4 / aktif 4 | BILGI SARMAL 2024 TYT Tarih Soru Bankasi %90; 2020-2021 BS TYT Tarih Soru Bankasi %60 | 70 sayfa yuklenmemis (gri) | AILE: yalniz biri islenmeli (BILGI SARMAL 2024 TYT Tarih Soru Bankasi %90; 2020-2021 BS TYT Tarih Soru Bankasi %60) + eksik (gri) sayfalar yeniden yakalanmali |
| 2023-2024 BS TYT-AYT Dil Bilgisi Soru Bankasi | ISLENMEDI | `Bilgi Sarmal 2023 2024 Tyt Ayt Dil Bilgisi Soru Bankasi 2023 2024` | 320 | `Bilgi Sarmal Tyt Ayt Dil Bilgisi Soru Bankasi 2022 2023`; `Bilgi Sarmal Tyt Ayt Dil Bilgisi Soru Bankasi 2024`; `Bilgi Sarmal Tyt Ayt Dilbilgisi Soru Bankasi` | eski hat 22 / aktif 22 | - | - | ISLENEBILIR |
| BILGI SARMAL 2023 Yildizlar Yarisiyor Edebiyat Sosyal Bilimler Brans Denemeleri | ISLENMEDI | `Bilgi Sarmal Turk Dili ve Edebiyati Sosyal Bilimler 1` | 128 | - | eski hat 1 / aktif 1 | - | - | ISLENEBILIR |
| BILGI SARMAL 2024 TYT Fizik Soru Bankasi | ISLENMEDI | `Bilgi Sarmali Tyt 2024 Fizik Soru Bankasi` | 336 | - | yok | - | - | ISLENEBILIR |
| BILGI SARMAL 2024 TYT Kimya Soru Bankasi | ISLENMEDI | `Bilgi Sarmal 2024 Tyt Kimya Soru Bankasi` | 304 | - | eski hat 247 / aktif 247 | - | - | ISLENEBILIR |
| BILGI SARMAL 2024 TYT Tarih Soru Bankasi | ISLENMEDI | `Bilgi Sarmal Tyt Tarih Soru Bankasi 2024` | 272 | - | eski hat 18 / aktif 18 | 2023-2024 BS TYT Tarih Soru Bankasi %90; 2020-2021 BS TYT Tarih Soru Bankasi %42 | - | AILE: yalniz biri islenmeli (2023-2024 BS TYT Tarih Soru Bankasi %90; 2020-2021 BS TYT Tarih Soru Bankasi %42) |
| BILGI SARMAL 2024 TYT Turkce Soru Bankasi | ISLENMEDI | `Bilgi Sarmal Tyt Turkce Soru Bankasi 2024` | 336 | - | eski hat 20 / aktif 20 | 2022-2023 BS TYT Turkce Soru Bankasi %62 | - | SAHIP KARARI: 2022-2023 BS TYT Turkce Soru Bankasi ile en az %62 ortak -> atla ya da yalniz farki isle |
| BILGI SARMAL 2025 AYT Edebiyat Video Ders Kitabi | ISLENMEDI | `Bilgi Sarmal Ayt Edebiyat Video Ders Kitabi 2025` | 304 | - | yok | - | - | ISLENEBILIR |
| BILGI SARMAL 2025 AYT Matematik Soru Bankasi | ISLENMEDI | `Bilgi Sarmali-2025-Ayt-Matematik Soru Bankasi` | 416 | - | eski hat 13 / aktif 13 | - | - | ISLENEBILIR |
| BILGI SARMAL 2025 AYT Matematik Video Ders Kitabi | ISLENMEDI | `Bilgi Sarmali-2025-Ayt-Matematik Video Ders Kitabi` | 356 | - | yok | - | - | ISLENEBILIR |
| BILGI SARMAL 2025 TYT Kimya Video Ders Kitabi | ISLENMEDI | `Bilgi Sarmal 2025 Tyt Kimya Video Ders Kitabi` | 144 | - | eski hat 103 / aktif 103 | - | - | ISLENEBILIR |
| BILGI SARMAL 2025 TYT Matematik Soru Bankasi | ISLENMEDI | `Bilgi Sarmali-2025-Tyt-Matematik Soru Bankasi` | 422 | - | eski hat 12 / aktif 12 | 2023-2024 BS TYT Matematik Soru Bankasi %62 | 20 sayfa art arda ayni (cift/takili yakalama) | AILE: yalniz biri islenmeli (2023-2024 BS TYT Matematik Soru Bankasi %62) |
| BILGI SARMAL 2025 TYT Matematik Video Ders Kitabi | ISLENMEDI | `Bilgi Sarmali-2025-Tyt-Matematik Video Ders Kitabi` | 289 | - | eski hat 3 / aktif 3 | - | - | ISLENEBILIR |
| BILGI SARMAL 2025 TYT Sosyal Bilimler Video Ders Kitabi | ISLENMEDI | `Bilgi Sarmal Tyt Sosyal Bilimler Video Ders Kitabi 2025` | 208 | - | yok | - | - | ISLENEBILIR |
| BILGI SARMAL 2025 TYT Turkce Video Ders Kitabi | ISLENMEDI | `Bilgi Sarmal Tyt Turkce Video Dets Kitabi 2025` | 256 | - | eski hat 23 / aktif 23 | - | - | ISLENEBILIR |
| BILGI SARMAL 2025 TYT-AYT Geometri Soru Bankasi | ISLENMEDI | `Bilgi Sarmali-2025-Tyt Ayt-Geometri Soru Bankasi` | 400 | - | yok | 2022-2023 BS TYT-AYT Geometri Soru Bankasi %29 | - | AILE: yalniz biri islenmeli (2022-2023 BS TYT-AYT Geometri Soru Bankasi %29) |
| BS 2024 AYT Fizik SB | ISLENMEDI | `Bilgi Sarmali Ayt 2024 Fizik Soru Bankasi` | 352 | - | yok | - | - | ISLENEBILIR |
| BS 2024 AYT Kimya SB | ISLENMEDI | `Bilgi Sarmal 2024 Ayt Kimya Sopru Bankasi` | 368 | - | eski hat 282 / aktif 282 | - | - | ISLENEBILIR |
| BS 2024 AYT Logaritma Diziler | ISLENMEDI | `Bilgi Sarmali-2024-Ayt-Logaritmik Diziler` | 144 | `Bilgi Sarmali-2024-Ayt-Logaritma Diziler` | eski hat 1 / aktif 1 | - | - | ISLENEBILIR |
| BS 2024 AYT Matematik Soru Bankasi | ISLENMEDI | `Bilgi Sarmali-2024-Ayt-Matematik Soru Bankasi` | 425 | - | eski hat 12 / aktif 12 | 2023-2024 BS AYT Matematik Soru Bankasi %62; 2022-2023 BS AYT Matematik Soru Bankasi %27 | - | AILE: yalniz biri islenmeli (2023-2024 BS AYT Matematik Soru Bankasi %62; 2022-2023 BS AYT Matematik Soru Bankasi %27) |
| BS 2024 AYT Turk Edebiyati 25 Brans Deneme | ISLENMEDI | `Bilgi Sarmal Ayt Turk Dili ve Edebiyati 2024` | 208 | - | yok | - | 10 sayfa art arda ayni (cift/takili yakalama) | ISLENEBILIR |
| BS 2024 TYT-AYT Paragraf SB | ISLENMEDI | `Bilgi Sarmal Tyt Ayt Paragraf Soru Bankasi` | 288 | - | eski hat 18 / aktif 18 | - | - | ISLENEBILIR |

### C1CELL (4 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| C1CELL 2024 Problemler SB | ISLENMEDI | `C1CELL-2024-Problemler Soru Bankasi` | 208 | - | eski hat 3 / aktif 3 | - | - | ISLENEBILIR |
| C1CELL 2024 TYT Matematik Soru Bankasi | ISLENMEDI | `C1CELL-2024-TYT-Matematik Soru Bankasi` | 384 | - | eski hat 26 / aktif 26 | - | - | ISLENEBILIR |
| C1CELL 2024 TYT-AYT Geometri Soru Bankasi | **ISLENDI** | `C1CELL-2024-TYT-AYT-Geometri Soru Bankasi` | 420 | - | modern 1770 / aktif 1770 | - | - | TAMAM (modern ithal) |
| C1CELL 2025 AYT Matematik Soru Bankasi | ISLENMEDI | `C1CELL-2025-Matematik Soru Bankasi` | 417 | - | eski hat 5 / aktif 5 | - | - | ISLENEBILIR |

### CAP (16 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2020-2021 CAP AYT Tarih SB (s1-192) + 2023-2024 CAP AYT Tarih SB (s193-288) | ISLENMEDI | `Cap Ayt Tarih Soru Bankasi` | 288 | - | eski hat 20 / aktif 20 | - | KARISIK: s1-192 = 2020-2021 CAP AYT Tarih SB, s193-288 = 2023-2024 CAP AYT Tarih SB (iki kitap tek klasorde, ikisi de eksik) | ISLENEBILIR |
| 2020-2021 CAP Capli Paragraf | ISLENMEDI | `Vaf Capli Paragraf Soru Bankasi` | 296 | - | eski hat 6 / aktif 6 | - | - | ISLENEBILIR |
| 2020-2021 CAP TYT Tarih Soru Bankasi | ISLENMEDI | `Cap Tyt Tarih Soru Bankasi 2020 2021` | 192 | - | eski hat 22 / aktif 22 | - | 16 sayfa yuklenmemis (gri) | ISLENEBILIR |
| 2020-2021 CAP TYT Turkce Soru Bankasi | ISLENMEDI | `Cap Tyt Turkce Soru Bankasi` | 304 | - | eski hat 7 / aktif 7 | 2023-2024 CAP TYT Turkce Soru Bankasi %19 | - | AILE: yalniz biri islenmeli (2023-2024 CAP TYT Turkce Soru Bankasi %19) |
| 2022-2023 CAP AYT Edebiyat Soru Bankasi | ISLENMEDI | `Cap Ayt Edebiyat Soru Bankasi 2022 2023` | 320 | - | yok | - | - | ISLENEBILIR |
| 2022-2023 CAP TYT Matematik Soru Bankasi | ISLENMEDI | `CAP-2022-2023-TYT-Matematik Soru Bankasi` | 384 | - | eski hat 40 / aktif 40 | - | - | ISLENEBILIR |
| 2022-2023 CAP TYT-AYT Geometri Soru Bankasi | ISLENMEDI | `CAP-2022-2023-TYT AYT-Geometri Soru Bankasi` | 384 | - | yok | - | - | ISLENEBILIR |
| 2023-2024 CAP AYT Fizik Soru Bankasi | ISLENMEDI | `Cap Ayt Fizik Soru Bankasi 2023 2024` | 320 | - | yok | - | - | ISLENEBILIR |
| 2023-2024 CAP AYT Matematik Soru Bankasi | ISLENMEDI | `CAP-2023-2024-AYT-Matematik Soru Bankasi` | 398 | - | eski hat 8 / aktif 8 | CAP 2023 AYT Matematik AL Soru Bankasi %56 | - | AILE: yalniz biri islenmeli (CAP 2023 AYT Matematik AL Soru Bankasi %56) |
| 2023-2024 CAP TYT Fizik Soru Bankasi | ISLENMEDI | `Cap Tyt Fizik Soru Bankasi 2023 2024` | 288 | - | yok | - | - | ISLENEBILIR |
| 2023-2024 CAP TYT Tarih Soru Bankasi | ISLENMEDI | `Cap Tyt Tarih Soru Bankasi 2023 2024` | 240 | - | eski hat 72 / aktif 72 | - | - | ISLENEBILIR |
| 2023-2024 CAP TYT Turkce Soru Bankasi | ISLENMEDI | `Cap Tyt Turkce Soru Bankasi 2023 2024` | 352 | - | eski hat 20 / aktif 20 | 2020-2021 CAP TYT Turkce Soru Bankasi %19 | - | AILE: yalniz biri islenmeli (2020-2021 CAP TYT Turkce Soru Bankasi %19) |
| CAP 2023 AYT Matematik AL Soru Bankasi | ISLENMEDI | `CAP-2023-AYT-Matematik -AL-Soru Bankasi` | 441 | - | eski hat 8 / aktif 8 | 2023-2024 CAP AYT Matematik Soru Bankasi %56 | - | AILE: yalniz biri islenmeli (2023-2024 CAP AYT Matematik Soru Bankasi %56) |
| CAP 2024 TYT Paragraf Konu Anlatimli Soru Bankasi | ISLENMEDI | `Cap Tyt Konu Anlatimli Soru Bankasi 2024` | 304 | - | eski hat 10 / aktif 10 | - | - | ISLENEBILIR |
| CAP 2025 TYT Dil Bilgisi Konu Anlatimli Soru Bankasi | ISLENMEDI | `Cap Tyt Dil Bilgisi Konu Anlatimli Soru Bankasi` | 352 | - | eski hat 43 / aktif 43 | - | - | ISLENEBILIR |
| Cap 2024 Anlam Bilgisi Kitabi | ISLENMEDI | `Cap Anlam Bilgisi Kitabi 2024` | 176 | - | eski hat 18 / aktif 18 | - | - | ISLENEBILIR |

### EDEBIYAT DENIZI / EDEBIYAT SOKAGI (11 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| ED 2024 TYT-AYT Paragraf SB | ISLENMEDI | `Edebiyat Denizi Tyt Ayt Paragraf Soru Bankasi 2024` | 336 | - | eski hat 5 / aktif 5 | - | - | ISLENEBILIR |
| Ed(ebiyat Denizi) 2024 AYT Edebiyat Soru Bankasi | ISLENMEDI | `Edebiyat Denizi Ayt Edebiyat Soru Bankasi` | 304 | - | yok | - | - | ISLENEBILIR |
| Es 2024 AYT Edebiyat Denemeleri | ISLENMEDI | `Edebiyat Sokagi Ayt Edebiyat Yeterlilik Testi` | 160 | - | yok | - | - | ISLENEBILIR |
| Es 2024 AYT Edebiyat Yeni Nesil Soru Bankasi | ISLENMEDI | `Edebiyat Sokagi Ayt Edebiyat Soru Bankasi` | 304 | - | yok | - | - | ISLENEBILIR |
| Es 2024 Atasozleri-Deyimler Soru Bankasi | ISLENMEDI | `Edebiyat Sokagi Atasozleri ve Deyimler Soru Bankasi` | 160 | - | yok | Es 2024 Dil Bilgisi %32 | - | AILE: yalniz biri islenmeli (Es 2024 Dil Bilgisi %32) |
| Es 2024 Baslangic Paragraf | ISLENMEDI | `Edebiyat Sokagi Baslangic Paragraf` | 224 | - | eski hat 6 / aktif 6 | - | - | ISLENEBILIR |
| Es 2024 Dil Bilgisi | ISLENMEDI | `Edebiyat Sokagi Dil Bilgisi Soru Bankasi 2024` | 272 | - | eski hat 12 / aktif 12 | Es 2024 Atasozleri-Deyimler Soru Bankasi %32 | - | AILE: yalniz biri islenmeli (Es 2024 Atasozleri-Deyimler Soru Bankasi %32) |
| Es 2024 Ileri Duzey Paragraf | ISLENMEDI | `Edebiyat Sokagi Paragraf ileri Duzey` | 309 | - | eski hat 352 / aktif 352 | Es 2024 Paragraf Yeterlilik Testi %16 | - | AILE: yalniz biri islenmeli (Es 2024 Paragraf Yeterlilik Testi %16) |
| Es 2024 Paragraf Analizi | ISLENMEDI | `Edebiyat Sokagi Paragraf Analizi` | 160 | - | yok | - | - | ISLENEBILIR |
| Es 2024 Paragraf Yeterlilik Testi | ISLENMEDI | `Edebiyat Sokagi Paragraf Yeterlilik Testi 2024` | 248 | - | eski hat 1 / aktif 1 | Es 2024 Ileri Duzey Paragraf %16 | - | AILE: yalniz biri islenmeli (Es 2024 Ileri Duzey Paragraf %16) |
| Es(Edebiyat Sokagi) 2024 Orta Duzey Paragraf | ISLENMEDI | `Edebiyat Sohagi Paragraf Orta Duzey` | 304 | - | eski hat 5 / aktif 5 | - | - | ISLENEBILIR |

### EGZERSIZ (1 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| Egzersiz 2021 TYT Fizik Soru Bankasi | ISLENMEDI | `Egsersiz Tyt Fizik Soru Bankasi 2021` | 352 | - | yok | - | - | ISLENEBILIR |

### ESEN (29 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| (Esen) 2024 Motivasyon Biyoloji PSB | ISLENMEDI | `Esen Yks Motivasyon Biyoloji` | 216 | - | yok | - | - | ISLENEBILIR |
| (Esen) 2024 Motivasyon Fizik 1 PSB | ISLENMEDI | `Esen Yks Motivasyon Fizik Testleri` | 272 | - | yok | - | - | ISLENEBILIR |
| (Esen) 2024 Motivasyon Fizik 2 PSB | ISLENMEDI | `Esen 2024 Motivasyon Fizik 2` | 304 | - | yok | - | - | ISLENEBILIR |
| (Esen) 2024 TYT Kimya PSB (Motivasyon) | ISLENMEDI | `Esen Yks Motivasyon Kimya Soru Bankasi` | 264 | - | eski hat 64 / aktif 64 | - | - | ISLENEBILIR |
| (Esen) 2025 APS AYT Biyoloji SB | ISLENMEDI | `Esen Apt Ayt Fizik 2025` | 224 | - | eski hat 61 / aktif 61 | - | - | ISLENEBILIR |
| (Esen) 2025 APS AYT Edebiyat SB | ISLENMEDI | `Esen Aps Ayt Edebiyat Soru Bankasi` | 304 | - | yok | - | - | ISLENEBILIR |
| (Esen) 2025 APS AYT Fizik SB | ISLENMEDI | `Esen 2025 Aps Ayt Fizik Soru Bankasi` | 240 | - | yok | (Esen) AYT Fizik Soru Bankasi %22 | - | AILE: yalniz biri islenmeli ((Esen) AYT Fizik Soru Bankasi %22) |
| (Esen) 2025 APS AYT Kimya SB | ISLENMEDI | `Esen Aylik Planli Biyoloji Soru Bankasi` | 240 | - | yok | - | - | ISLENEBILIR |
| (Esen) 2025 APS AYT Matematik SB | ISLENMEDI | `Esen 2025 Aps Ayt Matemat,k Soru Bankasi` | 192 | - | yok | - | - | ISLENEBILIR |
| (Esen) 2025 APS TYT Biyoloji SB | ISLENMEDI | `Esen Aps Biyoloji Soru Bankasi` | 160 | - | yok | (Esen) TYT-AYT Biyoloji Soru Bankasi %38 | - | AILE: yalniz biri islenmeli ((Esen) TYT-AYT Biyoloji Soru Bankasi %38) |
| (Esen) 2025 APS TYT Cografya SB | ISLENMEDI | `Esen Aps Cografya Soru Bankasi` | 260 | - | eski hat 44 / aktif 44 | (Esen) TYT Cografya Soru Bankasi %39 (gozle) | - | AILE: yalniz biri islenmeli ((Esen) TYT Cografya Soru Bankasi %39 gozle) |
| (Esen) 2025 APS TYT Fizik SB | ISLENMEDI | `Esen Aps Fizik Soru Bankasi 3` | 224 | - | yok | (Esen) TYT Fizik Soru Bankasi %37 | - | AILE: yalniz biri islenmeli ((Esen) TYT Fizik Soru Bankasi %37) |
| (Esen) 2025 APS TYT Kimya SB | ISLENMEDI | `Esen Aps Kimya Soru Bankasi` | 208 | - | eski hat 40 / aktif 40 | - | - | ISLENEBILIR |
| (Esen) 2025 APS TYT Matematik SB | ISLENMEDI | `Esen Aps Tyt Matematik Soru Bankasi` | 354 | - | eski hat 4 / aktif 4 | (Esen) TYT Matematik Soru Bankasi %34 (gozle) | - | AILE: yalniz biri islenmeli ((Esen) TYT Matematik Soru Bankasi %34 gozle) |
| (Esen) 2025 APS TYT Turkce SB | ISLENMEDI | `Esen Aps Tyt Turkce Soru Bankasi` | 352 | - | eski hat 20 / aktif 20 | (Esen) TYT Turkce Soru Bankasi %24 | - | AILE: yalniz biri islenmeli ((Esen) TYT Turkce Soru Bankasi %24) |
| (Esen) 2025 APS TYT-AYT Geometri SB | ISLENMEDI | `Esen Aps Geometri Soru Bankasi` | 283 | - | yok | (Esen) TYT-AYT Geometri Soru Bankasi %20 | - | AILE: yalniz biri islenmeli ((Esen) TYT-AYT Geometri Soru Bankasi %20) |
| (Esen) 2025 APS TYT-AYT Tarih SB | ISLENMEDI | `Esen Aps Tyt Ayt Tarih Soru Bankasi` | 336 | - | eski hat 47 / aktif 47 | (Esen) TYT Tarih Soru Bankasi %24 | - | AILE: yalniz biri islenmeli ((Esen) TYT Tarih Soru Bankasi %24) |
| (Esen) AYT Cografya Soru Bankasi | ISLENMEDI | `Esen Ayt Tarih Soru Bankasi` | 272 | - | eski hat 15 / aktif 15 | - | - | ISLENEBILIR |
| (Esen) AYT Fizik Soru Bankasi | ISLENMEDI | `Esen Ayt Fizik Soru Bankasi` | 352 | - | yok | (Esen) 2025 APS AYT Fizik SB %22 | - | AILE: yalniz biri islenmeli ((Esen) 2025 APS AYT Fizik SB %22) |
| (Esen) AYT Kimya Soru Bankasi | ISLENMEDI | `Esen Ayt Kimya Soru Bankasi` | 288 | - | eski hat 43 / aktif 43 | - | - | ISLENEBILIR |
| (Esen) TYT Cografya Soru Bankasi | ISLENMEDI | `Esen Tyt Cografya Soru Bankasi` | 320 | - | eski hat 31 / aktif 31 | (Esen) 2025 APS TYT Cografya SB %39 (gozle) | - | AILE: yalniz biri islenmeli ((Esen) 2025 APS TYT Cografya SB %39 gozle) |
| (Esen) TYT Fizik Soru Bankasi | ISLENMEDI | `Esen Tyt FizikSoru Bankasi` | 304 | - | yok | (Esen) 2025 APS TYT Fizik SB %37 | - | AILE: yalniz biri islenmeli ((Esen) 2025 APS TYT Fizik SB %37) |
| (Esen) TYT Kimya Soru Bankasi | ISLENMEDI | `Esen Tyt Kimya Soru Bankasi` | 256 | - | eski hat 66 / aktif 66 | - | - | ISLENEBILIR |
| (Esen) TYT Kronograf Soru Bankasi | ISLENMEDI | `Esen-Kronograf-Tyt-Paragraf Soru Bankasi` | 320 | - | eski hat 21 / aktif 21 | - | - | ISLENEBILIR |
| (Esen) TYT Matematik Soru Bankasi | ISLENMEDI | `Esen Tyt  Matematik Soru Bankasi` | 449 | - | eski hat 6 / aktif 6 | (Esen) 2025 APS TYT Matematik SB %34 (gozle) | - | AILE: yalniz biri islenmeli ((Esen) 2025 APS TYT Matematik SB %34 gozle) |
| (Esen) TYT Tarih Soru Bankasi | ISLENMEDI | `Esen Tyt Tarih Soru Bankasi` | 336 | - | eski hat 45 / aktif 45 | (Esen) 2025 APS TYT-AYT Tarih SB %24 | - | AILE: yalniz biri islenmeli ((Esen) 2025 APS TYT-AYT Tarih SB %24) |
| (Esen) TYT Turkce Soru Bankasi | ISLENMEDI | `Esen Tyt Turkce Soru Bankasi` | 432 | - | eski hat 26 / aktif 26 | (Esen) 2025 APS TYT Turkce SB %24 | - | AILE: yalniz biri islenmeli ((Esen) 2025 APS TYT Turkce SB %24) |
| (Esen) TYT-AYT Biyoloji Soru Bankasi | ISLENMEDI | `Esen Tyt Ayt Biyoloji Soru Bankasi` | 288 | - | yok | (Esen) 2025 APS TYT Biyoloji SB %38 | - | AILE: yalniz biri islenmeli ((Esen) 2025 APS TYT Biyoloji SB %38) |
| (Esen) TYT-AYT Geometri Soru Bankasi | ISLENMEDI | `Esen Tyt Ayt Geometri Soru Bankasi` | 352 | - | yok | (Esen) 2025 APS TYT-AYT Geometri SB %20 | - | AILE: yalniz biri islenmeli ((Esen) 2025 APS TYT-AYT Geometri SB %20) |

### FIZIPEDIA (2 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| FIZIPEDIA 2025 AYT Fizik Soru Bankasi | ISLENMEDI | `Fizipedia Ayt Fizik Soru Bankasi 2025` | 368 | - | eski hat 1 / aktif 1 | - | - | ISLENEBILIR |
| FIZIPEDIA 2025 TYT Fizik Soru Bankasi | ISLENMEDI | `Fizipedia Tyt Fizik Soru Bankasi 2025` | 352 | - | yok | - | - | ISLENEBILIR |

### FULL MATEMATIK (6 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2019-2020 FM TYT Matematik Soru Bankasi | ISLENMEDI | `Full Matematik-Tyt-Matematik Soru Bankasi` | 288 | - | yok | 2022-2023 FULL TYT Matematik Soru Bankasi %22 | - | AILE: yalniz biri islenmeli (2022-2023 FULL TYT Matematik Soru Bankasi %22) |
| 2019-2020 Full Matematik AYT Matematik Soru Bankasi | ISLENMEDI | `Full-2019-2020-Ayt-Matematik Soru Bankasi` | 288 | `Full-Ayt-Matematik Soru Bankasi` | yok | - | `Full-Ayt-Matematik Soru Bankasi`: 9 sayfa yuklenmemis (gri) | ISLENEBILIR |
| 2019-2020 Full Matematik Geometri Soru Bankasi | ISLENMEDI | `Full Matematik-2019-2020-Geometri Soru Bankasi` | 272 | - | yok | - | - | ISLENEBILIR |
| 2022-2023 FULL AYT Matematik Soru Bankasi | ISLENMEDI | `Full Matematik-Ayt-Matematik Soru Bankasi` | 386 | - | eski hat 3 / aktif 3 | - | - | ISLENEBILIR |
| 2022-2023 FULL TYT Matematik Soru Bankasi | ISLENMEDI | `Full Matematik-2022-2023-Tyt-Matematik Soru Bankasi` | 368 | - | eski hat 11 / aktif 11 | 2019-2020 FM TYT Matematik Soru Bankasi %22 | - | AILE: yalniz biri islenmeli (2019-2020 FM TYT Matematik Soru Bankasi %22) |
| 2022-2023 FULL TYT-AYT Geometri Soru Bankasi | ISLENMEDI | `Full Matematik-2022-2023-Tyt Ayt-Geometri Soru Bankasi` | 352 | - | yok | - | - | ISLENEBILIR |

### MIKRO ORIJINAL (30 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| MIKRO ORIJINAL 2024 Matematik Soru Bankasi | ISLENMEDI | `Mikro Orijinal-2024-matematik Soru Bankasi` | 384 | - | eski hat 33 / aktif 33 | - | - | ISLENEBILIR |
| MIKRO ORIJINAL 2024 TYT Matematik SB | ISLENMEDI | `Mikro Orijinal-2024-Tyt-Matematik Soru Bankasi` | 400 | - | eski hat 36 / aktif 36 | - | - | ISLENEBILIR |
| MIKRO ORIJINAL 2024 TYT Paragraf Soru Bankasi | ISLENMEDI | `Mikro Orijinal Tyt Paragraf Soru Bankasi 2024` | 304 | - | eski hat 20 / aktif 20 | - | - | ISLENEBILIR |
| MIKRO ORIJINAL 2024 TYT-AYT Geometri SB | ISLENMEDI | `Mikro Orijinal-Tyt Ayt-Geometri Soru Bankasi 2` | 416 | - | yok | MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi %81 (gozle) | - | SAHIP KARARI: MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi ile en az %81 ortak -> atla ya da yalniz farki isle |
| MIKRO ORIJINAL 2025 TYT Fizik Soru Bankasi | **ISLENDI** | `Mikro Orijinal Tyt Fizik Soru Bankasi 2025` | 400 | - | modern 1326 / aktif 1252 | - | - | TAMAM (modern ithal) |
| MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | **ISLENDI** | `Mikro Orijinal-2025-Ayt-Geometri Soru Bankasi` | 416 | - | modern 1211 / aktif 1211 | MIKRO ORIJINAL 2024 TYT-AYT Geometri SB %81 (gozle) | - | TAMAM (modern ithal) |
| Mikro Orijinal 2024 AYT 12'li Deneme-1 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-1` | 16 | - | yok | Mikro Orijinal 2024 AYT 12'li Deneme-2 %100 | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-10 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-10` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-11 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-11` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-12 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-12` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-3 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-3` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-4 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-4` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-5 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-5` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-6 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-6` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-7 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-7` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-8 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-8` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT 12'li Deneme-9 | ISLENMEDI | `Mikro Orijinal-2024-Ayt-12liDeneme-9` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 AYT Matematik SB | ISLENMEDI | `Mikro Orijinal-2024-Ayt-Matematik Soru Bankasi` | 400 | - | eski hat 19 / aktif 19 | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-10 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-10` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-11 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-11` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-12 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-12` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-2 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-2` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-3 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-3` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-4 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-4` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-5 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-5` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-6 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-6` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-7 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-7` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-8 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-8` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT 12'li Deneme-9 | ISLENMEDI | `Mikro Orijinal-2024-Tyt-12liDeneme-9` | 16 | - | yok | - | - | ISLENEBILIR |
| Mikro Orijinal 2024 TYT-AYT Geometri Soru Bankasi | ISLENMEDI | `Mikro-2024-Tyt Ayt-Geometri Soru Bankasi` | 400 | - | yok | - | - | ISLENEBILIR |

### NEOFIZIK (2 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| NEOFIZIK 2024 TYT Soru Bankasi | **ISLENDI** | `Neofizik Tyt Soru Bankasi` | 256 | - | modern 891 / aktif 827 | - | - | TAMAM (modern ithal) |
| NEOFIZIK 2025 AYT Fizik Soru Bankasi | **ISLENDI** | `Neofizik Ayt Fizik Soru Bankasi 2025` | 335 | - | modern 1218 / aktif 1181 | - | - | TAMAM (modern ithal) |

### ORIJINAL (13 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| ORIJINAL 2024 AYT Matematik SB | ISLENMEDI | `Orijinal2024-Ayt-Matematik Soru Bankasi` | 418 | - | eski hat 9 / aktif 9 | - | - | ISLENEBILIR |
| ORIJINAL 2025 AYT Logaritma Diziler | ISLENMEDI | `Orijinal-2025-Logaritma Diziler` | 144 | - | yok | - | - | ISLENEBILIR |
| ORIJINAL 2025 AYT Matematik Limit Sureklilik | ISLENMEDI | `Orijinal-2025-Limit` | 128 | - | yok | - | - | ISLENEBILIR |
| ORIJINAL 2025 AYT Matematik Turev | ISLENMEDI | `Orijinal-2025-Ayt-Matematik Turev` | 193 | - | yok | - | - | ISLENEBILIR |
| ORIJINAL 2025 AYT Polinom Parabol | ISLENMEDI | `Orijinal-2025-Ayt-Polinom parabol` | 208 | - | eski hat 10 / aktif 10 | - | - | ISLENEBILIR |
| ORIJINAL 2025 Analitik Geometri | ISLENMEDI | `Orijinal-2025-Analitik Geometri` | 192 | - | eski hat 4 / aktif 4 | Orijinal 2024 Analitik Geometri %44 (gozle) | - | AILE: yalniz biri islenmeli (Orijinal 2024 Analitik Geometri %44 gozle) |
| ORIJINAL 2025 TYT Matematik Problemler | ISLENMEDI | `Orijinal-2025-Tyt-Matematik Porblemler` | 208 | - | eski hat 1 / aktif 1 | - | - | ISLENEBILIR |
| ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | ISLENMEDI | `Orijinal-Tyt Ayt Geometri Soru Bankasi` | 432 | - | yok | Orijinal 2024 TYT-AYT Geometri SB %69 (gozle) | - | SAHIP KARARI: Orijinal 2024 TYT-AYT Geometri SB ile en az %69 ortak -> atla ya da yalniz farki isle |
| Orijinal 2024 AYT Integral | ISLENMEDI | `Orijinal-2024-Ayt-integral` | 160 | - | yok | - | - | ISLENEBILIR |
| Orijinal 2024 AYT Trigonometri | ISLENMEDI | `Orijinal-2024-Ayt-Trigonometri` | 208 | - | yok | - | - | ISLENEBILIR |
| Orijinal 2024 Analitik Geometri | ISLENMEDI | `Orijinal-2024-Geometri` | 160 | - | yok | ORIJINAL 2025 Analitik Geometri %44 (gozle) | - | AILE: yalniz biri islenmeli (ORIJINAL 2025 Analitik Geometri %44 gozle) |
| Orijinal 2024 TYT-AYT Fonksiyonlar | ISLENMEDI | `Orijinal-2024-Tyt Ayt-Fonksiyonlar` | 144 | - | eski hat 7 / aktif 7 | - | - | ISLENEBILIR |
| Orijinal 2024 TYT-AYT Geometri SB | HAZIR | `Orijinal-2024-Geometri Soru Bankasi` | 432 | - | 0 (2072 soru hazir) | ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi %69 (gozle) | - | `--yaz` bekliyor (Faz 3 bitti) |

### PES (5 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2020-2021 PES Kurgulu Paragraf | ISLENMEDI | `Pes Kurgulu Paragraf 2020 2021` | 288 | `Pes Paragraf Soru Bankasi 2020 2021` | eski hat 11 / aktif 11 | 2020-2021 PES TYT-AYT Paragraf Soru Bankasi %4 (gozle) | `Pes Kurgulu Paragraf 2020 2021`: 8 sayfa yuklenmemis (gri); `Pes Paragraf Soru Bankasi 2020 2021`: 8 sayfa yuklenmemis (gri) | AILE: yalniz biri islenmeli (2020-2021 PES TYT-AYT Paragraf Soru Bankasi %4 gozle) |
| 2020-2021 PES Problemler Kampi | ISLENMEDI | `PES-Konu ozetleri-Problemler Kampi` | 128 | - | eski hat 3 / aktif 3 | - | - | ISLENEBILIR |
| 2020-2021 PES Profesyonel Anlam Sorulari - Profesyonel Problem Sorulari | ISLENMEDI | `Pes PRofesyonel Anlam ve Problem Sorulari 2020 2021` | 240 | - | eski hat 3 / aktif 3 | - | - | ISLENEBILIR |
| 2020-2021 PES Sozcukte Cumlede Anlam Kampi | ISLENMEDI | `Pes Sozcuk ve Cumlede Anlam 2020 2021` | 160 | `Pes Sozcukte Cumle anlam Lampi 2020 2021` | eski hat 4 / aktif 4 | - | - | ISLENEBILIR |
| 2020-2021 PES TYT-AYT Paragraf Soru Bankasi | ISLENMEDI | `Pes Tyt Ayt Paragraf Sorulari 2020 2021` | 288 | - | eski hat 11 / aktif 11 | 2020-2021 PES Kurgulu Paragraf %4 (gozle) | - | AILE: yalniz biri islenmeli (2020-2021 PES Kurgulu Paragraf %4 gozle) |

### SURE (4 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2023-2024 SURE TYT Turkce Soru Bankasi | ISLENMEDI | `Sure Tyt Turkce Soru Bankasi 2023 2024` | 336 | - | eski hat 13 / aktif 13 | - | - | ISLENEBILIR |
| SURE 2023 AYT Edebiyat Soru Bankasi | ISLENMEDI | `Sure Ayt Edebiyat Soru Bankasi 2023` | 321 | `Sure Edebiyat Suresi 2025`; `Sure Ayt Edebiyat Soru Bankasi 2023` | yok | - | - | ISLENEBILIR |
| SURE 2023 TYT Paragraf Gunlukleri | ISLENMEDI | `Sure Tyt Paragraf Gunlukleri 2023` | 305 | `Sure Tyt Paragraf Gunlukleri` | eski hat 2 / aktif 2 | - | `Sure Tyt Paragraf Gunlukleri 2023`: 9 sayfa yuklenmemis (gri) | ISLENEBILIR |
| SURE 2025 Paragrafin Suresi | ISLENMEDI | `Sure Paragrafin Suresi 2025` | 288 | `Sure Tyt Ayt Paragraf Soru Bankasi 2023 2024` | eski hat 7 / aktif 7 | - | - | ISLENEBILIR |

### VAF (1 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| 2020-2021 AYT Turk Dili ve Edebiyati Soru Bankasi (Vaf) | ISLENMEDI | `Vaf Ayt Turk Dili ve Edebiyati` | 288 | - | eski hat 1 / aktif 1 | - | - | ISLENEBILIR |

### VIRAL (1 kitap)

| kitap (sekme basligi) | durum | klasor | png | ayni icerik | DB | ortaklik | kalite | oneri |
|---|---|---|---|---|---|---|---|---|
| VIRAL 2025 TYT Matematik | ISLENMEDI | `Viral-2025-Tyt Matematik` | 288 | - | eski hat 9 / aktif 9 | - | 49 sayfa art arda ayni (cift/takili yakalama) | ISLENEBILIR |

## 5. Yeniden yakalanmasi / duzeltilmesi gereken klasorler

| klasor | sorun | etki |
|---|---|---|
| `Orijinal-2024-Matematik Soru Bankasi` | 400 PNG'nin hepsi ayni sayfa (sha256 ozdes) | ORIJINAL 2024 TYT Matematik SB elde YOK |
| `Mikro Orijinal-2024-Ayt-12liDeneme-2` | 16 PNG'nin 16'si ayni sayfa | Mikro 2024 AYT 12'li Deneme-2 elde YOK |
| `Bilgi Sarmal Tyt Tarih Soru Bankasi 2023 2024` | 70 sayfa yuklenmemis (gri) | 2023-2024 BS TYT Tarih eksik |
| `Bilgi Sarmal Tyt Tarih Soru Bankasi` | 56 sayfa yuklenmemis (gri) | 2020-2021 BS TYT Tarih eksik |
| `Bilgi Sarmal Ayt Tarih Soru Bankasi 2020 2021` | 25 sayfa yuklenmemis | 2020-2021 BS AYT Tarih eksik |
| `Bilgi Sarmali Ayt Tarih Soru Bankasi 2021 2022` | 22 sayfa yuklenmemis | 2021-2022 BS AYT Tarih eksik |
| `Cap Tyt Tarih Soru Bankasi 2020 2021` | 16 sayfa yuklenmemis | 2020-2021 CAP TYT Tarih eksik |
| `Cap Ayt Tarih Soru Bankasi` | s1-192 2020-2021, s193-288 2023-2024 CAP AYT Tarih | iki baski yarim; ikisi de eksik |
| `Bilgi Sarmali-2024-Tyt Problemler Soru Bankasi` | 352 sayfanin 175'i art arda cift | kullanilabilir (176 tekil sayfa); tekillestir |
| `Aktif Ogrenme 2023 2024 Biyoloji` | 51 sayfa art arda cift | tekillestir |
| `Viral-2025-Tyt Matematik` | 49 sayfa art arda cift | tekillestir |
| `Bilgi Sarmal Tyt Turkce Soru Bankasi 2023 2024` | 13 PNG, 11'i gri | 2023-2024 BS TYT Turkce yakalamasi yok |
| `Bilgi Sarmal Tyt Tarih Soru Bankasi 2022 2023` | yalniz 5 PNG | 2022-2023 BS TYT Tarih yakalamasi yok |
| `Aydin Ayt Kamp Kitabim` | FERNUS degil (Aydin Yayinlari uygulamasi) | kapsam disi |
| `Sure Tyt Ayt Paragraf Soru Bankasi 2023 2024` (3 PNG) | YouTube penceresi | yok say |
| `Edebiyat Sokagi Ayt Yeni Nesil Soru Bankasi`, `kitap_20251206_181525` | PNG yok | yakalama yok |

## 6. Sahibe ait acik kararlar

1. **Mikro Orijinal 2024 TYT-AYT Geometri SB (#8):** planda 'islenmeye deger' yaziyordu; olcum islenmis 2025 baskisinin buyuk olcude kopyasi oldugunu gosteriyor -> atla / yalniz farkli sayfalar.
2. **Orijinal 2025 TYT-AYT Geometri:** hazirdaki 2024 baskisinin revize hali (en az %69 ortak) -> atla / yalniz fark.
3. **345 2024 AYT ve TYT Biyoloji:** mevcut ATLA onerisi olcumle tutarli.
4. **Baski aileleri** (bolum 4'te 'AILE' onerili satirlar): her ailede hangi baskinin islenecegi.
5. **Eski hat satirlari:** 122 islenmemis kitabin klasor adiyla DB'de deneme satiri var; bazilari AKTIF (or. Aktif 0'dan Kimya 520/520, Aktif AYT Kimya 490/490, Es Ileri Duzey Paragraf 352/352). Modern ithal bu kitaplara gecerken eski satirlarin akibeti karar ister.

## 7. Klasor -> kitap esleme (278 klasor)

`#` = bu raporun ic numarasi (olcum JSON'undaki sira). **ad?** = klasor adi sekme basligindan farkli bir kitap/baski ima ediyor.

| # | klasor | png | sekme basligi | ad? | grup durumu |
|---|---|---|---|---|---|
| 0 | `2019-2020-ACIL-AYT-Matematik Soru Bankasi` | 433 | 2019-2020 ACIL AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 1 | `2019-2020-ACIL-TYT-Soru Bankasi` | 432 | 2019-2020 Acil TYT Soru Bankasi |  | ISLENMEDI |
| 2 | `2019-2020-Acil Matematigin ilaci-1` | 382 | 2019-2020 Acil Matematigin Ilaci-1 |  | ISLENMEDI |
| 3 | `2019-2020-Acil-Matematigin ilaci Tyt Matematik Soru Bankasi` | 20 | 2019-2020 Acil Matematigin Ilaci TYT Matematik Soru Bankasi |  | kopya -> `2023-2024-ACIL-TYT-Matematigin Ilaci` |
| 4 | `2019-2020-Acil-Matematigin ilaci Tyt Matematik Soru Bankasi` | 319 | 2019-2020 Acil Matematigin Ilaci TYT Matematik Soru Bankasi |  | kopya -> `2023-2024-ACIL-TYT-Matematigin Ilaci` |
| 5 | `2019-2020-Apotemi-Tyt Matematik Soru Bankasi` | 324 | 2019-2020 APOTEMI TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 6 | `2020-2021-ACIL-AYT Matematik Soru Bankasi` | 449 | 2020-2021 ACIL AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 7 | `2020-2021-ACIL-TYT Matematik Soru Bankasi` | 448 | 2020-2021 ACIL TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 8 | `2020-2021-Acil-Problemlerin ilaci` | 191 | 2020-2021 Acil Problemlerin Ilaci |  | ISLENMEDI |
| 9 | `2020-2021-Acil-Tyt Ayt Geometrinin ilaci Soru Bankasi` | 288 | 2020-2021 Acil TYT-AYT Geometrinin Ilaci Soru Bankasi |  | ISLENMEDI |
| 10 | `2020-2021-Apotemi-Tyt Ayt-Geometri Maestro Soru Bankasi` | 320 | 2020-2021 APOTEMI TYT-AYT Geometri Maestro Soru Bankasi |  | ISLENMEDI |
| 11 | `2021-2022-Apotemi-Limit` | 128 | 2021-2022 Apotemi Limit ve Sureklilik |  | ISLENMEDI |
| 12 | `2021-2022-Apotemi-Problemler` | 240 | 2021-2022 Apotemi Problemler |  | ISLENMEDI |
| 13 | `2021-2022-Apotemi-Trigonometri` | 224 | 2021-2022 Apotemi Trigonometri |  | ISLENMEDI |
| 14 | `2022-2023-ACIL-Analitik Geometri` | 176 | 2022-2023 ACIL Analitik Geometri |  | ISLENMEDI |
| 15 | `2022-2023-ACIL-Kati Cisimler` | 160 | 2022-2023 ACIL Kati Cisimler |  | ISLENMEDI |
| 16 | `2022-2023-Apotemi-Fonksiyonlar` | 144 | 2022-2023 APOTEMI Fonksiyonlar |  | ISLENMEDI |
| 17 | `2022-Apotemi-Turev` | 224 | 2022 Apotemi Turev |  | ISLENMEDI |
| 18 | `2022-Apotemi-integral` | 224 | 2022 Apotemi Integral |  | ISLENMEDI |
| 19 | `2023-2024 ACIL- AYT Matematik Soru Bankasi` | 417 | 2023-2024 ACIL AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 20 | `2023-2024-ACIL-TYT Matematik Soru Bankasi` | 416 | 2023-2024 ACIL TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 21 | `2023-2024-ACIL-TYT-AYT Geometri Soru Bankasi` | 448 | 2023-2024 ACIL TYT-AYT Geometri Soru Bankasi |  | ISLENDI |
| 22 | `2023-2024-ACIL-TYT-AYT-Geometrinin Ilaci` | 290 | 2023-2024 ACIL TYT-AYT Geometrinin Ilaci |  | ISLENMEDI |
| 23 | `2023-2024-ACIL-TYT-Matematigin Ilaci` | 324 | 2023-2024 ACIL TYT Matematigin Ilaci |  | ISLENMEDI |
| 24 | `2024-ACIL TYT Matematik Geometri Kitap-1` | 208 | 2024 ACIL TYT Matematik Geometri Kitap-1 |  | ISLENMEDI |
| 25 | `345 2024 Ayt Biyoloji Soru Bankasi` | 376 | 345 2024 AYT Biyoloji Soru Bankasi |  | ISLENMEDI |
| 26 | `345 2024 Ayt Fizik Soru Bankasi` | 392 | 345 2024 AYT Fizik SB |  | islenmis kitabin kopyasi |
| 27 | `345 2024 Ayt Kimya Soru Bankasi` | 336 | 345 2024 AYT Kimya Soru Bankasi |  | ISLENMEDI |
| 28 | `345 2024 Ayt Matematik Soru Bankasi` | 399 | 345 2024 AYT Matematik SB |  | ISLENMEDI |
| 29 | `345 2024 Tyt Matematik Soru Bankasi` | 421 | 345 2024 TYT Matematik SB |  | kopya -> `345 2025 Tyt Matematik Soru Bankasi` |
| 30 | `345 2025 Ayt Biyoloji Soru Bankasi` | 374 | 345 2025 AYT Biyoloji SB |  | ISLENDI |
| 31 | `345 2025 Ayt Fizik Soru Bankasi` | 392 | 345 2025 AYT Fizik SB |  | ISLENDI |
| 32 | `345 2025 Ayt Kimya Soru Bankasi` | 336 | 345 2025 AYT Kimya SB |  | kopya -> `345 2024 Ayt Kimya Soru Bankasi` |
| 33 | `345 2025 Ayt Matematik Soru Bankasi` | 394 | 345 2025 AYT Matematik SB |  | kopya -> `345 2024 Ayt Matematik Soru Bankasi` |
| 34 | `345 2025 Ayt Turk Edebiyati Soru Bankasi` | 348 | 345 2025 AYT Turk Edebiyati SB |  | ISLENMEDI |
| 35 | `345 2025 Paragraf Sifir Risk Soru Bankasi` | 368 | 345 2025 Paragraf Sifir Risk SB |  | ISLENMEDI |
| 36 | `345 2025 Start Matematik` | 323 | 345 2025 Start Matematik |  | ISLENMEDI |
| 37 | `345 2025 Tyt Ayt Geometri Soru Bankasi 1` | 336 | 345 2025 TYT-AYT Geometri SB 1 |  | islenmis kitabin kopyasi |
| 38 | `345 2025 Tyt Biyoloji Soru Bankasi` | 235 | 345 2025 TYT Biyoloji SB |  | ISLENDI |
| 39 | `345 2025 Tyt Fizik Soru Bankasi` | 368 | 345 2025 TYT Fizik SB |  | ISLENMEDI |
| 40 | `345 2025 Tyt Kimya Soru Bankasi` | 280 | 345 2025 TYT Kimya SB |  | ISLENMEDI |
| 41 | `345 2025 Tyt Matematik Soru Bankasi` | 422 | 345 2025 TYT Matematik SB |  | ISLENMEDI |
| 42 | `345 2025 Tyt Sosyal Bilgiler Soru Bankasi` | 312 | 345 2025 TYT Sosyal Bilgiler SB |  | ISLENMEDI |
| 43 | `345 2025 Tyt Turkce Soru Bankasi` | 440 | 345 2025 TYT Turkce SB |  | ISLENMEDI |
| 44 | `345 Tyt Ayt Geometri Soru Bankasi` | 440 | 345 2024 TYT-AYT Geometri SB | ! | ISLENDI |
| 45 | `345 Tyt Ayt Geometri Soru Bankasi 2` | 336 | 345 2025 TYT-AYT Geometri SB 2 |  | ISLENDI |
| 46 | `345 Tyt Biyoloji Soru Bankasi` | 232 | 345 2024 TYT Biyoloji SB | ! | ISLENMEDI |
| 47 | `345 Tyt Fizik Soru Bankasi` | 368 | 345 2024 TYT Fizik SB | ! | kopya -> `345 2025 Tyt Fizik Soru Bankasi` |
| 48 | `345 Tyt Kimya Soru Bankasi` | 280 | 345 2024 TYT Kimya SB | ! | kopya -> `345 2025 Tyt Kimya Soru Bankasi` |
| 49 | `345 Tyt Sosyal Bilgiler Soru Bankasi` | 312 | 345 2024 TYT Sosyal Bilgiler SB | ! | kopya -> `345 2025 Tyt Sosyal Bilgiler Soru Bankasi` |
| 50 | `345 Tyt Turkce Soru Bankasi` | 440 | 345 2024 TYT Turkce SB | ! | kopya -> `345 2025 Tyt Turkce Soru Bankasi` |
| 51 | `ACIL-2025-Matematigin Ilaci Polinom` | 288 | ACIL 2025 Matematigin Ilaci Polinom |  | ISLENMEDI |
| 52 | `ACIL-2025-Matematigin Ilaci Sayilar-1` | 176 | ACIL 2025 Matematigin Ilaci Sayilar-1 |  | ISLENMEDI |
| 53 | `ACIL-2025-Matematigin Ilaci Sayilar-2` | 192 | ACIL 2025 Matematigin Ilaci Sayilar-2 |  | ISLENMEDI |
| 54 | `ACIL-2025-Problemin Ilaci` | 196 | ACIL 2025 Problemlerin Ilaci |  | ISLENMEDI |
| 55 | `ACIL-2025-TYT-Soeu Bankasi` | 416 | ACIL 2025 AYT Soru Bankasi | ! | ISLENMEDI |
| 56 | `ACIL-2025-TYT-Soru Bankasi` | 400 | ACIL 2025 TYT Soru Bankasi |  | ISLENMEDI |
| 57 | `ACIL-TYT-AYT-Geometri Soru Bankasi` | 400 | ACIL 2025 TYT-AYT Geometri Soru Bankasi |  | ISLENMEDI |
| 58 | `Acil-2024-AYT Matematik Kitap-1` | 224 | Acil 2024 AYT Matematik Kitap-1 |  | ISLENMEDI |
| 59 | `Aktif Ogrenme 0 Baslayanlara Kimya 2019 2020` | 368 | 2019-2020 Aktif 0'dan Baslayanlara Aktif Kimya |  | ISLENMEDI |
| 60 | `Aktif Ogrenme 2023 2024 Biyoloji` | 272 | 2023-2024 AKTIF Biyoloji |  | ISLENMEDI |
| 61 | `Aktif Ogrenme 2025 Tyt Fizik Soru Bankasi` | 352 | AKTIF 2025 TYT Fizik Soru Bankasi |  | ISLENMEDI |
| 62 | `Aktif Ogrenme Ayt Kartlarla Kimya 2022 2023` | 176 | 2022-2023 Kartlarla AYT Kimya |  | ISLENMEDI |
| 63 | `Aktif Ogrenme Ayt Kimya 2019 2020` | 416 | 2019-2020 Aktif AYT Kimya |  | ISLENMEDI |
| 64 | `Aktif Ogrenme Tyt Dilbilgisi Soru Bankasi 2025` | 224 | AKTIF 2025 TYT Dil Bilgisi Soru Bankasi |  | ISLENDI |
| 65 | `Aktif Ogrenme Tyt Paragraf Soru Bankasi 2025` | 144 | AKTIF 2025 TYT Paragraf Soru Bankasi |  | ISLENMEDI |
| 66 | `Altyapi Tyt Kartlarla Kimya` | 176 | 2022-2023 ALTYAPI Kartlarla TYT Kimya |  | ISLENMEDI |
| 67 | `Altyapi Tyt Kartlarla Tarih` | 192 | 2022-2023 ALTYAPI Kartlarla TYT Tarih |  | ISLENMEDI |
| 68 | `Altyapi 2022 2023 Kartlarla Ayt Fizik` | 144 | 2022-2023 Kartlarla AYT Fizik |  | ISLENMEDI |
| 69 | `Altyapi 2022 2023 Tyt Fizik` | 128 | 2022-2023 ALTYAPI Kartlarla TYT Fizik |  | ISLENMEDI |
| 70 | `Apotemi 2019 2020 Modern Fizik Konu Anlatimli Soru Bankasi` | 256 | 2019-2020 Apotemi Modern Fizik Konu Anlatimli SB |  | ISLENMEDI |
| 71 | `Apotemi 2019 2020 Tyt Ayt Fizik Soru Bankasi` | 448 | 2019-2020 Apotemi TYT-AYT Fizik Soru Bankasi |  | ISLENMEDI |
| 72 | `Apotemi 2020 2021 Modern Kimya` | 300 | 2020-2021 APOTEMI Modern Kimya |  | ISLENMEDI |
| 73 | `Apotemi 2022 2023 Modern Fizik` | 256 | 2022-2023 Apotemi Modern Fizik |  | ISLENMEDI |
| 74 | `Apotemi 2024 Ayt Kimya Soru Bankasi` | 268 | APOTEMI 2024 AYT Kimya Soru Bankasi |  | ISLENMEDI |
| 75 | `Apotemi Ayt Edebiyat Konu Ozeti` | 208 | Apotemi 2024 AYT Edebiyat Konu Ozeti |  | ISLENMEDI |
| 76 | `Apotemi Tyt Ayt Kimya 2019-2020` | 352 | 2019-2020 Apotemi TYT-AYT Kimya Soru Bankasi |  | ISLENMEDI |
| 77 | `Aramot Tyt 2023 Fen Bilimleri Model Sorular` | 80 | AROMAT 2023 TYT Fen Bilimleri Model Sorular |  | ISLENMEDI |
| 78 | `Aromat -2023-2024-Matematik Soru Bankasi` | 400 | 2023-2024 AROMAT Matematik Soru Bankasi |  | ISLENMEDI |
| 79 | `Aromat 2024 Ayt Fen Bilimleri` | 82 | Aromat 2024 AYT Fen Bilimleri Net-30 |  | ISLENMEDI |
| 80 | `Aromat 2024 Ayt Fen Bilimleri Model Sorular` | 83 | AROMAT 2024 AYT Fen Bilimleri Model Sorular |  | ISLENMEDI |
| 81 | `Aromat 2024 Ayt Fen Bilimleri Net 30` | 82 | Aromat 2024 AYT Fen Bilimleri Net-30 |  | kopya -> `Aromat 2024 Ayt Fen Bilimleri` |
| 82 | `Aromat Ayt 2023 2024 Fizik Soru Bankasi` | 320 | 2023-2024 AROMAT AYT Fizik Soru Bankasi |  | ISLENMEDI |
| 83 | `Aromat Ayt 2024 Fen Bilimleri Model Sorular Net 30` | 82 | AROMAT 2024 AYT Fen Bilimleri Model Sorular |  | kopya -> `Aromat 2024 Ayt Fen Bilimleri Model Sorular` |
| 84 | `Aromat Ayt 2024 Fen Bilimleri Net 30` | 7 | AROMAT 2024 AYT Fen Bilimleri Model Sorular |  | kopya -> `Aromat 2024 Ayt Fen Bilimleri Model Sorular` |
| 85 | `Aromat Ayt Edebiyat` | 82 | Aromat 2024 AYT Edebiyat Net-30 |  | ISLENMEDI |
| 86 | `Aromat Paragraf Soru Bankasi` | 304 | 2023-2024 AROMAT Paragraf Soru Bankasi |  | ISLENMEDI |
| 87 | `Aromat Tyt 2023 2024 Fizik Soru Bankasi` | 320 | 2023-2024 AROMAT Fizik Soru Bankasi |  | ISLENMEDI |
| 88 | `Aromat Tyt Sosyal Bilimler Model Sorular 2023` | 80 | AROMAT 2023 TYT Sosyal Bilimler Model Sorular |  | ISLENMEDI |
| 89 | `Aromat Tyt Turkce Model Sorular` | 80 | AROMAT 2023 TYT Turkce Model Sorular |  | ISLENMEDI |
| 90 | `Aromat-2023-Ayt-Matematik Soru Bankasi` | 336 | AROMAT 2023 AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 91 | `Aromat-2023-Tyt-Matematik Net 30` | 80 | AROMAT 2023 TYT Matematik Model Sorular |  | ISLENMEDI |
| 92 | `Aromat-2024-Matematik Net 30` | 82 | Aromat 2024 AYT Matematik Net-30 |  | ISLENMEDI |
| 93 | `Aydin Ayt Kamp Kitabim` | 29 | (Aydin Yayinlari Kutuphane uygulamasi - FERNUS degil) |  | KULLANILAMAZ |
| 94 | `Ayt Kartlarla Roman Ozetleri 2022 2023` | 144 | 2022-2023 Kartlarla AYT Roman Ozetleri |  | ISLENMEDI |
| 95 | `Bilgi Sarmal  Tyt Turkce Soru Bankasi` | 336 | 2022-2023 BS TYT Turkce Soru Bankasi |  | ISLENDI |
| 96 | `Bilgi Sarmal 2023 2024 Tyt Ayt Dil Bilgisi Soru Bankasi 2023 2024` | 320 | 2023-2024 BS TYT-AYT Dil Bilgisi Soru Bankasi |  | ISLENMEDI |
| 97 | `Bilgi Sarmal 2024 Ayt Kimya Sopru Bankasi` | 368 | BS 2024 AYT Kimya SB |  | ISLENMEDI |
| 98 | `Bilgi Sarmal 2024 Tyt Kimya Soru Bankasi` | 304 | BILGI SARMAL 2024 TYT Kimya Soru Bankasi |  | ISLENMEDI |
| 99 | `Bilgi Sarmal 2025 Tyt Kimya Video Ders Kitabi` | 144 | BILGI SARMAL 2025 TYT Kimya Video Ders Kitabi |  | ISLENMEDI |
| 100 | `Bilgi Sarmal Ayt Edebiyat Soru Bankasi` | 416 | 2023-2024 BS AYT Edebiyat Soru Bankasi |  | islenmis kitabin kopyasi |
| 101 | `Bilgi Sarmal Ayt Edebiyat Soru Bankasi 2024` | 416 | BS 2024 AYT Edebiyat SB |  | ISLENDI |
| 102 | `Bilgi Sarmal Ayt Edebiyat Video Ders Kitabi 2025` | 304 | BILGI SARMAL 2025 AYT Edebiyat Video Ders Kitabi |  | ISLENMEDI |
| 103 | `Bilgi Sarmal Ayt Soru Bankasi 2020 2021` | 8 | 2020-2021 BS AYT Tarih Soru Bankasi |  | kopya -> `Bilgi Sarmali Ayt Tarih Soru Bankasi 2021 2022` |
| 104 | `Bilgi Sarmal Ayt Tarih Soru Bankasi 2020 2021` | 288 | 2020-2021 BS AYT Tarih Soru Bankasi |  | kopya -> `Bilgi Sarmali Ayt Tarih Soru Bankasi 2021 2022` |
| 105 | `Bilgi Sarmal Ayt Turk Dili ve Edebiyati 2024` | 208 | BS 2024 AYT Turk Edebiyati 25 Brans Deneme | ! | ISLENMEDI |
| 106 | `Bilgi Sarmal Turk Dili ve Edebiyati Sosyal Bilimler 1` | 128 | BILGI SARMAL 2023 Yildizlar Yarisiyor Edebiyat Sosyal Bilimler Brans Denemeleri | ! | ISLENMEDI |
| 107 | `Bilgi Sarmal Tyt Ayt Dil Bilgisi Soru Bankasi 2022 2023` | 320 | 2022-2023 BS TYT-AYT Dil Bilgisi Soru Bankasi |  | kopya -> `Bilgi Sarmal 2023 2024 Tyt Ayt Dil Bilgisi Soru Bankasi 2023 2024` |
| 108 | `Bilgi Sarmal Tyt Ayt Dil Bilgisi Soru Bankasi 2024` | 320 | BILGI SARMAL 2024 TYT-AYT Dil Bilgisi Soru Bankasi |  | kopya -> `Bilgi Sarmal 2023 2024 Tyt Ayt Dil Bilgisi Soru Bankasi 2023 2024` |
| 109 | `Bilgi Sarmal Tyt Ayt Dilbilgisi Soru Bankasi` | 11 | 2022-2023 BS TYT-AYT Dil Bilgisi Soru Bankasi |  | kopya -> `Bilgi Sarmal 2023 2024 Tyt Ayt Dil Bilgisi Soru Bankasi 2023 2024` |
| 110 | `Bilgi Sarmal Tyt Ayt Paragraf Soru Bankasi` | 288 | BS 2024 TYT-AYT Paragraf SB |  | ISLENMEDI |
| 111 | `Bilgi Sarmal Tyt Sosyal Bilimler Video Ders Kitabi 2025` | 208 | BILGI SARMAL 2025 TYT Sosyal Bilimler Video Ders Kitabi |  | ISLENMEDI |
| 112 | `Bilgi Sarmal Tyt Tarih Soru Bankasi` | 272 | 2020-2021 BS TYT Tarih Soru Bankasi | ! | ISLENMEDI |
| 113 | `Bilgi Sarmal Tyt Tarih Soru Bankasi 2020 2021` | 7 | 2020-2021 BS TYT Tarih Soru Bankasi |  | kopya -> `Bilgi Sarmal Tyt Tarih Soru Bankasi` |
| 114 | `Bilgi Sarmal Tyt Tarih Soru Bankasi 2022 2023` | 5 | 2022-2023 BS TYT Tarih Soru Bankasi |  | KULLANILAMAZ |
| 115 | `Bilgi Sarmal Tyt Tarih Soru Bankasi 2023 2024` | 272 | 2023-2024 BS TYT Tarih Soru Bankasi |  | ISLENMEDI |
| 116 | `Bilgi Sarmal Tyt Tarih Soru Bankasi 2024` | 272 | BILGI SARMAL 2024 TYT Tarih Soru Bankasi |  | ISLENMEDI |
| 117 | `Bilgi Sarmal Tyt Turkce Soru Bankasi 2022 2023` | 336 | 2022-2023 BS TYT Turkce Soru Bankasi |  | islenmis kitabin kopyasi |
| 118 | `Bilgi Sarmal Tyt Turkce Soru Bankasi 2023 2024` | 13 | 2023-2024 BS TYT Turkce Soru Bankasi |  | KULLANILAMAZ |
| 119 | `Bilgi Sarmal Tyt Turkce Video Dets Kitabi 2025` | 256 | BILGI SARMAL 2025 TYT Turkce Video Ders Kitabi |  | ISLENMEDI |
| 120 | `Bilgi Sarmal Tyt Turkce Soru Bankasi 2024` | 336 | BILGI SARMAL 2024 TYT Turkce Soru Bankasi |  | ISLENMEDI |
| 121 | `Bilgi Sarmali Ayt Tarih Soru Bankasi 2021 2022` | 288 | 2021-2022 BS AYT Tarih Soru Bankasi |  | ISLENMEDI |
| 122 | `Bilgi Sarmali Ayt 2024 Fizik Soru Bankasi` | 352 | BS 2024 AYT Fizik SB |  | ISLENMEDI |
| 123 | `Bilgi Sarmali Tyt 2024 Fizik Soru Bankasi` | 336 | BILGI SARMAL 2024 TYT Fizik Soru Bankasi |  | ISLENMEDI |
| 124 | `Bilgi Sarmali-2022-2023-Tyt Ayt-Geometri Soru Bankasi` | 402 | 2022-2023 BS TYT-AYT Geometri Soru Bankasi |  | ISLENMEDI |
| 125 | `Bilgi Sarmali-2022-2023-Tyt-Matematik Soru Bankasi` | 440 | 2022-2023 BS AYT Matematik Soru Bankasi | ! | ISLENMEDI |
| 126 | `Bilgi Sarmali-2022-2023-Tyt-Problemler Soru Bankasi` | 176 | 2022-2023 BS TYT Problemler Soru Bankasi |  | ISLENMEDI |
| 127 | `Bilgi Sarmali-2023-2024-Ayt-Matematik Soru Bankasi` | 420 | 2023-2024 BS AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 128 | `Bilgi Sarmali-2023-2024-Problemler Brans DS Yildizlar Yarisiyor` | 112 | 2023-2024 BS TYT Problemler Brans DS Yildizlar Yarisiyor |  | ISLENMEDI |
| 129 | `Bilgi Sarmali-2023-2024-Problemler Soru Bankasi` | 176 | 2023-2024 BS TYT Problemler Soru Bankasi |  | kopya -> `Bilgi Sarmali-2022-2023-Tyt-Problemler Soru Bankasi` |
| 130 | `Bilgi Sarmali-2023-2024-Problemler Yildizlar Yarisiyor` | 112 | 2023-2024 BS TYT Problemler Brans DS Yildizlar Yarisiyor |  | kopya -> `Bilgi Sarmali-2023-2024-Problemler Brans DS Yildizlar Yarisiyor` |
| 131 | `Bilgi Sarmali-2023-2024-Tyt Ayt-Geometri Soru Bankasi` | 400 | 2023-2024 BS TYT-AYT Geometri Soru Bankasi |  | kopya -> `Bilgi Sarmali-2022-2023-Tyt Ayt-Geometri Soru Bankasi` |
| 132 | `Bilgi Sarmali-2023-2024-Tyt-Matematik Soru Bankasi` | 403 | 2023-2024 BS TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 133 | `Bilgi Sarmali-2024-Ayt-Logaritma Diziler` | 8 | BS 2024 AYT Logaritma Diziler |  | kopya -> `Bilgi Sarmali-2024-Ayt-Logaritmik Diziler` |
| 134 | `Bilgi Sarmali-2024-Ayt-Logaritmik Diziler` | 144 | BS 2024 AYT Logaritma Diziler |  | ISLENMEDI |
| 135 | `Bilgi Sarmali-2024-Ayt-Matematik Soru Bankasi` | 425 | BS 2024 AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 136 | `Bilgi Sarmali-2024-Tyt Problemler Soru Bankasi` | 352 | BILGI SARMAL 2024 TYT Problemler Soru Bankasi |  | kopya -> `Bilgi Sarmali-2022-2023-Tyt-Problemler Soru Bankasi` |
| 137 | `Bilgi Sarmali-2025-Ayt-Matematik Soru Bankasi` | 416 | BILGI SARMAL 2025 AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 138 | `Bilgi Sarmali-2025-Ayt-Matematik Video Ders Kitabi` | 356 | BILGI SARMAL 2025 AYT Matematik Video Ders Kitabi |  | ISLENMEDI |
| 139 | `Bilgi Sarmali-2025-Tyt Ayt-Geometri Soru Bankasi` | 400 | BILGI SARMAL 2025 TYT-AYT Geometri Soru Bankasi |  | ISLENMEDI |
| 140 | `Bilgi Sarmali-2025-Tyt-Matematik Soru Bankasi` | 422 | BILGI SARMAL 2025 TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 141 | `Bilgi Sarmali-2025-Tyt-Matematik Video Ders Kitabi` | 289 | BILGI SARMAL 2025 TYT Matematik Video Ders Kitabi |  | ISLENMEDI |
| 142 | `Bilgi Sarmali-Tyt Ayt-Geometri Soru Bankasi` | 401 | BS 2024 TYT-AYT Geometri SB |  | kopya -> `Bilgi Sarmali-2022-2023-Tyt Ayt-Geometri Soru Bankasi` |
| 143 | `C1CELL-2024-Problemler Soru Bankasi` | 208 | C1CELL 2024 Problemler SB |  | ISLENMEDI |
| 144 | `C1CELL-2024-TYT-AYT-Geometri Soru Bankasi` | 420 | C1CELL 2024 TYT-AYT Geometri Soru Bankasi |  | ISLENDI |
| 145 | `C1CELL-2024-TYT-Matematik Soru Bankasi` | 384 | C1CELL 2024 TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 146 | `C1CELL-2025-Matematik Soru Bankasi` | 417 | C1CELL 2025 AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 147 | `CAP-2022-2023-TYT AYT-Geometri Soru Bankasi` | 384 | 2022-2023 CAP TYT-AYT Geometri Soru Bankasi |  | ISLENMEDI |
| 148 | `CAP-2022-2023-TYT-Matematik Soru Bankasi` | 384 | 2022-2023 CAP TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 149 | `CAP-2023-2024-AYT-Matematik Soru Bankasi` | 398 | 2023-2024 CAP AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 150 | `CAP-2023-AYT-Matematik -AL-Soru Bankasi` | 441 | CAP 2023 AYT Matematik AL Soru Bankasi |  | ISLENMEDI |
| 151 | `Cap Anlam Bilgisi Kitabi 2024` | 176 | Cap 2024 Anlam Bilgisi Kitabi |  | ISLENMEDI |
| 152 | `Cap Ayt Edebiyat Soru Bankasi 2022 2023` | 320 | 2022-2023 CAP AYT Edebiyat Soru Bankasi |  | ISLENMEDI |
| 153 | `Cap Ayt Fizik Soru Bankasi 2023 2024` | 320 | 2023-2024 CAP AYT Fizik Soru Bankasi |  | ISLENMEDI |
| 154 | `Cap Ayt Tarih Soru Bankasi` | 288 | 2020-2021 CAP AYT Tarih SB (s1-192) + 2023-2024 CAP AYT Tarih SB (s193-288) |  | ISLENMEDI |
| 155 | `Cap Tyt Dil Bilgisi Konu Anlatimli Soru Bankasi` | 352 | CAP 2025 TYT Dil Bilgisi Konu Anlatimli Soru Bankasi |  | ISLENMEDI |
| 156 | `Cap Tyt Fizik Soru Bankasi 2023 2024` | 288 | 2023-2024 CAP TYT Fizik Soru Bankasi |  | ISLENMEDI |
| 157 | `Cap Tyt Konu Anlatimli Soru Bankasi 2024` | 304 | CAP 2024 TYT Paragraf Konu Anlatimli Soru Bankasi |  | ISLENMEDI |
| 158 | `Cap Tyt Tarih Soru Bankasi 2020 2021` | 192 | 2020-2021 CAP TYT Tarih Soru Bankasi |  | ISLENMEDI |
| 159 | `Cap Tyt Tarih Soru Bankasi 2023 2024` | 240 | 2023-2024 CAP TYT Tarih Soru Bankasi |  | ISLENMEDI |
| 160 | `Cap Tyt Turkce Soru Bankasi` | 304 | 2020-2021 CAP TYT Turkce Soru Bankasi |  | ISLENMEDI |
| 161 | `Cap Tyt Turkce Soru Bankasi 2023 2024` | 352 | 2023-2024 CAP TYT Turkce Soru Bankasi |  | ISLENMEDI |
| 162 | `Edebiyat Denizi Ayt Edebiyat Soru Bankasi` | 304 | Ed(ebiyat Denizi) 2024 AYT Edebiyat Soru Bankasi |  | ISLENMEDI |
| 163 | `Edebiyat Denizi Tyt Ayt Paragraf Soru Bankasi 2024` | 336 | ED 2024 TYT-AYT Paragraf SB |  | ISLENMEDI |
| 164 | `Edebiyat Sohagi Paragraf Orta Duzey` | 304 | Es(Edebiyat Sokagi) 2024 Orta Duzey Paragraf | ! | ISLENMEDI |
| 165 | `Edebiyat Sokagi Atasozleri ve Deyimler Soru Bankasi` | 160 | Es 2024 Atasozleri-Deyimler Soru Bankasi |  | ISLENMEDI |
| 166 | `Edebiyat Sokagi Ayt Edebiyat Soru Bankasi` | 304 | Es 2024 AYT Edebiyat Yeni Nesil Soru Bankasi |  | ISLENMEDI |
| 167 | `Edebiyat Sokagi Ayt Edebiyat Yeterlilik Testi` | 160 | Es 2024 AYT Edebiyat Denemeleri | ! | ISLENMEDI |
| 168 | `Edebiyat Sokagi Baslangic Paragraf` | 224 | Es 2024 Baslangic Paragraf |  | ISLENMEDI |
| 169 | `Edebiyat Sokagi Dil Bilgisi Soru Bankasi 2024` | 272 | Es 2024 Dil Bilgisi |  | ISLENMEDI |
| 170 | `Edebiyat Sokagi Paragraf Analizi` | 160 | Es 2024 Paragraf Analizi |  | ISLENMEDI |
| 171 | `Edebiyat Sokagi Paragraf Yeterlilik Testi 2024` | 248 | Es 2024 Paragraf Yeterlilik Testi |  | ISLENMEDI |
| 172 | `Edebiyat Sokagi Paragraf ileri Duzey` | 309 | Es 2024 Ileri Duzey Paragraf |  | ISLENMEDI |
| 173 | `Egsersiz Tyt Fizik Soru Bankasi 2021` | 352 | Egzersiz 2021 TYT Fizik Soru Bankasi |  | ISLENMEDI |
| 174 | `Esen 2024 Motivasyon Fizik 2` | 304 | (Esen) 2024 Motivasyon Fizik 2 PSB | ! | ISLENMEDI |
| 175 | `Esen 2025 Aps Ayt Fizik Soru Bankasi` | 240 | (Esen) 2025 APS AYT Fizik SB |  | ISLENMEDI |
| 176 | `Esen 2025 Aps Ayt Matemat,k Soru Bankasi` | 192 | (Esen) 2025 APS AYT Matematik SB |  | ISLENMEDI |
| 177 | `Esen Aps Ayt Edebiyat Soru Bankasi` | 304 | (Esen) 2025 APS AYT Edebiyat SB |  | ISLENMEDI |
| 178 | `Esen Aps Biyoloji Soru Bankasi` | 160 | (Esen) 2025 APS TYT Biyoloji SB |  | ISLENMEDI |
| 179 | `Esen Aps Cografya Soru Bankasi` | 260 | (Esen) 2025 APS TYT Cografya SB |  | ISLENMEDI |
| 180 | `Esen Aps Fizik Soru Bankasi 3` | 224 | (Esen) 2025 APS TYT Fizik SB | ! | ISLENMEDI |
| 181 | `Esen Aps Geometri Soru Bankasi` | 283 | (Esen) 2025 APS TYT-AYT Geometri SB |  | ISLENMEDI |
| 182 | `Esen Aps Kimya Soru Bankasi` | 208 | (Esen) 2025 APS TYT Kimya SB |  | ISLENMEDI |
| 183 | `Esen Aps Tyt Ayt Tarih Soru Bankasi` | 336 | (Esen) 2025 APS TYT-AYT Tarih SB |  | ISLENMEDI |
| 184 | `Esen Aps Tyt Matematik Soru Bankasi` | 354 | (Esen) 2025 APS TYT Matematik SB |  | ISLENMEDI |
| 185 | `Esen Aps Tyt Turkce Soru Bankasi` | 352 | (Esen) 2025 APS TYT Turkce SB |  | ISLENMEDI |
| 186 | `Esen Apt Ayt Fizik 2025` | 224 | (Esen) 2025 APS AYT Biyoloji SB | ! | ISLENMEDI |
| 187 | `Esen Aylik Planli Biyoloji Soru Bankasi` | 240 | (Esen) 2025 APS AYT Kimya SB | ! | ISLENMEDI |
| 188 | `Esen Ayt Fizik Soru Bankasi` | 352 | (Esen) AYT Fizik Soru Bankasi |  | ISLENMEDI |
| 189 | `Esen Ayt Kimya Soru Bankasi` | 288 | (Esen) AYT Kimya Soru Bankasi |  | ISLENMEDI |
| 190 | `Esen Ayt Tarih Soru Bankasi` | 272 | (Esen) AYT Cografya Soru Bankasi | ! | ISLENMEDI |
| 191 | `Esen Tyt  Matematik Soru Bankasi` | 449 | (Esen) TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 192 | `Esen Tyt Ayt Biyoloji Soru Bankasi` | 288 | (Esen) TYT-AYT Biyoloji Soru Bankasi |  | ISLENMEDI |
| 193 | `Esen Tyt Ayt Geometri Soru Bankasi` | 352 | (Esen) TYT-AYT Geometri Soru Bankasi |  | ISLENMEDI |
| 194 | `Esen Tyt Cografya Soru Bankasi` | 320 | (Esen) TYT Cografya Soru Bankasi |  | ISLENMEDI |
| 195 | `Esen Tyt FizikSoru Bankasi` | 304 | (Esen) TYT Fizik Soru Bankasi |  | ISLENMEDI |
| 196 | `Esen Tyt Kimya Soru Bankasi` | 256 | (Esen) TYT Kimya Soru Bankasi |  | ISLENMEDI |
| 197 | `Esen Tyt Tarih Soru Bankasi` | 336 | (Esen) TYT Tarih Soru Bankasi |  | ISLENMEDI |
| 198 | `Esen Tyt Turkce Soru Bankasi` | 432 | (Esen) TYT Turkce Soru Bankasi |  | ISLENMEDI |
| 199 | `Esen Yks Motivasyon Biyoloji` | 216 | (Esen) 2024 Motivasyon Biyoloji PSB |  | ISLENMEDI |
| 200 | `Esen Yks Motivasyon Fizik Testleri` | 272 | (Esen) 2024 Motivasyon Fizik 1 PSB | ! | ISLENMEDI |
| 201 | `Esen Yks Motivasyon Kimya Soru Bankasi` | 264 | (Esen) 2024 TYT Kimya PSB (Motivasyon) | ! | ISLENMEDI |
| 202 | `Esen-Kronograf-Tyt-Paragraf Soru Bankasi` | 320 | (Esen) TYT Kronograf Soru Bankasi |  | ISLENMEDI |
| 203 | `Fizipedia Ayt Fizik Soru Bankasi 2025` | 368 | FIZIPEDIA 2025 AYT Fizik Soru Bankasi |  | ISLENMEDI |
| 204 | `Fizipedia Tyt Fizik Soru Bankasi 2025` | 352 | FIZIPEDIA 2025 TYT Fizik Soru Bankasi |  | ISLENMEDI |
| 205 | `Full Matematik-2019-2020-Geometri Soru Bankasi` | 272 | 2019-2020 Full Matematik Geometri Soru Bankasi |  | ISLENMEDI |
| 206 | `Full Matematik-2022-2023-Tyt Ayt-Geometri Soru Bankasi` | 352 | 2022-2023 FULL TYT-AYT Geometri Soru Bankasi |  | ISLENMEDI |
| 207 | `Full Matematik-2022-2023-Tyt-Matematik Soru Bankasi` | 368 | 2022-2023 FULL TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 208 | `Full Matematik-Ayt-Matematik Soru Bankasi` | 386 | 2022-2023 FULL AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 209 | `Full Matematik-Tyt-Matematik Soru Bankasi` | 288 | 2019-2020 FM TYT Matematik Soru Bankasi |  | ISLENMEDI |
| 210 | `Full-2019-2020-Ayt-Matematik Soru Bankasi` | 288 | 2019-2020 Full Matematik AYT Matematik Soru Bankasi |  | ISLENMEDI |
| 211 | `Full-Ayt-Matematik Soru Bankasi` | 12 | 2019-2020 Full Matematik AYT Matematik Soru Bankasi |  | kopya -> `Full-2019-2020-Ayt-Matematik Soru Bankasi` |
| 212 | `Mikro Orijinal Tyt Fizik Soru Bankasi 2025` | 400 | MIKRO ORIJINAL 2025 TYT Fizik Soru Bankasi |  | ISLENDI |
| 213 | `Mikro Orijinal Tyt Paragraf Soru Bankasi 2024` | 304 | MIKRO ORIJINAL 2024 TYT Paragraf Soru Bankasi |  | ISLENMEDI |
| 214 | `Mikro Orijinal-2024-Ayt-12liDeneme-1` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-1 |  | ISLENMEDI |
| 215 | `Mikro Orijinal-2024-Ayt-12liDeneme-10` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-10 |  | ISLENMEDI |
| 216 | `Mikro Orijinal-2024-Ayt-12liDeneme-11` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-11 |  | ISLENMEDI |
| 217 | `Mikro Orijinal-2024-Ayt-12liDeneme-12` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-12 |  | ISLENMEDI |
| 218 | `Mikro Orijinal-2024-Ayt-12liDeneme-2` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-2 |  | KULLANILAMAZ |
| 219 | `Mikro Orijinal-2024-Ayt-12liDeneme-3` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-3 |  | ISLENMEDI |
| 220 | `Mikro Orijinal-2024-Ayt-12liDeneme-4` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-4 |  | ISLENMEDI |
| 221 | `Mikro Orijinal-2024-Ayt-12liDeneme-5` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-5 |  | ISLENMEDI |
| 222 | `Mikro Orijinal-2024-Ayt-12liDeneme-6` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-6 |  | ISLENMEDI |
| 223 | `Mikro Orijinal-2024-Ayt-12liDeneme-7` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-7 |  | ISLENMEDI |
| 224 | `Mikro Orijinal-2024-Ayt-12liDeneme-8` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-8 |  | ISLENMEDI |
| 225 | `Mikro Orijinal-2024-Ayt-12liDeneme-9` | 16 | Mikro Orijinal 2024 AYT 12'li Deneme-9 |  | ISLENMEDI |
| 226 | `Mikro Orijinal-2024-Ayt-Matematik Soru Bankasi` | 400 | Mikro Orijinal 2024 AYT Matematik SB |  | ISLENMEDI |
| 227 | `Mikro Orijinal-2024-Tyt-12liDeneme-10` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-10 |  | ISLENMEDI |
| 228 | `Mikro Orijinal-2024-Tyt-12liDeneme-11` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-11 |  | ISLENMEDI |
| 229 | `Mikro Orijinal-2024-Tyt-12liDeneme-12` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-12 |  | ISLENMEDI |
| 230 | `Mikro Orijinal-2024-Tyt-12liDeneme-2` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-2 |  | ISLENMEDI |
| 231 | `Mikro Orijinal-2024-Tyt-12liDeneme-3` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-3 |  | ISLENMEDI |
| 232 | `Mikro Orijinal-2024-Tyt-12liDeneme-4` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-4 |  | ISLENMEDI |
| 233 | `Mikro Orijinal-2024-Tyt-12liDeneme-5` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-5 |  | ISLENMEDI |
| 234 | `Mikro Orijinal-2024-Tyt-12liDeneme-6` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-6 |  | ISLENMEDI |
| 235 | `Mikro Orijinal-2024-Tyt-12liDeneme-7` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-7 |  | ISLENMEDI |
| 236 | `Mikro Orijinal-2024-Tyt-12liDeneme-8` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-8 |  | ISLENMEDI |
| 237 | `Mikro Orijinal-2024-Tyt-12liDeneme-9` | 16 | Mikro Orijinal 2024 TYT 12'li Deneme-9 |  | ISLENMEDI |
| 238 | `Mikro Orijinal-2024-Tyt-Matematik Soru Bankasi` | 400 | MIKRO ORIJINAL 2024 TYT Matematik SB |  | ISLENMEDI |
| 239 | `Mikro Orijinal-2024-matematik Soru Bankasi` | 384 | MIKRO ORIJINAL 2024 Matematik Soru Bankasi |  | ISLENMEDI |
| 240 | `Mikro Orijinal-2025-Ayt-Geometri Soru Bankasi` | 416 | MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi |  | ISLENDI |
| 241 | `Mikro Orijinal-Tyt Ayt-Geometri Soru Bankasi 2` | 416 | MIKRO ORIJINAL 2024 TYT-AYT Geometri SB | ! | ISLENMEDI |
| 242 | `Mikro-2024-Tyt Ayt-Geometri Soru Bankasi` | 400 | Mikro Orijinal 2024 TYT-AYT Geometri Soru Bankasi |  | ISLENMEDI |
| 243 | `Neofizik Ayt Fizik Soru Bankasi 2025` | 335 | NEOFIZIK 2025 AYT Fizik Soru Bankasi |  | ISLENDI |
| 244 | `Neofizik Tyt Soru Bankasi` | 256 | NEOFIZIK 2024 TYT Soru Bankasi |  | ISLENDI |
| 245 | `Orijinal-2024-Ayt-Trigonometri` | 208 | Orijinal 2024 AYT Trigonometri |  | ISLENMEDI |
| 246 | `Orijinal-2024-Ayt-integral` | 160 | Orijinal 2024 AYT Integral |  | ISLENMEDI |
| 247 | `Orijinal-2024-Geometri` | 160 | Orijinal 2024 Analitik Geometri | ! | ISLENMEDI |
| 248 | `Orijinal-2024-Geometri Soru Bankasi` | 432 | Orijinal 2024 TYT-AYT Geometri SB |  | HAZIR |
| 249 | `Orijinal-2024-Matematik Soru Bankasi` | 400 | ORIJINAL 2024 TYT Matematik SB |  | KULLANILAMAZ |
| 250 | `Orijinal-2024-Tyt Ayt-Fonksiyonlar` | 144 | Orijinal 2024 TYT-AYT Fonksiyonlar |  | ISLENMEDI |
| 251 | `Orijinal-2025-Analitik Geometri` | 192 | ORIJINAL 2025 Analitik Geometri |  | ISLENMEDI |
| 252 | `Orijinal-2025-Ayt-Matematik Turev` | 193 | ORIJINAL 2025 AYT Matematik Turev |  | ISLENMEDI |
| 253 | `Orijinal-2025-Ayt-Polinom parabol` | 208 | ORIJINAL 2025 AYT Polinom Parabol |  | ISLENMEDI |
| 254 | `Orijinal-2025-Limit` | 128 | ORIJINAL 2025 AYT Matematik Limit Sureklilik |  | ISLENMEDI |
| 255 | `Orijinal-2025-Logaritma Diziler` | 144 | ORIJINAL 2025 AYT Logaritma Diziler |  | ISLENMEDI |
| 256 | `Orijinal-2025-Tyt-Matematik Porblemler` | 208 | ORIJINAL 2025 TYT Matematik Problemler |  | ISLENMEDI |
| 257 | `Orijinal-Tyt Ayt Geometri Soru Bankasi` | 432 | ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi |  | ISLENMEDI |
| 258 | `Orijinal2024-Ayt-Matematik Soru Bankasi` | 418 | ORIJINAL 2024 AYT Matematik SB |  | ISLENMEDI |
| 259 | `PES-Konu ozetleri-Problemler Kampi` | 128 | 2020-2021 PES Problemler Kampi |  | ISLENMEDI |
| 260 | `Pes Kurgulu Paragraf 2020 2021` | 288 | 2020-2021 PES Kurgulu Paragraf |  | ISLENMEDI |
| 261 | `Pes PRofesyonel Anlam ve Problem Sorulari 2020 2021` | 240 | 2020-2021 PES Profesyonel Anlam Sorulari - Profesyonel Problem Sorulari |  | ISLENMEDI |
| 262 | `Pes Paragraf Soru Bankasi 2020 2021` | 288 | 2020-2021 PES Kurgulu Paragraf Soru Bankasi |  | kopya -> `Pes Kurgulu Paragraf 2020 2021` |
| 263 | `Pes Sozcuk ve Cumlede Anlam 2020 2021` | 160 | 2020-2021 PES Sozcukte Cumlede Anlam Kampi |  | ISLENMEDI |
| 264 | `Pes Sozcukte Cumle anlam Lampi 2020 2021` | 6 | 2020-2021 PES Sozcukte Cumlede Anlam Kampi |  | kopya -> `Pes Sozcuk ve Cumlede Anlam 2020 2021` |
| 265 | `Pes Tyt Ayt Paragraf Sorulari 2020 2021` | 288 | 2020-2021 PES TYT-AYT Paragraf Soru Bankasi |  | ISLENMEDI |
| 266 | `Sure Ayt Edebiyat Soru Bankasi 2023` | 321 | SURE 2023 AYT Edebiyat Soru Bankasi |  | ISLENMEDI |
| 267 | `Sure Ayt Edebiyat Soru Bankasi 2023` | 5 | SURE 2023 AYT Edebiyat Soru Bankasi |  | kopya -> `Sure Ayt Edebiyat Soru Bankasi 2023` |
| 268 | `Sure Edebiyat Suresi 2025` | 320 | SURE 2025 Edebiyatin Suresi |  | kopya -> `Sure Ayt Edebiyat Soru Bankasi 2023` |
| 269 | `Sure Paragrafin Suresi 2025` | 288 | SURE 2025 Paragrafin Suresi |  | ISLENMEDI |
| 270 | `Sure Tyt Ayt Paragraf Soru Bankasi 2023 2024` | 288 | 2023-2024 SURE TYT-AYT Paragraf Soru Bankasi |  | kopya -> `Sure Paragrafin Suresi 2025` |
| 271 | `Sure Tyt Ayt Paragraf Soru Bankasi 2023 2024` | 3 | (YouTube tarayici penceresi - kitap degil) |  | KULLANILAMAZ |
| 272 | `Sure Tyt Paragraf Gunlukleri` | 4 | SURE 2023 TYT Paragraf Gunlukleri |  | kopya -> `Sure Tyt Paragraf Gunlukleri 2023` |
| 273 | `Sure Tyt Paragraf Gunlukleri 2023` | 305 | SURE 2023 TYT Paragraf Gunlukleri |  | ISLENMEDI |
| 274 | `Sure Tyt Turkce Soru Bankasi 2023 2024` | 336 | 2023-2024 SURE TYT Turkce Soru Bankasi |  | ISLENMEDI |
| 275 | `Vaf Ayt Turk Dili ve Edebiyati` | 288 | 2020-2021 AYT Turk Dili ve Edebiyati Soru Bankasi (Vaf) |  | ISLENMEDI |
| 276 | `Vaf Capli Paragraf Soru Bankasi` | 296 | 2020-2021 CAP Capli Paragraf | ! | ISLENMEDI |
| 277 | `Viral-2025-Tyt Matematik` | 288 | VIRAL 2025 TYT Matematik |  | ISLENMEDI |

## 8. Olculen tum ciftler

A->B = A'nin iceriginin B'de bulunan orani (alt sinir). sayfa90 = 16 ornekten >=0.90 eslesen orani.

| A | B | A->B | B->A | sayfa90 A->B | not |
|---|---|---|---|---|---|
| 0 2019-2020 ACIL AYT Matematik Soru Bankasi | 6 2020-2021 ACIL AYT Matematik Soru Bankasi | %28 | %31 | 0.00 | gozle AYNI icerik |
| 0 2019-2020 ACIL AYT Matematik Soru Bankasi | 19 2023-2024 ACIL AYT Matematik Soru Bankasi | %1 | %0 | 0.00 |  |
| 1 2019-2020 Acil TYT Soru Bankasi | 2 2019-2020 Acil Matematigin Ilaci-1 | %4 | %1 | - |  |
| 1 2019-2020 Acil TYT Soru Bankasi | 51 ACIL 2025 Matematigin Ilaci Polinom | %0 | %0 | - |  |
| 1 2019-2020 Acil TYT Soru Bankasi | 52 ACIL 2025 Matematigin Ilaci Sayilar-1 | %0 | %0 | - |  |
| 1 2019-2020 Acil TYT Soru Bankasi | 53 ACIL 2025 Matematigin Ilaci Sayilar-2 | %0 | %0 | - |  |
| 1 2019-2020 Acil TYT Soru Bankasi | 55 ACIL 2025 AYT Soru Bankasi | %0 | %0 | 0.00 |  |
| 1 2019-2020 Acil TYT Soru Bankasi | 56 ACIL 2025 TYT Soru Bankasi | %0 | %0 | 0.00 |  |
| 2 2019-2020 Acil Matematigin Ilaci-1 | 4 2019-2020 Acil Matematigin Ilaci TYT Matematik Soru Bankasi | %28 | %31 | 0.00 |  |
| 2 2019-2020 Acil Matematigin Ilaci-1 | 23 2023-2024 ACIL TYT Matematigin Ilaci | %18 | %26 | 0.00 |  |
| 2 2019-2020 Acil Matematigin Ilaci-1 | 56 ACIL 2025 TYT Soru Bankasi | %0 | %0 | - |  |
| 3 2019-2020 Acil Matematigin Ilaci TYT Matematik Soru Bankasi | 4 2019-2020 Acil Matematigin Ilaci TYT Matematik Soru Bankasi | %0 | %0 | 0.00 |  |
| 4 2019-2020 Acil Matematigin Ilaci TYT Matematik Soru Bankasi | 23 2023-2024 ACIL TYT Matematigin Ilaci | %81 | %81 | 0.69 |  |
| 4 2019-2020 Acil Matematigin Ilaci TYT Matematik Soru Bankasi | 52 ACIL 2025 Matematigin Ilaci Sayilar-1 | %0 | %2 | - |  |
| 4 2019-2020 Acil Matematigin Ilaci TYT Matematik Soru Bankasi | 53 ACIL 2025 Matematigin Ilaci Sayilar-2 | %1 | %1 | - |  |
| 5 2019-2020 APOTEMI TYT Matematik Soru Bankasi | 11 2021-2022 Apotemi Limit ve Sureklilik | %0 | %0 | - |  |
| 5 2019-2020 APOTEMI TYT Matematik Soru Bankasi | 12 2021-2022 Apotemi Problemler | %0 | %0 | - |  |
| 5 2019-2020 APOTEMI TYT Matematik Soru Bankasi | 13 2021-2022 Apotemi Trigonometri | %0 | %0 | - |  |
| 5 2019-2020 APOTEMI TYT Matematik Soru Bankasi | 16 2022-2023 APOTEMI Fonksiyonlar | %0 | %0 | - |  |
| 5 2019-2020 APOTEMI TYT Matematik Soru Bankasi | 17 2022 Apotemi Turev | %0 | %1 | - |  |
| 5 2019-2020 APOTEMI TYT Matematik Soru Bankasi | 18 2022 Apotemi Integral | %0 | %0 | - |  |
| 6 2020-2021 ACIL AYT Matematik Soru Bankasi | 19 2023-2024 ACIL AYT Matematik Soru Bankasi | %1 | %0 | 0.00 |  |
| 6 2020-2021 ACIL AYT Matematik Soru Bankasi | 55 ACIL 2025 AYT Soru Bankasi | %0 | %0 | 0.00 |  |
| 7 2020-2021 ACIL TYT Matematik Soru Bankasi | 20 2023-2024 ACIL TYT Matematik Soru Bankasi | %0 | %0 | 0.00 |  |
| 7 2020-2021 ACIL TYT Matematik Soru Bankasi | 56 ACIL 2025 TYT Soru Bankasi | %0 | %2 | 0.00 |  |
| 8 2020-2021 Acil Problemlerin Ilaci | 54 ACIL 2025 Problemlerin Ilaci | %42 | %82 | 0.00 |  |
| 9 2020-2021 Acil TYT-AYT Geometrinin Ilaci Soru Bankasi | 21 2023-2024 ACIL TYT-AYT Geometri Soru Bankasi | %2 | %1 | - |  |
| 9 2020-2021 Acil TYT-AYT Geometrinin Ilaci Soru Bankasi | 22 2023-2024 ACIL TYT-AYT Geometrinin Ilaci | %17 | %17 | 0.00 | gozle AYNI icerik |
| 9 2020-2021 Acil TYT-AYT Geometrinin Ilaci Soru Bankasi | 57 ACIL 2025 TYT-AYT Geometri Soru Bankasi | %2 | %0 | - |  |
| 14 2022-2023 ACIL Analitik Geometri | 21 2023-2024 ACIL TYT-AYT Geometri Soru Bankasi | %1 | %0 | - |  |
| 14 2022-2023 ACIL Analitik Geometri | 57 ACIL 2025 TYT-AYT Geometri Soru Bankasi | %0 | %0 | - |  |
| 15 2022-2023 ACIL Kati Cisimler | 21 2023-2024 ACIL TYT-AYT Geometri Soru Bankasi | %1 | %0 | - |  |
| 15 2022-2023 ACIL Kati Cisimler | 57 ACIL 2025 TYT-AYT Geometri Soru Bankasi | %0 | %0 | - |  |
| 19 2023-2024 ACIL AYT Matematik Soru Bankasi | 55 ACIL 2025 AYT Soru Bankasi | %36 | %22 | 0.00 |  |
| 20 2023-2024 ACIL TYT Matematik Soru Bankasi | 56 ACIL 2025 TYT Soru Bankasi | %30 | %33 | 0.00 |  |
| 21 2023-2024 ACIL TYT-AYT Geometri Soru Bankasi | 22 2023-2024 ACIL TYT-AYT Geometrinin Ilaci | %1 | %0 | - |  |
| 21 2023-2024 ACIL TYT-AYT Geometri Soru Bankasi | 24 2024 ACIL TYT Matematik Geometri Kitap-1 | %1 | %1 | - |  |
| 21 2023-2024 ACIL TYT-AYT Geometri Soru Bankasi | 57 ACIL 2025 TYT-AYT Geometri Soru Bankasi | %0 | %0 | 0.00 | gozle FARKLI |
| 22 2023-2024 ACIL TYT-AYT Geometrinin Ilaci | 57 ACIL 2025 TYT-AYT Geometri Soru Bankasi | %1 | %0 | - |  |
| 23 2023-2024 ACIL TYT Matematigin Ilaci | 51 ACIL 2025 Matematigin Ilaci Polinom | %1 | %0 | - |  |
| 23 2023-2024 ACIL TYT Matematigin Ilaci | 52 ACIL 2025 Matematigin Ilaci Sayilar-1 | %1 | %2 | - |  |
| 23 2023-2024 ACIL TYT Matematigin Ilaci | 53 ACIL 2025 Matematigin Ilaci Sayilar-2 | %1 | %1 | - |  |
| 24 2024 ACIL TYT Matematik Geometri Kitap-1 | 57 ACIL 2025 TYT-AYT Geometri Soru Bankasi | %0 | %0 | - |  |
| 25 345 2024 AYT Biyoloji Soru Bankasi | 30 345 2025 AYT Biyoloji SB | %56 | %69 | 0.38 |  |
| 26 345 2024 AYT Fizik SB | 31 345 2025 AYT Fizik SB | %100 | %100 | 0.94 |  |
| 27 345 2024 AYT Kimya Soru Bankasi | 32 345 2025 AYT Kimya SB | %96 | %100 | 0.81 |  |
| 28 345 2024 AYT Matematik SB | 33 345 2025 AYT Matematik SB | %94 | %95 | 0.81 |  |
| 29 345 2024 TYT Matematik SB | 36 345 2025 Start Matematik | %0 | %0 | - |  |
| 29 345 2024 TYT Matematik SB | 41 345 2025 TYT Matematik SB | %87 | %88 | 0.75 |  |
| 35 345 2025 Paragraf Sifir Risk SB | 43 345 2025 TYT Turkce SB | %0 | %0 | - |  |
| 36 345 2025 Start Matematik | 41 345 2025 TYT Matematik SB | %0 | %0 | - |  |
| 37 345 2025 TYT-AYT Geometri SB 1 | 44 345 2024 TYT-AYT Geometri SB | %100 | %75 | 1.00 |  |
| 37 345 2025 TYT-AYT Geometri SB 1 | 45 345 2025 TYT-AYT Geometri SB 2 | %0 | %0 | 0.00 |  |
| 38 345 2025 TYT Biyoloji SB | 46 345 2024 TYT Biyoloji SB | %72 | %71 | 0.44 |  |
| 39 345 2025 TYT Fizik SB | 47 345 2024 TYT Fizik SB | %100 | %100 | 1.00 |  |
| 40 345 2025 TYT Kimya SB | 48 345 2024 TYT Kimya SB | %100 | %100 | 0.94 |  |
| 42 345 2025 TYT Sosyal Bilgiler SB | 49 345 2024 TYT Sosyal Bilgiler SB | %93 | %93 | 0.69 |  |
| 43 345 2025 TYT Turkce SB | 50 345 2024 TYT Turkce SB | %100 | %100 | 1.00 |  |
| 44 345 2024 TYT-AYT Geometri SB | 45 345 2025 TYT-AYT Geometri SB 2 | %0 | %0 | 0.00 |  |
| 51 ACIL 2025 Matematigin Ilaci Polinom | 56 ACIL 2025 TYT Soru Bankasi | %0 | %0 | - |  |
| 52 ACIL 2025 Matematigin Ilaci Sayilar-1 | 56 ACIL 2025 TYT Soru Bankasi | %0 | %0 | - |  |
| 53 ACIL 2025 Matematigin Ilaci Sayilar-2 | 56 ACIL 2025 TYT Soru Bankasi | %0 | %0 | - |  |
| 59 2019-2020 Aktif 0'dan Baslayanlara Aktif Kimya | 62 2022-2023 Kartlarla AYT Kimya | %0 | %0 | - |  |
| 59 2019-2020 Aktif 0'dan Baslayanlara Aktif Kimya | 63 2019-2020 Aktif AYT Kimya | %1 | %2 | 0.00 |  |
| 62 2022-2023 Kartlarla AYT Kimya | 63 2019-2020 Aktif AYT Kimya | %0 | %0 | - |  |
| 62 2022-2023 Kartlarla AYT Kimya | 66 2022-2023 ALTYAPI Kartlarla TYT Kimya | %0 | %0 | - |  |
| 64 AKTIF 2025 TYT Dil Bilgisi Soru Bankasi | 65 AKTIF 2025 TYT Paragraf Soru Bankasi | %0 | %0 | - |  |
| 68 2022-2023 Kartlarla AYT Fizik | 69 2022-2023 ALTYAPI Kartlarla TYT Fizik | %25 | %18 | - |  |
| 70 2019-2020 Apotemi Modern Fizik Konu Anlatimli SB | 73 2022-2023 Apotemi Modern Fizik | %48 | %32 | 0.19 | gozle AYNI icerik |
| 77 AROMAT 2023 TYT Fen Bilimleri Model Sorular | 87 2023-2024 AROMAT Fizik Soru Bankasi | %0 | %0 | - |  |
| 78 2023-2024 AROMAT Matematik Soru Bankasi | 90 AROMAT 2023 AYT Matematik Soru Bankasi | %12 | %25 | 0.06 | gozle FARKLI |
| 78 2023-2024 AROMAT Matematik Soru Bankasi | 91 AROMAT 2023 TYT Matematik Model Sorular | %0 | %0 | - |  |
| 79 Aromat 2024 AYT Fen Bilimleri Net-30 | 80 AROMAT 2024 AYT Fen Bilimleri Model Sorular | %26 | %26 | - |  |
| 79 Aromat 2024 AYT Fen Bilimleri Net-30 | 81 Aromat 2024 AYT Fen Bilimleri Net-30 | %100 | %100 | 1.00 |  |
| 80 AROMAT 2024 AYT Fen Bilimleri Model Sorular | 82 2023-2024 AROMAT AYT Fizik Soru Bankasi | %0 | %0 | - |  |
| 80 AROMAT 2024 AYT Fen Bilimleri Model Sorular | 83 AROMAT 2024 AYT Fen Bilimleri Model Sorular | %100 | %100 | 1.00 |  |
| 86 2023-2024 AROMAT Paragraf Soru Bankasi | 89 AROMAT 2023 TYT Turkce Model Sorular | %0 | %0 | - |  |
| 90 AROMAT 2023 AYT Matematik Soru Bankasi | 92 Aromat 2024 AYT Matematik Net-30 | %0 | %0 | - |  |
| 95 2022-2023 BS TYT Turkce Soru Bankasi | 96 2023-2024 BS TYT-AYT Dil Bilgisi Soru Bankasi | %5 | %3 | - |  |
| 95 2022-2023 BS TYT Turkce Soru Bankasi | 107 2022-2023 BS TYT-AYT Dil Bilgisi Soru Bankasi | %6 | %3 | - |  |
| 95 2022-2023 BS TYT Turkce Soru Bankasi | 110 BS 2024 TYT-AYT Paragraf SB | %1 | %3 | - |  |
| 95 2022-2023 BS TYT Turkce Soru Bankasi | 117 2022-2023 BS TYT Turkce Soru Bankasi | %100 | %100 | 1.00 |  |
| 95 2022-2023 BS TYT Turkce Soru Bankasi | 118 2023-2024 BS TYT Turkce Soru Bankasi | %0 | %0 | 0.00 |  |
| 95 2022-2023 BS TYT Turkce Soru Bankasi | 119 BILGI SARMAL 2025 TYT Turkce Video Ders Kitabi | %2 | %0 | - |  |
| 95 2022-2023 BS TYT Turkce Soru Bankasi | 120 BILGI SARMAL 2024 TYT Turkce Soru Bankasi | %62 | %56 | 0.44 |  |
| 96 2023-2024 BS TYT-AYT Dil Bilgisi Soru Bankasi | 107 2022-2023 BS TYT-AYT Dil Bilgisi Soru Bankasi | %89 | %100 | 0.56 |  |
| 96 2023-2024 BS TYT-AYT Dil Bilgisi Soru Bankasi | 108 BILGI SARMAL 2024 TYT-AYT Dil Bilgisi Soru Bankasi | %94 | %94 | 0.94 |  |
| 98 BILGI SARMAL 2024 TYT Kimya Soru Bankasi | 99 BILGI SARMAL 2025 TYT Kimya Video Ders Kitabi | %0 | %0 | 0.00 |  |
| 100 2023-2024 BS AYT Edebiyat Soru Bankasi | 101 BS 2024 AYT Edebiyat SB | %88 | %88 | 0.81 |  |
| 100 2023-2024 BS AYT Edebiyat Soru Bankasi | 105 BS 2024 AYT Turk Edebiyati 25 Brans Deneme | %0 | %0 | - |  |
| 101 BS 2024 AYT Edebiyat SB | 102 BILGI SARMAL 2025 AYT Edebiyat Video Ders Kitabi | %1 | %1 | 0.00 |  |
| 101 BS 2024 AYT Edebiyat SB | 105 BS 2024 AYT Turk Edebiyati 25 Brans Deneme | %0 | %0 | - |  |
| 101 BS 2024 AYT Edebiyat SB | 106 BILGI SARMAL 2023 Yildizlar Yarisiyor Edebiyat Sosyal Bilimler Brans Denemeleri | %0 | %0 | - |  |
| 104 2020-2021 BS AYT Tarih Soru Bankasi | 121 2021-2022 BS AYT Tarih Soru Bankasi | %91 | %82 | 0.60 |  |
| 107 2022-2023 BS TYT-AYT Dil Bilgisi Soru Bankasi | 108 BILGI SARMAL 2024 TYT-AYT Dil Bilgisi Soru Bankasi | %85 | %75 | 0.56 |  |
| 112 2020-2021 BS TYT Tarih Soru Bankasi | 115 2023-2024 BS TYT Tarih Soru Bankasi | %50 | %60 | 0.17 |  |
| 112 2020-2021 BS TYT Tarih Soru Bankasi | 116 BILGI SARMAL 2024 TYT Tarih Soru Bankasi | %42 | %33 | 0.17 |  |
| 115 2023-2024 BS TYT Tarih Soru Bankasi | 116 BILGI SARMAL 2024 TYT Tarih Soru Bankasi | %90 | %44 | 0.70 |  |
| 118 2023-2024 BS TYT Turkce Soru Bankasi | 120 BILGI SARMAL 2024 TYT Turkce Soru Bankasi | %0 | %0 | 0.00 |  |
| 119 BILGI SARMAL 2025 TYT Turkce Video Ders Kitabi | 120 BILGI SARMAL 2024 TYT Turkce Soru Bankasi | %0 | %2 | - |  |
| 124 2022-2023 BS TYT-AYT Geometri Soru Bankasi | 131 2023-2024 BS TYT-AYT Geometri Soru Bankasi | %92 | %75 | 0.62 |  |
| 124 2022-2023 BS TYT-AYT Geometri Soru Bankasi | 142 BS 2024 TYT-AYT Geometri SB | %72 | %75 | 0.44 |  |
| 125 2022-2023 BS AYT Matematik Soru Bankasi | 126 2022-2023 BS TYT Problemler Soru Bankasi | %0 | %0 | - |  |
| 125 2022-2023 BS AYT Matematik Soru Bankasi | 127 2023-2024 BS AYT Matematik Soru Bankasi | %48 | %48 | 0.19 |  |
| 125 2022-2023 BS AYT Matematik Soru Bankasi | 132 2023-2024 BS TYT Matematik Soru Bankasi | %0 | %1 | 0.00 |  |
| 125 2022-2023 BS AYT Matematik Soru Bankasi | 135 BS 2024 AYT Matematik Soru Bankasi | %27 | %26 | 0.00 |  |
| 126 2022-2023 BS TYT Problemler Soru Bankasi | 129 2023-2024 BS TYT Problemler Soru Bankasi | %100 | %100 | 0.69 |  |
| 126 2022-2023 BS TYT Problemler Soru Bankasi | 132 2023-2024 BS TYT Matematik Soru Bankasi | %0 | %0 | - |  |
| 126 2022-2023 BS TYT Problemler Soru Bankasi | 136 BILGI SARMAL 2024 TYT Problemler Soru Bankasi | %69 | %69 | 0.38 |  |
| 127 2023-2024 BS AYT Matematik Soru Bankasi | 134 BS 2024 AYT Logaritma Diziler | %0 | %0 | - |  |
| 127 2023-2024 BS AYT Matematik Soru Bankasi | 135 BS 2024 AYT Matematik Soru Bankasi | %61 | %62 | 0.38 |  |
| 128 2023-2024 BS TYT Problemler Brans DS Yildizlar Yarisiyor | 130 2023-2024 BS TYT Problemler Brans DS Yildizlar Yarisiyor | %100 | %100 | 1.00 |  |
| 129 2023-2024 BS TYT Problemler Soru Bankasi | 132 2023-2024 BS TYT Matematik Soru Bankasi | %0 | %0 | - |  |
| 129 2023-2024 BS TYT Problemler Soru Bankasi | 136 BILGI SARMAL 2024 TYT Problemler Soru Bankasi | %81 | %81 | 0.62 |  |
| 131 2023-2024 BS TYT-AYT Geometri Soru Bankasi | 139 BILGI SARMAL 2025 TYT-AYT Geometri Soru Bankasi | %23 | %26 | 0.00 |  |
| 131 2023-2024 BS TYT-AYT Geometri Soru Bankasi | 142 BS 2024 TYT-AYT Geometri SB | %100 | %100 | 0.81 |  |
| 132 2023-2024 BS TYT Matematik Soru Bankasi | 140 BILGI SARMAL 2025 TYT Matematik Soru Bankasi | %49 | %62 | 0.25 |  |
| 134 BS 2024 AYT Logaritma Diziler | 135 BS 2024 AYT Matematik Soru Bankasi | %0 | %0 | - |  |
| 134 BS 2024 AYT Logaritma Diziler | 137 BILGI SARMAL 2025 AYT Matematik Soru Bankasi | %0 | %0 | - |  |
| 135 BS 2024 AYT Matematik Soru Bankasi | 137 BILGI SARMAL 2025 AYT Matematik Soru Bankasi | %6 | %12 | 0.00 |  |
| 136 BILGI SARMAL 2024 TYT Problemler Soru Bankasi | 140 BILGI SARMAL 2025 TYT Matematik Soru Bankasi | %0 | %0 | - |  |
| 137 BILGI SARMAL 2025 AYT Matematik Soru Bankasi | 138 BILGI SARMAL 2025 AYT Matematik Video Ders Kitabi | %0 | %0 | 0.00 |  |
| 139 BILGI SARMAL 2025 TYT-AYT Geometri Soru Bankasi | 142 BS 2024 TYT-AYT Geometri SB | %29 | %24 | 0.00 |  |
| 140 BILGI SARMAL 2025 TYT Matematik Soru Bankasi | 141 BILGI SARMAL 2025 TYT Matematik Video Ders Kitabi | %0 | %0 | 0.00 |  |
| 143 C1CELL 2024 Problemler SB | 144 C1CELL 2024 TYT-AYT Geometri Soru Bankasi | %0 | %0 | - |  |
| 144 C1CELL 2024 TYT-AYT Geometri Soru Bankasi | 145 C1CELL 2024 TYT Matematik Soru Bankasi | %0 | %2 | - |  |
| 144 C1CELL 2024 TYT-AYT Geometri Soru Bankasi | 146 C1CELL 2025 AYT Matematik Soru Bankasi | %0 | %0 | - |  |
| 149 2023-2024 CAP AYT Matematik Soru Bankasi | 150 CAP 2023 AYT Matematik AL Soru Bankasi | %56 | %51 | 0.44 |  |
| 151 Cap 2024 Anlam Bilgisi Kitabi | 155 CAP 2025 TYT Dil Bilgisi Konu Anlatimli Soru Bankasi | %0 | %1 | - |  |
| 157 CAP 2024 TYT Paragraf Konu Anlatimli Soru Bankasi | 276 2020-2021 CAP Capli Paragraf | %0 | %0 | - |  |
| 158 2020-2021 CAP TYT Tarih Soru Bankasi | 159 2023-2024 CAP TYT Tarih Soru Bankasi | %0 | %0 | 0.00 |  |
| 160 2020-2021 CAP TYT Turkce Soru Bankasi | 161 2023-2024 CAP TYT Turkce Soru Bankasi | %19 | %13 | 0.00 |  |
| 164 Es(Edebiyat Sokagi) 2024 Orta Duzey Paragraf | 168 Es 2024 Baslangic Paragraf | %2 | %3 | - |  |
| 164 Es(Edebiyat Sokagi) 2024 Orta Duzey Paragraf | 170 Es 2024 Paragraf Analizi | %0 | %0 | - |  |
| 164 Es(Edebiyat Sokagi) 2024 Orta Duzey Paragraf | 171 Es 2024 Paragraf Yeterlilik Testi | %1 | %5 | - |  |
| 164 Es(Edebiyat Sokagi) 2024 Orta Duzey Paragraf | 172 Es 2024 Ileri Duzey Paragraf | %1 | %3 | - |  |
| 165 Es 2024 Atasozleri-Deyimler Soru Bankasi | 169 Es 2024 Dil Bilgisi | %32 | %15 | - |  |
| 166 Es 2024 AYT Edebiyat Yeni Nesil Soru Bankasi | 167 Es 2024 AYT Edebiyat Denemeleri | %7 | %9 | - |  |
| 168 Es 2024 Baslangic Paragraf | 170 Es 2024 Paragraf Analizi | %0 | %0 | - |  |
| 168 Es 2024 Baslangic Paragraf | 171 Es 2024 Paragraf Yeterlilik Testi | %4 | %12 | - |  |
| 168 Es 2024 Baslangic Paragraf | 172 Es 2024 Ileri Duzey Paragraf | %0 | %4 | - |  |
| 170 Es 2024 Paragraf Analizi | 171 Es 2024 Paragraf Yeterlilik Testi | %0 | %0 | - |  |
| 170 Es 2024 Paragraf Analizi | 172 Es 2024 Ileri Duzey Paragraf | %0 | %0 | - |  |
| 171 Es 2024 Paragraf Yeterlilik Testi | 172 Es 2024 Ileri Duzey Paragraf | %14 | %16 | - |  |
| 174 (Esen) 2024 Motivasyon Fizik 2 PSB | 188 (Esen) AYT Fizik Soru Bankasi | %0 | %0 | - |  |
| 174 (Esen) 2024 Motivasyon Fizik 2 PSB | 195 (Esen) TYT Fizik Soru Bankasi | %0 | %0 | - |  |
| 174 (Esen) 2024 Motivasyon Fizik 2 PSB | 200 (Esen) 2024 Motivasyon Fizik 1 PSB | %6 | %6 | 0.06 |  |
| 175 (Esen) 2025 APS AYT Fizik SB | 188 (Esen) AYT Fizik Soru Bankasi | %22 | %19 | 0.00 |  |
| 175 (Esen) 2025 APS AYT Fizik SB | 200 (Esen) 2024 Motivasyon Fizik 1 PSB | %0 | %0 | - |  |
| 178 (Esen) 2025 APS TYT Biyoloji SB | 192 (Esen) TYT-AYT Biyoloji Soru Bankasi | %38 | %16 | 0.00 |  |
| 178 (Esen) 2025 APS TYT Biyoloji SB | 199 (Esen) 2024 Motivasyon Biyoloji PSB | %0 | %0 | - |  |
| 179 (Esen) 2025 APS TYT Cografya SB | 194 (Esen) TYT Cografya Soru Bankasi | %39 | %13 | 0.00 | gozle AYNI icerik |
| 180 (Esen) 2025 APS TYT Fizik SB | 195 (Esen) TYT Fizik Soru Bankasi | %37 | %20 | 0.00 |  |
| 180 (Esen) 2025 APS TYT Fizik SB | 200 (Esen) 2024 Motivasyon Fizik 1 PSB | %0 | %0 | - |  |
| 181 (Esen) 2025 APS TYT-AYT Geometri SB | 193 (Esen) TYT-AYT Geometri Soru Bankasi | %20 | %10 | 0.00 |  |
| 182 (Esen) 2025 APS TYT Kimya SB | 196 (Esen) TYT Kimya Soru Bankasi | %11 | %6 | 0.00 |  |
| 182 (Esen) 2025 APS TYT Kimya SB | 201 (Esen) 2024 TYT Kimya PSB (Motivasyon) | %0 | %0 | 0.00 |  |
| 183 (Esen) 2025 APS TYT-AYT Tarih SB | 197 (Esen) TYT Tarih Soru Bankasi | %24 | %20 | 0.00 |  |
| 184 (Esen) 2025 APS TYT Matematik SB | 191 (Esen) TYT Matematik Soru Bankasi | %34 | %12 | 0.00 | gozle AYNI icerik |
| 185 (Esen) 2025 APS TYT Turkce SB | 198 (Esen) TYT Turkce Soru Bankasi | %24 | %17 | 0.00 |  |
| 185 (Esen) 2025 APS TYT Turkce SB | 202 (Esen) TYT Kronograf Soru Bankasi | %2 | %0 | - |  |
| 186 (Esen) 2025 APS AYT Biyoloji SB | 192 (Esen) TYT-AYT Biyoloji Soru Bankasi | %2 | %0 | 0.00 |  |
| 186 (Esen) 2025 APS AYT Biyoloji SB | 199 (Esen) 2024 Motivasyon Biyoloji PSB | %0 | %0 | - |  |
| 187 (Esen) 2025 APS AYT Kimya SB | 189 (Esen) AYT Kimya Soru Bankasi | %1 | %1 | 0.00 |  |
| 188 (Esen) AYT Fizik Soru Bankasi | 200 (Esen) 2024 Motivasyon Fizik 1 PSB | %0 | %0 | - |  |
| 192 (Esen) TYT-AYT Biyoloji Soru Bankasi | 199 (Esen) 2024 Motivasyon Biyoloji PSB | %0 | %0 | - |  |
| 195 (Esen) TYT Fizik Soru Bankasi | 200 (Esen) 2024 Motivasyon Fizik 1 PSB | %0 | %0 | - |  |
| 196 (Esen) TYT Kimya Soru Bankasi | 201 (Esen) 2024 TYT Kimya PSB (Motivasyon) | %0 | %0 | 0.00 |  |
| 198 (Esen) TYT Turkce Soru Bankasi | 202 (Esen) TYT Kronograf Soru Bankasi | %4 | %3 | - |  |
| 205 2019-2020 Full Matematik Geometri Soru Bankasi | 206 2022-2023 FULL TYT-AYT Geometri Soru Bankasi | %1 | %0 | 0.00 |  |
| 207 2022-2023 FULL TYT Matematik Soru Bankasi | 209 2019-2020 FM TYT Matematik Soru Bankasi | %17 | %22 | 0.00 |  |
| 208 2022-2023 FULL AYT Matematik Soru Bankasi | 210 2019-2020 Full Matematik AYT Matematik Soru Bankasi | %3 | %6 | 0.00 |  |
| 214 Mikro Orijinal 2024 AYT 12'li Deneme-1 | 215 Mikro Orijinal 2024 AYT 12'li Deneme-10 | %0 | %0 | - |  |
| 214 Mikro Orijinal 2024 AYT 12'li Deneme-1 | 218 Mikro Orijinal 2024 AYT 12'li Deneme-2 | %0 | %100 | 0.00 |  |
| 226 Mikro Orijinal 2024 AYT Matematik SB | 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | %1 | %1 | - |  |
| 226 Mikro Orijinal 2024 AYT Matematik SB | 252 ORIJINAL 2025 AYT Matematik Turev | %0 | %0 | - |  |
| 226 Mikro Orijinal 2024 AYT Matematik SB | 253 ORIJINAL 2025 AYT Polinom Parabol | %0 | %0 | - |  |
| 226 Mikro Orijinal 2024 AYT Matematik SB | 254 ORIJINAL 2025 AYT Matematik Limit Sureklilik | %0 | %0 | - |  |
| 226 Mikro Orijinal 2024 AYT Matematik SB | 255 ORIJINAL 2025 AYT Logaritma Diziler | %0 | %0 | - |  |
| 226 Mikro Orijinal 2024 AYT Matematik SB | 258 ORIJINAL 2024 AYT Matematik SB | %0 | %0 | 0.00 |  |
| 227 Mikro Orijinal 2024 TYT 12'li Deneme-10 | 230 Mikro Orijinal 2024 TYT 12'li Deneme-2 | %8 | %8 | 0.00 |  |
| 238 MIKRO ORIJINAL 2024 TYT Matematik SB | 239 MIKRO ORIJINAL 2024 Matematik Soru Bankasi | %6 | %0 | 0.00 |  |
| 238 MIKRO ORIJINAL 2024 TYT Matematik SB | 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | %9 | %2 | - |  |
| 238 MIKRO ORIJINAL 2024 TYT Matematik SB | 249 ORIJINAL 2024 TYT Matematik SB | %0 | %0 | 0.00 |  |
| 238 MIKRO ORIJINAL 2024 TYT Matematik SB | 256 ORIJINAL 2025 TYT Matematik Problemler | %0 | %0 | - |  |
| 239 MIKRO ORIJINAL 2024 Matematik Soru Bankasi | 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | %0 | %0 | - |  |
| 239 MIKRO ORIJINAL 2024 Matematik Soru Bankasi | 249 ORIJINAL 2024 TYT Matematik SB | %0 | %0 | 0.00 |  |
| 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | 241 MIKRO ORIJINAL 2024 TYT-AYT Geometri SB | %69 | %81 | 0.56 | gozle AYNI icerik |
| 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | 242 Mikro Orijinal 2024 TYT-AYT Geometri Soru Bankasi | %0 | %0 | 0.00 |  |
| 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | 245 Orijinal 2024 AYT Trigonometri | %0 | %0 | - |  |
| 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | 247 Orijinal 2024 Analitik Geometri | %0 | %2 | - |  |
| 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | 248 Orijinal 2024 TYT-AYT Geometri SB | %0 | %0 | 0.00 |  |
| 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | 251 ORIJINAL 2025 Analitik Geometri | %0 | %1 | - |  |
| 240 MIKRO ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | 257 ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | %0 | %0 | 0.00 |  |
| 241 MIKRO ORIJINAL 2024 TYT-AYT Geometri SB | 242 Mikro Orijinal 2024 TYT-AYT Geometri Soru Bankasi | %0 | %0 | 0.00 |  |
| 241 MIKRO ORIJINAL 2024 TYT-AYT Geometri SB | 245 Orijinal 2024 AYT Trigonometri | %0 | %0 | - |  |
| 241 MIKRO ORIJINAL 2024 TYT-AYT Geometri SB | 247 Orijinal 2024 Analitik Geometri | %0 | %2 | - |  |
| 241 MIKRO ORIJINAL 2024 TYT-AYT Geometri SB | 248 Orijinal 2024 TYT-AYT Geometri SB | %0 | %0 | 0.00 |  |
| 241 MIKRO ORIJINAL 2024 TYT-AYT Geometri SB | 257 ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | %0 | %0 | 0.00 |  |
| 242 Mikro Orijinal 2024 TYT-AYT Geometri Soru Bankasi | 248 Orijinal 2024 TYT-AYT Geometri SB | %0 | %0 | 0.00 |  |
| 243 NEOFIZIK 2025 AYT Fizik Soru Bankasi | 244 NEOFIZIK 2024 TYT Soru Bankasi | %0 | %0 | - |  |
| 245 Orijinal 2024 AYT Trigonometri | 248 Orijinal 2024 TYT-AYT Geometri SB | %0 | %0 | - |  |
| 245 Orijinal 2024 AYT Trigonometri | 257 ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | %0 | %0 | - |  |
| 247 Orijinal 2024 Analitik Geometri | 248 Orijinal 2024 TYT-AYT Geometri SB | %1 | %2 | - |  |
| 247 Orijinal 2024 Analitik Geometri | 251 ORIJINAL 2025 Analitik Geometri | %44 | %31 | 0.06 | gozle AYNI icerik |
| 247 Orijinal 2024 Analitik Geometri | 257 ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | %1 | %2 | - |  |
| 248 Orijinal 2024 TYT-AYT Geometri SB | 251 ORIJINAL 2025 Analitik Geometri | %1 | %1 | - |  |
| 248 Orijinal 2024 TYT-AYT Geometri SB | 257 ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | %69 | %69 | 0.38 | gozle AYNI icerik |
| 251 ORIJINAL 2025 Analitik Geometri | 257 ORIJINAL 2025 TYT-AYT Geometri Soru Bankasi | %1 | %1 | - |  |
| 252 ORIJINAL 2025 AYT Matematik Turev | 258 ORIJINAL 2024 AYT Matematik SB | %0 | %0 | - |  |
| 253 ORIJINAL 2025 AYT Polinom Parabol | 258 ORIJINAL 2024 AYT Matematik SB | %0 | %0 | - |  |
| 254 ORIJINAL 2025 AYT Matematik Limit Sureklilik | 258 ORIJINAL 2024 AYT Matematik SB | %0 | %0 | - |  |
| 255 ORIJINAL 2025 AYT Logaritma Diziler | 258 ORIJINAL 2024 AYT Matematik SB | %0 | %0 | - |  |
| 259 2020-2021 PES Problemler Kampi | 261 2020-2021 PES Profesyonel Anlam Sorulari - Profesyonel Problem Sorulari | %0 | %0 | - |  |
| 260 2020-2021 PES Kurgulu Paragraf | 262 2020-2021 PES Kurgulu Paragraf Soru Bankasi | %93 | %93 | 0.87 |  |
| 260 2020-2021 PES Kurgulu Paragraf | 265 2020-2021 PES TYT-AYT Paragraf Soru Bankasi | %4 | %1 | 0.00 | gozle AYNI icerik |
| 261 2020-2021 PES Profesyonel Anlam Sorulari - Profesyonel Problem Sorulari | 263 2020-2021 PES Sozcukte Cumlede Anlam Kampi | %0 | %0 | - |  |
| 262 2020-2021 PES Kurgulu Paragraf Soru Bankasi | 265 2020-2021 PES TYT-AYT Paragraf Soru Bankasi | %3 | %1 | 0.00 |  |
| 266 SURE 2023 AYT Edebiyat Soru Bankasi | 268 SURE 2025 Edebiyatin Suresi | %88 | %88 | 0.88 | gozle AYNI icerik |
| 269 SURE 2025 Paragrafin Suresi | 270 2023-2024 SURE TYT-AYT Paragraf Soru Bankasi | %100 | %100 | 1.00 |  |
| 269 SURE 2025 Paragrafin Suresi | 273 SURE 2023 TYT Paragraf Gunlukleri | %6 | %2 | 0.00 | gozle FARKLI |
| 269 SURE 2025 Paragrafin Suresi | 274 2023-2024 SURE TYT Turkce Soru Bankasi | %6 | %3 | - |  |
| 270 2023-2024 SURE TYT-AYT Paragraf Soru Bankasi | 274 2023-2024 SURE TYT Turkce Soru Bankasi | %2 | %4 | - |  |

## 9. Yeniden uretim

Olcum betikleri gecici calisma dosyalariydi (repo disi); bu rapordaki her sayi `zkitap_kitap_durumu_olcum.json` icinde klasor adlariyla durur: sekme basliklari, kalite sayimlari, cift olculeri. Yontem bolum 3'te; ayni olculer bu tariflerle yeniden kosulabilir.

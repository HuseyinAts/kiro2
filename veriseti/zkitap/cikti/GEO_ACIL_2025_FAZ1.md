# ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi -- FAZ 1-3 (veri hatti)

Kaynak: `veriseti/zkitap/screenshots/ACIL-TYT-AYT-Geometri Soru Bankasi`
(okuyucu sekmesi "ACIL - 2025 - TYT - AYT - Geometri Soru Bankasi"; 400 PNG,
392 soru sayfasi = dosya 7-398, basili sayfa = dosya - 4). Faz 0 fisi:
`GEO_ACIL_2025_KURS_KESIF.md`. Sahip karari (bu tur): **mevcut yakalamayla
devam**; okuyucu diski renge gore beyazlatilir, ortulen satirlar isaretlenir.

Hicbir soru cozulmedi. Cevaplar kitabin kendi basili seridinden okundu.

## 0. Sonuc tablosu

| kalem | deger |
|---|---|
| soru | **1948** |
| birim (serit numarasinin 1'den basladigi dizi) | **429** = 318 konu ogrenme + 111 test |
| konu (sayfa basligi) / alt konu (sari kutu) | **33 / 315** |
| cevap: uc okuma ayni / iki okuma + piksel B-D / goz | 1915 / 31 / 2 |
| harf dagilimi | A 266, B 361, C 575, D 460, E 286 |
| basili numara == birim ici sira (transkripsiyon kapisi) | **1948 / 1948** |
| okuyucu diski ortme suphesi (piksel) | 82 soru |
| okuyucunun kaynak kusuru notu | 83 soru |
| hic okunamayan sik (`[okunamadi]`) | 4 soru (4'u de ortme olcumunde; hicbiri anahtar sikki degil) |
| sekilli / gorsel sikli | 1692 / 10 |
| sekil ikizi (ayni metin + sikler, farkli sekil, farkli anahtar) | 1 cift (d8 sol #2 / sag #5) |

## 1. Cevap anahtari (sayfa alti serit)

Her soru sayfasinin altinda sutun basina yarim serit var: `N.X` girdileri,
alt bolum degisiminde `/` ayraci. Serit sirasi = sutundaki okuma sirasi.

* **Uc bagimsiz okuma.** A ve B: 4x Lanczos montaj, 24 satir/goruntu, farkli
  okuyucular. C: 6x kontrast montaj. 1948 girdinin 1915'i uc okumada ayni.
* **A != B (2 girdi):** 78R 1. ve 215L 2.; ikisi de goz ile C (78R'de ust
  kenari bir cizgi ortuyor).
* **A = B, C farkli (31 girdi):** hepsi B/D. Bu kitapta B'nin orta cubugu
  soluk (gri ~210) basiliyor; 6x kontrast okuma onu D gordu. Olcum: harf
  glifinin orta satirlarinda sol ve sag kenar arasindaki en acik piksel.
  Segmentasyonun kapsadigi 628 B/D girdisinde D glifi 254-255, tartismali
  31 girdi 209-211 (B'nin soluk cubuk kumesi). En-yakin-komsu kontrast
  buyutmesiyle 31'i de goz ile B. Segmentasyonun kapsamadigi 130 yarim-serit
  (B ya da D iceren) ayrica goz ile tarandi: okumayla celiski yok.
* **Kapi 1:** sutun basina serit girdisi == sayfadaki basili soru numarasi
  capasi (784/784 sutun).
* **Kapi 2:** okuma sirasinda her numara ya oncekinin +1'i ya da 1 (429
  sifirlama, baska kopma yok).

Dosyalar: `acil_2025_geometri_cevap_anahtari.json`; ham uc okuma
`acil_2025_geometri_serit_okumalari.json` (test anahtari bu dosyadan
birebir yeniden uretir).

## 2. Konu agaci ve birimler (icindekiler YOK)

Icindekiler sayfasi yakalamada yok (Faz 0 K0.7). Agac kitabin kendi
basliklarindan kuruldu; hicbir ad uydurulmadi.

* **Sayfa basliklari:** 392 sayfanin ust bandi (kirmizi konu adi + bant
  etiketi + test etiketi) iki bagimsiz okuyucuyla (duz / ters sira) okundu:
  391/392 ayni. Fark d139: kitabin kendi basim hatasi "Yeni Nesil Test Test"
  (goz ile). Konu adi YALNIZ buyuk (acilis) basliklarda degisiyor ve hicbir
  konu geri donmuyor -> 33 konu.
* **Sari alt baslik kutulari:** renk (255,247,163) maskesiyle 331 kutu
  (22'si iki sutunu kaplayan tam genislik). Iki bagimsiz okuma: 330/331 ayni
  (fark K019'da bir virgul). 318 kutu tam bir `no=1` girdisinin hemen
  ustunde (yeni birim); 13 kutu onceki birimin DEVAMI (sayfa basinda ayni
  baslik tekrar basilmis; 12'si birebir, 1'i yalniz buyuk/kucuk harf farkli).
* **Test birimleri:** kalan 111 sifirlamanin tamami buyuk baslikli bir
  'Konu Uygulama' sayfasinin ilk sorusu (Karma Test N / Yeni Nesil Test /
  Genel Test N) ve her buyuk uygulama basligi tam bir test baslatiyor.
* Kitap uc alt basligi yeniden aciyor (d306 sag, d309 sol, d328 sag): ayni
  adli iki birim ayni alt konu dugumunu paylasir.
* **Bolum (ust grup) duzeyi kitapta gorunmuyor; ACILMADI.** Konu kok+1, alt
  konu kok+2 (0041). Konu ogrenme sorulari alt konuya, test sorulari konuya
  baglanir. Adlar ASCII katlanir (diger GEO agaclari gibi), basili hali
  `ad_basili` alaninda durur.

Dosyalar: `acil_2025_geometri_konu_haritasi.json`,
`acil_2025_geometri_birim_haritasi.json`, `acil_2025_geometri_sari_kutular.json`,
`acil_2025_geometri_baslik_okumalari.json` (H1/H2 + K1/K2 ham okumalar),
`backend/alembic/versions/0041_acil25_geo_konu_agaci.py` (haritadan uretildi).

## 3. Kirpim kutulari (capa = basili soru numarasi)

Bu kitapta okuyucu simgeleri soruyla 1:1 DEGIL (sari kutu ve sekil yaninda
da simge var). Kutular sayfadaki basili numara blob'larindan turetildi
(`acil_2025_geometri_numara_taramasi.json`, 1948 capa).

* **Yatay:** numara x'i tek sayfada sol 45 / sag 372, cift sayfada sol 61 /
  sag 388 (392 sayfada en fazla 1 px sapma). Sutun arasindaki dikey ACIL
  MATEMATIK logosu tek sayfada x 353-363, cift sayfada x 370-380 (+ x 375
  ara cizgi) olculdu; sinirlar bunun disinda: tek sol [41,351] sag
  [368,684], cift sol [57,368] sag [384,700].
* **Dikey:** kutu ustu, numaradan yukari ilk 10 satirlik bos bandin alt ucu
  (seklin tepe etiketi numaranin ustunde basili olabiliyor; ilk surumde 8
  kirpimda kesildi, okuyucular bildirdi -> duzeltildi, 285 kutu numaranin
  ustune uzadi). Altu sonraki kutunun ustu; arada sari kutu varsa onun
  ustu; sutun sonunda y 906 (serit bandi 910'da basliyor).
* **Kapilar:** kart ici, cakisma yok, sonraki numara ustteki kutuda degil,
  numara kendi kutusunda, seride sizinti yok.

## 4. Okuyucu diski: beyazlatma ve ortme olcumu

* Beyazlatma: bilinen simge konumunun 26 px yaricapli dairesinde yalniz
  okuyucu renkleri (lila disk, mor glif, acik gri golge, mor-lila kenar
  karisimlari; diskin sol yarisinda ayrica notr gri >= 185). Kitabin siyah
  metni ve kirmizi/mavi cizimleri dokunulmaz. Ilk surumde sol sutun
  kirpimlarinin sag kenarinda sag sutun diskinin anti-alias kalintisi
  kaliyordu (d7, d18/d19 olculdu) -> iki kural eklendi.
* **Disk opak; altindaki icerik goruntude YOK.** Ortme olcumu (beyazlatmadan
  once): diskin disindaki halkada (yaricap 15-19, sagdaki 90 derece haric)
  koyu kitap murekkebi; halka pikselleri tek tek kirpimlara dagitilir (medyan
  konum d35'te isareti sutun arasina dusurup kaybetmisti). 82 soru.
* Tipik ortme: sag sutun diski, sol sutunda E sikkinin son rakaminin
  uzerine dusuyor. 4 soruda sikkin kendisi hic okunamadi -> `[okunamadi]`
  isareti (okuyucu bos birakti + kaynak kusuru yazdi). Dordu de piksel
  olcumunde isaretli (iki bagimsiz kanal); hicbiri anahtarin dogru sikki
  degil.

Dosya: `acil_2025_geometri_ortme_olcumu.json` (kirp aracinin ciktisi).

## 5. Transkripsiyon

* Kirpimlar 2x Lanczos buyutulup 32 gruba (birim sinirina hizali, ~60 soru)
  bolundu; her grubu ayri bir okuyucu okudu. Pilot (grup 32, 1x) eksi
  isaretini ve kesir cizgisini 'soluk' isaretledi -> 2x.
* Okuyucuya birim ici sira, soru sayisi ya da anahtar verilmedi. Kapilar:
  her kirpim tam bir kez; **basili numara == birim ici sira (1948/1948)**
  -- bu, kutu capalarinin dogru blob'a oturdugunu ayrica dogrular; bes sik
  dolu; toplam 1948.
* **Duzeltme okumasi:** ilk 8 grup kutu ustu kurali duzeltilmeden once
  okunmustu. O gruplarda kaynak kusuru isaretli 38 soru yeni kirpimdan AYRI
  bir okuyucuyla yeniden okundu ve yerine gecti. 32/38 birebir ayni; farkin
  3'u, ilk okuyucunun diskin altinda yari gorunen rakami TAHMIN etmesi
  (ikinci okuyucu bos birakti -> `[okunamadi]`).
* Okuyucular kitabin basim hatalarini oldugu gibi aktardi ve not dustu
  (ornek: ayni deger iki sikta, kac yerine eksik harfli yazim, 'veriln', iki sekle de 'Sekil 1').

Dosya: `acil_2025_geometri_metin.json`.

## 6. Ithal (PASIF) ve bilinen borc

`backend/scripts/kitap/acil25_geo_ithal.py` -- `kaynak_sozlesmesi.py`'de
`ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi` / `ACIL_GEO_2025`. Kuru kosum:
yapisal kapi + on kontrol temiz; 348 dugumun (33 + 315) hepsine en az bir
soru baglaniyor.

**Yerel DB (23 Eyl 2026):** 0041 kostu (348 dugum eklendi). `--yaz`:

| olcum | deger |
|---|---|
| DB'de zaten var (baska kaynak, ayni soru_hash) | **189** -- hepsi ACIL 2023-2024 |
| yeni yazilan | **1759** (is_active 0, kapidan gecen 0) |
| soru tasiyan GEO-ACL25 dugumu | 346 / 348 |

**189 ortak soru ayni sorudur:** ayni soru_hash (metin + bes sik), kitabin
anahtari 2023-2024 satirinin cevabiyla 189/189 ayni, sekil bayragi 189/189
ayni. Faz 0'daki '%0 ortaklik' sayfa/blok olcusuydu; soru duzeyinde 2025
KURS'un ~%9,7'si 2023-2024 baskisindan birebir alinmis. `ayristir` bunlara
dokunmadi (2023-2024 satirlari ve konu baglari oldugu gibi); 2 alt konu
dugumunun sorularinin tamami bu ortak kumede oldugu icin 346/348.

Gorseller `d-dataset/output/crops/ACILGEO_2025/` altina uretildi
(`acil25_geo_kirp.py --cikti ... --rapor ""`), `/static/crops` bunu servis eder.

* **Sekil ikizi:** d8 sol #2 ve sag #5 ayni govde + ayni siklar, farkli
  sekil, farkli anahtar (C / D). `soru_hash` formulu ortak altyapi,
  degistirilmedi; yalniz bu cift icin id = uuid5(hash | sekil | kirpim).
  `uq_qb_soru_hash_active` yuzunden ikizden yalniz biri ayni anda aktif
  olabilir -- aktiflestirme karari sirasinda cozulmeli.
* TAM ikinci transkripsiyon yapilmadi (38 soruluk duzeltme okumasi disinda).
* Cozumler kitapta yok; `explanation` bos.
* Sinav turu soru duzeyinde olculmedi; 'AYT' + `sinav_turu_kaynagi`.
* 82 ortme / 83 kaynak kusuru / 4 okunamayan sik bayrakla gorunur kalir.

## 7. Yeniden uretim

    python backend/scripts/kitap/acil25_geo_kutu.py --yaz
    python backend/scripts/kitap/acil25_geo_kirp.py            # kirpim + ortme olcumu
    python backend/scripts/kitap/acil25_geo_metin_harness.py hazirla | topla | kapi
    python backend/scripts/kitap/acil25_geo_ithal.py --kuru

Testler: `backend/tests/e2e/test_acil25_geo_veri.py` (veri capalari),
`backend/tests/e2e/test_acil25geo_ithal.py` (ithal kapilari + mutasyon).

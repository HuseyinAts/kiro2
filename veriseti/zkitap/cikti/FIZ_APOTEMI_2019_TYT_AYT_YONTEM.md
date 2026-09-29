# 2019-2020 Apotemi TYT-AYT Fizik Soru Bankasi -- yontem (APO19FZ)

Tarih: 29 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/apo19fz.py`; Apotemi 'konu testi' duzeni; kesif
`kesif.py --cikti apo19fz`). Kaynak: FERNUS 1920x1080, 448 PNG (goruntu
PDF'i), kart (589,43)-(1331,1022); basili sayfa = dosya.

## 1. Kitap yapisi

* Icindekiler dosya 6-7: 4 bolum (acilis 9, 143, 247, 345), 36 kalin konu
  basligi (dort 'Tekrar Testi' dahil). Konu = test bandindaki yesil BUYUK
  HARFLI ad; iki okuma ile icindekiler adlari birebir (BANT_KONU_KAPISI).
  'NEWTON'UN' kesme isareti bir okumada U+2019, gozle ayirt edilemedi ->
  ASCII `'` (anlam farki yok).
* Test sayfalari 11-142, 145-246, 249-344, 347-448; 10 / 144 / 248 / 346
  baska kitaplarin reklam sayfasi (simgeli ornek sorular) -> kapak. Her test
  iki sayfa: 216 test, 2180 soru.
* Sinav etiketi kitapta basili DEGIL: yeni genel kanca `SINAV_KONU` (ithal
  `sinav_sinif`) konu duzeyinde MEB 2018 unite sinifi: TYT 9-10 (1211),
  AYT 11-12 (969); karma tekrar testleri (2. ve 3. bolum) AYT.

## 2. Cevap anahtari

* Cift sayfanin altliginda soluk sari (240,236,189) kutularda gri
  '1-D 2-E ...' (c5_serit.py: 216 cift sayfa); profil `anahtar_bolgesi`
  kutu kosulari (>= 18 px), noktalar ve sayfa no disarida.
* Iki okuma A / B (4+4): A == B 2180 hucre, bant farki 0.
* Glif ucuncu kanal (APO19MT `hucre_harf_bloblari`, esik 190): 2180/2180
  uyum, goz teyidi yok. Harf A 434, B 444, C 454, D 452, E 396. Soru
  cozulmedi.

## 3. Capa ve kirpim

* Simge L 74 / R 361, numara kirmizi (NUMARA_MASKELERI). Dikey APOTEMI
  sekmesinin uzerindeki simge numarasizdir. EK_CAPA 5: s186 R 11, s216 L 5
  (simge seklin altina kaymis), s125 R 6, s307 R 4 ve 5 (simge konmamis;
  anahtar hucresi capadan fazla, gozle).
* Altlik: gri cizgi y ~879 koyu esigin ustunde -> `SAYFA_ALTLIGI_Y` 878.
  Serit altlikta -> yeni genel kanca `SERIT_ALTLIKTA` (kutu._alt_sinir
  seridin ustu yerine SAYFA_ALTI'ni gecmez; yoksa sol sutunun son kutusu
  sari sayfa no blokunu aliyordu, kirp kesik 216).
* s307 R 4: onceki E sikki ile numara arasi 9 bos satir -> KUTU_UST_KESIN.
* s88 L 5: tablo metni sutun sinirina 1 px kala bitiyor (sekme 361'den) ->
  yeni genel kanca `KENAR_GOZ_ONAY` (kirp.goz_onayi_ayir kenar icin; kirpim
  gozle tam).
* 2180 kutu, artik 0; kirp kenar 0 (1 goz onayli), KESIK 0; ortme 249 soru.

## 4. Metin

* 34 grup, iki bagimsiz okuma (GORUNMEYEN ISARET kurali bastan talimatta).
  455 fark 20 hakemle: okuma_1 120, okuma_2 63, ikisi 19, yok 253. Farklarin
  cogu sekil etiketi secimi (hakem talimatina 'Sekil etiketleri' kurali).
* Gorunen `[??]` 46 soru (pikselde isaret yok) -> beta disi. Ortak oncul yok.

## 5. Mukerrer, ithal, beta

* DB 6807 karsilastirilan satir; aday 0, ayni hash 0; eski hat yok.
* Kitap ici ayni hash 2 cift (T185_08/09, T188_05/06): ayni metin + gorsel
  siklar, farkli sekil -> `sekil_ikizi` (ayri id). uq_qb_soru_hash_active
  yuzunden cift basina yalniz en kucuk id acilir: beta sablonu ve beta_olc
  'kitap ici ayni soru_hash' kosulu (yeni, genel).
* 0119 agac (FIZ-APO19FZ: 4 bolum, 36 konu), ithal 2180 PASIF, 0120 eski hat
  (0), 0121 toplu beta 2132/2180 (dislanan 46 `[??]` + 2 ikiz).
  Round-trip (0118 <-> 0121) temiz.

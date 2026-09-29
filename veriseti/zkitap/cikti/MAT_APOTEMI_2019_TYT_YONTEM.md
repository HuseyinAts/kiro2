# 2019-2020 APOTEMI TYT Matematik Soru Bankasi -- yontem (APO19MT)

Tarih: 29 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (profil
`kitap_hat/profiller/apo19mt.py`; YENI SERI: Apotemi 'deneme konseptli'
duzeni). Kaynak: FERNUS 1920x1080, 324 PNG (goruntu PDF'i, metin katmani
yok), kart (589,43)-(1331,1022).

## 1. Kitap yapisi

* 11 bolum; bolum acilisi cift sayfa (dosya 8, 40, 58, 88, 120, 140, 156,
  226, 246, 266, 296: 'BOLUM N' + konu listesi). Bolum = konu (MAT-APO19MT:
  11 bolum, 11 konu). Sayfa turu: kapak 40, konu 1, test 283.
* Her bolum 'Deneme - N' testlerinden olusur: 122 test, 1382 soru. Testin
  ilk sayfasinda siyah kronometre kutusu (c4_saat.py) -> BAS_SAYFALARI 122.
* Yakalama kusurlari (gozle): dosya 176 dosya 175'in kopyasi; Deneme 23
  (test 81) sorulari 5-8'in sayfasi sette YOK. `KOPYA_SAYFALAR` ve yeni
  genel kanca `YAKALANMAYAN_SORU {81: (5,6,7,8)}` (ortak.yakalanan: anahtar
  hucresi var, soru yok -> capa eslemesi kalan hucrelerle). 322-324 dosya
  321'in kopyasi.

## 2. Cevap anahtari (kitap sonu tablo)

* Sayfalarda cevap seridi YOK. Anahtar dosya 316-321'de tablo:
  'DENEME - N  1-D 2-A ...' satirlari. Yeni genel kanca `ANAHTAR_HARICI
  {test: [(dosya, [y0,y1,x0,x1])]}` (anahtar.anahtar_parcalari; hazirla ve
  glif ikisi de kullanir); tarama.testleri_bul seritsiz test sayfasini bu
  durumda kabul eder (serit_sart=False). Satir kutulari c4_anahtar_satir.py;
  bolum basina satir sayisi kronometre sayisiyla ayni.
* Iki okuma A / B (4+4 okuyucu): A == B 1386 hucre (1382 + yakalanmayan 4).
* Glif ucuncu kanal: '1-D' tiresi harfe antialias ile yapisiyor, genel blob
  bolutlemesi calismadi -> profil `harf_bloblari` kancasi (hucre basina son
  ust-murekkep kolon grubu; anahtar._harf_bloblari profile devreder). 1386
  hucre, uyum 1380; 6 uyumsuz hucre gozle okuma harfi: T041#9=C, T067#10=D,
  T068#9=D, T089#10=D, T096#4=D, T101#10=D. Harf A 128, B 282, C 346,
  D 403, E 223. Soru cozulmedi; tek cevap kaynagi basili anahtar.

## 3. Capa ve kirpim

* Okuyucu simgesi numaranin solunda ayni satirda: L 72 / R 362 (iki
  parite), numara kirmizi, dx 18-40. Sayfa 216 R: `EK_CAPA`.
* Sayfa kenar cizgileri (x 30 / 710) ve dikey 'APOTEMI' sekmesi (x 361-380)
  sutun disinda: SUTUNLAR L 33-361, R 381-707. Ust bant murekkebi
  UST_BANT 98; SAYFA_ALTI 884.
* Seritsiz duzende sayfa altligi (sayfa no kutusu, y 887-907) alt sinir
  taramasina girip yanlis 'kesik' veriyordu -> yeni genel kanca
  `SAYFA_ALTLIGI_Y` (kutu.alt_sinir_alti altlik_y: tarama orada durur;
  altligin USTUNDEKI kesik yine yakalanir, birim test).
* 1382 kutu, artik 0; kirp kenar 0, KESIK 0; ortme 231 soru.

## 4. Metin

* 22 grup (GRUP_SORU 60), iki bagimsiz okuma; 247 fark 16 hakemle.
* GORUNMEYEN ISARET: ekran goruntusunde bazi eksi / arti isaretleri
  basilmamis ya da cok soluk (min piksel 244-253). Okuyucular ilk 8 grupta
  isareti baglamdan tahmin etmisti. Kural talimata eklendi (gorunmeyen
  isaret `[??]`, asla tahmin yok) ve gruplar 1-8 icin piksel son-gecisi
  kosuldu (6 ajan, 237 aday): 41 soruda 34 govde + 32 sik duzeltmesi ve
  41 `kaynak_kusuru` notu (`_c4_ak/ek_duzeltme.json`, duzeltme-yaz
  --hakem 16). Sinirda (min 244-245) izler basildigi gibi birakildi.
* Gorunen alanda `[??]` 159 soru -> beta disi. Ortak oncul yok.

## 5. Mukerrer, ithal, beta

* DB 12275 karsilastirilan satir; 16 aday, GUCLU 6; ayni hash 0. Cevap farki
  icerik 4 soru (T024_03, T042_12, T046_03, T049_15): hepsi zayif aday
  (govde 3-gram 0.75-0.81, farkli sayilar / siklar) -> ayni soru degil;
  basili anahtar degismez.
* Eski hat 9 satir: modern karsiligi olan 6'si 0117 ile pasif, 3 aktif.
* 0116 agac (MAT-APO19MT: 11 bolum, 11 konu), ithal 1382 PASIF, 0117 eski
  hat (6 pasif), 0118 toplu beta 1223/1382 (dislanan 159 = `[??]`).
  Round-trip (0115 <-> 0118) temiz.

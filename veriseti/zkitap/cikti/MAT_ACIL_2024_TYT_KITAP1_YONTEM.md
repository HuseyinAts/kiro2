# 2024 ACIL TYT Matematik Geometri Kitap-1 -- yontem (ACL24MG)

Tarih: 28 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (ucuncu
kitap, ilk MOZ Akademi duzeni; profil `kitap_hat/profiller/acl24mg.py`).
Kaynak: FERNUS 1920x1080 ekran goruntusu, 208 PNG, kart (589,43)-(1331,1022);
basili sayfa = dosya. Icerik TYT matematik (sayilar .. oran-oranti).

## 1. Kitap yapisi

* 9 renk bolumu (Sayilar, Rasyonel Sayi, Birinci Dereceden Denklemler, Basit
  Esitsizlik, Mutlak Deger, Uslu, Koklu, Carpanlara Ayirma, Oran-Oranti).
  Konu anlatim sayfalari halka icinde numarali cozumlu ORNEK (cogu acik
  uclu, cevap seridi sayisal/metin) -- kapsam DISI.
* Test sayfasi = ust bantta 'KONU TESTLERI' sekmesi. Sayfa turu kancasi bu
  sekme metninin koyu piksel kapsamini olcer (cift sayfa x 66-141, tek
  sayfa x 600-675, satir 37-46): 92 test, 106 konu, 10 kapak. Ayni satirda
  metni olan Mutlak Deger konu sayfalari (119-127) x kapsamiyla ayrildi.
  Okuyucu simgesi x konumu tek basina yetmedi (s96-97, 114, 201-204 test
  sayfalarinda simge 5-15 px kayik).
* Her test TEK sayfa (92 test), sorular 1..N.

## 2. Cevap anahtari (sayfa alti tek satir serit)

* Serit: iki ince yatay cizgi; alt cizgi y 905 (91 sayfada ust cizgi 889/890,
  s162'de ust cizgi 229 gri -- tespit alt cizgiden, ust = alt - 16).
* Okuma A (ileri, 2 okuyucu) ve B (geri, 2 okuyucu), bagimsiz: 505/505 hucre
  ayni. Bant: konu adi 9 testte ayirac bicimi farkli ('/' ile / bosluk ile,
  ayni metin) -- A bicimine esitlendi; test_no ayni.
* Glif ucuncu kanali: 431 hucre, LOO 430 uyum; 1 uyumsuz (T076#3 B) 5x
  gozle teyit. 12 test (74 hucre) glif kapsami disi, 5x gozle okundu --
  okumayla ayni. Harf dagilimi A 60, B 99, C 139, D 134, E 73. Hicbir soru
  cozulmedi.

## 3. Capa ve kirpim

* Capa: okuyucu simgesi + MAVI basili numara (64,96,160); tarama.py'ye
  profil kancasi `numara_maskesi` eklendi (varsayilan kirmizi). Numara
  simgeye gore dx 12-22, dy 12-21 (simge titremesi).
* Orta ayrac: dikey cizgi + 'MOZ AKADEMI' dikey harfleri; sag sutun simgesi
  ayracin ustunde. Sutunlar: cift L 40-368 / R 390-700, tek L 24-352 /
  R 372-684. Ust sinir 67 (bant alti), alt 885 ya da serit - 4.
* kirp.py: okuyucu diski beyazlatilirken mavi numaranin kenar yumusatma
  pikselleri 'mor' kuralina giriyordu (ilk kirpimda T002_05 / T089_04
  numaralari yarim) -- profil `numara_maskesi` pikselleri artik korunur
  (gozle dogrulandi). Kirmizi numarali kitaplar etkilenmez.
* Kapilar: 505 kutu, artik murekkep 0, kenar 0; ortme 34 soru.

## 4. Metin

* 10 grup, iki bagimsiz okuma tek dagitimda. 460 soru normalize ayni; 45
  fark 4 hakemle kirpimdan: okuma_2 23, okuma_1 11, ikisi 1, yok 10.
* Gorunen `[??]` 2 soru; tahmin yazilmadi.

## 5. Mukerrer ve eski hat

* DB 20162 aday satir; 37 aday, 16 GUCLU. 7 soru 2020-2021 (6) / 2019-2020
  (1) ACIL TYT Matematik Soru Bankasi'nda ayni soru_hash ile var -> ayni id,
  ithal yazmadi.
* Eski hat '2024-ACIL TYT Matematik Geometri Kitap-1': 12 satir aktif; 7'sinin
  modern karsiligi var -> 0084 ile pasif; 5'i aktif kaldi.

## 6. Ithal ve beta

* 0083 agac (MAT-ACL24MG: 9 bolum + 17 konu), ithal 498 yeni satir PASIF,
  0085 toplu beta onayi 495/498 (2 gorunen `[??]`, 1 sik okunamadi
  disarida). Round-trip (0082 <-> 0085) temiz.
* exam_type TYT, subject MATEMATIK.

## 7. Kesik kirpim duzeltmesi (28 Eyl 2026, 0089)

* `kitap_hat/kirp.py`'ye eklenen KESIK kapisi (beyazlatilmis kutunun ust/alt
  2 px seridinde koyu piksel) birlesmis kitaplarda yeniden kosuldu: bu kitapta
  3 kirpim alt kenarda kesik (T012_03 alt 57 px, T048_04 46, T053_03 36);
  `kutu.py` alt-sinir-alti taramasi 4. sayfayi ekledi (s183L y889, 22 px).
* Neden: SAYFA_ALTI 885; sol sutun (seritle ortusmez) metni serit hizasina
  iniyor -- en alt murekkep s29 889, s104 886, s183 895; diger sayfalarda
  <= 885. Serit alt cizgisi 905. SAYFA_ALTI 898; kutu 0 ihlal, kirp kenar 0
  kesik 0; kirpim kutulari ve ortme olcumu yeniden yazildi.
* Gozle (yeni kirpim): T012_03 D/E, T048_04 E, T053_03 D/E onceki okumayla
  AYNI (ust yarilari dogru okunmustu; kesik notu kalkti). T081_02'de siklar
  kirpimda hic yoktu, bes sik `[okunamadi]` idi (beta DISI): A) 7  B) 8  C) 9
  D) 10  E) 11. Sik metni degisince soru_hash / id degisir -> 0089 yeni satir
  ekler (ithal formulu, konu eski satirdan), eski satir pasif kalir ve
  `kesik_duzeltme_yerine` ile yeni id'yi tasir; yeni satir 0085 kapisindan
  gecer (beta 496/499). Round-trip (0088 <-> 0089) temiz. Soru cozulmedi.

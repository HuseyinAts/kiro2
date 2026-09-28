# 2022-2023 ACIL Kati Cisimler -- yontem (ACL23KC)

Tarih: 28 Eyl 2026. Hat: ortak `backend/scripts/kitap/kitap_hat/` (ikinci
kitap; profil `kitap_hat/profiller/acl23kc.py`, sayfa turu kancasi ve sabit
kaliplari ACL23AG profilinden). Kaynak: FERNUS 1920x1080 ekran goruntusu,
160 PNG, kart (589,43)-(1331,1022). Cekim basili s10'dan basliyor: basili
sayfa = dosya + 9 (`SAYFA_OFSETI`; ithal on kontrolu bunu dogrular).

## 1. Kitap yapisi (kontak sayfasi + olcum)

* 'Konu Anlatimli Soru Fasikulu', tek bolum KATI CISIMLER, 6 konu: Dik
  Prizmalar (test bandi dosya 10), Kup (41), Silindir (63), Piramit (87),
  Koni (112), Kure (131). Konu anlatimi ORNEK / COZUM kapsam DISI.
* Sayfa turu (ACL23AG kancasi): test 80, konu 70, kapak 10. Test sayfasi
  kumesi (10-29, 41-53, 63-76, 87-98, 112-123, 131-139) kapiyla birebir;
  kontak sayfasindan ilk gozle yazilan araliklar 2 yerde yanlisti (54, 87)
  -- kapi yakaladi, duzeltildi.
* Sayfa paritesi ACL23AG'nin tersi (simge x ve sutunlar ters).
* 39 test, 339 soru.

## 2. Cevap anahtari (test sonu tablosu)

* Tablo TURUNCU izgara (ACL23AG'de siyah): profilde ayri `anahtar_bolgesi`
  kancasi (turuncu piksel, >= 60 px kesintisiz kosu).
* Okuma A (ileri) ve okuma B (geri), bagimsiz: 339/339 hucre ayni.
* Glif ucuncu kanali: 160 hucre bolutlendi, LOO 150 uyum; 10 uyumsuz
  (T016 #3 #4 #5 #7 #9 #10 #11, T026 #1, T039 #5 #6) 5x gozle teyit --
  hepsinde okuma dogru. Bolutlemenin hucre sayisini tutturamadigi 21 test
  5x gozle okundu, okumayla ayni.
* Hucre sayisi == capa sayisi (39/39). Harf dagilimi A 22, B 62, C 80,
  D 102, E 73. Hicbir soru cozulmedi.

## 3. Capa ve kirpim

* Capa: okuyucu simgesi + kirmizi basili numara (ACL23AG ile ayni olcu,
  parite ters). Numarasi basilmamis soru yok.
* Ust sinir y 86 (bant cizgisi y 83), alt sinir 908 ya da cevap tablosu
  ustu - 18 (tablonun ustundeki mavi cerceve T016_12 kutusuna giriyordu).
* Kapilar: 339 kutu, cakisma 0, artik murekkep 0, kenar 0; disk ortme
  olcumu 47 soru.

## 4. Metin

* 10 grup, iki bagimsiz okuma tek dagitimda. 339 sorunun 304'u normalize
  ayni; 35 fark 4 hakemle kirpimdan gozle: okuma_1 10, okuma_2 9, ikisi 4,
  yok 12.
* `[??]` 14 soru; tahmin yazilmadi.

## 5. Mukerrer ve eski hat

* DB 19824 aday satir; 14 aday, 7 GUCLU. 1 soru (T013_05) ACIL 2025 KURS
  TYT-AYT Geometri'de ayni soru_hash ile var -> ayni id, ithal yazmadi.
  Yakin adaylarda 4 icerik cevap farki: bayrakli, cevap basili anahtardan.
* Eski hat: bu kitap adina DB'de satir yok (olculdu).

## 6. Ithal ve beta

* 0080 agac (GEO-ACL23KC: 1 bolum + 6 konu), ithal 338 yeni satir PASIF,
  0081 eski hat (0 satir), 0082 toplu beta onayi: 324/338 (14 gorunen
  `[??]` disarida). Round-trip (0079 <-> 0082) temiz.
* exam_type AYT, subject GEOMETRI.

# 345 2025 TYT Sosyal Bilgiler Soru Bankasi -- uretim yontemi ve olcumler

Kaynak adi (modern hat): `345 2025 TYT Sosyal Bilgiler Soru Bankasi`
(onek SOS345). Kitap '1 Ayda Tum TYT Sosyal': 30 GUN, her gunde 3-6
'OSYM TADINDA SORULAR k' testi (Tarih, Cografya, Felsefe, Din Kulturu).

## 0. Kaynak ve tavani

FERNUS okuyucusunun 1920x1080 ekran goruntuleri, 312 PNG; sayfa karti
(589, 43) - (1331, 1022) = 742x979; basili sayfa = dosya. Soru sayfalari
6-305 (300 sayfa; `sos345tyt_tarama.py`: okuyucu simgesi olan sayfa),
anahtar tablosu 306-312. Sayfa alti cevap SERIDI YOK (onceki 345 TYT
kitaplarindan farkli).

## 1. Cevap anahtari -- kitap sonu tablo (`sos345tyt_anahtar.py`)

Tablo: GUN basina satirlar 'OSYM TADINDA SORULAR k', hucreler '1.C 2.B ...'.

* Iki bagimsiz okuma: sayfa basina ayri okuyucu, 2.5x parcalar (3 parca /
  sayfa, ust uste binen kenarlar). A sayfa sirasiyla; B parcalar alttan
  uste, satirlar sagdan sola. 150 test, 1233 hucre; A == B 1230 hucre.
* Tek fark GUN 3 test 6, 3-5. hucreler (A 'E B C', B 'B C D'): s306 satiri
  5x gozle '1.E 2.A 3.E 4.B 5.C 6.D 7.A 8.A' -> A. Goz karari A ya da B
  olmak zorunda (kapi).
* Ucuncu kanal piksel glif: kart gri goruntusunde satir cizgileri, hucre
  metin kumeleri ('N.L'), en sag uzun bilesen harf, 12x12 vektor,
  en-yakin-komsu LOO: **1233/1233** (`_p345_gecici/ts_glif.py`; ekran
  goruntusu ister, sonuc ham dosyada).
* Hucre sayisi == okuyucu simgesi sayisi (1233 == 1233): sorular sayfa
  sirasinda (sutun L sonra R, yukaridan asagi) simgelere dagitilir.
* Birim: `SOS345-Tnnn` (GUN/test sirasinda ardisik, T001-T150).
* Soru cozulmedi.

## 2. Test haritasi ve konu agaci (`sos345tyt_harita.py`, 0065)

* Her soru sayfasinin ust bandi (DERS, KONU, rozet TEST, tek sayfada mavi
  kitapta GUN) iki bagimsiz okuma (B goruntuleri sondan basa): 300 sayfa,
  normalize fark 0.
* Kapi: her testin sayfalarinda bant (gun, test) == anahtar satiri (cift
  sayfanin gunu sonraki tek sayfadan); 150/150, her test 2 sayfa.
* Ders: Tarih 50, Cografya 50, Felsefe 25, Din Kulturu 25 test.
* Unite = (ders, konu tabani; sondaki ' - I/II' eki atilir): 69 dugum
  (TAR-345T25-U01..25, COG-345T25-U01..12, SOS-345T25-FEL-U01..15,
  SOS-345T25-DIN-U01..17). Felsefe ve Din icin ayri kok yok: SOS kokunun
  altinda, dugum subject_area FELSEFE / DIN.
* 0065_sos345_agac: yerel tur upgrade -> downgrade -> upgrade temiz.

## 3. Kirpim kutulari (`sos345tyt_kutu.py`, `sos345tyt_kirp.py`)

`kim345tyt_kutu.py` deseni; capa okuyucu simgesi (600/600 sutun).

* Kutu alti sutun sonunda kart y 925 (sayfa numarasi bandi 930'dan asagi).
* 'OSYM KOSESI' kutusu onceki sorunun son siklarina < 10 px yakin
  basilabiliyor: bos-bant kurali 5 soruda (T046_08, T052_08, T086_04,
  T127_08, T128_08) ust siniri onceki sorunun icine tasidi -- onceki
  sorunun son sik(lar)i sonraki kirpima dustu (ilk okumada okuyucular
  bildirdi: bos sik + komsu_not). Kural: onceki capanin altinda, capanin
  ustunde ya da yaninda turuncu kose etiketi dairesi (22-40 px) varsa kutu
  ustu = min(etiket, capa) - 1 (yalniz asagi). 65 kutu (60'i 2 px).
  Duzeltme sonrasi 10 kirpim yeniden okundu.
* 1233 kutu, kapi ihlali 0; ortme suphesi 169 soru; kenar kapisi 1 (T120_01
  sol kenar tablo cercevesi).
* Gorsel QA: rastgele 12 + kose / kesim bayrakli 8 kirpim gozle.

## Testler

`backend/tests/e2e/test_sos345tyt_veri.py` (19): anahtar hamdan birebir,
toplamlar, tek fark goz + glif, A/B / gereksiz / yabanci goz / bicim disi /
hucre-simge / glif mutasyonlari; harita hamdan birebir, sayilar, bant
(gun, test) ve A/B mutasyonu, konu tabani; migration == harita, kimlik;
kutu kapilari, kutu <-> cevap, kose etiketi duzeltmesi.

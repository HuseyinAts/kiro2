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
  ustu = min(etiket, capa) - 1 (yalniz asagi); ardindan bu sinirla
  etiket arasinda notr murekkep (min < 200) tasiyan son satirin bir alti
  (T046: onceki sorunun E satiri capanin 1-2 px altina iniyordu). 65 kutu.
  Capa kapisi capa MERKEZINE bakar (kose kutusunda ust sinir capa
  ustunden 1-3 px asagida olabilir).
  Duzeltme sonrasi 10 kirpim yeniden okundu.
* 1233 kutu, kapi ihlali 0; ortme suphesi 169 soru; kenar kapisi 1 (T120_01
  sol kenar tablo cercevesi).
* Gorsel QA: rastgele 12 + kose / kesim bayrakli 8 kirpim gozle.

## 4. Transkripsiyon (`sos345tyt_metin_harness.py`)

`345_2025_tyt_sosyal_metin.json` (1233 soru). Kirpimlar 2x Lanczos;
29 grup (test sinirina hizali, ~43 soru), 29 ayri okuyucu. Talimat
`VeraFilm/so_metin_talimat.md`: 'kitap ne yaziyorsa o', soru cozme yok,
ALAN BILGISIYLE KARAR VERME, anahtar gosterilmedi; sapkali harf pikselde
neyse; tablo ` | `; alti cizili `<u>`; sekil / harita / grafik yazisi
yalniz soru ona dayaniyorsa (K, L, M; I-V; lejant; tablo hucresi).

Kapilar (harness `kapi`): KAPI1 her kirpim bir kez; KAPI2 basili no ==
test ici sira; KAPI3 bes sik dolu; KAPI4 toplam 1233. **TUM KAPILAR
YESIL.** Null numara 0. Kose duzeltmesinden sonra 10 kirpim yeniden
okundu (ilgili gruplara islendi). Kaynak kusuru notu 117 soru.

### 4a. Ikinci okuma -- on kayitli TAM okuma

On kayit (`345_2025_tyt_sosyal_ikinci_okuma.json`, karsilastirmadan
ONCE): ilk okumayi gormeyen 29 ayri okuyucu, ayni talimat (teslim dizini
`so_metin_parca2`), ayni gruplar. Karsilastirma
`_p345_gecici/ts_metin_karsilastir.py`.

* Normalizasyon (NFC, kesme/tirnak tipi, eksi/tire tipi, orta nokta,
  `(gorsel)`/`(sekil)` yer tutucusu, tire cevresi bosluk) sonrasi 1039 soru
  ayni, 194 soru farkli (govde 170, sik 27; basili_no / sekil_var /
  sikler_gorsel / etiket farki 0).
* 194 farkin hepsi 5 hakem partisinde kirpimdan gozle (4-20x, piksel
  genisligi / profil) karara baglandi (hakem talimati
  `VeraFilm/so_hakem_talimat.md`; hukumler `hukumler`, nihai alanlar
  `duzeltmeler`): 40 yalniz bicim / sira, 66 ilk okuma, 81 ikinci okuma,
  7 ikisi hatali.
* **Ilk okuma esasli hata 73 / 1233 (%5.9)**; ikinci okuma 88. Hata
  turleri: soru metninin dayandigi sekil yazisinin (harita K/L/M, I-V
  numaralari, grafik ekseni / lejanti) atlanmasi; sapka (milli / Hukumet / askeri;
  sapka 4-6 px, i noktasi 2-3 px); noktalama (nokta / virgul /
  iki nokta / noktali virgul; virgul kuyrugu taban cizgisinin 1-3 px
  altina iner); tek / cift tirnak; rn / m. Kitabin baski hatalari
  ('faliyetleri', 'kalkida', 'getimek', 'dogru' (g), ters kesme `) korunur;
  duzelten okuma hatali sayildi.

### 4c. Okunamaz -> `[??]`

Hicbir soruda gercekten okunamayan karakter kalmadi; belirsiz tek
karakterler en iyi okuma + aday olarak `kaynak_kusuru`nda.

## 5. Mukerrer olcumu (`sos345tyt_mukerrer.py`)

`345_2025_tyt_sosyal_mukerrer_adaylari.json` (ithalden ONCE). KMT345
normal bicimi + kesme / tirnak tipi tek bicim + `<u>` silinir; govde
karakter 3-gram Jaccard (ters indeks). GUCLU = 3-gram >= 0.9 VE >= 3 ayni
sik. DB: TARIH / COGRAFYA / SOSYAL / FELSEFE / DIN (OSYM dahil) + bu kaynak
ve eski hat adlari: 533 satir.

* Pozitif kontrol: her 50. govdenin tirnak tipi degismis, bosluklari
  bozulmus, `<u>` sarili hali kendi sorusuna 1.0.
* Tam hash carpismasi 1: T095_06 == eski hat (2024 baskisi) satiri.
* Kitap ici: ayni hash yok; yakin cift 1 -- T010_02 / T148_01 (kitap
  soruyu 30. gunde tekrar basmis; C sikki 'suni gubre' / 'gubre'; iki
  basili cevap da E).
* Eski hat: 2025 baskisi 26 satir (25 modern karsilik), 2024 baskisi 12
  (8). Karsiliksiz 5: T050_07 (0.974, sik metni farkli), T062_04 (0.897,
  esigin alti), 3 satir 3-gram < 0.3.
* GUCLU aday 49 (eski hat 33, OSYM 2025 TYT 16).
* Cevap harfi farki 20: 14'unde DB'nin dogru sikkinin METNI bizde basili
  anahtarin harfinde (kitap OSYM siklarini yeniden siralamis; celiski
  yok). Icerik farki 6: eski hat 5 satir (T010_05 x2, T116_08, T136_09,
  T142_05; sik sirasi ayni, eski satirin cevabi basili anahtardan farkli)
  + Bilgi Sarmal T090_01 (0.828, zayif). Bizim cevap her zaman basili
  anahtar; degistirilmez.

## 6. Ithal (`sos345tyt_ithal.py`)

PASIF ithal (is_active FALSE, is_public FALSE, review PENDING); kaynak
sozlesmesi `SOS345`. 1233 yeni satir (zaten var 0, yabanci 0); DB'de bu
ithalin satirlari is_active 0, kapidan gecen 0.

* `subject_area` testin dersi (sayfa ust bandi): TARIH 441, COGRAFYA 395,
  FELSEFE 202, DIN 195; ders == unite dersi (0065) baglamada kapi.
* Cevap kanali: `iki_okuma+glif` 1230, `iki_okuma_farki+goz(5x)+glif` 3
  (GUN 3 test 6, soru 3-5).
* Bayraklar: okuyucu_diski_ortme 169, kaynak_kusuru 117, cikmis_soru 100
  (TYT / MSU / AYT etiketi), mukerrer_aday 44, diger_kaynak_sik_sirasi_farkli
  12, diger_kaynak_cevap_farki 4, sik_tekrar 5 (bes sik da gorsel),
  sikler_gorsel 6, db_hash_carpismasi 1.
* Kirpimlar `d-dataset/output/crops/SOS345/` (1233 PNG; boyut == kutu).

## Testler

`backend/tests/e2e/test_sos345tyt_veri.py` (35): anahtar hamdan birebir,
toplamlar, tek fark goz + glif, A/B / gereksiz / yabanci goz / bicim disi /
hucre-simge / glif mutasyonlari; harita hamdan birebir, sayilar, bant
(gun, test) ve A/B mutasyonu, konu tabani; migration == harita, kimlik;
kutu kapilari, kutu <-> cevap, kose etiketi duzeltmesi.
Transkripsiyon (bolum 5, +9): metin kapilari ve KAPI1-4 mutasyonu,
null numara yok, metin == kutular, kivrik kesme / numara notu yok,
ikinci okuma sayilari, duzeltmeler son metinde, `[??]` yok, etiketler.
Mukerrer (bolum 6, +7): ozet, eski hat iki baski, hash carpismasi,
hash degeri yazilmadi, cevap farki sik sirasi / icerik, pozitif kontrol
ve normal bicim, indeksli Jaccard == dogrudan.
`backend/tests/e2e/test_sos345tyt_ithal.py` (52): veri seti butunlugu,
yapisal kapilar, test ici sira, cevap kanali, unite == migration ve ders
== unite dersi, sozlesme, ASCII, pasif sozlesme, cikmis, bayrak capalari,
mukerrer bayraklari (icerik / sik sirasi ayrimi), mutasyonlar (yapisal 9,
on kontrol 8, baglama 6).

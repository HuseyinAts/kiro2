# 345 2025 AYT Matematik Soru Bankasi -- uretim yontemi ve olcumler

Kaynak: `veriseti/zkitap/screenshots/345 2025 Ayt Matematik Soru Bankasi/`
(384 PNG + PDF; ikisi de git disinda). Veri dosyalari
`veriseti/zkitap/cikti/345_2025_ayt_matematik_*.json`. Hat, 345 2025 TYT
Matematik hattinin (`MAT_345_TYT_YONTEM.md`) AYT'ye uyarlanmis kopyasidir;
farklar asagida ayrica yazildi.

| arac | is |
|---|---|
| `scripts/kitap/mat345ayt_tarama.py` | capa taramasi (simge, basili numara, ara cizgi) |
| `scripts/kitap/mat345ayt_kutu.py` | kirpim kutulari (+ `numara_disk_ortulu`) |
| `scripts/kitap/mat345ayt_kirp.py` | soru gorselleri + ortme / kenar olcumu |
| `scripts/kitap/mat345ayt_metin_harness.py` | transkripsiyon gruplari + kapilar + kusur notu normalizasyonu |
| `scripts/kitap/mat345ayt_ithal.py` | PASIF ithal |
| `alembic 0045_mat345ayt_agac` | konu agaci (MAT-345A25) |
| `alembic 0046_mat345ayt_kaynak_adi` | eski hat source_book yazim duzeltmesi |
| `alembic 0047_mat345ayt_eski_cevap` | 3 eski hat satiri kitabin basili cevabina |

Hicbir soru cozulmedi; hicbir cevap uretilmedi.

## 0. Hangi baski, kaynak ve tavani

Iki yakalama var: `345 2024 Ayt Matematik` (sekme '2024 - AYT - Matematik -
Sb') ve `345 2025 Ayt Matematik` (sekme '2025 ayt matematik sb'); ikisi de
384 sayfa. Durum raporu (`ZKITAP_KITAP_DURUMU.md`) ikisini %94-95 ortak
olcmustu; gozle: s20'deki OSYM kosesi sorusu 2024'te 'LYS - 1 - 2015',
2025'te 'AYT - 2025' -- 2025 baskisi cikmis sorulari guncellenmis baskidir.
**2025 islendi**; 2024 yalniz cevap celiskisi kanitinda okundu (bolum 7).

Sayfa karti TYT kitabiyla ayni olculdu: `(589, 43) - (1331, 1020)` = 742x977
(sol/sag golge x 583-588 / 1332-1337, ust y 43, 5 ornek sayfa). Basili sayfa
numarasi dosya numarasiyla ayni.

| kalem | deger | kanal |
|---|---|---|
| toplam sayfa | 384 | dosya sayimi |
| on sayfalar | 1-4 (kapak, kunye, icindekiler 3-4) | goz |
| bolum ayraci | 6 (5, 97, 155, 185, 219, 361) | sag kenar doygunlugu + goz |
| soru sayfasi | 374 | cevap satiri |
| test | 187 | cevap satiri numaralandirmasi |
| soru | 1942 | cevap satiri (x2) + transkripsiyon |

## 1. Cevap anahtari -- sayfa alti satir, iki okuma + piksel kanali

Anahtar her soru sayfasinin altinda, sutun basina ayri basili satir (kart
y 899-904; TYT'de 892-904). `345_2025_ayt_matematik_cevap_anahtari.json`;
ham okumalar `345_2025_ayt_matematik_ham_okumalar.json`.

| | okuma A | okuma B |
|---|---|---|
| olcek | 5x | 7x |
| montaj | 12 satir | 9 satir |
| sira | sayfa sirasinda | TERS |
| okuyucu | 2 ayri ajan | 2 ayri ajan |
| girdi sayisi okuyucuya soylendi mi | hayir | hayir |

* A == B: **1942/1942** girdi, harf ve numara duzeyinde fark 0.
* Ucuncu kanal (piksel): harf glifi 8x9 pencere, en-yakin-komsu,
  birini-disarida-birak. 1896 glif segmente edildi, LOO uyumu **1894/1896**.
  Uyumsuz 2 girdi (s189 sol 10.A, s262 sag 3.C) 6x en-yakin-komsu kontrast
  buyutmesiyle gozle incelendi: ikisinde de A/B okumasi dogru.
* Segmentasyonun kapsamadigi **12 yarim satir** (46 girdi) gozle tarandi;
  okumayla celiski yok.
* Okuyuculardan birinin '?' ile tereddut isaretledigi **24 girdi** (cogu
  14/4 rakami, iki noktasiz basilmis girdi '5C', '2B') ayni buyutmeyle gozle
  incelendi; harf 24'unde de dogru, rakam belirsizligi numara surekliligiyle
  kapaniyor.
* Numara kitap boyunca ya oncekinin +1'i ya da 1: 187 test, baska kopma yok.
* Testlerin 175'i 2, 6'si 1, 6'si 3 sayfa; sayfalar hep ardisik; iki testi
  birden tasiyan sayfa yok.

Kaynak dagilimi (`cevap_okuma_kanali`): `iki_okuma+piksel` 1870,
`iki_okuma+goz(piksel_kapsam_disi)` 46, `iki_okuma(biri_tereddutlu)+goz` 24,
`iki_okuma+piksel_supheli+goz` 2.

## 2. Konu agaci -- kitabin kendi icindekiler sayfasi (0045)

Icindekiler (dosya 3-4): 6 bolum, 15 konu ve her konunun basili baslangic
sayfasi. Bolum ayraci sayfalari yalniz 'BOLUM NN' ve konu listesini basiyor;
dugum adi 'Bolum NN' (uydurulmadi).

Bagimsiz ikinci kanal: her testin ilk sayfasindaki baslik bandi (187 bant,
ayri bir okuyucu okudu, `ham_okumalar.json` > `bant_okumasi`):

* test turu: Klasiklesmis 100 test / 1311 soru, OSYM Tadinda 77 / 575,
  Orijinal Sorular 10 / 56;
* 187 testin 187'si tek bir icindekiler araligina dusuyor;
* bantta konu adi basili 176 testin 176'sinda bant adi == aralik konusu
  (acik esleme gerekmedi). Orijinal Sorular bantlari (10) ve bir OSYM bandi
  (T095, s197, 'Sinavda Bu Tarz Sorular' basligi) konu adi basmiyor;
* Klasiklesmis ve OSYM Tadinda sira numaralari her konuda 1'den kesintisiz;
  her Orijinal bandi kendi konusunda 1.

## 3. Kirpim kutulari -- iki capa kanali, kitabin anahtari secer

| kanal | olcum |
|---|---|
| okuyucu simgesi | 1936 simge |
| basili numara | 1897 numara |

748 sutunun 704'unde numara, 44'unde simge kanali kullanildi; ikisinin de
tutmadigi sutun **0**. Kutusuz soru 0; kutular cevap satirina ulasmiyor
(`SAYFA_ALTI` 896 < 899).

TYT kurallari aynen (bant tavani, OSYM kosesi logosu, kisa bant, cerceve
beyazlatma). AYT'de olculen ve DUZELTILEN tek kusur:

| kusur | nasil yakalandi | duzeltme |
|---|---|---|
| OSYM kosesi logosunun hemen ustundeki onceki sorunun son secenek satiri logoya 6 px'ten yakin, hatta logonun ust kenarindan asagi sarkiyor; kesim secenegin alt kenarindan gecti (T114_04, T143_05, T157_10 -- T157_10'da E sikkinin integral alt siniri sonraki kutuya gecti) | ust kesimi +-3 satirda metne degen kutu olcumu (4 kutu) + uc okuyucunun 'kesik sik' notu | logonun SOLUNDA, logo ustu-6 ile capa-10 arasindaki son murekkep satirinin 2 px altindan kes (`logo_yakin_secenek`, 3 kutu) |

Degisen 6 kirpim (T114_04/05, T143_05/06, T157_10/11) yeni kirpimdan AYRI bir
okuyucuyla yeniden okundu (`duzeltme`). Dorduncu isaretli kutu (T165_07) goz
ile incelendi: kesim onceki sorunun kesir paydasinin 1-2 px altinda, metin
disinda.

Kenar kapisi: **0** kutu.

## 4. Transkripsiyon

1942 kirpim 2x Lanczos, test sinirina hizali 30 grup; her grubu ayri okuyucu
okudu (talimat: `VeraFilm/a_metin_talimat.md`, git disi). Okuyuculara anahtar
SOYLENMEDI; matematik yazimi sozlesmesi (kesir a/b, us ^, kok U+221A(...),
limit lim_(x U+2192 a), integral U+222B_a^b ... dx, toplam U+03A3_(k=1)^(n),
eksi U+2212)
talimatta sabit.

Kapilar (`mat345ayt_metin_harness.py kapi`) YESIL:

| kapi | sonuc |
|---|---|
| her kirpim tam bir kez | 1942/1942 |
| basili numara == test ici sira | 1881/1942 esit; 61 bos, hepsi disk altinda |
| bes sik dolu | 1942/1942 |

**Numara disk altinda.** 61 bos numaranin 51'i simge capali kutu. Kalan
10'unda capa basili numaradan alinmisti: okuyucu diski numaranin ilk
rakamini ortuyor, piksel kanali yalniz diskin sag kenarindan cikan parcayi
saydi (10'u da 4x buyutmede gozle gorulerek dogrulandi). Olcu: disk merkezi
ile numara kutusunun sol ucu arasi yatay mesafe; diski eslesen 1720 numara
capali kutuda medyan 17, 1697'si 14-26; bu 10 kutunun 10'unda <= 13.
Kutuya `numara_disk_ortulu` (23 kutu) yazildi; kapi bu kutularda bos
numaraya izin verir.

**Kusur notu normalizasyonu.** Ilk 6 grup, talimata 'Ek kurallar' eklenmeden
once okundu ve `kaynak_kusuru`na soluk ama okunan isaretleri de yazdi. 24
grupla tutarlilik icin 57 not dusuruldu (51 'soluk isaret', 6 'numara beyaz
leke'); okunan METIN degismedi. Kural mekanik, her not
`345_2025_ayt_matematik_kusur_normalizasyonu.json` icinde aynen saklanir ve
harness `topla` bu dosyayi uygular (yeniden uretilebilir). Kalan 135 not
gercek okuma belirsizligi (kucuk log tabanlari, teta / dik isareti kirik basim, kesik
harf).

Olculen capalar: sekilli 581, siklari gorsel 10 (ikisinde her sik cizim +
cumle), 'OSYM KOSESI' etiketli 142 (AYT 122, LYS 19, YGS 1; yil 2010-2025),
kaynak kusuru notu 137 (135 + ikinci okumada eklenen 2; bolum 4a).
Rastgele 5 soruluk orneklem (tohum 2026) gozle kirpimla karsilastirildi:
5/5 birebir.

## 4a. Ikinci okuma -- orneklemle karar, hedefli tabaka (0048)

Soru: tam ikinci okuma gerekli mi? Kural OLCUMDEN ONCE yazildi
(`345_2025_ayt_matematik_ikinci_okuma.json` -> `protokol`):

* Orneklem: 30 okuma grubunun her birinden 7 soru (random.Random(20260924)),
  210 soru. Ikinci okuyucular ilk okumayi GORMEDI; ayni talimat, ayni kirpim.
* Esasli hata: matematigi/anlami degistiren fark (rakam, isaret, degisken,
  us/kesir yapisi, aralik ucu, eksik ifade, yanlis sik). Yazim bicimi degil.
* Karar: ilk okumanin esasli hata oraninin 95% Clopper-Pearson ust siniri
  <= %3 -> tam ikinci okuma yok; > %3 ve hatalar bir tabakada -> yalniz o
  tabaka; > %3 ve yayilmis -> tam ikinci okuma.

Olcum:

| | n | esasli hata | 95% ust sinir |
|---|---|---|---|
| orneklem | 210 | 2 (T058_02, T060_08) | %3.40 |
| grup_11 | 7 | 2 | -- |
| grup_11 disi | 203 | 0 | %1.80 |

Iki hata da ayni grupta ve ayni ozellikte: sinirlayici gosterimi (aralik
ucu `(`/`[`, dogru parcasi `[AB]` / uzunluk `|AB|`). Dusuk cozunurlukte
kapanan parantez ucu kopuk piksel, koseli parantezin tirnagi cogu kez
gorunmez; hata burada toplaniyor. Karar: **HEDEFLI ikinci okuma**. Tabaka =
grup_11 tamami + kitaptaki tum sinirlayici ozellikli sorular = 362 (31'i
orneklemde okunmustu, 331 yeni).

Sonuc: 541 ikinci okumanin 77'sinde fark; her fark kirpima 8x en-yakin-komsu
buyutmeyle bakilarak hukme baglandi (soru cozulmedi). 10 soruda ilk okuma
esasli hatali, 4 soruda yalniz baski kusuru notu eklendi, kalan 63 farkta
ilk okuma korundu (ikinci okuma hatasi ya da esdeger yazim).

| soru | alan | ilk okuma | basili |
|---|---|---|---|
| T045_03 | govde | `2/x_((1)) + 1/1_((x))` | `2/x + 1/1` |
| T054_02 | D | `(0, 2]` | `(0, 2)` |
| T058_02 | govde | `\|AD\| U+22A5 \|CD\|`, `\|AC\| U+22A5 \|BC\|` | `[AD]`, `[CD]`, `[AC]`, `[BC]` |
| T060_01 | govde | `... - cos2x - 1` | `... - cos2x + 1` |
| T060_08 | govde | `(0, 360 U+00B0]` | `(0, 360 U+00B0)` |
| T062_03 | govde | `[0, 2 U+03C0)` | `(0, 2 U+03C0)` |
| T062_04 | govde | `[0, 2 U+03C0)` | `(0, 2 U+03C0)` |
| T062_14 | govde | `[0, 2 U+03C0]` | `(0, 2 U+03C0]` |
| T064_03 | govde | `\|AD\| // \|BC\|`, `\|AD\| U+22A5 \|AB\|` | `[AD] // [BC]`, `[AD] U+22A5 [AB]` |
| T073_04 | D | `36/65` | `38/65` |

Kusur notu (metin degismedi): T046_15 (`|AC|` ya da `[AC]` belirsiz), T105_04
(D sinirlayicilari belirsiz), T143_04 ve T162_05 (esittir isaretinin alt
cizgisi basimda yok, `=` olarak okundu).

**DB.** Bu satirlar DB'ye ilk metinle girmisti ve id = uuid5(ilk hash).
0048 metni/siki, soru_hash'i, kelime istatistiklerini ve kusur notunu
yerinde duzeltir; guard id + eski hash + parcanin tam bir kez gecmesi.
Ithal, kayittaki `id_sabitleme` ile bu 10 satirin id'sini ilk hash'e
sabitler: tekrar kosu 0 satir yazar (sabitleme kaldirilinca 10 cift satir
yazacagi olculdu). Migration sonrasi 14 satirin tum alanlari ithalin bugun
urettigi kayitla birebir; yerel DB'de yukari/asagi/yukari gidis-donus
42 tablo satirinda birebir.

Kalan risk: tabaka disi sorularda orneklem 0/203 (ust sinir %1.80); bu
sorular tam ikinci okunmadi.

## 5. Ortme

Okuyucu diski beyazlatildi; diskin kenar halkasinda kitap murekkebi olculen
**175 soru** `okuyucu_diski_ortme` bayragi tasir. Iki sutunlu sayfalarda sag
sutunun diski sol sutunun ilk satir sonunu da ortebiliyor (T069_04,
T073_03, T145_01, T165_04: son harf yarim). 2024 baskisi kurtarma kanali
olabilir -- bu ithalde KULLANILMADI (borc).

## 6. Mukerrer adaylari -- isaretlendi, silinmedi

DB'deki 14293 MATEMATIK+GEOMETRI satirina karsi govde kelime kumesi Jaccard
>= 0.75: 154 aday; GUCLU (ayrica bes sikkin >= 3'u birebir): **22**
(345 2025 AYT eski hat 8, OSYM 2025 AYT 7, 345 2024 AYT eski hat 5, diger 2).
22'nin 19'unda DB cevabi bizim okumamizla ayni; 3 celiski bolum 7'de.
Hash duzeyinde bu kitabin 1942 sorusu birbirinden farkli; biri (T176_10)
'345 2024 Ayt Matematik' eski hattindaki aktif bir satirla hash duzeyinde
ayni (ayni cevap C) -- ikinci kopya PASIF, aktif-benzersizlik indeksi
etkilenmez.

## 7. Eski hat satirlari (0046, 0047)

DB'de bu kitaptan eski hattan 11 satir var (`345 2025 Ayt Matematik Soru
Bankas<U+0131>`, 11'i aktif). Yazim yeni ASCII adla ayni anahtara cozuluyor;
0046 yalniz `source_book` yazimini duzeltir (0043 deseni, geri alinabilir).
'345 2024 Ayt Matematik' (10 satir) farkli anahtar, dokunulmadi.

**0047** -- sahip karari (24 Eyl 2026, 345 TYT icin verildi, ayni kural):
"kitabin basili cevabi baz alinir". Bolum 6'daki 3 celisen aktif + public
eski hat satiri kitabin basili cevap satirina hizalandi. Her satirin cevabi
KENDI baskisinin seridinde 6x buyutmeyle gozle okundu:

| satir | kaynak | DB | basili | not |
|---|---|---|---|---|
| d2b4fdfc | 345 2024 AYT s15 sag 13 | B | C | 2024 ve 2025 seridi '13.C' |
| af48fac5 | 345 2025 AYT s27 sol 5 | A | C | eski hattin 'en az 3' cikan cozum ozeti NULL |
| ada94c26 | 345 2025 AYT s76 sol 1 | D | C | eski metin '\ge 0', basili '> 0' (iki baskida da); yalniz bu parca duzeltildi, hash yeniden |

Yerel DB'de yukari/asagi/yukari gidis-donus olculdu (beta gorunumu sabit).

## 8. Alanlar ve kaynaklari

| alan | kaynak |
|---|---|
| `question_text`, `a..e` | kirpimdan gorsel okuma (30 grup + 6 duzeltme + 14 ikinci okuma hakemi) |
| `correct_answer` | sayfa alti cevap satiri, iki okuma + piksel + goz |
| `explanation` | NULL -- kitapta cozum yok, uydurulmadi |
| `question_image_url` | tam soru kirpimi `/static/crops/MAT345_AYT/` |
| `exam_type` | `AYT` |
| `source_page` | dosya no (= basili no) |
| `osym_year`, `osym_format_compliant` | yalniz OSYM kosesi etiketli 142 soruda |

Ithal PASIF: `is_active=FALSE, is_public=FALSE, is_ai_generated=TRUE,
review_status='PENDING'`. DB olcumu: qb/qc/qs 1942/1942/1942, aktif 0,
public 0, beta gorunumu 0, 15 konu dugumu, osym_year 142; ikinci kosum
0 satir yazar.

## 9. Bilinen borc

1. Ikinci okuma HEDEFLI yapildi (bolum 4a, 0048); tabaka disi sorular
   tam ikinci okunmadi (orneklem 0/203, ust sinir %1.80).
2. 175 soruda okuyucu diski ortme suphesi; 2024 baskisi kurtarma kanali
   kullanilmadi.
3. 137 soruda okuyucu kaynak kusuru notu (7'si 'kucuk log tabani en iyi
   tahmin', T084_03'te taban '?'); duzeltilmedi, bayrakli.
4. 22 guclu mukerrer aday; birlestirme/eleme karari verilmedi (celisen 3
   eski hat satiri 0047 ile basili anahtara hizalandi).
5. 10 soruda siklar gorsel; soru gorselle birlikte gosterilmeli.

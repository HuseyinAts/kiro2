# 345 2025 TYT Kimya Soru Bankasi -- uretim yontemi ve olcumler

Kesif ve plan: `KMT_345_KESIF_VE_PLAN.md`. Hat 345 2025 TYT Fizik
(`FZT_345_YONTEM.md`) ile ayni; betikler `fiz345tyt_*`'den uretildi,
bu kitapta olculen farklar asagida.

## 0. Kaynak ve tavani

FERNUS okuyucusunun 1920x1080 ekran goruntuleri, 280 sayfa. Ic kart
(589, 43, 1331, 1022) = 742x979; basili sayfa = dosya.

## 1. Cevap anahtari -- sayfa alti serit, iki okuma + glif + goz

Cikti: `345_2025_tyt_kimya_cevap_anahtari.json` (138 test, 1307 cevap).
Ham: `345_2025_tyt_kimya_ham_okumalar.json`. Tarama:
`345_2025_tyt_kimya_capa_taramasi.json`.

1. **Soru sayfasi:** kart y 899-904 bandinda gri murekkep + en az bir
   okuyucu simgesi: 267 sayfa. Seritsiz 3-5 ve 8 unite ayraci.
2. **Girdi sayisinin bagimsiz kanali:** okuyucu simgesi (stm345 tanimi).
   Serit bandinin uzerindeki simgeler soru capasi degil: 39 sutunda cy
   893-930 ve s185 L'de cy 887 (gozle: seridin hemen ustunde, soru metni
   yok). En alttaki gercek soru simgesi cy 834 -> esik 870. 1307 simge.
3. **Iki okuma:** A 5x sayfa sirasi (45 montaj, 12 satir), B 7x TERS sira
   (60 montaj, 9 satir); 8'er ayri okuyucu; girdi sayisi soylenmedi.
   A 1307 girdi, B 1307 girdi; 534 sutunun 534'u birebir ('?' haric).
4. **Kapilar:** girdi sayisi == simge 534/534; numara ya +1 ya 1
   (1307/1307, 138 test); her test tek unite araliginda, sayfalari ardisik.
5. **Glif kanali:** en-yakin-komsu LOO 1234/1307. Tutmayanlarin cogu
   serit ustundeki okuyucu simgesi / sayfa susu ve sol cubugu soluk 'D'.
6. **Goz (5x):** '?' tasiyan (64 sutun) ya da glifi tutmayan sutunlarin
   birlesimi 106 sutunun TUM girdileri (14 montaj, 8 satir); hepsi A/B
   okumasiyla ayni. Soluk 'D' sag kapali yay (C acik), 'B' orta centikli.

Kanal dagilimi: iki_okuma+piksel 1032, +goz(5x) 208, +goz+tereddut 67.
Harf: A 203, B 194, C 348, D 281, E 281.

## 2. Unite agaci (0062)

Cikti: `345_2025_tyt_kimya_konu_haritasi.json` (`kim345tyt_harita.py`),
migration `0062_kmt345_konu_agaci.py` (o JSON'dan uretildi).

* 9 unite, 35 konu: icindekiler (dosya 3-4, gozle).
* Bagimsiz dogrulama: her unitenin ilk soru sayfasinin ust bandi 9/9
  '1. TEST' rozeti + orta bantta ilk konu adi (ASCII buyuk; s110
  'MADDENIN FIZIKSEL HALLERI' -- icindekilerde 'Halleri', bantta sapkali).
  Her unite bir onceki ayractan (seritsiz sayfa) hemen sonra baslar.
* Duzey UNITE: her unitenin sonundaki 'OSYM TADINDA' testleri butun
  uniteyi kapsar ve son konunun sayfa araligina duser; test turu pikselden
  ayrilmadi. Konu listesi haritada kayitli, agaca yazilmaz.
* KIM kokunun altinda `KIM-345T25-Unn`, kok+1, subject_area 'KIMYA'.
  Yerel DB'de upgrade -> downgrade -> upgrade temiz (9 -> 0 -> 9).

## 3. Kirpim kutulari (`kim345tyt_kutu.py`, `kim345tyt_kirp.py`)

Cikti: `345_2025_tyt_kimya_kirpim_kutulari.json` (1307 kutu, kapi ihlali 0),
`345_2025_tyt_kimya_ortme_olcumu.json`.

* Capa: okuyucu simgesi BIRINCIL. Cift sayfa sol sutunun ustundeki
  'N. TEST' rozeti camgobegi rakamdir ve numara kanalina girer (95 sutunda
  numara = simge + 1); rozet + eksik bir numara sayiyi tutturabilecegi icin
  numara ikincil.
* 3 sutunda (s28 R, s226 R, s228 R -- 'OSYM TADINDA' sayfalari) okuyucu
  simgesi sorunun degil basligin yaninda (cy 58-94): ilk kosuda T012_04
  kirpimi basligi ve gostergeyi iceriyordu (gozle). Kural: kart y < 125
  (ust bant; en yuksek gercek soru capasi cy 137) capa olamaz; o sutunlarda
  ust bandin altindaki basili numaralar capa. Sonuc: simge 531, numara 3.
* Tavan: kirmizi konu bandi + 4; kisa bant kurali 47 kez.
* Gorsel QA (gozle, tohum 345): ilk kosuda kesim-metne-degen 16 kutu +
  8 ornek; duzeltmeden sonra numara capali 5, en kisa 3, en uzun 2,
  rastgele 12 kirpim -- hepsi tek soru, numara ustte, siklar icinde.
* Ortme suphesi 117 soru (118 halka); kenar kapisi ihlali 0.

## 4. Transkripsiyon (`kim345tyt_metin_harness.py`)

`345_2025_tyt_kimya_metin.json` (1307 soru). Kirpimlar 2x Lanczos;
30 grup (test sinirina hizali, ~44 soru), 30 ayri okuyucu. Talimat
`VeraFilm/k_metin_talimat.md`: 'kitap ne yaziyorsa o', soru cozme yok,
KIMYA BILGISIYLE KARAR VERME (kitap celdirici / yanlis deger basmis
olabilir), anahtar gosterilmedi, kimya yazim sozlesmesi (alt indis
`H_2O`, `C_6H_(12)O_6`; iyon yuku `Ca^(2+)`, `Cl^-`; izotop
`^(235)_(92)U`; fiziksel hal; tepkime oklari; eksi U+2212; tablo ` | `;
alti cizili `<u>`; sekil yazisi yalniz soru ona dayaniyorsa).

Kapilar (harness `kapi`): KAPI1 her kirpim bir kez; KAPI2 basili no ==
test ici sira; KAPI3 bes sik dolu; KAPI4 toplam 1307. **TUM KAPILAR
YESIL.** Null numara 2 (T073_09, T094_04: disk numarayi tamamen
kesiyor; ikisi de simge kanalinda). Numara-kesigi notlari `topla`da
ayiklanir; kalan gercek kusur notu 125 soru.

### 4a. Ikinci okuma -- on kayitli TAM okuma

On kayit (`345_2025_tyt_kimya_ikinci_okuma.json`, karsilastirmadan
ONCE): ilk okumayi gormeyen 30 ayri okuyucu, ayni talimat (teslim dizini
`k_metin_parca2`), ayni gruplar. Karsilastirma
`_p345_gecici/tk_metin_karsilastir.py`.

* Normalizasyon (NFC, kesme/tirnak tipi, eksi/tire tipi, carpma noktasi,
  tek karakterli indis parantezi `_(9)F == _9F`, `(gorsel)`/`(sekil)` yer
  tutucusu, tire cevresi bosluk) sonrasi 1115 soru ayni, 192 soru farkli
  (govde 155, sik 103, sekil_var 3, sikler_gorsel 1).
* 192 farkin hepsi 5 hakem partisinde kirpimdan gozle (4-20x, gri deger
  dokumu) karara baglandi (hakem talimati `VeraFilm/k_hakem_talimat.md`;
  hukumler `hukumler`, nihai alanlar `duzeltmeler`): 88 yalniz bicim,
  58 ilk okuma, 42 ikinci okuma, 4 ikisi hatali.
* **Ilk okuma esasli hata 62 / 1307 (%4.7)**; ikinci okuma 46. Fizik'in
  (%1.0) ustunde: hatalarin onemli bir kismi soru metninin dayandigi sekil yazisinin
  (beher / sise etiketi, kavram haritasi kutusu, kesit harfleri) atlanmasi;
  kalanlar tek karakter (alt indis 6/8, 1/4, 3/8; atom numarasi; virgul /
  nokta; iyon yuku isareti). Kitabin baski hatalari ('(suca)',
  '^(58)_(28)Fe', 'C_8H_6', '10^(25)', '+3'lur') korunur; duzelten okuma
  hatali sayildi.
* Lewis / yapi formulu cizimleri metne DOKULMEZ, `(sekil)` yer tutucusu
  (okuyucular noktali cizimi farkli sozcuklerle tarif ediyordu). Iki
  okumanin ayni bicimde metne doktugu 3 soru (T040_05 B, T048_04 D,
  T048_09) de ayni sozlesmeye cekildi (`tk/ek_duzeltme.json`); duzeltme
  kaydi 195.

### 4b. Soluk isaret taramasi (iyon yuku)

Kimya riski: '+'nin dikey cubugu soluk basilinca okuyucu '-' yazar.

* STM345 4b deseni (koyu kisa yatay cubuk + ortasindan gecen simetrik
  SOLUK dikey iz) 1x kirpimlarda: 20 soruda 41 aday; 36'si sekil ogesi
  (beher cizgisi, bag cizgisi, tepkime oku, elektron katman yayi, Lewis
  noktasi). Metindeki 5 aday (T018_07 Na^+, T028_02 X^-, T116_10 OH^-,
  T059_08 -60 / -39 C) buyutmede dogru.
* Metinde eksi yuklu yazilmis tipik katyonlar (9 kayit, 8 soru: T034_05
  Na, T042_04 Mg, T048_01 Mg, T083_08 H, T116_05 H, T117_07 H, T127_06 H,
  T130_10 Ca/Mg) gri deger dokumuyle incelendi: hepsinde cubugun ortasinda
  ust/alt dikey iz yok -> basildigi gibi eksi (kitabin baskisi; cozum
  yapilmaz). Karsi ornek: T039_01 NH_4 yukunde ustte 3 satir soluk dikey
  iz var -> '+' (ilk okuma '-' yazmisti; hakem karari dogrulandi), T045_02
  Ca^(2+) ayni desen.

### 4c. Okunamaz -> `[??]`

Hicbir soruda gercekten okunamayan karakter kalmadi; belirsiz tek
karakterler en iyi okuma + iki aday olarak `kaynak_kusuru`nda.

## 5. Mukerrer (`kim345tyt_mukerrer.py`)

`345_2025_tyt_kimya_mukerrer_adaylari.json` (ithal ONCESI olcum). Olcu
FZT345 ile ayni: formulu koruyan normal bicim (NFKC, kucuk, eksi tek '-',
bosluk / parantez / LaTeX / indis '_' / us '^' silinmis) karakter 3-gram
Jaccard, ters indeksle; GUCLU = 3-gram >= 0.9 VE bes sikkin >= 3'u
birebir. Pozitif kontrol: kesirli + eksili 33 govdenin LaTeX'lesmis hali
kendine 1.0.

* DB havuzu: KIMYA 4855 satir (OSYM dahil) + eski hat adlari.
* Kitap ici: ayni hash 0, yakin cift 0. Genel govdeler ('Asagidakilerden
  hangisi yanlistir?' 13 soru, vb.) 3-gram 1.0 verir ama siklar farkli.
* DB tam hash carpismasi 36 soru: 28'i eski hat 2025, 7'si eski hat 2024,
  1'i 345 AYT Kimya. Ithal bunlara satir yazmaz (FZT345 kurali: aktif
  ayni hash varken ikinci satir yok).
* Kayit esigi (0.75) ustu 553 aday, GUCLU 346 (266 farkli soru): eski hat
  330, Esen Aps 7, Bilgi Sarmal 2024 7, 345 AYT 1, OSYM 2025 TYT 1. OSYM
  etiketli 100 sorunun 39'u baska kaynakta da var.
* Cevap farki 59 kayit (bilgi): bizim cevap BASILI anahtardir,
  degistirilmez. GUCLU eski hat eslesmelerinde 19 farkli cevap.

### 5a. Eski hat (iki eski aktarim)

| kaynak adi (DB) | satir | aktif | modern karsiligi (GUCLU) |
|---|---|---|---|
| 345 2025 Tyt Kimya Soru Bankasi (Turkce i) | 294 | 294 | 211 |
| 345 Tyt Kimya Soru Bankasi (2024 baskisi) | 213 | 213 | 119 |

Eski satirlarin en yakin modern soruya 3-gram dagilimi: 1.0'a yuvarlanan
272, 0.9 164, 0.8 53, <= 0.7 18. GUCLU eslesen 330 eski satirin 311'inde
cevap bizimkiyle ayni. Ayni modern soruya iki baskidan birer eski satir
baglanan 55 soru var (ayni soru her iki baskida).

## 6. Ithal (`kim345tyt_ithal.py`) -- PASIF

`fiz345tyt_ithal.py` deseni; kaynak adi `345 2025 TYT Kimya Soru Bankasi`
(`kaynak_sozlesmesi`: onek KMT345). Kirpimlar
`d-dataset/output/crops/KMT345/` (1307 PNG, git disi).

* Yapisal kapi: 1307 soru + 138 test + 9 unite + 1307 anahtar + 1307 kutu
  + 100 etiket, cevap sizintisi yok. On kontrol temiz.
* Soru UNITE dugumune baglanir (`konu_eslesme_duzeyi` = 'unite'; 0062).
* Cevap kanali: iki_okuma+piksel 1032, iki_okuma+goz(5x) 208,
  iki_okuma+goz(5x)+tereddut 67.
* Bayraklar: mukerrer_aday 266, cikmis_soru 100, okuyucu_diski_ortme 117,
  kaynak_kusuru 125, db_hash_carpismasi 36, sik_tekrar 13, sikler_gorsel
  30, diger_kaynak_cevap_farki 18, numara_ortulu 2; okunamaz_isaret 0.
* Yerel DB'ye yazim (26 Eyl): **1306 yeni satir, hepsi is_active=FALSE,
  kapidan gecen 0.** 1 soru (T025_01) 345 2025 AYT Kimya'da (T008_07,
  pasif) ayni id ile zaten var -> `ayristir` dokunmaz, bu kitap icin
  satir yazilmaz. Eski hatla ayni soru_hash
  tasiyan 35 soru (eski satirlarin id'si farkli sema) PASIF yazildi;
  aktiflestirmede tekil aktif hash kurali geregi eski satir once pasife
  alinmadikca acilamaz (bolum 7).

## 7. Eski hat pasif (0063) ve aktiflestirme (0064) -- Faz 8

Sahip talimati (26 Eyl): "ucunu de sirayla onay istemeden kesintisiz tam
otonom isle". Emsaller 0058 (eski hat pasif) ve 0061 (toplu beta onayi).

* **0063_kmt345_eski_hat_pasif**: modern karsiligi GUCLU olan 330 eski
  satir (liste mukerrer olcumunden birebir; test) is_active=FALSE, SILINMEZ;
  onceki deger gunluge, downgrade geri yukler. Guard: modern karsiligi bu
  kitabin ithal satiri olarak DB'de yoksa eski satira dokunulmaz (taze/CI
  DB; T025_01 -> 1 eski satir aktif kalir). Yerel olcum: 329 pasif; eski
  hatta aktif kalan 83 + 95 = 178 (GUCLU eslesmeyen 177 + T025_01'in
  karsiligi). GUCLU eslesmeyen eski satirlar (3-gram < 0.9 ya da < 3 ayni
  sik; 2024 baskisinin farkli sorulari dahil) bilincli olarak AKTIF
  birakildi.
* **0064_kmt345_beta_onay**: 0061 ile ayni dislama kurali (servis disi
  bayrak, gorunen alanda `[??]`, aktif hash ikizi). Kapi yuku olculdu:
  1306/1306 pending, servis disi 0, `[??]` 0, bos sik 0, gorselsiz 0,
  aktif hash ikizi 0 (0063 sonrasi). **1306 satir acildi**
  (auto_judged_high, APPROVED; 'human_verified' yazilmaz; is_ai_generated /
  is_public dokunulmaz).
* Yerel tur: upgrade head -> downgrade 0062 (1306 kapandi, 329 eski geri
  aktif) -> upgrade head; tekrarli aktif hash 0.

## Testler

`backend/tests/e2e/test_kim345tyt_veri.py` (53): hamdan birebir anahtar
turetme, A/B birebir, A/B farki / gereksiz fark karari / bicim disi /
numara kopmasi / simge farki / goz celiskisi mutasyonlari, kapsam, unite
araliklari (ayractan hemen sonra), kanal durustlugu, ASCII; harita hamdan
turer, migration == harita, zincir, kodlar, bant / rozet mutasyonu, sapka
katlamasi; kutu kapilari, kutu <-> cevap birebir, simge birincil capa,
ust bant simgesi reddi, kapi mutasyonu, ortme raporu; metin kapilari ve
kapi mutasyonu, null numara kumesi, metin == kutular, kivrik kesme / numara
notu yok, on kayitli ikinci okuma sayilari (192 / 62 / 46), duzeltmeler son
metinde, `[??]` yok, Lewis cizimi metne dokulmedi, soluk isaret kararlari
(NH_4^+, Na^+, basili eksiler korunur), etiketler (100: TYT 51, MSU 49);
mukerrer ozeti, eski hat iki baski sayilari ve GUCLU tanimi, 36 hash
carpismasi, hash degeri yazilmadi, cevap farki basili anahtari degistirmez,
pozitif kontrol ve isaret korunur, indeksli Jaccard == dogrudan; 0063
kimlik / zincir / ASCII, ciftler olcumden turer (330, ayni hash'li 35 dahil),
guard (modern yoksa dokunmaz, T025_01 -> 329), durustluk (DELETE yok);
0064 kimlik / zincir / ASCII, dislama kurali, hedef 1306, durustluk.

`backend/tests/e2e/test_kim345tyt_ithal.py` (49): veri seti butunlugu,
yapisal kapilar, test ici sira / null numara, cevap kanali dagilimi, unite
baglantisi == 0062, kaynak sozlesmesi, arac dosyalari ASCII, pasif ithal
sozlesmesi, cozum uydurulmuyor, cikmis etiketleri, kutu / gorsel, olculen
bayrak capalari, mukerrer bayraklari == olcum; 9 yapisal + 12 on kontrol /
baglama mutasyonu.

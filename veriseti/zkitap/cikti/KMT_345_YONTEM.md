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

## Testler

`backend/tests/e2e/test_kim345tyt_veri.py` (27): hamdan birebir anahtar
turetme, A/B birebir, A/B farki / gereksiz fark karari / bicim disi /
numara kopmasi / simge farki / goz celiskisi mutasyonlari, kapsam, unite
araliklari (ayractan hemen sonra), kanal durustlugu, ASCII; harita hamdan
turer, migration == harita, zincir, kodlar, bant / rozet mutasyonu, sapka
katlamasi; kutu kapilari, kutu <-> cevap birebir, simge birincil capa,
ust bant simgesi reddi, kapi mutasyonu, ortme raporu.

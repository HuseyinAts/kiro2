# 345 2025 TYT Fizik Soru Bankasi -- uretim yontemi ve olcumler

Kesif ve plan: `FZT_345_KESIF_VE_PLAN.md`.

## 0. Kaynak ve tavani

FERNUS okuyucusunun 1920x1080 ekran goruntuleri, 368 sayfa (+ metin
katmani olmayan PDF). Kart cercevesi 10 ornek sayfada ayni: dikey cizgi
x 586-588 / 1331-1334, yatay y 42 / 1022 -> ic kart (589, 43, 1331, 1022).
Basili sayfa = dosya.

## 1. Cevap anahtari -- sayfa alti serit, iki okuma + glif + goz

Cikti: `345_2025_tyt_fizik_cevap_anahtari.json` (176 test, 1397 cevap).
Ham: `345_2025_tyt_fizik_ham_okumalar.json`. Tarama:
`345_2025_tyt_fizik_capa_taramasi.json`.

1. **Serit yeri pikselden:** kart y 840-975 murekkep bantlari; 342
   sayfada tam y 899-904 bandi. Soru sayfasi = bu bantta gri (doygunluk
   < 40) murekkep + en az bir okuyucu simgesi: 357 sayfa.
2. **Girdi sayisinin bagimsiz kanali:** serit fontu 6 px, girdiler arasi
   bosluk 3-5 px'te vadisiz; nokta sayimi da ince kenarlarda kopuyor
   (1530 / 1440, ikisi de tutarsiz). Bu yuzden sayim okuyucu simgesinden:
   stm345 tanimi (glif + lila disk + halka orani >= 0.6). Serit bandinin
   uzerinde (cy >= 890) 17 simge soru capasi DEGIL (seride binen okuyucu
   simgesi; soru metni yok) -> 1397.
3. **Iki okuma:** A 5x sayfa sirasi (60 montaj, 12 satir), B 7x TERS sira
   (80 montaj, 9 satir); 8'er ayri okuyucu; girdi sayisi soylenmedi.
   A 1397 girdi, B 1397 girdi; 714 sutunun 713'u birebir.
4. **Tek fark:** s277 R A '6.D', B '8.D?'. 10x gozle '6'; ayni sayfanin
   sol sutunu '4.B 5.A' -> +1 surekliligi. Karar '6.D' (A).
5. **Kapilar:** girdi sayisi == simge 714/714; numara ya +1 ya 1
   (1397/1397, 176 test); her test tek unite araliginda, sayfalari ardisik.
6. **Glif kanali:** sutun seridi okumadaki N'e N-1 en genis bosluktan
   bolunur, her girdinin son 7x12 px'i; en-yakin-komsu LOO 1380/1397.
   Gri maske doygunluk filtresiz ilk denemede 1211/1397 idi (mavi sus
   cubuklari ve seride binen simge bolmeyi kaydiriyordu).
7. **Goz (10x):** '?' tasiyan, A/B farkli ya da glifi tutmayan 70
   sutunun TUM girdileri; hepsi A okumasiyla ayni. Harf ayrimi: soluk sol
   cubuklu 'D' (orta centik yok) / 'B' (orta centik var).

Kanal dagilimi: iki_okuma+piksel 1252, +goz(10x) 88, +goz+tereddut 56,
farkli+goz+sureklilik 1. Harf: A 177, B 234, C 329, D 306, E 351.

## 2. Unite agaci (0060)

Cikti: `345_2025_tyt_fizik_konu_haritasi.json` (`fiz345tyt_harita.py`),
migration `0060_fzt345_konu_agaci.py` (o JSON'dan uretildi).

* 19 unite: icindekiler (dosya 3-4, gozle), basili baslangic sayfasi.
* Bagimsiz dogrulama: her baslangic sayfasinin ust bandi (kart y 20-145,
  gozle): 19/19 '1. bolum' rozeti + 'KAZANIM ODAKLI SORULAR' + orta bantta
  unite adi. Bant adi icindekiler adinin kelimeleriyle sirayla ortusur;
  tek fark s316 bandi 'ISIK AKISI VE AYDINLANMA' (icindekiler 'Isik Akisi -
  Aydinlanma - Golge Olaylari'): 've' baglaci yalniz bantta atlanir.
* Unite sonu sayfalari (sinirin oncesi) 'Orijinal Sorular', 'Karma
  Sorular', 'Gunluk Hayat Uygulamalari' bolumleridir; ayni unitenin
  parcasi.
* Her test tek unitenin sayfa araliginda (176/176).
* FIZ kokunun altinda `FIZ-345T25-Unn`, kok+1, subject_area 'FIZIK'.
  Yerel DB'de upgrade -> downgrade -> upgrade temiz (19 -> 0 -> 19).

## Testler

`backend/tests/e2e/test_fiz345tyt_veri.py` (21): hamdan birebir anahtar
turetme, tek farkin kaydi, A/B farki / gecersiz goz karari / bicim disi /
numara kopmasi / simge farki / goz celiskisi mutasyonlari, kapsam, unite
araliklari, kanal durustlugu, ASCII; Faz 2 ile +7: harita hamdan turer,
migration == harita, zincir, kodlar, bant adi / rozet mutasyonu, 've' kurali.

# 345 2025 Paragraf Sifir Risk Soru Bankasi -- uretim yontemi ve olcumler

Kaynak: `veriseti/zkitap/screenshots/345 2025 Paragraf Sifir Risk Soru Bankasi/`
(368 PNG; git disinda). Veri dosyalari
`veriseti/zkitap/cikti/345_2025_paragraf_*.json`. Faz 0 kesif fisi:
`PRG_345_KESIF.md`. Hat, 345 2025 AYT Turk Edebiyati hattinin
(`EDB_345_AYT_YONTEM.md`) kopyasidir; farklar asagida.

| arac | is |
|---|---|
| `scripts/kitap/prg345_tarama.py` | capa taramasi (simge, siyah basili numara, ara cizgi), dosya 1-355 |
| `scripts/kitap/prg345_kutu.py` | kirpim kutulari + ortak metin kutulari (koyu cerceveli baslik) + kapilar |
| `scripts/kitap/prg345_kirp.py` | soru + ortak metin gorselleri, ortme / kenar olcumu |
| `scripts/kitap/prg345_metin_harness.py` | transkripsiyon gruplari + kapilar (KAPI1-5) |
| `scripts/kitap/prg345_ithal.py` | PASIF ithal |
| `alembic 0054_prg345_kaynak_adi` | eski hat 8 satirin source_book'u ASCII ada |
| `alembic 0055_prg345_agac` | bolum agaci (TUR-345P25-B01..B07, TUR kokunun altinda) |

Hicbir soru cozulmedi; hicbir cevap uretilmedi.

## 0. Kaynak ve tavani

Tek yakalama (baska baski yok -> ortulen metin icin kurtarma kanali yok).
Sayfa karti `(589, 43) - (1331, 1020)` = 742x977. Basili sayfa numarasi =
dosya numarasi. Icerik 3-355, kitap sonu anahtar 356-368.

| kalem | deger | kanal |
|---|---|---|
| bolum ayraci | 7 (3, 63, 123, 183, 251, 283, 329) | bant okumasi + goz |
| test | 85 | bant + anahtar |
| soru | 1012 | anahtar (x2) + transkripsiyon (x2) |
| kapsam disi | '6. NUANS TESTI' s340-343 (acik uclu, anahtarda yok) | goz |

Kaynak cozunurlugu dusuk: 742 px genislikte `t`~`l` (or. 'testle' ->
'leslle'), `f`~`l`, `rn`~`m`, `r`+noktasiz i~`n` pikselde birlesiyor (bolum 4a).

## 1. Cevap anahtari -- kitap sonu, iki okuma + glif kanali

`345_2025_paragraf_cevap_anahtari.json`; ham okumalar
`345_2025_paragraf_ham_okumalar.json`.

| | okuma A | okuma B |
|---|---|---|
| olcek / montaj | 3x, yatay dilimler | 3x, tam sayfa |
| sira | sayfa sirasinda | TERS |
| girdi sayisi okuyucuya soylendi mi | hayir | hayir |

* A == B: 85/85 test satiri, 1012/1012 girdi numarasi, harf farki **0**.
* Okuyuculardan birinin '?' koydugu 34 girdi: 10x gozle bakildi, okuma
  dogrulandi (`iki_okuma(biri_tereddutlu)+goz`).
* Ucuncu kanal: tablo sayfalarinda (365-368) harf glifi en-yakin-komsu,
  birini-disarida-birak **441/441**. Kartli sayfalarda (356-364) hucre
  cizgileri ve tek sayfa acik renkli metin yuzunden glif segmentasyonu
  tutmadi (60 tokenin 54'u) -> orada piksel kanali yok.

Harf dagilimi A 175, B 173, C 240, D 232, E 192.

### 1a. Soru -> sayfa / sutun konumu

1. **Sayfa ust bandi** (353 sayfa, 3 okuyucu; `bant_okumasi`): bolum +
   test turu + tur ici sira. Yeni kosu = sira degisimi ya da kosunun
   turlerinde olmayan yeni basili tur; deneme sayfalari birlesir. 85
   kosunun 85'i anahtarin test sirasiyla ayni. OSYM Cikmis Sorular Ozel
   Denemesi sayfalarinin (242-250) bandinda bolum adi basilmaz.
2. **Sutun basina soru sayisi**: simge kanali; 8 sutunda dar numara
   (23L, 68R, 142L, 174R, 226R, 301L, 325L, 355L), 3 sutunda goz (4R=1,
   163L=2, 201L=2). 85/85 testin toplami anahtarla ayni.

## 2. Bolum agaci (0055)

7 bolum dugumu TUR kokunun altinda (kok+1), kodlar `TUR-345P25-Bnn`, adlar
Turkce (kaynakta `\u` kacisli). Her testin sayfalari tek bir bolumun
araliginda. Test -> bolum eslesmesi `konu_eslesme_duzeyi = bolum`.
Migration round-trip (upgrade -> downgrade -> upgrade) yerelde temiz.

## 3. Kirpim kutulari -- capa kanali, ortak metin

`345_2025_paragraf_kirpim_kutulari.json`; kurallar `prg345_kutu.py`
belgesinde. Kapi ihlali 0.

| olcu | deger |
|---|---|
| sutun kanali | numara 614, numara_alt 2 (4R, 201L; gozle dogru), simge 57 |
| kutusuz soru | 0 |
| kisa bant ust kurali | 8 kutu (gozle dogru) |
| numara diski ortulu kutu | 229 |
| sayfa alti | 904 (metin en cok y 902, alt bilgi logosu 905) |
| kesim metne degen | 105 (gozle: sayfa basligi / sure kutusu / kose susu) |

Faz 1'de bulunan ve duzeltilen kutu hatalari (her biri olculdu ya da
okuyucu bildirimiyle bulundu, gozle dogrulandi):

* **Logo kurali kaldirildi**: AYT hattindaki 'OSYM KOSESI' logo kurali
  turuncu kaynak etiketini ('2025 - MSU') logo sanip onceki sorunun
  etiketini sonraki kutuya koyuyordu.
* **Sayfa alti 896 -> 904**: sutun son sorusunun D/E sikki yarim
  kesiliyordu (grup 1 okumasi).
* **Doygun murekkep disi**: OSYM KOSESI'nin kirmizi dikey cerceve cizgisi
  cerceveli bolgede bos bant birakmiyor, kutu ustu ortak parcanin son iki
  satiri arasina dusuyordu (s154L; ortak metin okuyucusunun 'kesik son
  satir' bildirimi).
* **Sag sutun sol siniri <= 373**: OSYM KOSESI sayfalarinda (110, 139,
  146, 349) 'ara cizgi' cercevenin sol kenari olculuyor, soru numarasi
  kesiliyordu (okuyucular basili_no null bildirdi).
* **Ayrac bandi yalniz acik mavi**: renksiz sayim tam genislikli resmi /
  sayfa zeminini bant sanip sag kutuyu 17 px iceri itiyordu.

**Ortak metin**: koyu cerceveli baslik (`ortak_basliklari`) 29 + cercevesiz
yonerge 1 (s170L '18 - 20. sorularda ...', `ELLE_BASLIK`) = **30**; soru
kutusu ICINDE baslik 0. Ikinci kanal: sutun tavani ile ilk sahipli ust
arasinda > 40 px murekkep yalniz test ilk sayfasinda (168/168, tanitim
paneli) -- bu kanal simge maskesiyle kisalan ust kenari yuzunden kacan
s324/326/328 L basliklarini buldu.

## 4. Transkripsiyon

Kirpimlar 2x Lanczos; 25 grup (test sinirina hizali, ~40 soru), ayri
okuyucular; talimat `VeraFilm/p_metin_talimat.md` ('kitap ne yaziyorsa o';
soru cozme yok; anahtar gosterilmedi; bulanik parca '[bulanik metin]';
komsu icerik bildirimi). 30 ortak metin ayri okundu
(`VeraFilm/p_ortak_talimat.md`).

Kapilar (`prg345_metin_harness.py kapi`): KAPI1 her kirpim bir kez; KAPI2
basili no == test ici sira (gorunmeyen 2: T069_06 numarasi basilmamis,
T023_08 disk altinda; ikisinin capasi simgeden); KAPI3 bes sik dolu; KAPI4
toplam 1012; KAPI5 ortak metin 30, kapsam basi == kutudaki ilk soru.
**TUM KAPILAR YESIL.**

| olcu | deger |
|---|---|
| sekil_var | 16 |
| kaynak_kusuru | 143 (cogu okuyucu diski altinda kalan satir sonu harfleri ve iki adayli t~l okumalari) |
| cikmis etiketi | 84 (TYT 37, ALES 18, DGS 10, KPSS 8, MSU 7, AYT 4) |
| bulanik metin (tasarim) | 8 (Algisal Butunluk Testi) |
| duzeltme okumasi | 71 |

### 4a. Ikinci okuma -- once orneklem, sonra TAM

On kayit (olcumden ONCE, `345_2025_paragraf_ikinci_okuma.json`): 25 grubun
her birinden 8 soru (random.Random(20260925)) = 200, ilk okumayi gormeyen
7 okuyucu. Karar kurali: esasli hata oraninin tek yanli %95
Clopper-Pearson ust siniri <= %3 ise tam ikinci okuma yok.

* Orneklem: 176 ayni, 5 yalniz noktalama, 19 farkli; farklar 3x kesitle
  gozle hukme baglandi. Esasli ilk okuma hatasi **2** (T034_02 E
  'etkilidir' -> basili 'aktiftir'; T057_01 '1981' -> basili '1991'),
  ust sinir **%3.11 > %3** -> hatalar farkli grup ve turde -> kural geregi
  **TAM ikinci okuma**.
* Tam ikinci okuma: 1012 soru + 30 ortak metin, 25 + 1 okuyucu, rakam ve
  t~l icin ek uyari. 880 ayni, 53 yalniz noktalama (ilk okuma korundu),
  109 kayitta 138 kelime farki; her fark kirpimdan 3x kesitle (115 kesit,
  12 montaj) gozle hukme baglandi:

| hukum | kayit |
|---|---|
| ilk okuma dogru | 33 |
| ikinci okuma dogru -> ilk okuma duzeltildi | 48 |
| iki aday da piksele uyuyor -> ilk korundu, iki aday `kaynak_kusuru`na | 34 |
| bicim (tablo yonu, `</u>` boslugu) | 23 |

Duzeltilen esasli ilk okuma hatalari: T009_03 'yonetimlerine' -> basili
'yontemlerine', T034_02, T057_01, T036_06 (alti cizili kapsam 'olan'da
biter). Digerleri: kitabin basili yazimi / eki ilk okumada 'duzeltilmis'
ya da atlanmis (noktrun, gercaklesebilmesi, pisikolojik, billur,
kullanmasini ...) ve simge altinda gorunmeyen harf tamamlanmis (endustriy,
ferd, dunya ...). Son karsilastirmada kalan 92 farkin hepsi hukumlu.

## 5. Ortme ve kenar

`345_2025_paragraf_ortme_olcumu.json`: diskin halkasinda kitap murekkebi
olan **250** soru `okuyucu_diski_ortme` bayragi tasir (kurtarma kanali
yok). Komsu sutunun simgesi satir sonu harflerini ortuyor; okuyucular
yalniz gorunen harfleri yazdi ve `kaynak_kusuru`na not dustu. Kenar kapisi
(notr murekkep) **0**.

## 6. Mukerrer, eski hat, kitap ici tekrar

`345_2025_paragraf_mukerrer_adaylari.json` (DB TURKCE 3105 + eski hat 8):

* GUCLU aday (Jaccard >= 0.75 ve >= 3 sik birebir) **11** (10 soru):
  OSYM 2025 TYT 5, eski hat 4, Cap 1, Aromat 1. OSYM eslesmelerinde harf
  farkli olan 4'unde kitap sik sirasini degistirmis, dogru sikkin METNI
  iki tarafta ayni -> celiski yok.
* **Eski hat 8 satir** (`eski_hat_satirlari`): 8'i de ayni basili sayfadaki
  soruyla eslesiyor (Jaccard 0.65-0.97; eski metinde OCR hatalari) ve
  8'inin cevabi basili anahtarla AYNI -> cevap duzeltmesi yok. 0054 yalniz
  source_book yazimini ASCII'ye cevirir. Yeni satirlar `eski_hat_ikizi`
  isareti tasir.
* **Kitap ici tekrar**: T022_20 (s146) ve T038_13 (deneme) ayni cikmis
  soru; ikisi de ithal edilir (`kitap_ici_tekrar`, id kirpim adiyla).
* **Baska kitapta ayni hash**: T038_03 (2021 AYT cikmisi) 345 AYT Turk
  Edebiyati'nda (EDB345AYT-T093_09) ayni metin + sikler + cevapla zaten
  var -> sozlesme geregi dokunulmadi; ithal **1011** satir.

## 7. Alanlar ve kaynaklari

EDB ile ayni; farklar: `konu_eslesme_duzeyi = bolum`, `test_adi`,
`eski_hat_ikizi`, `kitap_ici_tekrar_ile`, `bulanik_metin_tasarim` bayragi.
`subject_area = TURKCE`, `exam_type = TYT`, `grade_level = 12`.

## 8. Bilinen borc / sahip karari bekleyen

* SAHIP KARARI UYGULANDI (25 Eyl, 0056): eski hat 8 satir PASIF
  (silinmedi; 58044c42'nin `subject_area = SOSYAL` etiketi pasif satirda
  kaldi). Yeni ithalin 1010 satiri toplu beta onayiyla AKTIF
  (`auto_judged_high`, `human_verified` degil; `bireysel_denetim_yapildi`
  false). T038_13 (T022_20 ile ayni soru_hash) aktif benzersizlik kisiti
  geregi PASIF kaldi. Kapi yuku olculdu: sik_bos 0, gorunen `[??]` 0,
  aktif satirlarla hash cakismasi 0. Geri alma: gunluk tablosu
  `prg345_beta_onay_gunlugu_0056`; downgrade/upgrade yerel DB'de denendi.
* Cozumler kitapta yok; `explanation` bos.
* Ortak metinli sorularin gorseli yalniz soru kirpimi (parca gorselde yok).
* Cozunurluk: iki adayli t~l / rn~m okumalari `kaynak_kusuru` notunda.
* Ithal PASIF yapildi; aktiflestirme 0056 ile (yukarida).

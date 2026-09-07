# SOS/TYT Gocu S1 -- Kor Crop Okuma Kaniti (2026-09-07)

Plan: `docs/superpowers/plans/2026-08-20-mat-tyt-goc-revize.md` (S239) boru hattinin ucuncu dilimi.
Gerekce: SS10.76'dan sonra TYT denemesini kapatan TEK eksik SOS'tu (0/20). Onceki turlar:
MAT R1 (448), MAT R2 (509), TURKCE T1 (919).

**Sonuc: TYT denemesi artik KURULUYOR** -- iddia degil olcum: `generate-mock`'un kullandigi
`YksBellCurveAssembler.assemble_test` canli havuzlara karsi kosuldu, dort brans da kotasini
doldurdu (40+20+40+20 = 120).

## Onkosullar (bu turda yapildi)

* **Seed'e KOK modu** (`y11_konu_seed.py --kok`): kaynakta `SOS`/`SOC0*` kodlari EBEVEYNSIZ
  (kok) duruyor ve canlida hic yoktu. Canlinin kendisi de karisik -- `TYT-KIM-01`, `KIM.ASI`
  gibi satirlar zaten kok. Uydurma ebeveyn takmak (SOS'u TAR altina) konu agacini YANLIS
  yapardi. Kok modunda ebeveyn invaryant sorgusu da doner: eski sorgu
  (`parent_id IS DISTINCT FROM NULL`) her satiri yanlis sayar, seed hic yazamazdi -- bu
  gerileme icin ayri bekci var. Iki saf yardimci + 5 test (`test_y11_konu_seed.py`).
* Seed sonucu: 17 kod (TAR01-05, TYT-TAR-01/02 ebeveyn TAR; COG01-05, TYT-COG-01/02 ebeveyn
  COG; SOS, SOC02, SOC03 KOK), `topic_hierarchy` 52 -> 69. Not: `exams.py`'nin
  `SUBJECT_MAPPING["SOS"]` listesi zaten canlida OLMAYAN `SOS`/`SOC01` kodlarini bekliyordu;
  seed uydurma degil, kodun varsaydigi boslugu kapatiyor.
* **Secici** (`y11_aday_uret.py`): `DILIMLER["sos_tyt"]`. Bu dilim TEK DERS DEGIL, TYT'nin
  SOS BOLUMU -- `generate-mock` bransi {sosyal,tarih,cografya,felsefe,din} kumesiyle esliyor;
  ders basina ayri dilim bolumu yapay bolerdi. Konu kapsami suzgeci TUR'daki gerekceyle:
  temiz dilimde 10 soru FIZ/KIM/TUR/GEN konularina bagli (etiket hatasi).

## Evren -- huni (kiro2_temp), OLCULDU

```
TYT toplam (TARIH+SOSYAL+COGRAFYA)   6816   (3939 + 1494 + 1383)
is_active                            5286
+auto_judged_high                    2452
+_qN.png + anahtar A-E + option_e    1052
+konu kapsami (TAR/COG/SOS aileleri) 1042   = ham aday
konu basi tavan 50 sonrasi            576   = ADAY (19 konu)
```

Havuz TUKENMEDI: secici tekrar kosumunda 257 aday daha hazir (8 konu) -- TUR'un aksine ikinci
tur mumkun.

## Yontem

* Orneklem = tavanin sectigi kumenin TAMAMI: **576/576 crop okundu**, 20 ajan x 30 (son dilim 6),
  2 dalga, acilamayan 0, dusen ajan 0. Her ajan `read_multiple_files` ile 10'arli gorseli acti.
* Sizinti olcutu oncekilerle ayni + sosyal bilimlere ozgu ek: kronoloji tablosu / kavram
  haritasi / ders metni; ve **coklu kirpim** (tek gorselde birden fazla bagimsiz soru).
* AYT sutunu SOS icin yeniden tanimlandi (Tarih / Cografya / Felsefe grubu ayri ayri).

## Sonuc

```
aday                           576  (19 konu)
sizdiran (SIZINTI=EVET)         55  (%9,55)  -- simdiye kadarki EN YUKSEK
AYT=EVET                        69  (%11,98)
AYT=KARARSIZ                    42  -> at 10 / tut 25 / zaten sizdiran 7
metin katmani bozuk              1  (orneklem cozumunde bulundu)
sizdiran & AYT kesisimi          5
atilan BIRLESIM                130
GOC KUMESI                     446
```

Ham kayit: `_kor_okuma_sos_ham.tsv` (576). Listeler: `_sos_sizdiran.txt` (55), `_sos_ayt.txt`
(79 = 69 + 10), `_sos_kararsiz_karar.tsv` (42), `_sos_metin_bozuk.tsv` (1), nihai
`y11_sos_kumesi.txt` (446). `y11_sos_crop.tsv` (host yollari) commit DISI.

### Sizinti KITAP duzeyinde toplaniyor -- ve bir kitap %100 sizdiriyor

```
Bilgi Sarmal Tyt Sosyal Bilimler Video Ders Kitabi   17 aday /  17 sizdiran  (%100)
Aromat Tyt Sosyal Bilimler Model Sorular 2023        32 aday /  15 sizdiran  (%47)
Bilgi Sarmali Ayt Tarih Soru Bankasi 2021 2022       17 aday /   5 sizdiran  (%29)
Bilgi Sarmal Ayt Tarih Soru Bankasi 2020 2021        26 aday /   4 sizdiran  (%15)
--- karsilastirma ---
Esen Tyt Tarih Soru Bankasi                          47 aday /   0 sizdiran  (%0)
Cap Tyt Tarih Soru Bankasi 2023 2024                 83 aday /   1 sizdiran  (%1)
```

"Video Ders Kitabi" adi zaten uyariyordu: kitap bastan sona konu anlatimi. **Secici kitap
adina bakmiyor**; bu tur kaynaklar her turda ayni maliyeti uretiyor. TUR turunda da ayni
desen olculmustu (`Sure Paragraf Gunlukleri` 9/11). Kitap-duzeyi kirmizi liste artik iki turda
ust uste kaniti olan bir eksik.

Sizinti turleri (kaba siniflandirma, 55): konu anlatimi / bilgi notu 27, coklu-eksik kirpim 14,
cozum/cevap ibaresi 9, diger 5. **Coklu kirpim ilk kez bu buyuklukte** -- sosyal bilimler
kitaplarinda sorular kisa oldugu icin bir kirpima 2-3 soru sigiyor.

### KARARSIZ: MAT'taki olcut SOS'ta CALISMIYOR

MAT R2'de kararsizlik konu ADIYLA cozulmustu ("2. derece esitsizlik" = 11. sinif, kesin).
SOS'ta bu imkansiz: TYT ve AYT sosyal mufredati AYNI konu basliklarini paylasiyor (Osmanli
kurumlari, Ataturk ilkeleri, iklim...) ve yalniz DERINLIK degisiyor. 42 kararsizin cogu bu
turden. Onun icin karar iki OLCULEBILIR sinyale baglandi:

1. **OSYM'nin kendi damgasi.** 28 karma-kitap kirpimi, yalniz "sinav-yil rozeti var mi"
   sorusuyla IKINCI ve BAGIMSIZ bir gecisten geciriIdi: 3 AYT damgasi bulundu ve bunlar kor
   okumanin bagimsizca bildirdigi 3 damgayla BIREBIR ayni cikti (capraz dogrulama).
2. **Kaynak kitap saf AYT mi.** TUR turunda olculmustu: saf AYT kitabindan gelen 4 adayin
   3'u icerikte de AYT idi.

Kalan 25 TUT edildi: damga yok, kitap TYT/karma, ve kor okuyucu "AYT'ye ozgu derinlik" GORMEDI
(EVET degil KARARSIZ dedi). Tutucu davranip 42'sini birden atmak, TYT'de gecerli 25 soruyu
gereksiz yere elerdi -- ve MAT'takinin aksine burada "atmak" bedava degil, cunku ayni konu
basligi iki mufredatta da var.

### Kaynak metadata'si crop klasoruyle celisiyor (%2,8) -- karar klasore baglandi

`y11_sos_crop.tsv`'nin `kitap` sutunu (`source_book`) ile gorselin geldigi klasor 576 satirin
**16'sinda** uyusmuyor (TUR'da 7/1001). Ornek: `f1969d9d` metadata'da "Esen Aps Tyt Ayt Tarih",
gercekte `Esen_Tyt_Tarih_Soru_Bankasi`. Kor okuma GORSELI okudugu icin okumalar etkilenmiyor,
ama kitap sinyaline dayanan KARAR etkilenirdi. Kural klasore cevrildi ve **yeniden kosuldu:
10 AT / 25 TUT ve nihai 446 DEGISMEDI** -- yani bu turda karar degistirmemis, ama olculmeden
guvenilemezdi. (Yan etki: kalan kumenin "saf AYT kitabi" payi metadata'ya gore 101, klasore
gore 54; SS10.76'daki TUR kitap tablosu da `kitap` sutununa dayaniyor, %0,7 paylik ayni sapma
orada da var.)

### Orneklem: 10 soru COZULDU, 10/10 anahtar uyumlu -- ama METIN katmaninda bir kusur cikti

Anahtarlarin hepsi benim cozumumle uyustu. Buna karsilik `fbb347a9`'un GOVDESI kendisiyle
celisiyor: *"Musluman olmayanlar her turlu devlet hizmetine girerken, Musluman olmayanlarin
kamu hizmetlerinde calistirilmasina izin verilmemistir"* (ilk oge "Muslumanlar" olmali).
**Gorsel saglam; bozulma cikarilan metinde.**

Bu yapisal bir bosluk: kor crop okuma GORSELI okur, servis edilen ise `question_text`. Yani bu
kusur sinifini kor okuma ILKESEL OLARAK goremez. Sezgisel bir tarama denendi (447 sorunun
tamami: kisa govde, dengesiz parantez, bos/mukerrer sik, tekrar eden 4-kelimelik obek, ham
LaTeX): 16 tekrar + 8 LaTeX isareti cikti, **tamami yanlis pozitif** (tekrarlar mesru, LaTeX
zaten render ediliyor). Yani sezgisel tarama bu katmani OLCEMIYOR; kusuru yakalayan tek adim
orneklemin elle cozulmesi oldu. Oran iddia edilmiyor: 10 orneklemde 1 -- kucuk orneklem, ama
katman boslugu kesin. Soru tutucu bicimde atildi (446).

## Prova ve kalici yazim

```
TABAN                      5350 | 5350 | 5350 | 5350 | kapi 4579
PROVA (geri alindi)        447 satir, yetim 0, damgali 447, sapma [], kural_sayimi hepsi 447
                           rollback: damgali 0, taban degismedi
                           (metin kusuru sonradan bulundu -> kume 447 -> 446)
KALICI                     5796 (5350+446) | damgali 446 | icerigi olmayan 0 | kapi 4579 degismedi
kume dogrulama             y11_sos_kumesi.txt ile canli damgali parti BIREBIR AYNI (446/446)
subject_area/exam_type     TARIH/TYT 291, COGRAFYA/TYT 123, SOSYAL/TYT 32  (baska deger yok)
A1 konu kirilimi           19 konu: TAR01 44, SOS 43, TYT-TAR-01 43, TAR 43, TAR02 42,
                           TYT-TAR-02 40, TAR04 40, TAR05 21, TYT-COG-01 21, COG03 21,
                           COG02 18, TYT-COG-02 17, COG01 13, COG 13, COG05 9, TAR03 7,
                           COG04 7, SOC02 2, SOC03 2
gorsel hatti               40/40 host'ta var (Python isfile)
idempotens                 secici tekrar: capraz-DB elenen 446 = 446; SECILEN 257 (havuz surer)
```

## FAZ E terfi (yedekli)

On-simulasyon: 446'nin 380'i kapiya girer (2 `demoted_at`, 56 `tier1_page_inline`/`tier1b`;
bayraksiz 0, fallback 0, AI-onaysiz 0). Yedek:
`question_statistics_terfi_yedek_sos_20260907` (446 satir, eski durum `pending`).

```
kapi   4579 -> 4959   (+380, simulasyonla BIREBIR; kapida SOS partisi 380)
ES     4959 (eklenen 380, silinen 0) -- kiro2-backend konteynerinden
```

Geri alma:
```sql
UPDATE question_statistics qs SET quality_review_status = y.eski
FROM question_statistics_terfi_yedek_sos_20260907 y WHERE y.id = qs.id;
REFRESH MATERIALIZED VIEW mv_safe_for_beta;
-- sonra konteynerde ES senkronu
```

## generate-mock: ARTIK KURULUYOR (endpoint mantigi kosuldu)

SQL havuz sayimi yetmez -- asil soru assembler'in kotayi doldurup dolduramadigiydi (zorluk
dagilimi carpiksa daha az donebilirdi). `exams.py`'nin kullandigi AYNI fonksiyon canli
havuzlara karsi kosuldu:

```
brans | havuz | kota | assembler dondurdu | durum
TUR   |   919 |   40 |                 40 | TAMAM
SOS   |   446 |   20 |                 20 | TAMAM
MAT   |   900 |   40 |                 40 | TAMAM
FEN   |  3531 |   20 |                 20 | TAMAM
TOPLAM 120/120 -> TYT denemesi KURULUYOR
```

Uyari: bu, PR #181'deki `exams.py` mantigi. master'daki surum hala brans-koru fallback'li eski
surum; 409 -> 120 gecisi kullaniciya PR #181 merge edilince yansir.

## Canli son durum

```
question_bank  5796   (KIMYA 3531 + MAT 900 + TURKCE 919 + SOS 446)
kapi           4959   ES 4959 (birebir)
topic_hierarchy   69  (52 + 17)
```

## Acik kalan

* **Kitap-duzeyi kirmizi liste**: iki turda ust uste kanitlandi (SOS'ta bir kitap %100, TUR'da
  %82). Secici hala kitap adina bakmiyor.
* **Metin katmani denetimi**: kor okumanin goremedigi kusur sinifi. Sezgisel tarama ise
  yaramadi; gercek cozum muhtemelen gorsel-metin karsilastirmasi (OCR ciktisini gorselle
  eslestiren ayri bir gecis) -- ayri is.
* `source_book` metadata'si ile crop klasoru %2,8 uyusmuyor: veri hattinda ayri bir kusur.
* SOS havuzu surer: 257 aday hazir (R2 mumkun).
* FEN kotasini KIMYA tek basina karsiliyor (BIY/FIZ canlida 0) -- deneme "Fen" bolumu %100
  kimya olur. Blueprint'te alt-brans kotasi yok; urun karari.

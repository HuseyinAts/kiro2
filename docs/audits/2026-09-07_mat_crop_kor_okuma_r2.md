# MAT/TYT Gocu R2 -- Kor Crop Okuma Kaniti (2026-09-07)

Plan: `docs/superpowers/plans/2026-08-20-mat-tyt-goc-revize.md` (S239, R1: 586 aday -> 448 yazildi -> 391 kaldi).
R2 ayni planin ikinci turu: kalan ~3.500 kapsanan MAT sorusundan bir dilim daha.

## Yontem (R1 ile ayni, iki ek)

* Evren: `kiro2_temp` MAT/TYT dilimi (`y11_aday_uret.py --dilim mat_tyt`), konu basina 50 tavan.
* **EK 1 -- AYT konu suzgeci** (`AYT_KONU_KODLARI`): S239'da icerik okunarak bulunan 6 AYT kodu
  (TRV, INT, LMT, LOG, TRG, DIZ) secici duzeyinde eleniyor; 939 aday dustu.
* **EK 2 -- kirmizi liste** (`--haric-dosya`): R1'de reddedilen 195 id (16 sizdiran + 26 metin-AYT +
  96 konu-AYT + 57 TRG/DIZ) canlida OLMADIGI icin capraz-DB elemesi onlari goremezdi; artik dosyadan
  eleniyor. R1 aday listesinin tamami (586) da kirmizi listede: R2 ile R1 kesisimi = 0, yapisal.
* Orneklem = evrenin TAMAMI, kirpma yok: **622/622 crop okundu**, 21 ajan x 30 (son dilim 22),
  acilamayan 0, dusen ajan 0. Her ajan `read_multiple_files` ile 10'arli gruplar halinde gorseli
  gercekten acti.
* Karar olcutu (sizinti): kenar/alt/ust seritte basili anahtar, cozum metni/"Cozum" blogu, bilgi notu /
  "Bilsen Yeter" aciklama kutusu, dogru sikki isaretleyen iz, gorselin soru DEGIL cozum/aciklama olmasi.
  Kararsiz -> EVET.
* **R2'ye ozgu ikinci sutun -- AYT icerik yargisi:** ajan her crop icin "TYT mufredati disinda mi"
  sorusunu da yanitladi (EVET/HAYIR/KARARSIZ). Gerekce: S239 dersi -- `exam_type` etiketi guvenilmez
  (%17,6 AYT), yargi icerikte. Konu kodu suzgeci AYT KONULARINI eler ama TYT konusu altindaki
  AYT-duzeyi soruyu (parabol, 2. derece esitsizlik, bagimsiz olaylar...) goremez.

## Sonuc

```
aday                          622  (13 konu)
sizdiran (SIZINTI=EVET)        34  (%5,47)
AYT=EVET                       66  (%10,6)
AYT=KARARSIZ                   47  -> icerik okunarak: 18 AT / 25 TUT / 4 zaten sizdiran
atilan BIRLESIM               113
GOC KUMESI                    509
```

Ham kayit: `backend/scripts/quality/_kor_okuma_r2_ham.tsv` (622 satir: id, sizinti, AYT, kanit).
Listeler: `_mat_r2_sizdiran.txt` (34), `_mat_r2_ayt.txt` (84 = 66 + 18), `_mat_r2_kararsiz_karar.tsv` (47),
nihai `y11_mat_kumesi_r2.txt` (509).

### Sizinti orani R1'in IKI KATI -- ve modu farkli

R1 (MAT, S239): %2,73, mod = kenar seridi anahtar listesi. R2: **%5,47**, mod cogunlukla
**ders-kitabi duzeni**: "BILGI NOTU" / "BILSEN YETER" / "Cozum" bloklari (34'un ~20'si), kenar seridi
anahtar (~9), crop'un soru degil cozum sayfasi olmasi (~5). Bu, S239'un KIMYA'da gordugu modla
(%5,96, cozumlu ornek blogu) ayni. Sebep: R2 dilimi R1'den farkli kitaplara uzaniyor (65 kitap;
"Matematigin Ilaci", "Bilsen Yeter" tarzi konu-anlatimli soru bankalari). **Oran dilimden dilime
degisiyor; R1'in %2,73'unu genellemek 17 tahmin ederdi, gercek 34.**

### KARARSIZ kararlari (icerik okunarak, kural belgeli)

TUT (25): 2. derece DENKLEM kok-katsayi/diskriminant (10. sinif, OSYM TYT listesinde) x15; deneme ile
cozulen basit esitsizlik x2; fonksiyon oteleme (10. sinif) x2; kok-katsayi/uslu denklem x2;
C(n,k) toplam ozdesligi = alt kume sayisi x2; kombinasyon (AYT rozeti konuyu degistirmez) x2.
AT (18): 2. derece / rasyonel ESITSIZLIK isaret tablosu (11. sinif) x8; bagimsiz olaylar / tekrarli
deneme (11. sinif) x4; trigonometri (cot x) x1; 3+. derece polinom grafik/kok iliskisi x4; geometrik
seri yorumu x1. Kararsiz kalan sinir durumlari TUTUCU yonde (AT) cozuldu -- servis edilmeyen TYT
sorusu bedava, servis edilen AYT sorusu ogrenciye gider.

## Prova ve kalici yazim

```
TABAN                      3922 | 3922 | 3922 | 3922 | kapi 3560
PROVA (geri alindi)        yazilan 4x509, yetim 0, damgali 509, sapma [], kural_sayimi hepsi 509
rollback                   damgali 0, taban degismedi
ORNEKLEM (10 soru COZULDU) 10/10 dogru anahtar (10. soru grafikli: grafik okunup dogrulandi)
KALICI                     4431 | damgali 509 | icerigi olmayan 0 | kapi 3560 (degismedi)
A1 konu kirilimi           13 konu / 509 soru (kabul >=5 / >=40); AYT konu kodu 0
gorsel hatti               40/40 host'ta var (Python isfile; bash [ -f ] DEGIL -- NFC/NFD)
idempotens                 secici tekrar: capraz-DB elenen 900 = 391 + 509
```

## FAZ E terfi (S239 politikasi: once kor okut, sonra terfi ettir)

Onkosul ONCEDEN simule edildi: 509'un 446'si kapiya girer (2 demoted_at, 22 tier1_page_inline,
47 bes bayraktan hicbiri yok). Yedek: `question_statistics_terfi_yedek_r2_20260907` (509 satir, eski
durum `pending`). `pending -> auto_judged_high` + `REFRESH MATERIALIZED VIEW mv_safe_for_beta`:

```
kapi   3560 -> 4006   (+446, tahmin birebir tuttu)
ES     4006 (eklenen 446, silinen 0) -- kiro2-backend konteynerinden kosuldu
MAT kapida: R1 351 + R2 446 = 797
```

Host'tan ES senkronu KOSMUYOR: host istemcisi 9.2.1, sunucu 8.11.0 (HEAD -> 400) ve .env docker
hostname'i tasiyor; konteyner icindeki istemci esliyor. Nightly beat de konteynerde kosuyor.

Geri alma:
```sql
UPDATE question_statistics qs SET quality_review_status = y.eski
FROM question_statistics_terfi_yedek_r2_20260907 y WHERE y.id = qs.id;
REFRESH MATERIALIZED VIEW mv_safe_for_beta;
-- sonra konteynerde ES senkronu
```

## Canli son durum

```
question_bank  4431   (KIMYA 3531 + MAT 900)
kapi           4006   ES 4006 (birebir)
```

## Acik kalan

* Kalan kapsanan MAT sorusu: secici tekrar kosumunda tavan oncesi 2.582 aday (10 konu). Kor okuma
  kapasitesi bu turda 622 crop / 21 ajan / ~30 dk. Ayni yontemle R3 mumkun.
* TUR / SOS / BIY hala canlida 0 -- TYT denemesi (SS10.73 onkosulu) icin ayri dilimler gerekiyor;
  `DILIMLER`'e yeni ders eklemek + canli `topic_hierarchy`'ye o dersin konu kodlarini seed etmek
  (`y11_konu_seed.py`) gerekir. Bu planin kapsami degil.
* Ayni OSYM sorusunun farkli kitaplardan 3 kopyasi (2021/AYT proje ekibi) `soru_hash` ile
  yakalanmadi -- metin farkli. Icerik-duzeyi dedup ayri is.

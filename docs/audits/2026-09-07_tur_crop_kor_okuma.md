# TURKCE/TYT Gocu T1 -- Kor Crop Okuma Kaniti (2026-09-07)

Plan: `docs/superpowers/plans/2026-08-20-mat-tyt-goc-revize.md` (S239) boru hattinin ilk MAT-DISI dilimi.
Gerekce: SS10.73 -- `generate-mock` TYT denemesi TUR 0/40 yuzunden 409 veriyordu; TYT denemesini acan
dilim bu. Onceki turlar: MAT R1 (448), R2 (509, `2026-09-07_mat_crop_kor_okuma_r2.md`).

## Onkosullar (bu turda yapildi)

* **Konu seed** (`y11_konu_seed.py`, artik ders-agnostik: `--ders --ebeveyn --kod-deseni --yaz-level`):
  canli `topic_hierarchy`'de TUR altina 7 kod eklendi (TUR.ANL, TUR.DIL, TUR.PAR, TUR.YAZ,
  TYT-TR-01/02/03), toplam 45 -> 52. Kaynak kodlari `kiro2_temp`'ten, ebeveyn canli TUR
  (`f5b7f58c`).
* **Secici** (`y11_aday_uret.py`): `DILIMLER["tur_tyt"]` eklendi (exam_type TYT + subject_area
  TURKCE + auto_judged_high + `_qN.png` + anahtar A-E + option_e dolu + konu kodu TUR/TUR.%/TYT-TR-%).
* **Secici hatasi bulundu ve duzeltildi -- UUID drift:** kapsam suzgeci konu ID'siyle calisiyordu;
  level-1 kokler (MAT, TUR) temp ile canlida AYNI KOD, FARKLI ID tasidigi icin TUR kokundeki 673 soru
  "kapsam disi" diye eleniyordu. `kapsam_suz()` artik KODLA olcuyor (yukleyicinin `_canli_topic_id`
  ile ayni anahtar). Kontrol kolu MAT'ta: kapsam disi 871 -> 386, diger tum sayimlar DEGISMEDI.
  Bekci: `test_kapsam_kodla_olculur_uuid_drift_yanlis_negatif_vermez`, `test_tur_dilimi_konu_kapsamiyla_sinirli`
  (`test_y11_aday_uret.py` 10 -> 12).

## Evren -- huni (kiro2_temp, TURKCE/TYT), OLCULDU

```
toplam                         18388
is_active                      14776
+quality auto_judged_high       3392   (pending 6578, unverified 4609, bronze_clean 197 disarida)
+gorsel _qN.png                 1029   (2345 "diger" desen, 18 null disarida)
+anahtar A-E, option_e dolu     1029
+konu kapsami TUR/TYT-TR        1001   = ADAY (tavan devreye girmedi)
```

**Havuz bu turda TUKENDI:** secici tekrar kosumunda capraz-DB elenen 919 = yazilan 919, kirmizi liste
1001, SECILEN 0. Bir sonraki TUR buyumesi suzgec gevsetmeyi gerektirir (pending/unverified kalite
durumu ya da `_qN.png` disi gorsel deseni) -- kalite politikasi karari, bu planin kapsami degil.

## Yontem (R2 ile ayni)

* Orneklem = evrenin TAMAMI: **1001/1001 crop okundu**, 34 ajan x 30 (son dilim 11), 3 dalga,
  acilamayan 0, dusen ajan 0 (~88k token/ajan). Her ajan `read_multiple_files` ile 10'arli gorseli acti.
* Sizinti olcutu R2 ile ayni + Turkce kitaplarina ozgu ek: gorselin KONU ANLATIMI / "Bilsen Yeter" /
  "Hap Bilgi" / "Dikkat" / "Sicak Bolge" / sozluk sayfasi olmasi; siksiz alistirma; eksik kirpim
  (parca/dizeler yok). Kararsiz -> EVET.
* AYT sutunu Turkce icin yeniden tanimlandi: AYT Edebiyat = sair/yazar/eser bilgisi, akim/donem,
  nazim bicimi/olcu, edebi sanat TANIMI, tur tarihi, halk/divan edebiyati. TYT = paragraf, sozcuk/cumle
  anlami, dil bilgisi, soz sanatinin cumlede TANINMASI.
* Dalga 1'in 360 satiri baglam sikismasi yuzunden bellekten dustu; ajan transkriptlerinden
  (`subagents/*.jsonl`, son assistant mesaji) programatik olarak geri cikarildi ve
  `y11_tur_crop.tsv` sirasiyla BIREBIR dogrulandi (`tur_ham_kontrol.py`: sira, benzersizlik, bicim).

## Sonuc

```
aday                          1001  (8 konu)
sizdiran (SIZINTI=EVET)         78  (%7,79)   -- simdiye kadarki EN YUKSEK oran
AYT=EVET                         3
AYT=KARARSIZ                     3  -> gorsel bizzat acildi: 2 TUT (paragraf becerisi) / 1 zaten sizdiran
anahtar supheli (orneklem)       1  -> tutucu AT
atilan BIRLESIM                 82
GOC KUMESI                     919
```

Ham kayit: `_kor_okuma_tur_ham.tsv` (1001). Listeler: `_tur_sizdiran.txt` (78), `_tur_ayt.txt` (3),
`_tur_kararsiz_karar.tsv` (3), `_tur_anahtar_supheli.tsv` (1), nihai `y11_tur_kumesi.txt` (919).
`y11_tur_crop.tsv` (host yollari) R2'deki gibi commit DISI.

### Sizinti modu: ders-kitabi duzeni baskin (kaba anahtar-kelime sinifi, 78)

konu anlatimi / bilgi notu 35, cozum metni / "Cevap:" ibaresi 30, soru degil / eksik kirpim 6, kenar
seridi anahtar 4, renkli sik isareti (OSYM cikmis soru cozumlu baski) 2, diger 1. R2'nin "BILSEN YETER"
modu Turkce'de daha da baskin; kenar-seridi modu (R1) neredeyse yok.

Kitap duzeyi (aday / sizdiran): `Sure Tyt Paragraf Gunlukleri 2023` 11 / 9; `Aromat Tyt Turkce Model
Sorular` 14 / 6; `Bilgi Sarmal Tyt Ayt Dil Bilgisi` (iki baski) 55 / 16; `Pes Sozcuk ve Cumlede Anlam`
7 / 3. Buna karsilik en buyuk kaynak `Edebiyat Sokagi Paragraf ileri Duzey` 357 / 5 (%1,4). **Oran
kitaba bagli; dilim ortalamasi tek basina yaniltir.** Gelecek turlar icin kitap-duzeyi kirmizi liste
adayi: yukaridaki ilk uc.

### exam_type etiketi (S239 dersi, Turkce'de yeniden)

AYT adli kitaptan 120 aday geldi (cogu "Tyt Ayt Dil Bilgisi/Paragraf" gibi cift amacli). Saf AYT
Edebiyat kitabindan 4 aday: 3'u icerik okumasinda AYT=EVET (yazar-eser eslestirme, Bati tiyatrosu
tarihi, biyografi turleri/tezkire), 1'i paragraf becerisi (TUT). Yani temp'teki `exam_type='TYT'`
etiketi Turkce'de de kitap kaynagini yansitmiyor; yargi icerikte.

### KARARSIZ (2 TUT, gorsel acilarak)

* `b2e014d3` (345 TYT Turkce): Tanzimat/Servetifunun icerikli parca ama soru "parcadan hangisine
  ulasilabilir" -- dis bilgi gerekmiyor.
* `0a0fd6a6` (Vaf AYT TDE): biyografi tanimi parcada verili, "ulasilamaz" (I-V oncul) sorusu.

### Orneklem: 10 soru COZULDU, 9/10 anahtarla uyumlu, 1 supheli

`756f59e5` ("catisi bakimindan farkli"): A/C/D/E gecisli-etken, yalniz B (`ortaya cikmisti`) gecissiz;
kitap anahtari A. Gorsel acilip OCR degil basim dogrulandi. Karar: tutucu AT (919 = 920 - 1). Bu,
kaynak anahtarlarinin da hata tasiyabildiginin ilk somut ornegi -- icerik-duzeyi anahtar denetimi
(sympy benzeri bir "cozucu" Turkce icin yok) ayri is.

## Prova ve kalici yazim

```
TABAN                      4431 | 4431 | 4431 | 4431 | kapi 4006
PROVA (geri alindi)        920 -> supheli anahtar dusuldu -> 919; yetim 0, damgali 919, sapma [],
                           kural_sayimi hepsi 919; rollback: damgali 0, taban degismedi
KALICI                     5350 (4431+919) | damgali 919 | icerigi olmayan 0 | kapi 4006 (degismedi)
subject_area/exam_type     TURKCE/TYT 919 (baska deger yok)
A1 konu kirilimi           TUR 643, TYT-TR-03 134, TYT-TR-02 51, TYT-TR-01 42, TUR.ANL 22,
                           TUR.YAZ 11, TUR.DIL 9, TUR.PAR 7   (8 konu; %70 level-1 kok -- temp'in
                           Turkce konu etiketi kaba, alt konu dagilimi MAT kadar ince degil)
gorsel hatti               40/40 host'ta var (Python isfile)
idempotens                 secici tekrar: capraz-DB elenen 919 = 919, SECILEN 0 (havuz tukendi)
```

## FAZ E terfi (yedekli)

On-simulasyon (terfi OLMADAN, `v_safe_for_beta` yuklemi `pipeline_metadata` uzerinden): 919'un
573'u kapiya girer (34 `demoted_at`, 261 `tier1_page_inline`/`tier1b`, kesisimli; bayraksiz 0,
fallback 0, AI-onaysiz 0). Yedek: `question_statistics_terfi_yedek_tur_20260907` (919 satir, eski
durum `pending`). `pending -> auto_judged_high` (919) + `REFRESH MATERIALIZED VIEW mv_safe_for_beta`:

```
kapi   4006 -> 4579   (+573, simulasyonla birebir; kapida TURKCE 573)
ES     4579 (eklenen 573, silinen 0) -- kiro2-backend konteynerinden
```

Geri alma:
```sql
UPDATE question_statistics qs SET quality_review_status = y.eski
FROM question_statistics_terfi_yedek_tur_20260907 y WHERE y.id = qs.id;
REFRESH MATERIALIZED VIEW mv_safe_for_beta;
-- sonra konteynerde ES senkronu
```

## generate-mock olcumu (PR #181 havuz yuklemi SQL ile canlida yeniden uretildi)

```
brans | kota | konu | aktif havuz | durum
TUR   |  40  |   8  |     919     | kota TAMAM   (once 0 -> 409 nedeni)
SOS   |  20  |   2  |       0     | EKSIK -> 409
MAT   |  40  |  22  |     900     | kota TAMAM
FEN   |  20  |  15  |    3531     | kota TAMAM
```

Kod karari DEGISMEDI ama neden DEGISTI: TYT denemesi artik yalniz SOS yuzunden 409. SOS dilimi
(temp: TARIH 3939 / SOSYAL 1494 / COGRAFYA 1383 TYT) denemeyi acar; konu seed + `DILIMLER` ayni
boru hattiyla. Not: master'daki `exams.py` hala brans-koru fallback'li eski surum; 409 davranisi
PR #181'de (`fix/coverage-esigi-gercekci-seviye`), bu yuzden endpoint degil yuklem olculdu.

## Surec notlari (tekrar etmesin)

* 920 id'lik `psql -c` komut satiri Windows sinirini asti (WinError 206) -> sorgu dosyaya yazilip `-f`.
* `.cmd` icinde `echo ... >= 919)` yonlendirme sayildi, `backend/919)` cop dosyasi olustu (R2'de
  `391+509)` ile AYNI kaza). Silindi; echo satirlarinda `>` kullanilmaz.
* `findstr` Turkce-duyarsiz esleme yapiyor ("TUR" -> "oturum"); belge taramasi Python ile.

## Canli son durum

```
question_bank  5350   (KIMYA 3531 + MAT 900 + TURKCE 919)
kapi           4579   ES 4579 (birebir)   -- KIMYA/MAT kapida degismedi, TURKCE 573
```

## Acik kalan

* TUR havuzu mevcut suzgecle tukendi; buyume icin kalite-durumu/gorsel-deseni gevsetme karari (Huseyin).
* SOS dilimi: `generate-mock`'u acacak tek eksik. BIY/FIZ canlida 0 (FEN kotasini KIMYA tek basina
  karsiliyor -- deneme "Fen" bolumu %100 kimya olur; blueprint alt-brans kotasi yok, urun karari).
* Kitap-duzeyi kirmizi liste (yuksek sizinti oranli 3 kitap) secicide yok; bir sonraki turda eklenebilir.
* Kaynak anahtar hatasi (`756f59e5`) ilk ornek; icerik-duzeyi anahtar denetimi ayri is.

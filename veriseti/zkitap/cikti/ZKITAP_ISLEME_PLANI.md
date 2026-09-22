# zkitap -- islenmemis 12 kitap (13 klasor) icin isleme PLANI

Durum: UYGULANIYOR (ilerleme: bolum 8). Bu belge yazilirken HICBIR uygulama
adimi atilmadi: transkripsiyon yok, migration yok, ithal yok, dal yok.
Yapilan tek sey salt-okunur kesif (`backend/_geo_gecici/_kesif.py` ->
`kesif.json`) ve salt-okunur DB sorgulari. Tarih: 17 Eyl 2026.

Kapsam: sahibin verdigi "Hic islenmemis -- en buyuk 12'si" tablosu
(ZKITAP_ENVANTER.md satir 1-9, 13, 16, 17, 19).

Ilke: iddia != olcum. Asagida "olculdu" denen her sey bir dosya/sorgu
ciktisina dayanir; "tahmin" denenler BS Turkce kampanyasinin olculmus
maliyetinden turetilmistir ve oyle etiketlenmistir.

---------------------------------------------------------------------

## 0. Olculen baslangic durumu

### 0.1 Klasorler (kesif.json, 13/13)

| # | klasor | PNG | PDF sayfa | ders | simge px (ort) |
|---|---|---|---|---|---|
| 1 | 2023-2024-ACIL-TYT-AYT Geometri Soru Bankasi | 448 | 448 | GEO | 3147 |
| 2 | Apotemi 2019 2020 Tyt Ayt Fizik Soru Bankasi | 448 | 448 | FIZ | 3324 |
| 3 | Orijinal-2024-Geometri Soru Bankasi | 432 | 432 | GEO | 3503 |
| 4 | Orijinal-Tyt Ayt Geometri Soru Bankasi | 432 | 432 | GEO | 3557 |
| 5 | C1CELL-2024-TYT-AYT-Geometri Soru Bankasi | 420 | **416** | GEO | 3133 |
| 6 | Bilgi Sarmal Ayt Edebiyat Soru Bankasi | 416 | 416 | EDB | 3186 |
| 7 | Bilgi Sarmal Ayt Edebiyat Soru Bankasi 2024 | 416 | 416 | EDB | 3200 |
| 8 | Mikro Orijinal-Tyt Ayt-Geometri Soru Bankasi 2 | 416 | 416 | GEO | 4452 |
| 9 | Bilgi Sarmali-2022-2023-Tyt Ayt-Geometri Soru Bankasi | 402 | **400** | GEO | 4118 |
| 10 | Mikro Orijinal Tyt Fizik Soru Bankasi 2025 | 400 | 400 | FIZ | 2813 |
| 11 | 345 2024 Ayt Fizik Soru Bankasi | 392 | 392 | FIZ | 2627 |
| 12 | 345 2025 Ayt Fizik Soru Bankasi | 392 | 392 | FIZ | 2370 |
| 13 | 345 2024 Ayt Biyoloji Soru Bankasi | 376 | 376 | BIO | 2982 |

Toplam 5.390 PNG sayfa (PDF 5.384). 13/13 icin olculen ortak gercekler
(OLCUM KAPSAMI: klasor basina 5 ornek PNG = 10/60/150/250/330; PDF metin
katmani 3 sayfada, gomulu gorsel 1 sayfada olculdu -- tum sayfalar Faz 0
K0.1'de taranacak):

  * Orneklenen her PNG 1920x1080; orneklenen PDF sayfalarinda METIN
    KATMANI YOK; orneklenen PDF sayfasi tek bir gomulu 1920x1080 gorsel.
    Yani cozunurluk TAVANI BS Turkce ile ayni
    (sayfa karti ~736x974, 2x buyutme okunabilir, nokta/virgul sinirda).
  * 13/13 klasorde, orneklenen sayfalarda okuyucu-uygulamasi simge imzasi
    var (sayfa basina ort. 2.370-4.452 px).
    BS Turkce'de %30.7 soruyu etkileyen SIMGE ORTMESI riski bu 13 kitabin
    HEPSINDE potansiyel olarak vardir; oran kitap basina OLCULMEDEN
    bilinemez (bkz. Faz 0 / K0.4).
  * Ornek sayfalarin (10/60/150/250/330) md5'leri 13 klasor arasinda
    tekrar etmiyor. Bu, cift sayilan BS Turkce durumunu (sayfa karti farki
    0, fark yalniz sekme cubugunda) DISLAMAZ: md5 tum ekrani kapsar. Ikili
    ciftler icin sayfa-karti piksel farki ayrica olculmeli (K0.6).
  * Iki klasorde PNG ve PDF sayfa sayisi TUTMUYOR: #5 (420/416) ve #9
    (402/400). Herhangi bir okuma oncesi bu fark aciklanmali (fazladan
    ekran goruntusu mu, PDF'te eksik sayfa mi?).

### 0.2 DB'de bugun ne var (postgresql, salt-okunur)

`pipeline_metadata.ithal_araci` tasiyan modern KITAP ithalleri (OSYM 2025
TYT 125 / AYT 166 kitapcik satiri ders bazli olmadigi icin tabloda yok):

| ders | kaynak | satir | aktif | gorselli |
|---|---|---|---|---|
| GEO | 345 2025 TYT-AYT Geometri | 2708 | 2702 | 2708 |
| GEO | Mikro Orijinal 2025 AYT Geometri | 1211 | 1211 | 1211 |
| FIZ | Neofizik AYT Fizik 2025 | 1218 | 1181 | 1218 |
| FIZ | Neofizik TYT Fizik | 891 | 827 | 891 |
| BIO | 345 2025 AYT Biyoloji | 1315 | 1315 | 1315 |
| BIO | 345 2025 TYT Biyoloji | 1023 | 1022 | 1022 |
| TUR | Aktif Ogrenme TYT Dilbilgisi 2025 | 678 | 644 | 0 |
| TUR | Bilgi Sarmal TYT Turkce | 1468 | 0 | 0 |
| EDB | -- | **0** | 0 | 0 |

Modern ithal toplamlari: GEO 3.919, BIO 2.338, TUR 2.146, FIZ 2.109,
EDB 0. (Eski hattin kismi satirlari -- envanterde 140 klasor -- bu
toplamlara DAHIL DEGIL; onceliklendirme yalnizca modern satirlara bakar.)

Konu agaci (`topic_hierarchy`): EDB kokunun altinda yalnizca 1 dugum var
(seviye 2) -- Edebiyat icin agac SIFIRDAN kurulacak (0029 deseni). FIZ
14/79, GEO 5/31, BIO 31 (yalniz seviye 2) dugum tasiyor; bu kitaplarin
icindekileri mevcut agacla eslenmeli, eksik dallar migration ile eklenmeli.

Bu 13 klasorun hicbirinin DB'de satiri yok (envanter olcumu: kaynak adi
eslesmesi 0). Yani BS Turkce'deki "eski 13 bozuk satir + kaynak adi
migration'i" isi bu kitaplarda BEKLENMIYOR; Faz 0'da hash ile yeniden
teyit edilecek.

### 0.3 Elimizdeki kanitlanmis hatlar

  * METIN hatti (sekil yok): BS Turkce / Dilbilgisi. Anahtar cift okuma,
    sifir-serbestlik kapilari, test sinirina hizali gruplarla
    transkripsiyon, kirmizi imlec piksel kanali, K1-K12, simge ortmesi
    isaretleme. Olculmus maliyet: 323 soru sayfasi, 29 grup, grup basina
    ~140-160k jeton (Opus, yalin istem, tam sayfa JPEG). NOT: jeton
    rakami bu oturumda alt-ajan raporlarindan olculdu, YONTEM'e YAZILMADI;
    ilk yeni YONTEM'e kaydedilecek. Sonnet daha pahali ve daha az dogru
    cikti (pilot olcumu).
  * SEKIL hatti (her soru gorsel): geo345 / mikro_geo / neofizik / biyo345.
    Ikon dedektoru (RGB 69,39,160), sutun kirpimi + soru kutusu,
    `<kitap>_kirp.py` ile `question_image_url` uretimi (olcek denetimli),
    sekil olup kirpim uretilemeyince `gorsel_yok_sekilli`.
  * Ortak altyapi: `metin_olcum.py` (tek kaynak), `kaynak_sozlesmesi.py`
    (kayit defteri), PASIF ithal sozlesmesi, e2e test dosyasi, YONTEM.md.

Bu plandaki 13 klasorun 6'si geometri, 4'u fizik, 1'i biyoloji -> SEKIL
hatti (11); 2'si edebiyat -> METIN hatti (Bilgi Sarmal, BS Turkce ile
ayni yayinevi ve ayni yakalama). 6+4+1+2 = 13.

Sekil hattinda iki EMSAL SOZLESME var ve alan adlari FARKLI:
  * geo345: `question_text`, `a..e`, `correct_answer`, `kutu`, `sekil_var`,
    `sekil_aciklama`, `okuma_supheli`, `sik_bos`
  * neofizik: `soru_metni`, `secenekler`, `dogru_cevap`, `kirpim_kutusu`,
    `gorsel_dosya`, `bayraklar`, `cevap_kaynagi`
Yeni kitaplar icin TEK sozlesme secilmeli (D8). Matematik gosterimi her
ikisinde de Unicode duz metin (ornek: `|EB| = sqrt3 birim`, `[AE] dik [CB]`
karsiliklari Unicode sembolle); LaTeX YOK -- ayni kalir.

TYT-AYT KARISIK kitaplar (6 geometri + Apotemi/345 fizik): `exam_type`
tek degerli. geo345 emsali: soru duzeyinde sinav turu OLCULMEDI, 'AYT'
yazildi ve `pipeline_metadata.sinav_turu_kaynagi='olculmedi_kitap_TYT-AYT_karisik'`
ile isaretlendi. Ayni emsal uygulanir; farkli istenirse D9.

---------------------------------------------------------------------

## 1. Onceliklendirme (ONERI -- son karar sahibin)

Olcutler, agirlik sirasiyla:
  (a) marjinal deger: derste bugun kac satir var (EDB 0 -> en yuksek)
  (b) surum/kopya riski: ayni kitabin iki surumu ya da DB'deki kitabin
      onceki baskisi (once ortusme olculur, sonra karar)
  (c) hat hazirligi: metin hatti > sekil hatti (kirpim isi ek yuk)
  (d) simge ortmesi riski: metin agirlikli kitap = daha yuksek risk

Onerilen dalgalar:

| dalga | kitap(lar) | gerekce | on kosul |
|---|---|---|---|
| A | Bilgi Sarmal Ayt Edebiyat (#6 / #7 -- BIRI) | EDB'de 0 satir; metin hatti hazir | K0.6: iki surumun sayfa-karti farki; K0.4: ortme orani |
| B1 | Mikro Orijinal Tyt Fizik 2025 (#10) | en guncel TYT fizik; TYT fizikte 891 satir var | K0.5 sekil yogunlugu |
| B2 | 345 2025 Ayt Fizik (#12) | guncel baski | #11 ile ortusme olcumu; #11 ancak farkli icerik varsa |
| B3 | Apotemi 2019 2020 Tyt Ayt Fizik (#2) | listedeki en eski baski | SAHIP KARARI: eski baski istenip istenmedigi |
| C | 345 2024 Ayt Biyoloji (#13) | klasor adina gore DB'deki 345 2025 AYT Biyoloji'nin ONCEKI baskisi | K0.6 ortusme; yuksekse ATLA onerisi |
| D | Geometri: #5 C1CELL 2024, #1 ACIL 2023-24, #3/#4 Orijinal (BIRI), #8 Mikro Orijinal 2, #9 BS 2022-23 | derste zaten 3.919 satir -> en dusuk marjinal deger; 5+ kitap | #3/#4 cifti ve #8'in DB'deki Mikro Orijinal 2025 ile ortusmesi |

Not: #8 "Mikro Orijinal ... Geometri 2" DB'deki "Mikro Orijinal 2025 AYT
Geometri" (1211 satir) kitabinin ikinci cildi olabilir; bu bir tahmin,
K0.6'da hash ile olculecek.

---------------------------------------------------------------------

## 2. FAZ 0 -- kitap basina KESIF FISI (salt-okunur, dusuk jeton)

Her kitap icin uretim baslamadan `veriseti/zkitap/cikti/<KITAP>_KESIF.md`
yazilir. Piksel olcumleri LLM okuma icermez; yalnizca 8-10 sayfalik goz
kontrolu icin okuma yapilir. Tahmini sure: kitap basina 30-60 dk.

| kod | olcum | cikti / kapi |
|---|---|---|
| K0.1 | sayfa karti dikdortgeni (BS: x 592-1328, y 42-1016) BU kitap icin olculur, varsayilmaz; PNG/PDF sayfa sayisi uzlastirilir (#5, #9) | dikdortgen + sayfa eslesme tablosu; uzlasmazsa DUR |
| K0.2 | sayfa haritasi: kapak / icindekiler / soru araligi / cevap anahtari, yatay cetvel sayimi ile (BS kurali); basili sayfa no <-> dosya no ofseti | aralik tablosu; ofset 2 sayfadan dogrulanir |
| K0.3 | anahtar bicimi: kitap sonu mu, test sonu mu, hic yok mu; serit geometrisi; her test icin anahtar VAR MI | anahtari olmayan test = cevapsiz (asla cozulmez, bkz. R5) |
| K0.4 | SIMGE ORTMESI: simge bloklari (disk 240,238,247 / glif 69,39,160), 0-3 px mesafede kitap murekkebi olan blok sayisi, etkilenen soru orani tahmini (ortme.py'nin bu kitaba uyarlanmasi) | oran raporlanir; esik SAHIP KARARI (emsal: %30.7 -> ithal et ama isaretle) |
| K0.5 | sekil yogunlugu: grafik agirlikli sutun orani (BS grafik dedektoru); kirmizi imlec / ikon sayimi ile beklenen soru sayisi | METIN mi SEKIL hatti mi karari; beklenen soru sayisi (anahtarla capraz) |
| K0.6 | surum/kopya, FAZ 0 kademesi: ciftler icin sayfa-karti piksel farki (#6/#7, #11/#12, #3/#4) ve DB'deki kardes kitapla sayfa sayisi / icindekiler karsilastirmasi (#13 vs 345 2025 AYT Biyoloji; #8 vs Mikro Orijinal 2025). Anahtar dizisi ve hash kademeleri Faz 1'de (1b, 2b) | fark 0 -> ayni yakalama, biri ATLANIR; farkliysa Faz 1 kapilarina devam |
| K0.7 | konu agaci: icindekiler -> kod listesi; mevcut `topic_hierarchy` ile eslesme; eksik dallar | migration gereksinimi (EDB: kesin; FIZ/GEO/BIO: kismi) |
| K0.8 | go/no-go + maliyet: soru sayfasi sayisi / 12 = grup sayisi; grup x 150k jeton; sekil hattinda kirpim isi ayrica | fis sonunda tek satir: GIT / GITME / SAHIBE SOR |

Faz 0 ciktisi sahibe sunulur; Faz 1'e gecis her kitap icin AYRI onaydir.

---------------------------------------------------------------------

## 3. FAZ 1 -- kitap basina URETIM HATTI (kanitlanmis desen)

Her adim bir oncekini sinar; her iddia ayni kapsamda olculur.

1. **Cevap anahtari, CIFT OKUMA.** Iki bagimsiz okuma, farkli olcek /
   farkli kirpim geometrisi, okuyucuya beklenen sayi SOYLENMEZ. Fark 0
   hedef; farkli girdilerde hakem turu (A/B'nin ne dedigi soylenmeden).
   Tek kaynak KITABIN BASILI ANAHTARI; soru asla cozulmez.
   Kapilar (sifir serbestlik): her testte 1..N kesintisiz; anahtardaki
   `Sayfa:` (varsa) tekduze artan; test araliklari soru araligini
   bosluksuz/cakismasiz doser; bolum numaralari sirali.
   1b. **Surum kapisi (anahtar dizisi).** Cift/kardes kitap varsa test
   bazli cevap dizileri karsilastirilir (transkripsiyonsuz, ucuz). Dizi
   birebir ayniysa transkripsiyona GECILMEZ, sahibe sorulur (D2/D3).
2. **Transkripsiyon.** Test sinirina hizali gruplar (~12 sayfa), her grup
   ayri okuyucu (Opus, yalin istem: her goruntuyu bir kez oku, yalniz
   YAPISAL `kaynak_kusuru`, cozunurluk suphesi kusur degil). Okuyucuya
   test basina soru sayisi SOYLENMEZ. "Kitap ne yaziyorsa o."
   SEKIL hattinda ek olarak: sutun kirpimi + soru kutusu (`kutu`),
   `<kitap>_kirp.py` (olcek denetimi: render boyutu != beklenen -> DUR),
   `question_image_url = <CROP_IMAGE_DIR>/<ONEK>/<id>.png`; sekil var
   ama kirpim yoksa `gorsel_yok_sekilli`.
   2b. **Surum kapisi (hash).** `soru_hash` + kelime-kumesi ortusmesi
   (>=0.75, BS emsali) DB ile; ortusme orani rapor edilir, ithal oncesi
   sahip karari (tumunu ithal / yalniz farklilari / atla).
3. **Bagimsiz piksel kanallari.** Kirmizi imlec / ikon sayimi sutun
   basina vs okunan soru sayisi; grafik-agirlikli sayfa dedektoru vs
   "soru bulunamadi" sayfalari. HER sapma tek tek aciklanir.
4. **Yapisal dogrulayici.** K1-K12 (`metin_olcum.py`), test basina
   okunan == anahtar, 5 sik varligi, cevap harfi A-E.
5. **Simge ortmesi isaretleme.** Satir bazinda
   `okuyucu_simgesi_ortmesi`, `ortulen_bolge`, bayrak listesi.
6. **Veri seti + YONTEM.** `veriseti/zkitap/cikti/<kitap>_sorular.json`
   (+ konu agaci json) ve `<KITAP>_YONTEM.md` (bolum 0-11 deseni:
   kaynak/tavan, sayfa yapisi, anahtar, kapilar, transkripsiyon, ortme,
   agac, alanlar, ithal sonrasi olcum, bilinen borc). `git add -f`.
7. **Kod.** `kaynak_sozlesmesi.py`'ye kayit (`onek`, `ithal_araci`);
   `scripts/kitap/<kitap>_ithal.py` (`metin_olcum`'dan ice aktarir,
   PASIF sozlesme: is_active=FALSE, is_public=FALSE, is_ai_generated=TRUE,
   review_status='PENDING', explanation NULL); sekil hattinda
   `<kitap>_kirp.py`.
8. **Migration'lar.** Konu agaci `00NN_<kitap>_konu_agaci.py` (0029
   deseni, GUNLUK tablosu, geri alinabilir). Kaynak adi migration'i
   YALNIZCA eski satir bulunursa (beklenmiyor).
9. **Testler.** `tests/e2e/test_<kitap>_ithal.py` (sabitler: soru/test
   sayisi, aralik, kapilar; ASCII kaynak, `_ascii_kucuk`), gerekirse
   nobetci test. Yerelde: ruff (0.7.1), mypy REPO KOKUNDEN, bandit,
   detect-secrets, `ascii_dosya.py`.
10. **Dal -> commit -> PR -> CI -> merge.** Adli dosyalarla stage
    (`git add -A` ASLA; yasakli dosyalar asla), `git commit -F`, amend /
    rebase / --no-verify yok. Merge yalniz kalan kirmizilar miras set ise
    (Automatic PR Review, Frontend Tests, CI Summary, 3 backend testi).
    ZAP beklenmez.
11. **Ithal sonrasi olcum.** DB satir == veri seti; hepsi PASIF; bayrak
    sayimlari; `v_safe_for_beta` = 0; YONTEM bolum 10'a yazilir.
12. **Aktiflestirme = AYRI SAHIP KARARI** (Faz 3). 0027 deseni: kapi
    bayrakli satirlari (`okuyucu_simgesi_ortmesi`, `gorsel_yok_sekilli`,
    `kaynak_dizgi_kusuru`, `sik_bos`) disarida birakir; `is_public`e
    dokunulmaz.

Kural: BIR PR = BIR KITAP. Iki kitap ayni PR'a girmez.

---------------------------------------------------------------------

## 4. FAZ 2 -- kampanya duzeni (cok oturum)

Maliyet tahmini (BS Turkce olcumunden turetilmis, TAHMIN):

| kalem | olcum (BS Turkce) | 400-448 sayfalik kitap |
|---|---|---|
| soru sayfasi | 323 | ~380-430 |
| transkripsiyon grubu | 29 | ~32-36 |
| grup basi jeton | ~140-160k | ayni |
| transkripsiyon toplam | ~4-4.5M | ~5-5.5M |
| anahtar + dogrulama + kod | OLCULMEDI (tahmin ~0.5-1M) | ~0.5-1M |
| sekil hatti kirpim isi | (yok) | OLCULMEDI; Faz 0 fisinde tahmin |
| kitap basina | ~5M, 1 (sikistirmali) oturum | ~6M, 1-1.5 oturum |

12 kitap icin kaba toplam ~70M jeton ve 12-18 oturum. Bu kampanya TEK
OTURUMDA BITMEZ; her kitap kendi basina bitirilir ve merge edilir, yarim
kitap birakilmaz.

Duzen:
  * Sira: A -> B -> C -> D (bolum 1). Her dalga sonunda sahibe kisa rapor
    ve bir sonraki dalga icin yeniden onay.
  * Her kitap icin Faz 0 fisi -> onay -> Faz 1. Faz 0 fisleri toplu da
    cikarilabilir (13 klasor icin ~1 oturum -- TAHMIN, dusuk jeton) -- sahip
    isterse once BUTUN fisler, sonra siralama kesinlesir.
  * Oturum icinde durum `backend/_<kitap>_gecici/` altinda dosyalarla
    tasinir (baglam sikistirmasina dayanikli); YONTEM.md adim adim
    yazilir, sonda degil.
  * Ilk adim (onay gelirse): Dalga A icin Faz 0 -- #6/#7 sayfa-karti
    farki, ortme orani, anahtar bicimi, agac ihtiyaci. Transkripsiyon
    BASLAMAZ; fis sunulur, beklenir.

---------------------------------------------------------------------

## 5. Riskler ve karsi onlemler

| # | risk | kanit | onlem |
|---|---|---|---|
| R1 | Simge ortmesi 13/13 kitapta | simge imzasi 2.370-4.452 px | K0.4 olcum; oran sahibe; emsal karari uygula ya da kitap basina karar; metin agirlikli EDB en riskli |
| R2 | Sekil hattinda yanlis kirpim | geo345 F2/F4 gecmisi (kutu seti bozulmustu) | olcek denetimi, ikon + murekkep koridoru kurali, `gorsel_yok_sekilli`; kirpimlar goz orneklemi ile denetlenir |
| R3 | Surum kopyasi / onceki baski (ciftler ve #13) | BS Turkce 2. klasoru fark 0 cikti | K0.6 uc kademe (piksel / anahtar dizisi / hash); ithal oncesi kapi |
| R4 | PNG/PDF sayfa sayisi uyusmazligi (#5, #9) | kesif.json | K0.1'de uzlastirilmadan okuma yok |
| R5 | Anahtari olmayan test/soru | K0.3 | soru COZULMEZ; cevapsiz satir ithal edilmez ya da `cevap_yok` bayragi ile PASIF kalir -- SAHIP KARARI |
| R6 | Eski baskilar (#2 2019-20, #9 2022-23) | klasor adi | plan icerik yargisi vermez; dahil edilip edilmeyecegi sahibin |
| R7 | Jeton / sure; baglam sikistirmasi | BS kampanyasi olcumu | kitap basina kapali dongu; durum dosyalari; YONTEM'i erken yaz |
| R8 | Arac degisimi (Desktop_Commander gitti; DB araci salt-okunur) | bu oturum | PowerShell .bat deseni; migration'lar Windows alembic ile; DB yazimi yalniz migration/ithal betigi uzerinden |
| R9 | Transkripsiyon okuyucusunun "duzeltme" egilimi | BS pilot: virgul/nokta asiri isaretleme | yalin istem; yalniz yapisal kusur; "kitap ne yaziyorsa o" |
| R10 | Veri seti alan sozlesmesi ayrismasi (geo345 vs neofizik) | bolum 0.3 | D8 ile tek sozlesme; `metin_olcum.py` dogrulayicilari o sozlesmeye gore |
| R11 | TYT-AYT karisik kitapta `exam_type` | geo345_ithal.py docstring | geo345 emsali + `sinav_turu_kaynagi` isareti; PASIF satirda geriye donuk duzeltilebilir |

---------------------------------------------------------------------

## 6. Sahibe ayrilan kararlar (uygulama ONCESI gerekli olanlar)

| # | karar | plandaki varsayilan |
|---|---|---|
| D1 | Dalga sirasi A->B->C->D onayi | oneri bolum 1 |
| D2 | Ciftlerde hangisi: #6/#7, #11/#12, #3/#4 | Faz 0 olcer, sonra sorar |
| D3 | #13 (345 2024 Ayt Biyoloji): ortusme yuksekse atla mi | ortusme >= 0.5 -> ATLA onerisi |
| D4 | Ortme politikasi: "ithal et ama isaretle" tum kitaplara mi, kitap basina mi | kitap basina oran raporu + soru |
| D5 | Eski baskilar (#2, #9) dahil mi | karar yok |
| D6 | Faz 0 fisleri: once 13'u birden mi, dalga dalga mi | dalga dalga (A once) |
| D7 | ZKITAP_ENVANTER.* ve bu plan git'e girsin mi | girmedi (cikti/ git disinda) |
| D8 | Sekil hatti veri seti alan sozlesmesi: geo345 mi neofizik mi | oneri: neofizik (`bayraklar`, `cevap_kaynagi` -- BS Turkce ile ayni bayrak mantigi) |
| D9 | TYT-AYT karisik kitaplarda `exam_type` | geo345 emsali: 'AYT' + `sinav_turu_kaynagi` isareti |

Hicbir karar plan yazilirken verilmis sayilmadi.

---------------------------------------------------------------------

## 7. Bu belge yazilirken yapilmayanlar

  * Hicbir sayfa transkribe edilmedi, hicbir anahtar okunmadi.
  * Hicbir migration, ithal, dal, commit, PR olusturulmadi.
  * DB'ye yazilmadi (yalniz SELECT).
  * `backend/_geo_gecici/kesif.json` salt-okunur kesif ciktisidir,
    git'e girmedi.

Uygulama, sahibin acik "basla" demesiyle ve yalniz onayladigi dalga /
kitap icin baslar.

---------------------------------------------------------------------

## 8. ILERLEME (uygulama kaydi)

Bu bolum plan uygulanirken guncellenir. Her satirin arkasinda merge
edilmis bir PR ve bir YONTEM belgesi vardir.

| dalga | kitap | soru | PR | durum | yontem belgesi |
|---|---|---|---|---|---|
| A | Bilgi Sarmal Ayt Edebiyat Soru Bankasi (#6) | 1597 | #289 | MERGE | `BILGI_SARMAL_EDEBIYAT_YONTEM.md` |
| B1 | Mikro Orijinal Tyt Fizik Soru Bankasi 2025 (#10) | 1326 | #290 | MERGE | `MIKRO_FIZIK_TYT_YONTEM.md` |
| B2 | 345 2025 Ayt Fizik Soru Bankasi (#12) | 1308 | #291 | MERGE | `FIZ_345_AYT_YONTEM.md` |
| B3 | Apotemi 2019 2020 Tyt Ayt Fizik (#2) | -- | -- | SAHIP KARARI BEKLIYOR (eski baski istenip istenmedigi) | -- |
| C | 345 2024 Ayt Biyoloji (#13) | -- | -- | **ATLA onerisi** (Faz 0 olculdu: DB ile %85 ortusme, beklenen yeni soru ~45) | `BIO_345_2024_KESIF.md` |
| D | Geometri (#1, #3/#4, #5, #8, #9) | -- | -- | on kesif yapildi: dalga 5 degil **4 kitap** (#3/#4 ayni yakalama) | `GEO_DALGA_D_KESIF.md` |
| D / #1 | ACIL 2023-2024 Tyt Ayt Geometri | 1730 | #304 | **MERGE** (ithal kosuldu, PASIF; 151 soru okuyucu diski ortmesi yuzunden disarida) | `GEO_ACIL_2324_KESIF.md`, `GEO_ACIL_2324_YONTEM.md` |
| D / #5 | C1CELL 2024 Tyt Ayt Geometri | 1770 | #311, #312, #313, #314 | **MERGE** (ithal kosuldu, PASIF; ortulu soru YOK -- 1770/1770 girdi) | `GEO_C1CELL_2024_KESIF.md` |
| D / #3 | Orijinal 2024 Tyt Ayt Geometri | ~2099 (beklenen) | -- | Faz 0 bitti, **GIT**; test haritasi Faz 1'de icindekilerden kurulacak | `GEO_ORIJINAL_2024_KESIF.md` |
| D / ek | ACIL 2025 KURS Tyt Ayt Geometri | ~1951 (beklenen) | -- | Faz 0 bitti, **GIT** (sahip karari: iki ACIL baskisi da islenecek) | `GEO_ACIL_2025_KURS_KESIF.md` |

Bu planin tablosundan gelen toplam: **7731 soru**, hepsi PASIF
(A 1597 + B1 1326 + B2 1308 + D/#1 1730 + D/#5 1770). Her satir canli
DB'de tek tek dogrulandi (21 Eyl 2026). DIKKAT: bu sayi DB'nin tamami
DEGILDIR -- `pipeline_metadata->>'ithal_araci'` tasiyan modern ithal
satirlarinin tamami ayni olcumde 15 kitapta 18534; kalani bu plandan
onceki hatlardan gelir.

### 8.1 Baski ikilemleri nasil kapandi

* **#6 / #7 (Edebiyat)**: ayni kitabin iki baskisi; sayfalarin %76'si
  birebir ayni, %24'u revize. #6 islendi, #7 ISLENMEDI ama okuyucu
  simgesi ortmesini KURTARMA kanali olarak kullanildi (ortme borcu 451
  satirdan 2 satira dustu).
* **#11 / #12 (345 Fizik)**: 392 sayfanin kart bolgesi karsilastirildi;
  farkin medyani %0,28 (simge kaymasi) ama 25 sayfa gercekten farkli
  icerik. #12 (2025) islendi, #11 ISLENMEDI.

### 8.2 Plan yazilirken bilinmeyen, uygulamada olculen seyler

1. **Sayfa karti her kitap icin ayri**: Mikro TYT Fizik 728x968,
   345 AYT Fizik 748x980, BS Edebiyat 728x968. Kardes kitabin degeri
   varsayilsa her kirpim kayardi (K0.1 kurali karsiligini verdi).
2. **Anahtar bicimi ucuncu bir tur cikti**: kitap sonu izgarasi (BS),
   test sonu seridi (Mikro) ve SAYFA ALTI SUTUN SATIRI (345). Plan
   yalnizca ilk ikisini ongoruyordu.
3. **Tesseract kucuk puntoda elendi** (Mikro serit metni ~8 px);
   okuma LLM montaj kanaliyla yapildi ve iki bagimsiz okumayla
   dogrulandi.
4. **Siklarin GRAFIK oldugu sorular** plan tarafindan ongorulmemisti;
   345 Fizik'te 19 soru boyle cikti. Sik metni uydurulmadi,
   `(gorsel sik)` + `sikler_gorsel` bayragi kondu.
5. **Simge sayisi != soru sayisi**: konu anlatimli kitaplarda okuyucu
   ornek cozumlerin de soluna simge koyuyor. Kirpim kutusu turetimi
   bu yuzden "sutundaki simge sayisi == o sutunun anahtar girdisi"
   kapisina baglandi.
6. **Dorduncu anahtar bicimi**: ACIL geometride anahtar, testin son
   sayfasinin altinda iki satirlik IZGARA KUTUSU olarak duruyor (kitap
   sonu izgarasi / test sonu seridi / sayfa alti sutun satiri disinda
   bir tur).
7. **Kirpim koordinati tek/cift sayfada kayabiliyor**: ACIL geometride
   simge sutunlari tek sayfada gx 14 ve 346, cift sayfada gx 32 ve 361
   -- 18 px recto/verso kaymasi. Tek koordinat varsayilsa sayfalarin
   yarisi kayardi.
8. **Ortme olcumunun maskesi DAIRE olmali**: disk daireseldir; kare
   ayak izi kosede sayfayi gosterip "diskin ALTINDA murekkep var" gibi
   fiziken imkansiz bir sonuc uretiyor (opak disk). Ayrica cizimlerdeki
   lacivert tonlar glif rengine 40 tolerans icinde dusebiliyor, bu
   yuzden glif blogunun cevresinde DISK halkasi sarti gerekiyor.
9. **Icindekiler bazen test sayisini da veriyor**: Orijinal 2024
   Geometri'de her konunun yanina test numaralari yazili (toplam 226
   test). Piksel dedektoru esige gore 196-244 arasi gezinirken
   icindekiler kesin sayiyi veriyor -- sayim otoritesi olarak once
   icindekiler denenmeli.
10. **Cevap satiri ORTALANMIS olabilir**: 345 kitaplarinda satir sabit
   x'te basliyordu, Orijinal 2024'te icerige gore ortalaniyor (s200
   x0=82, s230 x0=235). Sabit x varsayan dedektor sayfalarin yarisini
   kaciriyor.
11. **Yakalama tekrari (ayni dosyanin birden fazla kopyasi) olabilir**:
   ACIL 2025 KURS'ta dosya 3-4-5 bayt bayt ayni. Bu yuzden "PNG sayisi
   = PDF /Count" tek basina uzlasma degil -- PDF ayni PNG'lerden
   uretildigi icin ayni fazlaligi tasiyor. Sayfa sayisi kapisina md5
   tekrar taramasi eklenmeli.
12. **Basili sayfa no ofseti 0 olmak zorunda degil**: ACIL 2025'te
   basili no = dosya no - 4 (12 ornekte sabit). Ofset olculmeden
   icindekiler sayfa numaralari kullanilamaz.
13. **Icindekiler sayfasi yakalamada olmayabilir**: ACIL 2025 KURS'ta
   kunyeden sonra dogrudan icerik geliyor. Konu agaci o zaman sayfa
   ust bandindaki basliklardan turetilmek zorunda -- ek is ve ek hata
   riski.
14. **Baski ayrimi icin en ucuz kanit KUNYE**: ISBN + yazar/editor
   listesi, piksel karsilastirmasindan once bakilmali. ACIL'in iki
   baskisi boyle bir dakikada "ayri kitap" olarak ayrildi
   (978-625-7134-31-6 vs 978-625-7134-96-5).
15. **Anahtarin sik dagilimi dengeli olmayabilir**: ACIL 2023-2024'te
   C %30,3, A %12,5. Olcum hatasi degil (test basina C orani 0,00-0,62
   arasinda geziyor ve uc ornek 4x'te dogrulandi). Kalibrasyon ve
   zorluk kestirimi "sik dagilimi uniform" varsayamaz.
16. **Cevap kutusu kirpimi olculen cerceve degerinden turetilmemeli**:
   `cerceve_ust` bazi sayfalarda izgaranin ORTA cizgisini yakaliyor ve
   ust satiri kesiyor; kirmizi piksel x'i de son hucrenin harfini
   disarida birakiyor. Comert sabit pencere daha guvenli.
17. **3 px pay ortme demek DEGIL; konum-bazli beyazlatma orada da
   calisiyor.** `GEO_DALGA_D_KESIF.md` eki, C1CELL'i "diskin sagindaki
   en kucuk bosluk 3 px, ortme sinyali 301" diye isaretlemis ve bu dar
   payli kitaplarda ortme borcu beklenmisti. C1CELL islenince olculen
   sonuc: **ortulu soru 0**, 1770 sorunun tamami dort kapidan gecti.
   Yani (a) "ortme sinyali" bant olcusu bir UST SINIRDIR ve gercek
   sayiyi 300 kat asabilir -- planlama girdisi olarak kullanilabilir,
   kapsam kararina temel yapilamaz; (b) KAPI 6'nin konum-bazli
   beyazlatmasi (renk-bazli degil) 3 px payda da sayfayi bozmadan
   calisiyor. Dalga D'nin "ayar testi once ACIL 2025 KURS'ta yapilsin,
   sonucu dalga geneli karardir" onerisi bu yuzden artik kritik yolda
   DEGIL: dar pay tek basina yeniden yakalamayi gerektirmiyor.
18. **Tasiyici kapi birim/test duzeyinde sayim olmali.** C1CELL'de
   birim sinirlari basili degildi; "N'e geri topla" (seritten geriye
   dogru simge toplayip birimin cevap sayisina esitleme) 163 birimin
   163'unde tutturdu ve 1770 == 1770 esitligini yapisal garanti haline
   getirdi. Naif segmentasyon 135/163'te kaliyordu.
19. **Kapinin kapi oldugu ayrica olculmeli.** C1CELL ithal aracinda 13
   mutasyon denendi; ilk gecis 12'sini yakaladi. Kacan mutasyon (bir
   kirpim kutusunu `ortulu` isaretlemek) satiri gorselsiz ithal
   ettiriyordu ve dosya SAYIMI dogru gorundugu icin fark edilmezdi.
   Mutasyon testi olmasa bu delik uretime giderdi.
20. **Dosya sayimi bozuk dosyayi gizler.** C1CELL kirpimlari servis
   dizinine kopyalanirken mount dustu ve bir PNG yarim kaldi; robocopy
   "var olani atla" bayragiyla onu yenilemedi. Sayim 1770/1770 dogru
   gorunuyordu. Bozukluk ancak dosyalar ACILARAK (PIL) yakalandi --
   kopyalama dogrulamasi sayim degil sha256 + acilabilirlik olmali.
21. **Bir hatayi bulunca AYNI SINIFI repo genelinde ara.** Gorsel URL
   hatasi (`CROP_IMAGE_DIR` dizininin URL kolonuna yazilmasi) once iki
   geometri kitabinda bulundu ve 0036 ile onarildi. Onarimdan SONRA
   "DB genelinde `/static/crops` disi URL sifir olmali" diye taraninca
   **2542 satir daha** cikti: 345 AYT Fizik (1295) ve Mikro TYT Fizik
   (1247). Yani ilk tur eksik kalmisti ve bunu ancak kapsam disi bir
   dogrulama sorgusu gosterdi -- "duzelttim" demek ile "artik hic
   kalmadi" demek ayri iddialardir ve ikincisi ayri bir olcum ister.
   0038 kalan ikisini onardi.

   Testin bicimi de bu yuzden degisti: kitap basina test yazmak yerine
   `tests/e2e/test_kitap_gorsel_url.py` `scripts/kitap/` altindaki URL
   ureten HER araci tarar, boylece yeni bir kitap eklendiginde
   kendiliginden kapsar. Taramanin kendisi de test edilir (en az dort
   arac bulmali), yoksa desen degisince test sessizce bosa duserdi.

   Dort kitabin dordu de PASIF oldugu icin bu hata hicbir ogrenciye
   yansimadi; ikisi (3032 sekilli soru) aktiflestirmeden hemen once
   yakalandi.

22. **Basili icindekiler bir OZETTIR, olcum degildir.** Orijinal 2024
   Geometri'nin Faz 0 fisi "sayim otoritesi piksel degil, iki bagimsiz
   okuma olmali" demisti. Iki okuma yapildi, birebir tuttu -- ama okunan
   sey kitabin icindekiler tablosuydu. Sayfalardaki TEST rozetleri 425
   sayfada tarandiginda iki konuda sapma cikti: Ucgende Acilar rozet 8 /
   icindekiler 9, Aci-Kenar Bagintilari rozet 5 / icindekiler 4. Kitabin
   kendi dizgi hatasi; 5x buyutmeyle iki kez okundu, okuma hatasi degil.

   Iki bagimsiz okuma OKUMA hatasini eler, KAYNAGIN KENDI hatasini elemez.
   Sayim otoritesi her zaman birimin uzerindeki kendi kimligidir (burada
   testin kendi rozet numarasi); ozet tablo denetim icin yaninda durur.

   Sapmalar ZIT YONLU oldugu icin TOPLAM iki kanalda da 226 cikti. Toplama
   bakip gecilseydi iki konunun atamasi sessizce yanlis ithal edilecekti.
   **Toplamin tutmasi dagilimin dogru oldugunu gostermez** -- madde 20'deki
   "dosya sayimi dogru gorunuyordu" tuzaginin ayni ailesi, bu kez sayfa
   degil konu duzeyinde.

   Kapi bicimi: bilinen sapmalar teste CIVILENDI (tam olarak bu ikisi).
   Ucuncusu cikarsa da biri sessizce duzelirse de test kirmizi olur.

23. **Siniflandirici kullaniyorsan marji da yaz.** Orijinal 2024'un cevap
    anahtarinda 2072 harfin 1249'u 1-NN ile siniflandirildi. Ilk turda 7
    girdi yanlis cikti (E yerine B) ve harf dagiliminin TOPLAMI yine
    tutuyordu -- madde 22'nin ayni tuzagi, bu kez harf duzeyinde.

    Hatayi bulan sey daha buyuk bir toplam degil, olcumun kendi guven
    payiydi: her girdinin marji (en iyi sinif skoru - ikinci sinif skoru)
    hesaplaninca, yanlis cikan 7 girdi tum kumenin en dusuk marjli TAM
    OLARAK 7 girdisi oldu. Gozle okunup duzeltildi, en dusuk marj
    0.0101'den 0.1004'e cikti.

    Kural: bir cikti bir siniflandiriciyla uretiliyorsa, satir yalniz
    etiketi degil etiketin marjini da tasimali ve kapi marja bir alt sinir
    koymali. Marjsiz etiket, nerede supheli oldugunu soramayacagin bir
    etikettir.

    Ikinci kural: etiketli altkume ile makine altkumesi ayni dosyada
    KAYNAK alaniyla ayrilmali. Gozle okunan yerde otorite okumadir; kapi
    "anahtar, gozle okuma dosyasiyla birebir ayni olmali" diye capalanir.

24. **Kapi, olculen seyin KENDISINE degil, KAYNAGINA bagli olmali.**
    Orijinal 2024'un kirpim kutulari PR #322'de 9 kapidan gecmisti: kart
    icinde mi, ters mi, cakisiyor mu, cevap seridine siziyor mu, hepsi ayni
    sutun sinirina oturuyor mu. Hepsi yesildi. Kutular yine de yanlisti:
    kitabin metin blogu tek/cift sayfada ~16 px kayiyor ve sabit sutun
    siniri cift sayfalarda sol sutunun sag kenarini kesiyordu.

    Kapilar bunu goremedi cunku hepsi kutulari BIRBIRIYLE karsilastiriyordu.
    Hepsi ayni yanlis sinira oturuyordu, yani "tutarli" idiler. Hata ancak
    kirpim URETILIP GOZLE bakilinca goruldu (s432 sol #2'de son sik yoktu).

    Kural: bir olcumun kapisi, o olcumun TURETILDIGI kaynaga bagli olmali.
    Kutunun kapisi "hepsi ayni sinirda mi" degil, "sinir o sayfanin kendi
    simgelerinden mi turetilmis" olmali. Ic tutarlilik, kaynakla
    tutarliligin yerine gecmez.

    Ikinci ders: goruntu ureten her adimda **urune gozle bakilmali**. 2072
    kutunun sayisi, boyutu, cakismamasi dogruydu; iceriginin eksik oldugunu
    yalnizca bir kirpima bakmak gosterdi.

25. **Gevsek dosya deseni yanlis kaynagi sessizce secer.** Ayni ekran
    goruntusu dizininde `Orijinal-2024-Geometri` (160 sayfa) ve
    `Orijinal-2024-Geometri Soru Bankasi` (432 sayfa) yan yana duruyor.
    `Orijinal-2024-Geometri*` deseni birincisini secti ve 761 dosya yanlis
    kitaptan kirpildi; hata ancak sayfa 161 bulunamayinca ortaya cikti.

    Kural: kaynak dizin SECILMEZ, DOGRULANIR. Desen dar olmali, eslesme tek
    olmali, ve dizinin kimligi olculen bir degerle (sayfa sayisi)
    karsilastirilmali.

# 345 2025 AYT Kimya Soru Bankasi -- uretim yontemi ve olcumler

Kaynak: `veriseti/zkitap/screenshots/345 2025 Ayt Kimya Soru Bankasi/`
(336 PNG + PDF; ikisi de git disinda). Veri dosyalari
`veriseti/zkitap/cikti/345_2025_ayt_kimya_*.json`. Faz 0 kesif fisi:
`KIM_345_AYT_KESIF.md`. Hat, 345 2025 AYT Matematik hattinin
(`MAT_345_AYT_YONTEM.md`) kimyaya uyarlanmis kopyasidir; farklar asagida.

| arac | is |
|---|---|
| `scripts/kitap/kim345ayt_tarama.py` | capa taramasi (simge, basili numara, ara cizgi) |
| `scripts/kitap/kim345ayt_kutu.py` | kirpim kutulari (+ `numara_disk_ortulu`, konu kutusu kenari) |
| `scripts/kitap/kim345ayt_kirp.py` | soru gorselleri + ortme / kenar olcumu |
| `scripts/kitap/kim345ayt_metin_harness.py` | transkripsiyon gruplari + kapilar |
| `scripts/kitap/kim345ayt_ithal.py` | PASIF ithal |
| `alembic 0049_kim345ayt_agac` | konu agaci (KIM-345A25: 12 unite + 50 konu) |
| `alembic 0050_kim345ayt_kaynak_adi` | eski hat source_book yazim duzeltmesi (161 satir) |
| `alembic 0051_kim345ayt_eski_cevap` | 6 eski hat satiri kitabin basili haline |
| `alembic 0052_kim345ayt_eski_etiket` | eski hat TYT etiketi -> AYT (268), TYT konu dugumu -> kitabin dugumu (117), ikiz pasif (1) |

Hicbir soru cozulmedi; hicbir cevap uretilmedi.

## 0. Hangi baski, kaynak ve tavani

Iki yakalama var (`345 2024 Ayt Kimya`, `345 2025 Ayt Kimya`), ikisi de 336
sayfa. Durum raporu 2025'i 2024'un kopyasi sayiyordu; olcum (KESIF K0.0):
sha256 ozdes sayfa 0/336, ~13 soru sayfasinda soru degismis -- iki ayri
baski. **2025 islendi.** 2024 yalniz eski hat celiskilerinde ayni sayfanin
seridini karsilastirmak icin acildi (bolum 7).

Sayfa karti `(589, 43) - (1331, 1020)` = 742x977 (MAT hattiyla ayni).
Basili sayfa numarasi dosya numarasiyla ayni.

| kalem | deger | kanal |
|---|---|---|
| toplam sayfa | 336 | dosya sayimi |
| on sayfalar | 1-4 (kapak, kunye, icindekiler 3-4) | goz |
| unite ayraci | 12 (5, 39, 71, 107, 127, 151, 175, 205, 243, 265, 295, 325) | kenar doygunlugu + goz |
| soru sayfasi | 316 | cevap satiri |
| test | 160 | cevap satiri numaralandirmasi |
| soru | 1304 | cevap satiri (x2) + transkripsiyon |

Kitap KONU ANLATIMLI: bir sutunu konu anlatimi olan sayfalarda o sutunda
cevap seridi yok; kutu yalniz seridi olan sutunda uretilir.

## 1. Cevap anahtari -- sayfa alti satir, iki okuma + piksel kanali

Anahtar her soru sayfasinin altinda, sutun basina ayri basili satir (kart
y 899-904). `345_2025_ayt_kimya_cevap_anahtari.json`; ham okumalar
`345_2025_ayt_kimya_ham_okumalar.json`.

| | okuma A | okuma B |
|---|---|---|
| olcek | 5x | 7x |
| montaj | 12 satir | 9 satir |
| sira | sayfa sirasinda | TERS |
| girdi sayisi okuyucuya soylendi mi | hayir | hayir |

* Serit dedektoru (y 899-904'te gri murekkep VE y 878-897 bos) ilk surumde
  4 yariyi (s53R, s66R, s120L, s292L) kacirdi: sik alt simgesi banda
  sarkiyor. Esik gevsetildi (ust bantta < 100 piksel); bu 4 yari ayri 7x
  montajda bir ajan + goz ile okundu (A tarafinda goz, B tarafinda ajan).
* A == B: **1304/1304** girdi, harf ve numara duzeyinde fark 0.
* Ucuncu kanal (piksel): harf glifi en-yakin-komsu, birini-disarida-birak.
  1282 glif segmente edildi, LOO uyumu **1253/1282** (B/E glifleri 8 px
  yukseklikte birbirine yakin).
* Piksel kanalinin uyusmadigi 29 girdi, segmentasyonun kapsamadigi 9 yari
  (18 girdi) ve okuyuculardan birinin '?' ile tereddut isaretledigi 211
  girdi -- toplam 200 yari serit -- 6x en-yakin-komsu kontrast buyutmesiyle
  gozle tek tek incelendi: hepsinde iki okumanin harfi dogru; rakam
  belirsizligi numara surekliligiyle kapaniyor.
* Numara kitap boyunca ya oncekinin +1'i ya da 1: 160 test, baska kopma yok.
* Testlerin 141'i 2, 13'u 1, 3'u 3, 3'u 4 sayfa; sayfalar hep ardisik.

Kaynak dagilimi (`cevap_okuma_kanali`): `iki_okuma+piksel` 1054,
`iki_okuma(biri_tereddutlu)+goz` 211, `iki_okuma+piksel_supheli+goz` 21,
`iki_okuma+goz(piksel_kapsam_disi)` 18. Harf: A 155, B 249, C 304, D 296,
E 300.

## 2. Konu agaci -- kitabin kendi icindekiler sayfasi (0049)

Icindekiler (dosya 3-4): 12 unite, 50 konu ve her konunun basili baslangic
sayfasi (KESIF K0.2). Bagimsiz ikinci kanal: her testin ilk sayfasindaki
baslik bandi (160 bant, ayri okuyucu, `ham_okumalar.json` > `bant_okumasi`):

* test turu: Kazanim Odakli 100 test / 834 soru, OSYM Tadinda 48 / 430,
  Orijinal Sorular 12 / 40;
* 160 testin 160'i tek bir icindekiler araligina dusuyor;
* 100 Kazanim Odakli bandinin 100'unde bant bolum no == konunun unite ici
  sirasi ve bant basligi == icindekiler konu adi (ASCII katlanmis; 9
  noktalama / on-ek farki `bant_esleme`de acik);
* 48 OSYM Tadinda bandinin 48'i kendi unitesinin adini basar;
* K parca no her konuda, O ve R sirasi her unitede 1'den kesintisiz; 50
  konunun 50'sinde en az bir K testi var.

**Baglanti duzeyi.** Kazanim Odakli sorular KONU dugumune (834), OSYM
Tadinda ve Orijinal sorular UNITE dugumune (470) baglanir
(`konu_eslesme_duzeyi`). Bu testler kitapta unite sonunda, uniteyi bir
butun olarak yoklar; bir konuya dagitmak uydurma olurdu. 62 dugumun 62'si
soru tasir.

## 3. Kirpim kutulari -- iki capa kanali, kitabin anahtari secer

| kanal | olcum |
|---|---|
| okuyucu simgesi | 1376 simge (konu baslik simgeleri dahil) |
| basili numara | 1507 numara (konu kutusundaki genis mavi rakamlar dahil) |

553 soru sutununda secilen kanal: numara 524, simge 25, birlesik 3,
numara_alt 1; kutusuz sutun **0**. Kutular cevap satirina ulasmiyor
(`SAYFA_ALTI` 896 < 899).

MAT hattina gore olculen ve DUZELTILEN kusurlar:

| kusur | nasil yakalandi | duzeltme |
|---|---|---|
| konu kutusundaki genis mavi rakamlar numara capasi sanildi | kanal sayisi cevap satiriyla tutmadi | numara genisligi <= 12 px suzgeci once uygulanir |
| bazi sutunlarda ne numara ne simge sayisi tutuyor | kutusuz sutun raporu | iki kanalin BIRLESIGI (ayni soruyu gosteren numara+simge 15 px icinde tek capa), fazlaysa en alttaki k tanesi |
| konu anlatimi kutusunun kalin acik mavi sag kenari ara cizgi sanildi, sag sutun kirpimina girdi | kenar kapisi 250 isabet | sol sinir bandin sonuna kaydirilir (`ayrac_bandi_sonu`, 95 kutu); kenar kapisi 3 |
| diskin numarayi ortugu 3 kutu kapiya takildi | KAPI2 | `DISK_NUMARA_EN_AZ` 14 -> 16 (numara bolgesi koyu piksel mod 17-18, bos kalanlar <= 15) |

Kalan 3 kenar kapisi isabeti (T066_03, T111_01, T148_02) soru kutusunun
kendi cercevesi; metin kesilmiyor. OSYM kosesi logosu kurali 90 kutuda,
`logo_yakin_secenek` 1 kutuda uygulandi; ust kesimi metne degen kutu 0.

## 4. Transkripsiyon

1304 kirpim 2x Lanczos, test sinirina hizali 21 grup; her grubu ayri okuyucu
okudu (talimat `VeraFilm/k_metin_talimat.md`, git disi). Okuyuculara anahtar
SOYLENMEDI. Kimya yazimi sozlesmesi: alt indis `_`, ust indis/yuk `^`
(`Cu^(2+)`), ok `U+2192` / denge `U+21CC`, eksi `U+2212`, fiziksel hal
`(g)`, yapi formulleri satir duzeniyle.

Kapilar (`kim345ayt_metin_harness.py kapi`) YESIL:

| kapi | sonuc |
|---|---|
| her kirpim tam bir kez | 1304/1304 |
| basili numara == test ici sira | 1270/1304 esit; 34 bos, hepsi disk altinda |
| bes sik dolu | 1304/1304 |

34 bos numaranin 25'i simge, 2'si birlesik capali; 7'sinde capa basili
numaradan alinmisti ama disk numarayi ortuyor (`numara_disk_ortulu`, 57
kutu).

Olculen capalar: sekilli 544, siklari gorsel 12, 'OSYM KOSESI' etiketli 94
(hepsi AYT, 2018-2025), kaynak kusuru notu 278.

## 4a. Iyon yuku isareti -- '?' kurali ve hakemlik

Bu kitabin ekran goruntusunde ust indisteki `+` isaretinin bir cizgisi sik
sik kaybolur: dikey kaybolunca `-` gibi, yatay kaybolunca `'` gibi gorunur
(or. `Na'`, `Pb^(2')`). 2024 yakalamasi ayni pikselleri tasir (yalniz
okuyucu simgeleri farkli); ek bilgi vermez.

Sahip onayli kural: isaret belirsizse `+` ya da `-` SECILMEZ, `?` yazilir
(`Cu^(2?)`, `Ag^?`) ve `kaynak_kusuru`na "X yuk isareti belirsiz" notu
duser. Hakem kurali (`k_isaret*/talimat.md`, git disi): iki cizgi -> `+`;
tek temiz yatay cizgi ve ayni kirpimdaki acik `-` ile ayni -> `-`; diger
her durum -> `?`. Kimya bilgisiyle "dogrusu budur" diye secilmez. Kapsam
disi: 10'un usu, alt/ust indis rakamlari, iki madde arasindaki `+`, `e^-`.
Rakam belirsizlikleri (6/8, 2/4 ...) en iyi piksel okumasi + not (MAT
emsali).

* Ilk hakemlik: notunda isaret belirsizligi gecen 57 soru -> 47'sinde metin
  degisti.
* Hedefli ikinci okuma (bolum 4b): iyon yuku gecen ve ilk hakemlikten
  gecmemis 124 soru -> 68'inde metin degisti. Iki ust yazma ana hakemden
  (goz): T099_02 `H^-` -> `H^?` (cizgi ayni kirpimdaki `X^-`den belirgin
  acik), T152_01 `Cu^(2-)` -> `Cu^(2?)` (kirpimda karsilastirilacak `-`
  yok).

Sonuc: iyon yuku tasiyan **178 sorunun 178'i** hakemden gecti
(`hakem_notu`); her `?` isaretli soruda not var (test civili).

## 4b. Ikinci okuma -- orneklemle karar, hedefli tabaka

Kural OLCUMDEN ONCE yazildi (`345_2025_ayt_kimya_ikinci_okuma.json` ->
`on_kayit`): 21 grubun her birinden 10 soru (tohum 20260925), 210 soru;
ikinci okuyucular ilk okumayi GORMEDI; ayni talimat, ayni kirpim. Esasli
hata: kimyayi/anlami degistiren fark (rakam, isaret, element/formul, yuk,
eksik/fazla ifade, yanlis sik); yazim bicimi, noktalama, Turkce ek esasli
degil; ilk okumanin notunda AYNEN belgelenmis piksel belirsizligi esasli
hata sayilmaz. Karar: 95% Clopper-Pearson ust siniri <= %3 -> tam ikinci
okuma yok; > %3 ve tabakada -> yalniz o tabaka.

Olcum: 162/210 ayni, 48 farkli; her fark kirpima (gerekirse 3x) bakilarak
hukme baglandi:

| hukum | n |
|---|---|
| ilk okuma hatasi (esasli) | 5 -- T006_08, T054_01, T094_09, T105_08, T105_10 |
| belgelenmis belirsizlik | 10 |
| ikinci okuma hatasi | 11 (cogu yapi formulunu atlamis) |
| esdeger yazim | 22 (ondalik ayrac, noktalama, gorsel sik bicimi) |

Ust sinir 5/210 = **%5.47** > %3. Bes hatanin BESI de ayni ozellikte: `+`
isaretinin yatay cizgisi kaybolmus (`'`), ilk okuma `+` yazmis; hepsi ilk
hakemligin (not tabanli secim) disinda kalmis. Karar: **HEDEFLI ikinci
okuma** -- tabaka = iyon yuklu ve hakemden gecmemis 124 soru (4 hakem, ayni
kural; bolum 4a). Tabaka disi esasli hata orneklemde 0.

Ithal bu duzeltmelerden SONRA yapildigi icin (MAT'in 0048'inden farkli)
DB'de id sabitlemesi gerekmez.

## 5. Ortme

Okuyucu diski beyazlatildi; diskin kenar halkasinda kitap murekkebi olculen
**94 soru** `okuyucu_diski_ortme` bayragi tasir. 2024 yakalamasinda simgeler
farkli yerde (KESIF K0.4) -- kurtarma kanali VAR, bu ithalde KULLANILMADI
(borc).

## 6. Mukerrer adaylari -- isaretlendi, silinmedi

DB'deki 3551 KIMYA satirina karsi govde kelime kumesi Jaccard >= 0.75: 305
aday; GUCLU (ayrica bes sikkin >= 3'u birebir): **211** (345 2024 AYT eski
hat 108, 345 2025 AYT eski hat 90, OSYM 2025 AYT 6, diger 7). 211'in
205'inde DB cevap harfi bizimle ayni; 6 harf celiskisi bolum 7'de. Bu
kitabin 1304 sorusu hash duzeyinde birbirinden ve DB'den farkli.

## 7. Eski hat satirlari (0050, 0051, 0052)

DB'de bu kitaptan eski hattan (kiro2_batch_v4.14e, gemini) 363 AKTIF +
PUBLIC satir var: `345 2025 Ayt Kimya Soru Bankas<U+0131>` 161 (43 AYT,
118 TYT etiketli), `345 2024 Ayt Kimya Soru Bankas<U+0131>` 202.

**0050** -- 2025 yazimi yeni ASCII adla ayni anahtara cozuluyor; yalniz
`source_book` duzeltilir (161 satir, geri alinabilir). 2024, '345 2025 Tyt
Kimya' ve '345 Tyt Kimya' farkli anahtar, dokunulmadi. 'TYT' etiketi 0050'de
degismedi; 0052'de duzeltildi.

**0051** -- sahip karari (24 Eyl 2026): "kitabin basili cevabi baz alinir".
Eski hattin 363 satirinin HER biri icin bu kitaptaki en iyi soru bulundu
(mukerrer taramasi soru basina en iyi satiri aldigi icin ikizleri
kaciriyordu); cevap ICERIGI karsilastirildi. 7 aktif satir basili anahtarla
celisiyor; 6'si duzeltildi:

| satir | etiket / sayfa | DB | basili | eski hattin okuma hatasi |
|---|---|---|---|---|
| a0ee5afc | 2025 s32 sol 2 | A | E | `Cr^+` -> `Cr^{2+}`; sik B/D yer degismis |
| 118a2a68 | 2024 s36 sol 2 | A | E | `np^5` -> `np^3`, 'bir grubundaki' -> 'II. grubundaki' |
| 2e60703b | 2025 s129 sag 6 | A | E | metin ve sikler basiliyla ayni |
| 6453cd45 | 2024 s33 sol 9 | E | D | sik D/E alt indisleri yer degismis (`N_2O_5` / `P_2O_3`) |
| 076f3caa | 2024 s207 sol 1 | C | E | 'yukseltgendir' -> 'yukseltgenir' |
| 53c380ed | 2025 s289 sol 6 | B | A | `C_4H_8` -> `C_2H_6`, 11 -> 7 sigma, sik B |

Basili seritler 3x en-yakin-komsu buyutmeyle gozle okundu; 2024 etiketli
satirlarin sayfalarinda 2024 yakalamasinin serit satirlari 2025 ile piksel
olarak ayni. Eski hattin metni ya da siki basilidan farkliysa eski cevap o
bozuk icerigin cevabidir; yalniz cevabi degistirmek satiri kendi icinde
tutarsiz birakacagi icin metin parcasi / sik da basili hale getirildi,
basili sonuca celisen cozum ozeti NULL yapildi, soru_hash yeniden
hesaplandi (cakisma 0). Guard: id + eski hash + eski cevap + her parca tam
bir kez + her sik beklenen eski degerde. Yerel DB'de 0048 -> 0051 -> 0048
-> 0051 gidis-donus olculdu (62 dugum, 161 ad, 6 satir; downgrade hepsini
geri koydu).

**7. celiski -- ikiz pasif (0052):** 0344bdd2 (2024 etiketi, s129 sag 6)
2e60703b'nin ikizi; sik D/E yanlis okunmus, dogru icerik siklarinda yok.
Basiliya cekilirse 2e60703b ile ayni aktif hash'i alirdi
(`uq_qb_soru_hash_active`). Sahip karari (25 Eyl): ikiz pasif; 0052
`is_active = FALSE` yapar (silinmez, gunluklu). Ogrenciye 0051 ile basili
cevaba cekilen 2e60703b kalir.

**0052 -- TYT etiketi ve konu dugumu.** Sahip karari (25 Eyl): "COZ".
Eski hattin bu kitaptan gelen 268 satiri `exam_type='TYT'` etiketliydi
(2025 etiketi 118, ayni kitabin 2024 baskisi etiketi 150). Kanit: sayfalari
kitabin 7-336 araliginda ve 12 unitenin 12'sinde; 244'u bu kitabin modern
sorusuyla govde Jaccard >= 0.75 eslesiyor (263'u >= 0.5); grade_level
hepsinde 12. -> `exam_type = 'AYT'`. Bu satirlarin 117'si TYT agacindaki bir
dugume (TYT-KIM-*) bagliydi; AYT etiketiyle celisir. Yeni dugum KIM-345A25
(0049) agacindan, yalniz guvenli kanitla: 104'unde bu kitaptaki en iyi soru
(Jaccard >= 0.75) AYNI basili sayfada -> o sorunun testinin dugumu; 13'unde
sayfadaki tum testler ayni dugumde. KIM / KIM.ASI/DEN/ORG/TER konulu
satirlara dokunulmadi. Yerel DB'de 0051 -> 0052 -> 0051 -> 0052 gidis-donus:
363 satirin (exam_type, dugum, aktiflik) parmak izi iki yonde birebir.
Not: `v_safe_for_beta` is_active'i kendisi suzmez (0009 pasifleri de gorunur);
`core/quality_gate.py` kurali geregi her ogrenci sorgusu is_active'i AYRICA
uygular.

Harf farkli ama icerik ayni: 096bab8a (s291 sol 8, 'I ve III'; eski hatta
sik C/D yer degismis) -- cevap icerigi dogru, dokunulmadi.

## 8. Alanlar ve kaynaklari

| alan | kaynak |
|---|---|
| `question_text`, `a..e` | kirpimdan gorsel okuma (21 grup + 181 yuk isareti hakemi) |
| `correct_answer` | sayfa alti cevap satiri, iki okuma + piksel + goz |
| `explanation` | NULL -- kitapta cozum yok, uydurulmadi |
| `question_image_url` | tam soru kirpimi `/static/crops/KIM345_AYT/` |
| `exam_type`, `subject_area` | `AYT`, `KIMYA` |
| `primary_topic_id` | KIM-345A25 konu (834) ya da unite (470) dugumu |
| `source_page` | dosya no (= basili no) |
| `osym_year`, `osym_format_compliant` | yalniz OSYM kosesi etiketli 94 soruda |

Ithal PASIF: `is_active=FALSE, is_public=FALSE, is_ai_generated=TRUE,
review_status='PENDING'`. Yerel DB olcumu: 1304 satir yazildi, aktif 0,
beta gorunumu 0; ikinci kosum 0 satir yazar.

## 9. Bilinen borc

1. Ikinci okuma HEDEFLI yapildi (yuk isareti tabakasi); tabaka disi sorular
   tam ikinci okunmadi (orneklemde tabaka disi esasli hata 0).
2. 94 soruda okuyucu diski ortme suphesi; 2024 kurtarma kanali kullanilmadi.
3. 278 soruda kaynak kusuru notu (yuk isareti `?`, 6/8 gibi rakam
   belirsizlikleri); bayrakli. 14 soruda iki sik ayni gorunuyor
   (`sik_tekrar`; 11'i gorsel sik, 3'u belgelenmis rakam belirsizligi:
   T091_10, T096_08, T152_02).
4. 211 guclu mukerrer aday; birlestirme/eleme karari verilmedi.
5. Eski hat: ikiz 0344bdd2 pasif, TYT etiketi ve TYT dugumleri 0052 ile
   duzeltildi (bolum 7); eski
   hattin 19 guclu eslesmesinde cevap harfi ya da sik icerigi bu kitabin
   okumasindan farkli; 7'si cevap celiskisi (bolum 7), kalanlarda cevap
   harfi ayni ama sik metni farkli (or. T070_01 E sikki: eski hat '0,6',
   bu okuma '0,5') -- kapsam cevap celiskisiyle sinirli tutuldu, bu satirlar
   gozle incelenmedi.
6. 2024 baskisinda olup 2025'te olmayan ~13 soru islenmedi.
7. 12 soruda siklar gorsel; soru gorselle birlikte gosterilmeli.

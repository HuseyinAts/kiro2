## KIRO2 Nedir, Şu An Nerede, Nereye Gidiyor (teknik olmayan özet — 16 Ağustos 2026)

**Nedir:** KIRO2, Türkiye'de üniversite giriş sınavına (YKS/TYT/AYT) hazırlanan
öğrenciler için bir çalışma platformu. Amaç her öğrenciye tam ona göre bir
çalışma deneyimi sunmak: çok kolay soruyla zaman kaybettirmemek, çok zor
soruyla moralini bozmamak, unutmaya başladığı konuyu tam zamanında hatırlatmak.

**Elde ne var:**
- ~188 bin soru — bunların ~111 bini şu an aktif kullanılabilir, ~25 bini de
  ayrıca kalite kontrolünden geçip "öğrenciye güvenle gösterilebilir" diye
  işaretlenmiş bir havuzda.
- 405 kaynak kitaptan derlenmiş içerik.
- Öğrencinin hangi konuda zayıf olduğunu tahmin eden, ne zaman tekrar etmesi
  gerektiğini hatırlatan, kişiye özel çalışma planı çıkaran bir motor.
- Öğretmen sınıfını takip edebiliyor, veli çocuğunun ilerlemesini görebiliyor.

**Şu an neyle uğraşıyoruz:** Platform aylardır büyüyor; bir ara hız kazanmak
için kısayollar alındı — geçen ay bir yapay zekâ aracının devraldığı bir
dönemde, kod tabanına gözden geçirilmeden ve test edilmeden çok fazla
değişiklik girdi. Şu anki iş bunun temizliği: soru veritabanının iç yapısını
daha sağlam bir şekle sokuyoruz (tek büyük, hantal bir tabloyu yönetilebilir
parçalara ayırdık) ve bu ayırmanın her yerde doğru çalıştığını, tek tek test
yazarak kanıtlıyoruz. Sıkıcı ama gerekli bir iş — atlanırsa öğrenciye yanlış
soru gitmesi veya sistemin sessizce çökmesi gibi fark edilmesi zor hatalar
üretir.

**Nereye gidiyor:** Hedef, platformu öğrencilere doğrudan abonelik olarak
sunmak (okul/kurum üzerinden değil, öğrencinin kendisinin abone olduğu bir
model). Bunun için önce birkaç güvenlik ve sağlamlık kapısının kapanması
gerekiyor: kimin neyi görebileceğinin sıkılaştırılması, verinin tutarlılığının
garanti altına alınması, testlerin platformun büyük bölümünü kapsıyor olması.
Bu kapıların çoğu ya kapandı ya da kapanmak üzere.

**Özetle:** İçerik ve zekâ tarafı zengin ve büyük ölçüde hazır; şu anki emek
bu zenginliğin üzerine sağlam ve güvenilir bir temel inşa etmek. O tamamlanınca
öğrencilere açılış için teknik bir engel kalmayacak.

---

## 📦 Önceki oturumlar arşivde

S215…S233 devir notları (2.206 satır) `.claude/sessions/arsiv/2026-08_S215-S233.md`
dosyasına **birebir** taşındı — silinmedi. Bu dosya bundan sonra yalnız **son 3**
oturumu tutar; kapanan her oturumda en eskisi arşive iner.

Gerekçe (20 Ağu 2026 ölçümü): dosya 2.605 satır / 185 KB'a ulaşmıştı ve tek okumada
25K token tavanına çarpıyordu — devri okumak, devrin kendisinden pahalı hale gelmişti.

---

## Session Handoff — 2026-08-20 (S241 · A1 ALTIN YOL ÖLÇÜLDÜ + CEVAP SIZINTISI KAPATILDI)
**Branch:** feature/self-evolution-optimization · **Son commit:** `adcadb61d` · **Push:** ✅ 0 bekleyen
**Uncommitted:** yalnız devralınan `backend/semantic_cache.pkl`

### Bu oturumun tek cümlesi
A1'in dört ayağı ilk kez uçtan uca ölçüldü (11 ajan, 45 bulgu, 44 ayakta) ve
**beş ölçücünün hiçbirinin bulamadığı** P0 kapatıldı: düz öğrenci token'ı cevap
anahtarını okuyabiliyordu.

### Yapılanlar
- `fa1784215` tasarım · `0973e5495` plan · `3a4b4bae7` denetim raporu
  (`docs/audits/2026-08-20_a1_altin_yol_olcum.md`)
- 🟢 `a664c2d5e` + `adcadb61d` **cevap sızıntısı KAPATILDI** — `core/cevap_kapisi.py`
  (YENİ, tek kaynak) + 3 uç kablolandı + 13 test. Canlı: 4/4 uç `200 TEMIZ`, gövde dolu.
- Defter **155 → 156**; zorlayıcı liste **24 → 25 dosya**, kapı **264 passed / 1 xfailed / 0 failed**

### A1'in dört ayağı (kanıtlı yargı)
```
L1 Kayit      CALISIYOR  mutlu yol acik; username carpismasi 500 (commands/auth.py:100)
L2 Dogrulama  YOK        1119 yolda uc yok; is_verified'i TRUE yapan TEK SATIR yok
L3 Sinav      KIRIK      secim DOGRU (40/40 kapida, 11-13 konu), teslim OLU
L4 Puanlama   KIRIK      tamami erisilemez + "konu" kirilimi aslinda DERS kirilimi
L5 Yuzey      KIRIK      sayfa saglam, ilk yazma adimi 500
```

### 🔴 AÇIK P0 — B1: `exam_sessions` RLS (A1'in tek ve asıl engeli)
Üç ayağı birden öldürüyor. `exam_sessions` politikası **fail-closed**; GUC
`core/dependencies.py:455`'te *transaction-local* set ediliyor ama motor
`core/osym_exam_engine.py:441`'de **ayrı bağlantı** açıyor. Backend `kiro2_app`
(`rolbypassrls=f`). **`exam_sessions` = 0 satır, bugüne kadar.**
`dependencies.py:456` yorumu sebebi belgeliyor: *"App superuser (postgres)
olduğundan RLS bypass edilir"* — varsayım bayatlamış.

### Sonraki Adımlar (maks 5)
1. **B1 RLS** — altın yolu açan tek fix. Motoru istek-kapsamlı oturuma bağla
   VEYA GUC'u motorun bağlantısında set et. Kiracılık izolasyonunu bozma.
2. **B3 konu kırılımı** — `osym_exam_engine.py:1364` `subject_area` → `topic_hierarchy.code`;
   `QuestionResponse.topic` ham UUID yerine konu kodu. B1 onarılsa bile A1'in 4. ayağı bunsuz karşılanmaz.
3. **B4 e-posta doğrulama** — yol **yok**, inşa kararı bekliyor (SMTP ayrı iş).
4. **B5 username 500** — `commands/auth.py:100`, 409/422 dön + benzersiz username türet.
5. Eksiklik eleştirmeninin 13 boşluğu — özellikle offline sync paketi (tasarım gereği
   `correct_answer` taşıyor, şu an 500 olduğu için sızmıyor) ve sınav süresi hiç zorlanmıyor.

### Kararlar (gelecek session tekrar tartışmasın)
- **Cevap alanları cache'e TAM yazılır, ÇIKIŞTA temizlenir.** Cache anahtarı rol taşımıyor;
  role göre cache'lemek öğretmenin girdisini öğrenciye servis ederdi. Bu yüzden
  `cevaplari_ele` **saf olmak zorunda** (çivi: `test_girdi_sozlugu_degistirilmez`).
- **MEMORY.md'deki "RLS GUC set edilmezse tüm satırlar geçer" ÇÜRÜDÜ** — 73 politika
  fail-closed / 6 permissive. Bu yanlış kayıt B1'in görülmesini geciktirmiş olabilir.
- **`bandit`/`mypy` SKIP'i ölçüldü, benim kodum değil** — değişikliklerim stash'liyken
  aynı dosyada HEAD üzerinde aynı 2 mypy hatası; bandit B311 dokunmadığım satırlarda.
  `osym_questions_api.py`'nin önceden var olan borcu, **ayrı açık iş**.

### Dürüst kayıt — bu turda 5 kez yanıldım, 4'ü kayıtlı ders
1. **Kendi ölçüm aletim 3 kez** yanlış "0/boş" verdi: `LIKE 'MAT%'` (kolon UUID),
   `information_schema` (matview `pg_attribute`'da), `/api/v1/sorular` (uç kök yolda).
2. **Biçimlendirici import'u sildi** (`reference_formatter-import-stripping`) →
   canlıda `name 'cevaplari_ele' is not defined` 500. Deploy edip **ölçtüğüm için**
   yakalandı; ölçmeseydim "fix bitti" derdim ve iki uç 500 kalırdı.
3. **Yarım commit**: `git stash pop` index'e değil çalışma ağacına koydu, `git add`'im
   uçtu; `EXIT=0` + yeni hash geldi ama `osym_questions_api.py` **girmemişti**.
   `git show --stat HEAD` yakaladı.
4. **CRLF**: `printf` ile `.gitignore`'a LF yazdım, `mixed-line-ending` commit'i düşürdü.
5. **N802 ONUNCU kez** (6 test adı). S240 bunu görünür kılmak için hook enforcement'ı
   eklemişti — **bu turda bana görünmedi**, ancak `pre-commit` yakaladı. **Y13 yeniden açık.**

---

## Session Handoff — 2026-08-20 (S239 · MAT/TYT GOCU KALICI) ✅

**Branch:** feature/self-evolution-optimization · **Son commit:** `1b3285d1c` · **Push:** ⏳ 4 commit
**Canli DB:** `question_bank` **3.616 → 4.064** (+448 MAT/TYT) · kapi **0** (yeni parti `pending`, KASITLI)

### Bu oturumun tek cumlesi
448 TYT MATEMATIK sorusu, **her crop'u tek tek gozle okunmus** olarak kalici yazildi;
ama asil ders, kendi AYT-kontrolumun **yanlis katmanda** olcup yesil vermesi oldu.

### Yapilanlar
- `ec40e2b2c` revize plan — eski planin **T2'si IPTAL** (MAT-T1 kitap katmanini curuttu:
  9/354 = %2,54, kitap sinyali orneklem gurultusuyle ayni). Eski plandaki TUM taban sayilari
  bayatti; "kapsam disi 386" **871** olctu.
- `505a4ab28` `y11_aday_uret.py` + 7 bekci (TDD). Konu suzgeci ZORUNLU (871 eleniyor, yoksa
  yukleyici TEK transaction'da tumden duser). Determinizm birebir + girdi sirasindan bagimsiz.
  Cikti yazicisi trailing-newline uretiyor — kanca ciktiyi yamamak yerine YAZICI duzeltildi.
- 🟢 `1b3285d1c` **KOR OKUMA: 586/586 crop, 15 ajan, 0 acilamayan** → 16 sizdiran **%2,73**.
  **BAGIMSIZ TEKRARLAMA**: MAT-T1 farkli orneklemde %2,54; havuzlanmis 25/940 = %2,66.
- PROVA 544 → sapma `[]`, yetim 0. **10 soru tek tek cozuldu: 9/10** (esik >=8/10).
- KALICI 448. Gorsel 40/40 container'dan. Idempotens: capraz-DB elenen **448**.

### 🔴 KENDI KONTROLUM YANLIS KATMANDA OLCTU (durust kayit)
A1 konu kirilimi **MAT.TRV 30 + MAT.INT 26 + MAT.LMT 28 + MAT.LOG 12 = 96** AYT sorusu
gosterdi. Ayni turda calistirdigim "AYT konusu kalan" olcumu **0** diyordu.
Sebep: metin regex'i. Sorularin METNINDE "turev" gecmiyor — *"cemberin icine cizilen
dikdortgenin alani en fazla kac cm2"* bir maks-min sorusu, digeri `f'(x)=0` notasyonlu.
Yargi metinde degil **`primary_topic_id`**'de yasiyor.
**Bu, MAT-T1'in kitap katmanini curuttugu hatanin BIREBIR AYNI SINIFI.** 96 satir silindi.

### Fail Eden Testler
**YOK.** `test_y11_aday_uret.py` 7 passed. Kapi (22 dosya) S238'de EXIT=0 dogrulanmisti.

### A1 KABUL (canli olculdu)
```
farkli konu kodu = 16   (kabul >=5)     3 kat
toplam soru      = 448  (kabul >=40)   11 kat
gorseli dolu     = 448/448     AYT konusu = 0     kapi = 0 (degismedi)
```

### Engelleyiciler
- Kapi hala **0** — terfi (`pending → auto_judged_high` + `REFRESH`) **AYRI ONAY** bekliyor.
  Bu tek adim platformu ilk kez gercek soru servis eder hale getirir.

### Sonraki Adimlar (maks 5)
1. **PUSH** — 4 commit.
2. **FAZ E terfi** (ayri onay): 448 MAT + 3.616 KIMYA `pending → auto_judged_high` + REFRESH.
3. **MAT.TRG (30) + MAT.DIZ (27) mufredat karari** — sinirda; temel trigonometri TYT'de var,
   ilerisi AYT'de. Kesin AYT olmadiklari icin silinmedi, karar bekliyor.
4. Kalan ~3.500 kapsanan MAT sorusu — kor okuma kapasitesi artirilirsa ayri turda.
5. Canlidaki 3.616 KIMYA'nin crop sizintisi **hic olculmedi** (~1.426 gorsel, ~%2,7 → ~38).

### Kararlar (gelecek session tekrar tartismasin)
- **Baglayici kisit ERISILEBILIRLIK degil DOGRULAMA KAPASITESI.** 5.420 aday vardi; 586
  secildi cunku kor okunabilecek buyukluk buydu. Dogrulanmamis icerik = S238'de sildigimiz sey.
- **"0 bulundu" her seferinde once ALET ARIZASI varsayilmali.** Bu oturumda iki kez oldu:
  biri gercekti (capraz-DB 0), biri yanlis katmandi (AYT metin regex'i 0).
- **exam_type GUVENILMEZ** — TYT etiketli dilimde %17,6 AYT konusu vardi.

---

### 🟢 EK — FAZ E KAPANDI: KAPI 0 → 3.615 (ayni oturum, kullanici onayiyla)

Kullanici (a) sikkini secti: **once KIMYA croplarini da kor okut, sonra ikisini
birlikte terfi ettir.** Karar dogru cikti.

**KIMYA kor okuma (evrenin TAMAMI):** 30 ajan x ~48, **1426/1426** okundu,
acilamayan 0, dusen ajan 0 -> **85 sizdiran = %5,96**.
🔴 MAT'in (%2,73) **iki katindan fazla**. Sizinti MODU da farkli: MAT'ta kenar
seridi anahtar listesi, KIMYA'da **cozumlu ornek blogu** (`Ornek: 6` -> `Cozum:`
-> `Cevap: D`) -- ders kitabi duzeni. MAT oranini genellemek ~38 tahmin ederdi,
gercek 85. **Katman degil ORAN da dersten derse degisiyor.** 85 satir SILINDI.

**FAZ E terfi:** yedek `question_statistics_terfi_yedek_20260820` (3.979 eski
durum) -> `auto_judged_high` -> `REFRESH MATERIALIZED VIEW`.
Onkosul ONCEDEN simule edilmisti (kapi ayrica `demoted_at` + tier1_page_inline
disliyor, bes bayraktan biri sart): 3.697 ongoruldu; silinen 85'in 82'si kapiya
girecekti -> 3.697-82 = **3.615**. **Tahmin birebir tuttu.**

**ASIL OLCUM (sayi vekildir, orneklem OKUNDU):**
```
S231 : kapidan 40 soru -> 0/40 servis edilebilir
simdi: kapidan 12 soru -> 12/12 gercek, tutarli, KITAP KAYNAKLI
       anahtarlar tek tek dogrulandi, 11'i kesin dogru
       1 zayif: fc87492b II. onculunde OCR bozuklugu
```

**Canli son durum:** `question_bank` **3.979** (KIMYA 3.531 + MAT 448) ·
kapi `mv_safe_for_beta` **3.615** (KIMYA 3.209 + MAT 406, damgasiz 0).

**Geri alma:** `UPDATE question_statistics qs SET quality_review_status=y.eski
FROM question_statistics_terfi_yedek_20260820 y WHERE y.id=qs.id;` + REFRESH.

**Yeni acik isler:** ES index'i hala eski kapidan (#433) · MAT.TRG/MAT.DIZ
mufredat karari · kalan ~3.500 MAT sorusu (kor okuma kapasitesi) ·
`question_bank_cop_yedek_20260820` 4x36.967 disk tutuyor.

---

### 🟢 EK 2 — S239 KAPANIS: #433 kok neden + mufredat temizligi + defter bosluğu

**#433 KAPANDI ama kayitli baslik YANLIS TESHISTI.** "ES index'ini yeniden kur"
diyordu; gercek kok neden bir **sema kacagi**: `core/es_index_schema.SORGU`
S210 split'inden (`0fd9b8413`) once yazilmisti ve `SELECT q.question_text ...
FROM question_bank q` diyordu. Split sonrasi o kolonlar yavru tablolarda.
Senkron HER kosumda `asyncpg.UndefinedColumnError` ile dusuyordu -> canli ES
index **AYLARDIR 0 dokuman**. Fix: `ALAN_KAYNAK` haritasi + dort tabloya JOIN.
Index **0 -> 3.560**, yasakli alan (correct_answer/explanation/is_active) YOK.
Bayat `_yedek_20260731` (64.270 dok, `correct_answer` TASIYORDU, silinmis
satirlarin projeksiyonuydu) **DROP edildi**. ES 127.0.0.1'e bagli, LAN'a acik degil.

🔴 **DEFTER BU KOR NOKTAYI ZATEN YAZMISTI VE BOSLUK ISIRDI.**
`L-s230-ast-sayaci-ham-sql-goremez`: *"ham SQL yapisal kor noktadir... ZORLAYICI
YOK, bu bosluk bilincli olarak gorunur birakildi."* Bugun ayni kor nokta ES
senkronunda tekrar etti. Bosluk kapatildi: o dersin `zorlayici` alani artik
`tests/integration/test_es_index_schema_split.py`. Bekci sorgunun METNINI okumaz,
**canli semaya karsi KOSTURUR** (AST tarayici string literal icini goremez).

**MUFREDAT: MAT.TRG + MAT.DIZ de AYT cikti.** Onceki turda "sinirda" deyip
birakmistim; ICERIK OKUNDU: TRG'de radyan trigonometrik ozdeslikler /
`tan(x+pi/3)` / `cos 235`, DIZ'de aritmetik-geometrik diziler (biri `sin 75`
kullaniyor). TYT'de ne trigonometri ne diziler var. **57 soru silindi**, zincir
tek turda hizalandi: DELETE -> REFRESH -> ES senkron.
Kumulatif AYT temizligi **179** (26 metin + 96 konu kodu + 57) —
`exam_type='TYT'` etiketinin guvenilmezlik olcusu.

**YEDEK TABLOLARI: KENDI ONERIMI GERI ALDIM.** "Disk tutuyor, dusurulebilir"
demistim; olculdu: **34 MB** (DB toplam 135 MB). 36.967 satirlik bir silmenin
TEK geri alma yolunu 34 MB icin yok etmek kotu takas. **TUTULACAK.**

### Canli son durum
```
question_bank 3.922   (KIMYA 3.531 + MAT 391)
KAPI          3.560   ES index 3.560 (birebir)
AYT konusu 0 | yetim 0 | A1: 14 konu / 391 soru (kabul >=5 / >=40)
```

### Kapi (defterden turetilen zorlayici liste)
```
22 dosya -> 23 dosya (ES bekcisi eklendi)
226 passed / 1 skipped / 1 xfailed / 0 failed   EXIT=0
```
Kalan tek xfail hacim tabani (3.922 < 150.000) ve DOGRU kirmizi.

### Yapilmayan (durust kayit)
- **Kalan ~3.500 MAT sorusu** — baglayici kisit kor okuma kapasitesi. Bu oturumda
  2.012 crop okundu (586 MAT + 1.426 KIMYA); kalan ayri tur isi.
- `MAT.IST` (15 soru) tek basina az; A1'i etkilemiyor ama dengesiz.

---
### Durust kayit — kayitli ders BU TURDA YINE ihlal edildi

`d03674d9d` commit mesajini `-m` ile ve icinde TERS TIRNAK ile verdim. Bash cift
tirnak icinde ters tirnagi komut olarak calistirdi:

    /usr/bin/bash: line 134: L-s230-ast-sayaci-ham-sql-goremez: command not found

Sonuc: mesaj govdesinde defter kimligi YUTULDU ("Defter  kaydinda ham SQL...").
Commit EXIT=0 verdi, push gecti — yani sessiz kayip. Kural (`L-s231-ters-tirnak`):
**commit mesajini DAIMA `git commit -F <dosya>` ile ver.**

Duzeltme yolu olarak `--amend` + force-push SECILMEDI: commit push'lanmisti ve
yayimlanmis gecmisi yeniden yazmak bir mesaj duzeltmesi icin orantisiz. Ankraj
zaten iki yerde duruyor: bu devir notu ve defterin kendisi
(`L-s230-ast-sayaci-ham-sql-goremez`, `zorlayici` alani artik dolu).

Bu oturumda tekrarlayan kayitli dersler: ters tirnak (1), `/tmp` ad-alani (1),
CRLF ankraj (1), N802 buyuk harfli test adi (**2** — 7. ve 8. tekrar, Y13 acik).

---

## Session Handoff — 2026-08-20 (S240 · TEKRARLAYAN DERSLERE ENFORCEMENT)
**Branch:** feature/self-evolution-optimization
**Son commit:** `476cdd6a8` fix(hook): pre-commit-check'teki 3 SESSIZ exception handler gorunur yapildi
**Uncommitted:** yalniz devralinan `backend/semantic_cache.pkl` (Bin 4892->4892, 0 satir)

### Yapilanlar
- `.claude/hooks/ders_dedektorleri.py` (YENI, 100 sat) — uc saf dedektor (`8ab187329`)
- `.claude/hooks/post-edit-format.py:53+` — `ruff check --output-format=concise` ikinci gecis;
  bulgular stderr'e. Once `--fix --quiet` + `capture_output=True` ile YAKALANIP ATILIYORDU
- `.claude/hooks/pre-commit-check.py:174-200` — ters tirnak BLOKLAR (exit 2), `/tmp` UYARIR
- `.claude/hooks/pre-commit-check.py:65,122,157` — 3 sessiz `except: pass` gorunur (`476cdd6a8`, #495'ten 3/15)
- `backend/tests/unit/test_hooks/test_ders_dedektorleri.py` (YENI, 24 test)
- `.claude/lessons/ders_kaydi.yaml` — `L-s231-ters-tirnak…` + `L-s233-ayni-linter…` `zorlayici` dolduruldu (23->24)
- `docs/superpowers/plans/2026-08-20-tekrarlayan-ders-enforcement.md` (plan)

### Fail Eden Testler
**YOK.** Kapi 24 dosya: **250 passed / 1 skipped / 1 xfailed / 0 failed** EXIT=0.
Dedektor 24 passed · hook bekcileri 216 passed · mutasyon **3/3 OLDU** (commit sonrasi).

### Engelleyiciler
**YOK.** Devralinan: SMTP kimlik bilgisi · odeme saglayicisi · alan adi+SSL (operator).

### Sonraki Adimlar (maks 5)
1. **Kalan ~3.500 MAT sorusu** — baglayici kisit kor okuma kapasitesi (bu oturumda 2.012 crop okundu)
2. `MAT.IST` 15 soruyla dengesiz — konu dagilimi duzeltmesi
3. #495 kalan **12** bos exception handler (`.claude/hooks` geneli)
4. CRLF cok satirli ankraj — enforcement noktasi YOK, bosluk GORUNUR birakildi
5. `question_bank_cop_yedek_20260820` (34 MB) — ikmal olgunlasana kadar TUTULACAK

### Kararlar (gelecek session tekrar tartismasin)
- **Y13 KAPANDI, S233 HAKLIYDI.** O tur kancayi degistirmeme karari vermisti (testsiz +
  gurultu olcumsuz + kapanista degistirme). Bugun tam o sartlarla yapildi.
- **Hipotez duzeldi:** N802'yi susturan `--quiet` DEGIL; `capture_output=True` ile
  yakalananin HIC OKUNMAMASI. ruff 0.14 yeni tani bicimi -> `--output-format=concise` sart.
- **`/tmp` bloklamaz, uyarir.** Mesru kullanimi var; bloklasak kapatilir, kontrol yine olur.
- **3 sessiz handler SKIP edilmedi.** Kontrol kolu (`git show HEAD~1`) onceden var oldugunu
  gosterdi (SKIP savunulabilirdi) ama bu tam olarak bu oturumun patolojisi.

### Durust kayit — bu turda 3 kez yanildim
1. Dedektor ILK gercek kullanimda **yanlis-pozitif** verdi, kendi defter guncellememi blokladi
   (heredoc'taki ders METNINI komut sandi) -> segment-basi daraltma + 3 regresyon testi
2. **N802 DOKUZUNCU kez** — tam da N802'yi zorlayan test dosyasinda (`VERI` buyuk harf)
3. Mutasyon harness'i "M3 GECERSIZ" dedi, **yanlisti**: gevsek `" error"` alt-dizesi testin
   kendi verisindeki "Found 2 errors."e esledi. Ozet satiri ayristirilinca 3/3 OLDU.

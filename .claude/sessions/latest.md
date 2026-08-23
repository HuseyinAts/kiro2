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

## Session Handoff — 2026-08-23 (S249 · AÇIK KALEMLER — 5 kalem kapandı)
**Branch:** feature/self-evolution-optimization · **Aralık:** `1212ccea0..0fc88b7f4` (11 commit)
**Uncommitted:** `backend/semantic_cache.pkl` (S244'ten devralındı, bu işe ait değil)
**Yöntem:** `superpowers:brainstorming` → spec → `writing-plans` → hibrit yürütme
(paralel ölçüm **workflow**'da, sıralı/git/tarayıcı işi ana bağlamda)
**Spec:** `docs/superpowers/specs/2026-08-23-acik-kalemler-design.md`
**Plan:** `docs/superpowers/plans/2026-08-23-acik-kalemler-uygulama.md` (11 task / 54 adım)

### Kapanan

| # | Kalem | Kabul kanıtı |
|---|---|---|
| **İ0** | Sıçramanın kök nedeni | `docs/audits/2026-08-23_i0_yonlendirme_kok_neden.md`. Belge **2 kez** yüklendi → sert gezinme; 401'ler stub'lanınca sıçrama **kayboldu** |
| **İ1** | Public-rota 401 muafiyeti | 🟢 **KULLANICI-GÖRÜNÜR.** Tarayıcı: 10 sn boyunca `/eposta-dogrula`'da **kaldı**, 250ms'de *"E-posta adresiniz doğrulandı"*. Regresyon 4/4 |
| **İ2** | `user_item_fsrs` + ayrışma kayması | Canlı `/fsrs/due`, `/due?mercy`, `/due-count` → **200** (öncesi 500) |
| **İ3** | X06 envanteri (kod yok) | `docs/audits/2026-08-23_x06_rol_kapisi_envanteri.md` — 23 tanım, **16'sı ölü**, 3 zıt yargı kanıtlandı |
| **İ5** | X11 2. kol | Karar C: docstring koda uyduruldu, özellik yazılmadı |
| **İ4** | Kütük | `dogrulandi` 4 → **3**, `uygulandi` 8 → **9** |

### Fail Eden Testler
**YOK.** `test_fsrs_schema_contract` **2 failed → 0** (12 passed) · frontend
`src/utils/__tests__` 86 passed · kütük bekçileri 23 passed · İ2 regresyon 32 passed.

### 🔴 Bu turda ÜÇ bekçi de ÖLÜ DOĞDU — üçünü de mutasyon yakaladı

*"Bir deseni **anlatan** yorum, o deseni **içerir**"* (`audit-methodology.md`) —
kural yazılıydı, **bir oturumda üç kez** ısırdı:

1. **İ2 bekçisi**: migration docstring'i tabloyu 20+ kez geçiyor, düz alt-dize
   araması onu *tanım* sandı → M1 hayatta kaldı. Fix: `tokenize`+`ast` ile
   yorum/docstring ayıklama. **M6** (kod ref'leri silindi, docstring'de 6 referans
   DURUYOR) → öldü. Bu, strip'in çalıştığının kanıtı.
2. **İ5 docstring'i** eski yalanı **alıntılıyordu** → `grep` yine **1** dönüyordu.
3. **İ5 bekçisi iki kez**: önce kendi docstring'imdeki `StudentAnswer` kelimesini
   "yazım var" sandı; düzeltince bu kez kendi `NOT PERSISTED` başlığımı **vaat**
   sandı (olumsuzlamayı görmüyordu) → `_vaat_bul()` olumsuzlama-farkındalığı.

**Mutasyon olmasaydı bugün üç işe yaramaz bekçi commit'lenmişti.**

### 🔴 Çürütülen kendi iddialarım
1. *"U25 ankrajı yok"* → **YANLIŞ**, `versions_archive/fa067642bdfe…` duruyor; yalnız `versions/` altına bakmıştım.
2. **Planımın Task 2 Adım 1'i yanlış dosyayı hedefliyordu** — squash **inline DDL içermiyor**, gövdeyi `baseline/*.sql`'den okuyor. Workflow ajanının kontrol kolu yakaladı (`question_bank` için de 0 döndü).
3. *"Rota bundle'da yok"* ×2 — biri yanlış dizin (`/assets` vs `/js`), biri minification (fonksiyon adı aranmaz, **dize** aranır).
4. *"Sayfa reload olup HTTP 400 gösteriyor"* → **deploy artığıydı**; SW güncelken ikinci koşum 10 sn kararlı. Az kalsın fantom raporluyordum.

### Engelleyiciler / açık kalemler
- 🔴 **Aynı squash (`e002f550b`) ikinci bir kurban yaratmış:** `test_rls_fail_closed_with_check.py`'nin ankraj migration'ı (`ad6ba3bbe485`) arşive taşınmış → **8 collection error**. Kontrol koluyla benim olmadığı doğrulandı. **Görev no atanmalı.**
- 🔴 `synced_count` fazla-raporluyor (`offline_sync_service.py:330`) — kütüğe yazıldı, davranış bilinçli değiştirilmedi.
- 🔴 `enhanced_authentication.py:381` **TypeError → HTTP 500** — bugün çağıranı 0, X06 birleştirmesinden **önce** kapatılmalı.
- ⚠️ Kapı borcu: `SKIP=bandit` ×3 — **üç kollu ölçüldü**, B608'ler `safe_for_beta_sql` deseninden, **6 dosyada** yaygın, HEAD'de birebir aynı.
- ⚠️ **İki commit sessizce düştü** (prettier auto-fix + stash çakışması). Hash ölçümü olmasaydı "girdi" sanılacaktı.

### Sonraki Adımlar (maks 5)
1. **SMTP** (#441, operatör) → sonra `EPOSTA_DOGRULAMA_ZORUNLU=true`.
2. `ad6ba3bbe485` ankrajı — RLS testinin 8 collection error'ı (squash'ın 2. kurbanı).
3. X06 birleştirme — **önce** kanon rol yazımını `psql` ile ölç, **sonra** `:381` TypeError→500'ü kapat.
4. U25 — `tests/test_migrations.py` `skipif(True)` kaldır veya downgrade'i CI'ya bağla.
5. X04 — CLAUDE.md 910 satır; kesme ayrı tur.

### Kararlar (gelecek oturum tekrar tartışmasın)
- **`PUBLIC_ROUTES` küratörlü liste, türetilmez.** App.tsx'te `ProtectedRoute` içermeyen 14 rota var ama yalnız 9'u anlamsal olarak public; `*` catch-all türetmeyle muaf olurdu. Spec'in "inşa ile tekillik" önerisi **ölçümle reddedildi**.
- **`env.py:84` yorumdan ÇIKARILMADI** — ölçüldü, **+0 değer**: `alembic_autogen_guard.py:82` yansıtılmış+metadata'sız her nesneyi zaten dışlıyor. Tekrar-DROP riski autogenerate'ten değil **squash**'tan geldi.
- **INNER JOIN seçildi, LEFT değil** — `fsrs_service.py:209` `float(row.irt_a)` None'da patlar. IRT varsayılanı **uydurulmadı** (adaptif seçimi etkiler). Güvenli: 3922/3922/3922/3922, yetim 0, IRT NULL 0.
- **Karşı-olgusalda EFEKTİ engellemek kırılgan, NEDENİ kaldırmak sağlam.** `location.href` redefine edilemez, `page.route` service worker'ı göremez, SW her yüklemede kendini yeniden kaydeder — üç deneme de başarısız. 401'leri stub'lamak ilk seferde çalıştı.

---

## Session Handoff — 2026-08-23 (S248 · L2 CANLIYA ALINDI + ölü-link kusuru kapandı)
**Branch:** feature/self-evolution-optimization · **Commit:** `9561654472`
**Uncommitted:** `backend/semantic_cache.pkl` (S244'ten devralındı, bu işe ait değil)

### Bağlam: bilgisayar kapandı, iş yarım kaldı → **kod kaybı SIFIR**
Ölçüldü: ağaç temiz, `origin` ile **0/0**, S247'nin 6 commit'i push'lu. Stash'lerin
hepsi **12 Ağu ve öncesi**. Kaybolan tek şey **çalışan altyapı**: Docker Desktop
kapanmıştı (PostgreSQL native servis olduğu için kendi dönmüştü).
⚠️ Oturum banner'ı `Backend=200 Frontend=200` diyordu — **bayat**; daemon'a pipe yoktu.

### 🔴 Bulunan kusur: doğrulama linkleri ÖLÜ PORTA gidiyordu
S247 L2'yi doğru kodladı, testleri yeşildi, uçları canlıydı — ama üretilen bağlantı
hiçbir yere gitmiyordu:
```
'FRONTEND_URL' in os.environ -> False      (compose'da HIC tanimli degil)
uretilen link -> http://localhost:3001/eposta-dogrula?token=...
curl :3001 -> 000  (baglanti yok)     curl :3000 -> 200  (frontend nginx)
```
**Kusur kodda DEĞİL**: `core/eposta_dogrulama.py:324` + `api/auth.py:2088`'deki `:3001`
varsayılanı Docker'sız yerel geliştirmede DOĞRU (Vite dev portu). Kusur compose'un
backend'e dağıtım gerçeğini hiç söylememesiydi → **tek satır**, Python'a dokunulmadı.
Etki iki akışta: L2 **ve** veli onayı. SMTP (#441) gelseydi ikisi de ölü doğacaktı.

**Bekçi:** `backend/tests/unit/test_compose_frontend_url.py` (5 test).
Port **sabit yazılmadı** — `assert port == 3000` totoloji olurdu. İki kaynak
karşılaştırılıyor: frontend'in YAYINLADIĞI host portu vs bağlantının portu.
TDD: RED 2F/3P → GREEN 9P. **Mutasyon 3/3 öldü**, üç geri alım da doğrulandı:
M1 satır silindi→**2** · M2 `3000`→`3001`→**1** · M3 frontend portu `3002`→**1**
(M3 kritik: testin sabit port beklemediğini kanıtlar). Kapı: pre-commit **24/24, SKIP YOK**.

### Canlıya alındı ve ÖLÇÜLDÜ
Backend + frontend **yeniden kuruldu ve recreate edildi** (env değişimi restart'la geçmez).
```
imaj ONCE 21 Agu 16:29 -> eposta_dogrulama.py YOK, auth.py grep 0
imaj SONRA              -> eposta_dogrulama.py VAR, auth.py grep 2
canli openapi yol sayisi: 1119 -> 1121   (+2 = tam olarak L2'nin iki ucu)
Redis token anahtari: kayit ONCE 0 -> SONRA 1     <- kayit tetikleyicisi KABLOLU
DB is_verified: False -> TRUE                      <- 21/21 false olan kolon ilk kez yukseldi
verify 200 · ayni token tekrar 400 (replay) · gonder 200 (notr mesaj) · login 200 (kapi kapali)
TARAYICI: POST /eposta-dogrula/verify -> 200, DB True
```
Düz metin token hiçbir yerde saklanmıyor (yalnız HMAC) + SMTP ölü → token **yan
kanaldan** üretildi (aynı container, aynı pepper, aynı Redis). Uç, Redis ve DB
**gerçek**; taklit edilen tek şey e-posta teslimi.

### 🔴 AÇIK — ÖNCEDEN VAR OLAN: anonim ziyaretçi public rotada KALAMIYOR
Zamanlama ölçümü (temiz tarayıcı: çerez + localStorage + SW + cache silinmiş):
```
0ms    /eposta-dogrula  h1=null
250ms  /eposta-dogrula  h1="E-posta Dogrulama"  status="Dogrulaniyor..."
500ms  /login           <- FIRLATILDI
750ms  /login           h1="Tekrar hos geldin."
```
Hesap **doğrulanıyor** (DB kanıtlıyor) ama kullanıcı onay mesajını **hiç görmüyor**.
Kök neden sınıfı: global 401 yakalayıcıları **sert yönlendirme** yapıyor, public rota
muafiyeti yok — `utils/apiHelpers.ts:467` · `services/apiClient.ts:77` ·
`kiro/api/api-client.ts:147` · `services/learningStyleService.ts:31`. Tetikleyici:
anonim kullanıcıya `401` dönen `/api/v1/osb/settings/`.
**Kontrol kolu — benim/S247'nin işi DEĞİL:** dosyalar en son 7 Ağu / 10 Mar / 23 Nis'te
değişmiş; `git diff 750c38ef3~1..ac4c9dcef` bu dosyalarda **boş**. `/register` de aynı
şekilde fırlıyor → L2'ye özgü değil, **global**. Görev numarası atanmalı.

### Ölçüm aleti iki kez yanıldı (bulgu diye raporlanmadan yakalandı)
1. *"Rota bundle'da YOK (0 eşleşme)"* → **alet arızası**: JS `/js` altında, `/assets`'te
   yalnız 59 KaTeX fontu var. Kontrol kolu (`dashboard→12`, `exam→26`) ortaya çıkardı.
2. *"L2 sayfası fırlıyor"* → **L2'ye özgü değil**; `/register` de fırlıyor. Az kalsın
   fantom rapor ediliyordu. Ayırt edici ölçüm: **başka bir public rota da fırlıyor mu?**

### Fail Eden Testler
**YOK.** 43 passed / 0 failed (`test_eposta_dogrulama` 26 + zincir 8 + compose 9).

### Sonraki Adımlar (maks 5)
1. **SMTP kimlik bilgisi** (#441, operatör) → sonra `EPOSTA_DOGRULAMA_ZORUNLU=true`.
   Not: kapı hâlâ **varsayılan KAPALI**, `EPOSTA_DOGRULAMA_ZORUNLU` container'da `None`.
2. **Public-rota 401 muafiyeti** (yukarıdaki açık kalem) — 4 dosya, plan gate gerekir.
3. `X06` — 5+ ayrı rol-kontrolü implementasyonu (kütükte `dogrulandi`).
4. `user_item_fsrs` tablosunu geri getir → 2 şema bekçisi yeşile döner.
5. `U25` migration geri-alınabilirliği · `X11` imaj/host farkı.

### Kararlar (gelecek oturum tekrar tartışmasın)
- **Varsayılan port bir DAĞITIM gerçeğidir, kod sabiti değil.** `:3001` kodda kalıyor
  (yerel dev doğru); dağıtım gerçeği compose'ta. Kodu değiştirmek yerel devi kırardı.
- **Bekçi sabit değer beklememeli.** `assert port == 3000` bugün geçer, frontend yarın
  taşınınca sessizce yeşil kalır — bugünkü kusurun aynısı. İki kaynağı karşılaştır.
- **httpOnly çerez `document.cookie`'de GÖRÜNMEZ.** "Çerez yok" diye ölçüp temiz durum
  sandım; gerçekte `refresh_token` + `logged_in` duruyordu. Temizlik `context.clearCookies()`
  ile yapılır ve **öncesi/sonrası listelenerek** doğrulanır.
- **Ortamda bırakılanlar:** 5 `@kiro2-e2e.dev` test öğrencisi (4'ü `is_verified=true`) —
  yeniden ölçüm için kasıtlı. Redis'te 1-2 doğrulama token'ı (24 sa TTL, kendiliğinden düşer).

---

## Session Handoff — 2026-08-22 (S247 · L2 E-POSTA DOĞRULAMA — A1'in 2. ayağı KAPANDI)
**Branch:** feature/self-evolution-optimization
**Aralık:** `750c38ef3 · 076ade47c · 25c6a2475 · aa037cef8` (4 commit)
**Uncommitted:** `backend/semantic_cache.pkl` (S244'ten devralındı, bu işe ait değil)

### Neden bu iş seçildi (ölçüm, beyan değil)
A1 altın yolunun 4 ayağı ölçüldü: L1 kayıt ✅ (21 kullanıcı) · **L2 ❌ YOK** ·
L3 sınav ✅ (23 oturum / 15 tamamlanmış) · L4 net ✅ (15/15 `raw_score` dolu).
Tek eksik ayak L2'ydi ve altyapısı hazırdı (`core/email_util.py`, #466).

### Kök neden
`users.is_verified` **21/21 false**; kolonu YÜKSELTEN uç yok (canlı openapi 1119 yol),
OKUYAN giriş kontrolü yok (grep `backend/**`), `commands/auth.py:94` sabit `FALSE`
yazıyordu. Alan beyan edilmiş, hiçbir yere bağlanmamıştı.

### Yapılanlar
- `backend/core/eposta_dogrulama.py` **(YENİ)** — politika (flag + muafiyet + tek karar
  noktası) + HMAC'li tek-kullanımlık token deposu + `store_al()` **tekil** + tek e-posta
  gövdesi. Mutasyon **5/5**, M2 iki test öldürdü (assert'ler bağımsız).
- `api/auth.py` + `commands/auth.py` — 2 uç, kayıt tetikleyicisi, giriş kapısı
  (`is_active`'in kardeşi), `EpostaDogrulanmamis` → **403** (401 değil: kimlik doğru).
- `tests/integration/test_eposta_dogrulama_zinciri.py` **(YENİ, 8 test)** — HTTP zinciri.
  Mutasyon: M1 kapı silindi→**2** · M2 yalnız `/login/secure`→**1** · M3 verify UPDATE
  silindi (uç yine 200)→**1**.
- `frontend/` — `/eposta-dogrula` rotası + `EpostaDogrulaPage` + 2 servis metodu.

### Fail Eden Testler
**YOK.** 26 birim + 8 zincir + 55 regresyon (auth/rate-limit) → **0 failed**.
29 skip: `test_auth_api_comprehensive.py`'nin tamamı, canlı backend ister, önceden var olan.

### Engelleyiciler
- 🔴 **SMTP hâlâ yapılandırılmamış (#441, operatör).** Kapı bu yüzden **varsayılan KAPALI**
  (`EPOSTA_DOGRULAMA_ZORUNLU`). Açık + SMTP ölü = yeni kayıtlar giriş yapamaz.
- 🔴 **Canlıda DEĞİL** — backend+frontend yeniden kurulmadı (#511 dersi).
- ⚠️ Kapı borcu `#509` +1: `SKIP=ruff,mypy` — üç kollu ölçüldü, **ruff 8→8 / mypy 4→4**,
  bulguların hiçbiri benim satırlarımda değil (satır no kayması dışında birebir aynı).

### Sonraki Adimlar (maks 5)
1. **SMTP kimlik bilgisi** (#441, operatör) → sonra `EPOSTA_DOGRULAMA_ZORUNLU=true`.
2. Backend + frontend **rebuild** → L2'yi canlıya al, tarayıcıda doğrula.
3. `X06` — 5+ ayrı rol-kontrolü implementasyonu (kütükte `dogrulandi`).
4. `user_item_fsrs` tablosunu geri getir → 2 şema bekçisi yeşile döner.
5. `U25` migration geri-alınabilirliği · `X11` imaj/host farkı.

### Kararlar (gelecek session tekrar tartismasin)
- **Kapı flag'li + varsayılan KAPALI, muafiyet TARİH bazlı** (kullanıcı onayı). Muafiyet
  sınırı `2026-08-22 00:00 UTC` — ölçümle seçildi: 21 hesabın **hepsinden sonra**
  (max `08-21 20:40`), `now()`'dan **önce** (`04:18`). Gelecekteki sınır kapıyı süse çevirirdi.
  DB'ye tek satır yazılmadı → geri alınabilir.
- **Depo TEKİL, çekirdek modülde.** Token'ı ÜRETEN (komut katmanı) ile ÇÖZEN (API katmanı)
  ayrı katmanlarda; her biri kendi örneğini yaratsaydı Redis'siz kurulumda doğrulama
  **her zaman sessizce** başarısız olurdu — `api/auth.py:1297`'deki kusurun aynısı.
- **Negatif test istegin İŞLEYİCİYE ULAŞTIĞINI da ölçmeli.** İlk koşumda iki "engellenmedi"
  testi 422 (geçersiz `.test` TLD) yüzünden **boşuna geçti**. `_istek_isleyiciye_ulasti()`
  premis assert'i eklendi. Yanlış-SIFIR kuralının negatif-test hâli.
- **Biçimlendirici tuzağı 2. kez ısırdı:** import'u kullanımdan ÖNCE yazdım, ruff sildi,
  `F821` üretti. Import smoke GÖRMEDİ (dal çalışma anında), ruff gördü. **Kullanımı önce yaz.**
- `git stash pop` index'e değil **çalışma ağacına** koyar → `git add` tekrar gerekir
  (commit "no changes added" ile sessizce iptal oldu).

---

## Session Handoff — 2026-08-22 06:43
**Branch:** feature/self-evolution-optimization (master'dan 629 commit önde)
**Son commit:** `f20f5bfc5` docs(devir): S246 — eksik alet yazıldı + 3 kusur kapatıldı (kuyruk 7 → 4)
**Uncommitted:** `backend/semantic_cache.pkl` (Bin 4892→4892, S244'ten **devralındı**, bu işe ait değil — bilinçli commit'lenmedi)

### Yapilanlar
- `.claude/agents/kusur-kapatici.md` — **eksik alet yazıldı** (`0e3314f02`, kayıt kısıtı notu `3da8e5159`). Boşluk ölçüldü: `tdd-loop`/`debug-bug` 5 adımı kapsıyor, deponun dayattığı 7 kontrolün (mutasyon · kontrol kolu · üç kollu SKIP · hash-değişimi · kütük · biçimlendirici · `/tmp`) **hiçbiri** yok; 7'si de bu oturumda ısırdı. Sözleşme 9 adım, ajan **commit etmez**.
- `backend/tests/db/test_question_bank_invariants.py` — **X10 P0 kapandı** (`2e7c11d53`, +171/−2). İki kolu varmış; `27c8fff02` yalnız birincisini kapatmış. İkincisi: sessiz skip **sessiz VEKİL ÖLÇÜMLE** değiştirilmiş (`tests/e2e/pg_dsn.py:48-70` hiç soket açmaz). sıkı+DB-ölü `EXIT=0` → **`EXIT=1`**. Mutasyon 6/6.
- `.claude/settings.json` — **X05 kapandı** (`1c9299f96`, +1/−56). `excludePatterns` + `contextManagement` ölü ölçüldü (binary'de 0, kontrol kolu 17/24/1). Mutasyon 5/5, ikisi "aşırıya kaçma" civisi.
- `backend/tests/unit/test_claude_settings_anahtar_kumesi.py` — X05 kalıcı bekçisi (`d220255c1`, 3 test, mutasyon 3/3).
- `docs/audits/2026-08-12_25uzman/iddialar.yaml` — kütük (`42af7ed3f`): X10/X05 → `uygulandi`, X02 → `abartili`. **`dogrulandi` 7 → 4** · `uygulandi` 6 → **8**.
- `backend/app/services/fsrs_engine.py` + `backend/tests/unit/test_fsrs_yks_cap.py` — U02 (`3ccff58a1`, önceki tur): `yks_gun_kalan()` + `max_interval_days`; çağrı yerleri değişmeden kapandı.

### Fail Eden Testler
- **YOK.** `tests/audit/` + `test_claude_settings_anahtar_kumesi.py` + `test_question_bank_invariants.py` + `test_fsrs_yks_cap.py` → **26 passed / 3 skipped / 0 failed**.
- (3 skipped = varsayılan gevşek modda DB'ye bağlı invaryantlar — X10 fix'i bunu **bilinçli** korudu; `KIRO2_STRICT_DB_INVARIANTS=1` ile 4 assert koşuyor.)

### Engelleyiciler
- 🔴 `user_item_fsrs` tablosu **canlı DB'de YOK** (`to_regclass` → NULL). `#461`'de restore edilmişti, yine düşmüş. `tests/integration/test_fsrs_schema_contract.py` 2 kırmızı — kontrol koluyla **önceden var olduğu** ölçüldü, bu turun regresyonu değil.
- 🔴 **11 CI workflow'unun 0'ı** bu dalda tetikleniyor (`on: [main,master,develop]`, dal 629 commit önde) → görev `#468`.
- ⚠️ Kapı borcu `#509` büyüdü: `fsrs_engine.py`'de 4 `no-any-return` + 7 `PLC240x`; **üç kollu ölçüldü, hepsi HEAD'de birebir var**, benim satırlarımla örtüşme yok.

### Sonraki Adimlar (maks 5)
1. `X06` — 5+ ayrı rol-kontrolü implementasyonu (`require_role` ×3, `require_admin` ×2). Kütükte `dogrulandi`; **yeni `kusur-kapatici` ajanı artık kayıtlı**, doğrudan `agentType` ile çağrılabilir.
2. `U25` — migration geri-alınabilirliği otomatik test edilmiyor (`dogrulandi`).
3. `user_item_fsrs` tablosunu geri getir → 2 şema bekçisi yeşile döner.
4. `X11` — `offline_sync_api.py` host ağacında var, **dağıtılan imajda yok** (`dogrulandi`, rebuild gerektirir).
5. X10'un **fail-open `STRICT` bayrağı** (`"true"` → sessizce gevşek) ve **M6 ölçülmemiş dalı** — ikisi de bilinçli açık bırakıldı, +0 değer kuralı.

### Kararlar (gelecek session tekrar tartismasin)
- **Bir planın kendisi de bayatlar.** 6 Ağu'da yazdığım FAZ 0 (`TRUNCATE question_bank` + `pg_restore`) 22 Ağu'da **yıkıcı** olurdu: FAZ 0'ın 5 kalemi kapalıydı ve dump **eski tek-tablo şeması**. Komuttan önce planın yazıldığı günün varsayımlarını ölç.
- **Mutasyon adımı pazarlık dışı.** Yazdığım X05 bekçisi `parents[2]` yüzünden ölü doğdu (`3 skipped`, üç mutasyon da "hayatta kaldı" çünkü test hiç koşmadı) — X10'un birebir aynı sınıfı. Mutasyon olmasaydı **ölü bekçi commit'lenecekti**.
- **Ankraj tekilliği ölçülür.** `replace(...,1)` docstring'i vurabilir → sahte "hayatta kaldı". `count==1` doğrula.
- **Commit'siz iş `git stash push -- <dosya>` ile mutasyona sokulur, `git checkout HEAD --` ile ASLA.** X05 çürütücüsü bunu ihlal edip uncommitted fix'i sildi; sha256 ile geri kuruldu, kayıp yok.
- **Yeni ajan aynı oturumda kayıt olmaz** (ölçüldü: 3/3 `not found`). Sözleşmeyi prompt'a göm. *Bu oturumda teyit edildi: `kusur-kapatici` artık kayıtlı.*
- Ajan **commit etmez** — paralel kapatma turunda git index çakışmasını önler, her commit tek tek doğrulanabilir.

---

## Session Handoff — 2026-08-22 (S245 · İddia kütüğü: beklemede 15 → 0)

**Branch:** feature/self-evolution-optimization · **Commit:** `1a39a71e4` (2 dosya, +221/−52)
**Kapı:** `tests/audit` **13 passed / 0 failed** (önce 9 passed / 1 failed) · ruff + format temiz
**Ağaç:** yalnız `backend/semantic_cache.pkl` kirli (S244'ten devralındı, bu işe ait değil)

### 🛑 İlk iş: bayat bir planı ÇALIŞTIRMAYI REDDETTİM
Kullanıcı 6 Ağu'da yazdığım "FAZ 0" komutlarını (`TRUNCATE question_bank` +
`pg_restore`) uygulamamı istedi. Ölçtüm: **plan 16 gün / ~20 oturum bayat.**
FAZ 0'ın 5 kaleminin **5'i de kapalı** (#472-#476); celery log'da parola
**0 isabet**; iki "regresyon" **yok** (`git diff` boş). Ve komut bugün
**zarar verirdi**: (a) `TRUNCATE` S232-S240'ta `kiro2_temp`'ten taşınan
küratörlü 3.922 satırı siler, (b) 27 Tem dump'ı **eski tek-tablo şeması** —
`question_bank.question_text` artık YOK (4 tabloya bölündü).

### Yapılan — 25-uzman kütüğünün ölçülmemiş kuyruğu boşaltıldı
`docs/audits/2026-08-12_25uzman/iddialar.yaml`: **beklemede 15 → 0.**
Kütük ilk kez tamamen ölçülü: fantom 6→14 · doğrulandi 6→8 · abartili 4→9.

Yöntem: iddia başına **iki bağımsız çürütücü** (`iddia-dogrulayici`, farklı
mercek: A=zaten-kapalı/yanlış-ad, B=başka-katman/semantik-yanlış) +
anlaşmazlıkta **`kanit-hakemi`**. 12 ajan / 498 araç çağrısı / salt-okunur.
13/15 mutabık; U09 ve X05 hakeme gitti.

**15 iddianın 8'i FANTOM (%53).** Örnekler: U10 `position:fixed` saf
layout/compositing — JS re-render tetiklemez · U12 iddia edilen "36px"
dosyada hiç yok, global CSS zaten 44px merkezi token · U11 #415 zaten
kapatmış · U06 ankraj dosyası git'e hiç commit'lenmemiş + import zinciri
kırık · U16 XP-kaybı mekanizması hiçbir katmanda yok · U23 Bloom 6-seviye
filtresi hem FE Select'inde hem BE Pydantic'te (`ge=1,le=6`) VAR.

### ✅ U02 KAPANDI — `3ccff58a1` + kütük `ed61bfb12`
`yks_gun_kalan()` eklendi (bu yılınki geçtiyse **veya bugünse** gelecek yılınki →
dönüş **her zaman ≥1**; sınav günü 0 dönmek cap'i o gün etkisiz kılardı).
`fsrs_update(..., max_interval_days=None)`; None → `yks_gun_kalan()` →
**çağrı yerleri değişmeden** canlı kusur kapandı (`fsrs_service.py` diff'i **boş**).
Cap tek noktada (scheduled_days + due_date yazımından hemen önce) → 4 dal tek satırla.
Dal yerine **ternary**: `fsrs_update` zaten PLR0912 sınırındaydı (HEAD 16>12);
ölçüldü, benim hâlim de **16** — mevcut ihlal kötüleşmedi.

**TDD:** RED (ImportError) → GREEN 6/6. **Mutasyon 4/4 öldü, her biri FARKLI
sayıda test öldürdü** (assert'ler bağımsız): M1 cap silindi→2 · M2 varsayılan cap
kaldırıldı→1 (canlı fix yolu) · M3 `interval=1`→1 (kontrol kolu) · M4 `<=`→`<`→1.

**Regresyon kontrol kolu (`git stash`):** `test_fsrs_card_persistence` ÖNCE 2F+2E /
SONRA 2F+2E · `test_fsrs_schema_contract` ÖNCE 2F / SONRA 2F → **benim değil.**
Kök neden: `to_regclass('public.user_item_fsrs')` → **NULL, tablo canlıda YOK.**
🔴 Bu AYRI ve AÇIK bir kusur — `#461`'de restore edilmişti, yine düşmüş.

**Kapı borcu (SKIP=ruff,mypy — üç kollu ölçüldü):** şikayet edilen 4 satır
(178/222/235/249) HEAD'de birebir var (158/202/215/229); benim eklediklerim
32/67-86/255-260/360-370 → **örtüşme yok**. Yaygınlık: 4 `no-any-return` +
7 `PLC240x` (Türkçe sabit adları, 10 dosya). Aynı sınıf `#509`'da kayıtlı.

### 🔴 (kapanmadan önceki kayıt) U02 — doğrulandı, P2
FSRS aralığı **YKS tarihine göre cap'lenmiyor**. `app/services/fsrs_engine.py:64`
`MAX_INTERVAL_DAYS=36_500` tek cap; `grep 'yks_tarih|sinav_tarih|exam_date'`
fsrs_engine/fsrs_service → **0 sonuç**. İki çürütücü de canlı motoru koşturdu:
5 ardışık PUAN_İYİ → **194 gün**; rep4 → **6055 gün (due 2043-03-21)**.
İddia edilenden **geniş**: tetikleyici "Çok Kolay" değil (o buton yok,
`response_ms` hiç gönderilmiyor → her zaman PUAN_İYİ=3); **herhangi 2-3
ardışık doğru cevap** yetiyor. → Sıradaki iş: `min(interval, gun_kalan_yks)`.

### Bekçi kör noktası — bulundu ve TDD ile kapatıldı
`test_ankraj_dosyalari_var` *"dosya yoksa FANTOM'dur"* diyerek X07'yi kırmızı
yapıyordu. Oysa X07 `durum=uygulandi` ve fix'in **kendisi silmeydi**
(`a978ae86a`). Ölçüm aleti, ölçtüğü doğru kapanışı cezalandırıyordu.
**Kontrol kolu:** eski kütük 1F/9P, yeni kütük 1F/9P → bu turun regresyonu değil.
Fix: `_kayip_ankrajlar()` saf fonksiyonu, `durum=="uygulandi"` MUAF.
**Mutasyon 2/2 öldü** (M6 muafiyeti kaldır · M7 toptan-atlamaya çevir);
geri alım sha256 ile doğrulandı.

### Kalıcı ders
**Bir planın kendisi de bayatlar.** 16 gün önce doğru olan `TRUNCATE`,
bugün yıkıcıydı. Komutu çalıştırmadan önce planın yazıldığı günün
varsayımlarını ölç — özellikle şema, tarih ve "kapandı" listesi.

---

## Session Handoff — 2026-08-21/22 (S244 · B3 FAZ 3 + 3 devralınan P0 — KAPANIŞ)
**Branch:** feature/self-evolution-optimization
**Aralık:** `ee5ef3c03..34f957482` — **18 commit**, hepsi push'lu, ağaç temiz
**Tasarım:** `docs/superpowers/specs/2026-08-21-b3-faz3-design.md`
**Plan:** `docs/superpowers/plans/2026-08-21-b3-faz3-uygulama.md`
**Denetim:** `docs/audits/2026-08-21_b3_konu_kirilimi.md` §FAZ 3 + EK 1-4 (**828 → 1413 satır**)

### 📌 KAPANIŞ TABLOSU — 6 kalem kapandı, 3'ü "kusur değildi" çıktı

| # | Kapanış türü | Kanıt |
|---|---|---|
| **#511** | düzeltildi | `git == imaj`, 5/5 dosyada md5 eşit (önce imajda `topic_code` 0/0) |
| **#512** | düzeltildi | kök neden **modelde**; 3 sessiz kusur + 1 kardeş kusur |
| **#510** | çivilendi | M6 mutasyonda **tek başına** ölüyor |
| **#513** | **ÖLÇÜLDÜ → tekrarlanmıyor** | kod değişikliği YOK; ankraj/proza çelişiyordu |
| **#514** | **yeniden çerçevelendi** + düzeltildi | motor doğruydu; kusur ders listesindeydi |
| **#516** | **ölü çıktı** → silindi | git geçmişi: doğuştan spekülatif; invaryant çivilendi |
| **#515** | silme **önce durdu** → sonra silindi | bekçi denkliği 4 açık invaryant buldu |

**Kapı:** 1278-1292 passed / 0 failed (tur boyunca). Backend **2×**, frontend **2×**
yeniden kuruldu; her fix **deploy edildi ve tarayıcıda/SQL'le doğrulandı**.

### 🔴 Bu turda ÇÜRÜTÜLEN 5 iddia — beşi de benim

1. *"(c) dalı B3 öncesi de ölüydü"* → `.lower()` üretiyordu, dal **canlıydı**
2. *Planın kovalama-değişmezlik verisi* → **dejenereydi**, test hatalı koda karşı da geçerdi
3. *"`normalize_tr` başka yerde kullanılıyor"* → üç kullanımın üçü de değişen bloklardaydı
4. *"#516 ikinci **CANLI** yol"* → dal **ölüydü**; import zinciri bileşeni kanıtlar, dalı değil
5. *"push kapısı uyarıda blokluyor"* → 3 gerçek kritik vardı, üçü de devralınmış

Ayrıca **iki alet arızası** bulgu diye raporlanmadan yakalandı: snapshot `depth`
kesmesi ("boş tablo") ve yanlış asset yolu ("imajda kod yok"). İkisi de **kontrol
koluyla** ayıklandı.

### ⚠️ Ortamda bırakılanlar
- DB: **4** `@kiro2-e2e.dev` test öğrencisi + **23** sınav oturumu (kasıtlı, yeniden ölçüm için)
- `backend/semantic_cache.pkl` takipli-kirli — **devralındı**, bu işe ait değil, commit'lenmedi

### Kapanan (üçü de S243'ün bıraktığı P0)
| # | Kabul kanıtı |
|---|---|
| **#511** | `git == imaj` — **5/5 dosyada md5 eşit**. Önce: imajda `topic_code` 0/0, git'te 1/5 |
| **#512** | 3 sessiz kusur + 1 kardeş kusur; kök neden **modelde** çözüldü (`ders`+`konu_kodu`) |
| **#510** | M6 **öldü** — mutasyonda T7 tek başına FAIL |

### Kök neden ve fix
`KonuPerformansi` yalnız `konu: str` taşıyordu; ders kimliği için alan yoktu.
İki varsayılanlı alan eklendi (sona), üretici doldurdu, üç tüketici dize
eşleşmesi yerine **alan** okuyor:

- **(a) IRT** → `_get_irt_aggregate(topic_code=…, ders=…)`; `topic_hierarchy.code`
  ile anahtarlanır, cache anahtarı ayrışır. Ölçüldü: `"Kimya"` (level-1 KONU,
  263 soru) ders yolundan **3531** dönüyordu; `"Kimyasal Denge"` **0** (gerçek 1262).
- **(b) ZPD** → `_agirlikli_ortalama`; **kovalama-değişmez**. Bugünkü +9,91
  sapmayı kaldırmakla kalmaz, sonraki kardinalite değişiminde de kaymaz.
- **(c) ders dalı** → `_ders_uyum_skoru` + `subject_key(ders)`. Kardeş kusur:
  Türkçe harfli dize kanon `{KIMYA, MATEMATIK}` ile hiç eşleşemezdi → `turkce`.

### Fail eden testler
**YOK.** Kapı: **1292 passed / 1 skipped / 0 failed**.
Yeni: `tests/unit/test_konu_kimligi.py` (15) · `tests/fast/test_irt_aggregate_topic_split.py` (6) ·
`tests/integration/test_osym_exam_konu_tuketiciler.py` T6+T7 (gerçek Postgres, mock YOK).

### Canlı E2E (yeni imaj)
```
kayit 201 · giris 200 · beta-practice 200 · start 200 · complete 200
  8 kova · topic_code dolu 8/8 · benzersiz 8
subject-performance 200 · 8 satir · 8 farkli topic_code
zpd 200 · irt-analysis 200 · learning-style 200 · osym-ets 200   -> 5XX YOK
```

### 🔴 DÜRÜST SINIRLAR (iddia EDİLMEYENLER — denetimde 7 madde)
1. **(a) IRT kusuru CANLIDA DEĞİLDİ.** Ölçüldü: `config/mock_endpoint_flags.json`
   5/5 `advanced_reports.*` = `false`; iki çağrı yeri de `_real` yolda = **uykuda**.
   Gerçek kusur (bayrak çevrilince sessizce aktifleşir) ama *"bugün öğrenciyi
   bozuyor"* aşırı iddia olurdu. Kanıt uçtan değil **doğrudan SQL**'den alındı.
2. **`TURKCE` dalı E2E ile doğrulanamadı** — canlı DB'de `TURKCE` satırı yok.
3. **Bayat-mock assert'i mutasyonla kanıtlanmadı** — sqlite hatası önce patlıyor.
4. **+9,91 bu turda yeniden ölçülmedi** (S243'ten devralındı).

### Çürütülen 3 iddia — üçü de PLANI YAZANIN
1. *"(c) dalı B3 öncesi de ölüydü"* → `osym_exam_engine.py:1387` `.lower()`
   üretiyor; dal **canlıydı**, B3 öldürdü.
2. **Planın kovalama-değişmezlik test verisi DEJENEREYDİ** — ağırlıksız
   ortalamalar 6.0 vs 6.0, yani test **hatalı implementasyona karşı da geçerdi**.
   İmplementer aritmetiği kontrol edip yakaladı, hakem doğruladı.
3. *"`normalize_tr` başka yerde kullanılıyor"* → üç kullanımın üçü de
   değiştirilen bloklardaydı.

### 3 dişsiz assert bulundu ve değiştirildi
T6'nın kapsanan assert'i · `test_konu_adi_ders_dalini_secmez` (inceleyici çağrı
yeri mutasyonuyla kanıtladı: **7 passed**) · bayat mock ankrajı. Nihai inceleme
**dördüncüyü aradı, bulamadı**.

### Orkestrasyon dersi (bu tur ısırdı)
Depoda **tek git index** var — `git add .` yapmamak yeterli koruma değil,
**commit'in kendisi pathspec ister**. Ayrıca dosya-değiştiren inceleyici, aynı
dosyadaki implementer ile paralel koşturulmamalı (olası veri kaybı penceresi
oluştu; bütünlük sonradan ölçüldü, kayıp yoktu — ama şans).

### 🟢 EK — #513 ÖLÇÜLDÜ: TEKRARLANMIYOR (aynı oturum, kapanış turu)

Devir notunun **ankrajı prozasıyla çelişiyordu**: `App.tsx:348` =
`/exam/:sinavId/results`, ama proza `/exams` diyor — farklı rotalar.
`App.tsx` S243'ten beri hiç değişmedi.

**Sarmal kök neden olamaz** (S243'ün `/register` kontrol kolundan daha güçlü
kanıt): `/dashboard` (sağlıklı) ile `/exams` (bozuk denilen) **birebir aynı
bileşimi** kullanıyor — aynı `PageTransition`, aynı `ProtectedRoute`, aynı
`['ogrenci']`, ikisi de `lazy()`.

Canlı Playwright ölçümü (kimlik doğrulanmış `ogrenci`, yeni backend imajı):
```
/exams              SERT YUKLEME -> tam render, 0 konsol hatasi
/exam/{sid}/results SERT YUKLEME -> tam render, 0 konsol hatasi
konu kirilimi tablosu -> 9 satir (Ders | Konu)
backend subject-performance -> 200, 9 satir
EKRAN == BACKEND: 9 == 9
```

🔴 **Kendi ölçüm aletim yanıldı, dürüst kayıt:** ara adımda "tablo BOŞ" bulgusu
üretildi — snapshot `depth: 7` ile alındığı için tablonun çocukları kesilmişti.
Hedefli ikinci ölçüm 9 satırı gösterdi. Ayırt edici sinyal: `<TableHead>`
**statik** hücreler taşıyor, onların boş çıkması veri kusuruyla açıklanamaz.
Fantom raporlanmadan yakalandı.

**DÜRÜST SINIR:** *"tekrarlanmıyor" ≠ "hiç yoktu"*. Backend imajı bugün **iki
kez** yeniden kuruldu (#511); S243 bayat 18 Ağu imajıyla gözlem yapıyordu. En
olası açıklama gözlemin o bayat imajdan kaynaklandığı ve #511 ile yan etki
olarak düzeldiği — **ama kanıtlanmadı** (eski imaj geri kurulup karşı-olgusal
test yapılmadı). Kapanış türü: **ÖLÇÜLDÜ → TEKRARLANMIYOR**, kod değişikliği YOK.
Ayrıntı: `docs/audits/2026-08-21_b3_konu_kirilimi.md` §EK.

### 🟢 EK 2 — #514 ÖLÇÜLDÜ + DÜZELTİLDİ (aynı oturum)

**#514 bir kusur DEĞİLDİ.** `"Mevcut: 33"` aritmetiği birebir tuttu:
TYT dağılımı MATEMATIK 26 + KIMYA 7 = **33**; diğer 5 ders kapıda **sıfır**.
`_select_questions` kusursuz — kısa sınavı sessizce servis etmiyor, sayıyı
söyleyerek reddediyor.

**A1 engellenmiyordu:** A1 "40 soruluk TYT *Matematik*" istiyor, tam TYT değil.
Ölçüldü: `create(MATEMATIK,40)` → **200**. Üstelik `ModernExamStartPage`
varsayılanı zaten `TYT/Matematik/orta/40` — altın yol kutudan çıktığı gibi.

**ASIL kusur ders listesindeydi:** sabit kodlu 8 seçenek, havuz 2 karşılıyor →
üretimin birebir yüküyle ölçüldü, **8'de 6 ham 400**. Düzeltildi (`cf196bdb6`):
`GET /api/v1/osym/subjects` (zaten vardı, yeni uç YOK) ile müsait olmayanlar
**görünür ama devre dışı + "İçerik hazırlanıyor"**.

Üç bağlayıcı kısıt: (1) `question_count` **ekrana yazılmadı** — o alan
`question_bank` toplamı (3.531), motor kapıdan servis ediyor (3.209);
(2) **Türkçe locale tuzağı** — `'Türkçe'.toUpperCase()`=`'TÜRKÇE'` ≠ `'TURKCE'`,
açık eşleme tablosu + **mutasyonla çivili** (`.toUpperCase()` ile tek assert ölüyor);
(3) **FAIL-OPEN** — uç düşerse hiçbir ders kapanmaz, altın yol korunur (2 test).

Frontend imajı yeniden kuruldu, **tarayıcıda doğrulandı**: 2 açık (Matematik,
Kimya) / 6 gerekçeli kapalı / 0 konsol hatası.

🔴 **İKİNCİ YOL kapsanmadı (#516):** `ModernExamStart.tsx:215-221` `create`'i
`subject` alanı OLMADAN çağırıyor → tam TYT (120) → aynı 400. Zincir
`App.tsx:89 → ExamPage.tsx:18,195`. Farklı kusur sınıfı, ayrı karar gerekiyor.

### 🟢 EK 3 — #516 ÖLÇÜLDÜ: DAL ÖLÜYDÜ, SİLİNDİ (aynı oturum)

🔴 **Kendi iddiamı çürüttüm.** #514 turunda "ikinci **CANLI** yol" demiştim —
yanlıştı. Import zinciri **bileşenin** ulaşılabilirliğini kanıtlar, **içindeki
dalın** değil. Yanıltıcı sinyal `useParams<{ sinavId?: string }>()` idi:
tipin `?` olması çalışma zamanında opsiyonel demek değil — **tip imzası niyet
beyanı, rota tablosu gerçek kısıt.**

Çürütme 5 yönden denendi, 5'i de yol bulamadı. Kesin olan **git geçmişi**:
fallback `7d7025b71` (8 Mar) ile eklendiğinde rota tablosu **zaten aynıydı** —
kaldırılmış bir rotanın kalıntısı değil, **doğuştan spekülatif**.
(Tarayıcıda `/exam/` denemesi araç zaman aşımına uğradı → **sonuçsuz**,
kanıt sayılmadı.)

Silindi (`508a6bd4b`): `subject`siz `createExam` → açık hata. RED kanıtı
silinen dalın ta kendisini yakaladı: `createExam` çağrısı `exam_type:"TYT"`
ve **`subject` YOK** — canlı 400'ü üreten çağrının aynısı.

**Mutasyon 3/3 öldü**, biri yanlış-sıfır bekçisi (`<ExamPage/>` yeniden
adlandırılırsa test boş kümede geçmek yerine düşer). Testin taşıdığı iddia:
*biri `ExamPage`'i segmentsiz rotaya bağlarsa silinen dalın YOKLUĞU gerçek
kusura döner* — M1/M2 tam o anda düşer.

Doğrulama: yeni test 4 passed · kardeş paket 8 passed · `tsc` EXIT 0 ·
eslint **kontrol koluyla HEAD ile aynı**, +0. (`ExamInterface.test.tsx`'teki
4 fail HEAD'de de var, o dosyada `ModernExamStart` geçmiyor — ilgisiz.)

### 🟢 EK 4 — #515 KAPANDI: silme, bekçi boşluğu bulduğu için ÖNCE DURDU

Ölü ikizi silmeden önce tek soru soruldu: **ardılın bekçisi öncekinin
çivilediğini gerçekten çiviliyor mu?** Prozayla değil **mutasyonla** ölçüldü —
cevap **hayır**: 10 invaryantın **4'ü açıktı**.

🔴 **M-C asıl bulgu:** ders-fallback dalından `QuestionMetadata` JOIN'i silinince
**sessiz kartezyen** oluşuyor (2 FROM → her soru × her metadata satırı) →
şişmiş `sample_size`, yanlış IRT ortalaması, **çökme yok**. Eski yeni-bekçi bunu
**hayatta bıraktı** çünkü `subject_area='MATEMATIK'` iddiası bir **WHERE dizesi**
ve JOIN gitse bile derlenmiş SQL'de duruyor; tek-FROM kontrolü de yalnız **konu
dalını** koşuyordu.

**Bu kural `audit-methodology.md`'de ZATEN yazılı** ("WHERE iddiasını yalnız
`stmt.whereclause`'da ara — filtre silinse bile dize tam SQL'de durur").
Kural vardı, kör nokta yine ısırdı — ama bu sefer **silmeden önce** yakalandı.

3 test eklendi (bekçi **5 → 9 invaryant**), M-C/D/E her biri **tek** testle
öldü, sonra silindi: fonksiyon 82 satır + eski bekçi dosyası 211 satır.
`advanced_reports.py` **1809 → 1730 (−79)**. Defter kontrolü: hiçbir
`zorlayici:` silinen dosyayı işaret etmiyordu.

Doğrulama: **1278 passed / 0 failed** · ruff temiz · pre-commit **19/19, SKIP YOK**.

**Ders:** ölü kod silmeden önce sorulacak soru *"bu kod kullanılıyor mu"* değil,
***"bu kodu koruyan bekçi neyi çiviliyor ve ardıl onu çiviliyor mu"***.

### Sonraki Adımlar (maks 5)
1. **L2 e-posta doğrulama** — hâlâ YOK, blokaj SMTP (#441) — `Gerekli: 120, Mevcut: 33`; havuz kapasitesi
2. **L2 e-posta doğrulama** — hâlâ YOK, blokaj SMTP (#441)
3. `_get_subject_irt_aggregate` ölü ikizi sil (#515; bekçisi ardıla taşınmalı)
4. `advanced_reports.py:561` `get_subject_morphology_factor` ölü (`hasattr` daima False)
5. #513'ü kesin kapatmak istersen: eski backend imajını geri kurup karşı-olgusal test

### Kararlar (gelecek oturum tekrar tartışmasın)
- **Ölçü kovalamadan bağımsız olmalı, düzeltilmiş olmalı değil.** Ağırlıklı
  ortalama seçildi çünkü bir sonraki kardinalite değişiminde de kaymaz.
- **`ders` küçük harf saklanır** (motorun ürettiği biçim); karşılaştırmada
  `subject_key()`, DB'de `subject_db()` — `normalize_tr` YASAK (Türkçe locale).
- **Eski `_get_subject_irt_aggregate` silinmedi** — split bekçisinin ankrajı.
  Tanım yerine `URETIMDE OLU` işareti kondu (nihai incelemenin Important'ı).
- **Defter 156 → 158**: `L-s244-kovalama-degismez-metrik` (zorlayıcı dolu) +
  `L-s244-paralel-ajanlar-tek-git-index`.
- **#509 borcuna +1**: `test_advanced_reports_schema_parity.py` 5× E402,
  kontrol koluyla önceden-var-olan ölçüldü, `SKIP=ruff` kullanıldı.

### Not
Bu dosya **5 devir notu** taşıyor (S244/S243/S242/S241/S239-S240) — "son 3"
kuralı önceki turda da aşılmıştı. En eskilerin arşive inmesi küçük bir açık iş.

---

## Session Handoff — 2026-08-21 (S243 · B3 FAZ 2 — regresyon kapandı, B3 KAPANMADI)
**Branch:** feature/self-evolution-optimization
**Denetim:** `docs/audits/2026-08-21_b3_konu_kirilimi.md` §FAZ 2 (394 → 829 satır)

### Ölçülen (canlı oturum `62d6b582…`, 40 soru / 13 kova / 2 ders)
S242'nin 3 çürütücüsünün bulduğu **beyan edilmiş** regresyonlar kapandı. ÖNCE değerleri
alıntı değil — aynı canlı veriden `konu=sp.subject` ile **karşı-olgusal** türetildi.
```
benzersiz konu etiketi : 2/13  -> 13/13
zayif ∩ guclu          : {kimya, matematik} -> []
benzersiz oneri (12)   : 4     -> 12   (gercek _generate_personalized_recommendations)
sinav_sayisi > 1       : {kimya:9, matematik:4} -> {}   (TEK sinav)
cok-sinavli kontrol    : 3 oturum, konu bazinda uyusmazlik YOK
subject-performance    : 13 satir / 13 benzersiz topic_code / sum=40  (bozulmadi)
```
**Mutasyon 6/7 öldü.** Faz 1'de HAYATTA kalan iki dal artık ölüyor:
`M2 sıralama` → T4 **tek başına** · `M4 "Konu atanmamis"` → T5 **tek başına, SKIP yok**
(eski bekçisi `konu_kirilimi.py:398` kalıcı ölüydü — sütun NOT NULL, sayaç hiç artamaz).
🔴 **M6 (`commands/sinav.py:844`) HAYATTA** — 2069 testte DELTA=0, **bekçisiz**.

### Kök neden (DERS, deftere eklendi: `L-s241-kardinalite-degisiminde-SAYAN-tuketici`)
> Kardinalite değiştiren değişikliğin en kırılgan tüketicisi listeyi **OKUYAN** değil,
> listeyi **SAYAN / etiketi ANAHTAR SANAN** koddur.
Faz 1'in taraması `application/` dizinini hiç taramadı + geçişli tüketiciyi izlemedi.
Testler yeşil kaldı çünkü 4/4 referans `AsyncMock(return_value=None)`.
Zorlayıcı: `tests/integration/test_osym_exam_konu_tuketiciler.py` (T1-T5, gerçek Postgres).

### 🔴 KAPANMADI — aynı kusur sınıfı bir katman yukarıda
| Bulgu | Ölçüm | Görev |
|---|---|---|
| `advanced_reports.py:474/1167` IRT | `sample_size 391→0`, ama adı `Kimya` olan level-1 konu **3531**'i yiyor (`MAT` latent, 0 soru) | #512 |
| `advanced_reports.py:761/869/873` | `len(konu_zpd_analizleri)` → ZPD ortalaması **+9,91 puan** sessiz kaydı | #512 |
| `advanced_reports.py:933/1051` | `"matematik" in normalize_tr(...)` → ders dalları **ölü** | #512 |
| `commands/sinav.py:844` | M6 bekçisiz — POST /complete sözleşme testi yok | #510 |
| `App.tsx:348` | sert yüklemede **boş sayfa** (`/exams` bozuk, `/dashboard` sağlıklı); rebuild'le ilk kez canlıda. Kök neden iddiası (`PageTransition:57`) kontrol koluyla **çürüdü** (`/register` sağlıklı) | #513 |
| **imaj** | fix git'te ✅ / imajda ❌ / container'da ✅ → `docker compose up -d` geri alır | **#511** |

### Kayıt
- Bu commit'le kapandı: fix **commit'siz**di (`git show HEAD:` → 0) ve T1-T5 **takipsiz**di.
- `sp.subject` fallback'i **ÖLÜ KOD**: `primary_topic_id`/`name_tr` ikisi de NOT NULL.
- 🔴 **S241'in "NET=1.0 = D−Y/4 TUTTU" ölçümü AYIRT EDİCİ DEĞİLDİ** — D=1,Y=0'da iki
  formül çakışır. Canlı: `D=22, Y=18 → net 22.0` (D−Y/4 = 17,5). Motor `net = doğru`.
- Kapı `SKIP=ruff,mypy` (#509) **önceden var olan borç** — kontrol kolu: HEAD'de aynı 4 bulgu.
- `backend/semantic_cache.pkl` bu işe ait değil, commit'e alınmadı.
  DB'de 3 test öğrencisi + 4 oturum kasıtlı bırakıldı.
- **Oturum sonu temizliği (ana bağlam, S243 kapanışı):** workflow ajanlarının bıraktığı
  9 takipsiz artık silindi (`b3-*.png` ×4, `backend/.b3_*` ×4, `.b3_read.py`). Kalan
  takipli-kirli: **yalnız** `backend/semantic_cache.pkl` (bu işe ait değil).
  Tarayıcı kanıtı depo kökünden `docs/audits/kanit/2026-08-21_b3-tablo-gorunur.png`
  altına alındı ve denetim dokümanının 677. satırındaki kırık referans düzeltildi
  (`3071b9fdc`) — dosya kökte **takipsiz** durduğu için referans hiçbir makinede çözülmüyordu.
- **Teslim kanıtı (A1 4. ayak):** ekran görüntüsünde `Ders | Konu` iki sütun, **14 satır /
  14 farklı konu** (Kimyasal Denge · Asitler ve Bazlar · Fonksiyonlar · Olasılık …).
  Bu kanıt **uygulama-içi gezinme** yolundan alındı; **sert yüklemede boş sayfa** (#513).
- **Karar (kullanıcı, oturum sonu):** açık 3 P0'ın hiçbiri bu turda alınmadı —
  "dur, devir notu yaz". Sıradaki oturum #511'den başlar.

### Sonraki Adımlar (maks 5)
1. **#511** `docker compose build backend` + `up -d --no-deps backend` + `Start-Sleep 90` + E2E
2. **#512** `KonuPerformansi`'ye ders alanı → B1+B2+B3 tek turda (model kararı, plan gate)
3. **#510** POST /complete sözleşme testi → M6'yı öldür
4. **#513** sert-yükleme boş sayfa: `ProtectedRoute`+`PageTransition` bileşimi, teşhis sıfırdan
5. **L2 e-posta doğrulama** hâlâ YOK — blokaj SMTP (#441)

---

## Session Handoff — 2026-08-21 (S242 · B3 KONU KIRILIMI — motor açıldı, tüketiciler bozuldu)
**Branch:** feature/self-evolution-optimization
**Denetim:** `docs/audits/2026-08-21_b3_konu_kirilimi.md`

### Ölçülen
- `GET /osym-exam/{sid}/subject-performance` **1 kova → 13/14 kova**, API == DB (küme eşit,
  sayı eşitliğiyle bırakılmadı). Σ`total_questions` 40 == 40. SQL `execute` **4 → 4**
  (S220 kazancı korundu). Kabul kriteri (≥5 `topic_code`) **GEÇTİ**.
- Backend canlıya deploy edildi (`/openapi.json` `SubjectPerformanceResponse` içinde
  `topic_code`+`topic_name` var). Testler: 628 passed / 31 skipped / 0 failed.

### 🔴 KAPANMADI — 3 çürütücü mercek "hiçbir regresyon" iddiasını 3/3 çürüttü
1. **P0** `core/osym_exam_engine.py:2168` `session_to_sinav_sonucu` → `konu=sp.subject`.
   13 satırın 13'ü `'matematik'`; `zayif_konular` ×11 + `guclu_konular` ×1 = **aynı ders
   hem zayıf hem güçlü**. Yayılım: `advanced_reports.py` 5 uç + `ogretmen_service.py`.
2. **P0** `services/ogretmen_service.py:210` — tek sınav `sinav_sayisi=13` sayılıyor (önce 1).
3. **P1** `application/commands/sinav.py:831` — mapping 8 alan kopyalıyor, `topic_code` yok.
   **Kök neden:** GREEN'in tüketici grep'i `application/` dizinini taramadı.
4. **P1** 4/4 test `session_to_sinav_sonucu`'yu `AsyncMock(return_value=None)` ile mockluyor
   → regresyon test yüzeyinde **görünmez** (58/58 yeşil kaldı).
5. **P2** Sıralama %0 kapsam: M2 mutasyonu (`sort` bloğu silindi) → **631 passed, 0 fail**.
6. **P2** "Konu atanmamış" dalı ölü (DB'de NULL konu 0/3922); M4 mutasyonu 0 fail.
7. **P2** Frontend imajı 31 Tem tarihli — bundle'da `topic` = **0**. Öğrenci hâlâ göremiyor.

### Sonraki Adımlar (maks 5)
1. P0-1/2 + P1-1 tüketici düzeltmesi (4 dosya → Root Cause + TDD turu, plan gate)
2. `session_to_sinav_sonucu` için gerçek-veri testi (mock körlüğü kapansın)
3. `docker compose build frontend` + `up -d --no-deps frontend`
4. Sıralama bekçisi + Türkçe collation tie-break (`Ç` sona düşüyor)
5. L2 e-posta doğrulama — hâlâ YOK, blokaj SMTP kimlik bilgisi (#441)

### Kayıt
- `api.generated.ts` **güncellenmedi** — gerekçe ölçüldü (0 importer, tsconfig exclude,
  `openapi-typescript` kurulu değil, `backend/openapi.json` bayat). Ayrı commit'e konu.
- pre-commit ruff(15) + mypy(3) **FANTOM** — kontrol kolu `git show HEAD:`/`stash` ile
  ölçüldü, ikisi de HEAD sürümünde de var, benim hunk'larımda değil.
- 3 ölçüm aleti arızası bulgu diye raporlanmadı: cp1254 mojibake (`encoding=` eksik),
  `MSYS_NO_PATHCONV`, boru hattında `$?` son halkayı ölçmesi.

---

## Session Handoff — 2026-08-21 01:00 (S241 · A1 ALTIN YOLU AÇILDI)
**Branch:** feature/self-evolution-optimization
**Son commit:** `3d28c00ba` fix(core): GUC kurulum hatasi artik SESSIZ GECMIYOR
**Uncommitted:** yalnız devralınan `backend/semantic_cache.pkl` (Bin 4892→4892, 0 satır)
**Push:** ✅ 0 bekleyen · 9 commit · E3: kullanıcı-görünür yola dokunan **2** ✅

### Yapılanlar
- `docs/superpowers/specs/2026-08-20-a1-altin-yol-e2e-design.md` tasarım (`fa1784215`)
- `docs/superpowers/plans/2026-08-20-a1-altin-yol-olcum.md` plan (`0973e5495`)
- `docs/audits/2026-08-20_a1_altin_yol_olcum.md` — 11 ajan, **45 bulgu → 44 ayakta / 1 düştü** (`3a4b4bae7`)
- `backend/core/cevap_kapisi.py` (YENİ) + `api/soru_bankasi.py:125` + `api/osym_questions_api.py:247,468`
  — **cevap anahtarı sızıntısı KAPATILDI** (`a664c2d5e`, `adcadb61d`)
- `backend/core/tenant_context.py` (YENİ) + `core/database.py:526` `after_begin` +
  `core/dependencies.py:183` — **RLS GUC her transaction'da** (`79a81ae05`)
- `backend/core/dependencies.py:466-476` — sessiz `except: pass` görünür + bayat yorum (`3d28c00ba`)
- `.claude/lessons/ders_kaydi.yaml` 155→156 · zorlayıcı liste 24→**25 dosya**

### Fail Eden Testler
**YOK.** Kapı: **264 passed / 1 xfailed / 0 failed**.
Yeni: `tests/unit/test_cevap_kapisi.py` 13 · `tests/unit/test_tenant_context.py` 8 ·
`tests/integration/test_rls_guc_transaction.py` 4 (canlı Postgres, `kiro2_app` rolü).

### Engelleyiciler
**YOK.** Devralınan: SMTP · ödeme sağlayıcısı · alan adı+SSL (operatör).

### A1'in dört ayağı (kanıtlı)
```
L1 Kayit      CALISIYOR   B5: username carpismasi 500 (commands/auth.py:100)
L2 Dogrulama  YOK         1119 yolda uc yok, is_verified'i TRUE yapan satir yok
L3 Sinav      CALISIYOR   create 200 / beta-practice 200
L4 Puanlama   CALISIYOR   NET=1.0 = D-Y/4 TUTTU   B3: kirilim hala DERS bazli
L5 Yuzey      uclar acildi, TARAYICIDA DOGRULANMADI
exam_sessions 0 -> 5   (platform tarihinde ILK sinav oturumlari)
```

### Sonraki Adımlar (maks 5)
1. **B3 konu kırılımı** — `core/osym_exam_engine.py:1364` `subject_area` → `topic_hierarchy.code`;
   `QuestionResponse.topic` ham UUID yerine konu kodu. A1'in 4. ayağı bunsuz karşılanmaz.
2. **L5 tarayıcıda doğrula** — `/exam/start` → `/exam/:id` → `/exam/:id/results` (Playwright)
3. **B4 e-posta doğrulama** — yol **yok**, inşa kararı bekliyor (SMTP ayrı iş)
4. **B5** `commands/auth.py:100` — çakışmada 409/422 + benzersiz username türet
5. Denetimin 13 boşluğu — özellikle offline sync paketi (tasarım gereği `correct_answer` taşıyor)

### Kararlar (gelecek session tekrar tartışmasın)
- **Cevap alanları cache'e TAM yazılır, ÇIKIŞTA temizlenir.** Cache anahtarı rol taşımıyor;
  role göre cache'lemek öğretmenin girdisini öğrenciye servis ederdi.
- **RLS GUC çağrı yerlerine değil boğaz noktasına.** 79 tablo, 22 çağrı yeri; biri atlanırsa
  sessiz 500. `is_local=true` ZORUNLU — `false` havuzdan kiracı sızdırırdı.
- **`bandit`/`mypy`/`ruff` SKIP'leri ÖLÇÜLDÜ**: `dependencies.py` ruff 8→7 (iyileşti), mypy 3→3;
  `database.py`+`dependencies.py` 10→10 fark 0. Önceden var olan borç, **ayrı açık iş**.
- **Y13 AÇIK VE BÜYÜYOR** — N802 11. kez, bu oturumda **2 kez** (6+7=bugün 13). Kanca edit
  anında göstermiyor, yalnız pre-commit yakalıyor.

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

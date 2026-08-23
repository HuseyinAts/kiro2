# S249 — Açık kalemlerin kapatılması (tasarım)

**Tarih:** 23 Ağustos 2026 · **Dal:** `feature/self-evolution-optimization`
**Öncül commit:** `06c0da274` (S248 devir notu)
**Yöntem:** `superpowers:brainstorming` → bu spec → `superpowers:writing-plans` → workflow

---

## 0. Bu spec neden var

S248 (23 Ağu) L2 e-posta doğrulamasını canlıya aldı ve yolda bir ölü-link kusuru
kapattı. Geriye altı açık kalem kaldı. Kalemleri **kütükten okuyup doğrudan işe
girmek yerine önce canlıda ölçtük** — ve ölçüm kapsamı maddi olarak değiştirdi:

| Kalem | Kütükteki durum | 23 Ağu canlı ölçümü |
|---|---|---|
| X11 | `dogrulandi` | **1. kolu bugün kapandı**, 2. kolu **yeni ulaşılabilir oldu** |
| U25 | `dogrulandi` | **Öncül bayat** — ankraj dosyası yok, 115 migration → 2 |
| X06 | `dogrulandi` ("5+") | **Gerçek ve daha büyük: 21 implementasyon / 6 dosya** |
| X04 | `dogrulandi` (883 satır) | Gerçek, **910 satıra büyümüş** |
| `user_item_fsrs` | blocker | Gerçek — `to_regclass` → `None` |
| 401 sıçraması | *(yeni)* | Gerçek — zaman çizelgesiyle ölçüldü |

**Kalıcı ders (bu turda üç kez ısırdı):** kütüğü veya `grep` çıktısını okumak
ölçüm değildir. Üç ayrı tasarım kusurunun üçü de bu sınıftandı (§7).

---

## 1. Kapsam

### İçeride

| # | Kalem | Tür |
|---|---|---|
| **İ0** | 401 sıçramasının kök nedenini **yığın iziyle** kanıtla | ölçüm (İ1'in önkoşulu) |
| **İ1** | Public-rota 401 muafiyeti | **kod — kullanıcı-görünür** |
| **İ2** | `user_item_fsrs` kök neden + kalıcı restore | kod + şema |
| **İ3** | X06 rol-kapısı envanteri | ölçüm (kod değişikliği YOK) |
| **İ4** | Kütük temizliği: X11 (1. kol) · U25 · X04 | kütük |
| **İ5** | X11 2. kol — `student_answers` yazılmıyor | kod |

### Dışarıda

- **SMTP (#441)** — operatör işi, kimlik bilgisi bekleniyor.
- **X06 birleştirme** — kullanıcı kararı: bu turda yalnız envanter.
- **X04 kesme** — CLAUDE.md talimat dosyası; 910 satırı kısaltmak ayrı tur.
- **Migration `_archive` arkeolojisi** — İ2'nin ihtiyacı kadarı hariç.

### A1 bağlantısı

CLAUDE.md'nin tek kabul kriteri A1 altın yolu; E3 kuralı oturum başına en az bir
**kullanıcı-görünür** çıktı istiyor. Bu turda E3'ü **İ1** karşılıyor (öğrenci
doğrulama ekranını fiilen görebilecek). Kalanlar altyapı/ölçüm — devir notunda
gerekçesiyle işaretlenir.

---

## 2. İ0 — Kök nedeni KANITLA (İ1'in önkoşulu)

### Neden ayrı bir kalem

23 Ağu'da `grep "location.href = '/login'"` dört sonuç verdi ve bunlar
`/api/v1/osb/settings/` 401'leriyle **ilişkilendirildi**. İlişkilendirme ölçüm
değildir. Yönlendirme `ProtectedRoute`, `RoleBasedLayout` veya `AuthProvider`
kaynaklı da olabilir. `debugging-first.md` kapısı İ1 için henüz geçilmedi.

### Ölçüm

Tarayıcıda `window.location`'ın `href` setter'ı ve `history.pushState`/
`replaceState` enstrümante edilir; yönlendirme anında `new Error().stack`
yakalanır. Sayfa `/eposta-dogrula?token=<taze>` ile açılır.

### Kabul kriteri

Yönlendirmeyi yapan **dosya:satır** yığın izinden okunur. Ek olarak
**karşı-olgusal**: o yol devre dışı bırakıldığında sıçrama **kaybolmalı**
(`audit-methodology.md` — *"Y'yi kaldır, X kayboluyor mu?"*). Kaybolmuyorsa
tek sebep değildir ve İ1'in kapsamı yeniden çizilir.

**Karşı-olgusalın yöntemi (belirsiz bırakılmaz):** kaynak dosyada geçici
mutasyon **yapılmaz** — frontend rebuild gerektirir ve tur uzar. Bunun yerine
tarayıcıda çalışma anında yama uygulanır: yığın izinin gösterdiği modülün
yönlendirme çağrısı `page.addInitScript` ile etkisizleştirilir (ör. `location`
setter'ı yutulur) ve sayfa yeniden açılır. Sıçrama kayboluyorsa neden
kanıtlanmıştır. Yama yalnız tarayıcı oturumunda yaşar, depoda iz bırakmaz.

**İ0 tamamlanmadan İ1 için tek satır kod yazılmaz.**

---

## 3. İ1 — Public-rota 401 muafiyeti

### Bulgu (23 Ağu, temiz tarayıcı: çerez + localStorage + SW + cache silinmiş)

```
0ms    /eposta-dogrula  h1=null
250ms  /eposta-dogrula  h1="E-posta Dogrulama"  status="Dogrulaniyor..."
500ms  /login           <- FIRLATILDI
750ms  /login           h1="Tekrar hos geldin."
```

Hesap **doğrulanıyor** (`POST /eposta-dogrula/verify` → 200, DB `is_verified=True`)
ama kullanıcı onay mesajını **hiç görmüyor**. `/register` de aynı şekilde sıçrıyor
→ kusur L2'ye özgü değil, **global**.

### Muafiyet kavramı zaten var, listesi eksik

| Dosya | Mevcut muafiyet |
|---|---|
| `frontend/src/utils/apiHelpers.ts:466` | `pathname !== '/login'` |
| `frontend/src/services/apiClient.ts:76` | `pathname !== '/login'` |
| `frontend/src/kiro/api/api-client.ts:146` | `pathname !== '/login'` — yorumu *"apiHelpers ile aynı sözleşme"* |
| `frontend/src/services/learningStyleService.ts:31` | **YOK** — koşulsuz + `setTimeout(0)` |

Üç yerde kopyalanmış, dördüncüde unutulmuş. Deponun kendi kuralı
(*"abstraction SADECE 3+ yerde tekrar ediyorsa"*) soyutlamayı meşru kılıyor.

### Tasarım

`frontend/src/utils/publicRoutes.ts`:

```ts
export const PUBLIC_ROUTES = [...] as const;
export function girisYonlendirmesiGerekli(pathname: string): boolean;
```

Dört çağrı yeri (İ0 doğrularsa) bunu kullanır.

### Kayma kontrolü — regex DEĞİL, inşa ile tekillik

İlk taslak bekçinin `App.tsx`'i regex ile ayrıştırmasını öneriyordu. **Reddedildi:**
TSX regex'i kırılgan ve `<Navigate>` ile `<PageTransition>` rotalarını ayırt etmesi
gerekiyor. Tercih edilen: **`App.tsx` public rotalarını `PUBLIC_ROUTES`'tan
türetsin** — liste ile rotalar aynı şey olur, kayma yapısal olarak imkânsızlaşır.

`App.tsx`'in yapısı buna direnirse (heterojen element'ler) geri düşüş: kaynak
ayrıştıran bekçi **+ zorunlu körleşme güvencesi** (çıkarım ≥5 rota bulmazsa test
"alet arızası" diye düşer).

### Kabul kriterleri

1. `girisYonlendirmesiGerekli()` birim testleri — public rota `false`, korumalı rota `true`.
2. Dört çağrı yerinin **dördü de** yardımcıyı kullanıyor (kopyala-yapıştır geri gelmesin).
3. **Canlı, tarayıcıda:** yukarıdaki zaman çizelgesi tekrarlanır; `/eposta-dogrula`
   sayfada **kalır** ve `status` metni *"doğrulandı"* olur. Bu, kalemin tek gerçek
   kabul kanıtıdır — birim testleri tek başına yetmez.

---

## 4. İ2 — `user_item_fsrs`

### Ölçülen (23 Ağu)

```
to_regclass('public.user_item_fsrs') -> None          (tablo YOK)
alembic/versions_archive/20260410_create_user_item_fsrs.py    <- tanimlanmis
alembic/versions_archive/20260801_restore_user_item_fsrs.py   <- bir kez de restore edilmis
core/alembic_autogen_guard.py + test_alembic_autogen_guard.py <- bekci ZATEN VAR
```

Tüketiciler (ölü değil): `app/services/fsrs_service.py` · `fsrs_engine.py` ·
`learning_path_orchestrator.py` · `cat_session.py` · `app/api/fsrs.py` ·
`api/teacher_copilot_api.py`.

### Çürütülen hipotez

İlk taslak *"tablo hiçbir migration'da tanımlı değil, ad-hoc yaratılmış"* diyordu.
**Yanlış** — iki kez tanımlanmış. İkisi de `versions_archive`'da, yani göç yolunda
değil. Dolayısıyla reçete de değişiyor: "yeni model yaz + autogenerate" **değil**.

### Ölçülecek iki soru (fix'ten önce)

1. `0001_baseline_squash.py` tabloyu içeriyor mu? İçermiyorsa squash onu düşürmüş
   demektir — bu, tekrarlayan kaybın kök nedenidir.
2. **`alembic_autogen_guard` neden yakalamadı?** Bekçi var ve tablo kayıp. Bekçinin
   kendisi bir kusur taşıyor olabilir (bu depoda ölü bekçi sınıfı defalarca görüldü:
   S238 XPASS, S246 `parents[2]`, S248 yanlış bundle yolu).

Reçete bu iki ölçümden **sonra** yazılır.

### Kabul kriterleri

1. Kök neden `dosya:satır` düzeyinde yazılı.
2. Tablo canlı DB'de var (`to_regclass` → dolu) ve **göç yolunda** tanımlı
   (arşivde değil) — aksi hâlde bir sonraki sıfırlamada yine düşer.
3. `tests/integration/test_fsrs_schema_contract.py` iki kırmızısı yeşile döner.
4. Enforcement: ya mevcut `alembic_autogen_guard`'ın kusuru kapanır ya da
   **neden kapatılmadığı ölçümle** yazılır (+0 değer kuralı).

---

## 5. İ3 — X06 rol-kapısı envanteri (ölçüm, kod YOK)

### Ölçülen

Kütük "5+" diyordu; 23 Ağu grep'i **21 implementasyon / 6 dosya** gösterdi
(`auth_dependencies.py` 8 · `authorization.py` 5 · `dependencies.py` 3 ·
`jwt_auth.py` 2 · `enhanced_authentication.py` 2 · +1).

### Envanterin cevaplayacağı sorular

Her implementasyon için: tanım yeri · kaç uçtan çağrılıyor · **ÖLÜ mü** ·
hangi rol kümesini kabul ediyor.

**Belirleyici soru:** *iki kapı aynı rolü farklı mı yargılıyor?* Sayı tek başına
kusur değildir — **tutarsızlık** kusurdur. Çelişki bulunmazsa X06 kütükte
`dogrulandi` → `abartili`'ya iner.

### Kabul kriteri

`docs/audits/2026-08-23_x06_rol_kapisi_envanteri.md` — 21 satırlık tablo +
tutarsızlık bulgusu (varsa birebir kanıtla, yoksa "aranmış ve bulunamamış"
açıkça yazılı). Kod değişikliği **yok**.

---

## 6. İ4 / İ5 — Kütük ve X11'in ikinci kolu

### X11 iki koludur — kütük birebir "İKİ AYRI FIX" diyor

| Kol | Durum |
|---|---|
| (1) `offline_sync_api.py` imajda yok → 404 | **Bugün kapandı** — dosya imajda, canlı openapi'de 4 offline yolu, uçlar 401/405 |
| (2) `offline_sync_service.py:207` docstring `student_answers`'a yazdığını söylüyor, kod yalnız `db.add(card)` yapıyor | **AÇIK — ve bugün ulaşılabilir oldu** |

Kütük şunu yazıyor: *"Şu an (1) kapalı olduğu için (2) tetiklenemez — sıralı
bağımlılık var, (1) önce."* **Bugünkü rebuild (1)'i açtı, dolayısıyla (2) artık
canlı bir kod yolu.** Önce 404 ile erişilemezdi; şimdi kayıtlı.

X11'i toptan `uygulandi` yapmak **S246'daki X10 hatasının birebir tekrarı** olur
(*"İki kolu varmış; önceki fix yalnız birincisini kapatmış"*).

**İ5 kapsamı:** gerçek bir sync isteğiyle `student_answers`'a satır oluşup
oluşmadığı ölçülür.

**Karar kuralı (belirsiz bırakılmaz).** Ölçüm sonucuna göre iki yoldan **biri**,
tartışmasız:

| Ölçüm | Aksiyon |
|---|---|
| Satır oluşuyor | Docstring doğru; X11 2. kol **fantom** → kütük `fantom`, kod değişmez |
| Satır oluşmuyor **ve** uca canlı çağrı var | Veri kaybı → **yazım eklenir** (TDD + mutasyon) |
| Satır oluşmuyor **ve** uca hiç çağrı yok (kütük: 0 paket) | **Docstring koda uydurulur** (yalan silinir). Yazım eklemek kullanılmayan bir yola özellik yazmak olur — YAGNI ve "+0 değer" kuralı |

Üçüncü satırda "yazım eklenmedi" kararı devir notuna **gerekçesiyle** yazılır;
sessizce atlanmaz.

### İ4 / İ5 kabul kriterleri

1. `iddialar.yaml`: X11 → **kol bazında** işaretli (1 kapandı / 2'nin durumu
   ölçüme göre) · U25 yeniden çerçevelenmiş · X04 güncel sayıyla (910).
2. Her kütük değişikliği için `kanit` alanı **bu turun ölçümüyle** doldurulur.
3. `backend/tests/unit/test_ders_kaydi.py` ve kütük bekçileri yeşil kalır.

### U25 — yeniden çerçeveleme

Ankraj (`fa067642bdfe_force_drop_questions`) **yok**; 115 migration
`versions_archive`'a squash edilmiş, göç yolunda **2 dosya** var ve ikisinde de
`downgrade()` mevcut. İddianın öncülü bayat. Yeni soru: *bu 2 migration'ın
geri-alınabilirliği test ediliyor mu?* — ölçülür, kütük buna göre güncellenir.

### X04

CLAUDE.md **910** satır (iddia 883 derken). Gerçek ama bu turda **kesilmez**;
kütükte güncel sayıyla işaretlenir.

---

## 7. Doğrulama sözleşmesi (her kod kalemi için, atlanamaz)

Bu maddelerin her biri bu depoda en az bir kez ısırdı:

1. **RED önce** — fix'ten önce düşen test.
2. **Mutasyon ≥3, hepsi ölmeli** — ankraj tekilliği (`count == 1`) doğrulanır.
   Mutasyon **commit sonrası** koşulur; commit'siz iş `git stash push -- <dosya>`
   ile mutasyona sokulur, `git checkout HEAD --` ile **asla**.
3. **Kontrol kolu** — her bulgu için: HEAD'de de var mı? Varsa devralınmıştır.
4. **Körleşme güvencesi** — her yeni bekçi boş küme üzerinde geçemez.
5. **Kapı** — `pre-commit run --files` **depo kökünden**; `SKIP` üç kollu
   ölçülmeden kullanılmaz (benim satırlarım temiz mi · kontrol kolu · yaygınlık).
6. **Commit** — mesaj `git commit -F <dosya>` ile; hash'in **değiştiği** ölçülür.
7. **Canlı doğrulama** — kod imaja girmeden "canlı" sayılmaz (#511 dersi).

### Bekçi tasarım kuralı (S248'de kazanıldı)

Bekçi **sabit değer beklememeli**. `assert port == 3000` bugün geçer, yarın
sessizce yanlış kalır. İki bağımsız kaynağı karşılaştır. Aynı kural İ1'in rota
listesine uygulanır.

---

## 8. Workflow şekli

| Faz | İçerik | Şekil |
|---|---|---|
| **1 — Ölçüm** | İ0 yığın izi · İ2 squash+bekçi kök neden · İ3 X06 envanteri · İ4 kütük doğrulama · İ5 `student_answers` ölçümü | paralel |
| **2 — Uygulama** | İ1 kod+bekçi → İ2 şema+bekçi → İ5 (ölçüm ne derse) | sıralı, izole |
| **3 — Çürütme** | **yalnız kod değiştiren kalemler** için 2 bağımsız çürütücü, anlaşmazlıkta `kanit-hakemi` | paralel |
| **4 — Canlı** | frontend+backend rebuild · tarayıcı zaman çizelgesi · E2E | sıralı |

**Ajan bütçesi:** oturum kılavuzu ~15. Faz 3 bu yüzden yalnız kod kalemlerine
uygulanır; ölçüm kalemleri (İ3, İ4) çürütücüye gönderilmez.

---

## 9. Riskler

| Risk | Azaltma |
|---|---|
| İ0 kök nedeni beklenenden farklı çıkar, İ1 kapsamı büyür | İ0 bir **kapı**: sonuç farklıysa kullanıcıya dönülür, kör devam edilmez |
| `App.tsx` inşa-ile-tekilliğe direnir | Regex bekçi + zorunlu körleşme güvencesi (geri düşüş belgeli) |
| Yeni FSRS modeli `Table already defined` verir | `testing.md` #6: relative import (`from .base import Base`) |
| İ2'nin kök nedeni migration geçmişinde derine iner | Kapsam sınırı: **squash + bekçi** ile sınırlı; arşiv arkeolojisi kapsam dışı |
| Frontend rebuild ~3-4 dk × 2 | Kabul edilir; canlı doğrulama pazarlık dışı |
| Bu spec'in kendisi bayatlar | Her faz başında öncüller yeniden ölçülür (S245 dersi: *"bir planın kendisi de bayatlar"*). Somut olarak: Faz 2'ye girmeden önce Faz 1'in bulguları hâlâ geçerli mi diye tek komutla doğrulanır |

---

## 10. Kapsam dışı bırakılanların gerekçesi

- **SMTP #441** — operatör; kod tarafı hazır, kapı varsayılan KAPALI.
- **X06 birleştirme** — 21 implementasyona dokunmak A1'in dört ayağını birden
  düşürebilir; kullanıcı kararıyla önce envanter.
- **X04 kesme** — CLAUDE.md talimat dosyası; içerik kesmek davranış değiştirir.

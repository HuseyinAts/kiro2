# İ0 — Anonim ziyaretçinin public rotadan sıçratılması: kök neden

**Tarih:** 23 Ağustos 2026 (S249) · **Plan:** `docs/superpowers/plans/2026-08-23-acik-kalemler-uygulama.md` Task 1
**Spec:** `docs/superpowers/specs/2026-08-23-acik-kalemler-design.md` §2
**Ortam:** kiro2-frontend (23 Ağu imajı) · kiro2-backend (23 Ağu imajı) · Playwright/Chromium

---

## Neden bu ölçüm yapıldı

S248'de sıçrama gözlendi ve kök neden olarak
`grep "location.href = '/login'"` sonucu (4 dosya) ile `/osb/settings/` 401'leri
**ilişkilendirildi**. İlişkilendirme ölçüm değildir. `debugging-first.md` kapısı bu
kalem için geçilmemişti. Spec bu yüzden İ1'in önüne bir **kapı** koydu: kök neden
yığın izi ve karşı-olgusalla kanıtlanmadan kod yazılmayacaktı.

**İyi ki kondu:** ilk hipotezi test eden ilk ölçüm onu doğrulamadı (§2) ve üç ayrı
alet arızası bulgu diye raporlanmaktan son anda kurtarıldı (§5).

---

## 1. Semptom (S248'de ölçülmüş, burada tekrarlandı)

Temiz tarayıcı (çerez + localStorage + SW + cache silinmiş):

```
0ms    /eposta-dogrula  h1=null
250ms  /eposta-dogrula  h1="E-posta Dogrulama"  status="Dogrulaniyor..."
500ms  /login           <- FIRLATILDI
750ms  /login           h1="Tekrar hos geldin."
```

Hesap **doğrulanıyor** (`POST /eposta-dogrula/verify` → 200, DB `is_verified=True`)
ama kullanıcı onay mesajını **hiç görmüyor**. `/register` de aynı şekilde sıçrıyor
→ kusur L2'ye özgü değil, global.

---

## 2. Mekanizma: SERT gezinme mi, router gezinmesi mi?

İlk deneme `window.location.href` setter'ını enstrümante etmeye çalıştı ve
**başarısız oldu**:

```
hrefHata: "TypeError: Cannot redefine property: href"
```

Chrome'da `href`, `location` örneğinin **yapılandırılamaz kendi özelliği**;
prototip üzerinden gölgelenemez. Yakalanan tek kayıt `history.replaceState` idi ve
çağıranı `vendor-router` (React Router) görünüyordu — **ilk bakışta "router yaptı"
denecekti**. Ama `hedef: undefined` idi, yani URL değiştirmeyen bir açılış çağrısı.
Yani ölçüm **kesin değildi** ve öyle raporlandı.

### Ayırt edici sinyal (aletten bağımsız)

Sert gezinme belgeyi **yeniden yükler**; router gezinmesi yüklemez. `addInitScript`
her belge için koşar, `sessionStorage` sekme ömrü boyunca yaşar:

```json
{
  "belgeYuklemeSayisi": 2,
  "herYuklemeninAcilisYolu": ["/eposta-dogrula", "/login"],
  "unloadYolu": "/eposta-dogrula",
  "sonYol": "/login"
}
```

**Belge iki kez yüklendi**, `beforeunload` `/eposta-dogrula`'da ateşlendi, ikinci
belge `/login`'de açıldı. → **SERT GEZİNME**. React Router değil.

---

## 3. Karşı-olgusal: nedeni kaldır, semptom kayboyor mu?

İlk iki karşı-olgusal denemesi **efekti** (gezinmeyi) engellemeye çalıştı ve ikisi
de alet arızasına düştü (§5). Üçüncü deneme **nedeni** kaldırdı: anonim kullanıcıya
`401` dönen uçlar `200`'e çevrildi (Playwright `page.route`, API çağrıları XHR/fetch
olduğu için service worker precache'i onları servis etmiyor — bu yol **görülüyor**).

```json
{
  "stubEdilen": ["osb/settings", "osb/settings", "osb/settings", "osb/settings", "refresh/secure"],
  "yol": "/eposta-dogrula",
  "belgeYukleme": 1,
  "h1": "E-posta Doğrulama",
  "durum": "E-posta adresiniz doğrulandı. Artık giriş yapabilirsiniz.",
  "girisLinki": true
}
```

Konsol: **0 hata**.

**Sonuç:** 401'ler kaldırıldığında sıçrama **kayboluyor**, belge tek kez yükleniyor
ve kullanıcı onay mesajını **görüyor**. `audit-methodology.md`'nin kök neden testi
(*"Y'yi kaldır — X kayboluyor mu?"*) **geçildi**.

Bu çıktı aynı zamanda İ1'in **beklenen kullanıcı-görünür sonucudur**: fix sonrası
canlı ölçüm (plan Task 9 Adım 4) birebir bunu üretmeli.

---

## 4. Ateşleyen çağrı yeri — kanıtlı zincir

```
frontend/src/hooks/useAccessibilitySettings.ts       (her sayfada mount olur)
  -> frontend/src/services/osbService.ts:165          apiClient.get('/api/v1/osb/settings/')
    -> frontend/src/services/apiClient.ts:64          response interceptor 401 yakalar
      -> apiClient.ts:69                              refreshAccessToken() denenir
        -> POST /api/v1/auth/refresh/secure           401 (anonim) / 429 (kota dolu)
          -> apiClient.ts:76-78                       window.location.href = '/login'
```

`osbService.ts:13` → `import apiClient from './apiClient'` (ölçüldü).

### Dürüst sınır — İDDİA EDİLMEYEN

Yalnızca **`apiClient.ts:76-78`**'in ateşlendiği kanıtlandı. Diğer üç dosya
(`apiHelpers.ts:467`, `kiro/api/api-client.ts:147`, `learningStyleService.ts:31`)
**aynı kusur sınıfını taşıyor ama bu senaryoda ateşlendikleri ölçülmedi.**

Bunlar İ1 kapsamında yine de düzeltilir — gerekçe *"ateşlendiler"* değil,
**sınıfın kendisi**: üçü de `pathname !== '/login'` kopyası taşıyor ve dördüncüsü
(`learningStyleService.ts`) **hiç muafiyet taşımıyor**, yani `/login` sonsuz
sıçrama korumasından bile yoksun. Bu, kanıtlanmış bir ateşleme değil, **önlenmiş
bir sınıf**tır ve devir notunda böyle kaydedilir.

---

## 5. Alet arızaları — üçü de bulgu diye raporlanmadan yakalandı

Bu bölüm dürüstlük kaydıdır: ölçümün kendisi üç kez yanıldı.

| # | Alet | Belirti | Neden yanıldı | Nasıl yakalandı |
|---|---|---|---|---|
| 1 | `Object.defineProperty(window.location, 'href', …)` | `TypeError: Cannot redefine property` | `href`, `location` örneğinin yapılandırılamaz **kendi** özelliği | Hata açıkça döndü; "veri yok" olarak raporlandı, `replaceState` kaydı **cevap sanılmadı** |
| 2 | `page.route` ile `/login` document isteğini iptal | `engellenenSertGezinme: 0` ama `belgeYukleme: 2` | **Service worker** (Workbox) kabuğu precache'ten servis ediyor; gezinme ağ katmanına düşmüyor | Sayaç ile route kaydı **çelişti** — çelişki alet arızasının imzası |
| 3 | SW'yi kaldırıp (2)'yi tekrarlamak | `swKontrolEden: true` yine | Uygulama her yüklemede SW'yi **yeniden kaydediyor** | Aynı çelişki tekrarladı; efekti engellemek bırakılıp **nedeni kaldırmaya** geçildi |

**Ders:** bir karşı-olgusalda **efekti** engellemek kırılgandır (araya SW, tarayıcı
içselleri, non-configurable özellikler girer); **nedeni** kaldırmak sağlamdır.
Neden tarafı uygulamanın kendi HTTP yüzeyindedir ve enstrümante edilebilir.

---

## 6. İ1 için sonuç

- **KAPI GEÇİLDİ.** Kök neden kanıtlandı, karşı-olgusal semptomu kaldırdı.
- İ1 planlandığı gibi ilerler: kanonik `girisYonlendirmesiGerekli()` + 4 çağrı yeri.
- Kabul kanıtı §3'teki çıktının **stub olmadan** üretilmesidir.

# S249 Açık Kalemler — Uygulama Planı

> **Ajan işçiler için:** GEREKLİ ALT-SKILL: `superpowers:subagent-driven-development`
> (önerilen) veya `superpowers:executing-plans`. Adımlar `- [ ]` kutucuk sözdizimi
> kullanır.

**Hedef:** S248'den kalan altı açık kalemi kapatmak; kullanıcı-görünür olan tek
kalem (İ1) öğrencinin e-posta doğrulama onayını fiilen görebilmesini sağlar.

**Mimari:** Ölçüm-önce. İki kalem (İ0, İ2) kök nedeni kanıtlamadan koda geçmez;
iki kalem (İ3, İ4) hiç kod değiştirmez. İ1 mevcut `pathname !== '/login'`
desenini genelleştirir — yeni mimari değil, kopyalanmış bir kuralın tekilleştirilmesi.

**Teknoloji:** React 18 + TypeScript (Vite), vitest, Playwright · FastAPI +
SQLAlchemy async, pytest, Alembic · PostgreSQL 18 (port 5434) · Docker Compose

**Spec:** `docs/superpowers/specs/2026-08-23-acik-kalemler-design.md`

---

## Dosya Yapısı

| Dosya | Sorumluluk | Durum |
|---|---|---|
| `frontend/src/utils/publicRoutes.ts` | **Tek** karar noktası: bu yolda 401 sonrası sert yönlendirme yapılır mı? | **Oluştur** |
| `frontend/src/utils/__tests__/publicRoutes.test.ts` | Politikanın birim testleri | **Oluştur** |
| `frontend/src/utils/__tests__/publicRoutes.kayma.test.ts` | Kayma bekçisi: liste ↔ `App.tsx` invaryantları + çağrı yeri kapsamı | **Oluştur** |
| `frontend/src/utils/apiHelpers.ts:462-470` | 401 dalı → yardımcıyı kullan | Değiştir |
| `frontend/src/services/apiClient.ts:73-80` | refresh-fail dalı → yardımcıyı kullan | Değiştir |
| `frontend/src/kiro/api/api-client.ts:144-149` | `redirectToLogin()` → yardımcıyı kullan | Değiştir |
| `frontend/src/services/learningStyleService.ts:26-35` | **muafiyeti hiç yok** → yardımcıyı kullan | Değiştir |
| `docs/audits/2026-08-23_i0_yonlendirme_kok_neden.md` | İ0 yığın izi kanıtı | Oluştur |
| `docs/audits/2026-08-23_x06_rol_kapisi_envanteri.md` | İ3 envanteri | Oluştur |
| `docs/audits/2026-08-12_25uzman/iddialar.yaml` | İ4 kütük güncellemesi | Değiştir |

**Not — spec'ten sapma (ölçümle gerekçelendirildi):** Spec "App.tsx public rotaları
`PUBLIC_ROUTES`'tan türetsin (inşa ile tekillik)" diyordu. Ölçüldü ve **reddedildi**:
App.tsx'te `ProtectedRoute` içermeyen 14 rota var ama bunların yalnız 9'u anlamsal
olarak public; `*`, `/`, `/veli-takip`, `/parent-new` korumalı hedeflere `<Navigate>`
ediyor. Türetme yapılsaydı `*` (catch-all) muaf sayılırdı — kusuru genişletirdi.
Bu yüzden **küratörlü liste + üç invaryantlı bekçi** kullanılıyor.

---

## Faz 1 — Ölçüm (kod yazılmadan önce)

### Task 1: İ0 — Yönlendirmenin kök nedenini yığın iziyle KANITLA

**Neden:** 23 Ağu'da `grep "location.href = '/login'"` dört sonuç verdi ve bunlar
`/osb/settings/` 401'leriyle **ilişkilendirildi**. İlişkilendirme ölçüm değildir.
`debugging-first.md` kapısı bu kalem için henüz geçilmedi.

**Files:**
- Create: `docs/audits/2026-08-23_i0_yonlendirme_kok_neden.md`

- [ ] **Adım 1: Taze doğrulama linki üret**

Container içinde kullanıcı kaydı + token üretimi (düz metin token hiçbir yerde
saklanmıyor; yan kanaldan üretilir — aynı pepper, aynı Redis):

```bash
cat > backend/_i0_link.py <<'PY'
import asyncio, json, os, sys, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EPOSTA = sys.argv[1]
async def ana():
    istek = urllib.request.Request(
        "http://localhost:8000/api/v1/auth/kayit",
        data=json.dumps({"email": EPOSTA, "ad_soyad": "I0 Olcum",
                         "sifre": "Kiro2Guclu!Parola47", "rol": "ogrenci"}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(istek, timeout=30) as y:
        print("kayit:", y.status)
    from sqlalchemy import text
    from core.database import db_manager
    from core.eposta_dogrulama import store_al
    async with db_manager.get_session() as s:
        r = (await s.execute(text("SELECT id FROM users WHERE lower(email)=:e"),
                             {"e": EPOSTA.lower()})).fetchone()
    token = await (await store_al()).token_uret(str(r.id), EPOSTA)
    print(f"LINK={os.environ.get('FRONTEND_URL','http://localhost:3000')}/eposta-dogrula?token={token}")
asyncio.run(ana())
PY
MSYS_NO_PATHCONV=1 docker cp backend/_i0_link.py kiro2-backend:/app/_i0_link.py
MSYS_NO_PATHCONV=1 docker exec kiro2-backend python /app/_i0_link.py "i0-$(date +%s)@kiro2-e2e.dev" | grep LINK=
```

Beklenen: `kayit: 201` ve `LINK=http://localhost:3000/eposta-dogrula?token=...`

- [ ] **Adım 2: `window.location` ve `history` enstrümante et, yığın izini yakala**

Playwright MCP `browser_run_code_unsafe` ile. `addInitScript` **sayfa kodundan
önce** çalışır, bu yüzden yönlendirmeyi ilk yapan kim olursa yakalanır:

```js
async (page) => {
  await page.context().clearCookies();
  await page.addInitScript(() => {
    window.__yonlendirmeler = [];
    const kaydet = (tur, hedef) => {
      window.__yonlendirmeler.push({ tur, hedef, yigin: new Error().stack });
    };
    const asil = Object.getOwnPropertyDescriptor(window.Location.prototype, 'href');
    Object.defineProperty(window.location, 'href', {
      configurable: true,
      get() { return asil.get.call(window.location); },
      set(v) { kaydet('location.href', v); /* YUTULMAZ: gercek davranis korunur */
               return asil.set.call(window.location, v); },
    });
    for (const m of ['pushState', 'replaceState']) {
      const o = history[m].bind(history);
      history[m] = (s, t, u) => { kaydet(`history.${m}`, String(u)); return o(s, t, u); };
    }
    window.location.assign = new Proxy(window.location.assign, {
      apply(t, self, args) { kaydet('location.assign', String(args[0])); return Reflect.apply(t, self, args); },
    });
  });
  await page.goto('<ADIM 1 LINKI>', { waitUntil: 'commit' });
  await page.waitForTimeout(4000);
  return await page.evaluate(() => (window.__yonlendirmeler || []).map(
    x => ({ tur: x.tur, hedef: x.hedef, yigin: String(x.yigin).split('\n').slice(1, 7).join(' | ') })
  ));
}
```

Beklenen: en az bir `/login` hedefli kayıt; `yigin` alanı **dosya:satır** içerir.

- [ ] **Adım 3: Karşı-olgusal — sebebi kaldır, sıçrama kayboluyor mu?**

Kaynak dosyaya **dokunulmaz** (rebuild gerektirir). Çalışma anında yutulur:

```js
async (page) => {
  await page.context().clearCookies();
  await page.addInitScript(() => {
    const asil = Object.getOwnPropertyDescriptor(window.Location.prototype, 'href');
    Object.defineProperty(window.location, 'href', {
      configurable: true,
      get() { return asil.get.call(window.location); },
      set(v) { if (String(v).includes('/login')) { window.__yutuldu = (window.__yutuldu||0)+1; return; }
               return asil.set.call(window.location, v); },
    });
  });
  await page.goto('<ADIM 1 LINKI (YENI TOKEN)>', { waitUntil: 'commit' });
  await page.waitForTimeout(4000);
  return await page.evaluate(() => ({
    yol: location.pathname,
    yutulan: window.__yutuldu || 0,
    durum: document.querySelector('[role="status"]')?.textContent?.trim() ?? null,
  }));
}
```

Beklenen: `yol === '/eposta-dogrula'`, `yutulan >= 1`, `durum` *"doğrulandı"*.

**KAPI:** `yol` hâlâ `/login` ise sebep `location.href` **değildir** (router
seviyesinde bir `<Navigate>`/`useNavigate` vardır). Bu durumda **DUR**, bulguyu
raporla, İ1'in kapsamını yeniden çiz. Kör devam etme.

- [ ] **Adım 4: Bulguyu belgele ve commit et**

`docs/audits/2026-08-23_i0_yonlendirme_kok_neden.md` — Adım 2'nin yığın izi
(birebir), Adım 3'ün karşı-olgusalı, ve **hangi çağrı yerlerinin gerçekten
ateşlendiği** (4'ünün hepsi mi, bir kısmı mı).

```bash
rm -f backend/_i0_link.py
MSYS_NO_PATHCONV=1 docker exec kiro2-backend rm -f /app/_i0_link.py
git add docs/audits/2026-08-23_i0_yonlendirme_kok_neden.md
git commit -F <mesaj-dosyasi>
git show --stat --format="" HEAD   # ne girdigini OKU
```

---

### Task 2: İ2 — `user_item_fsrs` kök nedenini ölç

**Neden:** İlk hipotez (*"ad-hoc yaratılmış, migration'da yok"*) **çürüdü** —
tablo iki migration'da tanımlı, ikisi de `versions_archive`'da. Reçete ölçümden
sonra yazılır.

**Files:** (bu task'ta kod değişmez)

- [ ] **Adım 1: Squash tabloyu içeriyor mu?**

```bash
grep -c "user_item_fsrs" backend/alembic/versions/0001_baseline_squash.py
grep -c "user_item_fsrs" backend/alembic/versions/0002_is_active_server_default.py
grep -n "user_item_fsrs" backend/alembic/versions_archive/20260801_restore_user_item_fsrs.py | head -5
```

Beklenen ayrım: göç yolundaki iki dosyada **0** çıkarsa squash tabloyu düşürmüş
demektir — tekrarlayan kaybın kök nedeni budur.

- [ ] **Adım 2: Alembic'in gördüğü baş (head) ve uygulanan sürüm**

```bash
MSYS_NO_PATHCONV=1 docker exec kiro2-backend python -c "
import asyncio,sys
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
from sqlalchemy import text
from core.database import db_manager
async def m():
    async with db_manager.get_session() as s:
        r=(await s.execute(text('SELECT version_num FROM alembic_version'))).fetchall()
    print('alembic_version:', [x.version_num for x in r])
asyncio.run(m())"
```

- [ ] **Adım 3: Mevcut bekçi neden yakalamadı?**

```bash
cd backend && python -m pytest tests/integration/test_alembic_autogen_guard.py -v --tb=short -p no:cacheprovider 2>&1 | tail -20
```

Üç olasılık ve ayırt edici sinyalleri:
- Bekçi **skip** oluyor (DB yok / koşul sağlanmıyor) → çıktıda `skipped`
- Bekçi **geçiyor ama tabloyu görmüyor** (ORM modeli import edilmiyor) → `passed`,
  ama `grep "user_item_fsrs" backend/core/alembic_autogen_guard.py` = 0
- Bekçi **kırmızı** ve kimse bakmıyor → `failed`

- [ ] **Adım 4: ORM modeli var mı?**

```bash
grep -rn "user_item_fsrs" backend/models/ backend/app/models/ 2>/dev/null | head
grep -rn "__tablename__.*user_item_fsrs" backend/ --include="*.py" | head
```

- [ ] **Adım 5: Bulguyu Task 6'ya taşı (henüz commit yok — ölçüm notu)**

Kök neden `dosya:satır` düzeyinde yazılır. **KAPI:** kök neden squash/göç yolu
DIŞINDA bir şey çıkarsa (ör. bir script tabloyu düşürüyor), **DUR** ve raporla.

---

### Task 3: İ3 — X06 rol-kapısı envanteri (kod değişikliği YOK)

**Files:**
- Create: `docs/audits/2026-08-23_x06_rol_kapisi_envanteri.md`

- [ ] **Adım 1: 21 implementasyonu ve çağıranlarını say**

```bash
python - <<'PY'
import re, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
kok = Path("backend")
tanimlar = []
for p in sorted(kok.glob("core/*.py")):
    for i, s in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        m = re.match(r"\s*(?:async\s+)?def\s+(require_\w+)", s)
        if m:
            tanimlar.append((str(p).replace("\\", "/"), i, m.group(1)))
print(f"tanim sayisi: {len(tanimlar)}\n")
for yol, satir, ad in tanimlar:
    ok = subprocess.run(["rg", "-l", rf"\b{ad}\b", "backend", "--glob", "!**/tests/**",
                         "--glob", "*.py"], capture_output=True, text=True).stdout.split()
    ok = [x for x in ok if x.replace("\\", "/") != yol]
    print(f"{ad:32} {yol}:{satir:<5} cagiran_dosya={len(ok)}  {'OLU' if not ok else ''}")
PY
```

- [ ] **Adım 2: Belirleyici ölçüm — iki kapı aynı rolü farklı mı yargılıyor?**

Her `require_*` için kabul edilen rol kümesini çıkar; **aynı adı taşıyan** ama
farklı küme kabul eden çiftleri listele (`require_role` üç dosyada var —
davranışları aynı mı?). Ayrıca rol adı yazımını karşılaştır: `'ogrenci'` vs
`'student'` vs `KullaniciRolu.OGRENCI`.

- [ ] **Adım 3: Envanteri yaz ve commit et**

Tablo: 21 satır (ad · dosya:satır · çağıran dosya sayısı · ÖLÜ mü · kabul ettiği
roller). Sonuç bölümü **iki şıktan biri**, açıkça:
- *Tutarsızlık bulundu:* birebir kanıtla → X06 `dogrulandi` kalır, birleştirme
  ayrı tura görev olarak yazılır.
- *Tutarsızlık aranmış, bulunamamış:* → X06 `abartili`'ya iner. **21 sayısı tek
  başına kusur değildir.**

---

### Task 4: İ5 — X11'in 2. kolu: `student_answers` yazılıyor mu?

**Neden:** Kütük birebir *"İKİ AYRI FIX"* diyor ve *"(1) kapalı olduğu için (2)
tetiklenemez"*. 23 Ağu rebuild'i (1)'i açtı → (2) artık **canlı bir kod yolu**.

- [ ] **Adım 1: Kod gerçekten `student_answers`'a yazıyor mu?**

```bash
grep -n "student_answers\|StudentAnswer\|db.add(" backend/app/services/offline_sync_service.py | head -20
sed -n '195,240p' backend/app/services/offline_sync_service.py
```

- [ ] **Adım 2: Uca canlı çağrı var mı? (karar kuralının 3. şıkkı için)**

```bash
for U in /api/v1/offline/sync-status /api/v1/offline/sync-results /api/v1/offline/sync-package; do
  printf "%-38s -> %s\n" "$U" "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 http://localhost:8000$U)"
done
grep -rn "offline/sync" frontend/src --include="*.ts" --include="*.tsx" | grep -v "\.test\." | head
```

- [ ] **Adım 3: Karar kuralını uygula (spec §6)**

| Ölçüm | Aksiyon |
|---|---|
| Satır oluşuyor | X11 2. kol **fantom** → kütük `fantom`, kod değişmez |
| Oluşmuyor **ve** canlı çağrı var | Veri kaybı → yazım ekle (TDD + mutasyon) |
| Oluşmuyor **ve** hiç çağrı yok | **Docstring'i koda uydur** (yalanı sil) |

Üçüncü şıkta "yazım eklenmedi" kararı devir notuna **gerekçesiyle** yazılır.

---

## Faz 2 — Uygulama

### Task 5: İ1 — `publicRoutes.ts` (TDD)

**ÖN KOŞUL:** Task 1 (İ0) tamamlanmış ve karşı-olgusal `yol === '/eposta-dogrula'`
vermiş olmalı. Vermemişse bu task **başlamaz**.

**Files:**
- Create: `frontend/src/utils/publicRoutes.ts`
- Test: `frontend/src/utils/__tests__/publicRoutes.test.ts`

- [ ] **Adım 1: Düşen testi yaz**

```ts
// frontend/src/utils/__tests__/publicRoutes.test.ts
import { describe, expect, it } from 'vitest';
import { PUBLIC_ROUTES, girisYonlendirmesiGerekli } from '../publicRoutes';

describe('girisYonlendirmesiGerekli', () => {
  it('anonim kullanicinin ait oldugu rotalarda yonlendirme YAPILMAZ', () => {
    for (const yol of ['/login', '/register', '/eposta-dogrula', '/veli-onay',
                       '/hesap-kurtarma', '/forgot-password', '/unauthorized',
                       '/404', '/error']) {
      expect(girisYonlendirmesiGerekli(yol), yol).toBe(false);
    }
  });

  it('korumali rotalarda yonlendirme YAPILIR', () => {
    for (const yol of ['/dashboard', '/exam/123/results', '/parent/dashboard',
                       '/teacher/classes']) {
      expect(girisYonlendirmesiGerekli(yol), yol).toBe(true);
    }
  });

  it('KORUMALI hedefe Navigate eden yollar muaf DEGIL', () => {
    // App.tsx: '/' ve '*' -> Navigate; '/veli-takip' -> /parent/dashboard.
    // Bunlari muaf saymak catch-all'i muaf yapardi -> kusuru genisletirdi.
    for (const yol of ['/', '/veli-takip', '/parent-new']) {
      expect(girisYonlendirmesiGerekli(yol), yol).toBe(true);
    }
  });

  it('sondaki egik cizgi ve query/hash kirletmez', () => {
    expect(girisYonlendirmesiGerekli('/eposta-dogrula/')).toBe(false);
    expect(girisYonlendirmesiGerekli('/eposta-dogrula?token=abc')).toBe(false);
    expect(girisYonlendirmesiGerekli('/eposta-dogrula#x')).toBe(false);
  });

  it('buyuk/kucuk harf bypass uretmez', () => {
    // React Router eslesmesi buyuk/kucuk harf duyarsiz; liste duyarli olsaydi
    // /LOGIN sayfasi acilir ama muaf sayilmaz -> sonsuz sicrama.
    expect(girisYonlendirmesiGerekli('/LOGIN')).toBe(false);
    expect(girisYonlendirmesiGerekli('/Eposta-Dogrula')).toBe(false);
  });

  it('bos/bozuk girdi CAGRILANI COKERTMEZ', () => {
    expect(girisYonlendirmesiGerekli('')).toBe(true);
    // @ts-expect-error kasitli: uretimde undefined gelebilir
    expect(girisYonlendirmesiGerekli(undefined)).toBe(true);
  });

  it('KORLESME GUVENCESI: liste bosalirsa test bos kume uzerinde gecmez', () => {
    expect(PUBLIC_ROUTES.length).toBeGreaterThanOrEqual(9);
  });
});
```

- [ ] **Adım 2: Testin DÜŞTÜĞÜNÜ doğrula**

```bash
cd frontend && npx vitest --run src/utils/__tests__/publicRoutes.test.ts
```
Beklenen: FAIL — `Failed to resolve import "../publicRoutes"`

- [ ] **Adım 3: Minimal implementasyonu yaz**

```ts
// frontend/src/utils/publicRoutes.ts
/**
 * 401 sonrasi /login'e SERT yonlendirme yapilMAyacak rotalar.
 *
 * NEDEN VAR (23 Agu 2026'da olculdu)
 * ----------------------------------
 * Anonim ziyaretci /eposta-dogrula'ya geldiginde hesabi DOGRULANIYOR
 * (POST verify -> 200, DB is_verified True) ama ~500ms sonra /login'e
 * firlatiliyor ve onay mesajini HIC gormuyor:
 *
 *   250ms  /eposta-dogrula  status="Dogrulaniyor..."
 *   500ms  /login           <- firlatildi
 *
 * Muafiyet kavrami zaten VARDI; listesinde yalniz '/login' yaziyordu ve
 * uc dosyaya kopyalanmisti, dorduncude (learningStyleService) unutulmustu.
 *
 * NEDEN "ProtectedRoute ICERMEYEN HER ROTA" DEGIL
 * ------------------------------------------------
 * App.tsx'te ProtectedRoute icermeyen 14 rota var ama yalnizca 9'u anlamsal
 * olarak public. '*' (catch-all), '/', '/veli-takip', '/parent-new' korumali
 * hedeflere <Navigate> ediyor. Otomatik turetme catch-all'i muaf yapardi.
 * Bu yuzden liste KURATORLU; kayma bekcisi publicRoutes.kayma.test.ts'te.
 */

export const PUBLIC_ROUTES = [
  '/login',
  '/register',
  '/veli-onay',
  '/eposta-dogrula',
  '/hesap-kurtarma',
  '/forgot-password',
  '/unauthorized',
  '/404',
  '/error',
] as const;

/**
 * ASCII kucultme KASITLI: `toLowerCase()` yerel-ayar BAGIMSIZDIR.
 * `toLocaleLowerCase()` Turkce ayarda 'I' -> 'ı' yapip yolu bozardi
 * (.claude/rules/case-convention.md Endpoint Gate ile ayni tuzak).
 */
function yolNormalize(pathname: string | null | undefined): string {
  const ham = (pathname ?? '/').split('?')[0].split('#')[0].toLowerCase();
  if (ham === '') return '/';
  return ham.length > 1 && ham.endsWith('/') ? ham.slice(0, -1) : ham;
}

/** Bu yolda 401 sonrasi /login'e sert yonlendirme yapilmali mi? */
export function girisYonlendirmesiGerekli(pathname: string | null | undefined): boolean {
  return !(PUBLIC_ROUTES as readonly string[]).includes(yolNormalize(pathname));
}
```

- [ ] **Adım 4: Testin GEÇTİĞİNİ doğrula**

```bash
cd frontend && npx vitest --run src/utils/__tests__/publicRoutes.test.ts
```
Beklenen: PASS — 7 test

- [ ] **Adım 5: Commit**

```bash
git add frontend/src/utils/publicRoutes.ts frontend/src/utils/__tests__/publicRoutes.test.ts
git commit -F <mesaj-dosyasi>
git show --stat --format="" HEAD
```

---

### Task 6: İ1 — Dört çağrı yerini yardımcıya bağla

**Files:**
- Modify: `frontend/src/utils/apiHelpers.ts`
- Modify: `frontend/src/services/apiClient.ts`
- Modify: `frontend/src/kiro/api/api-client.ts`
- Modify: `frontend/src/services/learningStyleService.ts`

> **Cerrahi kural:** yalnız 401 dalına dokunulur. Komşu kod, yorum, biçimlendirme
> **iyileştirilmez**. `import` satırı **kullanımdan SONRA** yazılır — biçimlendirici
> kullanılmayan import'u siler ve `F821`/`no-undef` üretir (bu depoda 2 kez ısırdı).

- [ ] **Adım 1: `apiHelpers.ts`**

`apiHelpers.ts:465-470` şu hâlden:

```ts
      if (response.status === 401) {
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        throw new Error('Oturum süresi doldu');
      }
```

şu hâle:

```ts
      if (response.status === 401) {
        if (girisYonlendirmesiGerekli(window.location.pathname)) {
          window.location.href = '/login';
        }
        throw new Error('Oturum süresi doldu');
      }
```

ve dosyanın import bloğuna: `import { girisYonlendirmesiGerekli } from './publicRoutes';`

- [ ] **Adım 2: `apiClient.ts`**

`apiClient.ts:75-78` şu hâlden:

```ts
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
```

şu hâle:

```ts
            if (girisYonlendirmesiGerekli(window.location.pathname)) {
              window.location.href = '/login';
            }
```

import: `import { girisYonlendirmesiGerekli } from '../utils/publicRoutes';`

- [ ] **Adım 3: `kiro/api/api-client.ts`**

`api-client.ts:145-149` şu hâlden:

```ts
function redirectToLogin(): void {
  if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}
```

şu hâle:

```ts
function redirectToLogin(): void {
  if (typeof window !== 'undefined' && girisYonlendirmesiGerekli(window.location.pathname)) {
    window.location.href = '/login';
  }
}
```

import: `import { girisYonlendirmesiGerekli } from '../../utils/publicRoutes';`

- [ ] **Adım 4: `learningStyleService.ts` — muafiyeti HİÇ YOK**

`learningStyleService.ts:28-34` şu hâlden:

```ts
  (error) => {
    if (error.response?.status === 401) {
      // setTimeout(0) allows pending promise chains to complete before redirect
      setTimeout(() => { window.location.href = '/login'; }, 0);
    }
    return Promise.reject(error);
  },
```

şu hâle:

```ts
  (error) => {
    if (error.response?.status === 401 && girisYonlendirmesiGerekli(window.location.pathname)) {
      // setTimeout(0) allows pending promise chains to complete before redirect
      setTimeout(() => { window.location.href = '/login'; }, 0);
    }
    return Promise.reject(error);
  },
```

import: `import { girisYonlendirmesiGerekli } from '../utils/publicRoutes';`

- [ ] **Adım 5: Tip ve lint kapısı**

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/utils/publicRoutes.ts src/utils/apiHelpers.ts src/services/apiClient.ts src/kiro/api/api-client.ts src/services/learningStyleService.ts
```
Beklenen: ikisi de EXIT 0.
**Kontrol kolu:** eslint bulgusu çıkarsa `git stash push -- <dosya>` ile HEAD
sürümünde de var mı ölç. Varsa devralınmıştır, `SKIP` gerekçesi budur.

- [ ] **Adım 6: Commit**

```bash
git add frontend/src/utils/apiHelpers.ts frontend/src/services/apiClient.ts \
        frontend/src/kiro/api/api-client.ts frontend/src/services/learningStyleService.ts
git commit -F <mesaj-dosyasi>
git show --stat --format="" HEAD
```

---

### Task 7: İ1 — Kayma bekçisi (üç invaryant)

**Files:**
- Test: `frontend/src/utils/__tests__/publicRoutes.kayma.test.ts`

**Neden üç invaryant:** liste küratörlü olduğu için "listeyi App.tsx'ten türet"
denklemi kurulamaz (§Dosya Yapısı notu). Kurulabilen üç invaryant var ve
**tehlikeli yön** olan ilki tam olarak yakalanıyor.

- [ ] **Adım 1: Düşen testi yaz**

```ts
// frontend/src/utils/__tests__/publicRoutes.kayma.test.ts
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { PUBLIC_ROUTES } from '../publicRoutes';

const KOK = resolve(__dirname, '../../..');
const APP = readFileSync(resolve(KOK, 'src/App.tsx'), 'utf-8');

/** <Route ...> bloklarini kabaca ayristir: her '<Route' basindan kapanisa kadar. */
function rotaBloklari(): { yol: string; korumali: boolean }[] {
  const satirlar = APP.split('\n');
  const cikti: { yol: string; korumali: boolean }[] = [];
  for (let i = 0; i < satirlar.length; i++) {
    if (!satirlar[i].includes('<Route')) continue;
    let j = i;
    const blok: string[] = [satirlar[i]];
    while (j < satirlar.length - 1 && !/\/>\s*$|<\/Route>/.test(satirlar[j])) {
      j += 1;
      blok.push(satirlar[j]);
    }
    const metin = blok.join('\n');
    const m = metin.match(/path="([^"]+)"/);
    if (m) cikti.push({ yol: m[1], korumali: metin.includes('ProtectedRoute') });
    i = j;
  }
  return cikti;
}

describe('publicRoutes <-> App.tsx kaymasi', () => {
  it('KORLESME GUVENCESI: ayristirici gercekten rota buluyor', () => {
    // Bu assert olmadan asagidaki testler BOS KUME uzerinde gecer ve hicbir sey
    // korumaz. Bu depoda tam bu sinif hata yasandi (S238 XPASS, S246 parents[2],
    // S248 yanlis bundle yolu). 23 Agu olcumu: 82 blok / 67 korumali / 14 public.
    const bloklar = rotaBloklari();
    expect(bloklar.length).toBeGreaterThanOrEqual(60);
    expect(bloklar.filter((b) => b.korumali).length).toBeGreaterThanOrEqual(50);
    expect(bloklar.filter((b) => !b.korumali).length).toBeGreaterThanOrEqual(9);
  });

  it('INVARYANT 1 (tehlikeli yon): muaf listesindeki hicbir rota ProtectedRoute DEGIL', () => {
    const korumali = new Set(rotaBloklari().filter((b) => b.korumali).map((b) => b.yol));
    const ihlal = PUBLIC_ROUTES.filter((y) => korumali.has(y));
    expect(ihlal, `Korumali rota muaf listesinde: ${ihlal.join(', ')}`).toEqual([]);
  });

  it('INVARYANT 2: muaf listesindeki her rota App.tsx"te GERCEKTEN var', () => {
    const tumYollar = new Set(rotaBloklari().map((b) => b.yol));
    const kayip = PUBLIC_ROUTES.filter((y) => !tumYollar.has(y));
    expect(kayip, `App.tsx"te olmayan rota muaf listesinde: ${kayip.join(', ')}`).toEqual([]);
  });

  it('INVARYANT 3: dort cagri yerinin DORDU de yardimciyi kullaniyor', () => {
    // Kopyala-yapistir geri gelmesin: cagri yerlerinden biri tekrar
    // `pathname !== '/login'` yazarsa bu test duser.
    const dosyalar = [
      'src/utils/apiHelpers.ts',
      'src/services/apiClient.ts',
      'src/kiro/api/api-client.ts',
      'src/services/learningStyleService.ts',
    ];
    for (const d of dosyalar) {
      const metin = readFileSync(resolve(KOK, d), 'utf-8');
      expect(metin, `${d} yardimciyi kullanmiyor`).toContain('girisYonlendirmesiGerekli');
      expect(metin, `${d} eski deseni hala tasiyor`).not.toContain("pathname !== '/login'");
    }
  });
});
```

- [ ] **Adım 2: Testin GEÇTİĞİNİ doğrula (Task 6 sonrası yeşil olmalı)**

```bash
cd frontend && npx vitest --run src/utils/__tests__/publicRoutes.kayma.test.ts
```
Beklenen: PASS — 4 test

- [ ] **Adım 3: MUTASYON — bekçi gerçekten ısırıyor mu? (≥3, hepsi ölmeli)**

Commit **sonrası** koşulur. Ankraj tekilliği (`count == 1`) doğrulanır.

| # | Mutasyon | Ölmesi beklenen |
|---|---|---|
| M1 | `PUBLIC_ROUTES`'a `'/dashboard'` ekle | INVARYANT 1 |
| M2 | `PUBLIC_ROUTES`'a `'/boyle-bir-rota-yok'` ekle | INVARYANT 2 |
| M3 | `apiHelpers.ts`'te `girisYonlendirmesiGerekli(...)` → `window.location.pathname !== '/login'` | INVARYANT 3 |
| M4 | `rotaBloklari()`'ni `[]` döndür | KÖRLEŞME GÜVENCESİ |

Her mutasyon sonrası:
```bash
cd frontend && npx vitest --run src/utils/__tests__/publicRoutes.kayma.test.ts
git checkout HEAD -- <dosya> && git status --short <dosya>   # cikti BOS olmali
```

M4 kritik: körleşme güvencesi olmadan M1/M2 boş kümede **hayatta kalırdı**.

- [ ] **Adım 4: Commit**

```bash
git add frontend/src/utils/__tests__/publicRoutes.kayma.test.ts
git commit -F <mesaj-dosyasi>
```

---

### Task 8: İ2 — Tabloyu kalıcı geri getir

**ÖN KOŞUL:** Task 2 tamamlanmış ve kök neden `dosya:satır` düzeyinde yazılı olmalı.

> **Repo kuralı:** yeni tablo → **ÖNCE ORM model**, SONRA
> `alembic revision --autogenerate`. Ham SQL `op.execute()` yalnız index/constraint/
> data migration için. Ayrıca `testing.md` #6: model import'u **relative**
> (`from .base import Base`) — absolute import iki ayrı `MetaData` üretir ve
> `Table already defined` verir.

- [ ] **Adım 1: Kırmızı testin gerçekten kırmızı olduğunu doğrula (kontrol kolu)**

```bash
cd backend && python -m pytest tests/integration/test_fsrs_schema_contract.py -v --tb=short -p no:cacheprovider 2>&1 | tail -20
```
Beklenen: 2 FAILED (`to_regclass(...) is None`)

- [ ] **Adım 2: Tabloyu göç yoluna taşı**

Task 2'nin bulgusuna göre **iki yoldan biri**:
- Squash tabloyu düşürdüyse → arşivdeki `20260801_restore_user_item_fsrs.py`'nin
  tanımı yeni bir migration'a alınır (`0003_restore_user_item_fsrs.py`), `down_revision`
  = `0002_is_active_server_default`.
- ORM modeli de yoksa → önce model (`backend/models/` altında, relative import),
  sonra `alembic revision --autogenerate -m "restore user_item_fsrs"`.

Uygulama:
```bash
cd backend && alembic upgrade head
```

- [ ] **Adım 3: Şemayı DB'den doğrula (migration SQL'i değil, DB'yi oku)**

`testing.md` #28: `CREATE TABLE IF NOT EXISTS` şema farkını **gizler**.

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A -c "
SELECT column_name||' '||data_type||' null='||is_nullable
FROM information_schema.columns WHERE table_name='user_item_fsrs' ORDER BY ordinal_position"
```

- [ ] **Adım 4: Kırmızı testlerin YEŞİLE döndüğünü doğrula**

```bash
cd backend && python -m pytest tests/integration/test_fsrs_schema_contract.py -v --tb=short -p no:cacheprovider 2>&1 | tail -10
```
Beklenen: 2 PASSED

- [ ] **Adım 5: Tüketici regresyonu — değişikliğin KAPSAMI kadar test koş**

`verification.md`: kapsamı dizin yakınlığıyla değil **grep ile** belirle.

```bash
cd backend && python -m pytest tests/unit/test_fsrs_yks_cap.py tests/integration/test_fsrs_schema_contract.py \
  tests/integration/test_alembic_autogen_guard.py -q --tb=short -p no:cacheprovider 2>&1 | tail -8
```

- [ ] **Adım 6: Commit**

```bash
git add backend/alembic/versions/ backend/models/
git commit -F <mesaj-dosyasi>
git show --stat --format="" HEAD
```

---

## Faz 3 — Canlı doğrulama (pazarlık dışı)

### Task 9: Yeniden kur ve tarayıcıda ÖLÇ

**Neden:** kod imaja girmeden "canlı" sayılmaz (#511 dersi). Birim testleri
İ1'in kabul kriterini **karşılamaz** — kabul kanıtı tarayıcı zaman çizelgesidir.

- [ ] **Adım 1: Frontend'i yeniden kur ve recreate et**

```bash
docker compose build frontend
docker compose up -d --no-deps frontend
sleep 30
curl -s -o /dev/null -w "frontend :3000 -> %{http_code}\n" --max-time 20 http://localhost:3000
```

- [ ] **Adım 2: Kodun İMAJDA olduğunu doğrula (kontrol kolu ile)**

```bash
MSYS_NO_PATHCONV=1 docker exec kiro2-frontend sh -c '
for D in girisYonlendirmesiGerekli eposta-dogrula dashboard; do
  echo "$D -> $(grep -rlo "$D" /usr/share/nginx/html 2>/dev/null | wc -l) dosya"
done'
```
> ⚠️ Arama **`/usr/share/nginx/html`** kökünde yapılır, `/assets` altında **değil**:
> `assets/` yalnız KaTeX fontlarını taşır, JS bundle `js/` altındadır. 23 Ağu'da
> bu yanlış yol "rota bundle'da YOK" diye sahte bir bulgu üretti.
> `dashboard` kontrol koludur: 0 dönerse **alet arızası** vardır, bulgu değil.

- [ ] **Adım 3: Taze token üret (Task 1 Adım 1'in aynısı)**

- [ ] **Adım 4: KABUL KANITI — zaman çizelgesini yeniden ölç**

```js
async (page) => {
  await page.context().clearCookies();
  await page.evaluate(() => { localStorage.clear(); sessionStorage.clear(); }).catch(() => {});
  const kayit = [];
  await page.goto('<TAZE LINK>', { waitUntil: 'commit' });
  for (let i = 0; i < 40; i++) {
    const d = await page.evaluate(() => ({
      yol: location.pathname,
      h1: document.querySelector('h1')?.textContent?.trim() ?? null,
      durum: document.querySelector('[role="status"]')?.textContent?.trim() ?? null,
    })).catch(() => null);
    if (d) kayit.push(`${i * 250}ms yol=${d.yol} h1=${JSON.stringify(d.h1)} durum=${JSON.stringify(d.durum)}`);
    await page.waitForTimeout(250);
  }
  const sikis = [];
  for (const s of kayit) {
    const a = s.replace(/^\d+ms\s+/, '');
    if (!sikis.length || sikis[sikis.length - 1].a !== a) sikis.push({ a, ilk: s });
  }
  return sikis.map((x) => x.ilk);
}
```

**KABUL:** 5+ saniye boyunca `yol === '/eposta-dogrula'` **kalmalı** ve `durum`
*"E-posta adresiniz doğrulandı"* olmalı. Karşılaştırma tabanı (23 Ağu, fix ÖNCESİ):
`500ms`'de `/login`.

- [ ] **Adım 5: Regresyon — korumalı rota HÂLÂ yönlendiriyor mu?**

Muafiyet fazla genişse korumalı sayfalar açıkta kalır. Anonim olarak
`http://localhost:3000/dashboard`'a git; `/login`'e **yönlenmeli**.

- [ ] **Adım 6: DB kanıtı**

```bash
MSYS_NO_PATHCONV=1 docker exec kiro2-backend python -c "
import asyncio,sys; sys.stdout.reconfigure(encoding='utf-8',errors='replace')
from sqlalchemy import text
from core.database import db_manager
async def m():
    async with db_manager.get_session() as s:
        r=(await s.execute(text(\"SELECT email,is_verified FROM users WHERE email LIKE 'i0-%' OR email LIKE 'e2e-%' ORDER BY created_at DESC LIMIT 3\"))).fetchall()
    for x in r: print(f'{x.email:45} is_verified={x.is_verified}')
asyncio.run(m())"
```

---

## Faz 4 — Kütük ve kapanış

### Task 10: İ4 — Kütüğü ölçümlerle güncelle

**Files:**
- Modify: `docs/audits/2026-08-12_25uzman/iddialar.yaml`

- [ ] **Adım 1: X11'i KOL BAZINDA işaretle**

X11'i toptan `uygulandi` yapmak **yasak** — S246'daki X10 hatasının tekrarı olur.
`kanit` alanına birebir eklenecek metin:

```
23 Agu 2026 (S249) -- KOL BAZINDA KAPANIS:
  (1) DAGITIM KAYMASI: KAPANDI. docker compose build backend + up -d (S248).
      docker exec kiro2-backend test -f /app/api/offline_sync_api.py -> VAR
      canli /openapi.json -> 'offline' gecen 4 yol (onceki olcumde 0)
      /api/v1/offline/sync-status -> 401 (onceki: 404)
  (2) DOCSTRING/KOD UYUSMAZLIGI: <Task 4 sonucu>
      NOT: (1) acildigi icin bu kod yolu artik ULASILABILIR. Onceki olcumde
      404 ile erisilemezdi; bugun kayitli.
```

`durum` alanı Task 4'ün karar kuralına göre yazılır. **İkinci kol açıksa `durum`
`dogrulandi` KALIR.**

- [ ] **Adım 2: U25'i yeniden çerçevele**

```
23 Agu 2026 (S249) -- ONCUL BAYAT:
  ankraj `alembic/versions/fa067642bdfe_force_drop_questions` -> DOSYA YOK
  ls backend/alembic/versions/*.py -> 2 (iddia 115 diyordu; gerisi versions_archive'da)
  ikisinde de downgrade() var
  Yeni soru: bu 2 migration'in geri-alinabilirligi test ediliyor mu? -> <olcum>
```

`durum` → `abartili` (öncül bayat), veya ölçüm hâlâ bir boşluk gösteriyorsa
yeni ankrajla `dogrulandi`.

- [ ] **Adım 3: X04'ü güncel sayıyla işaretle**

```
23 Agu 2026 (S249): wc -l CLAUDE.md -> 910 (iddia 883 diyordu, BUYUMUS).
Bu turda KESILMEDI: CLAUDE.md talimat dosyasi, icerik kesmek davranis degistirir.
```

- [ ] **Adım 4: X06'yı Task 3 sonucuna göre işaretle**

Tutarsızlık bulunduysa `dogrulandi` + envanter yolu; bulunmadıysa `abartili` +
*"21 implementasyon var ama celiski aranmis, bulunamamis"*.

- [ ] **Adım 5: Kütük bekçilerinin yeşil kaldığını doğrula**

```bash
cd backend && python -m pytest tests/audit/ tests/unit/test_ders_kaydi.py -q --tb=short -p no:cacheprovider 2>&1 | tail -6
```

- [ ] **Adım 6: Commit**

---

### Task 11: Kapanış — kapı, devir notu, push

- [ ] **Adım 1: Kapıyı depo kökünden koş**

```bash
cd /c/Users/husey/kiro2 && pre-commit run --files <degisen tum dosyalar>
```
`SKIP` **üç kollu ölçülmeden** kullanılmaz: (a) benim satırlarım temiz mi —
kapının sürümüyle, (b) kontrol kolu `git show HEAD:<dosya>`, (c) yaygınlık.

- [ ] **Adım 2: Backend test paketi (değişiklik kapsamı kadar)**

```bash
cd backend && python -m pytest tests/unit/test_eposta_dogrulama.py \
  tests/integration/test_eposta_dogrulama_zinciri.py \
  tests/unit/test_compose_frontend_url.py tests/integration/test_fsrs_schema_contract.py \
  -q --tb=short -p no:cacheprovider 2>&1 | tail -6
```

- [ ] **Adım 3: Frontend test paketi**

```bash
cd frontend && npx vitest --run src/utils/__tests__/ && npx tsc --noEmit
```

- [ ] **Adım 4: Devir notunu yaz**

`.claude/sessions/latest.md` başına S249 girdisi. **Zorunlu bölümler:**
Yapılanlar · **Fail Eden Testler** · Engelleyiciler · Sonraki Adımlar (maks 5) ·
Kararlar. Ayrıca: bu turda **çürütülen kendi iddialarım** ve **yakalanan alet
arızaları** ayrı başlıkta (bu depoda dürüstlük kaydı zorunlu).

- [ ] **Adım 5: Geçici dosyaları temizle ve ağacı ölç**

```bash
rm -f backend/_i0_link.py .commit_msg.tmp
MSYS_NO_PATHCONV=1 docker exec kiro2-backend sh -c 'rm -f /app/_i0_link.py'
rm -rf .playwright-mcp
git status --untracked-files=no --short   # yalniz semantic_cache.pkl kalmali
```

- [ ] **Adım 6: Push ve doğrula**

```bash
git push
git rev-list --left-right --count origin/feature/self-evolution-optimization...HEAD
```
Beklenen: `0	0`

---

## Öz-Denetim (plan ↔ spec kapsamı)

| Spec bölümü | Karşılayan task | Durum |
|---|---|---|
| §2 İ0 kök neden + karşı-olgusal | Task 1 | ✅ |
| §3 İ1 yardımcı + 4 çağrı yeri | Task 5, 6 | ✅ |
| §3 İ1 kayma kontrolü | Task 7 | ✅ (inşa→küratörlü liste sapması gerekçeli) |
| §3 İ1 canlı kabul kriteri | Task 9 Adım 4 | ✅ |
| §4 İ2 iki ölçüm sorusu | Task 2 Adım 1-4 | ✅ |
| §4 İ2 kabul kriterleri 1-4 | Task 8 | ✅ |
| §5 İ3 envanter + belirleyici soru | Task 3 | ✅ |
| §6 İ5 karar kuralı | Task 4 Adım 3 | ✅ |
| §6 İ4 kabul kriterleri | Task 10 | ✅ |
| §7 doğrulama sözleşmesi (7 madde) | Task 6 Adım 5, Task 7 Adım 3, Task 11 | ✅ |
| §8 workflow şekli | Faz 1 paralel / 2 sıralı / 3 canlı / 4 kütük | ✅ |

**Bilinen boşluk (dürüstlük kaydı):** Kayma bekçisinin üç invaryantı da
*"var olan bir muafiyet yanlıştır"* yönünü yakalar. **Yakalanmayan yön:**
App.tsx'e yeni bir public sayfa eklenir ve `PUBLIC_ROUTES`'a yazılmazsa
kullanıcılar o sayfadan sıçratılır ve **hiçbir test düşmez**. Bu anlamsal bir
karardır; yapısal olarak çivilenemez. Kapatılmadı, gizlenmedi.

## Session Handoff — 2026-08-01 (S202 · FAZ 0 devam)

**Branch:** feature/self-evolution-optimization · **Son commit:** `2e439f40a`
**TEK AKTİF REFERANS:** `docs/audits/2026-08-01_eksiklik_master.md` — **95 açık kalem**

---

## 0. PC kapanması kurtarması (oturum başı)

Çalışma ağacında **M2 mutasyonu hâlâ uygulanmış** bulundu
(`test_fsrs_schema_contract.py:132` → salt-AST). Güç kesintisi geri alımı kesti.
`git checkout HEAD --` + `git status` BOŞ ile doğrulandı, **9/9 PASS**.
4 hurda dosya (`_mutate.py`, `_probe_*.py`, `_old_contract.py`) silindi.
**Kayıp:** kapanış-saldırısı workflow'u `wf_1bcfa871-4d1` — diskte transkript yok.

> Ders: mutasyon uygulayan script geri alımı `try/finally`'ye almalı; süreç
> ortada ölürse repo **sessizce yalan söyler**.

## 1. Kapanan (S202)

### A.4 + A.4b + A.4c — RLS bekçisi ✅ `75c70dab5` · `2e439f40a`

| Kalem | Bulgu | Kanıt |
|---|---|---|
| A.4 | **Kalemin kendi ifadesi yanlıştı.** `ci.yml:281` marker filtresiz → dosya **TOPLANIYOR**; koşmama sebebi *tetiklenmeme* (dal 334 commit önde). Asıl kusur: `psycopg2-binary` CI'da yok → collection ERROR + `-x` = **tüm job** | A/B: gölgelenmiş psycopg2 → korumasız **ERROR** · korumalı **2 skipped** |
| A.4 | "163 router" hiçbir sayımdan çıkmıyor | ölçüldü: **153** dosya / **155** `APIRouter(` / **2** `get_current_tenant` |
| A.4 | Tuzak dedektörü tek fixture'sız test → DB'siz ortamda ERROR | M4: fixture yok → `OperationalError` FAILED |
| A.4b | Oran assert'i (`toplam==permissive`) 78 politika silinse yeşil | `_kalip_ihlali(1,1,79)` sentetik vakum · M1/M2 düştü |
| A.4c | `<= 1` dalı 0 ile 1'i aynı sayıyordu → kör dedektör | `_kiracilik_yargisi()` kor/tek/cok · M3 düştü |

**Yeni:** `backend/tests/test_ci_collection_guard.py` — sınıf bekçisi
(3 kontrol kolu + 633 dosya taban). `websocket` bilerek dışarıda:
`backend/websocket.py` yerel modülü gölgeliyor → yanlış pozitif olurdu.

**Doğrulama:** RED 1F/3P → GREEN 19P · RLS 6→8 test · **mutasyon 4/4**,
her geri alım repo kökünden `git status --short` BOŞ ile doğrulandı.

## 2. Sıradaki (master FAZ 0 kalanı)

`A.2` → `A.3` → `A.5` → `A.6` → `A.6b`

## 3. Bu oturumda tekrarlanan alet dersleri

1. **Saf fonksiyona ayır** — canlı DB'de üretilemeyen vakum (79 politika silme,
   `organizations=0`) ancak mantık ayrılınca sentetik girdiyle çivilenebilir.
2. **Pozitif kanıt** — `websocket` "CI'da yok" görünüyordu; yerel modül
   gölgelemesi ölçülünce yanlış fix önlendi. Dağıtım-adı ≠ modül-adı.
3. **pre-commit `ruff-format` yerel `--check`'ten farklı biçimlendirir** —
   commit reddedilirse `git add` tekrar şart (2. kez yaşandı).
4. **Mutasyondan ÖNCE commit** — commit'siz iş `git checkout HEAD --` ile uçar.

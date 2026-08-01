## Session Handoff — 2026-08-01 (S202 · FAZ 0)

**Branch:** feature/self-evolution-optimization · **Son commit:** `5bbdaa401`
**TEK AKTİF REFERANS:** `docs/audits/2026-08-01_eksiklik_master.md` — **98 açık kalem**
**Push:** `862d11509..b1a73a17a` yapıldı; sonrasındaki 2 commit yerelde

---

## 0. PC kapanması kurtarması (oturum başı)

Çalışma ağacında **M2 mutasyonu hâlâ uygulanmış** bulundu
(`test_fsrs_schema_contract.py` → salt-AST). Güç kesintisi geri alımı kesti.
`git checkout HEAD --` + `git status` BOŞ ile doğrulandı → **9/9 PASS**.
4 hurda dosya silindi. **Kayıp:** kapanış-saldırısı workflow'u `wf_1bcfa871-4d1`.

> Ders: mutasyon uygulayan script geri alımı `try/finally`'ye almalı.

## 1. Kapanan (S202) — 4 kalem

### A.4 + A.4b + A.4c — RLS bekçisi ✅ `75c70dab5` · `2e439f40a`

- **A.4 kaleminin kendi ifadesi yanlıştı**: `ci.yml:281` marker filtresiz →
  dosya **toplanıyor**; koşmama sebebi *tetiklenmeme*. Asıl kusur `psycopg2`
  CI'da yok → collection ERROR + `-x` = **tüm job** (merge-anı mayını).
- "163 router" ölçüldü → **153** dosya / **155** `APIRouter(` / **2** tenant.
- A.4b oran→taban (`_kalip_ihlali`), A.4c körlük (`_kiracilik_yargisi`).
- Yeni: `tests/test_ci_collection_guard.py` (sınıf bekçisi, 633 dosya taban).
- **Mutasyon 4/4** · A/B: gölgelenmiş psycopg2 → korumasız ERROR, korumalı SKIP.

### A.2 — Golden Flow eşiği ✅ `d5f07039d`

**Eşik ilk kez ölçüldü:** 178 test → **164 geçti / 12 düştü / 2 atlandı** (94 sn).
`ESIK=150` ulaşılabilirmiş → "kalıcı kırmızı" endişesi **çürüdü**. Gerçek kusurlar:
sabit eşik suite büyüdükçe gevşer · `hata` assert edilmiyordu · mantık YAML içi
heredoc, testi yok. Fix: `backend/scripts/gf_esik_kapisi.py` + 11 test.
Kural artık `toplam≥170 · hata==0 · atlanan≤5`. `-x` kaldırıldı.
**Değer ölçüldü:** aynı gerçek raporda eski kural **YEŞİL**, yeni kural **KIRMIZI**.
**Mutasyon 5/5** (M4 ilk denemede syntax hatası = geçersiz, tekrarlandı).

## 2. Bulunan — 12 Golden Flow CANLIDA KIRIK (`GF-K1..K3`)

`UndefinedTable` logda **74 kez**. 6 tablo yok (`to_regclass` ile doğrulandı,
trigram alias yok): `video_watch_sessions` `video_notes` `emotional_states`
`appointments` `live_sessions` `reasoning_cache`. Ayrıca 2 kod kusuru
(`LearningStyleService.update_behavioral_data` yok · `AsyncSession.query`
senkron API) + 1 timeout + 1 server-disconnect. **Fantom değil** (konteyner
modülleri 30 Tem'den beri değişmemiş). Düzeltme ayrı tur — kullanıcı kararı.

> Sayaç 95 → 97 **arttı**: ölçmeyen kapı kalem sayısını düşük gösteriyordu.

### GF-K1 kök nedeni ✅ `5bbdaa401` (GF-K1-b) — ama önce yanlış ölçtüm

`c555a10f4b93_sync_db_changes.py` `upgrade()` **145 `DROP TABLE IF EXISTS`**
taşıyor (`drop_table` grep'i boş döner — raw SQL). Sebep: `env.py:22` yalnız
`models.database` import ediyor → `Base.metadata` **123**, canlı şema **210**
→ **87 tablo yönetilmiyor**, autogenerate farkı "sil" sanıyor.

**Ölçüm düzeltmesi:** "87 tablo DROP edilir" dedim — YANLIŞ. `compare_metadata`'yı
alembic'in **hiç kullanmadığı** filtresiz konfigürasyonla koşturmuştum.
Gerçek yol: `filtresiz 86/134` · `önceki kural 0/65` · `yeni kural 0/0`.
Açık **index tarafındaydı** (`type_ == "table"` sınırı). Kural
`core/alembic_autogen_guard.py`'ye alındı (env.py import edilemez → yüklem test
edilemezdi), 9 test, **mutasyon 3/3**, `alembic current` çıkış 0.

**Yeni kalem `GF-K4`:** 87 tablonun metadata kaydı (asıl düzeltme, riskli).
GF-K1'in 6 tablosu **hâlâ yok** — geri getirme yapılmadı.

## 3. Sıradaki

Kullanıcı kararı: `GF-K1` (6 tablo restore) mi, FAZ 0 kalanı mı
(`A.3` → `A.5` → `A.6` → `A.6b`)?

## 4. Alet dersleri (bu oturumda canlı tekrarlandı)

1. **Saf fonksiyona ayır** — canlıda üretilemeyen vakum (79 politika silme,
   `organizations=0`) ancak mantık ayrılınca sentetik girdiyle çivilenebilir.
2. **Pozitif kanıt** — `websocket` "CI'da yok" görünüyordu; `backend/websocket.py`
   yerel modülü gölgeliyormuş. Dağıtım-adı ≠ modül-adı.
3. **Mutasyon syntax hatası verirse ölçüm GEÇERSİZ** — M4 tekrarlandı.
4. **pre-commit `ruff-format`/bandit/mypy yerel `--check`'ten fazlasını ister** —
   `# noqa` bandit'i susturmaz, `# nosec` gerekir; nosec'ten sonraki metni
   bandit test adı sanar.
5. **Mutasyondan ÖNCE commit** — commit'siz iş `git checkout HEAD --` ile uçar.

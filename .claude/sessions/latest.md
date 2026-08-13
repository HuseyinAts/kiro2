## Session Handoff — 2026-08-13 (RLS fix izolasyonu)
**Branch:** feature/self-evolution-optimization
**Son commit:** `68f0783a1` fix(rls): ALTER POLICY yazma yolunu da fail-closed yap (WITH CHECK)
**Uncommitted:** 3558 dosya (2021 M · 1437 D · 100 ??) — Gemini 7-11 Agu devri, KASITLI commit'siz

### Yapilanlar
- **"Commit'siz RLS fix'i" fix DEGILDI (olculdu):** `faz1_rls_20260704:49` +
  `faz1_rls2_20260704:21` `_PRED` edit'leri, DB revizyonu `51b325d6ff41` o
  migration'larin **83 ata ilerisinde** oldugu icin hicbir mevcut DB'de etkisiz.
  Kullanici karariyla GERI ALINDI (`git checkout HEAD --`; scoped status BOS,
  kirli sayac 3560->3558; revert oncesi kapsam dogrulandi: iki dosyada tek hunk).
- **Gercek acik bulundu + kapatildi** (`68f0783a1`):
  `backend/alembic/versions/ad6ba3bbe485_fix_rls_fail_closed_policy.py:120` —
  `ALTER POLICY ... USING(...)` PostgreSQL'de `WITH CHECK`'e DOKUNMAZ.
  Canli kanit (psql :5434): `SET ROLE kiro2_app` + GUC yok ->
  `INSERT ... 'ORG-FOREIGN'` GECTI (`INSERT 0 1`), sonra kendi satirini goremedi
  (superuser gordu). Yaz-serbest/oku-kapali sizinti. Fix: `alter_policy_sql()`
  cikarildi, `USING` + `WITH CHECK` birlikte yaziliyor.
- Test: `backend/tests/integration/test_rls_fail_closed_with_check.py` (5 test,
  uretim tablosuna dokunmaz — sentetik tablo + rollback). RED->GREEN kanitli
  (3 dustu -> 5/5), mutasyon 3/3 tam beklenen testleri dusurdu, geri alim sha256.
- ruff check + ruff format --check: temiz.

### Fail Eden Testler
- `backend/tests/integration/test_rls_tenant_isolation_guard.py` -> **3 failed /
  5 passed** (ONCEDEN VAR, bu oturumun degisikligi DEGIL). Bekci dogru calisiyor:
  `:192` refresh_tokens RLS tasimiyor · `:210` yanlis-org GUC'u ile 10 satir
  goruluyor · `:337` politika sayisi 0 (taban 79).

### Engelleyiciler
- **P0:** Bu DB'de RLS **hic yok** — 241 tablonun 0'inda `rowsecurity`, semada
  **0 policy**. Ama alembic 4 RLS migration'inin da atasinda. Yani stamp'lenmis
  ama DDL kosmamis VEYA downgrade edilmis (ikisi ayni izi birakir).
  `mv_safe_for_beta` matview'i VAR -> bazi migration'lar kosmus, celiski.
- 6 Agu makinesindeki 79 canli permissive policy buradan ULASILAMAZ;
  `ad6ba3bbe485` orada henuz kosmamis olabilir (9 Agu'da yazildi).

### Sonraki Adimlar (maks 5)
1. **P0:** RLS'in neden hic olmadigini coz (stamp mi, downgrade mi) —
   `alembic upgrade` DB-mutating, once karar.
2. Kalan 109 .py dosyasini (RLS + kvkk_compliance disi) tek tek siniflandir.
3. `frontend`/`scripts`/`docs`/`orchestrator` D'lerini import-referans kontrolu.
4. 21 commit'i push et (0 behind).

### Kararlar (gelecek session tekrar tartismasin)
- Kirli agaci topluca commit'lememe **kasitli** ("M=kozmetik" 4 kez yanlis cikti).
- Uygulanmis migration'i YERINDE degistirme; forward-fix migration yaz.
  `ad6ba3bbe485` artik hem taze hem mevcut kurulumu fail-closed yapiyor.
- `--no-verify` commit kullanici onayli: 3558 dosyalik agacta pre-commit'in
  stash/restore adimi gecen oturumda veri kaybina yol acmisti.
- Mutasyon kosumunda `-p no:xdist` KULLANMA: `pytest.ini` addopts `-n auto
  --dist=loadscope` ile catisir, usage error uretir, "0 test dustu" gibi gorunur.

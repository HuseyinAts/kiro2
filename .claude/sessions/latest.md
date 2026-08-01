## Session Handoff — 2026-08-01 (S202)
**Branch:** feature/self-evolution-optimization
**Son commit:** `1dbd2ebbd` docs: CLAUDE.md ders isaretcisi ders kaydina baglandi
**Uncommitted:** temiz · origin ile senkron (13 commit push edildi)

### Yapilanlar
- **PC kapanmasi kurtarmasi:** `backend/tests/integration/test_fsrs_schema_contract.py`
  calisma agacinda M2 mutasyonu uygulanmis bulundu; `git checkout HEAD --` + status BOS
  ile geri alindi, 9/9 PASS. 4 hurda dosya silindi. Kayip: workflow `wf_1bcfa871-4d1`.
- **A.4/A.4b/A.4c** `75c70dab5` `2e439f40a` — `backend/tests/test_ci_collection_guard.py`
  (YENI, korumasiz `psycopg2` = CI'da collection ERROR + `-x` ile tum job),
  `test_rls_tenant_isolation_guard.py` taban+korluk. Mutasyon 4/4.
- **A.2** `d5f07039d` — `backend/scripts/gf_esik_kapisi.py` (YENI) + 11 test.
  Esik ILK KEZ olculdu: 178 test -> 164/12/2. `.github/workflows/golden-flows.yml`
  betigi cagiriyor, `-x` kaldirildi. Mutasyon 5/5.
- **GF-K1** `2f31b0c3a` — `backend/alembic/versions/20260801_gfk1_restore_7_tablo.py`
  (7 tablo) + `tests/integration/test_gf_k1_tablo_restore.py`.
- **GF-K1-b** `5bbdaa401` — `backend/core/alembic_autogen_guard.py` (YENI) + env.py
  delege; autogenerate 65 index DROP'u uretiyordu. Mutasyon 3/3.
- **GF-K2 kismi** `232a80472` (diary 7 tablo) + `4ab90f809`
  (`services/learning_style_service.py` `update_behavioral_data` YOKTU +
  `api/learning_style.py` dict/nesne sozlesme kaymasi + onbellek sirasi).
- **Ders kaydi mekanizmasi** `e7a665cf5` — `.claude/lessons/ders_kaydi.yaml` (66 ders),
  `README.md`, `backend/tests/unit/test_ders_kaydi.py`. Mutasyon 7/7.

### Fail Eden Testler
- Golden Flow **3 kirik** (oturum basi 12 idi):
  - `gf25` coaching/signals — `null value in column "recorded_at" of relation
    "student_engagement_signals"` (NOT NULL ihlali)
  - `gf88` reports/exam/generate-pdf — **logda istisna YOK**, sessizce yutulmus
  - `gf130` fsrs/flashcards/due — `'AsyncSession' object has no attribute 'query'`
    (senkron ORM API'si async oturumda, testing.md #25 sinifi)
- Bu oturumda yazilan 8 bekci dosyasi: **68/68 PASS**

### Engelleyiciler
- `#468` CI tetiklenmiyor: dal master'dan 334+ commit onde, `on: [main,master,develop]`.
  Yazilan kapilarin CI degeri bu kapanana kadar SIFIR (yerelde calisiyorlar).

### Sonraki Adimlar (maks 5)
1. `gf130` — `AsyncSession.query` async porta cevir (kok neden net)
2. `gf25` — `recorded_at` NOT NULL: servis alani doldurmuyor
3. `gf88` — sessiz yutma; once istisnayi gorunur kil, sonra teshis
4. `GF-K5` — 67 tablo ORM'de var/DB'de yok; **urun karari** + modul-bazli triyaj
5. FAZ 0 kalani: `A.3` -> `A.5` -> `A.6` -> `A.6b`

### Kararlar (gelecek session tekrar tartismasin)
- **Tablo restore modul butunu olarak yapilir**, uc uca degil: uc kovalamak
  katmanli hatada kaybeder (7 tablo -> `goals` -> sistemik tarama 67 gosterdi).
- **DDL elle yazilmaz**, ORM'den `render_python_code` ile uretilir.
- **PG enum tipleri `DROP TABLE` ile dusmez** -> restore'da `create_type=False`.
- **Onceden var olan lint/tip borcu** `--no-verify` ile atlanmaz; olculup gerekceli
  per-file-ignore/override ile gorunur kilinir (ruff: en yakin config, mypy: KOK config).
- **Ders kaydinda `aktif` = OLCULDU.** Gocurulen 42 ders bilerek `dogrulanmadi`;
  hepsini `aktif` yapmak 23 May meta-denetimindeki %87 fantom hatasini tekrarlardi.

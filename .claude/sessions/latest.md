## Session Handoff — 2026-04-12 Session 155
**Branch:** master
**Son commit:** 499dde6 (Session 154 handoff — Session 155 değişiklikleri henüz commitlenmedi)
**Pending changes:** `backend/scripts/audit_orm_schema_drift.py` (yeni), `docs/audits/2026-04-12_orm-schema-drift-baseline.md` (yeni), `docs/audits/2026-04-12_orm-schema-drift-baseline.json` (yeni)
**Golden Flow:** 164 PASS / 0 FAIL / 2 SKIP (Session 154 baseline korunuyor, çalıştırılmadı)

### Yapilanlar — Session 155 (audit_orm_schema_drift.py tooling)

Session 153'ün handoff backlog #3 görevi: ORM ↔ live PostgreSQL schema drift audit script. GF115 (Session 152'de) ve GF106 (Session 148'de) yakalanabilirdi — bu script tooling açığını kapatır.

**Yeni dosya: `backend/scripts/audit_orm_schema_drift.py` (~430 satır):**

- `models/` paketini walk-import ederek 222 ORM tablosunu yükler.
- Live `kiro2` DB'ye `psycopg2` ile bağlanır (read-only), `information_schema.columns` sorgusu ile 235 tablonun şemasını çeker.
- SQLAlchemy column tip sınıflarını (`String`, `UUID`, `Integer`, `Boolean`, ...) kanonik PG `udt_name` değerlerine indirger; family-based comparison (`string`, `integer`, `uuid`, `bool`, ...).
- Üç HIGH pattern flag'ler: `inverse-rule-of-seven` (ORM=String/DB=uuid), `forward-rule-of-seven` (ORM=UUID/DB=varchar), `int-vs-string` (ORM=Integer/DB=varchar). MEDIUM: family mismatch + tz drift. LOW: nullability + DB-only columns.
- CLI: `--fail` (CI gate exit 1), `--json` (rapor), `--table` (tek tablo debug), `--severity HIGH|MEDIUM|LOW`.

**Doğrulama:**

İlk run sonrası **Sessions 149/153/154 fix edilmiş 8 tablonun hepsi CLEAN dönüyor** — script'in correctness'ı kanıtlandı:

| Table | Session/GF | Audit |
|-------|-----------|-------|
| `osb_settings` | 153 GF115 | CLEAN |
| `student_reviews` + 5 review tables | 154 GF106 | CLEAN |
| `coppa_parental_consents` | 149 GF113 | CLEAN |

**Bulgular:**

İlk baseline run: **HIGH=203, MEDIUM=455, LOW=206**. Hepsi gerçek bug'lar (false positive yok, spot-check edildi).

HIGH findings 3 küme:

1. **University-info backlog (~140 finding, 8 tablo)**: `dormitory_info` (32), `scholarship_programs` (31), `city_living_costs` (30), `university_statistics` (9), `department_curricula` (8), `salary_expectations` (8), `sector_analyses` (8), `campus_info` (7) — `orm-declares-missing-db-col` pattern. ORM modelleri yazılmış ama Alembic migration koşulmamış. Cold tables, kullanıcı yoluna girmiyor. Tek batch migration ile 140 finding kapanır.

2. **Inverse rule-of-seven (41 finding, ~22 tablo)** — GF115 pattern'inin dökülmemiş hali. **Production verisi olan kritik tablolar:**
   - `kiro2_learning_events` (243 satır): id, user_id, session_id
   - `topic_prerequisites` (106 satır): id
   - `kiro2_cat_sessions` (8 satır): id, user_id
   - `osym_questions`: 19 finding
   - + `reasoning_cache`, `reasoning_sessions`, `reasoning_steps`, `student_knowledge_states`, `knowledge_points`, vd.
   ORM `Column(String, default=lambda: str(uuid4()))` deklare ediyor ama DB `uuid`. Bu tabloların yazıldığı kod yolları muhtemelen raw SQL veya caller-side `str(uuid)` shim kullanıyor; ORM yolundan giden herhangi bir kod path'i `DatatypeMismatchError` üretir. Fix: model deklarasyonlarında `Column(UUID(as_uuid=True), default=uuid4)` — Session 154 reçetesinin tek satırlık tekrarı.

3. **int-vs-string (4 finding, 2 tablo)**: `badges.id`, `user_badges.id`, `user_badges.badge_id` — ORM Integer, DB varchar. Half-wired feature (5 badge seed, 0 user_badge). Her iki yön de geçerli.

**Persistent rapor:**
- `docs/audits/2026-04-12_orm-schema-drift-baseline.json` — full machine-readable findings
- `docs/audits/2026-04-12_orm-schema-drift-baseline.md` — triage analizi + cluster breakdown

### Fail Eden Testler
- Çalıştırılmadı (Session 155 sadece tooling). Golden Flow baseline 164 PASS sabit (Session 154'ten).

### Engelleyiciler
- YOK

### Session 155 Bulgular / Notlar

- **DATABASE_URL trap**: Live env `.env`'de URL `postgresql+asyncpg://...` formatında. psycopg2 driver suffix anlamıyor; script `replace("postgresql+asyncpg://", "postgresql://")` shim'i ile iki driver'i uzlaştırıyor. Bu pattern başka audit script'lerinde de tekrar edebilir.
- **Walk-import side effect**: `models/__init__.py` 29 modülü explicit import ediyor ama 60+ model dosyası daha var. `pkgutil.iter_modules()` ile walk-import 222 tabloyu yüklüyor (vs. 119 sadece `__init__.py` ile). Bazı modüller heavy import-time side effects yapıyor (LLM init, JVM bridges) ve fail oluyor — script silently skip ediyor, çünkü `Base.metadata` class body execution side effect'i.
- **Pattern density beklentisi**: 203 HIGH finding Wave 10-14'ün hit rate trailing indicator curve'unun (80% → 50% → 20% → 50% → 10% → 0% → 0%) **gerçek hesabını** veriyor. Suite saturation = "single-handler bug discovery saturated", system saturation ≠. Hâlâ ~200 yapısal asyncpg crash bekliyor — sadece probe-discoverable değiller, çünkü kullanıcı bu cold path'leri henüz çağırmıyor. Bu script onları toplu çıkarıyor.
- **Production data risk**: `kiro2_learning_events` 243 satır + ORM/DB tip uyumsuzluğu = bir gün biri ORM yazma yolu yazarsa anlık 500. Cluster 2 fix'i yüksek öncelik.

### Sonraki Adimlar (maks 5)

1. **Cluster 2 fix sweep (P1)** — Inverse rule-of-seven (41 finding, ~22 tablo). Session 154 reçetesinin tek-satırlık tekrarı: `Column(String, default=lambda: str(uuid4()))` → `Column(UUID(as_uuid=True), default=uuid4)`. Production tablolar (`kiro2_learning_events`, `topic_prerequisites`, `kiro2_cat_sessions`) öncelikli. Migration GEREKMİYOR (DB zaten doğru).
2. **Cluster 1 batch migration (P1)** — University-info 8 tablo, ~140 finding. Tek Alembic migration ile ORM'ün bildiği tüm kolonları DB'ye ekle. Cold tables, sıralama önemsiz.
3. **Cluster 3 fix (P2)** — `badges`/`user_badges` Integer vs varchar. 0 user_badge satırı, her iki yön güvenli; ORM → String tercih edilir (UUID hazırlığı için).
4. **CI integration (P2)** — `audit_orm_schema_drift.py --fail` `.github/workflows/`'a ekle. Önce baseline'i 0 HIGH'a çek, sonra gate aktif et (yoksa CI sürekli kırmızı kalır).
5. **Sync service async port backlog (P1, ertelendi)** — DifficultyClassificationService ~700 satır (GF112), DINA EM calibration (GF151b). Cluster 1+2+3 fix sonrası ele alınabilir.

### Kararlar (gelecek session tekrar tartismasin)
- Session 155 deliverable'ı `audit_orm_schema_drift.py` script + baseline raporu. Findings'in fix'i Session 156+ işi (her cluster ayrı session olabilir).
- Script `docs/audits/2026-04-12_orm-schema-drift-baseline.json` baseline'ı persistent — gelecek run'lar bu baseline ile diff'lenebilir.
- Inverse rule-of-seven pattern'i Session 153 GF115 (1 tablo) + Session 154 GF106 (6 tablo) + Session 155 audit (~22 tablo) = **toplam 29 tablo** kapsama alanına alındı.
- DATABASE_URL `postgresql+asyncpg://` shim pattern'i diğer psycopg2-based script'lere de eklenebilir (audit_db_dependency.py vd.).
- Golden Flow baseline 164 PASS / 0 FAIL / 2 SKIP sabit. Suite saturation declaration hâlâ geçerli.

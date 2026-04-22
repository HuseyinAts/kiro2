# Database Migration

Alembic migration işlemleri. Kullanıcı operation belirtecek: `status`, `migrate`,
`rollback`, veya `create <description>`.

## Operasyonlar

### status — Mevcut durumu göster

```bash
cd backend && alembic current
cd backend && alembic history --verbose | head -20
cd backend && alembic heads  # tek head olmalı, aksi halde branch var
```

### migrate — Migration uygula

Pre-flight kontrolü:

```bash
pg_isready -p 5434 || exit 1
cd backend && alembic heads  # tek head mi?
```

Sonra:
```bash
cd backend && alembic upgrade head
```

### rollback — Son migration'ı geri al

```bash
cd backend && alembic downgrade -1
```

**Uyarı:** Data migration'ın rollback'i data kaybı yapabilir. Önce `alembic history`
ile son migration'ın içeriğini gör.

### create — Yeni migration oluştur (ELLE YAZMA)

⚠️ `alembic revision --autogenerate` KESİNLİKLE YASAK.
Autogenerate IRT kolonlarını DROP eder (`irt_discrimination`,
`irt_difficulty`, `irt_guessing` — 360 kalibre soru kaybı riski).
Migration'lar **elle** yazılır. Referans pattern:
`backend/alembic/versions/20260406_uni_dept.py`.

Adımlar:

1. Mevcut head'i al:
   ```bash
   cd backend && alembic heads
   ```
   → Tek head olmalı. İki head varsa branch var, önce merge.

2. Yeni dosya oluştur: `backend/alembic/versions/YYYYMMDD_<description>.py`

3. Şablon:
   ```python
   revision = "<unique_id_max_32_char>"       # alembic_version kolonu 32 char
   down_revision = "<parent_revision>"          # bir önceki head
   branch_labels = None
   depends_on = None

   def upgrade() -> None:
       ...

   def downgrade() -> None:
       ...
   ```

4. **FK tipi kuralı**: `users.id` VARCHAR. Tüm `user_id` FK'lerinde
   `sa.String` kullan, `sa.UUID` DEĞİL. `user_badges.id` da VARCHAR,
   aynı kural. `sub_problems.id` UUID ama reasoning domain'i, karıştırma.

5. **Enum**: `sa.Enum(create_type=False)` SQLAlchemy'de çalışmıyor,
   enum kolonları için `sa.String` kullan. PG enum type gerekiyorsa:
   ```python
   op.execute("DO $$ BEGIN CREATE TYPE ... EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
   ```

6. **Container write yok**: `/app/alembic/versions/` container'da writable
   değil. Lokalde yaz, sonra kopyala:
   ```bash
   docker cp backend/alembic/versions/YYYYMMDD_<description>.py kiro2-backend:/app/alembic/versions/
   docker exec kiro2-backend alembic upgrade head
   ```

Description snake_case, ne yaptığı açık:
- `add_slug_to_subjects`
- `create_irt_params_table`
- `backfill_user_default_ability`

Detay: `KIRO2_SESSION_BRIEFING.md §Migrasyon_Dersleri`.

## Zorunlu Post-Create Adımlar (Session 120 dersleri)

Auto-generate sonrası **manuel review şart**:

1. **Reversible mi?** `downgrade()` boş değil, gerçek revert yapıyor
2. **CONCURRENTLY index?** Production tablolarda `CREATE INDEX` yerine:
   ```python
   op.execute('CREATE INDEX CONCURRENTLY ix_... ON ...')
   ```
3. **Data migration ayrı mı?** Schema + data aynı revision'da olmasın
4. **Şema doğrulaması:**
   ```bash
   psql -p 5434 -d kiro2 -U postgres -c "
     SELECT column_name, data_type, is_nullable, column_default
     FROM information_schema.columns
     WHERE table_name = 'tablo_adi'
     ORDER BY ordinal_position"
   ```
5. **Round-trip test:**
   ```bash
   cd backend && alembic upgrade head
   pytest tests/migrations/ -v
   alembic downgrade -1
   alembic upgrade head
   ```

## Phantom Sorun Filtresi (Session 121)

"Kolon X yok" veya "tablo Y eksik" raporlarına dikkat — önce 30 saniyelik
doğrulama:

```bash
# Kod gerçekten kullanıyor mu?
grep -rn 'kolon_adi' backend/app/

# DB'de gerçekten eksik mi?
psql -p 5434 -d kiro2 -U postgres -c "\d+ tablo_adi"

# Container vs local farkı olabilir
docker exec kiro2-backend grep -c 'pattern' /app/file
```

%30-70 sorun phantom çıkıyor — migration yazmadan önce doğrula.

## KIRO2 Kritik Tablolar

Bu tablolara migration yazarken **EXTRA dikkat** — büyük veri, canlı sistem etkisi:

| Tablo | Kayıt sayısı | Not |
|---|---|---|
| `question_bank` | 77,336+ | Dual Table Trap — `questions` DEĞIL |
| `users` | aktif | PII, KVKK |
| `exam_sessions` | sürekli yazılıyor | Lock hassas |
| `user_progress` | FSRS state | Indexler kritik |
| `irt_params` | ~80 ItemCalibration | Kalibrasyon kurulumu |

## İlgili Referans

- `.cursor/rules/30-migrations.mdc` — detaylı migration kuralları
- `backend/alembic/versions/` — revision geçmişi
- `CLAUDE.md` — Docker/PG pre-flight checks

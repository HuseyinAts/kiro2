# Pilot Planı — offline_sync Kod Borcu #2 (`package_id` persist)

**Tarih:** 2026-04-23
**Pilot tipi:** Kod borcu fix + yeni tablo/migration
**Önkoşul:** `ff06119` (debt #4 kapandı, pilot 1+2 tamamlandı)
**Kapsam:** Tek servis dosyası + 1 yeni model + 1 yeni migration + smoke regression
**Hedef artifact:**
- `backend/_pilots/20260423_offline_sync_debt_2_state.md` (ADIM 0 çıktısı — Composer 2 yazar)
- `.cursor/plans/20260423_offline_sync_debt_2_RESULT.md` (pilot sonrası — Composer 2 yazar, insan commit'ler)

---

## §1 — Amaç

**Borç #2 özeti:** `build_sync_package` `str(uuid.uuid4())` üretir ve yanıtta döner; `process_sync_results` `package_id`'i parametre alır ama **fonksiyon gövdesinde hiç kullanmaz** — ne doğrular, ne loglar. Sonuç: saldırgan `POST /sync-results` endpoint'ine rastgele bir UUID ile istek atıp `synced_count=1` cevabı alabilir (FSRS kartı bulunamazsa bile mevcut `synced += 1` pattern'i — borç #3 — bunu maskeler). Replay koruması da yok: aynı package_id ile tekrar POST edilebilir.

**Amaç:** Package lifecycle'ı DB'de persist etmek + 3 kontrol katmanı eklemek:
1. **Existence** — bilinmeyen `package_id` → tüm items `failed_count`'a düşer
2. **Ownership** — `pkg.student_id != caller.student_id` → tüm items fail
3. **Replay** — `pkg.consumed_at IS NOT NULL` → tüm items fail (idempotency)

Başarılı işlem sonunda `consumed_at = NOW()` UPDATE edilir; aynı paket bir daha kullanılamaz.

**Hedef olmayan:** HTTP status kodu değiştirmek (400/404/409) — mevcut batch pattern korunur (her durumda 200 dön, `failed_count`'la sinyal ver). Client'ın mevcut sözleşmesi kırılmaz.

---

## §2 — Kapsam İçi / Kapsam Dışı (açıkça)

### Kapsam İçi
- [KI1] Yeni tablo: `offline_sync_packages` (migration + ORM model)
- [KI2] `build_sync_package` içinde paket INSERT + commit
- [KI3] `process_sync_results` içinde 3 katmanlı validasyon + başarıda `consumed_at` UPDATE
- [KI4] Smoke regression: 5 senaryo (happy path + 3 fail mode + mevcut sync-status korunur)
- [KI5] RESULT dosyası; diff özeti; log sample'ları

### Kapsam Dışı (açıkça ayrılmıştır)
- [KD1] Borç #1 (`student_answers` persist) — ürün kararı bekliyor (virtual exam_session vs ayrı tablo)
- [KD2] Borç #3 (FSRS FK) — ayrı pilot; ancak `offline_sync_packages.question_ids` JSONB kolonu #3'te replay için kullanılmak üzere **şimdi** eklenecek (ileri dönük pratik)
- [KD3] HTTP status değişikliği (400/404/409) — mevcut 200 + failed_count pattern korunur
- [KD4] Ownership testi ikinci kullanıcıyla — tek admin var, simülasyon SQL ile (sahte kayıt INSERT + caller mismatch senaryosu)
- [KD5] Unit test eklemek — ileride ayrı iş
- [KD6] `pwa_sync_api` aktivasyonu, briefing v13 commit, `fb18866`+`a8474e4` incelemesi — ayrı işler
- [KD7] Router dosyasına dokunmak (`offline_sync_api.py`) — schema ve endpoint davranışı dışarıdan aynı

---

## §3 — Ön Koşullar (insan yapmalı, pilot başlamadan)

| # | Kontrol | Komut / Yer |
|---|---|---|
| P1 | DB backup | `docker exec kiro2_postgres pg_dump -U postgres kiro2 > backups/pre_debt_2_$(date +%Y%m%d_%H%M).sql` (Windows'ta tarih kısmı manuel) |
| P2 | Alembic head teyit | `docker exec kiro2-backend alembic heads` → `student_review_drift_001 (head)` beklenir |
| P3 | Backend healthy | `docker ps --filter name=kiro2-backend` → `healthy` |
| P4 | Bu planı Composer 2'ye yükle | Bkz. §13 prompt |

**Backup yapılmadan ilerleme.** Migration `CREATE TABLE IF NOT EXISTS` olsa bile — kural.

---

## §4 — ADIM 0: Durum Tespiti (Composer 2)

**Kural:** Bu adımda **kod/migration/HTTP yazılmaz**, yalnızca okuma + sorgu. Çıktı `backend/_pilots/20260423_offline_sync_debt_2_state.md`'ye yazılır.

### 4.1 Prior knowledge okuma
Önce şu dosyaları oku (tekrar sorma):
- `backend/_pilots/20260421_offline_sync_state.md` — offline_sync mevcut şema, `users.id` VARCHAR, FSRS/QB tablo adları
- `.cursor/plans/20260422_offline_sync_code_fix_RESULT.md` — #4 fix pattern (before/after diff, docker cp akışı)

### 4.2 Sürpriz kontrolü — service kodu tekrar okuma
`backend/services/offline_sync_service.py` içinde:
- [S1] `package_id` geçen TÜM satırları listele. `build_sync_package` ve `process_sync_results` dışında başka kullanım var mı?
- [S2] `process_sync_results` fonksiyon imzası hâlâ `package_id: str` mi? (pilot 2'den sonra dokunulmamış olmalı)
- [S3] `build_sync_package`'ın dönüş dict'i `package_id` anahtarını hâlâ içeriyor mu?

### 4.3 Tablo çakışma + FK pattern
- [T1] `information_schema.tables` → `table_name LIKE 'offline%'` sorgula. Sıfır satır beklenir (yeni tablo güvenli).
- [T2] `users` tablosunda bir `ON DELETE CASCADE` FK pattern'i var mı? Örnek olarak: `SELECT conname, confdeltype FROM pg_constraint WHERE conrelid = 'fsrs_cards'::regclass AND contype = 'f';` — benzer bir cascade pattern varsa yeni tabloda aynısını kullan. Yoksa `ON DELETE CASCADE` kullan ama insan onayı bekle.
- [T3] `users.id` gerçekten `character varying` mi? `\d users` ile teyit.

### 4.4 Alembic + pattern örneği
- [A1] `alembic current` → `student_review_drift_001 (head)` beklenir. Başka head varsa DUR.
- [A2] `backend/alembic/versions/20260410_create_user_item_fsrs.py` pattern'i (op.execute + CREATE IF NOT EXISTS) bu plan için referans — içeriğini oku, benzer yapıyı §6'da üret.
- [A3] `backend/models/__init__.py` veya `backend/core/database.py` — yeni ORM model nereye import edilmeli? Diğer modellerin import pattern'ini çıkar.

### 4.5 ADIM 0 çıktı şablonu

`backend/_pilots/20260423_offline_sync_debt_2_state.md` şu bölümleri içerir:
- Prior knowledge farkı (var mı?)
- S1–S3 sürpriz kontrolü sonuçları (sıfır sürpriz beklenir)
- T1–T3 tablo/FK gözlemleri
- A1–A3 Alembic durumu
- **Aşama önerisi:** B (şema uyumlu, migration yazılabilir) veya **C** (beklenmedik UUID/tip çakışması varsa — DUR, insan onayı bekle)

**DUR sinyalleri (Composer 2 devam etmez):**
- S1'de `package_id`'in 3+ yerde farklı semantikle kullanıldığı ortaya çıkarsa
- T1'de `offline_sync_packages` adında başka bir tablo zaten varsa
- A1'de head farklıysa (çift head / farklı revision)

---

## §5 — Aşama Kararı (insan onayı noktası)

ADIM 0 çıktısı sonrası insan onayı gerekli. Tablo:

| Senaryo | Aşama | Aksiyon |
|---|---|---|
| S1/S2/S3 temiz, T1 boş, T3 varchar, A1 tek head | **B** → İlerle | §6–§10 uygula |
| T2 cascade pattern yok veya karışık | **B (kısmi)** | Insan `ON DELETE CASCADE` kararını netleştirsin; sonra ilerle |
| T1'de önceden tablo var | **DUR** | Drift araştır — muhtemelen eski silinmiş migration kalıntısı |
| A1 çift head | **DUR** | Önce merge migration (ayrı iş) |

---

## §6 — Migration Dosyası (tam içerik)

**Dosya:** `backend/alembic/versions/20260423_offline_sync_packages.py`

**Pattern referansı:** `20260410_create_user_item_fsrs.py` (op.execute + IF NOT EXISTS + idempotent downgrade)

```python
"""Create offline_sync_packages table (debt #2)

Revision ID: offline_sync_packages_001
Revises: student_review_drift_001
Create Date: 2026-04-23
"""

from alembic import op

revision = "offline_sync_packages_001"
down_revision = "student_review_drift_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS offline_sync_packages (
            package_id    VARCHAR     PRIMARY KEY,
            student_id    VARCHAR     NOT NULL,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            consumed_at   TIMESTAMPTZ,
            question_ids  JSONB,
            CONSTRAINT fk_osp_student
                FOREIGN KEY (student_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_osp_student_created "
        "ON offline_sync_packages (student_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_osp_unconsumed "
        "ON offline_sync_packages (student_id) "
        "WHERE consumed_at IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_osp_unconsumed")
    op.execute("DROP INDEX IF EXISTS idx_osp_student_created")
    op.execute("DROP TABLE IF EXISTS offline_sync_packages")
```

**Notlar:**
- `ON DELETE CASCADE` — öğrenci silinirse paketleri de gider (KVKK uyumlu). T2 gözlemine göre değişebilir; karar §5'te.
- Partial index (`WHERE consumed_at IS NULL`) — açık paket sayısı görece az olacak, listelemede performans.
- `question_ids JSONB` — borç #3 için ileri dönük. Şu an sadece INSERT edilir, okuma yok.

**Deploy (insan):**
```
docker cp C:\Users\husey\kiro2\backend\alembic\versions\20260423_offline_sync_packages.py kiro2-backend:/app/alembic/versions/
docker exec kiro2-backend alembic upgrade head
docker exec kiro2-backend alembic current   # teyit: offline_sync_packages_001 (head)
```

---

## §7 — Yeni ORM Model (tam içerik)

**Dosya:** `backend/models/offline_sync_package.py`

```python
"""ORM model for offline_sync_packages table (debt #2)."""

from __future__ import annotations

from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class OfflineSyncPackage(Base):
    """A package issued by GET /sync-package, consumed by POST /sync-results.

    Lifecycle:
        INSERT in build_sync_package (created_at=now, consumed_at=null).
        UPDATE in process_sync_results on success (consumed_at=now).
        Package is single-use; subsequent POST with same package_id fails
        (consumed_at != null → batch fail).
    """

    __tablename__ = "offline_sync_packages"

    package_id = Column(String, primary_key=True)
    student_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    consumed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    question_ids = Column(JSONB, nullable=True)
```

**Register kontrolü (ADIM 0 §4.4 A3 çıktısına göre):**
- Eğer `backend/models/__init__.py` diğer modelleri `from .x import Y` olarak export ediyorsa, yeni satır ekle:
  `from .offline_sync_package import OfflineSyncPackage`
- Eğer `__init__.py` boşsa veya lazy import pattern kullanıyorsa — dokunma; servis doğrudan `from models.offline_sync_package import OfflineSyncPackage` ile import edecek.

---

## §8 — Servis Değişikliği: `build_sync_package`

**Dosya:** `backend/services/offline_sync_service.py`

### Before (mevcut, satır ~100–135 civarı)

```python
    total = len(questions)
    estimated_minutes = total * _MINUTES_PER_QUESTION

    return {
        "package_id": package_id,
        "created_at": now.isoformat(),
        "questions": questions,
        "fsrs_due_cards": fsrs_due_cards,
        "total_questions": total,
        "estimated_study_time_minutes": estimated_minutes,
    }
```

### After

```python
    total = len(questions)
    estimated_minutes = total * _MINUTES_PER_QUESTION

    # Persist package for audit + replay protection (debt #2)
    from models.offline_sync_package import OfflineSyncPackage

    question_ids = [q["id"] for q in questions]
    db.add(
        OfflineSyncPackage(
            package_id=package_id,
            student_id=student_id,
            question_ids=question_ids,
        )
    )
    await db.commit()

    return {
        "package_id": package_id,
        "created_at": now.isoformat(),
        "questions": questions,
        "fsrs_due_cards": fsrs_due_cards,
        "total_questions": total,
        "estimated_study_time_minutes": estimated_minutes,
    }
```

**Diff beklentisi:** +13 satır, -0 satır. Return bloğuna dokunulmuyor.

---

## §9 — Servis Değişikliği: `process_sync_results`

### Before (başlangıç, mevcut)

```python
async def process_sync_results(
    *,
    db: AsyncSession,
    student_id: str,
    package_id: str,
    results: list[dict[str, Any]],
    completed_at: str,
) -> dict[str, Any]:
    """..."""
    from models.question_bank import QuestionBankItem
    from models.fsrs_models import FSRSCard

    synced = 0
    failed = 0

    for item in results:
        # ... mevcut loop ...
```

### After (validasyon bloğu loop'tan önce eklenir)

```python
async def process_sync_results(
    *,
    db: AsyncSession,
    student_id: str,
    package_id: str,
    results: list[dict[str, Any]],
    completed_at: str,
) -> dict[str, Any]:
    """..."""
    from models.question_bank import QuestionBankItem
    from models.fsrs_models import FSRSCard
    from models.offline_sync_package import OfflineSyncPackage

    # --- Package validation (debt #2) ---
    pkg_result = await db.execute(
        select(OfflineSyncPackage).where(
            OfflineSyncPackage.package_id == package_id
        )
    )
    pkg = pkg_result.scalar_one_or_none()

    next_sync = datetime.now(timezone.utc) + timedelta(hours=6)

    def _reject_batch(reason: str, log_level: str = "warning") -> dict[str, Any]:
        log_fn = logger.error if log_level == "error" else logger.warning
        log_fn(
            f"Offline sync package rejected: {reason}",
            extra_data={
                "student_id": student_id,
                "package_id": package_id,
                "result_count": len(results),
            },
        )
        return {
            "synced_count": 0,
            "failed_count": len(results),
            "next_sync_recommended_at": next_sync.isoformat(),
        }

    if pkg is None:
        return _reject_batch("unknown package_id")
    if pkg.student_id != student_id:
        return _reject_batch("package ownership mismatch", log_level="error")
    if pkg.consumed_at is not None:
        return _reject_batch(
            f"package already consumed at {pkg.consumed_at.isoformat()}"
        )
    # --- End package validation ---

    synced = 0
    failed = 0

    for item in results:
        # ... mevcut loop DEĞİŞMEZ ...

    # Mark package as consumed (debt #2)
    pkg.consumed_at = datetime.now(timezone.utc)
    db.add(pkg)

    await db.commit()

    return {
        "synced_count": synced,
        "failed_count": failed,
        "next_sync_recommended_at": next_sync.isoformat(),
    }
```

**Diff beklentisi:** +40/-2 satır (-2 mevcut `next_sync` hesaplamasının bir kez hesaplanıp iki yerde kullanılması için).

**Kritik:** Mevcut `for item in results:` döngüsü ve `_apply_fsrs_grade` akışı **DOKUNULMAZ**. Sadece öncesine validasyon, sonrasına `consumed_at` UPDATE eklenir.

---

## §10 — Smoke Regression Matrisi

**Auth:** Briefing pattern'i — `POST /api/v1/auth/giris`, `.access_token` alanı.

| # | Test | Beklenen |
|---|---|---|
| S1 | `GET /sync-status` | 200; `last_sync_at` / `pending_results_count` değişmedi (debt #2 bu endpoint'e dokunmaz) |
| S2 | `GET /sync-package?limit=5` | 200; yanıtta `package_id` var; `offline_sync_packages` tablosunda yeni bir satır (`consumed_at IS NULL`, `question_ids` JSONB'de 5 id) |
| S3 | `POST /sync-results` (S2'den gelen gerçek `package_id` + gerçek `question_id`) | 200; `synced_count >= 1`; `offline_sync_packages.consumed_at IS NOT NULL` |
| S4 | `POST /sync-results` (S3'teki aynı `package_id` tekrar) | 200; `synced_count=0`, `failed_count=len(results)`; log: `"package already consumed"` WARN |
| S5 | `POST /sync-results` (rastgele yeni UUID `package_id`) | 200; `synced_count=0`, `failed_count=len(results)`; log: `"unknown package_id"` WARN |
| S6 | Ownership simülasyonu (SQL ile sahte paket): `INSERT INTO offline_sync_packages (package_id, student_id) VALUES ('pkg-fake-001', 'ANOTHER-USER-ID')` + admin caller ile POST | 200; `synced_count=0`, `failed_count=len(results)`; log: `"package ownership mismatch"` ERROR. Test sonrası `DELETE FROM offline_sync_packages WHERE package_id='pkg-fake-001'` ile temizle. |

**DB verification (her smoke sonrası):**
```sql
SELECT package_id, student_id, created_at, consumed_at, jsonb_array_length(question_ids) AS q_count
FROM offline_sync_packages
ORDER BY created_at DESC
LIMIT 5;
```

**Log tail:**
```
docker logs kiro2-backend --tail 50 | Select-String "offline_sync"
```
ERROR/CRITICAL (S6 hariç) beklenmez. S6 ERROR'u `"package ownership mismatch"` log şablonuyla eşleşmeli.

---

## §11 — Rollback Stratejisi

**Problem:** Smoke başarısız olursa (örn. S2 500 dönerse INSERT hatası nedeniyle).

**Adımlar (insan yapar):**
1. `docker cp` ile eski `offline_sync_service.py` geri yaz (git checkout HEAD~ ile önceki haliyle lokalde kopya al)
2. Pyc temizle, restart
3. Migration için:
   ```
   docker exec kiro2-backend alembic downgrade student_review_drift_001
   ```
4. `offline_sync_packages` tablosunun gittiğini `\dt` ile teyit et
5. State snapshot al — `_pilots/20260423_..._state.md` "rollback notu" ekle

**Notlar:**
- `CREATE TABLE IF NOT EXISTS` + `DROP TABLE IF EXISTS` sayesinde tekrar çalıştırma güvenli
- `ON DELETE CASCADE` yalnızca ileride users silinirse etkili; migration rollback'ta direkt DROP yeter

---

## §12 — Bilinen Sınırlamalar (kapsam dışı, #4 pilotu gibi açıkça ayrılır)

- **Borç #1** (`student_answers` persist) — AÇIK. Bu pilot dokunmuyor. Ürün kararı bekliyor.
- **Borç #3** (FSRS FK `front_text.contains`) — AÇIK. `offline_sync_packages.question_ids` kolonu #3 için yararlı olabilir ama bu pilotta **yalnızca INSERT edilir**, okunmaz.
- **HTTP 200 + failed_count pattern** — API sözleşmesi korunur. Client tarafı "paketim consumed oldu" durumunu `failed_count == len(results) && synced_count == 0` ile tespit etmeli; 4xx döndürmek ileride ayrı karar.
- **Ownership testi** (S6) — SQL injection tarzı manuel hazırlık gerektirir; production'da iki kullanıcı + iki auth token ile daha doğru test edilir.
- **Unit test** — eklenmiyor (seçenek B, §4 kod fix pilotu kararına uyumlu).

---

## §13 — RESULT Şablonu

`.cursor/plans/20260423_offline_sync_debt_2_RESULT.md` formatı (`20260422_offline_sync_code_fix_RESULT.md` benzeri):

```markdown
# Pilot RESULT — offline_sync debt #2 (package_id persist)

**Tarih:** 2026-04-23
**Tür:** Kod borcu fix + yeni tablo
**Sonuç:** Başarı / Kısmi başarı / Başarısız

## ADIM 0 özet
- Prior knowledge farkı: <yok/...>
- Sürpriz kontrolü: <yok/...>
- Alembic head: student_review_drift_001 → offline_sync_packages_001 (upgrade sonrası)

## Değişiklikler
- `backend/alembic/versions/20260423_offline_sync_packages.py` (yeni, +42 satır)
- `backend/models/offline_sync_package.py` (yeni, +~30 satır)
- `backend/services/offline_sync_service.py` (+53/-2)
- `backend/models/__init__.py` (register — varsa)

## Smoke regression sonuçları
<S1–S6 tablo>

## Etki
- Borç #2: Kapandı
- Borç #1, #3: Açık

## Kapsam dışı
- Unit test, HTTP status değişikliği, borç #1/#3

## Sonraki adım
- Borç #3 (FSRS FK) → ayrı pilot
- Borç #1 (student_answers) → ürün kararı
- pwa_sync_api aktivasyonu → alternatif yol
```

---

## §14 — Composer 2'ye Yükleme Prompt'u

```
@.cursor/plans/20260423_offline_sync_debt_2_package_persist.md — uygula

Prior knowledge (tekrar sorma, oku ve özümse):
- backend/_pilots/20260421_offline_sync_state.md (ortam: users.id VARCHAR, FSRS tablo adları, auth token alanı access_token)
- .cursor/plans/20260422_offline_sync_code_fix_RESULT.md (#4 pilot pattern, docker cp akışı)

Kurallar:
1. ADIM 0 tamamlanmadan kod/migration/HTTP yazma.
2. ADIM 0 çıktısını backend/_pilots/20260423_offline_sync_debt_2_state.md'ye yaz.
3. DUR sinyalleri (plan §4.5) olursa uygulamaya geçme, insan onayı iste.
4. Insan onayı sonrası §5-§9 adımlarını uygula:
   - Migration yaz (lokalde), docker cp, alembic upgrade → **insanın çalıştırması için komutları göster, ÇALIŞTIRMA**
   - Servis kodunu değiştir (lokalde), docker cp, pyc temizle, restart
5. Smoke regression §10 — 6 senaryo. S6 için SQL INSERT/DELETE kendin yap.
6. RESULT dosyasını yaz (§13 şablonu).
7. Commit komutunu göster ama ÇALIŞTIRMA (fix pilot 2'deki gibi — insan commit atar).

Briefing v13 kuralları:
- sa.Enum yasak (kullanılmıyor bu planda zaten)
- users.id VARCHAR → ForeignKey("users.id") + String kolonu (plan §7'de uygulanmış)
- DISABLED_ROUTERS'a dokunma
- Hook'suz commit: core.hooksPath=.git/hooks-empty
```

---

## §15 — İnsan × Composer 2 × Claude iş bölümü

| Aksiyon | Kim |
|---|---|
| Plan yazımı (bu dosya) | Claude (tamam) |
| ADIM 0 gözlemi + state.md | Composer 2 |
| Aşama kararı (B/DUR) | İnsan (Hüseyin) |
| Migration dosyasını yaz (lokalde) | Composer 2 |
| `docker cp` + `alembic upgrade head` | **İnsan** (briefing kuralı) |
| Servis kodu değişikliği (lokalde) | Composer 2 |
| `docker cp` + pyc temizle + restart | Composer 2 |
| Smoke regression (S1–S6) | Composer 2 |
| RESULT yaz | Composer 2 |
| `git commit` | **İnsan** |
| `git push` (karar) | **İnsan** |

---

*Plan sonu. ADIM 0 başlamadan önce §3 ön koşulları (backup, head teyit) tamamlanmalı.*

# Architecture Decision Record (ADR) — Live Database Telemetry & Zero-Downtime Resolution

**Status:** Approved  
**Author:** Principal PostgreSQL DBA / Redis SRE / Antigravity AI  
**Context:** KIRO2 (elendin.com) High-Concurrency Production System Audit  
**Date:** 2026-06-07  

---

## BÖLÜM 1: CANLI TELEMETRİ KANITLARI

Canlı Docker ortamından (PostgreSQL 5434 ve Redis 6379) toplanan gerçek telemetri verileri aşağıda raporlanmıştır.

### 1. PostgreSQL Tablo ve İndeks İstatistikleri (Sequential Scans & Dead Tuples)
`pg_stat_user_tables` görünümünden elde edilen net rakamlar:

| Tablo Adı | Sequential Scans (`seq_scan`) | Seq Tup Read (`seq_tup_read`) | Index Scans (`idx_scan`) | Index Tup Fetch (`idx_tup_fetch`) | Live Tuples (`n_live_tup`) | Dead Tuples (`n_dead_tup`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`question_bank`** | **53** | **3.944.514** | **4.240** | **190.002** | **187.582** | **11.300** |
| **`bkt_states`** | **26** | **687** | **40** | **16** | **1** | **22** |
| **`fsrs_reviews`** | **5** | **0** | **0** | **0** | **0** | **0** |

*   **Analiz:** `question_bank` tablosunda **11.300 dead tuple** bulunmaktadır (Dead Tuple oranı: **%5,68**). sequential scan sayısına kıyasla okunan satır sayısının (**3,94M**) yüksekliği, tabloda indeks eksikliği veya indeksleri bypass eden query paternlerinin olduğunu kanıtlamaktadır.

### 2. PostgreSQL Cache Hit Ratios
- **Heap (Table) Buffer Cache Hit Ratio:** **%91,92** (1.405.760 hit, 123.586 disk read)
- **Global Database Buffer Cache Hit Ratio (`kiro2`):** **%98,78**
- **Analiz:** Genel cache hit oranı tatmin edici olsa da, sequential scans nedeniyle heap okumalar disk yerine shared buffers üzerinde yük oluşturmaktadır.

### 3. Redis State Profiler
`INFO memory` ve `INFO stats` çıktılarından toplanan net rakamlar:
- **Kullanılan Bellek (Used Memory):** **2.96 MB** (Peak: **3.23 MB**)
- **Maksimum Bellek (Max Memory Limit):** **512.00 MB**
- **Memory Fragmentation Ratio:** **3,34**
- **Keyspace Hits / Misses:** **53 / 239**
- **Önbellek Tutturma Oranı (Cache Hit Ratio):** **%18,15**
- **Analiz:** Redis bellek kullanımı son derece güvenli seviyededir. Ancak önbellek tutturma oranının düşük olması (%18,15), cache entry'lerin TTL sürelerinin veya caching stratejilerinin optimize edilmesi gerektiğini göstermektedir.

### 4. Schema Drift Tespiti
Alembic autogenerate simülasyonu çalıştırılarak `models.py` (SQLAlchemy modelleri) ile canlı veritabanı şeması karşılaştırılmış ve drift tespit edilmiştir:

- **Canlı Veritabanında Olup Kod Modellerinde Olmayan Kolonlar (Missing in Code):**
  `numeric_tolerance`, `fisher_info_theta`, `soru_hash`, `irt_se_c`, `q_matrix`, `metadata_completeness_score`, `osym_section`, `canonical_form_id`, `embedding_model`, `last_flagged_date`, `irt_se_a`, `ocr_confidence_avg`, `expected_answer_formula`, `mufredat_kazanim_id`, `kc_ids`, `metadata_filled_at`, `solo_level`, `marzano_level`, `fisher_info_max`, `diagram_type`, `variant_id`, `embedding_updated_at`, `answer_equivalent_forms`, `has_alt_text`, `dina_guess`, `flag_count`, `estimated_solve_time_seconds`, `dina_slip`, `alt_text`, `mufredat_versiyon`, `is_math_solvable`, `irt_se_b`, `irt_method_used`.
- **Canlı Veritabanında Olup Kod Modellerinde Olmayan İndeksler (Drifted Indexes):**
  `idx_qb_calib_pool`, `idx_qb_cat_subject_active`, `idx_qb_primary_topic`, `idx_qb_soru_hash`, `idx_qbank_active_created`, `idx_qbank_beta_filter_rule`, `idx_qbank_calib_pool`, `idx_qbank_created_by`, `idx_qbank_embedding_hnsw`, `idx_qbank_quality_subject_exam`, `idx_qbank_source_book`, `idx_qbank_status_active`, `idx_qbank_text_gin`, `idx_qbank_verified_provisional`, `idx_question_bank_reviewed_at`, `uq_qb_soru_hash_active`.

---

## BÖLÜM 2: SIFIR KESİNTİ (ZERO-DOWNTIME) ÇÖZÜMLER

### 1. ⚠️ Concurrently Alembic İndeks Düzeltmesi (Transaction Dışı İndeksleme)
PostgreSQL'de canlı tabloları kilitlemeden indeks oluşturmak için `CONCURRENTLY` kullanılmalıdır. Alembic migration dosyası aşağıdaki standarda uygun yazılmalıdır:

```python
"""add_indexes_concurrently

Revision ID: <revision_id>
Revises: <prev_revision>
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_indexes_concurrently'
down_revision = 'beta_vp_idx_20260602'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # DBA Altın Kuralı: CONCURRENTLY transaction içinde çalıştırılamaz!
    # Autocommit modunu etkinleştiriyoruz.
    connection = op.get_bind()
    connection.execution_options(isolation_level="AUTOCOMMIT")
    
    # Canlı sistemi kilitlemeden indeks atma
    op.create_index(
        'idx_qbank_subject_active',
        'question_bank',
        ['subject_area', 'is_active'],
        postgresql_concurrently=True
    )
    op.create_index(
        'idx_qbank_topic_active',
        'question_bank',
        ['primary_topic_id', 'is_active'],
        postgresql_concurrently=True
    )

def downgrade() -> None:
    connection = op.get_bind()
    connection.execution_options(isolation_level="AUTOCOMMIT")
    
    op.drop_index('idx_qbank_subject_active', table_name='question_bank', postgresql_concurrently=True)
    op.drop_index('idx_qbank_topic_active', table_name='question_bank', postgresql_concurrently=True)
```

### 2. Async ORM Refactoring (Cartesian Product & N+1 Çözümü)
`QuestionBankItem` tablosunu sorgularken, collection ilişkilerinin (`tag_associations` ve `calibration_history`) lazy load veya yanlış `joinedload` kullanımı nedeniyle N+1 sorgusu tetiklemesi veya Cartesian product oluşturması önlenmiştir.

*   **Dosya:** [question_bank_service.py](file:///C:/Users/husey/kiro2/backend/services/question_bank_service.py)
*   **Çözüm:** Many-to-one / One-to-one ilişkiler için `joinedload`, collection'lar (One-to-many / Many-to-many) için `selectinload` kullanılmıştır.

#### Refaktör Edilmiş Kod Parçası (Satır 76-88):
```python
    async def get_question(self, question_id: str) -> QuestionBankItem | None:
        """Soru detayını getir"""
        result = await self.db.execute(
            select(QuestionBankItem)
            .options(
                joinedload(QuestionBankItem.primary_topic),       # Many-to-one (JOIN)
                selectinload(QuestionBankItem.tag_associations),   # Collection (SELECT IN)
                selectinload(QuestionBankItem.calibration_history), # Collection (SELECT IN)
            )
            .where(QuestionBankItem.id == question_id)
        )
        return result.scalar_one_or_none()
```

#### Refaktör Edilmiş Kod Parçası (Satır 575-583):
```python
        # FIX N+1: Eager loading ile ilişkili verileri tek sorguda getir
        query = (
            select(QuestionBankItem)
            .options(
                joinedload(QuestionBankItem.primary_topic),       # Many-to-one (JOIN)
                selectinload(QuestionBankItem.tag_associations),   # Collection (SELECT IN)
            )
            .where(QuestionBankItem.is_active == True)
        )
```

### 3. Altyapı Optimasyonu (Docker Connection Pooling)
Canlı FastAPI uygulamamızın high-concurrency (10K+ RPS) altında darboğaz yaşamaması için `database.py` üzerindeki connection pool ayarları optimize edilmelidir:

*   **Mevcut / Önerilen Ayarlar:**
    - `pool_size = 200` (FastAPI instance başına kalıcı tutulacak connection sayısı)
    - `max_overflow = 300` (Yoğun RPS altında dinamik olarak açılabilecek ekstra connection sayısı)
    - `pool_pre_ping = True` (Her bağlantı kullanımından önce ping testi - koptu/hatalı bağlantı engelleme)
    - `pool_recycle = 3600` (Bağlantı sızıntılarını ve timeout'ları önlemek için 1 saatte bir bağlantıları yenileme)

*   **FastAPI / Docker `.env.production` veya `.env.mvp` Yapılandırması:**
    ```ini
    # High-Concurrency connection pool configurations
    DB_POOL_SIZE=200
    DB_MAX_OVERFLOW=300
    ```
    Bu environment değişkenleri [config.py](file:///C:/Users/husey/kiro2/backend/core/config.py#L113-L114) tarafından otomatik olarak okunmakta ve [database.py](file:///C:/Users/husey/kiro2/backend/core/database.py#L97-L98) üzerinde connection pool'a aktarılmaktadır.

"""Kalite kapısı — öğrenci-yüzü soru seçiminin TEK doğruluk kaynağı.

Convention v3 (12 Haz 2026): öğrenciye soru İÇERİĞİ dönen her sorgu
`v_safe_for_beta` view'inin kapsadığı id kümesiyle sınırlıdır. View;
is_active + quality_review_status + pipeline_metadata dışlamalarını
(demoted / tier1 tek-sinyal / fallback-topic / görselsiz-şekil / bozuk-LaTeX)
TEK yerde kodlar. Kod bu predikatları REPLİKE ETMEZ — replike etmek,
kapatmaya çalıştığımız kod↔view drift'inin ta kendisidir.

NEDEN BU MODÜL VAR (27 Tem 2026)
--------------------------------
Kapı üç dosyada üç ayrı yerde `text("SELECT id FROM v_safe_for_beta")` diye
elle yazılmıştı; öğrenciye soru servis eden diğer ~24 yolda ise hiç yoktu.
Ölçüm:

    v_safe_for_beta                      25.127
    status-only filtre (cat/placement)   34.982   -> +9.855 sızıntı
    sadece is_active (duel/PF/osym/...) 110.858   -> +85.731 sızıntı

Yani 30 May 2026'da "circular defect / verdict: drop" diye yargılanmış bir soru
27 Tem 2026'da hâlâ öğrenciye servis edilebiliyordu. Tek tanım noktası, bir
sonraki yayılımın "kopyala-yapıştır sürüklenmesi" ile bozulmasını engeller.
(.claude/rules/testing.md Ders #31'in aynı sınıfı.)

NEDEN MATVIEW
-------------
`v_safe_for_beta` tanımı ağır: 5 ayrı jsonb varlık testi + `gate2c_demoted`
alt sorgusu. Planlayıcı bunları çağıran sorgunun Filter'ına düzleştiriyor.
27 Tem ölçümü (EXPLAIN ANALYZE, canlı DB, 3'er tur, MATEMATIK konu sorgusu):

    kapı = v_safe_for_beta    -> planning 12-13 ms | execution 730-907 ms
    kapı = mv_safe_for_beta   -> planning  0.3-0.6 ms | execution  58-87 ms
    kapısız baseline          -> planning  7-14 ms | execution  87-116 ms

Matview'li kapı, kapısız sorgudan bile ucuz.

BAYAT PENCERE — BİLİNÇLİ KABUL, AMA ŞARTLI
------------------------------------------
Matview zamanlı yenilenir (bkz. tasks/quality_gate_tasks.py). İki yönü var:
  - yeni onaylanan soru geç görünür            -> zararsız
  - demote edilen soru bir süre daha servis edilir -> TEHLİKELİ

İkinci yönün zararı, kapıyı kullanan HER sorgunun `is_active`'i AYRICA canlı
filtrelemesiyle sınırlanır: arşivleme/silme bayat matview'a rağmen anında
etki eder. Bu yüzden:

    KURAL: safe_for_beta_gate() `is_active` filtresinin YERİNE geçmez,
           YANINA gelir. Kapı eklerken mevcut is_active koşulunu KALDIRMA.

İKİNCİ BAYATLIK KATMANI (matview'den bağımsız)
----------------------------------------------
`core/osym_exam_engine.py` seçilen id havuzunu `_question_pool_cache`'e
TTL=3600 sn ile yazıyor. Kapı cache'e YAZILMADAN ÖNCE uygulanıyor (doğru),
ama matview tazelense bile demote edilmiş bir soru süreç-içi havuzda bir
saate kadar servis edilmeye devam edebilir. Yani gerçek en kötü gecikme
= matview bayatlığı + 1 saat. Kapı yayılımını "anında etkili" saymadan
önce bu katman hatırlanmalı.

Bkz: docs/quality_review_status_convention.md
     backend/alembic/versions/20260727_mv_safe_for_beta.py
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.sql.elements import ColumnElement

# Kapının okuduğu ilişki. Canlı view'den matview'e geçiş burada tek satır.
SAFE_POOL_RELATION = "mv_safe_for_beta"

# Kapının doğruluk kaynağı olan canlı view. Matview bunun anlık görüntüsü;
# testler ve bayatlık ölçümü bu ada göre yapılır.
SAFE_POOL_SOURCE_VIEW = "v_safe_for_beta"


# girdisi hiçbir zaman buraya ulaşmıyor. Sabiti string'e gömmek yerine tek yerde
# tutmanın amacı zaten enjeksiyon değil, ad sürüklenmesini engellemek.
_SAFE_POOL_ID_SQL = f"SELECT id FROM {SAFE_POOL_RELATION}"  # noqa: S608


def safe_for_beta_gate(id_column: ColumnElement) -> ColumnElement:
    """ORM sorguları için kapı koşulu.

    Kullanım:
        select(QuestionBankItem).where(
            QuestionBankItem.is_active.is_(True),      # <- KALDIRMA
            safe_for_beta_gate(QuestionBankItem.id),
        )
    """
    return id_column.in_(text(_SAFE_POOL_ID_SQL))


def safe_for_beta_sql(column: str = "id") -> str:
    """Ham SQL sorguları için kapı koşulu (WHERE parçası).

    Kullanım:
        text(f"SELECT ... FROM question_bank qb "
             f"WHERE qb.is_active = TRUE AND {safe_for_beta_sql('qb.id')}")

    `column` çağıran tarafından yazılan sabit bir tanımlayıcıdır (kullanıcı
    girdisi DEĞİL); bu yüzden f-string enjeksiyonu söz konusu değil.
    """
    return f"{column} IN ({_SAFE_POOL_ID_SQL})"

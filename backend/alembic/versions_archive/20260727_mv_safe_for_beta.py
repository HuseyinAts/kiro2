"""mv_safe_for_beta — kalite kapısını materyalize et

Revision ID: mv_safe_for_beta_20260727
Revises: restore_dropped_tables_20260727
Create Date: 2026-07-27

NEDEN
-----
`v_safe_for_beta` öğrenci-yüzü soru seçiminin TEK doğruluk kaynağı. Ama tanımı
ağır: `pipeline_metadata::jsonb ? '...'` biçiminde 5 ayrı jsonb varlık testi +
`NOT id IN (SELECT id FROM gate2c_demoted)` alt sorgusu. Planlayıcı bunu her
çağrıda inline ediyor.

27 Tem 2026 ölçümü (EXPLAIN ANALYZE, 3'er tur, canlı DB, 25.127 satırlık view):

    kapı  = v_safe_for_beta   -> planning 12-13 ms | execution 730-907 ms
    kapı  = matview eşdeğeri  -> planning  0.3-0.6 ms | execution  58-87 ms
    kapısız baseline          -> planning  7-14 ms | execution  87-116 ms

Yani matview'li kapı, kapısız sorgudan bile ucuz. ~10x kazanç.
`SELECT id FROM v_safe_for_beta` tam taraması ~2,3 s — REFRESH maliyeti bu.

TASARIM KARARLARI
-----------------
1. Matview yalnız `id` tutar (~25 K varchar). Tüm çağrı yerleri
   `id IN (SELECT id FROM mv_safe_for_beta)` biçiminde kullanır; başka kolona
   ihtiyaç yok. Küçük tutmak REFRESH'i ucuzlatır.

2. UNIQUE INDEX ZORUNLU — `REFRESH MATERIALIZED VIEW CONCURRENTLY` onsuz
   çalışmaz. CONCURRENTLY olmadan yenileme matview'i AccessExclusive kilitler,
   yani yenileme süresince tüm soru servisi durur.

3. REFRESH sahiplik ister. Uygulama `kiro2_app` (non-superuser) ile bağlanıyor,
   view'lerin sahibi `postgres`. Alembic'in hangi rolle koştuğu ortama göre
   değişiyor (DATABASE_URL_SYNC). Bu yüzden yenileme SECURITY DEFINER bir
   fonksiyona sarıldı: celery worker yalnız EXECUTE hakkı alır, REFRESH
   fonksiyon sahibinin yetkisiyle koşar. search_path sabitlenerek
   SECURITY DEFINER'ın klasik yetki yükseltme yüzeyi kapatıldı.

4. Bayat pencere KABUL EDİLDİ (ürün kararı, Hüseyin 27 Tem). İki yönü var:
     - yeni onaylanan soru geç görünür   -> zararsız
     - demote edilen soru bir süre daha servis edilir -> TEHLİKELİ
   İkinci yön küratör yargısından sonra tetiklenen yenileme ile kısaltılır
   (bkz. tasks/quality_gate_tasks.py). Gecelik yenileme yalnız emniyet ağı.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "mv_safe_for_beta_20260727"
down_revision: str | None = "restore_dropped_tables_20260727"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


APP_ROLE = "kiro2_app"


def upgrade() -> None:
    # ÖN KOŞUL. `v_safe_for_beta` alembic ile DEĞİL, elle çalıştırılan
    # migrations/*.sql dosyalarıyla yaratıldı (safe_for_beta_exclude_*.sql,
    # D4/D5_*.sql, image_audit_v1_apply_filter.sql). Yani alembic zinciri
    # alembic-DIŞI SQL'e örtük bağımlı. Temiz bir DB'de (CI, yeni ortam)
    # aşağıdaki CREATE, "relation v_safe_for_beta does not exist" gibi
    # bağlamsız bir hatayla düşerdi. Nedeni söyleyerek düş.
    op.execute(
        """
        DO $pre$
        BEGIN
            IF to_regclass('public.v_safe_for_beta') IS NULL THEN
                RAISE EXCEPTION
                    'mv_safe_for_beta ön koşulu eksik: v_safe_for_beta view''i yok. '
                    'Bu view alembic ile değil backend/migrations/*.sql ile '
                    'yaratılıyor (safe_for_beta_exclude_*.sql + D4/D5). Önce '
                    'onları uygula, sonra bu migration''ı çalıştır.';
            END IF;
        END
        $pre$
        """
    )

    # WITH DATA: migration anında doldur (~2,3 s). Boş bırakmak, kapıyı
    # açtığımız anda tüm soru servisinin 0 sonuç dönmesi demek olurdu.
    # CONCURRENTLY yenileme ÖNCEDEN DOLU matview ister; WITH NO DATA ile
    # yaratılsaydı ilk yenileme AccessExclusiveLock alıp ~2 sn boyunca tüm
    # öğrenci soru sorgularını bloklardı.
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_safe_for_beta AS
        SELECT id FROM v_safe_for_beta
        WITH DATA
        """
    )

    # CONCURRENTLY yenileme için ŞART.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_safe_for_beta_id "
        "ON mv_safe_for_beta (id)"
    )

    op.execute(
        "COMMENT ON MATERIALIZED VIEW mv_safe_for_beta IS "
        "'v_safe_for_beta id anlık görüntüsü. Öğrenci-yüzü soru seçiminin sıcak "
        "yol kapısı. Yenileme: refresh_safe_for_beta() — gecelik beat + küratör "
        "yargısı sonrası. Bayat pencere bilinçli kabul (bkz. migration docstring).'"
    )

    # SECURITY DEFINER: kiro2_app matview'in sahibi değil, REFRESH edemez.
    # search_path sabit — SECURITY DEFINER'da bu ihmal edilirse çağıran kendi
    # şemasındaki sahte pg_catalog fonksiyonlarıyla yetki yükseltebilir.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION refresh_safe_for_beta()
        RETURNS void
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $fn$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_safe_for_beta;
        END;
        $fn$
        """
    )

    op.execute(
        "COMMENT ON FUNCTION refresh_safe_for_beta() IS "
        "'mv_safe_for_beta CONCURRENTLY yenile. SECURITY DEFINER — uygulama rolü "
        "matview sahibi olmadığı için gerekli.'"
    )

    # Rol her ortamda var olmayabilir (CI, temiz dev DB). Yoksa sessizce atla:
    # GRANT hatası tüm migration'ı düşürürdü.
    op.execute(
        f"""
        DO $do$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                EXECUTE 'GRANT SELECT ON mv_safe_for_beta TO {APP_ROLE}';
                EXECUTE 'GRANT EXECUTE ON FUNCTION refresh_safe_for_beta() TO {APP_ROLE}';
            END IF;
        END
        $do$
        """
    )

    # Planlayıcı 25 K satırlık yeni ilişki için istatistik ister; ANALYZE
    # yapılmazsa ilk sorgular kötü plan seçebilir.
    op.execute("ANALYZE mv_safe_for_beta")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS refresh_safe_for_beta()")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_safe_for_beta")

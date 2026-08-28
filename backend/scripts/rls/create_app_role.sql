-- Faz 1 RLS aktivasyonu — non-superuser app rolü (idempotent, reproducible)
-- Neden: app `postgres` (superuser+bypassrls) → RLS BYPASS. Non-superuser rol
-- RLS policy'lerini uygular = tenant izolasyonu gerçekten aktif.
-- KANIT: bu rolle bağlanınca GUC=nonexistent_org → 0 satır (izolasyon çalışıyor).
--
-- Çalıştırma (operatör, superuser postgres ile):
--   psql -h localhost -p 5434 -U postgres -d kiro2 -f create_app_role.sql
-- PAROLA: aşağıdaki placeholder'ı güçlü bir parola ile değiştir (dev: kiro2_app_rls_2026).

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kiro2_app') THEN
    ALTER ROLE kiro2_app WITH LOGIN NOSUPERUSER NOBYPASSRLS
      PASSWORD 'kiro2_app_rls_2026';
  ELSE
    CREATE ROLE kiro2_app WITH LOGIN NOSUPERUSER NOBYPASSRLS
      PASSWORD 'kiro2_app_rls_2026';
  END IF;
END $$;

GRANT CONNECT ON DATABASE kiro2 TO kiro2_app;
GRANT USAGE, CREATE ON SCHEMA public TO kiro2_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO kiro2_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO kiro2_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO kiro2_app;

-- Gelecek objeler (migration'ların yaratacakları) için default privilege:
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO kiro2_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO kiro2_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT EXECUTE ON FUNCTIONS TO kiro2_app;

-- Geri alma (RLS deaktivasyonu için app'i postgres'e döndür + rol düşür):
--   REVOKE ALL ON ALL TABLES IN SCHEMA public FROM kiro2_app;
--   DROP OWNED BY kiro2_app; DROP ROLE kiro2_app;

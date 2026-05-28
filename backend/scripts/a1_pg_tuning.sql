-- A1.2 PostgreSQL tuning for 32GB RAM system (port 5434, kiro2)
-- RELOAD-able params (no downtime) + RESTART params (pending until restart)

\echo '=== BEFORE ==='
SELECT name, setting, unit FROM pg_settings
WHERE name IN ('shared_buffers','work_mem','max_connections','random_page_cost','effective_cache_size','maintenance_work_mem');

-- RELOAD-able (active after pg_reload_conf, NO restart)
ALTER SYSTEM SET work_mem = '32MB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_cache_size = '16GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET effective_io_concurrency = 200;

-- RESTART-required (written to auto.conf, pending until restart)
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET max_connections = 200;

-- Apply reload-able now
SELECT pg_reload_conf();

\echo ''
\echo '=== AFTER reload (restart-pending shown as old until restart) ==='
SELECT name, setting, unit,
       CASE WHEN pending_restart THEN 'PENDING RESTART' ELSE 'active' END AS status
FROM pg_settings
WHERE name IN ('shared_buffers','work_mem','max_connections','random_page_cost','effective_cache_size','maintenance_work_mem','effective_io_concurrency')
ORDER BY name;

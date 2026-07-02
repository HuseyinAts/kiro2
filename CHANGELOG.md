# KIRO2 Platform Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- **Auth/Database**: Fixed a critical `Multiple tables found for 'users'` error during authentication by ensuring `DBUser` safely references the unified `users` table instead of conflicting with legacy models.
- **Exception Handling**: Removed overly aggressive exception swallowing in `backend/core/application.py` that masked underlying errors as `{"detail": "Dahili sunucu hatasi"}`, making debugging difficult.
- **Test Environment**: Fixed `backend/core/config.py` where `load_dotenv(override=True)` was indiscriminately overwriting test environment variables with production defaults, breaking the local SQLite-based `TestClient` and resulting in `ConnectionRefusedError: [WinError 1225]`.
- **Golden Flow Mocks**: Addressed the testing bug where bypassing the live HTTP client with `TestClient` inadvertently triggered a mock database generation. This caused `result.scalar_one_or_none()` to yield an `AsyncMock` coroutine instead of a `DBUser`, resulting in `AttributeError: 'coroutine' object has no attribute 'is_active'`.
- **Alembic SQLite Compatibility**: Added multi-dialect compatibility checks (`is_sqlite`) for the `003_real_performance_indexes.py` migration script and removed problematic auto-generated SQLite table drop commands in `60e185cfcca9_unified_schema.py` to enable successful testing without requiring PostgreSQL/Docker.

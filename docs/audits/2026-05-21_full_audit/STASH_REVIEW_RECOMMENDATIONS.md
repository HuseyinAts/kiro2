# Stash Review — Session 179 (21 May 2026)

**Stash ref:** `stash@{0}` — `session-179-evidence-based-deep-review-audit-work`
**Total:** 552 file ops (56 added + 268 deleted + 228 modified)
**HEAD:** `a74696add audit(evidence): line-by-line review of 13 deep audit reports`

---

## Karar Matrisi (Adım C doğrulamasıyla güncel)

| # | Grup | Dosya | Önerilen Karar | Gerekçe |
|---|------|-------|----------------|---------|
| 1 | **RISKY — passlib/agents/ai_chat reverts** | 3 | ⚠️ **DROP** | Bu turda revert ettim. Stash sürümü hatalı varsayımlı kod içeriyor (`get_ensemble_manager` yok, `orchestrator.config.agents` yok, fake CryptContext). Pop edilmemeli. |
| 2 | **Doc + MEMORY drift fix** | ~12 | ✅ **KEEP — pop + commit** | CLAUDE.md/README.md/MEMORY: PG18.1, 1,163 endpoint, 16.64% coverage gerçekçi. EVIDENCE_BASED_DEEP_REVIEW_APPLIED.md son düzeltmeleriyle dürüst. |
| 3 | **_deprecated/ purge (126 silme)** | 126 | ✅ **KEEP — pop + commit** | Smoke import OK (14/14). 9 restore zaten yapıldı (team_challenges, fsrs_service, vb.). Kalan 126 silme güvenli — silinen dosyalara live import yok. |
| 4 | **Pilot scripts + audit artifacts** | 19 | 🟡 **KEEP — ayrı commit veya silme** | _pilots/ debug residue. fix_codemod_*.py scriptleri yararlı, geriye dönük referans. audit doc'lar (state-2026-05-21.md, llm_sample_50.tsv) saklı tutulmalı. |
| 5 | **Yeni özellik kodu** | 4 | 🟡 **PARÇALI** | <br>• migration ✅ chain `curator_audit_20260521 → s179_hot_path_idx_20260521` doğru + dry-run header var<br>• csrf smoke test ✅ (önceden PASS)<br>• **redis_rate_limiter.py 🟡 DEAD CODE** — 0 consumer, auth.py hâlâ in-process bucket. Kod kalitesi iyi ama wiring eksik<br>• beta_e2e_smoke_test.sh ✅ shell script, izole |
| 6 | **Algorithm + IDOR + middleware fix (9 dosya)** | 9 | ✅ **KEEP — pop + commit** | En yüksek değerli iş. BKT placement seed UUID, FSRS case mismatch, DAG mastery, learning_path_v2 IDOR, sinav.py BKT pipeline, bilge_alp BKT, enhanced_auth `/devices` — 184 unit test PASS. |
| 7 | **Codemod sweep (84 services + 66 scripts)** | 150 | ✅ **KEEP — pop + ayrı commit** | services/: 261 valid + 23 over-broad cleanup. **scripts/ DSN sweep doğrulandı: 66/66 anomali=0**, tümü surgical `os.getenv("DATABASE_URL", "postgres:1470@…")` → env-required check. Audit'in 53+'ten 13 fazla saymam doğru (pattern varyantları). |

### Adım C ek doğrulamalar (21 May 2026, bu turda)

| Test | Sonuç |
|---|---|
| 5 rastgele scripts/ DSN diff spot-check | 5/5 tutarlı, surgical |
| 66 scripts/ anomali taraması (>4 add veya >5 remove) | **0/66 anomali** |
| `redis_rate_limiter.py` kod kalitesi | ✅ İyi (Redis ZSET, fail-open, dataclass) |
| `redis_rate_limiter.py` consumer count | ❌ **0 consumer** (dead code) |
| Migration chain | ✅ `curator_audit → s179_hot_path_idx` |
| Migration dry-run header | ✅ Mevcut (alembic upgrade head ENGELLENDI) |

---

## Pop stratejisi (önerilen sıra)

```bash
# 1. ÖNCE: Sadece güvenli grupları pop et
# Grup 6 (algoritma fixleri) — en yüksek değer, test edilmiş
git checkout stash@{0} -- \
  backend/api/bilge_alp.py \
  backend/api/encryption_management.py \
  backend/api/enhanced_auth_api.py \
  backend/api/learning_path_v2.py \
  backend/api/sinav.py \
  backend/app/services/dag_service.py \
  backend/app/services/learning_path_orchestrator.py \
  backend/services/bkt_service.py \
  backend/services/learning_event_service.py

# 2. Grup 5 (yeni kod — koşullu)
git checkout stash@{0} -- \
  backend/alembic/versions/20260521_s179_hot_path_indexes.py \
  backend/core/redis_rate_limiter.py \
  backend/tests/unit/test_csrf_protection_s179.py \
  backend/scripts/quality/beta_e2e_smoke_test.sh

# 3. Grup 2 (doc düzeltmeleri)
git checkout stash@{0} -- \
  CLAUDE.md \
  README.md \
  docs/architecture/state-2026-05-21.md \
  docs/audits/2026-05-21_full_audit/EVIDENCE_BASED_DEEP_REVIEW_APPLIED.md

# 4. Grup 3 (_deprecated/ purge) — git stash apply --keep-index ile partial
# VEYA tüm silmeleri kopyala
git stash show stash@{0} --name-only -- backend/_deprecated/ | \
  xargs -I {} rm -rf {}
git stash show stash@{0} --name-only | grep "/_deprecated/" | \
  xargs -I {} rm -rf {}

# 5. Grup 4 (pilot artifacts) — opsiyonel, kişisel tercih
git checkout stash@{0} -- backend/_pilots/

# 6. Grup 7 (codemod) — EN SON, en geniş etki, ayrı commit'te tut
# services/ ve scripts/ codemod dosyalarını listele:
git stash show stash@{0} --name-only | \
  grep -E "^backend/(services|scripts)/" | \
  grep -v "/_deprecated/" | \
  xargs git checkout stash@{0} --

# 7. Grup 1 (risky) — POP ETME, stash'te bırak veya drop et
# auth.py + ai_chat_service.py + agents.py — bunlar stash'te kalsın
# Tehlikeli kod'u repo'ya geri getirme.

# Tüm gruplar uygun ise:
git stash drop stash@{0}  # SADECE her şey iyi olduktan sonra
```

---

## Test stratejisi (her pop'tan sonra)

```bash
cd backend
# Smoke imports
python -c "from api.auth import router"
python -c "from api.bilge_alp import router"
python -c "from services.bkt_service import BKTService"

# Targeted unit tests
python -m pytest tests/unit/test_bkt_zpd_static_methods.py \
                 tests/unit/test_subject_normalize.py \
                 tests/unit/test_csrf_protection_s179.py \
                 tests/unit/test_irt_validators.py \
                 tests/unit/test_fsrs_v6_service.py \
                 tests/test_smoke_api_critical.py \
                 tests/test_router_registration.py \
                 -q --tb=short

# 194 PASS / 7 SKIPPED beklenir (önceki çalışmadaki sonuç)
```

---

## Risk değerlendirmesi

**EN YÜKSEK RİSK (POP ETME):**
- `backend/api/auth.py` stash sürümü — passlib shim (fake CryptContext)
- `backend/api/agents.py` stash sürümü — `orchestrator.config.agents` (yok)
- `backend/services/ai_chat_service.py` stash sürümü — `get_ensemble_manager` (yok)
- Bu üçü import-time error veya runtime AttributeError üretir

**ORTA RİSK:**
- Grup 7 codemod sweep — 84 services + 66 scripts. Bazı pre-existing logger.error sitelerine eklenmiş exc_info=True over-broad olabilir. Spot-check yapılmadı (sadece services/ AST taraması yapıldı, scripts/ atlanmıştı).

**DÜŞÜK RİSK:**
- Grup 6 algorithm fixleri (testleri pass etti)
- Grup 5 yeni dosyalar (migration dry-run, smoke test)
- Grup 3 _deprecated/ silmeleri (smoke import OK)
- Grup 2 dokümantasyon

---

## Kararını söyle, ben uygulamayım

Şu üç seçeneğin var:

**Seçenek A: Konservatif — sadece Grup 2+6 pop et, gerisini stash'te bırak**
- Sadece doc + algorithm fix → 1 commit, 21 dosya
- Geri kalan stash'te bekler, ileride tek tek değerlendirilir

**Seçenek B: Geniş — Grup 1 hariç hepsi**
- 5 ayrı commit (Grup 2, 3, 4, 5, 6, 7)
- Stash drop edilir (Grup 1 risky kod gitsin)

**Seçenek C: Daha fazla doğrulama**
- Önce Grup 7 codemod spot-check
- Sonra Grup 5 redis_rate_limiter.py test
- Karar sonradan

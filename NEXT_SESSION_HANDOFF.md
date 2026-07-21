# NEXT SESSION HANDOFF

**Tarih:** 2026-07-21
**Proje:** KIRO2 (YKS/TYT/AYT Hazırlık Platformu)
**Branch:** `feature/self-evolution-optimization` @ `2a1bb42e5` — origin ile senkron
**Bağlam:** ~19 gün boyunca commit'lenmeden birikmiş "War Room" (2 Tem otonom oturum) + lint churn + cache çöpü yığınının elden geçirilmesi.

## 1. BU OTURUMDA NE YAPILDI

Commit'lenmemiş 600+ dosyalık karışık yığın 3 paralel agent ile sınıflandırıldı, sonra ayrıştırılıp **11 commit** halinde temizlendi (hepsi push edildi):

| Commit | İçerik |
|---|---|
| `075e37ba5` | Çöp untrack (64K satır cache/berturk + pid + reports/health) + gitignore |
| `8a3028c8b` | `ai_tasks.py` celery worker register + 2 pool-growth audit md |
| `7bff8af80` | 159 dosya kozmetik lint (ruff+eslint autofix, davranış-koruyan) |
| `ce80ed5b5` | `irt_analysis_service` legacy `Soru` → prod `question_bank` + is_active (dual-table fix) |
| `da73bab85` | gemini MCP `google.generativeai` → `google.genai` SDK + requirements google-genai==2.0.0 |
| `1cc5106c9` | War Room tweaks: hybrid_llm redis cache, FSRS stres adaptasyonu, figonly-gate, chat disclaimer |
| `038e1c132` | Dev-ops: PostgreSQL health check port 5432→**5434** fix + ASCII console marker (cp1254) |
| `ef71e023c` | blindsolve re-gate audit doc (bulk %95 temiz) |
| `ac4936f8b` | **FSRS mercy** `/due?mercy=true` wire + TDD (3 test) |
| `97c6c0211` | mercy metodu (`get_due_items_with_mercy`) commit — caller/callee bütünlüğü |
| `2a1bb42e5` | gitignore poolA retag scratch SQL |

### Verification-driven kararlar (Karpathy push-back)
- **3 phantom yakalandı, wire EDİLMEDİ:** `analytics_engine.py` IRT theta guard (her iki estimator zaten NaN/Inf/bounds korumalı), `ai_chat_service.py` guardrail+cache (mock method'a ölü — system_prompt hiç kullanılmıyor; gerçek chat `enhanced_chat.py`/qwen3:8b), `security_guard.py` (mevcut `verify_student_access` IDOR ile mükerrer + global body-read riski).
- **1 gerçek hata düzeltildi:** mercy caller (`ac4936f8b`) commit'lenmiş ama callee değildi → temiz checkout'ta AttributeError; `97c6c0211` ile kapatıldı.
- **REVERT:** `ai_chat_service.py` (mock'a ölü), `docker-compose.yml` (spekülatif pgbouncer + yanlış DB adı), `.cursor/mcp.json` (şifre churn), 5 alembic migration (history NEVER MODIFY), requirements sympy pin.
- **SİLİNDİ (orphan, unimported, kullanıcı onaylı):** `data_masking.py`, `security_guard.py`, `analytics_engine.py`, `indexedDBExamStore.ts`.

## 2. MEVCUT DURUM
- **Working tree:** temiz (bu handoff hariç).
- **FSRS mercy:** canlı — `GET /api/v1/fsrs/due?mercy=true` yığılma/catch-up modu (stability/zorluk önceliği, bilişsel yük limiti).
- **Test:** mercy 3 + fsrs regresyon 62 PASS; proje-standart lint temiz.

## 3. SONRAKİ OTURUM İÇİN (TODO)
1. **MEB guardrail'i gerçek yola taşı** — `ai_chat_service` mock'undaki guardrail değersizdi; istenirse `backend/api/enhanced_chat.py` (qwen3:8b gerçek chat) system prompt'una eklenmeli.
2. **security_guard prompt-injection** — global middleware yerine, LLM input noktasına (enhanced_chat) cerrahi guard olarak istenirse eklenebilir (verify_student_access IDOR zaten yeterli).
3. **KVKK data masking** — Faz B (anonimleştirme) zaten DONE; ek maskeleme gerekirse env-based salt ile yeniden yazılmalı (silinen hardcoded-salt versiyonu değil).
4. **Bekleyen (task backlog):** `#390` gh CLI + Dependabot (operatör), `#415` A11y/WCAG AccessibilityProvider, `#270` GitHub Actions kontrol.

---
*Önceki War Room handoff (2 Tem) bu oturumda gerçek duruma göre baştan yazıldı; o içerik commit'lenmemiş yığındaki yarım/ölü kodu anlatıyordu — hepsi elden geçirildi.*

---
name: tdd-loop
description: Self-correcting test-driven fix. Failing test veya bug alır, max 3 iterasyonda düzeltir. Sonsuz döngü koruması ve regresyon kontrolü içerir.
---

# TDD Loop — Self-Correcting Fix

Failing test veya bug açıklaması verildiğinde **max 3 iterasyonda** çözüme
ulaşır, çözülemezse durur ve kullanıcıya sorar.

## Ne Zaman Kullanılmalı

- Tek failing test düzeltme: `backend/tests/test_auth.py::test_login_success`
- Bug raporu: "health endpoint 503 dönüyor"
- Yeni feature için TDD: önce test yaz, sonra döngüyle geçir

## Döngü

### 1. Testi çalıştır / bug'ı reproduce et
```bash
cd backend && pytest <TEST_PATH> -x --tb=short -q
```
**Geçiyorsa:** "Test zaten geçiyor, fix gerekmiyor" — dur.

### 2. Hatayı analiz et
- Traceback'i oku, kaynak dosyayı aç
- `.claude/rules/testing.md`'deki 30 "öğrenilen ders"e bak:
  - #23 Dual Table Trap
  - #25 async generator vs context manager
  - #26 case convention (enum vs DB)
  - #11 pytestmark placement
- **503/500 ise INFRA-FIRST**: önce altyapı (Docker/Redis/PG port 5434)

### 3. Minimal fix uygula
- **Tek dosya**, minimum değişiklik
- Büyük refactor YOK — sadece testi geçir
- Fix öncesi geri dönüş noktası belirle (`git stash` veya commit)

### 4. Testi tekrar çalıştır
Geçti mi? Regresyon kontrolü:
```bash
cd backend && pytest -x --tb=short -q
```

### 5. Sonuç değerlendirmesi
- **GEÇTI + Regresyon yok** → ruff check, bitir
- **KALDI + iterasyon < 3** → Adım 2'ye dön
- **KALDI + iterasyon = 3** → Durun, kullanıcıya sor

## 3. İterasyonda Durma Mesajı

```
3 denemede çözülemedi.
Sorun: [özet]
Denemeler:
  1. [deneme 1] → neden başarısız
  2. [deneme 2] → neden başarısız
  3. [deneme 3] → neden başarısız
Öneri: [sonraki adım — farklı yaklaşım, daha derin debug, vs]
Devam edeyim mi, yoksa farklı yaklaşım mı deneyelim?
```

## Sıkı Kurallar

- **Max 3 iterasyon** — sonsuz döngü yok
- **Her iterasyonda 1 dosya** değiştir
- **Reward hacking YASAK** — `assert True`, `pytest.skip` without reason,
  boş test, `@pytest.mark.flaky` (gerçek reason olmadan)
- **Regresyon kontrolü** her iterasyon sonrası
- Fix başarılı → `ruff check` + `ruff format`

## Detaylı Rehber

- `.claude/skills/tdd-loop/SKILL.md`
- `.claude/rules/testing.md` — 30 öğrenilen ders (Session 6-148)
- `.cursor/rules/10-backend.mdc` — KIRO2 backend pattern'ları

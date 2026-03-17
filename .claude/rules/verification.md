---
name: verification-rules
description: Boris Cherny verification feedback loop kurallari
trigger: always
priority: high
---

# Verification Rules - Boris Cherny Standards

> "Claude'a calismasini dogrulama imkani vermek, nihai sonucun kalitesini %200-300 artiriyor."
> - Boris Cherny, Claude Code Creator

## ZORUNLU DOGRULAMA ADIMLARI

### Her Kod Degisikliginden Sonra

YOU MUST run these verification steps after ANY code modification:

1. **Python Dosyalari icin**
   ```bash
   cd backend && ruff check . --select=E,F,W --ignore=E501
   cd backend && mypy --ignore-missing-imports main.py
   ```

2. **TypeScript Dosyalari icin**
   ```bash
   cd frontend && npx tsc --noEmit
   ```

3. **Test Calistirma**
   ```bash
   pytest -x --tb=short -q
   ```

## ASLA YAPMA (NEVER)

- NEVER skip verification steps
- NEVER mark task complete without running tests
- NEVER use `assert True` or similar fake assertions
- NEVER use `# pragma: no cover` without justification
- NEVER ignore Exit Code 2 errors

## EXIT CODE KURALLARI (Daisy Stanton)

| Code | Anlam | Aksiyon |
|------|-------|---------|
| 0 | Basari | Devam et |
| 2 | Engelleyici Hata | DUR ve duzelt |
| Diger | Uyari | Kullaniciya goster |

## PROACTIVELY SUBAGENT KULLANIMI

IMPORTANT: Bu agent'lari kullanici istemeden OTOMATIK calistir:

- `test-runner`: Kod degisikligi sonrasi
- `code-reviewer`: Commit oncesi
- `verification-agent`: Her degisiklik sonrasi

## REWARD HACKING ONLEME

Asagidaki patternler tespit edilirse EXIT CODE 2 dondur:

```
assert True
assert true
ASSERT_TRUE(true)
echo Success
print("Success")
pass # placeholder
return None # stub
```

## DOGRULAMA KONTROL LISTESI

Her gorev tamamlanmadan once bu listeyi kontrol et:

- [ ] Linting (ruff) basarili mi?
- [ ] Type check (mypy/tsc) basarili mi?
- [ ] Testler geciyor mu?
- [ ] Reward hacking pattern yok mu?
- [ ] Guvenlik kontrolleri gecti mi?
- [ ] Coverage dusmus mu?
- [ ] Dogru tablo mu? (`question_bank` = 77K production, `questions` = BOS legacy)
- [ ] `is_active == True` filtresi var mi? (soru sorgularinda ZORUNLU)
- [ ] Infra calisiyor mu? (ONCE health check, SONRA koda bak — detay asagida)
- [ ] En basit cozum mu? (Daha basit alternatif varsa ONU sec — YAGNI)
- [ ] Root Cause Analysis tablosu yazildi mi? (debugging-first.md gate)

## INFRA-FIRST HATA AYIKLAMA (Infrastructure Check First)

Endpoint/servis hatasi goruldugunde ONCE altyapiyi kontrol et:

1. Docker servisleri: `docker ps --format "table {{.Names}}\t{{.Status}}"`
2. PostgreSQL (port 5434 — native Windows): `pg_isready -p 5434`
   - Docker ise: `docker exec kiro2_postgres pg_isready`
3. Redis: `redis-cli ping` veya `docker exec kiro2_redis redis-cli ping`
4. Backend health: `curl -s http://localhost:8000/api/v1/health`

Kural: 503/500 donuyorsa %75 ihtimalle altyapi sorunu.
ONCE altyapi kontrolu yap, SONRA koda bak.

## ADIM ADIM ILERLEME KURALI (Incremental Progress)

> "Buyuk degisiklikler yerine kucuk, test edilebilir adimlar tercih et"
> - JWT DRY Refactoring Dersi (Subat 2026)

### TDD Kurali (Red-Green-Verify)
Bug fix icin: ONCE fail eden testi bul/yaz → FIX yap → Test PASS mi? → Evet: commit. Hayir: geri al.
Fix ONCESI fail eden test YOKSA, once testi yaz.

### Degisiklik Stratejisi

```
1. ANALIZ: Mevcut durumu anla
   - Bagimlilik grafini ciz
   - Scope'lari belirle
   - Risk analizi yap

2. PLAN: Kucuk adimlar planla
   - Her adim bagimsiz test edilebilir olmali
   - Her adim geri alinabilir olmali
   - Maximum 3 dosya/adim

3. UYGULA: Adim adim ilerle
   - Adim 1 -> Test -> Basarili? Devam : Geri Al
   - Adim 2 -> Test -> Basarili? Devam : Geri Al
   - ...

4. DOGRULA: Her adimda
   - pytest -x --tb=short
   - Etkilenen testleri calistir
```

### Hibrit Yaklasim Tercihi

Buyuk refactoring'lerde HIBRIT yaklasim kullan:

| Senaryo | Yaklasim |
|---------|----------|
| Yeni fonksiyon | Merkezi tanimla |
| Mevcut fixture | Lokal tut, merkezi cagir |
| Sabitler | Merkezi tanimla, import et |
| Context-bagimli | Lokal tut |

### Geri Alma Noktasi

Her adimda soyle dusun:
- "Bu degisiklik basarisiz olursa nasil geri alirim?"
- "Minimum geri alma maliyeti ne?"

```python
# DOGRU: Kucuk, geri alinabilir
# Adim 1: Import ekle
from tests.conftest import helper_func  # Geri al: satiri sil

# Adim 2: Kullan
result = helper_func()  # Geri al: eski kodu geri koy

# YANLIS: Buyuk, geri almasi zor
# Tum dosyayi yeniden yaz
```

## TEKRARLAYAN SORUN TESPITI (Session 6-19 Analizi)

Ayni sorun 2+ session'da gorulurse ROOT CAUSE cozulmeli, patch yapilmamali.

### Bilinen Tekrarlayan Sorunlar

| Sorun | Session'lar | Root Cause | Cozum | Status |
|-------|------------|------------|-------|--------|
| Health 503 | 7, 12, 19 | Test ortaminda Redis/DB yok | conftest mock fixture | TAMAMLANDI |
| httpx AsyncClient | 8, 12 | 0.27+ deprecated | ASGITransport migration | TAMAMLANDI |
| SQLAlchemy import | 11, 19 | absolute vs relative | Lint rule + pre-commit | TAMAMLANDI |
| Password validator | 7, 8 | Sequential char rejection | Test password generator | TAMAMLANDI |
| DuplicateTable | 12 | PostgreSQL index conflict | Test DB isolation | TAMAMLANDI |

### Kural
- 1. kez: Fix + not al
- 2. kez: ROOT CAUSE coz + enforcement ekle (lint/hook)
- 3. kez: ASLA olmasin - CI/CD'de blokla

## FIX/SKIP METRIK TAKIBI

Her session sonunda hesapla ve raporla:

```
Fix: [sayi] dosya gercekten duzeltildi
Skip: [sayi] dosya module/class skip edildi
Oran: [X]% fix (hedef: >=%50)
Toplam Skip: [sayi] (hedef: <500, mevcut: 3718)
```

## KAYNAK

Bu kurallar su kaynaklardan derlenmistir:
- Boris Cherny (Claude Code Creator) - Verification Feedback Loops
- Daisy Stanton (Anthropic) - Exit Code Standards
- Sid Bidasaria (Anthropic) - Subagent Architecture
- Alex Albert (Anthropic) - Prompt Engineering
- KIRO2 Team (Subat 2026) - JWT DRY Refactoring Lessons
- KIRO2 Team (7 Subat 2026) - Session 6-19 Mikroskobik Analiz

# Code Review

Son kod değişikliklerini incele. **SADECE kanıtlanabilir sorunları** raporla,
yapay bulgu üretme.

## Öncelikle Lint + Test Çalıştır

Sorunu iddia etmeden önce:

```bash
cd backend && ruff check . --select=E,F,W --ignore=E501 2>&1 | head -20
cd backend && python -m pytest tests/unit/ -x --tb=short -q 2>&1 | tail -10
```

Lint ve test geçiyorsa "kod çalışmıyor" deme — kanıt yok.

## Diff Kapsamı

```bash
git diff HEAD~3 --stat
git diff HEAD~3
```

Son 3 commit'teki değişiklikleri incele. Kullanıcı farklı range isterse
`HEAD~N` veya `main..HEAD` gibi belirtir.

## Raporlama Prensibi

**SADECE bu üç kategoride bulgu çıkar:**

- **CRITICAL** — lint fail, test fail, kesin runtime crash (AttributeError, TypeError)
- **WARNING** — spesifik senaryo ile tetiklenen sorun
- **ÖNERİ** — iyileştirme (opsiyonel, merge engeli değil)

**Asla raporlama:**

- Teorik/varsayımsal sorunlar ("şöyle olsa şuna yol açabilir")
- Önceki review'da düzeltilmiş şeyler
- Değiştirilmemiş satırlardaki sorunlar (scope dışı)
- Docstring/type hint eksikliği (değişmeyen kodda)

## İnceleme Kriterleri

### Güvenlik (kanıt zorunlu)

- SQL injection: raw f-string query satırını göster
- Hardcoded credentials: dosya:satır göster
- JWT bypass: exploit senaryosu göster
- IDOR: `.cursor/rules/10-backend.mdc` pattern ihlali göster

### Performans

- N+1 query: sorgu örneği göster
- Missing index: EXPLAIN çıktısı tavsiye et
- Memory leak: nesne referansı zinciri göster

### KIRO2 Özel

- `authStore.ts` kullanılmalı (`useAuth.ts` DEĞIL)
- UTF-8 + NFC Turkish normalization
- DB port: 5434
- Dual Table Trap: `QuestionBankItem` kullanılıyor mu? (Session 78)
- `is_active == True` filtresi var mı? (Session 78)
- Middleware'de `raise HTTPException` yerine `JSONResponse` kullanılıyor mu? (Session 148)

## Çıktı Formatı

```markdown
### Lint: PASS/FAIL
### Test: PASS/FAIL

### CRITICAL (merge engeli)
- [dosya:satır] Sorun + KANIT

### WARNING
- [dosya:satır] Sorun + senaryo

### ÖNERİ
- [dosya:satır] İyileştirme

### SONUÇ: Commit edilebilir mi? EVET/HAYIR
```

0 critical + 0 warning → **"Kod temiz, commit edilebilir."**
Yapay bulgu üretme — sessiz geç.

# Test Coverage Analyzer

Backend test coverage gap analizi yapar ve oncelikli test plani olusturur.

## Gorev

1. `cd backend && pytest --cov=app --cov-report=term-missing -q --no-header 2>/dev/null | tail -50` ile coverage raporu al
2. Coverage %50 altindaki modulleri tespit et
3. Kritik servisleri onceliklendir:
   - `services/soru_bankasi_service.py` (soru bankasi — ana is mantigi)
   - `services/osym_exam_engine.py` (sinav motoru)
   - `api/auth.py` (kimlik dogrulama)
   - `api/learning_path*.py` (ogrenme yolu)
   - `services/content_management_service.py` (icerik yonetimi)
4. Her modul icin 3-5 test senaryosu oner (happy path, edge case, error)
5. Oncelik sirasi: P0 (guvenlik + ana is mantigi) > P1 (API endpoints) > P2 (yardimci servisler)

## Kurallar

- Sadece OKUMA yap, dosya DEGISTIRME
- `question_bank` tablosu kullan (`questions` degil — bos legacy tablo)
- `is_active == True` filtresi unutma
- Turkce enum degerleri: `SubjectType.MATEMATIK` (MATHEMATICS degil)
- Mevcut test sayisi: 10,082 passed, coverage ~%18

## Cikti Formati

```markdown
## Coverage Gap Raporu

| Modul | Mevcut Coverage | Oncelik | Onerilen Test Sayisi |
|-------|----------------|---------|---------------------|

### P0 Testler (Hemen yazilmali)
- [ ] test_soru_bankasi_service.py: ...
- [ ] test_auth_endpoints.py: ...

### P1 Testler
...
```

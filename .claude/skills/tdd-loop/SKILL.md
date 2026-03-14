# TDD Loop — Self-Correcting Test-Driven Fix

Failing test veya bug aciklamasi alir, max 3 iterasyonda duzeltir.

## Kullanim

```
/tdd-loop backend/tests/test_auth.py::test_login_success
/tdd-loop "health endpoint 503 donuyor"
```

## Adimlar

1. **Testi calistir** (veya bug'i reproduce et):
   ```bash
   cd C:/Users/husey/kiro2/backend && pytest $TEST_PATH -x --tb=short -q
   ```
   Test geciyorsa: "Test zaten geciyor, fix gerekmiyor" de ve dur.

2. **Hatayi analiz et**:
   - Traceback'i oku, ilgili kaynak dosyayi ac
   - testing.md derslerini kontrol et (ozellikle #23 Dual Table, #25 async generator, #26 case convention)
   - INFRA-FIRST: 503/500 ise ONCE altyapi kontrolu yap

3. **Minimal fix uygula**:
   - Tek dosyada, minimum degisiklik
   - Buyuk refactor YAPMA — sadece testi gecir
   - Fix oncesi geri alma noktasi belirle

4. **Testi tekrar calistir**:
   ```bash
   cd C:/Users/husey/kiro2/backend && pytest $TEST_PATH -x --tb=short -q
   ```

5. **Sonuc degerlendirmesi**:
   - GECTI: Regresyon kontrolu yap (`pytest -x --tb=short -q`), basariliysa bitir
   - KALDI + iterasyon < 3: Adim 2'ye don
   - KALDI + iterasyon = 3: Kullaniciya sor:
     ```
     3 denemede cozulemedi.
     Sorun: [ozet]
     Denemeler: [ne denendi]
     Oneri: [sonraki adim]
     Devam edeyim mi, yoksa farkli yaklasim mi deneyelim?
     ```

## Kurallar

- Max 3 iterasyon (sonsuz dongu yok)
- Her iterasyonda sadece 1 dosya degistir
- `assert True`, `pytest.skip`, veya bos test ile fix YAPMA (reward hacking)
- Iterasyonlar arasi test sonucunu karsilastir (regression kontrolu)
- Fix basarili ise ruff check calistir

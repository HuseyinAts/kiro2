# Plan-Before-Execute Gate

3+ dosya degisikligi gerektiren HER gorevde (bug fix, feature, refactor):
Edit/Write CAGIRMADAN ONCE kullaniciya kisa plan sun.

## Format

| # | Dosya | Degisiklik | Risk |
|---|-------|-----------|------|
| 1 | path/file.py | Ne yapilacak | LOW/MED/HIGH |

## Kurallar

- 1-2 dosya → plan OPSIYONEL (direkt ilerle)
- 3+ dosya → plan ZORUNLU (kullanici onaysiz Edit yapma)
- Bug fix → debugging-first.md root cause tablosu DA gerekli (iki gate birlikte)
- Kullanici "hizli yap" / "direkt ilerle" / "plan atla" derse plan ATLA

## Neden

94 session analizinde 43x wrong_approach friction teshis edildi.
Kok neden: Claude dogrudan koda dalip yanlis yonde ilerliyor.
Bu gate, 30 saniyelik plan adimi ile saatlerce surabilecek yeniden calismayi onler.

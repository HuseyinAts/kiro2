# Deprecation Guard

Dosya `_deprecated/` klasorune tasinmadan ONCE asagidaki adimlari ZORUNLU uygula.
Bu kural 3+ Docker rebuild israfi sonrasi eklendi (20 Mart 2026).

## Tasima Oncesi Kontrol Listesi

1. **Import taramasi** — tasinacak dosyanin ADINI grep ile tara:
   ```bash
   # Frontend
   grep -r "from.*DosyaAdi\|import.*DosyaAdi" frontend/src/ --include="*.ts" --include="*.tsx" | grep -v _deprecated | grep -v node_modules

   # Backend
   grep -r "from.*dosya_adi\|import.*dosya_adi" backend/ --include="*.py" | grep -v _deprecated | grep -v __pycache__
   ```

2. **Wrapper chain kontrolu** — Ozellikle `*Page.tsx` → `Modern*Page.tsx` → `Modern*Dashboard.tsx` gibi zincirleri kontrol et:
   ```bash
   # Wrapper dosyalari bul
   grep -l "export.*from\|import.*from.*Modern" frontend/src/pages/*.tsx | head -20
   ```

3. **Sonuc degerlendirmesi:**
   - 0 referans → guvenle tasi
   - 1+ referans → referanslari ONCE guncelle, SONRA tasi
   - Wrapper chain → TUM chain'i birlikte tasi veya HICBIRINI tasima

## Bilinen Wrapper Chain'ler (Mart 2026)

| Wrapper Page | Imports | Imports |
|-------------|---------|---------|
| StudentDashboardPage.tsx | StudentDashboard.tsx | ModernStudentDashboard.tsx |
| TeacherDashboardPage.tsx | TeacherDashboard.tsx | ModernTeacherDashboard.tsx |
| TeacherClassesPage.tsx | ModernTeacherClassesPage.tsx | - |

## Hook Enforcement

- `pre-tool-use.py`: `_deprecated` path'e Write/Edit yapildiginda uyari verir
- `pre-commit-check.py`: Commit oncesi case-duplicate tespiti yapar

@echo off
echo ======================================================
echo   Claude AI Projects - Dosya Ekleme Yardımcısı
echo   Teknofest 2025 - YKS Hazırlık Platformu
echo ======================================================
echo.

echo [1] Instructions dosyasını aç
start "" "C:\Users\husey\kiro2\.claude\CLAUDE_AI_INSTRUCTIONS.md"
echo ✅ Instructions dosyası açıldı - İçeriği kopyalayıp Claude'a yapıştırın
echo.

echo [2] Kritik dosyalar klasörünü aç
explorer "C:\Users\husey\kiro2\.claude\files"
echo ✅ Files klasörü açıldı - Dosyaları Claude'a yükleyin
echo.

echo [3] Proje ana klasörünü aç
explorer "C:\Users\husey\kiro2"
echo ✅ Ana proje klasörü açıldı
echo.

echo ======================================================
echo   YAPILACAKLAR:
echo ======================================================
echo   1. CLAUDE_AI_INSTRUCTIONS.md içeriğini Claude Instructions'a yapıştırın
echo   2. Şu dosyaları sırayla Claude Files'a ekleyin:
echo      - README.md
echo      - .env.example
echo      - backend/main.py
echo      - backend/services/learning_style_service.py
echo      - backend/HIBRIT_OGRENME_STILI_DEMO.md
echo   3. Projeyi test edin
echo ======================================================
echo.

pause
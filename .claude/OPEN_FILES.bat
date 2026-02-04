@echo off
echo ========================================================
echo   Claude AI Projects - 15 Dosya Hazir!
echo   Teknofest 2025 - YKS Hazirlik Platformu
echo ========================================================
echo.

echo [1] Claude Instructions dosyasini ac
start "" notepad "C:\Users\husey\kiro2\.claude\CLAUDE_AI_INSTRUCTIONS.md"
timeout /t 1 /nobreak >nul

echo [2] Organize edilen dosyalar klasorunu ac
explorer "C:\Users\husey\kiro2\.claude\files"
timeout /t 1 /nobreak >nul

echo [3] Ozet dosyasini ac
start "" notepad "C:\Users\husey\kiro2\.claude\FINAL_15_FILES_READY.md"
timeout /t 1 /nobreak >nul

echo.
echo ========================================================
echo   DOSYA LISTESI (11 Hazir Dosya):
echo ========================================================
echo.
echo   CORE (5 dosya):
echo   1. README.md
echo   2. main.py
echo   3. learning_style_service.py
echo   4. .env.example
echo   5. docker-compose.yml
echo.
echo   FEATURES (6 dosya):
echo   6. HIBRIT_OGRENME_STILI_DEMO.md
echo   7. ZPD_MAARIF_DEMO.md
echo   8. IRT_MORFOLOJI_DEMO.md
echo   9. API_INTEGRATION_SUMMARY.md
echo   10. requirements.txt
echo   11. package.json
echo.
echo ========================================================
echo   ADIMLAR:
echo ========================================================
echo   1. CLAUDE_AI_INSTRUCTIONS.md icerigini kopyala
echo   2. Claude Projects > Instructions'a yapistir
echo   3. Files bolumune yukaridaki dosyalari ekle
echo   4. Test et: "64 hibrit ogrenme profili nedir?"
echo ========================================================
echo.
echo Basarilar! 
echo.
pause
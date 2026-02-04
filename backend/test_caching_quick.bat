@echo off
echo ============================================
echo REDIS CACHING TEST
echo ============================================
echo.

echo Test 1: Ilk cagri (cache miss - yavas)
curl -s -w "\nResponse Time: %%{time_total}s\n" http://localhost:9000/health
echo.

timeout /t 2 /nobreak >nul

echo Test 2: Ikinci cagri (cache hit - HIZLI olmali!)
curl -s -w "\nResponse Time: %%{time_total}s\n" http://localhost:9000/health
echo.

timeout /t 2 /nobreak >nul

echo Test 3: Ucuncu cagri (cache hit - HIZLI olmali!)
curl -s -w "\nResponse Time: %%{time_total}s\n" http://localhost:9000/health
echo.

echo ============================================
echo Test tamamlandi!
echo Ikinci ve ucuncu cagrilar ^<0.01s olmali
echo ============================================
pause

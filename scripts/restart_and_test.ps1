# KIRO2 — Backend Yeniden Başlat + Placement/CAT/FSRS Tam Akış Testi
# Çalıştır: cd C:\Users\husey\kiro2 && powershell -ExecutionPolicy Bypass -File .\scripts\restart_and_test.ps1

Set-Location "C:\Users\husey\kiro2\backend"

Write-Host "=== 1. Tüm Python/Uvicorn process'leri durdur ===" -ForegroundColor Yellow
Get-Process -Name "python","uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

Write-Host "=== 2. __pycache__ temizle ===" -ForegroundColor Yellow
Get-ChildItem "C:\Users\husey\kiro2\backend" -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Pycache temizlendi"

Write-Host "`n=== 3. Backend başlat (port 8000, no-reload) ===" -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m","uvicorn","main:app","--host","127.0.0.1","--port","8000" `
    -RedirectStandardOutput "kiro2_backend.log" -RedirectStandardError "kiro2_backend_err.log"
Write-Host "Backend başlatıldı. 35 saniye bekleniyor..."
Start-Sleep -Seconds 35

# Health check
$ready = $false
for ($i = 0; $i -lt 10; $i++) {
    Start-Sleep -Seconds 3
    try {
        $hc = Invoke-WebRequest "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 4 -ErrorAction Stop
        if ($hc.StatusCode -eq 200) { Write-Host "Backend HAZIR" -ForegroundColor Green; $ready = $true; break }
    } catch {}
    Write-Host "  bekleniyor..."
}
if (-not $ready) { Write-Host "Backend BAŞLAMADI! Logları kontrol et: backend\kiro2_backend_err.log" -ForegroundColor Red; exit 1 }

$BASE = "http://localhost:8000"

# Login
$loginResp = Invoke-WebRequest "$BASE/api/v1/auth/login" -Method POST -ContentType "application/json" `
    -Body '{"email":"admin@kiro2.com","password":"Kiro2Beta2026@x"}' -UseBasicParsing -ErrorAction Stop
$token = ($loginResp.Content | ConvertFrom-Json).access_token
$h = @{ "Authorization" = "Bearer $token"; "Content-Type" = "application/json" }
Write-Host "LOGIN OK" -ForegroundColor Green

# TEST 1: Placement Start
Write-Host "`n─── TEST 1: placement/start (matematik) ───"
try {
    $r1 = Invoke-WebRequest "$BASE/api/v1/placement/start" -Method POST -Headers $h `
        -Body '{"subject_id":"matematik","school_type":"default"}' -UseBasicParsing -ErrorAction Stop
    $p1 = $r1.Content | ConvertFrom-Json
    $SID = $p1.session_id; $QID = $p1.question.question_id
    Write-Host "  ✅ HTTP $($r1.StatusCode)" -ForegroundColor Green
    Write-Host "  session_id  : $SID"
    Write-Host "  question_id : $QID"
    Write-Host "  soru        : $($p1.question.question_text.Substring(0,[Math]::Min(90,$p1.question.question_text.Length)))..."
    Write-Host "  A           : $($p1.question.option_a.Substring(0,[Math]::Min(70,$p1.question.option_a.Length)))"
    Write-Host "  B           : $($p1.question.option_b.Substring(0,[Math]::Min(70,$p1.question.option_b.Length)))"
    Write-Host "  level_hint  : $($p1.level_hint)"
    if ($null -eq $p1.question.correct_answer -or $p1.question.correct_answer -eq "") {
        Write-Host "  cevap gizli : ✅ EVET" -ForegroundColor Green
    } else {
        Write-Host "  cevap gizli : ❌ SIZI: $($p1.question.correct_answer)" -ForegroundColor Red
    }
} catch { Write-Host "  ❌ HATA: $($_.ErrorDetails.Message)" -ForegroundColor Red; exit 1 }

Start-Sleep -Milliseconds 400

# TEST 2: Placement Answer
Write-Host "`n─── TEST 2: placement answer ───"
try {
    $r2 = Invoke-WebRequest "$BASE/api/v1/placement/$SID/answer" -Method POST -Headers $h `
        -Body "{`"question_id`":`"$QID`",`"answer`":`"A`",`"response_time_ms`":3500}" -UseBasicParsing -ErrorAction Stop
    $p2 = $r2.Content | ConvertFrom-Json
    Write-Host "  ✅ HTTP $($r2.StatusCode)" -ForegroundColor Green
    Write-Host "  theta : $($p2.theta)  se: $($p2.se)  completed: $($p2.is_complete)"
    if (-not $p2.is_complete -and $p2.next_question) { Write-Host "  next_q: $($p2.next_question.question_id)" }
} catch { Write-Host "  ❌ HATA: $($_.ErrorDetails.Message)" -ForegroundColor Red }

Start-Sleep -Milliseconds 400

# TEST 3: CAT Session
Write-Host "`n─── TEST 3: cat/sessions ───"
try {
    $r3 = Invoke-WebRequest "$BASE/api/v1/cat/sessions" -Method POST -Headers $h `
        -Body '{"subject_area":"MATEMATIK","exam_type":"TYT","max_items":10}' -UseBasicParsing -ErrorAction Stop
    $p3 = $r3.Content | ConvertFrom-Json
    $CATSID = $p3.session_id; $CATQID = $p3.question.question_id
    Write-Host "  ✅ HTTP $($r3.StatusCode)" -ForegroundColor Green
    Write-Host "  cat_session : $CATSID"
    Write-Host "  soru        : $($p3.question.question_text.Substring(0,[Math]::Min(70,$p3.question.question_text.Length)))..."
} catch { Write-Host "  ❌ HATA: $($_.ErrorDetails.Message)" -ForegroundColor Red }

Start-Sleep -Milliseconds 400

# TEST 4: CAT Answer
Write-Host "`n─── TEST 4: cat answer ───"
if ($CATSID -and $CATQID) {
    try {
        $r4 = Invoke-WebRequest "$BASE/api/v1/cat/sessions/$CATSID/answer" -Method POST -Headers $h `
            -Body "{`"question_id`":`"$CATQID`",`"answer`":`"B`",`"response_time_ms`":5000}" -UseBasicParsing -ErrorAction Stop
        $p4 = $r4.Content | ConvertFrom-Json
        Write-Host "  ✅ HTTP $($r4.StatusCode)" -ForegroundColor Green
        Write-Host "  theta: $($p4.theta)  se: $($p4.se)  completed: $($p4.completed)"
    } catch { Write-Host "  ❌ HATA: $($_.ErrorDetails.Message)" -ForegroundColor Red }
}

Start-Sleep -Milliseconds 400

# TEST 5: FSRS Due
Write-Host "`n─── TEST 5: fsrs/due ───"
try {
    $r5 = Invoke-WebRequest "$BASE/api/v1/fsrs/due" -Method GET -Headers $h -UseBasicParsing -ErrorAction Stop
    Write-Host "  ✅ HTTP $($r5.StatusCode) — kart sayısı: $(($r5.Content | ConvertFrom-Json).Count)" -ForegroundColor Green
} catch { Write-Host "  ❌ HATA: $($_.ErrorDetails.Message)" -ForegroundColor Red }

# DB Özet
Write-Host "`n─── DB Kayıtları ───"
$env:PGPASSWORD = "changeme_strong_password_here"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2 -c `
    "SELECT 'cat_sessions'   as tablo, COUNT(*) as kayit FROM kiro2_cat_sessions
     UNION ALL SELECT 'learning_events', COUNT(*) FROM kiro2_learning_events
     UNION ALL SELECT 'fsrs_cards',      COUNT(*) FROM user_item_fsrs;" 2>&1

Write-Host "`n════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "          TEST TAMAMLANDI" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════" -ForegroundColor Cyan

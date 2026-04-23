# KIRO2 — P0 Golden paketi (J1+J2+J3+J4+K4): önce :8000 health, sonra 10 test
# (GF1y: J2 PUT profil; GF1x/GF3d: J1 çıkış + J4 complete; GF6w: admin soru; GF1w/GF3w: BKT/regresyon).
# Optimum: backend ayakta + seed (test@kiro2.com) + bu script → tek doğruluk.
# Kullanım:  repo kökünden
#   powershell -ExecutionPolicy Bypass -File .\scripts\run_p0_golden_local.ps1
# İsteğe:     -BackendUrl "http://127.0.0.1:8000"
param(
    [string] $BackendUrl = "http://localhost:8000"
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$backend = Join-Path $repo "backend"

Write-Host "=== P0 Golden (10 test) -> $BackendUrl ===" -ForegroundColor Cyan
try {
    # İlk yanıt DB/ES kontrolleriyle 5s+ sürebilir (TimeoutSec 30)
    $h = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 30
    if ($h.StatusCode -ne 200) { throw "HTTP $($h.StatusCode)" }
} catch {
    Write-Host "HATA: $BackendUrl health yok. Once: cd backend; uvicorn main:app --host 0.0.0.0 --port 8000" -ForegroundColor Red
    exit 1
}
Write-Host "Health OK" -ForegroundColor Green

$env:BACKEND_URL = $BackendUrl
Set-Location $backend
# P0 (CI backend-test ile aynı 10 test)
python -m pytest `
    tests/e2e/test_golden_flows.py::test_gf1_login_and_me `
    tests/e2e/test_golden_flows.py::test_gf3_exam_configs_list `
    tests/e2e/test_golden_flows.py::test_gf3b_osym_subjects_reachable `
    tests/e2e/test_golden_flows.py::test_gf3c_exam_session_save_answer_smoke `
    tests/e2e/test_golden_flows.py::test_gf1x_logout_invalidates_bearer_token `
    tests/e2e/test_golden_flows.py::test_gf1y_profile_put_smoke `
    tests/e2e/test_golden_flows.py::test_gf3d_exam_session_complete_smoke `
    tests/e2e/test_golden_flows.py::test_gf6w_admin_question_create_returns_success `
    tests/e2e/test_golden_flows.py::test_gf1w_save_answer_updates_mastery `
    tests/e2e/test_golden_flows.py::test_gf3w_save_answer_rejects_empty_question_id `
    -v --tb=short
exit $LASTEXITCODE

# KIRO2 — P0 Golden paketi (J1+J3+J4 tabanı): önce :8000 health, sonra 4 test.
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

Write-Host "=== P0 Golden (4 test) -> $BackendUrl ===" -ForegroundColor Cyan
try {
    $h = Invoke-WebRequest -Uri "$BackendUrl/health" -UseBasicParsing -TimeoutSec 5
    if ($h.StatusCode -ne 200) { throw "HTTP $($h.StatusCode)" }
} catch {
    Write-Host "HATA: $BackendUrl health yok. Once: cd backend; uvicorn main:app --host 0.0.0.0 --port 8000" -ForegroundColor Red
    exit 1
}
Write-Host "Health OK" -ForegroundColor Green

$env:BACKEND_URL = $BackendUrl
Set-Location $backend
# GF1, GF3, GF3b, GF3c
python -m pytest `
    tests/e2e/test_golden_flows.py::test_gf1_login_and_me `
    tests/e2e/test_golden_flows.py::test_gf3_exam_configs_list `
    tests/e2e/test_golden_flows.py::test_gf3b_osym_subjects_reachable `
    tests/e2e/test_golden_flows.py::test_gf3c_exam_session_save_answer_smoke `
    -v --tb=short
exit $LASTEXITCODE

# Faz 2.5 — Weekly audit wrapper (Windows Task Scheduler tetikler).
# Pazar 09:00 çalışır, RAW + SCORING TSV üretir, log dosyasına yazar.
#
# Setup: bkz. SCHEDULER_SETUP.md

$ErrorActionPreference = "Continue"
$PROJECT_ROOT = "C:\Users\husey\kiro2"
$LOG_DIR = "$PROJECT_ROOT\backend\_pilots\scheduler_logs"
$DATE_STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$LOG_FILE = "$LOG_DIR\weekly_audit_$DATE_STAMP.log"

New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null

Set-Location $PROJECT_ROOT

# DATABASE_URL env zaten user-scope set'liyse otomatik miras alınır.
# Açıkça override gerekirse uncomment:
# $env:DATABASE_URL = "postgresql://postgres:1470@localhost:5434/kiro2"

"=== Weekly Audit started at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" | Tee-Object -FilePath $LOG_FILE

python -m backend.scripts.quality.weekly_audit 2>&1 | Tee-Object -FilePath $LOG_FILE -Append

$EXIT_CODE = $LASTEXITCODE
"=== Weekly Audit exited with code $EXIT_CODE at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" | Tee-Object -FilePath $LOG_FILE -Append

exit $EXIT_CODE

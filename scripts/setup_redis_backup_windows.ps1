# Setup Redis Backup Task Scheduler (Windows)
# Türkiye Üniversite Sınavları Hazırlık Platformu

param(
    [string]$BackupPath = "C:\Users\husey\kiro2\backups\redis",
    [string]$ScriptPath = "C:\Users\husey\kiro2\scripts\backup_redis.sh",
    [string]$Schedule = "Daily",
    [string]$Time = "02:00"
)

# Configuration
$TaskName = "RedisBackup-TurkeySinavPlatform"
$TaskDescription = "Daily Redis backup for Turkey University Exam Preparation Platform"

Write-Host "[INFO] Setting up Redis backup task scheduler..." -ForegroundColor Green

# Create backup directory
if (!(Test-Path $BackupPath)) {
    New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
    Write-Host "[OK] Created backup directory: $BackupPath" -ForegroundColor Green
}

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "[WARN] Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create task action (run backup script with Git Bash)
$BashPath = "C:\Program Files\Git\bin\bash.exe"
$Action = New-ScheduledTaskAction `
    -Execute $BashPath `
    -Argument "-c `"cd /c/Users/husey/kiro2/scripts && ./backup_redis.sh`"" `
    -WorkingDirectory "C:\Users\husey\kiro2\scripts"

# Create trigger (daily at 2 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

# Create principal (run with highest privileges)
$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Register task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $TaskDescription `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings | Out-Null

Write-Host "[OK] Scheduled task created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Task Details:" -ForegroundColor Cyan
Write-Host "  Name:          $TaskName"
Write-Host "  Schedule:      $Schedule at $Time"
Write-Host "  Backup Path:   $BackupPath"
Write-Host "  Script:        $ScriptPath"
Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Cyan
Write-Host "  View task:     Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Run now:       Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Disable:       Disable-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Remove:        Unregister-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "[SUCCESS] Redis backup automation setup complete!" -ForegroundColor Green

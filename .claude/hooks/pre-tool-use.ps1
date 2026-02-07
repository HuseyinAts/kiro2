# PreToolUse Security Hook - Daisy Stanton Reward Hacking Prevention
# PURPOSE: Tehlikeli komutlari ENGELLEMEK
# TRIGGER: Her Bash tool kullanimi oncesi
# EXIT CODE 2: BLOCKS operation (Daisy Stanton recommendation)

param(
    [Parameter(Mandatory=$false)]
    [string]$Command = "",
    [Parameter(Mandatory=$false)]
    [string]$ToolName = "Bash"
)

$ErrorActionPreference = "Continue"

# Color output functions
function Write-Success { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "[FAIL] $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }

Write-Host ""
Write-Host "================================================================" -ForegroundColor Yellow
Write-Host "  SECURITY GATE - PreToolUse Hook" -ForegroundColor Yellow
Write-Host "  Daisy Stanton: Reward Hacking Prevention" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Yellow
Write-Host ""

$IsBlocked = $false
$BlockReason = ""

# ============================================================
# 1. TEHLIKELI BASH KOMUTLARI (BLOCKING)
# ============================================================

$DangerousPatterns = @{
    # File system destruction
    "rm\s+-rf\s+/" = "Root dizin silme - KRITIK TEHLIKE"
    "rm\s+-rf\s+\*" = "Wildcard silme - TEHLIKE"
    "rm\s+-rf\s+\." = "Current directory silme - TEHLIKE"
    "rmdir\s+/s\s+/q" = "Windows recursive silme - TEHLIKE"
    "del\s+/s\s+/q" = "Windows recursive silme - TEHLIKE"

    # Database destruction
    "DROP\s+TABLE" = "Tablo silme - VERI KAYBI"
    "DROP\s+DATABASE" = "Veritabani silme - KRITIK"
    "TRUNCATE\s+TABLE" = "Tablo bosaltma - VERI KAYBI"
    "DELETE\s+FROM\s+\w+\s*$" = "WHERE olmadan DELETE - TEHLIKE"
    "DELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1" = "Tum kayitlari silme - TEHLIKE"

    # Git dangerous operations
    "git\s+push\s+.*--force\s+origin\s+(main|master)" = "Force push to main - TEHLIKE"
    "git\s+reset\s+--hard\s+HEAD~\d+" = "Hard reset - KAYIP RISKI"
    "git\s+clean\s+-fd" = "Git clean force - KAYIP RISKI"

    # System modification
    "chmod\s+777" = "Tum izinleri acma - GUVENLIK RISKI"
    "chown\s+-R" = "Recursive sahiplik degistirme - DIKKAT"

    # Secrets exposure
    "cat\s+\.env" = ".env okuma - SECRETS RISKI"
    "echo\s+.*API_KEY" = "API key loglama - SECRETS RISKI"
    "echo\s+.*PASSWORD" = "Password loglama - SECRETS RISKI"
    "echo\s+.*SECRET" = "Secret loglama - SECRETS RISKI"

    # Code injection
    "eval\s*\(" = "Eval kullanimi - INJECTION RISKI"
    "exec\s*\(" = "Exec kullanimi - INJECTION RISKI"
    "\$\(" = "Command substitution - DIKKAT"

    # Network attacks
    "curl.*\|\s*bash" = "Pipe to bash - MALWARE RISKI"
    "wget.*\|\s*bash" = "Pipe to bash - MALWARE RISKI"
    "curl.*\|\s*sh" = "Pipe to shell - MALWARE RISKI"
}

# Check command against patterns
foreach ($pattern in $DangerousPatterns.Keys) {
    if ($Command -match $pattern) {
        $IsBlocked = $true
        $BlockReason = $DangerousPatterns[$pattern]
        break
    }
}

# ============================================================
# 2. PROTECTED PATHS (BLOCKING)
# ============================================================

$ProtectedPaths = @(
    "C:\\Windows",
    "C:\\Program Files",
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "~/.ssh",
    "~/.aws",
    "~/.config"
)

foreach ($path in $ProtectedPaths) {
    if ($Command -match [regex]::Escape($path)) {
        $IsBlocked = $true
        $BlockReason = "Protected path access: $path"
        break
    }
}

# ============================================================
# 3. .ENV FILE PROTECTION
# ============================================================

if ($Command -match "\.env" -and $Command -notmatch "\.env\.example") {
    # Allow reading .env.example but not .env
    if ($Command -match "(cat|type|less|more|head|tail|Edit|Write)\s+.*\.env\s*$") {
        $IsBlocked = $true
        $BlockReason = ".env file access - secrets korunmali"
    }
}

# ============================================================
# 4. REWARD HACKING PREVENTION (kod icinde)
# ============================================================

$RewardHackingCommands = @(
    'echo\s+[\x27\x22]?Success[\x27\x22]?\s*$',
    'echo\s+[\x27\x22]?OK[\x27\x22]?\s*$',
    'exit\s+0\s*#',
    'true\s*$',
    ':\s*$'
)

foreach ($pattern in $RewardHackingCommands) {
    if ($Command -match $pattern) {
        Write-Warning "Potential reward hacking pattern detected: $pattern"
        # Not blocking, just warning
    }
}

# ============================================================
# FINAL VERDICT
# ============================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Yellow
Write-Host "  SECURITY CHECK RESULT" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Yellow

if ($IsBlocked) {
    Write-Host ""
    Write-Error "COMMAND BLOCKED!"
    Write-Host ""
    Write-Host "Command: $Command" -ForegroundColor Red
    Write-Host "Reason: $BlockReason" -ForegroundColor Red
    Write-Host ""
    Write-Host "This command has been blocked for security reasons." -ForegroundColor Yellow
    Write-Host "If you believe this is a false positive, please review the command." -ForegroundColor Yellow
    Write-Host ""

    # EXIT CODE 2 = BLOCKING ERROR (Daisy Stanton)
    exit 2
} else {
    Write-Host ""
    Write-Success "Security check passed"
    Write-Host "Command: $($Command.Substring(0, [Math]::Min(80, $Command.Length)))$(if ($Command.Length -gt 80) {'...'} else {''})" -ForegroundColor Cyan
    Write-Host ""

    # EXIT CODE 0 = SUCCESS
    exit 0
}

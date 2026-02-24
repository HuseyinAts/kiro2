# PreToolUse Security Hook - Daisy Stanton Reward Hacking Prevention
# EXIT CODE 2: BLOCKS operation | EXIT CODE 0: ALLOW
# Reads command from env var CLAUDE_BASH_COMMAND (set by Claude Code)

param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$Cmd = "",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Rest
)

$ErrorActionPreference = "SilentlyContinue"

# Primary: env var (no shell parsing issues)
$Command = $env:CLAUDE_BASH_COMMAND

# Fallback: command-line args (legacy)
if ([string]::IsNullOrWhiteSpace($Command)) {
    if ($Rest) { $Cmd = ($Cmd, ($Rest -join " ")) -join " " }
    $Command = $Cmd
}

# Use prefixed names to avoid shadowing built-in cmdlets
function Out-Ok { param([string]$M) Write-Host "[OK] $M" -ForegroundColor Green }
function Out-Warn { param([string]$M) Write-Host "[WARN] $M" -ForegroundColor Yellow }
function Out-Block { param([string]$M) Write-Host "[BLOCK] $M" -ForegroundColor Red }

try {
    if ([string]::IsNullOrWhiteSpace($Command)) { exit 0 }

    $IsBlocked = $false
    $BlockReason = ""

    # === 1. DANGEROUS COMMANDS ===
    $DangerousPatterns = @(
        @{ P = 'rm\s+-rf\s+/';                     R = "Root dizin silme" }
        @{ P = 'rm\s+-rf\s+\*';                    R = "Wildcard silme" }
        @{ P = 'rm\s+-rf\s+\.';                    R = "Current dir silme" }
        @{ P = 'rmdir\s+/s\s+/q';                  R = "Win recursive silme" }
        @{ P = 'del\s+/s\s+/q';                    R = "Win recursive silme" }
        @{ P = 'DROP\s+TABLE';                      R = "Tablo silme" }
        @{ P = 'DROP\s+DATABASE';                   R = "DB silme" }
        @{ P = 'TRUNCATE\s+TABLE';                  R = "Tablo bosaltma" }
        @{ P = 'DELETE\s+FROM\s+\w+\s*$';           R = "WHERE olmadan DELETE" }
        @{ P = 'git\s+push\s+.*--force\s+origin\s+(main|master)'; R = "Force push main" }
        @{ P = 'git\s+reset\s+--hard\s+HEAD~';     R = "Hard reset" }
        @{ P = 'git\s+clean\s+-fd';                 R = "Git clean force" }
        @{ P = 'chmod\s+777';                       R = "Tum izinleri acma" }
        @{ P = 'cat\s+\.env\b';                     R = ".env okuma" }
        @{ P = 'echo\s+.*[\$%]\w*API_KEY';          R = "API key loglama" }
        @{ P = 'echo\s+.*[\$%]\w*PASSWORD';         R = "Password loglama" }
        @{ P = 'echo\s+.*[\$%]\w*SECRET';           R = "Secret loglama" }
        @{ P = '^\s*eval\s+';                       R = "Eval injection" }
        @{ P = ';\s*eval\s+';                       R = "Eval injection" }
        @{ P = '&&\s*eval\s+';                      R = "Eval injection" }
        @{ P = 'curl.*\|\s*bash';                   R = "Pipe to bash" }
        @{ P = 'wget.*\|\s*bash';                   R = "Pipe to bash" }
        @{ P = 'curl.*\|\s*sh';                     R = "Pipe to shell" }
    )

    foreach ($entry in $DangerousPatterns) {
        if ($Command -match $entry.P) {
            $IsBlocked = $true
            $BlockReason = $entry.R
            break
        }
    }

    # === 2. PROTECTED PATHS (skip Program Files — legit tools live there) ===
    if (-not $IsBlocked) {
        $ProtectedPaths = @(
            "C:\\Windows\\System32",
            "/etc/passwd",
            "/etc/shadow",
            "~/.ssh/id_",
            "~/.aws/credentials"
        )
        foreach ($path in $ProtectedPaths) {
            if ($Command.Contains($path)) {
                $IsBlocked = $true
                $BlockReason = "Protected path: $path"
                break
            }
        }
    }

    # === 3. .ENV PROTECTION ===
    if (-not $IsBlocked -and $Command -match '\.env\b' -and $Command -notmatch '\.env\.example') {
        if ($Command -match '(cat|type|less|more|head|tail)\s+.*\.env\s*$') {
            $IsBlocked = $true
            $BlockReason = ".env dosyasina erisim"
        }
    }

    # === 4. REWARD HACKING (warning only) ===
    $RewardHackPatterns = @(
        'echo\s+[\x27\x22]?Success[\x27\x22]?\s*$',
        'echo\s+[\x27\x22]?OK[\x27\x22]?\s*$',
        '^\s*true\s*$',
        '^\s*:\s*$'
    )
    foreach ($rp in $RewardHackPatterns) {
        if ($Command -match $rp) {
            Out-Warn "Reward hacking pattern: $rp"
        }
    }

    # === VERDICT ===
    if ($IsBlocked) {
        Out-Block "BLOCKED: $BlockReason"
        Write-Host "  Command: $Command" -ForegroundColor Red
        exit 2
    }

    # Silent pass — no output for normal commands
    exit 0

} catch {
    # Hook failure must not block work — fail open with warning
    Out-Warn "Hook exception: $($_.Exception.Message)"
    exit 0
}

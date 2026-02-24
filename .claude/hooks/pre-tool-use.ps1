# PreToolUse Security Hook - Daisy Stanton Reward Hacking Prevention
# EXIT CODE 2: BLOCKS operation | EXIT CODE 0: ALLOW
# Input: JSON via stdin from Claude Code (tool_input.command)

$ErrorActionPreference = "SilentlyContinue"

# Read hook input from stdin JSON (non-blocking, 500ms timeout)
$Command = ""
try {
    $stream = [Console]::OpenStandardInput()
    $buffer = New-Object byte[] 65536
    $asyncResult = $stream.BeginRead($buffer, 0, $buffer.Length, $null, $null)
    if ($asyncResult.AsyncWaitHandle.WaitOne(500)) {
        $bytesRead = $stream.EndRead($asyncResult)
        if ($bytesRead -gt 0) {
            $json = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $bytesRead)
            $hookInput = $json | ConvertFrom-Json
            $Command = $hookInput.tool_input.command
        }
    }
} catch {}

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
        @{ P = '(?i)DROP\s+TABLE';                  R = "Tablo silme" }
        @{ P = '(?i)DROP\s+DATABASE';               R = "DB silme" }
        @{ P = '(?i)TRUNCATE\s+TABLE';              R = "Tablo bosaltma" }
        @{ P = '(?i)DELETE\s+FROM\s+\w+\s*;?\s*$';  R = "WHERE olmadan DELETE" }
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

    # === 2. PROTECTED PATHS ===
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
            Write-Host "[WARN] Reward hacking pattern: $rp" -ForegroundColor Yellow
        }
    }

    # === VERDICT ===
    if ($IsBlocked) {
        [Console]::Error.WriteLine("BLOCKED: $BlockReason")
        exit 2
    }

    exit 0

} catch {
    Write-Host "[WARN] Hook exception: $($_.Exception.Message)" -ForegroundColor Yellow
    exit 0
}

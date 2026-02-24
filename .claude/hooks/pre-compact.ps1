# Pre-Compaction Hook
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$bd = "$env:USERPROFILE\.claude\session-backups"

if (!(Test-Path $bd)) { New-Item -ItemType Directory -Path $bd -Force | Out-Null }

if (Test-Path "progress.md") {
    Copy-Item "progress.md" "$bd\progress-$ts.md"
}

if (Test-Path "CLAUDE.local.md") {
    Copy-Item "CLAUDE.local.md" "$bd\CLAUDE.local-$ts.md"
}

if (Test-Path ".git") {
    git status --short > "$bd\git-$ts.txt" 2>$null
    git log -3 --oneline >> "$bd\git-$ts.txt" 2>$null
}

"[$(Get-Date)] Saved" | Add-Content "$env:USERPROFILE\.claude\compaction.log"

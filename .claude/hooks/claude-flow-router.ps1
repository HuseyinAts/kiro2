# Claude Flow Router Hook (PowerShell)
# Runs AUTOMATICALLY before Claude processes any user message
# Routes prompts to specialized agents based on content analysis

param(
    [string]$UserMessage
)

# Skip empty messages
if ([string]::IsNullOrWhiteSpace($UserMessage)) {
    exit 0
}

# Change to project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
Set-Location $ProjectRoot

# Run the orchestrator
try {
    $RoutingResult = python .claude/scripts/claude_flow_orchestrator.py $UserMessage 2>$null

    if ($LASTEXITCODE -eq 0 -and $RoutingResult) {
        $Routing = $RoutingResult | ConvertFrom-Json

        $PrimaryAgent = $Routing.routing.primary_agent
        $Confidence = $Routing.routing.confidence
        $Reasoning = $Routing.routing.reasoning
        $SecondaryAgents = $Routing.routing.secondary_agents -join ", "

        # Only show routing info for non-trivial routes
        if ($PrimaryAgent -ne "general-purpose" -and $PrimaryAgent) {
            Write-Host ""
            Write-Host "============================================================" -ForegroundColor Cyan
            Write-Host "[CLAUDE FLOW] Akilli Yonlendirme Aktif" -ForegroundColor Yellow
            Write-Host "============================================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "[>] Ana Agent: $PrimaryAgent" -ForegroundColor Green
            Write-Host "[>] Guven: $([math]::Round($Confidence * 100))%" -ForegroundColor White
            Write-Host "[>] Sebep: $Reasoning" -ForegroundColor White

            if ($SecondaryAgents -and $SecondaryAgents -ne "") {
                Write-Host "[>] Yardimci: $SecondaryAgents" -ForegroundColor Magenta
            }

            Write-Host ""
            Write-Host "============================================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Claude, bu gorevi $PrimaryAgent agent ile ele almali." -ForegroundColor Yellow
            Write-Host "   Task tool kullanarak: subagent_type=$PrimaryAgent" -ForegroundColor Gray
            Write-Host ""
            Write-Host "============================================================" -ForegroundColor Cyan
            Write-Host ""
        }
    }
} catch {
    # Silently continue on error
}

exit 0

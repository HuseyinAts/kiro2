# Auto Router for Claude Desktop App
# Provides visual routing + automatic clipboard injection

param(
    [string]$Prompt
)

# Run orchestrator
$result = python .claude/orchestration/orchestrator_v2.py "$Prompt" | ConvertFrom-Json

if ($result.routing.primary_agent -ne "general-purpose") {
    # Get agent and confidence
    $agent = $result.routing.primary_agent
    $confidence = [math]::Round($result.routing.confidence * 100)
    
    # Create auto-injection prompt
    $autoPrompt = "Use Task tool with subagent_type='$agent' to: $Prompt"
    
    # Copy to clipboard for easy paste
    $autoPrompt | Set-Clipboard
    
    # Visual feedback
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  AUTO-ROUTING ACTIVE" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Agent: $agent" -ForegroundColor Green
    Write-Host "  Confidence: $confidence%" -ForegroundColor White
    Write-Host ""
    Write-Host "  [COPIED TO CLIPBOARD]" -ForegroundColor Yellow
    Write-Host "  Press Ctrl+V to paste the routing command" -ForegroundColor Gray
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

exit 0
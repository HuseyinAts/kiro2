# KIRO2 MCP Server Startup Script
# Tarih: 2026-01-26
# Aciklama: MCP sunucularini dogru sirada baslatir

param(
    [switch]$HealthCheck,
    [switch]$StopAll,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# MCP Sunucu Yapilandirmasi
$McpServers = @(
    @{
        Name = "zemberek-mcp"
        Port = 8081
        Priority = 1
        Command = "python -m zemberek_mcp.server"
        WorkDir = ".mcp_pids"
        Critical = $true
        HealthEndpoint = "http://localhost:8081/health"
    },
    @{
        Name = "chromadb-mcp"
        Port = 8082
        Priority = 2
        Command = "python -m chromadb_mcp.server"
        WorkDir = ".mcp_pids"
        Critical = $true
        DependsOn = @("zemberek-mcp")
    },
    @{
        Name = "kiro2-orchestrator"
        Port = 8083
        Priority = 3
        Command = "python -m kiro2_orchestrator.server"
        WorkDir = ".mcp_pids"
        Critical = $true
        DependsOn = @("zemberek-mcp", "chromadb-mcp")
    },
    @{
        Name = "gemini-mcp"
        Port = 8084
        Priority = 4
        Command = "python -m gemini_mcp.server"
        WorkDir = ".mcp_pids"
        Critical = $false
    },
    @{
        Name = "youtube-education-api"
        Port = 8085
        Priority = 5
        Command = "python -m youtube_education_mcp.server"
        WorkDir = ".mcp_pids"
        Critical = $false
    },
    @{
        Name = "blackboard-coordinator"
        Port = 8765
        Priority = 6
        Command = "python -m blackboard_mcp.server"
        WorkDir = ".mcp_pids"
        Critical = $true
    }
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "INFO" { "White" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Test-PortInUse {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $connection
}

function Wait-ForHealthy {
    param([string]$Endpoint, [int]$TimeoutSeconds = 30)

    $startTime = Get-Date
    while ((Get-Date) - $startTime -lt [TimeSpan]::FromSeconds($TimeoutSeconds)) {
        try {
            $response = Invoke-WebRequest -Uri $Endpoint -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                return $true
            }
        } catch {
            # Henuz hazir degil
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Start-McpServer {
    param([hashtable]$Server)

    $name = $Server.Name
    $port = $Server.Port

    # Port kontrolu
    if (Test-PortInUse -Port $port) {
        Write-Log "Port $port zaten kullanimda ($name)" -Level "WARNING"
        return $true
    }

    # Bagimliliklari kontrol et
    if ($Server.DependsOn) {
        foreach ($dep in $Server.DependsOn) {
            $depServer = $McpServers | Where-Object { $_.Name -eq $dep }
            if ($depServer -and -not (Test-PortInUse -Port $depServer.Port)) {
                Write-Log "$name icin bagimlillik bekleniyor: $dep" -Level "WARNING"
                return $false
            }
        }
    }

    Write-Log "Baslatiliyor: $name (port $port)..." -Level "INFO"

    # Sunucuyu baslat (arka planda)
    try {
        $process = Start-Process -FilePath "powershell" -ArgumentList "-Command", $Server.Command -WindowStyle Hidden -PassThru

        # PID kaydet
        $pidFile = Join-Path $Server.WorkDir "$name.pid"
        $process.Id | Out-File -FilePath $pidFile -Force

        # Saglik kontrolu bekle
        if ($Server.HealthEndpoint) {
            if (Wait-ForHealthy -Endpoint $Server.HealthEndpoint) {
                Write-Log "$name basariyla baslatildi (PID: $($process.Id))" -Level "SUCCESS"
                return $true
            } else {
                Write-Log "$name saglik kontrolu basarisiz" -Level "ERROR"
                return $false
            }
        } else {
            # Saglik endpoint'i yoksa kisa bekle
            Start-Sleep -Seconds 2
            if (Test-PortInUse -Port $port) {
                Write-Log "$name basariyla baslatildi (PID: $($process.Id))" -Level "SUCCESS"
                return $true
            }
        }
    } catch {
        Write-Log "$name baslatma hatasi: $_" -Level "ERROR"
        return $false
    }

    return $false
}

function Stop-McpServer {
    param([hashtable]$Server)

    $pidFile = Join-Path $Server.WorkDir "$($Server.Name).pid"

    if (Test-Path $pidFile) {
        $pid = Get-Content $pidFile
        try {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Remove-Item $pidFile -Force
            Write-Log "$($Server.Name) durduruldu" -Level "SUCCESS"
        } catch {
            Write-Log "$($Server.Name) durdurulamadi: $_" -Level "WARNING"
        }
    }
}

function Get-McpHealth {
    Write-Host ""
    Write-Host "=== MCP Sunucu Saglik Durumu ===" -ForegroundColor Cyan
    Write-Host ""

    foreach ($server in $McpServers | Sort-Object { $_.Priority }) {
        $status = if (Test-PortInUse -Port $server.Port) { "AKTIF" } else { "KAPALI" }
        $color = if ($status -eq "AKTIF") { "Green" } else { "Red" }
        $critical = if ($server.Critical) { "[KRITIK]" } else { "" }

        Write-Host ("{0,-25} Port: {1,-5} Durum: {2,-7} {3}" -f $server.Name, $server.Port, $status, $critical) -ForegroundColor $color
    }

    Write-Host ""
}

# Ana Logic
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  KIRO2 MCP Server Yonetimi" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# PID dizini olustur
$pidDir = ".mcp_pids"
if (-not (Test-Path $pidDir)) {
    New-Item -ItemType Directory -Path $pidDir -Force | Out-Null
}

if ($HealthCheck) {
    Get-McpHealth
    exit 0
}

if ($StopAll) {
    Write-Log "Tum MCP sunuculari durduruluyor..." -Level "INFO"
    foreach ($server in $McpServers | Sort-Object { -$_.Priority }) {
        Stop-McpServer -Server $server
    }
    Write-Log "Tum sunucular durduruldu" -Level "SUCCESS"
    exit 0
}

# Sunuculari sirasina gore baslat
$sortedServers = $McpServers | Sort-Object { $_.Priority }

$successCount = 0
$failCount = 0

foreach ($server in $sortedServers) {
    $result = Start-McpServer -Server $server

    if ($result) {
        $successCount++
    } else {
        $failCount++
        if ($server.Critical) {
            Write-Log "Kritik sunucu baslatma hatasi: $($server.Name). Islem durduruluyor." -Level "ERROR"
            exit 2
        }
    }

    # Sunucular arasi kucuk bekleme
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ozet" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Basarili: $successCount" -ForegroundColor Green
Write-Host "  Basarisiz: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "White" })
Write-Host ""

Get-McpHealth

if ($failCount -gt 0) {
    exit 1
}

exit 0

# CoAct.AI Enhanced Reports - VM Monitoring Script
# This script monitors the health and performance of the enhanced reporting system

param(
    [switch]$Continuous,
    [int]$Interval = 30,
    [switch]$ShowLogs,
    [switch]$ShowMetrics
)

$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Status {
    param($Message, $Color = $Blue)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Test-ServiceHealth {
    param($ServiceName, $Url, $ExpectedStatus = 200)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Status "✅ $ServiceName is healthy" $Green
            return $true
        } else {
            Write-Status "⚠️ $ServiceName returned status $($response.StatusCode)" $Yellow
            return $false
        }
    } catch {
        Write-Status "❌ $ServiceName is not responding: $($_.Exception.Message)" $Red
        return $false
    }
}

function Get-ContainerStats {
    try {
        $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-Object -Skip 1
        Write-Status "📊 Container Status:" $Blue
        $containers | ForEach-Object { Write-Host "   $_" }
        
        if ($ShowMetrics) {
            Write-Status "📈 Resource Usage:" $Blue
            docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        }
    } catch {
        Write-Status "❌ Could not get container stats: $($_.Exception.Message)" $Red
    }
}

function Test-EnhancedReporting {
    Write-Status "🧪 Testing Enhanced Reporting Features..." $Blue
    
    # Test health endpoint
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 10
        Write-Status "✅ Health Check: $($healthResponse.status)" $Green
        Write-Status "   Version: $($healthResponse.version)" $Blue
        Write-Status "   Sessions: $($healthResponse.services.sessions)" $Blue
        Write-Status "   LLM: $($healthResponse.services.llm)" $Blue
    } catch {
        Write-Status "❌ Health check failed: $($_.Exception.Message)" $Red
    }
    
    # Check report directory
    $reportDir = ".\inter-ai-backend\reports"
    if (Test-Path $reportDir) {
        $reportCount = (Get-ChildItem $reportDir -Filter "*.pdf").Count
        Write-Status "📄 Reports generated: $reportCount" $Green
    } else {
        Write-Status "⚠️ Reports directory not found" $Yellow
    }
    
    # Check audio directory
    $audioDir = ".\inter-ai-backend\static\audio"
    if (Test-Path $audioDir) {
        $audioCount = (Get-ChildItem $audioDir -Filter "*.mp3").Count
        Write-Status "🔊 Audio files: $audioCount" $Green
    } else {
        Write-Status "⚠️ Audio directory not found" $Yellow
    }
}

function Show-SystemInfo {
    Write-Status "🖥️ System Information:" $Blue
    
    # Disk space
    $disk = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 }
    foreach ($drive in $disk) {
        $freeGB = [math]::Round($drive.FreeSpace / 1GB, 2)
        $totalGB = [math]::Round($drive.Size / 1GB, 2)
        $percentFree = [math]::Round(($drive.FreeSpace / $drive.Size) * 100, 1)
        Write-Host "   Drive $($drive.DeviceID) $freeGB GB free of $totalGB GB ($percentFree% free)"
    }
    
    # Memory
    $memory = Get-WmiObject -Class Win32_ComputerSystem
    $totalRAM = [math]::Round($memory.TotalPhysicalMemory / 1GB, 2)
    Write-Host "   Total RAM: $totalRAM GB"
    
    # Docker version
    try {
        $dockerVersion = docker --version
        Write-Host "   $dockerVersion"
    } catch {
        Write-Status "⚠️ Docker not available" $Yellow
    }
}

function Monitor-Loop {
    do {
        Clear-Host
        Write-Host "🔍 CoAct.AI Enhanced Reports - VM Monitor" -ForegroundColor $Blue
        Write-Host "=" * 60
        
        # Test services
        $frontendHealthy = Test-ServiceHealth "Frontend" "http://localhost:3000"
        $backendHealthy = Test-ServiceHealth "Backend API" "http://localhost:8000/api/health"
        
        Write-Host ""
        
        # Container stats
        Get-ContainerStats
        
        Write-Host ""
        
        # Enhanced reporting tests
        Test-EnhancedReporting
        
        Write-Host ""
        
        # System info
        Show-SystemInfo
        
        if ($ShowLogs) {
            Write-Host ""
            Write-Status "📋 Recent Backend Logs:" $Blue
            try {
                docker-compose logs --tail=10 backend
            } catch {
                Write-Status "❌ Could not fetch logs" $Red
            }
        }
        
        Write-Host ""
        Write-Host "=" * 60
        
        if ($Continuous) {
            Write-Status "⏱️ Next check in $Interval seconds... (Ctrl+C to stop)" $Yellow
            Start-Sleep -Seconds $Interval
        }
        
    } while ($Continuous)
}

# Main execution
Write-Host "🚀 Starting CoAct.AI VM Monitor..." -ForegroundColor $Blue

if ($Continuous) {
    Write-Status "Running continuous monitoring every $Interval seconds..." $Blue
    Monitor-Loop
} else {
    Monitor-Loop
}

Write-Status "Monitor completed." $Green
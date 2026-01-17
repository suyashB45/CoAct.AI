# CoAct.AI Enhanced Reports - VM Deployment Script (PowerShell)
# This script deploys the enhanced reporting system on a Windows VM

param(
    [switch]$SkipHealthCheck,
    [switch]$Rebuild
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

Write-Host "🚀 Deploying CoAct.AI Enhanced Reports on VM..." -ForegroundColor $Blue

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Success "Docker is installed"
} catch {
    Write-Error "Docker is not installed. Please install Docker Desktop first."
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
    Write-Success "Docker Compose is available"
} catch {
    Write-Error "Docker Compose is not available. Please install Docker Compose."
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Warning ".env file not found. Creating template..."
    @"
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
MODEL_NAME=gpt-4o-mini
TTS_DEPLOYMENT_NAME=tts-1

# Optional: Azure Storage (for report persistence)
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection_string_here
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Warning "Please edit .env file with your Azure OpenAI credentials before continuing."
    Write-Warning "Edit with: notepad .env"
    exit 1
}

# Create necessary directories
Write-Status "Creating necessary directories..."
New-Item -ItemType Directory -Force -Path "inter-ai-backend\reports" | Out-Null
New-Item -ItemType Directory -Force -Path "inter-ai-backend\static\audio" | Out-Null

# Stop existing containers
Write-Status "Stopping existing containers..."
try {
    docker-compose down --remove-orphans 2>$null
} catch {
    Write-Warning "No existing containers to stop"
}

# Build and start services
Write-Status "Building and starting enhanced CoAct.AI services..."
if ($Rebuild) {
    docker-compose up --build -d
} else {
    docker-compose up -d
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start services"
    exit 1
}

# Wait for services to be ready
Write-Status "Waiting for services to start..."
Start-Sleep -Seconds 10

# Check health
if (-not $SkipHealthCheck) {
    Write-Status "Checking service health..."
    $healthCheckPassed = $false
    
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Success "Backend service is healthy!"
                $healthCheckPassed = $true
                break
            }
        } catch {
            # Continue trying
        }
        
        if ($i -eq 30) {
            Write-Error "Backend service failed to start properly"
            docker-compose logs backend
            exit 1
        }
        Start-Sleep -Seconds 2
    }
    
    # Check frontend
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
        if ($frontendResponse.StatusCode -eq 200) {
            Write-Success "Frontend service is healthy!"
        }
    } catch {
        Write-Warning "Frontend may still be starting..."
    }
}

# Display service status
Write-Status "Service Status:"
docker-compose ps

# Display access information
Write-Host ""
Write-Success "🎉 CoAct.AI Enhanced Reports deployed successfully!"
Write-Host ""
Write-Host "📊 Access your application:" -ForegroundColor $Blue
Write-Host "   Frontend: http://localhost:3000"
Write-Host "   Backend API: http://localhost:8000"
Write-Host "   Health Check: http://localhost:8000/api/health"
Write-Host ""
Write-Host "📁 Report Storage:" -ForegroundColor $Blue
Write-Host "   Reports are saved to: .\inter-ai-backend\reports\"
Write-Host "   Audio files: .\inter-ai-backend\static\audio\"
Write-Host ""
Write-Host "🔧 Management Commands:" -ForegroundColor $Blue
Write-Host "   View logs: docker-compose logs -f"
Write-Host "   Stop services: docker-compose down"
Write-Host "   Restart: docker-compose restart"
Write-Host "   Update: git pull; docker-compose up --build -d"
Write-Host ""

# Test enhanced reporting
Write-Status "Testing enhanced reporting system..."
try {
    Push-Location "inter-ai-backend"
    $testResult = python -c "import cli_report; print('✅ Enhanced reporting modules loaded successfully')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Enhanced reporting system is ready!"
    } else {
        Write-Warning "Enhanced reporting test failed - check dependencies"
    }
} catch {
    Write-Warning "Could not test Python modules"
} finally {
    Pop-Location
}

# Display VM-specific notes
Write-Host ""
Write-Status "🖥️ VM Deployment Notes:"
Write-Host "   • Reports persist in mounted volumes"
Write-Host "   • Services auto-restart unless stopped"
Write-Host "   • Monitor with: docker-compose logs -f backend"
Write-Host "   • Health endpoint available for monitoring"
Write-Host ""

# Check Windows Firewall
Write-Status "🔥 Windows Firewall Check:"
try {
    $firewallProfiles = Get-NetFirewallProfile | Where-Object { $_.Enabled -eq $true }
    if ($firewallProfiles) {
        Write-Warning "Windows Firewall is active. You may need to allow ports:"
        Write-Host "   Port 3000 (Frontend) and Port 8000 (Backend API)"
        Write-Host "   Or run: New-NetFirewallRule -DisplayName 'CoAct.AI Frontend' -Direction Inbound -Port 3000 -Protocol TCP -Action Allow"
        Write-Host "   And: New-NetFirewallRule -DisplayName 'CoAct.AI Backend' -Direction Inbound -Port 8000 -Protocol TCP -Action Allow"
    }
} catch {
    Write-Warning "Could not check Windows Firewall status"
}

Write-Success "Deployment complete! 🚀"

# Open browser if requested
$openBrowser = Read-Host "Would you like to open the application in your browser? (y/N)"
if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
    Start-Process "http://localhost:3000"
}
# CoAct.AI Enhanced Reports - VM Setup Guide

## 🖥️ VM Deployment Overview

This guide helps you deploy the enhanced CoAct.AI reporting system on a Windows VM with improved features for both learning and assessment modes.

## 📋 Prerequisites

### Required Software
- **Docker Desktop** (with WSL2 backend recommended)
- **Git** for version control
- **PowerShell 5.1+** (built into Windows)
- **Azure OpenAI** account with deployed models

### VM Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 10GB+ free space
- **CPU**: 2+ cores recommended
- **Network**: Internet access for Azure OpenAI API calls

## 🚀 Quick Deployment

### 1. Clone and Setup
```powershell
# Clone the repository
git clone <your-repo-url>
cd <repo-directory>

# Copy environment template
copy .env.template .env

# Edit with your Azure OpenAI credentials
notepad .env
```

### 2. Configure Environment
Edit `.env` file with your Azure OpenAI details:
```env
AZURE_OPENAI_API_KEY=your_actual_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
MODEL_NAME=gpt-4o-mini
TTS_DEPLOYMENT_NAME=tts-1
```

### 3. Deploy with PowerShell
```powershell
# Run deployment script
.\deploy-vm.ps1

# Or rebuild everything
.\deploy-vm.ps1 -Rebuild
```

### 4. Monitor System
```powershell
# Check system health
.\monitor-vm.ps1

# Continuous monitoring
.\monitor-vm.ps1 -Continuous -Interval 30

# Show detailed metrics and logs
.\monitor-vm.ps1 -ShowMetrics -ShowLogs
```

## 🔧 Manual Deployment (Alternative)

If the automated script doesn't work:

```powershell
# Create directories
mkdir inter-ai-backend\reports
mkdir inter-ai-backend\static\audio

# Stop existing containers
docker-compose down

# Build and start
docker-compose up --build -d

# Check status
docker-compose ps
docker-compose logs -f backend
```

## 📊 Accessing the Enhanced System

### Web Interfaces
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/health

### File Locations
- **Reports**: `.\inter-ai-backend\reports\`
- **Audio Files**: `.\inter-ai-backend\static\audio\`
- **Logs**: `docker-compose logs backend`

## 🎯 Enhanced Features Available

### Assessment Mode Improvements
- ✅ Conversation analytics (talk time, question ratios)
- ✅ Evidence-based scoring with quotes
- ✅ Personalized learning paths
- ✅ Business impact explanations
- ✅ Success metrics and timelines

### Learning Mode Improvements
- ✅ Self-awareness reflection questions
- ✅ Mindset transformation tracking
- ✅ Curiosity building techniques
- ✅ Practice plans with difficulty levels
- ✅ Journal prompts for continued growth

## 🔍 Troubleshooting

### Common Issues

#### 1. Docker Not Starting
```powershell
# Check Docker status
docker --version
docker-compose --version

# Restart Docker Desktop
# Or restart the Docker service
```

#### 2. Port Conflicts
```powershell
# Check what's using ports 3000 and 8000
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Kill processes if needed
taskkill /PID <process_id> /F
```

#### 3. Azure OpenAI Connection Issues
```powershell
# Test API connection
curl -H "api-key: YOUR_API_KEY" "https://your-resource.openai.azure.com/openai/deployments?api-version=2024-12-01-preview"

# Check environment variables
docker-compose exec backend env | grep AZURE
```

#### 4. Report Generation Fails
```powershell
# Check backend logs
docker-compose logs backend

# Test Python dependencies
docker-compose exec backend python -c "import cli_report; print('OK')"

# Check file permissions
docker-compose exec backend ls -la reports/
```

### Windows Firewall
If accessing from other machines:
```powershell
# Allow ports through Windows Firewall
New-NetFirewallRule -DisplayName "CoAct.AI Frontend" -Direction Inbound -Port 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "CoAct.AI Backend" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow
```

## 📈 Performance Optimization

### For Low-Resource VMs
```yaml
# In docker-compose.yml, add resource limits:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### For High-Traffic Usage
```env
# In .env file:
WORKERS=4
REQUEST_TIMEOUT=120
MAX_UPLOAD_SIZE=100
```

## 🔄 Maintenance Commands

### Daily Operations
```powershell
# View logs
docker-compose logs -f backend

# Restart services
docker-compose restart

# Update application
git pull
docker-compose up --build -d

# Clean up old containers/images
docker system prune -f
```

### Backup Important Data
```powershell
# Backup reports
copy inter-ai-backend\reports\* backup\reports\

# Backup environment
copy .env backup\

# Export container logs
docker-compose logs backend > backup\backend-logs.txt
```

## 📞 Support

### Health Check Endpoint
Visit `http://localhost:8000/api/health` to see:
- Service status
- Version information
- Active sessions count
- LLM connection status

### Log Analysis
```powershell
# Backend application logs
docker-compose logs backend | Select-String "ERROR"

# System resource usage
docker stats --no-stream

# Container health
docker-compose ps
```

### Performance Monitoring
```powershell
# Run continuous monitoring
.\monitor-vm.ps1 -Continuous -ShowMetrics

# Check disk space
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, @{Name="Size(GB)";Expression={[math]::Round($_.Size/1GB,2)}}, @{Name="FreeSpace(GB)";Expression={[math]::Round($_.FreeSpace/1GB,2)}}
```

## 🎉 Success Indicators

Your enhanced reporting system is working correctly when:
- ✅ Health check returns "healthy" status
- ✅ Frontend loads at http://localhost:3000
- ✅ Backend API responds at http://localhost:8000
- ✅ Reports generate in `.\inter-ai-backend\reports\`
- ✅ Enhanced features appear in generated PDFs
- ✅ No error messages in `docker-compose logs backend`

## 🔗 Next Steps

1. **Test Enhanced Reports**: Create a session and generate both assessment and learning mode reports
2. **Customize Branding**: Modify colors and logos in the PDF generation code
3. **Scale Resources**: Adjust Docker resource limits based on usage
4. **Monitor Performance**: Set up regular health checks and log monitoring
5. **Backup Strategy**: Implement automated backups of reports and configuration
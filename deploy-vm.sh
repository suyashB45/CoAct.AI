#!/bin/bash

# CoAct.AI Enhanced Reports - VM Deployment Script
# This script deploys the enhanced reporting system on a VM

set -e

echo "🚀 Deploying CoAct.AI Enhanced Reports on VM..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating template..."
    cat > .env << EOF
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
MODEL_NAME=gpt-4o-mini
TTS_DEPLOYMENT_NAME=tts-1

# Optional: Azure Storage (for report persistence)
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection_string_here
EOF
    print_warning "Please edit .env file with your Azure OpenAI credentials before continuing."
    print_warning "Run: nano .env"
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p inter-ai-backend/reports
mkdir -p inter-ai-backend/static/audio
chmod 755 inter-ai-backend/reports
chmod 755 inter-ai-backend/static/audio

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down --remove-orphans || true

# Build and start services
print_status "Building and starting enhanced CoAct.AI services..."
docker-compose up --build -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check health
print_status "Checking service health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        print_success "Backend service is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Backend service failed to start properly"
        docker-compose logs backend
        exit 1
    fi
    sleep 2
done

# Check frontend
if curl -f http://localhost:3000 &> /dev/null; then
    print_success "Frontend service is healthy!"
else
    print_warning "Frontend may still be starting..."
fi

# Display service status
print_status "Service Status:"
docker-compose ps

# Display access information
echo ""
print_success "🎉 CoAct.AI Enhanced Reports deployed successfully!"
echo ""
echo "📊 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   Health Check: http://localhost:8000/api/health"
echo ""
echo "📁 Report Storage:"
echo "   Reports are saved to: ./inter-ai-backend/reports/"
echo "   Audio files: ./inter-ai-backend/static/audio/"
echo ""
echo "🔧 Management Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Update: git pull && docker-compose up --build -d"
echo ""

# Test enhanced reporting
print_status "Testing enhanced reporting system..."
if command -v python3 &> /dev/null; then
    cd inter-ai-backend
    if python3 -c "import cli_report; print('✅ Enhanced reporting modules loaded successfully')" 2>/dev/null; then
        print_success "Enhanced reporting system is ready!"
    else
        print_warning "Enhanced reporting test failed - check dependencies"
    fi
    cd ..
fi

# Display VM-specific notes
echo ""
print_status "🖥️  VM Deployment Notes:"
echo "   • Reports persist in mounted volumes"
echo "   • Services auto-restart unless stopped"
echo "   • Monitor with: docker-compose logs -f backend"
echo "   • Health endpoint available for monitoring"
echo ""

# Check if firewall rules might be needed
if command -v ufw &> /dev/null; then
    print_status "🔥 Firewall Check:"
    if ufw status | grep -q "Status: active"; then
        print_warning "UFW firewall is active. You may need to allow ports:"
        echo "   sudo ufw allow 3000/tcp  # Frontend"
        echo "   sudo ufw allow 8000/tcp  # Backend API"
    fi
fi

print_success "Deployment complete! 🚀"
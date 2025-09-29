#!/bin/bash
set -e

# RAG Anything with AWS Bedrock Installation Script for Amazon Linux 2023
# Optimized for disk space and excludes GPU packages

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as ec2-user."
fi

# Check if running on Amazon Linux 2023
if ! grep -q "Amazon Linux" /etc/os-release; then
    error "This script is designed for Amazon Linux 2023"
fi

log "Starting RAG Anything with AWS Bedrock installation (No GPU version)..."

# Check available disk space
AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024))

log "Available disk space: ${AVAILABLE_GB}GB"

if [ "$AVAILABLE_GB" -lt 10 ]; then
    error "Insufficient disk space. At least 10GB free space required."
fi

# Clean up before starting
log "Cleaning up temporary files and caches..."
sudo dnf clean all
pip cache purge 2>/dev/null || true
sudo rm -rf /tmp/* 2>/dev/null || true

# Update system
log "Updating system packages..."
sudo dnf update -y

# Fix curl conflicts first
log "Resolving curl package conflicts..."
sudo dnf remove -y curl-minimal || true
sudo dnf install -y --allowerasing curl

# Verify curl is working
if ! command -v curl &> /dev/null; then
    error "Failed to install curl. Please resolve manually."
fi

log "Curl installed successfully: $(curl --version | head -n1)"

# Install system dependencies
log "Installing system dependencies..."
sudo dnf install -y \
    python3.11 \
    python3.11-pip \
    python3.11-devel \
    git \
    gcc \
    gcc-c++ \
    make \
    wget \
    unzip \
    htop \
    tree \
    vim

# Install LibreOffice alternatives (skip LibreOffice to save space)
log "Installing document processing tools..."
sudo dnf install -y pandoc || warn "Pandoc not available"

# Create application user if it doesn't exist
if ! id "raganything" &>/dev/null; then
    log "Creating raganything user..."
    sudo useradd -m -s /bin/bash raganything
fi

# Create directory structure
log "Creating directory structure..."
sudo mkdir -p /opt/raganything/{app,config,logs,data,cache,scripts,backups}
sudo chown -R raganything:raganything /opt/raganything

# Set up Python virtual environment
log "Setting up Python virtual environment..."
sudo -u raganything python3.11 -m venv /opt/raganything/venv

# Upgrade pip and install build tools
log "Upgrading pip and installing build tools..."
sudo -u raganything /opt/raganything/venv/bin/pip install --upgrade pip setuptools wheel --no-cache-dir

# Install AWS SDK
log "Installing AWS SDK..."
sudo -u raganything /opt/raganything/venv/bin/pip install boto3 botocore --no-cache-dir

# Install additional dependencies (excluding GPU packages)
log "Installing additional Python dependencies (CPU only)..."
sudo -u raganything /opt/raganything/venv/bin/pip install --no-cache-dir \
    python-dotenv \
    asyncio-throttle \
    tenacity \
    aiofiles \
    uvloop

# Install document processing libraries
log "Installing document processing libraries..."
sudo -u raganything /opt/raganything/venv/bin/pip install --no-cache-dir \
    python-docx \
    openpyxl \
    python-pptx \
    PyPDF2 \
    pdfplumber \
    Pillow

# Install RAG Anything with CPU-only dependencies
log "Installing RAG Anything (CPU only)..."

# First, install core dependencies without GPU packages
sudo -u raganything /opt/raganything/venv/bin/pip install --no-cache-dir \
    numpy \
    pandas \
    scikit-learn \
    transformers \
    sentence-transformers \
    faiss-cpu \
    chromadb \
    langchain \
    langchain-community

# Install RAG Anything without all extras to avoid GPU packages
sudo -u raganything /opt/raganything/venv/bin/pip install --no-cache-dir raganything

# Clone the enhanced RAG Anything repository
log "Setting up application code..."
if [ -d "/opt/raganything/app/.git" ]; then
    log "Updating existing repository..."
    sudo -u raganything git -C /opt/raganything/app pull
else
    log "Cloning RAG Anything repository..."
    sudo -u raganything git clone https://github.com/satishk01/raganything-aws.git /opt/raganything/app
fi

# Install application in development mode
log "Installing application in development mode..."
sudo -u raganything /opt/raganything/venv/bin/pip install -e /opt/raganything/app --no-cache-dir

# Copy configuration template
log "Setting up configuration..."
if [ ! -f "/opt/raganything/config/.env" ]; then
    if [ -f "/opt/raganything/app/deployment/config/environment.template" ]; then
        sudo -u raganything cp /opt/raganything/app/deployment/config/environment.template /opt/raganything/config/.env
    else
        # Create a basic .env file
        sudo -u raganything tee /opt/raganything/config/.env > /dev/null << 'EOF'
# AWS Configuration
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1

# Bedrock Model Configuration
BEDROCK_CLAUDE_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_CLAUDE_HAIKU_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_TITAN_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

# Model Parameters
BEDROCK_MAX_TOKENS=4096
BEDROCK_TEMPERATURE=0.7
BEDROCK_RETRY_MAX_ATTEMPTS=3
BEDROCK_RETRY_BACKOFF_FACTOR=2.0

# RAG Anything Configuration
WORKING_DIR=/opt/raganything/data/rag_storage
OUTPUT_DIR=/opt/raganything/data/output
PARSER=mineru
PARSE_METHOD=auto

# Multimodal Processing
ENABLE_IMAGE_PROCESSING=true
ENABLE_TABLE_PROCESSING=true
ENABLE_EQUATION_PROCESSING=true

# Performance Settings
MAX_CONCURRENT_FILES=2
CONTEXT_WINDOW=1
MAX_CONTEXT_TOKENS=2000

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=/opt/raganything/logs
EOF
    fi
    
    sudo -u raganything chmod 600 /opt/raganything/config/.env
    log "Configuration file created"
else
    log "Configuration file already exists"
fi

# Set up systemd service
log "Setting up systemd service..."
if [ -f "/opt/raganything/app/deployment/systemd/raganything.service" ]; then
    sudo cp /opt/raganything/app/deployment/systemd/raganything.service /etc/systemd/system/
else
    # Create a basic systemd service file
    sudo tee /etc/systemd/system/raganything.service > /dev/null << 'EOF'
[Unit]
Description=RAG Anything with AWS Bedrock
After=network.target

[Service]
Type=simple
User=raganything
Group=raganything
WorkingDirectory=/opt/raganything/app
Environment=PATH=/opt/raganything/venv/bin
EnvironmentFile=/opt/raganything/config/.env
ExecStart=/opt/raganything/venv/bin/python -m raganything.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
fi

sudo systemctl daemon-reload
sudo systemctl enable raganything

# Create test script
log "Creating test script..."
sudo -u raganything tee /opt/raganything/scripts/test_bedrock.py > /dev/null << 'EOF'
#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/opt/raganything/app')

try:
    from raganything.bedrock_rag import BedrockRAGAnything
    from raganything import RAGAnythingConfig
    from raganything.bedrock import BedrockConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure RAG Anything with Bedrock integration is properly installed")
    sys.exit(1)

async def test_bedrock_integration():
    """Test basic Bedrock integration"""
    
    print("🚀 Testing RAG Anything with AWS Bedrock")
    print("=" * 50)
    
    try:
        # Create configurations
        rag_config = RAGAnythingConfig(
            working_dir="/opt/raganything/data/rag_storage",
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )
        
        bedrock_config = BedrockConfig.from_env()
        
        # Initialize RAG Anything with Bedrock
        rag = BedrockRAGAnything(
            config=rag_config,
            bedrock_config=bedrock_config
        )
        
        print("✅ RAG Anything initialized successfully")
        
        # Validate Bedrock access
        print("\n🔍 Validating Bedrock access...")
        if await rag.validate_bedrock_access():
            print("✅ Bedrock access validation successful")
        else:
            print("❌ Bedrock access validation failed")
            return False
        
        # Test basic text query
        print("\n🔍 Testing basic text query...")
        result = await rag.aquery(
            "What is artificial intelligence?",
            mode="naive"
        )
        print(f"✅ Query successful: {result[:100]}...")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bedrock_integration())
    sys.exit(0 if success else 1)
EOF

chmod +x /opt/raganything/scripts/test_bedrock.py

# Create startup script
log "Creating startup script..."
sudo tee /opt/raganything/scripts/start.sh > /dev/null << 'EOF'
#!/bin/bash

echo "🚀 Starting RAG Anything with AWS Bedrock..."

# Start the service
sudo systemctl start raganything

# Check status
sleep 5
if systemctl is-active --quiet raganything; then
    echo "✅ RAG Anything service started successfully"
else
    echo "❌ Failed to start RAG Anything service"
    sudo journalctl -u raganything --no-pager -l
    exit 1
fi
EOF

chmod +x /opt/raganything/scripts/start.sh

# Set proper permissions
log "Setting proper permissions..."
sudo chown -R raganything:raganything /opt/raganything
sudo chmod -R 755 /opt/raganything/scripts
sudo chmod 600 /opt/raganything/config/.env

# Final cleanup
log "Final cleanup..."
sudo -u raganything /opt/raganything/venv/bin/pip cache purge
sudo dnf clean all

# Check final disk usage
log "Final disk usage:"
df -h

log "✅ Installation completed successfully!"
echo
echo "📋 Next steps:"
echo "1. Test the installation: sudo -u raganything /opt/raganything/scripts/test_bedrock.py"
echo "2. Start the service: /opt/raganything/scripts/start.sh"
echo "3. Check status: sudo systemctl status raganything"
echo
echo "📝 Note: This installation excludes GPU packages to save disk space."
echo "If you need GPU support later, you can install it separately."
echo
log "Installation complete! 🎉"